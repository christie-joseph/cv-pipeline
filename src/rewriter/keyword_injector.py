import re
from typing import List, Dict, Tuple, Optional
from ..models.experience import SkillTaxonomy

class KeywordInjector:
    """Surfaces canonical skills and safely injects verified keywords from bullet tags."""

    def __init__(self, taxonomy: Optional[SkillTaxonomy] = None, global_taxonomy: Optional[SkillTaxonomy] = None):
        self.taxonomy = taxonomy
        self.global_taxonomy = global_taxonomy
        self.alias_to_canonical: Dict[str, str] = {}

        all_skills = []
        if self.taxonomy:
            all_skills.extend(self.taxonomy.skills)
        if self.global_taxonomy:
            all_skills.extend(self.global_taxonomy.skills)

        for s in all_skills:
            self.alias_to_canonical[s.display.lower()] = s.display
            for a in s.aliases:
                self.alias_to_canonical[a.lower()] = s.display

    def inject(
        self,
        bullet_text: str,
        bullet_tags: List[str],
        jd_keywords: List[str],
        keyword_scores: Dict[str, float]
    ) -> Tuple[str, List[str]]:
        """
        1. Normalizes alias mentions in the bullet to canonical names if they match high-value JD keywords.
        2. If bullet_tags contains a high-value JD keyword not present in the text, appends it safely.
        """
        text = bullet_text
        injected = []
        jd_kw_lower = {k.lower(): k for k in jd_keywords}

        # 1. Alias canonicalization
        for alias, canonical in self.alias_to_canonical.items():
            if len(alias) <= 2:
                continue
            if canonical.lower() in jd_kw_lower:
                pattern = r"\b" + re.escape(alias) + r"\b"
                if re.search(pattern, text, flags=re.IGNORECASE) and not re.search(r"\b" + re.escape(canonical) + r"\b", text, flags=re.IGNORECASE):
                    text = re.sub(pattern, canonical, text, count=1, flags=re.IGNORECASE)
                    injected.append(canonical)

        # 2. Tag-based explicit tech context append if strongly scored
        text_lower = text.lower()
        missing_high_priority_tags = []
        for tag in bullet_tags:
            tag_clean = tag.strip()
            canonical = self.alias_to_canonical.get(tag_clean.lower(), tag_clean)
            if canonical.lower() in jd_kw_lower and not re.search(r"\b" + re.escape(canonical.lower()) + r"\b", text_lower):
                score = keyword_scores.get(canonical, keyword_scores.get(tag_clean, 0.0))
                if score >= 0.8:
                    missing_high_priority_tags.append(canonical)

        if missing_high_priority_tags:
            # Safely append without breaking sentence flow
            added_skills = ", ".join(dict.fromkeys(missing_high_priority_tags[:2]))
            text = text.rstrip(".")
            text = f"{text} leveraging {added_skills}."
            injected.extend(missing_high_priority_tags[:2])

        return text, injected
