import re
import spacy
from typing import List, Set, Dict, Optional

# Non-technical adjectives and nouns to avoid extracting generic filler as skills
GENERIC_MODIFIERS = {
    "strong", "good", "excellent", "proven", "demonstrated", "prior", "relevant",
    "successful", "hands-on", "deep", "solid", "broad", "comprehensive", "effective",
    "key", "core", "great", "high", "low", "fast", "new", "current", "best",
    "various", "multiple", "several", "ideal", "preferred", "minimum", "basic"
}

DISALLOWED_HEADS = {
    # Time / Duration
    "year", "years", "month", "months", "week", "weeks", "day", "days",
    # Roles, People & Orgs
    "engineer", "engineers", "developer", "developers", "architect", "architects",
    "lead", "leads", "manager", "managers", "specialist", "specialists",
    "candidate", "candidates", "person", "people", "employee", "employees",
    "team", "teams", "company", "companies", "role", "roles", "position", "positions",
    # Education
    "degree", "degrees", "field", "fields", "discipline", "disciplines", "major", "majors",
    # Experience / Meta
    "experience", "knowledge", "skill", "skills", "ability", "background",
    "understanding", "proficiency", "familiarity", "expertise", "environment",
    "responsibility", "responsibilities", "qualification", "qualifications",
    "duty", "duties", "requirement", "requirements", "mindset", "attitude", "passion",
    "track record"
}


class NounChunkExtractor:
    """
    Extracts high-value technical compound phrases using spaCy linguistic parsing:
    e.g. 'distributed caching', 'event-driven architecture', 'load balancing'.
    Filters out boilerplate and non-technical noise.
    """

    def __init__(self, nlp=None):
        self.nlp = nlp

    def extract_technical_phrases(self, text: str, non_skill_stopwords: Set[str]) -> Dict[str, int]:
        if not self.nlp or not text:
            return {}

        doc = self.nlp(text)
        phrase_counts: Dict[str, int] = {}

        for chunk in doc.noun_chunks:
            # Clean chunk text
            clean_chunk = chunk.text.strip()
            # Strip non-word prefix symbols (bullets, pluses, dashes)
            clean_chunk = re.sub(r"^[^\w]+", "", clean_chunk).strip()
            # Strip leading determiners/articles (the, a, an, our, their)
            clean_chunk = re.sub(r"^(?:the|a|an|our|your|their|its|this|these|all|any)\s+", "", clean_chunk, flags=re.IGNORECASE).strip()
            clean_chunk = re.sub(r"^[^\w]+", "", clean_chunk).strip()
            
            # Words in the chunk
            words = clean_chunk.split()
            if len(words) < 2 or len(words) > 4:
                continue

            # Skip any chunk containing digits (e.g. '3+ years', '5 years')
            if any(c.isdigit() for c in clean_chunk):
                continue

            chunk_lower = clean_chunk.lower()
            
            # Skip if explicitly in stopwords
            if chunk_lower in non_skill_stopwords:
                continue

            first_word = words[0].lower()
            last_word = words[-1].lower()

            # Skip if starts or ends with disallowed heads / metadata
            if last_word in DISALLOWED_HEADS or first_word in DISALLOWED_HEADS:
                continue

            # Skip if starts with generic modifier ("strong experience", "solid knowledge")
            if first_word in GENERIC_MODIFIERS and len(words) == 2:
                continue

            # Ensure chunk contains nouns/proper nouns
            chunk_doc = self.nlp(clean_chunk)
            pos_tags = [t.pos_ for t in chunk_doc]
            
            # Must contain at least one NOUN or PROPN
            if not any(pos in ["NOUN", "PROPN"] for pos in pos_tags):
                continue

            # Must not contain verbs, pronouns, or punctuation
            if any(pos in ["VERB", "PRON", "PUNCT"] for pos in pos_tags):
                continue

            display_term = clean_chunk.title()
            phrase_counts[display_term] = phrase_counts.get(display_term, 0) + 1

        return phrase_counts
