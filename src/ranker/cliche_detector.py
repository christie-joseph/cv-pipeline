import re
from typing import List, Dict, Tuple, Optional


class ClicheMatch:
    def __init__(self, phrase: str, category: str, suggestion: str, context: str):
        self.phrase = phrase
        self.category = category  # 'weak_preamble', 'buzzword', 'vague_verb'
        self.suggestion = suggestion
        self.context = context

    def __repr__(self) -> str:
        return f"<ClicheMatch phrase='{self.phrase}' category='{self.category}' suggestion='{self.suggestion}'>"


class ClicheDetector:
    """
    High-performance, deterministic detector for resume anti-patterns, weak preambles,
    empty corporate buzzwords, and vague verbs.
    Provides FAANG-recruiter recommended active replacements.
    """

    # Category 1: Weak responsibility preambles that dilute agency and ownership
    WEAK_PREAMBLE = {
        r"\b(?:was\s+)?responsible for\b": "spearheaded, owned, architected",
        r"\bduties included\b": "executed, delivered, managed",
        r"\bhelped with\b": "facilitated, engineered, co-developed",
        r"\bassisted (?:in|with)\b": "enabled, co-engineered, supported",
        r"\bworked on\b": "developed, engineered, refactored",
        r"\bwas in charge of\b": "directed, led, orchestrated",
        r"\bparticipated in\b": "collaborated on, contributed to",
        r"\btasked with\b": "drove, delivered, executed",
        r"\bhandled daily\b": "streamlined, orchestrated",
        r"\bwas part of\b": "collaborated with, partnered on",
        r"\bworked with\b": "partnered with, integrated with",
    }

    # Category 2: Empty corporate buzzwords with zero technical substance
    BUZZWORDS = {
        r"\bteam player\b": "cross-functional collaborator",
        r"\bhard working\b": "proven high-throughput contributor",
        r"\bself-starter\b": "independently driven engineer",
        r"\bresults-driven\b": "quantifiable metrics track record",
        r"\bdetail-oriented\b": "rigorous test & code quality discipline",
        r"\bthink outside the box\b": "innovative architecture designer",
        r"\bgo-to person\b": "subject matter expert / domain owner",
        r"\bdynamic\b": "adaptable, scalable",
        r"\bsynergy\b": "cross-system integration",
        r"\bpassionate\b": "demonstrated expertise in",
    }

    # Category 3: Low-impact vague verbs that lack technical precision
    VAGUE_VERBS = {
        r"\butilized\b": "leveraged",
        r"\bused\b": "leveraged",
        r"\bdid\b": "implemented, executed",
        r"\bmade\b": "architected, engineered",
        r"\bchanged\b": "refactored, modernized",
        r"\bfixed\b": "resolved, remediated",
    }

    def __init__(self):
        # Precompile patterns for maximum speed
        self._compiled_preambles = [
            (re.compile(pat, re.IGNORECASE), pat, sug)
            for pat, sug in self.WEAK_PREAMBLE.items()
        ]
        self._compiled_buzzwords = [
            (re.compile(pat, re.IGNORECASE), pat, sug)
            for pat, sug in self.BUZZWORDS.items()
        ]
        self._compiled_vague = [
            (re.compile(pat, re.IGNORECASE), pat, sug)
            for pat, sug in self.VAGUE_VERBS.items()
        ]

    def detect(self, bullet_text: str) -> List[ClicheMatch]:
        """Scans a bullet point and returns all detected anti-pattern matches."""
        if not bullet_text or not bullet_text.strip():
            return []

        text = bullet_text.strip()
        matches: List[ClicheMatch] = []

        # 1. Check weak preambles
        for regex, raw_pat, suggestion in self._compiled_preambles:
            found = regex.search(text)
            if found:
                matches.append(
                    ClicheMatch(
                        phrase=found.group(0),
                        category="weak_preamble",
                        suggestion=suggestion,
                        context=text
                    )
                )

        # 2. Check buzzwords
        for regex, raw_pat, suggestion in self._compiled_buzzwords:
            found = regex.search(text)
            if found:
                matches.append(
                    ClicheMatch(
                        phrase=found.group(0),
                        category="buzzword",
                        suggestion=suggestion,
                        context=text
                    )
                )

        # 3. Check vague verbs (especially when opening a sentence)
        for regex, raw_pat, suggestion in self._compiled_vague:
            found = regex.search(text)
            if found:
                matches.append(
                    ClicheMatch(
                        phrase=found.group(0),
                        category="vague_verb",
                        suggestion=suggestion,
                        context=text
                    )
                )

        return matches

    def score_bullet_penalty(self, bullet_text: str) -> float:
        """
        Calculates a penalty deduction (0.0 to 0.4) for detected clichés.
        Useful for integrating with FAANG bullet scorer and ATS rating.
        """
        matches = self.detect(bullet_text)
        if not matches:
            return 0.0

        penalty = 0.0
        for m in matches:
            if m.category == "weak_preamble":
                penalty += 0.15
            elif m.category == "buzzword":
                penalty += 0.20
            elif m.category == "vague_verb":
                penalty += 0.05

        return min(0.5, penalty)
