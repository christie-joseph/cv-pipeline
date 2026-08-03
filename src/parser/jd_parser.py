import re
import spacy
import yake
import numpy as np
from typing import List
from ..models.jd_profile import JDProfile

from ..models.experience import SkillTaxonomy

NON_SKILL_STOPWORDS = {
    # JD sections
    "qualifications",
    "responsibilities",
    "requirements",
    "qualifications & skills",
    "key responsibilities",
    "preferred qualifications",
    "required qualifications",
    "minimum qualifications",
    "key",
    "skills",
    "experiences",

    # Role boilerplate
    "software engineer",
    "senior software engineer",
    "backend software",
    "senior backend",
    "developer",
    "engineer",
    "software",
    "position",
    "candidate",
    "ideal candidate",
    "the ideal candidate",
    "looking for",
    "about the role",
    "about the company",
    "the role",
    "role",
    "you",
    "performance",

    # Experience language
    "experience",
    "experience with",
    "experience in",
    "years of experience",
    "strong experience",
    "hands-on experience",
    "hands on experience",
    "working knowledge",
    "knowledge of",
    "familiarity with",
    "proficiency",

    # Generic verbs
    "building",
    "build",
    "designing",
    "design",
    "developing",
    "develop",
    "implementing",
    "implement",
    "optimizing",
    "optimize",
    "collaborating",
    "collaborate",
    "working",
    "joining",
    "troubleshoot",
    "troubleshoot production issues",
    "aggregating",

    # Generic soft skills
    "communication",
    "excellent communication",
    "written communication",
    "verbal communication",
    "leadership",

    # Generic phrases
    "responsible for",
    "responsibilities include",
    "ability to",
    "capable of",
    "passion for",
    "interest in",
    "join us",
    "our team",
    "our company",
    "we are",
    "you will",
    "legacy applications",
    "application performance",
    "containerized applications",
    "application reliability",
    "scalability",
    "engineering teams",
    "code reviews",
    "software delivery",
    "agile/scrum methodologies",

    # Academic noise
    "degree",
    "computer science",
    "science",
    "field",

    # Formatting artifacts
    "github actions\n",
    "query\ngithub actions\n",
    "query"
}


class JDParser:
    def __init__(self, embedding_model=None, taxonomy: SkillTaxonomy = None):
        self.embedding_model = embedding_model
        self.taxonomy = taxonomy or SkillTaxonomy.load_from_yaml()
        self.nlp = None
        
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            try:
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
            except Exception:
                # Fallback to blank model if offline and download fails
                self.nlp = spacy.blank("en")
        
        self.kw_extractor = yake.KeywordExtractor(
            lan="en", n=2, dedupLim=0.8, top=20, features=None
        )

    def parse(self, text: str) -> JDProfile:
        if not text or len(text.strip()) == 0:
            return JDProfile(raw_text="")

        # 1. YAKE statistical keywords
        yake_kws = [kw for kw, score in self.kw_extractor.extract_keywords(text)]

        # 2. spaCy NER & Noun Chunks
        doc = self.nlp(text)
        spacy_kws = []
        org_entities = set()
        role = None
        
        # Extract Proper Nouns (often technical tools/skills like Redux, GraphQL, Vite, Jest)
        for token in doc:
            if token.pos_ == "PROPN" and len(token.text) > 2 and token.text.lower() not in NON_SKILL_STOPWORDS:
                spacy_kws.append(token.text.lower())
                
        # Extract short noun chunks only if they are single words or contain technical terms/PROPNs
        if hasattr(doc, "noun_chunks"):
            for chunk in doc.noun_chunks:
                chunk_text = chunk.text.strip()
                words = chunk_text.split()
                # Exclude long action/responsibility phrases
                if 1 <= len(words) <= 2:
                    # Skip chunks starting with verbs or stop words
                    if not chunk[0].pos_ in ["VERB", "AUX"] and chunk_text.lower() not in NON_SKILL_STOPWORDS:
                        spacy_kws.append(chunk_text.lower())

        if hasattr(doc, "ents"):
            for ent in doc.ents:
                if ent.label_ == "PRODUCT":
                    spacy_kws.append(ent.text.lower())

        # Clean role extraction & company header detection
        first_line = text.strip().split("\n")[0]
        if "—" in first_line or " - " in first_line:
            company_header = re.split(r"\s*(?:—|-)\s*", first_line)[0].strip().lower()
            if company_header:
                org_entities.add(company_header)
                for part in re.split(r"\W+", company_header):
                    if len(part) > 2:
                        org_entities.add(part)
        # Match common clean target roles
        role_match = re.search(r"\b((?:Senior\s+|Staff\s+|Principal\s+|Lead\s+|Junior\s+)?(?:Full\s*Stack|Backend|Frontend|Software|Data|DevOps|Cloud|Machine\s+Learning)\s+(?:Engineer|Developer|Architect|Scientist))\b", text[:300], re.IGNORECASE)
        if role_match:
            role = role_match.group(1).title()
        elif re.search(r"\b(engineer|developer|architect|lead|analyst)\b", first_line, re.IGNORECASE):
            parts = re.split(r"\s*(?:\||-|–|\bat\b)\s*", first_line, flags=re.IGNORECASE)
            role_part = parts[0]
            for part in parts:
                if re.search(r"\b(engineer|developer|architect|lead|analyst)\b", part, re.IGNORECASE):
                    role_part = part
                    break
            role = re.sub(r"[^\w\s,]", "", role_part).strip()
            if len(role.split()) > 5:
                # If parsed role is a long sentence, extract the concise title phrase
                phrase_match = re.search(r"\b([A-Z][a-zA-Z\s]{3,30}\s+(?:Engineer|Developer|Architect|Scientist))\b", role)
                if phrase_match:
                    role = phrase_match.group(1).strip()

        # 3. Regex for Seniority using word boundaries
        seniority = None
        text_lower = text.lower()
        if re.search(r"\b(principal)\b", text_lower):
            seniority = "Principal"
        elif re.search(r"\b(staff)\b", text_lower):
            seniority = "Staff"
        elif re.search(r"\b(senior|sr\.|lead)\b", text_lower):
            seniority = "Senior"
        elif re.search(r"\b(junior|jr\.|entry)\b", text_lower):
            seniority = "Junior"
        elif re.search(r"\b(mid|mid-level|midlevel|associate)\b", text_lower):
            seniority = "Mid-Level"
        elif re.search(r"\b(engineer|developer|architect|swe|fullstack|backend|frontend|programmer)\b", text_lower):
            seniority = "Mid-Level"

        # 4. FastEmbed keyword extraction (candidate n-grams cosine vs full JD)
        embedding_kws = []
        if self.embedding_model:
            try:
                # Retain document order (not alphabetical) using dict.fromkeys to avoid keyphrase truncation
                raw_words = [token.text.lower() for token in doc if token.is_alpha and not token.is_stop and len(token.text) > 2]
                words = list(dict.fromkeys(raw_words))
                if words:
                    jd_emb = list(self.embedding_model.embed([text]))[0]
                    word_embs = list(self.embedding_model.embed(words[:50]))
                    
                    sims = [
                        np.dot(jd_emb, w_emb) / (np.linalg.norm(jd_emb) * np.linalg.norm(w_emb) + 1e-9)
                        for w_emb in word_embs
                    ]
                    top_indices = np.argsort(sims)[-15:]
                    embedding_kws = [words[i] for i in reversed(top_indices)]
            except Exception:
                pass

        # Clean extracted keywords: strip punctuation/newlines and drop multi-word noise sentences or company ORG names
        clean_kws = []
        
        # 5. Direct Taxonomy Skill Scanning in raw text
        taxonomy_kws = []
        text_lower_raw = text.lower()
        if self.taxonomy:
            for skill in self.taxonomy.skills:
                # Check display name or aliases using boundary-aware regex
                terms_to_check = [skill.display.lower()] + [a.lower() for a in skill.aliases]
                for term in terms_to_check:
                    left_b = r"\b" if re.match(r"^\w", term) else r"(?<!\w)"
                    right_b = r"\b" if re.search(r"\w$", term) else r"(?!\w)"
                    pattern = f"{left_b}{re.escape(term)}{right_b}"
                    if re.search(pattern, text_lower_raw):
                        taxonomy_kws.append(skill.display)
                        break

        for kw in taxonomy_kws + yake_kws + spacy_kws + embedding_kws:
            # Strip leading markdown symbols (*, **, -, #) and whitespace
            kw_clean = re.sub(r"^[^\w]+", "", kw)
            kw_clean = re.sub(r"[\r\n]+", " ", kw_clean).strip()
            
            # Filter out section headers, conversational phrases, long phrases
            kw_lower = kw_clean.lower()
            kw_words = set(re.split(r"\W+", kw_lower))
            if (
                len(kw_clean) > 2 
                and len(kw_clean.split()) <= 3 
                and kw_lower not in NON_SKILL_STOPWORDS
                and kw_lower not in org_entities
                and not (kw_words & org_entities)
                and not kw_lower.startswith(("key responsibilities", "strong proficiency", "hands-on experience", "bs/ms", "experience with", "experience building", "this role", "qualifications"))
            ):
                clean_kws.append(kw_clean)

        # Merge & deduplicate keywords deterministically
        combined = list(dict.fromkeys(clean_kws))
        skills = combined

        return JDProfile(
            role=role,
            seniority=seniority,
            skills=skills,
            keywords=combined,
            raw_text=text
        )
