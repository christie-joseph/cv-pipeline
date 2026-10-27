import re
import time
import logging
import threading
from typing import Dict, Optional

logger = logging.getLogger(__name__)


def is_rate_limit_error(error: Exception) -> bool:
    """Detects HTTP 429, 503 demand spikes, 529 overload, or quota exhaustion messages."""
    if not error:
        return False
    msg = str(error).lower()
    
    # Common status codes for rate limits and capacity spikes
    rate_limit_codes = ["429", "503", "529"]
    for code in rate_limit_codes:
        if code in msg:
            return True
            
    # Common textual indicators across OpenAI, Gemini, Groq, OpenRouter, Cerebras
    rate_indicators = [
        "rate limit",
        "too many requests",
        "resource exhausted",
        "high demand",
        "spikes in demand",
        "overloaded",
        "quota exceeded",
        "tokens per minute",
        "requests per minute",
        "tpm",
        "rpm",
    ]
    return any(ind in msg for ind in rate_indicators)


def parse_retry_after(error: Exception) -> Optional[float]:
    """Attempts to parse recommended wait duration in seconds from exception text or headers."""
    if not error:
        return None
    msg = str(error)
    # Check for "retry after X seconds" or "wait X.Xs" or "in X seconds"
    match = re.search(r"(?:retry\s+after|wait|in)\s+(\d+(?:\.\d+)?)\s*(?:s|sec|seconds)?", msg, re.IGNORECASE)
    if match:
        try:
            return float(match.group(1))
        except (ValueError, TypeError):
            pass
    return None


class EndpointPacer:
    """Thread-safe request pacer that enforces a minimum wait interval between consecutive calls."""
    def __init__(self):
        self._last_call_time: Dict[str, float] = {}
        self._lock = threading.Lock()

    def acquire(self, key: str, min_interval_seconds: float) -> float:
        """
        Ensures at least `min_interval_seconds` have elapsed since the last call for `key`.
        Blocks with time.sleep if called too quickly.
        Returns the actual seconds slept (0.0 if no sleep needed).
        """
        if min_interval_seconds <= 0:
            return 0.0

        with self._lock:
            now = time.time()
            last_time = self._last_call_time.get(key, 0.0)
            elapsed = now - last_time
            sleep_needed = min_interval_seconds - elapsed

            if sleep_needed > 0:
                time.sleep(sleep_needed)
                slept = sleep_needed
                self._last_call_time[key] = time.time()
            else:
                slept = 0.0
                self._last_call_time[key] = now

            return slept

    def reset(self, key: Optional[str] = None):
        with self._lock:
            if key:
                self._last_call_time.pop(key, None)
            else:
                self._last_call_time.clear()


class ProviderSafetyManager:
    """
    Manages cooldowns, rate limits, and circuit breakers for API providers.
    Prevents hammering failing/rate-limited endpoints and protects services from DDoS.
    """
    def __init__(self, default_cooldown_seconds: float = 60.0, failure_threshold: int = 2):
        self.default_cooldown_seconds = default_cooldown_seconds
        self.failure_threshold = failure_threshold
        self._consecutive_failures: Dict[str, int] = {}
        self._cooldown_until: Dict[str, float] = {}
        self._lock = threading.Lock()

    def is_healthy(self, provider_name: str) -> bool:
        """Returns True if the provider is not currently in a cooldown window."""
        with self._lock:
            cooldown_time = self._cooldown_until.get(provider_name, 0.0)
            if time.time() < cooldown_time:
                return False
            return True

    def get_remaining_cooldown(self, provider_name: str) -> float:
        """Returns remaining cooldown duration in seconds, or 0.0 if provider is healthy."""
        with self._lock:
            cooldown_time = self._cooldown_until.get(provider_name, 0.0)
            remaining = cooldown_time - time.time()
            return max(0.0, remaining)

    def record_success(self, provider_name: str):
        """Resets failure counts and clears any cooldown upon successful response."""
        with self._lock:
            self._consecutive_failures[provider_name] = 0
            self._cooldown_until.pop(provider_name, None)

    def record_failure(
        self,
        provider_name: str,
        is_rate_limit: bool = False,
        retry_after: Optional[float] = None
    ) -> float:
        """
        Records an API error. If rate-limited or if failure threshold is reached,
        trips the circuit breaker and places the provider in cooldown.
        Returns the duration of the cooldown assigned.
        """
        with self._lock:
            current_failures = self._consecutive_failures.get(provider_name, 0) + 1
            self._consecutive_failures[provider_name] = current_failures

            # Calculate cooldown duration
            if is_rate_limit:
                duration = retry_after if retry_after and retry_after > 0 else self.default_cooldown_seconds
                self._cooldown_until[provider_name] = time.time() + duration
                logger.warning(
                    f"SafetyManager: Provider '{provider_name}' rate-limited or high-demand. "
                    f"Cooldown activated for {duration:.1f}s."
                )
                return duration
            elif current_failures >= self.failure_threshold:
                duration = self.default_cooldown_seconds
                self._cooldown_until[provider_name] = time.time() + duration
                logger.warning(
                    f"SafetyManager: Provider '{provider_name}' reached {current_failures} consecutive failures. "
                    f"Circuit breaker tripped for {duration:.1f}s."
                )
                return duration

            return 0.0

    def reset(self, provider_name: Optional[str] = None):
        """Clears state for testing or manual recovery."""
        with self._lock:
            if provider_name:
                self._consecutive_failures.pop(provider_name, None)
                self._cooldown_until.pop(provider_name, None)
            else:
                self._consecutive_failures.clear()
                self._cooldown_until.clear()
