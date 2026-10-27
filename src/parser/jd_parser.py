import re
import spacy
import logging
from typing import List, Dict, Set
from pathlib import Path
from ..models.jd_profile import JDProfile
from ..models.experience import SkillTaxonomy
from .tech_patterns import TECH_REGEX_PATTERNS, WORK_DOMAIN_PATTERNS

logger = logging.getLogger(__name__)

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
    "science",
    "field",
    "mid",
    "mid-level",
    "technical",

    # Formatting artifacts & generic words
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
                logger.warning("spaCy model 'en_core_web_sm' not found. Attempting download...")
                spacy.cli.download("en_core_web_sm")
                self.nlp = spacy.load("en_core_web_sm")
            except Exception as e:
                logger.warning(f"Could not download or load en_core_web_sm: {e}. Falling back to blank english model.")
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

        # Match common clean target roles
        role_match = re.search(
            r"\b((?:Senior\s+|Staff\s+|Principal\s+|Lead\s+|Junior\s+)?(?:\w+\s+)?(?:Full\s*Stack|Backend|Frontend|Software|Data|DevOps|Cloud|Machine\s+Learning)\s+(?:Engineer|Developer|Architect|Scientist))\b",
            text[:300],
            re.IGNORECASE
        )
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

        # Clean text for parsing: strip markdown headers (lines starting with # or ##)
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

        # 2. Extract Seniority
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

        # 3. Multi-Pass Skill & Keyword Extraction
        # Dictionary to store keyword: (base_weight, count)
        extracted_scores: Dict[str, float] = {}
        text_lower_raw = text.lower()

        # Pass 1: Direct Taxonomy Scanning (User + Global)
        # Deduplicate skills across taxonomies by display name
        taxonomy_by_display: Dict[str, Set[str]] = {}
        all_taxonomy_skills = []
        if self.taxonomy:
            all_taxonomy_skills.extend(self.taxonomy.skills)
        if self.global_taxonomy:
            all_taxonomy_skills.extend(self.global_taxonomy.skills)

        for skill in all_taxonomy_skills:
            if skill.display not in taxonomy_by_display:
                taxonomy_by_display[skill.display] = set()
            taxonomy_by_display[skill.display].add(skill.display.lower())
            for a in skill.aliases:
                taxonomy_by_display[skill.display].add(a.lower())

        for display, terms in taxonomy_by_display.items():
            # Combine terms into a single regex to avoid double-counting if alias and display both match the same span
            sorted_terms = sorted(terms, key=len, reverse=True)
            patterns = []
            for t in sorted_terms:
                left_b = r"\b" if re.match(r"^\w", t) else r"(?<!\w)"
                right_b = r"\b" if re.search(r"\w$", t) else r"(?!\w)"
                patterns.append(f"{left_b}{re.escape(t)}{right_b}")
            combined_pattern = "(?:" + "|".join(patterns) + ")"
            matches = len(re.findall(combined_pattern, text_lower_raw))
            if matches > 0:
                score = round(1.0 * min(2.0, 1.0 + 0.25 * (matches - 1)), 2)
                extracted_scores[display] = score

        # Pass 2: Curated Tech Pattern Regex Library
        for tech_pat in TECH_REGEX_PATTERNS:
            matches = len(tech_pat.pattern.findall(text))
            if matches > 0:
                display = tech_pat.display
                score = round(tech_pat.weight * min(2.0, 1.0 + 0.25 * (matches - 1)), 2)
                extracted_scores[display] = max(extracted_scores.get(display, 0.0), score)


        # Pass 3: Work-Domain Concepts
        for pattern, display, cat, weight in WORK_DOMAIN_PATTERNS:
            matches = len(pattern.findall(text))
            if matches > 0:
                score = round(weight * min(2.0, 1.0 + 0.2 * (matches - 1)), 2)
                extracted_scores[display] = max(extracted_scores.get(display, 0.0), score)

        # Pass 4: spaCy NER Extraction for Unknown Products
        doc = self.nlp(cleaned_text)
        spacy_products = []
        if hasattr(doc, "ents"):
            for ent in doc.ents:
                if ent.label_ == "PRODUCT":
                    spacy_products.append(ent.text.strip())

        for prod in spacy_products:
            prod_clean = re.sub(r"^[^\w]+", "", prod)
            prod_clean = re.sub(r"[\r\n]+", " ", prod_clean).strip()
            prod_lower = prod_clean.lower()
            if (
                len(prod_clean) > 2
                and len(prod_clean.split()) <= 3
                and prod_lower not in NON_SKILL_STOPWORDS
                and prod_lower not in org_entities
            ):
                display = prod_clean.title()
                if display not in extracted_scores:
                    extracted_scores[display] = 0.8

        # 4. Filter & Clean Extracted Skills
        final_scores: Dict[str, float] = {}
        for kw, score in extracted_scores.items():
            kw_clean = re.sub(r"^[^\w]+", "", kw)
            kw_clean = re.sub(r"[\r\n]+", " ", kw_clean).strip()
            kw_lower = kw_clean.lower()
            if (
                len(kw_clean) > 1
                and kw_lower not in NON_SKILL_STOPWORDS
                and kw_lower not in org_entities
                and not kw_lower.startswith(("key responsibilities", "strong proficiency", "hands-on experience", "bs/ms", "experience with", "experience building", "this role", "qualifications"))
            ):
                final_scores[kw_clean] = score

        # Sort skills by score descending
        sorted_skills = sorted(final_scores.keys(), key=lambda k: final_scores[k], reverse=True)

        return JDProfile(
            role=role,
            seniority=seniority,
            skills=sorted_skills,
            keywords=sorted_skills,
            keyword_scores=final_scores,
            raw_text=text
        )
