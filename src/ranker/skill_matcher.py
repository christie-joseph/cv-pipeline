import re
from typing import List, Dict, Set, Tuple
from collections import defaultdict
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
        self.canonical_to_aliases: Dict[str, Set[str]] = defaultdict(set)
        self.all_skills: List[str] = []

        for skill in self.taxonomy.skills:
            self.all_skills.append(skill.display)
            self.alias_map[skill.display.lower()] = skill.display
            self.canonical_to_aliases[skill.display].add(skill.display.lower())
            for alias in skill.aliases:
                self.alias_map[alias.lower()] = skill.display
                self.canonical_to_aliases[skill.display].add(alias.lower())

    def _build_regex_pattern(self, term: str) -> str:
        """Constructs a boundary-aware regex pattern for skills, accounting for non-alphanumeric terms like c++, c#, .net."""
        escaped = re.escape(term)
        # Left boundary: \b if starts with word character, else (?<!\w)
        left_b = r"\b" if re.match(r"^\w", term) else r"(?<!\w)"
        # Right boundary: \b if ends with word character, else (?!\w)
        right_b = r"\b" if re.search(r"\w$", term) else r"(?!\w)"
        return f"{left_b}{escaped}{right_b}"

    def match(self, jd_skills: List[str], resume_tags: List[str]) -> MatchResult:
        matched: List[Tuple[str, str]] = []
        missing: List[str] = []
        seen_matched: Set[str] = set()

        # Filter out empty or whitespace-only tags to prevent zero-length regex false positives
        resume_tags_lower = {t.lower().strip() for t in resume_tags if t and len(t.strip()) > 0}

        for jd_skill in jd_skills:
            jd_skill_lower = jd_skill.lower()
            found = False

            # Pass 1: Canonical Alias Match (O(1) lookups via inverted index)
            if jd_skill_lower in self.alias_map:
                canonical = self.alias_map[jd_skill_lower]
                aliases_for_canonical = self.canonical_to_aliases[canonical]
                if any(alias in resume_tags_lower for alias in aliases_for_canonical):
                    if canonical not in seen_matched:
                        matched.append((canonical, "alias match"))
                        seen_matched.add(canonical)
                    found = True

            # Pass 2: Boundary-aware Tag Match (handles C++, C#, .Net, etc.)
            if not found:
                for tag in resume_tags_lower:
                    pattern = self._build_regex_pattern(tag)
                    if re.search(pattern, jd_skill_lower, flags=re.IGNORECASE):
                        canonical = self.alias_map.get(jd_skill_lower, jd_skill.title())
                        if canonical not in seen_matched:
                            matched.append((canonical, "exact match"))
                            seen_matched.add(canonical)
                        found = True
                        break

            # Pass 3: RapidFuzz Fuzzy Match (for longer terms)
            if not found and len(jd_skill_lower) > 2:
                for tag in resume_tags_lower:
                    if len(tag) > 2:
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

        # Preserve deterministic insertion order for missing skills
        unique_missing = list(dict.fromkeys(missing))
        return MatchResult(matched=matched, missing=unique_missing)
