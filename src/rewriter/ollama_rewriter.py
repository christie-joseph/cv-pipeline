import requests
import logging
from typing import List, Optional
from .base import BaseRewriter
from ..models.config import RateLimitConfig
from .rate_limiter import EndpointPacer, ProviderSafetyManager

logger = logging.getLogger(__name__)


class OllamaRewriter(BaseRewriter):
    def __init__(
        self,
        model_name: str = "qwen2.5:1.5b",
        base_url: str = "http://localhost:11434",
        timeout_seconds: int = 5,
        rate_limit_config: Optional[RateLimitConfig] = None
    ):
        self.model_name = model_name
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        self.rate_limit = rate_limit_config or RateLimitConfig()
        
        self.pacer = EndpointPacer()
        self.safety_manager = ProviderSafetyManager(
            default_cooldown_seconds=self.rate_limit.cooldown_seconds,
            failure_threshold=self.rate_limit.circuit_breaker_threshold
        )
        self._checked: bool = False
        self._available: bool = False
        self.active_model: Optional[str] = None

    def is_available(self) -> bool:
        # If circuit breaker is tripped, report unavailable immediately without blocking
        if not self.safety_manager.is_healthy("ollama"):
            return False

        if self._checked:
            return self._available

        self._checked = True
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=2)
            if res.status_code == 200:
                models = [m.get("name") for m in res.json().get("models", [])]
                if not models:
                    self._available = False
                    return False

                # 1. Prefer requested model or matching prefix
                matching = [m for m in models if self.model_name in m]
                if matching:
                    self.active_model = matching[0]
                    self._available = True
                    self.safety_manager.record_success("ollama")
                    return True

                # 2. Fall back to ANY available model currently installed in Ollama
                self.active_model = models[0]
                logger.info(
                    f"Ollama model '{self.model_name}' not found. Falling back to installed model '{self.active_model}'."
                )
                self._available = True
                self.safety_manager.record_success("ollama")
                return True

            self._available = False
            self.safety_manager.record_failure("ollama")
            return False
        except Exception as e:
            logger.debug(f"Ollama connection check failed: {e}")
            self._available = False
            self.safety_manager.record_failure("ollama")
            return False

    def rewrite(self, bullet_text: str, jd_keywords: List[str], prompt_template: str, **kwargs) -> str:
        if not self._checked:
            self.is_available()

        if not self._available or not self.active_model:
            raise RuntimeError("Ollama local service is not available or has no installed models.")

        if not self.safety_manager.is_healthy("ollama"):
            raise RuntimeError("Ollama circuit breaker is active. Service in cooldown.")

        # Pace requests to give GPU/CPU breathing room between bullets
        self.pacer.acquire("ollama", self.rate_limit.ollama_request_interval)

        keywords_str = ", ".join(jd_keywords[:10])
        prompt = (
            "You are a strict, non-hallucinating resume editor. The original bullet point is the single SOURCE OF TRUTH. "
            "Never invent new metrics, tools, responsibilities, or facts. Return only the single reworded bullet.\n\n"
            f"{prompt_template}\n\n"
            f"Original Bullet: {bullet_text}\n"
            f"Keywords: {keywords_str}\n"
            f"Rewritten Bullet:"
        )

        payload = {
            "model": self.active_model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 100}
        }

        try:
            res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout_seconds)
            if res.status_code == 200:
                content = res.json().get("response", "")
                if content:
                    self.safety_manager.record_success("ollama")
                    return content.strip().strip('"')
            
            self.safety_manager.record_failure("ollama")
            raise RuntimeError(f"Ollama returned status code {res.status_code}")
        except Exception as e:
            self.safety_manager.record_failure("ollama")
            raise e
