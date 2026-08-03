import re
import spacy
import numpy as np
from typing import List
from pathlib import Path
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
    "software engineers",
    "senior software engineer",
    "backend software",
    "senior backend",
    "devops engineer",
    "devops engineers",
    "product manager",
    "product managers",
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
    "familiarity",

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
    "familiarity",
    

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
    "software engineering",
    "information technology",
    "software engineers",
    "Devops Engineers",
    "Product Managers",
    "science",
    "field",
    "mid",
    "mid-level",
    "technical",

    # Formatting artifacts
    "github actions\n",
    "query\ngithub actions\n",
    "query"
}


class JDParser:
    def __init__(self, embedding_model=None, taxonomy: SkillTaxonomy = None):
        self.embedding_model = embedding_model
        self.taxonomy = taxonomy or SkillTaxonomy.load_from_yaml()
        
        # Load global skills whitelist
        project_root = Path(__file__).resolve().parent.parent.parent
        self.global_taxonomy = SkillTaxonomy.load_from_yaml(str(project_root / "data" / "global_skills.yaml"))
        
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

    def parse(self, text: str) -> JDProfile:
        if not text or len(text.strip()) == 0:
            return JDProfile(raw_text="")

        # 1. Clean role extraction & company header detection from the first line
        lines = text.strip().split("\n")
        first_line = lines[0]
        org_entities = set()
        role = None
        
        first_line_clean = re.sub(r"^#+\s*", "", first_line)
        if re.search(r"\s*(?:—|–|-|\||:)\s*", first_line_clean):
            company_header = re.split(r"\s*(?:—|–|-|\||:)\s*", first_line_clean)[0].strip()
            if company_header:
                org_entities.add(company_header.lower())
                # Run NER specifically on the company header to extract organization parts
                try:
                    header_doc = self.nlp(company_header)
                    for ent in header_doc.ents:
                        if ent.label_ in ["ORG", "PERSON"]:
                            org_entities.add(ent.text.lower().strip())
                except Exception:
                    pass
                for part in re.split(r"\W+", company_header):
                    if len(part) > 2:
                        org_entities.add(part.lower())

        # Match common clean target roles
        role_match = re.search(r"\b((?:Senior\s+|Staff\s+|Principal\s+|Lead\s+|Junior\s+)?(?:\w+\s+)?(?:Full\s*Stack|Backend|Frontend|Software|Data|DevOps|Cloud|Machine\s+Learning)\s+(?:Engineer|Developer|Architect|Scientist))\b", text[:300], re.IGNORECASE)
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
                phrase_match = re.search(r"\b([A-Z][a-zA-Z\s]{3,30}\s+(?:Engineer|Developer|Architect|Scientist))\b", role)
                if phrase_match:
                    role = phrase_match.group(1).strip()

        # Clean text for parsing: strip other markdown headers (lines starting with # or ##)
        cleaned_lines = []
        for line in lines[1:]:
            line_str = line.strip()
            if line_str.startswith("#"):
                continue
            # Strip leading markdown bullets and list markers (*, -, +)
            line_str = re.sub(r"^[\*\-\+\s\u2022]+", "", line_str)
            # Strip double asterisks (bold markers)
            line_str = line_str.replace("**", "")
            cleaned_lines.append(line_str)
        cleaned_text = "\n".join(cleaned_lines)

        # 2. Extract PROPNs via spaCy as a fallback for unknown skills
        doc = self.nlp(cleaned_text)
        spacy_kws = []
        
        # Pre-compile taxonomy lower-case display and aliases for O(1) checks
        taxonomy_terms = set()
        
        # Combine user and global taxonomy
        all_skills = []
        if self.taxonomy:
            all_skills.extend(self.taxonomy.skills)
        if self.global_taxonomy:
            all_skills.extend(self.global_taxonomy.skills)
            
        for skill in all_skills:
            taxonomy_terms.add(skill.display.lower())
            for a in skill.aliases:
                taxonomy_terms.add(a.lower())

        if hasattr(doc, "ents"):
            for ent in doc.ents:
                if ent.label_ == "PRODUCT":
                    spacy_kws.append(ent.text.lower())

        # 4. Regex for Seniority using word boundaries from the first line or role title
        seniority = None
        seniority_search_text = (role or first_line).lower()
        if re.search(r"\b(principal)\b", seniority_search_text):
            seniority = "Principal"
        elif re.search(r"\b(staff)\b", seniority_search_text):
            seniority = "Staff"
        elif re.search(r"\b(senior|sr\.|lead)\b", seniority_search_text):
            seniority = "Senior"
        elif re.search(r"\b(junior|jr\.|entry)\b", seniority_search_text):
            seniority = "Junior"
        elif re.search(r"\b(mid|mid-level|midlevel|associate)\b", seniority_search_text):
            seniority = "Mid-Level"
        elif re.search(r"\b(engineer|developer|architect|swe|fullstack|backend|frontend|programmer)\b", seniority_search_text):
            seniority = "Mid-Level"



        # Clean extracted keywords: strip punctuation/newlines and drop multi-word noise sentences or company ORG names
        clean_kws = []
        
        # 5. Direct Taxonomy Skill Scanning in raw text (User + Global)
        taxonomy_kws = []
        text_lower_raw = text.lower()
        
        for skill in all_skills:
            # Check display name or aliases using boundary-aware regex
            terms_to_check = [skill.display.lower()] + [a.lower() for a in skill.aliases]
            for term in terms_to_check:
                left_b = r"\b" if re.match(r"^\w", term) else r"(?<!\w)"
                right_b = r"\b" if re.search(r"\w$", term) else r"(?!\w)"
                pattern = f"{left_b}{re.escape(term)}{right_b}"
                if re.search(pattern, text_lower_raw):
                    taxonomy_kws.append(skill.display)
                    break

        for kw in taxonomy_kws + spacy_kws:
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
