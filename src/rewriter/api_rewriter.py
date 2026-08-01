import os
import logging
from typing import List, Optional
from openai import OpenAI
from .base import BaseRewriter
from ..models.config import ApiProviderConfig

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
                    timeout=float(config.timeout_seconds)
                )
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client for '{config.name}': {e}")

    @property
    def is_available(self) -> bool:
        return self.client is not None


class ApiRewriter(BaseRewriter):
    def __init__(self, providers: List[ApiProviderConfig]):
        self.providers = sorted(providers, key=lambda p: p.priority)
        self.pool: List[ProviderClient] = [
            ProviderClient(cfg) for cfg in self.providers if cfg.enabled
        ]
        # Sort pool by provider priority (lowest number first)
        self.pool.sort(key=lambda p: p.config.priority)

    def is_available(self) -> bool:
        """Returns True if at least one provider in the pool has a valid API key."""
        return any(p.is_available for p in self.pool)

    def rewrite(self, bullet_text: str, jd_keywords: List[str], prompt_template: str) -> str:
        """Tries active API providers in order of priority (1st OpenRouter -> 2nd Gemini -> 3rd Cerebras -> 4th Groq)."""
        if not self.is_available():
            raise RuntimeError("No Cloud LLM API keys configured.")

        keywords_str = ", ".join(jd_keywords[:10])
        user_prompt = (
            f"Original Bullet: {bullet_text}\n"
            f"Target Job Keywords: {keywords_str}\n\n"
            f"Instructions:\n{prompt_template}"
        )

        last_error = None
        for provider_client in self.pool:
            if not provider_client.is_available:
                continue

            cfg = provider_client.config
            try:
                response = provider_client.client.chat.completions.create(
                    model=cfg.api_model,
                    messages=[
                        {"role": "system", "content": "You are a professional resume tailoring assistant."},
                        {"role": "user", "content": user_prompt}
                    ],
                    max_tokens=cfg.max_tokens,
                    temperature=cfg.temperature
                )

                if response and response.choices and len(response.choices) > 0:
                    choice = response.choices[0]
                    if choice.message and choice.message.content:
                        content = choice.message.content.strip().strip('"')
                        if content:
                            return content, cfg.name

            except Exception as e:
                logger.warning(f"Cloud API provider '{cfg.name}' (priority {cfg.priority}, model {cfg.api_model}) failed: {e}. Trying next priority provider...")
                last_error = e

        raise RuntimeError(f"All Cloud API providers in pool failed. Last error: {last_error}")
