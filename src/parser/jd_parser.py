import re
import spacy
import yake
import numpy as np
from typing import List, Optional
from ..models.jd_profile import JDProfile

NON_SKILL_STOPWORDS = {
    "qualifications", "responsibilities", "requirements", "software engineer",
    "backend software", "senior backend", "looking for", "experience", "role",
    "team", "years", "degree", "field", "communication", "skills", "about",
    "joining", "working", "building", "designing", "optimizing", "collaborating",
    "qualifications & skills", "key responsibilities", "senior software engineer",
    "developer", "architect", "engineer", "software", "backend", "frontend",
    "fullstack", "position", "candidate", "company", "systems", "pipelines"
}


class JDParser:
    def __init__(self, embedding_model=None):
        self.embedding_model = embedding_model
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            spacy.cli.download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
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
        role = None
        for ent in doc.ents:
            if ent.label_ in ["ORG", "PRODUCT"]:
                spacy_kws.append(ent.text.lower())

        # Extract potential role from first line or title
        first_line = text.strip().split("\n")[0]
        if re.search(r"\b(engineer|developer|architect)\b", first_line, re.IGNORECASE):
            role = first_line.strip()

        # 3. Regex for Seniority using word boundaries
        seniority = None
        text_lower = text.lower()
        if re.search(r"\b(senior|sr\.|lead|principal)\b", text_lower):
            seniority = "Senior"
        elif re.search(r"\b(junior|jr\.|entry)\b", text_lower):
            seniority = "Junior"
        elif re.search(r"\b(mid|staff)\b", text_lower):
            seniority = "Mid/Senior"

        # 4. FastEmbed keyword extraction (candidate n-grams cosine vs full JD)
        embedding_kws = []
        if self.embedding_model:
            try:
                words = list(set([token.text.lower() for token in doc if token.is_alpha and not token.is_stop and len(token.text) > 2]))
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

        # Merge & deduplicate keywords
        combined = list(dict.fromkeys(yake_kws + spacy_kws + embedding_kws))
        
        # Filter extracted skills to remove non-skill noise
        skills = [
            kw for kw in combined
            if len(kw) > 2 and kw.lower() not in NON_SKILL_STOPWORDS
        ]

        return JDProfile(
            role=role,
            seniority=seniority,
            skills=skills,
            keywords=combined,
            raw_text=text
        )
