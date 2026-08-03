import os
import logging
from typing import List, Optional, Tuple
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
                    timeout=float(config.timeout_seconds),
                    max_retries=0
                )
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client for '{config.name}': {e}")

    @property
    def is_available(self) -> bool:
        return self.client is not None


import json
import re

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

    def rewrite(self, bullet_text: str, jd_keywords: List[str], prompt_template: str) -> Tuple[str, str]:
        """Tries active API providers in order of priority (1st OpenRouter -> 2nd Gemini -> 3rd Cerebras -> 4th Groq)."""
        res, provider_name = self.rewrite_batch([bullet_text], jd_keywords, prompt_template)
        return res[0], provider_name

    def rewrite_batch(self, bullets: List[str], jd_keywords: List[str], prompt_template: str) -> Tuple[List[str], str]:
        """Sends a single batch API request containing all bullets, returning a list of rewritten bullets and provider_name."""
        if not bullets:
            return [], "None"

        if not self.is_available():
            raise RuntimeError("No Cloud LLM API keys configured.")

        keywords_str = ", ".join(jd_keywords[:10])
        bullets_formatted = "\n".join(f"{i+1}. {b}" for i, b in enumerate(bullets))
        
        system_prompt = (
            "You are a strict, non-hallucinating resume editor. The original bullet points are the single SOURCE OF TRUTH. "
            "Reword wording ONLY for alignment with job description keywords. Never invent new metrics, tools, responsibilities, or facts. "
            "You will be given a list of numbered bullets. Respond ONLY with a valid JSON array of strings containing the reworded bullets in exact corresponding order. "
            "Example response format: [\"reworded bullet 1\", \"reworded bullet 2\"]"
        )
        
        user_prompt = (
            f"Target Job Keywords: {keywords_str}\n\n"
            f"Instructions:\n{prompt_template}\n\n"
            f"Bullets to rewrite:\n{bullets_formatted}"
        )

        last_error = None
        for provider_client in self.pool:
            if not provider_client.is_available:
                continue

            cfg = provider_client.config
            try:
                from rich import print as rprint
                rprint(f"[cyan][*] Trying Cloud API Provider (Priority {cfg.priority}): {cfg.name}...[/cyan]")
                
                # Scale max_tokens proportionally to number of bullets
                batch_max_tokens = max(cfg.max_tokens, len(bullets) * 120)
                
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
                        content = choice.message.content.strip()
                        # Extract JSON array using regex if surrounded by markdown codeblock or text
                        json_match = re.search(r"\[\s*\".*\"\s*\]", content, re.DOTALL)
                        if json_match:
                            content = json_match.group(0)
                        
                        try:
                            parsed_list = json.loads(content)
                            if isinstance(parsed_list, list) and len(parsed_list) == len(bullets):
                                rprint(f"[green][+] Cloud API Provider {cfg.name} succeeded![/green]")
                                return [str(item).strip() for item in parsed_list], cfg.name
                            elif isinstance(parsed_list, list) and len(parsed_list) > 0:
                                # Fallback padding/truncation if LLM returned slightly different list length
                                result = [str(item).strip() for item in parsed_list[:len(bullets)]]
                                while len(result) < len(bullets):
                                    result.append(bullets[len(result)])
                                rprint(f"[green][+] Cloud API Provider {cfg.name} succeeded (with length adjustment)![/green]")
                                return result, cfg.name
                        except json.JSONDecodeError as je:
                            rprint(f"[yellow][!] Cloud API Provider {cfg.name} returned invalid JSON. Trying next...[/yellow]")
                            logger.warning(f"Failed to parse JSON batch from '{cfg.name}': {je}. Content: {content[:100]}...")

            except Exception as e:
                from rich import print as rprint
                rprint(f"[yellow][!] Cloud API Provider '{cfg.name}' failed. Trying next provider...[/yellow]")
                logger.warning(f"Cloud API provider '{cfg.name}' (priority {cfg.priority}, model {cfg.api_model}) failed batch request: {e}. Trying next priority provider...")
                last_error = e

        raise RuntimeError(f"All Cloud API providers in pool failed batch request. Last error: {last_error}")
