import re
from typing import List, Dict, Set, Tuple
from rapidfuzz import fuzz
from ..models.experience import SkillTaxonomy


class MatchResult:
    def __init__(self, matched: List[Tuple[str, str]], missing: List[str]):
        self.matched = matched
        self.missing = missing

    @property
    def match_percentage(self) -> float:
        total = len(self.matched) + len(self.missing)
        if total == 0:
            return 100.0
        return round((len(self.matched) / total) * 100, 1)


class SkillMatcher:
    def __init__(self, taxonomy: SkillTaxonomy = None):
        self.taxonomy = taxonomy or SkillTaxonomy.load_from_yaml()
        self.alias_map: Dict[str, str] = {}  # alias -> display_name
        self.all_skills: List[str] = []

        for skill in self.taxonomy.skills:
            self.all_skills.append(skill.display)
            self.alias_map[skill.display.lower()] = skill.display
            for alias in skill.aliases:
                self.alias_map[alias.lower()] = skill.display

    def match(self, jd_skills: List[str], resume_tags: List[str]) -> MatchResult:
        matched: List[Tuple[str, str]] = []
        missing: List[str] = []
        seen_matched: Set[str] = set()

        resume_tags_lower = {t.lower() for t in resume_tags}

        for jd_skill in jd_skills:
            jd_skill_lower = jd_skill.lower()
            found = False

            # Pass 1: Canonical Alias Match
            if jd_skill_lower in self.alias_map:
                canonical = self.alias_map[jd_skill_lower]
                if any(alias in resume_tags_lower for alias in self.alias_map if self.alias_map[alias] == canonical):
                    if canonical not in seen_matched:
                        matched.append((canonical, "alias match"))
                        seen_matched.add(canonical)
                    found = True

            # Pass 2: Word Boundary / Exact Tag Match
            if not found:
                for tag in resume_tags_lower:
                    # Match full word boundaries to prevent 'java' matching 'javascript' or 'c' matching 'caching'
                    pattern = r"\b" + re.escape(tag) + r"\b"
                    if re.search(pattern, jd_skill_lower):
                        canonical = self.alias_map.get(jd_skill_lower, jd_skill.title())
                        if canonical not in seen_matched:
                            matched.append((canonical, "exact match"))
                            seen_matched.add(canonical)
                        found = True
                        break

            # Pass 3: RapidFuzz Fuzzy Match (for longer terms)
            if not found and len(jd_skill_lower) > 3:
                for tag in resume_tags_lower:
                    if len(tag) > 3:
                        score = fuzz.ratio(jd_skill_lower, tag)
                        if score >= 85:
                            canonical = self.alias_map.get(jd_skill_lower, jd_skill.title())
                            if canonical not in seen_matched:
                                matched.append((canonical, f"fuzzy match ({int(score)}%)"))
                                seen_matched.add(canonical)
                            found = True
                            break

            if not found and len(jd_skill) > 2:
                missing.append(jd_skill.title())

        return MatchResult(matched=matched, missing=list(set(missing)))
