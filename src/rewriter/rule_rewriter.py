import re
from typing import List, Optional, Dict
from pathlib import Path
from .base import BaseRewriter
from ..models.experience import SkillTaxonomy
from .keyword_injector import KeywordInjector
from .sentence_restructurer import SentenceRestructurer


class RuleRewriter(BaseRewriter):
    """
    Upgraded Deterministic Rule-Based Rewriter.
    Applies:
      1. Passive-to-active transformations
      2. Weak preamble & filler stripping
      3. Extensive multi-verb strengthening (25+ patterns)
      4. Impact-first sentence reordering
      5. Safe keyword canonicalization and verified context injection
    """

    VERB_MAP = {
        r"\bworked on\b": "engineered",
        r"\bhelped with\b": "contributed to",
        r"\bwas responsible for\b": "owned",
        r"\bwas in charge of\b": "spearheaded",
        r"\bused\b": "leveraged",
        r"\butilized\b": "leveraged",
        r"\bbuilt\b": "developed",
        r"\bled\b": "spearheaded",
        r"\bmade\b": "architected",
        r"\bwas part of\b": "collaborated on",
        r"\bparticipated in\b": "contributed to",
        r"\bassisted with\b": "enabled",
        r"\bassisted in\b": "enabled",
        r"\bworked with\b": "partnered with",
        r"\bhandled\b": "orchestrated",
        r"\bdid\b": "executed",
        r"\bwrote\b": "authored",
        r"\bset up\b": "configured",
        r"\bfixed\b": "resolved",
        r"\btested\b": "validated",
        r"\bmanaged\b": "orchestrated",
        r"\bcoordinated\b": "spearheaded",
        r"\bsupported\b": "enabled",
        r"\bhelped\b": "facilitated",
        r"\bstarted\b": "established",
        r"\bchanged\b": "transformed",
        r"\bupdated\b": "modernized",
        r"\bmaintained\b": "optimized",
        r"\baided\b": "facilitated",
    }

    def __init__(self, taxonomy: Optional[SkillTaxonomy] = None, global_taxonomy: Optional[SkillTaxonomy] = None):
        if taxonomy is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            skills_path = project_root / "data" / "skills.yaml"
            if skills_path.exists():
                taxonomy = SkillTaxonomy.load_from_yaml(str(skills_path))
        if global_taxonomy is None:
            project_root = Path(__file__).resolve().parent.parent.parent
            g_skills_path = project_root / "data" / "global_skills.yaml"
            if g_skills_path.exists():
                global_taxonomy = SkillTaxonomy.load_from_yaml(str(g_skills_path))

        self.taxonomy = taxonomy
        self.global_taxonomy = global_taxonomy
        self.injector = KeywordInjector(self.taxonomy, self.global_taxonomy)
        self.restructurer = SentenceRestructurer()

    def is_available(self) -> bool:
        return True

    def rewrite(
        self,
        bullet_text: str,
        jd_keywords: List[str],
        prompt_template: str = "",
        bullet_tags: Optional[List[str]] = None,
        keyword_scores: Optional[Dict[str, float]] = None
    ) -> str:
        text = bullet_text.strip()
        if not text:
            return ""

        # Step 1: Strip filler preamble (e.g. "I was tasked with...")
        text = self.restructurer.strip_filler(text)

        # Step 2: Convert passive constructs to active
        text = self.restructurer.passive_to_active(text)

        # Step 3: Action verb strengthening (replace all matching weak verbs)
        for weak_verb_pattern, strong_verb in self.VERB_MAP.items():
            if re.search(weak_verb_pattern, text, flags=re.IGNORECASE):
                text = re.sub(weak_verb_pattern, strong_verb, text, flags=re.IGNORECASE, count=1)

        # Step 4: Impact-first reordering (e.g. moving metric clause forward)
        text = self.restructurer.impact_first(text)

        # Step 5: Safe keyword canonicalization and contextual injection from tags
        if jd_keywords:
            text, _ = self.injector.inject(
                bullet_text=text,
                bullet_tags=bullet_tags or [],
                jd_keywords=jd_keywords,
                keyword_scores=keyword_scores or {}
            )

        # Step 6: Clean capitalization and sentence termination
        text = text.strip()
        if text:
            text = text[0].upper() + text[1:]
        if not text.endswith("."):
            text += "."

        return text
