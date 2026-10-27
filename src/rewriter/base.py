from abc import ABC, abstractmethod
from typing import List, Optional, Dict


class BaseRewriter(ABC):
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this rewriter provider is configured and reachable."""
        pass

    @abstractmethod
    def rewrite(
        self,
        bullet_text: str,
        jd_keywords: List[str],
        prompt_template: str,
        bullet_tags: Optional[List[str]] = None,
        keyword_scores: Optional[Dict[str, float]] = None
    ) -> str:
        """Rewrite a single bullet point using the specified provider."""
        pass

    def rewrite_batch(
        self,
        bullets: List[str],
        jd_keywords: List[str],
        prompt_template: str,
        bullets_tags: Optional[List[List[str]]] = None,
        keyword_scores: Optional[Dict[str, float]] = None
    ) -> List[str]:
        """Rewrite a list of bullet points. Default implementation loops through rewrite()."""
        results = []
        for i, b in enumerate(bullets):
            tags = bullets_tags[i] if bullets_tags and i < len(bullets_tags) else None
            results.append(self.rewrite(b, jd_keywords, prompt_template, bullet_tags=tags, keyword_scores=keyword_scores))
        return results
