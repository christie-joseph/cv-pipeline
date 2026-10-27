import re
from typing import List, Dict, Tuple
from dataclasses import dataclass


@dataclass
class JDSection:
    section_type: str  # 'required', 'preferred', 'responsibilities', 'company_intro', 'general'
    weight_multiplier: float
    title: str
    content: str


class SectionSegmenter:
    """
    Segments job descriptions into semantic sections with contextual weighting:
      - Required / Must-Have Qualifications (1.8x)
      - Preferred / Bonus Qualifications (1.2x)
      - Key Responsibilities / Scope (1.0x)
      - General / Context (1.0x)
      - Company Intro / Perks / EEO / Benefits (0.2x)
    """

    # Section patterns with corresponding types and weight multipliers
    SECTION_RULES = [
        (
            re.compile(
                r"\b(?:minimum|required|basic|mandatory)\s+(?:qualifications?|requirements?|skills?|experience)\b|"
                r"\b(?:what\s+you(?:'ll|\s+will)?\s+need|what\s+we(?:'re|\s+are)?\s+looking\s+for|must\s+haves?|requirements?)\b",
                re.IGNORECASE
            ),
            "required",
            1.8
        ),
        (
            re.compile(
                r"\b(?:preferred|desired|bonus|nice\s+to\s+have|plus|stand\s+out)\s*(?:qualifications?|requirements?|skills?|experience)?\b|"
                r"\b(?:what\s+would\s+make\s+you\s+stand\s+out|bonus\s+points?|it(?:'s|\s+is)\s+a\s+plus)\b",
                re.IGNORECASE
            ),
            "preferred",
            1.2
        ),
        (
            re.compile(
                r"\b(?:responsibilities|key\s+responsibilities|what\s+you(?:'ll|\s+will)?\s+do|your\s+role|day\s+to\s+day|scope\s+of\s+work|the\s+role)\b",
                re.IGNORECASE
            ),
            "responsibilities",
            1.0
        ),
        (
            re.compile(
                r"\b(?:about\s+us|about\s+the\s+company|who\s+we\s+are|company\s+overview|benefits|perks|compensation|salary|equal\s+opportunity|why\s+join\s+us|our\s+culture)\b",
                re.IGNORECASE
            ),
            "company_intro",
            0.2
        ),
    ]

    def segment(self, jd_text: str) -> List[JDSection]:
        if not jd_text or not jd_text.strip():
            return []

        lines = jd_text.splitlines()
        sections: List[JDSection] = []
        
        current_title = "Header / Overview"
        current_type = "general"
        current_multiplier = 1.0
        current_lines: List[str] = []

        header_pattern = re.compile(
            r"^(?:#{1,6}\s+|[A-Z0-9\s/&—–\-]{3,50}:?$|\*\*[A-Z0-9\s/&—–\-]{3,50}\*\*:?$)",
            re.MULTILINE
        )

        for line in lines:
            line_stripped = line.strip()
            if not line_stripped:
                current_lines.append(line)
                continue

            # Check if this line looks like a section header
            # E.g. "## Qualifications", "Requirements:", "**What You'll Do**", "Required Skills"
            cleaned_heading = re.sub(r"^#+\s*|\*+|:+$", "", line_stripped).strip()
            
            matched_rule = None
            if len(cleaned_heading.split()) <= 8 and (
                line_stripped.startswith("#") or
                line_stripped.endswith(":") or
                line_stripped.isupper() or
                line_stripped.startswith("**")
            ):
                for regex, sec_type, multiplier in self.SECTION_RULES:
                    if regex.search(cleaned_heading):
                        matched_rule = (cleaned_heading, sec_type, multiplier)
                        break

            if matched_rule:
                # Flush previous section
                if current_lines:
                    content_str = "\n".join(current_lines).strip()
                    if content_str:
                        sections.append(JDSection(
                            section_type=current_type,
                            weight_multiplier=current_multiplier,
                            title=current_title,
                            content=content_str
                        ))
                # Start new section
                current_title, current_type, current_multiplier = matched_rule
                current_lines = []
            else:
                current_lines.append(line)

        # Flush final section
        if current_lines:
            content_str = "\n".join(current_lines).strip()
            if content_str:
                sections.append(JDSection(
                    section_type=current_type,
                    weight_multiplier=current_multiplier,
                    title=current_title,
                    content=content_str
                ))

        if not sections and jd_text.strip():
            sections.append(JDSection(
                section_type="general",
                weight_multiplier=1.0,
                title="Full Job Description",
                content=jd_text.strip()
            ))

        return sections
