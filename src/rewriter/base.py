from abc import ABC, abstractmethod
from typing import List


class BaseRewriter(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this rewriter provider is configured and reachable."""
        pass

    @abstractmethod
    def rewrite(self, bullet_text: str, jd_keywords: List[str], prompt_template: str) -> str:
        """Rewrite a single bullet point using the specified provider."""
        pass

    def rewrite_batch(self, bullets: List[str], jd_keywords: List[str], prompt_template: str) -> List[str]:
        """Rewrite a list of bullet points. Default implementation loops through rewrite()."""
        return [self.rewrite(b, jd_keywords, prompt_template) for b in bullets]
