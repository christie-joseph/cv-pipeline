import os
import json
import re
import time
import random
import logging
from typing import List, Optional, Tuple
from openai import OpenAI
from rich import print as rprint

from .base import BaseRewriter
from ..models.config import ApiProviderConfig, RateLimitConfig
from .rate_limiter import EndpointPacer, ProviderSafetyManager, is_rate_limit_error, parse_retry_after

logger = logging.getLogger(__name__)


class ProviderClient:
    """Initialized OpenAI client instance for a single API provider."""
    def __init__(self, config: ApiProviderConfig):
        self.config = config
        self.client: Optional[OpenAI] = None

        # Check provider-specific key first, then fall back to generic LLM_API_KEY
        api_key = os.getenv(config.api_key_env) or os.getenv("LLM_API_KEY")
        if api_key and len(api_key.strip()) > 0:
            try:
                self.client = OpenAI(
                    api_key=api_key.strip(),
                    base_url=config.api_url,
                    timeout=float(config.timeout_seconds),
                    max_retries=0
                )
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client for '{config.name}': {e}")

    @property
    def is_available(self) -> bool:
        return self.client is not None


class ApiRewriter(BaseRewriter):
    def __init__(
        self,
        providers: List[ApiProviderConfig],
        rate_limit_config: Optional[RateLimitConfig] = None
    ):
        self.providers = sorted(providers, key=lambda p: p.priority)
        self.pool: List[ProviderClient] = [
            ProviderClient(cfg) for cfg in self.providers if cfg.enabled
        ]
        self.pool.sort(key=lambda p: p.config.priority)
        self.rate_limit = rate_limit_config or RateLimitConfig()
        self.pacer = EndpointPacer()
        self.safety_manager = ProviderSafetyManager(
            default_cooldown_seconds=self.rate_limit.cooldown_seconds,
            failure_threshold=self.rate_limit.circuit_breaker_threshold
        )

    def is_available(self) -> bool:
        """Returns True if at least one enabled provider has an active API key."""
        return any(p.is_available for p in self.pool)

    def has_healthy_provider(self) -> bool:
        """Returns True if at least one available provider is not currently cooling down."""
        return any(p.is_available and self.safety_manager.is_healthy(p.config.name) for p in self.pool)

    def rewrite(self, bullet_text: str, jd_keywords: List[str], prompt_template: str) -> Tuple[str, str]:
        """Tries active API providers in order of priority."""
        res, provider_name = self.rewrite_batch([bullet_text], jd_keywords, prompt_template)
        return res[0], provider_name

    def rewrite_batch(self, bullets: List[str], jd_keywords: List[str], prompt_template: str) -> Tuple[List[str], str]:
        """
        Sends batch API request with rate limiting, pacing, retries, and circuit breaker protection.
        Returns (rewritten_bullets, provider_name).
        """
        if not bullets:
            return [], "None"

        if not self.is_available():
            raise RuntimeError("No Cloud LLM API keys configured.")

        # Ultra-compact machine-optimized representation
        system_prompt = (
            "Task: Align resume bullets with target keywords. "
            "Rules: preserve facts/numbers/tech exactly; no hallucinations. "
            "Output format: JSON object {\"out\": [\"reworded 1\", \"reworded 2\"]}"
        )

        compact_payload = {
            "kw": [k for k in jd_keywords[:8] if len(k) > 1],
            "b": bullets
        }
        user_prompt = json.dumps(compact_payload, separators=(",", ":"))

        last_error = None
        for provider_client in self.pool:
            if not provider_client.is_available:
                continue

            cfg = provider_client.config
            provider_name = cfg.name

            # Check if provider is currently in cooldown (e.g. recent 429/503 or circuit breaker)
            if not self.safety_manager.is_healthy(provider_name):
                rem = self.safety_manager.get_remaining_cooldown(provider_name)
                rprint(f"[yellow][!] Provider '{provider_name}' in cooldown ({rem:.1f}s remaining). Skipping...[/yellow]")
                continue

            # Scale max_tokens proportionally to number of bullets
            batch_max_tokens = max(cfg.max_tokens, len(bullets) * 120)

            # Retry loop with exponential backoff for transient errors
            max_attempts = max(1, self.rate_limit.max_retries + 1)
            for attempt in range(max_attempts):
                try:
                    # Enforce minimum spacing between calls to this provider
                    slept = self.pacer.acquire(provider_name, self.rate_limit.min_request_interval)
                    if slept > 0:
                        logger.debug(f"EndpointPacer: Waited {slept:.2f}s before calling '{provider_name}'")

                    rprint(f"[cyan][*] Trying Cloud API Provider (Priority {cfg.priority}): {provider_name}...[/cyan]")

                    response = provider_client.client.chat.completions.create(
                        model=cfg.api_model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        max_tokens=batch_max_tokens,
                        temperature=cfg.temperature
                    )

                    if response and response.choices and len(response.choices) > 0:
                        choice = response.choices[0]
                        if choice.message and choice.message.content:
                            content = choice.message.content
                            parsed_list = None
                            try:
                                raw_json = json.loads(content)
                                if isinstance(raw_json, dict) and "out" in raw_json:
                                    parsed_list = raw_json["out"]
                                elif isinstance(raw_json, list):
                                    parsed_list = raw_json
                            except json.JSONDecodeError:
                                # Strip markdown fences if present
                                content_stripped = re.sub(r"^```(?:json)?\s*", "", content, flags=re.MULTILINE)
                                content_stripped = re.sub(r"```\s*$", "", content_stripped, flags=re.MULTILINE).strip()
                                try:
                                    raw_json = json.loads(content_stripped)
                                    if isinstance(raw_json, dict) and "out" in raw_json:
                                        parsed_list = raw_json["out"]
                                    elif isinstance(raw_json, list):
                                        parsed_list = raw_json
                                except json.JSONDecodeError:
                                    json_match = re.search(r"\{.*?\"out\":\s*(\[.*?\]).*?\}|(\[.*?\])", content_stripped, re.DOTALL)
                                    if json_match:
                                        target_str = json_match.group(1) or json_match.group(2)
                                        try:
                                            parsed_list = json.loads(target_str)
                                        except json.JSONDecodeError:
                                            pass

                            if isinstance(parsed_list, list) and len(parsed_list) == len(bullets):
                                self.safety_manager.record_success(provider_name)
                                rprint(f"[green][+] Cloud API Provider {provider_name} succeeded![/green]")
                                return [str(item).strip() for item in parsed_list], provider_name
                            elif isinstance(parsed_list, list) and len(parsed_list) > 0:
                                self.safety_manager.record_success(provider_name)
                                result = [str(item).strip() for item in parsed_list[:len(bullets)]]
                                while len(result) < len(bullets):
                                    result.append(bullets[len(result)])
                                rprint(f"[green][+] Cloud API Provider {provider_name} succeeded (with length adjustment)![/green]")
                                return result, provider_name
                            else:
                                rprint(f"[yellow][!] Cloud API Provider {provider_name} returned invalid structure. Trying next...[/yellow]")
                                logger.warning(f"Failed to parse valid list from '{provider_name}'. Content: {content[:100]}...")
                                # Structure parsing failures are not transient API rate-limits, so don't retry same model
                                break

                except Exception as e:
                    last_error = e
                    is_rl = is_rate_limit_error(e)
                    retry_sec = parse_retry_after(e)

                    if is_rl:
                        # On 429/503 rate-limit, immediately activate cooldown and switch provider
                        cd = self.safety_manager.record_failure(provider_name, is_rate_limit=True, retry_after=retry_sec)
                        rprint(f"[yellow][!] Provider '{provider_name}' hit rate limit / demand spike. Cooling down for {cd:.1f}s...[/yellow]")
                        break
                    elif attempt < max_attempts - 1:
                        # Transient network error, retry with exponential backoff & jitter
                        backoff = self.rate_limit.backoff_base * (2 ** attempt) + random.uniform(0.1, 0.4)
                        rprint(f"[yellow][!] Provider '{provider_name}' transient error: {e}. Retrying in {backoff:.1f}s...[/yellow]")
                        time.sleep(backoff)
                    else:
                        # Max retries exhausted, record failure
                        self.safety_manager.record_failure(provider_name, is_rate_limit=False)
                        rprint(f"[yellow][!] Cloud API Provider '{provider_name}' failed. Trying next provider...[/yellow]")
                        logger.warning(f"Cloud API provider '{provider_name}' failed: {e}. Trying next priority provider...")

        raise RuntimeError(f"All Cloud API providers in pool failed batch request. Last error: {last_error}")
