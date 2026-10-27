import time
import pytest
from src.rewriter.rate_limiter import (
    EndpointPacer,
    ProviderSafetyManager,
    is_rate_limit_error,
    parse_retry_after
)
from src.models.config import ApiProviderConfig, RateLimitConfig
from src.rewriter.api_rewriter import ApiRewriter
from src.rewriter.ollama_rewriter import OllamaRewriter


def test_endpoint_pacer():
    pacer = EndpointPacer()
    key = "test_provider"

    # First call should not sleep
    slept1 = pacer.acquire(key, min_interval_seconds=0.1)
    assert slept1 == 0.0

    # Immediate second call should sleep to fulfill 0.1s interval
    slept2 = pacer.acquire(key, min_interval_seconds=0.1)
    assert slept2 > 0.0
    assert slept2 <= 0.15

    # Waiting 0.12s before next call should mean no sleep needed
    time.sleep(0.12)
    slept3 = pacer.acquire(key, min_interval_seconds=0.1)
    assert slept3 == 0.0


def test_rate_limit_error_detection():
    # Status code indicators
    assert is_rate_limit_error(RuntimeError("Error code: 429 - Too Many Requests"))
    assert is_rate_limit_error(RuntimeError("Error code: 503 - High demand spike"))
    assert is_rate_limit_error(RuntimeError("Error code: 529 - Site Overloaded"))

    # Textual indicators
    assert is_rate_limit_error(Exception("Rate limit reached for requests per minute"))
    assert is_rate_limit_error(Exception("RESOURCE_EXHAUSTED: quota exceeded"))
    assert is_rate_limit_error(Exception("This model is currently experiencing high demand."))

    # Normal errors should NOT be detected as rate limits
    assert not is_rate_limit_error(ValueError("Invalid JSON response"))
    assert not is_rate_limit_error(KeyError("missing key"))


def test_parse_retry_after():
    assert parse_retry_after(Exception("Please retry after 15 seconds")) == 15.0
    assert parse_retry_after(Exception("Rate limited, wait 2.5s before retrying")) == 2.5
    assert parse_retry_after(Exception("retry in 30 seconds")) == 30.0
    assert parse_retry_after(Exception("unrelated error")) is None


def test_provider_safety_manager_cooldown():
    manager = ProviderSafetyManager(default_cooldown_seconds=0.5, failure_threshold=2)
    provider = "gemini"

    assert manager.is_healthy(provider)

    # 1. Direct rate limit triggers immediate cooldown
    manager.record_failure(provider, is_rate_limit=True, retry_after=0.3)
    assert not manager.is_healthy(provider)
    assert manager.get_remaining_cooldown(provider) > 0.0

    # Wait for cooldown to expire
    time.sleep(0.35)
    assert manager.is_healthy(provider)
    assert manager.get_remaining_cooldown(provider) == 0.0


def test_provider_safety_manager_circuit_breaker():
    manager = ProviderSafetyManager(default_cooldown_seconds=0.5, failure_threshold=2)
    provider = "groq"

    # First transient failure should not trip circuit breaker
    manager.record_failure(provider, is_rate_limit=False)
    assert manager.is_healthy(provider)

    # Second failure reaches threshold (2) -> trips circuit breaker
    manager.record_failure(provider, is_rate_limit=False)
    assert not manager.is_healthy(provider)

    # Success resets everything
    manager.record_success(provider)
    assert manager.is_healthy(provider)


def test_api_rewriter_skips_cooling_down_provider(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "dummy_key_1")
    monkeypatch.setenv("GROQ_API_KEY", "dummy_key_2")

    providers = [
        ApiProviderConfig(name="openrouter", api_key_env="OPENROUTER_API_KEY", priority=1),
        ApiProviderConfig(name="groq", api_key_env="GROQ_API_KEY", priority=2)
    ]
    rate_cfg = RateLimitConfig(cooldown_seconds=60.0)
    rewriter = ApiRewriter(providers=providers, rate_limit_config=rate_cfg)

    # Put openrouter into cooldown
    rewriter.safety_manager.record_failure("openrouter", is_rate_limit=True)
    assert not rewriter.safety_manager.is_healthy("openrouter")
    assert rewriter.safety_manager.is_healthy("groq")

    # Has healthy provider should still be True because groq is active
    assert rewriter.has_healthy_provider()


def test_ollama_rewriter_circuit_breaker():
    rate_cfg = RateLimitConfig(cooldown_seconds=60.0, circuit_breaker_threshold=2)
    # Target non-existent port to simulate unavailable/broken Ollama
    rewriter = OllamaRewriter(
        base_url="http://localhost:99999",
        timeout_seconds=1,
        rate_limit_config=rate_cfg
    )

    # First check fails
    assert not rewriter.is_available()
    assert rewriter.safety_manager._consecutive_failures.get("ollama") == 1

    # Second check fails and trips circuit breaker
    rewriter._checked = False
    assert not rewriter.is_available()
    assert rewriter.safety_manager._consecutive_failures.get("ollama") == 2
    assert not rewriter.safety_manager.is_healthy("ollama")

    # While tripped, is_available returns False immediately without attempting HTTP
    start = time.time()
    assert not rewriter.is_available()
    elapsed = time.time() - start
    assert elapsed < 0.1  # Fast return without blocking
