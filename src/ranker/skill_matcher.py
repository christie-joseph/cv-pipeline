import re
from pathlib import Path
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
    def __init__(self, taxonomy: SkillTaxonomy = None, global_taxonomy: SkillTaxonomy = None):
        self.taxonomy = taxonomy or SkillTaxonomy.load_from_yaml()
        
        project_root = Path(__file__).resolve().parent.parent.parent
        g_path = project_root / "data" / "global_skills.yaml"
        self.global_taxonomy = global_taxonomy or (SkillTaxonomy.load_from_yaml(str(g_path)) if g_path.exists() else None)

        self.alias_map: Dict[str, str] = {}  # alias -> display_name
        self.canonical_to_aliases: Dict[str, Set[str]] = defaultdict(set)
        self.all_skills: List[str] = []

        all_taxonomy_items = []
        if self.taxonomy:
            all_taxonomy_items.extend(self.taxonomy.skills)
        if self.global_taxonomy:
            all_taxonomy_items.extend(self.global_taxonomy.skills)

        for skill in all_taxonomy_items:
            self.all_skills.append(skill.display)
            self.alias_map[skill.display.lower()] = skill.display
            self.canonical_to_aliases[skill.display].add(skill.display.lower())
            for alias in skill.aliases:
                self.alias_map[alias.lower()] = skill.display
                self.canonical_to_aliases[skill.display].add(alias.lower())

    def _build_regex_pattern(self, term: str) -> str:
        """Constructs a boundary-aware regex pattern for skills, accounting for non-alphanumeric terms like c++, c#, .net."""
        escaped = re.escape(term)
        left_b = r"\b" if re.match(r"^\w", term) else r"(?<!\w)"
        right_b = r"\b" if re.search(r"\w$", term) else r"(?!\w)"
        return f"{left_b}{escaped}{right_b}"

    def match(self, jd_skills: List[str], resume_tags: List[str], resume_text: str = "") -> MatchResult:
        matched: List[Tuple[str, str]] = []
        missing: List[str] = []
        seen_matched: Set[str] = set()

        resume_tags_lower = {t.lower().strip() for t in resume_tags if t and len(t.strip()) > 0}
        resume_text_lower = resume_text.lower() if resume_text else ""

        # Filter generic non-technical words
        GENERIC_WORDS = {
            "senior", "core", "develop", "devops", "aws", "framework core",
            "software development", "rest apis", "api", "apis",
            "microsoft", "agile/scrum", "agile", "scrum", "software development lifecycle",
            "sdlc", "enterprise", "deployments", "applications", "platforms",
            "knowledge", "experience", "responsibilities", "qualifications",
            "enterprise applications", "applications team", "development experience", "net asp.net",
            "solutions", "application", "development", "creative", "creative applications",
            "frontend applications", "frontend software", "user experiences", "user experience",
            "build", "building", "modern", "component", "components", "rendering", "client", "frameworks",
            "deploy", "indexing", "enterprise systems", "code principles", "call", "on-call"
        }

        for jd_skill in jd_skills:
            jd_skill_lower = jd_skill.lower().strip()
            if not jd_skill_lower or len(jd_skill_lower) <= 2:
                continue

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

            # Pass 3: Full-Text Resume Scanning
            if not found and resume_text_lower:
                pattern = self._build_regex_pattern(jd_skill_lower)
                if re.search(pattern, resume_text_lower, flags=re.IGNORECASE):
                    canonical = self.alias_map.get(jd_skill_lower, jd_skill.title())
                    if canonical not in seen_matched:
                        matched.append((canonical, "text match"))
                        seen_matched.add(canonical)
                    found = True

            # Pass 4: RapidFuzz Fuzzy Match
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

            # Only append to missing if it is not a generic non-technical stopword
            if not found and jd_skill_lower not in GENERIC_WORDS:
                canonical_missing = self.alias_map.get(jd_skill_lower, jd_skill.title())
                missing.append(canonical_missing)

        # Filter out sub-phrase fragments
        matched_canonical_lower = {m[0].lower() for m in matched}
        all_terms_lower = matched_canonical_lower.union({m.lower() for m in missing})

        filtered_missing = []
        for m in missing:
            m_lower = m.lower().strip()
            if len(m_lower.split()) == 1:
                is_subphrase = any(
                    len(other.split()) > 1 and re.search(r"\b" + re.escape(m_lower) + r"\b", other)
                    for other in all_terms_lower
                    if other != m_lower
                )
                if is_subphrase:
                    continue
            filtered_missing.append(m)

        unique_missing = list(dict.fromkeys(filtered_missing))
        return MatchResult(matched=matched, missing=unique_missing)
