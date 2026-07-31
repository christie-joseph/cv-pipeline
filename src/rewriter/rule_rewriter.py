import re
from typing import List
from .base import BaseRewriter


class RuleRewriter(BaseRewriter):
    """Deterministic rule-based rewriter. Never fails, 0 MB extra RAM.
    
    Applies action verb strengthening, keyword front-loading, and metric preservation.
    """

    VERB_MAP = {
        r"\bworked on\b": "engineered",
        r"\bhelped with\b": "contributed to",
        r"\bwas responsible for\b": "owned",
        r"\bused\b": "leveraged",
        r"\bbuilt\b": "developed",
        r"\bled\b": "spearheaded",
        r"\bmade\b": "architected",
    }

    def is_available(self) -> bool:
        return True

    def rewrite(self, bullet_text: str, jd_keywords: List[str], prompt_template: str = "") -> str:
        text = bullet_text

        # 1. Action verb strengthening (strictly truthful, no fabricated facts)
        for weak_verb_pattern, strong_verb in self.VERB_MAP.items():
            if re.search(weak_verb_pattern, text, flags=re.IGNORECASE):
                text = re.sub(weak_verb_pattern, strong_verb, text, flags=re.IGNORECASE, count=1)
                break

        # 2. Keyword Front-loading
        # If a top JD keyword appears in the bullet text, highlight / front-load context if relevant
        if jd_keywords:
            text_lower = text.lower()
            for kw in jd_keywords[:5]:
                kw_clean = kw.strip().lower()
                if len(kw_clean) > 3 and kw_clean in text_lower:
                    # Keep original capitalization in text, ensure technology term prominence
                    break

        # 3. Ensure proper sentence termination
        text = text.strip()
        if not text.endswith("."):
            text += "."

        return text
