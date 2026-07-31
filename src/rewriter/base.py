from abc import ABC, abstractmethod
from typing import List


class BaseRewriter(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this rewriter provider is configured and reachable."""
        pass

    @abstractmethod
    def rewrite(self, bullet_text: str, jd_keywords: List[str], prompt_template: str) -> str:
        """Rewrite a bullet point using the specified provider."""
        pass
