import requests
import logging
from typing import List, Optional
from .base import BaseRewriter

logger = logging.getLogger(__name__)


class OllamaRewriter(BaseRewriter):
    def __init__(self, model_name: str = "qwen2.5:1.5b", base_url: str = "http://localhost:11434", timeout_seconds: int = 5):
        self.model_name = model_name
        self.base_url = base_url
        self.timeout_seconds = timeout_seconds
        
        self._checked: bool = False
        self._available: bool = False
        self.active_model: Optional[str] = None

    def is_available(self) -> bool:
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
                    return True

                # 2. Fall back to ANY available model currently installed in Ollama
                self.active_model = models[0]
                logger.info(
                    f"Ollama model '{self.model_name}' not found. Falling back to installed model '{self.active_model}'."
                )
                self._available = True
                return True

            self._available = False
            return False
        except Exception as e:
            logger.debug(f"Ollama connection check failed: {e}")
            self._available = False
            return False

    def rewrite(self, bullet_text: str, jd_keywords: List[str], prompt_template: str) -> str:
        if not self._available or not self.active_model:
            raise RuntimeError("Ollama local service is not available or has no installed models.")

        keywords_str = ", ".join(jd_keywords[:10])
        prompt = (
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

        res = requests.post(f"{self.base_url}/api/generate", json=payload, timeout=self.timeout_seconds)
        if res.status_code == 200:
            content = res.json().get("response", "")
            if content:
                return content.strip().strip('"')
        
        raise RuntimeError(f"Ollama returned status code {res.status_code}")
