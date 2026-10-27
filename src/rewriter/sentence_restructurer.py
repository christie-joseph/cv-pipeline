import re

class SentenceRestructurer:
    """Restructures bullet points: passive-to-active conversion, impact-first reordering, and filler elimination."""

    FILLER_PREFIXES = [
        r"^in this role,?\s*(?:i\s*)?",
        r"^as part of my responsibilities,?\s*(?:i\s*)?",
        r"^i was tasked with\s*",
        r"^i was responsible for\s*",
        r"^was responsible for\s*",
        r"^responsible for\s*",
        r"^helped the team to\s*",
        r"^assisted in\s*",
    ]

    PASSIVE_TRANSFORMS = [
        (r"\bwas implemented by me\b", "implemented"),
        (r"\bwas designed and built\b", "designed and built"),
        (r"\bwas responsible for leading\b", "spearheaded"),
        (r"\bwas responsible for developing\b", "engineered"),
        (r"\bwas responsible for building\b", "developed"),
        (r"\bwas responsible for creating\b", "created"),
        (r"\bhelped to build\b", "engineered"),
        (r"\bhelped to develop\b", "developed"),
        (r"\bworked with the team to\b", "collaborated to"),
    ]

    IMPACT_PATTERNS = [
        r"(?:,\s*)?(reducing\s+[^,.]*(?:latency|downtime|costs?|time|errors?)[^,.]*)",
        r"(?:,\s*)?(increasing\s+[^,.]*(?:throughput|revenue|coverage|performance|efficiency)[^,.]*)",
        r"(?:,\s*)?(improving\s+[^,.]*(?:performance|speed|reliability|test coverage)[^,.]*)",
        r"(?:,\s*)?(achieving\s+[^,.]*(?:\d+%|\d+x)[^,.]*)",
    ]

    def strip_filler(self, text: str) -> str:
        s = text.strip()
        for pat in self.FILLER_PREFIXES:
            match = re.search(pat, s, flags=re.IGNORECASE)
            if match:
                s = s[match.end():].strip()
                break
        if s:
            s = s[0].upper() + s[1:]
        return s

    def passive_to_active(self, text: str) -> str:
        s = text
        for pat, repl in self.PASSIVE_TRANSFORMS:
            s = re.sub(pat, repl, s, flags=re.IGNORECASE)
        return s

    def impact_first(self, text: str) -> str:
        """If bullet ends with impact clause like 'reducing latency by 40%', restructures if suitable."""
        s = text.rstrip(".")
        for pat in self.IMPACT_PATTERNS:
            match = re.search(pat + r"$", s, flags=re.IGNORECASE)
            if match:
                impact_clause = match.group(1).strip()
                # Turn 'reducing latency by 40%' into 'Reduced latency by 40%'
                impact_words = impact_clause.split()
                first_word = impact_words[0].lower()
                verb_map = {
                    "reducing": "Reduced",
                    "increasing": "Increased",
                    "improving": "Improved",
                    "achieving": "Achieved",
                    "cutting": "Cut",
                }
                past_verb = verb_map.get(first_word, first_word.capitalize())
                rest_of_impact = " ".join(impact_words[1:])

                main_action = s[:match.start()].strip().rstrip(",")
                if main_action:
                    # e.g. "Reduced latency by 40% by optimizing query pipelines"
                    # lowercase first word of main action
                    words = main_action.split()
                    if words:
                        words[0] = words[0].lower()
                    restructured = f"{past_verb} {rest_of_impact} through { ' '.join(words) }"
                    return restructured[0].upper() + restructured[1:]
        return text
