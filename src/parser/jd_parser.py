import re
import spacy
import logging
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
from collections import defaultdict

from ..models.jd_profile import JDProfile
from ..models.experience import SkillTaxonomy
from .tech_patterns import TECH_REGEX_PATTERNS, WORK_DOMAIN_PATTERNS
from .section_segmenter import SectionSegmenter, JDSection
from .noun_chunk_extractor import NounChunkExtractor

logger = logging.getLogger(__name__)

NON_SKILL_STOPWORDS = {
    # JD sections & boilerplate
    "qualifications",
    "responsibilities",
    "requirements",
    "qualifications & skills",
    "key responsibilities",
    "preferred qualifications",
    "required qualifications",
    "minimum qualifications",
    "basic qualifications",
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
    "year",
    "years",
    "team",
    "teams",
    "candidate",
    "candidates",
    "position",
    "positions",

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

    # Generic verbs & actions
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

    # Academic & general noise
    "degree",
    "computer science",
    "software engineering",
    "information technology",
    "science",
    "field",
    "mid",
    "mid-level",
    "technical",
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

        self.segmenter = SectionSegmenter()
        self.noun_extractor = NounChunkExtractor(self.nlp)

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

        # 3. Section Segmentation (Requirements vs Preferred vs Scope vs Intro)
        sections = self.segmenter.segment(text)

        # 4. Multi-Pass Skill & Keyword Extraction across Sections
        extracted_scores: Dict[str, float] = {}
        skill_sections: Dict[str, Set[str]] = defaultdict(set)

        # Build taxonomy regex mapping
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

        compiled_taxonomy_patterns = {}
        for display, terms in taxonomy_by_display.items():
            sorted_terms = sorted(terms, key=len, reverse=True)
            patterns = []
            for t in sorted_terms:
                left_b = r"\b" if re.match(r"^\w", t) else r"(?<!\w)"
                right_b = r"\b" if re.search(r"\w$", t) else r"(?!\w)"
                patterns.append(f"{left_b}{re.escape(t)}{right_b}")
            compiled_taxonomy_patterns[display] = re.compile("(?:" + "|".join(patterns) + ")", re.IGNORECASE)

        for sec in sections:
            sec_text = sec.content
            sec_text_lower = sec_text.lower()
            sec_type = sec.section_type
            multiplier = sec.weight_multiplier

            # Pass 1: Direct Taxonomy Scanning with Section Weighting
            for display, pattern in compiled_taxonomy_patterns.items():
                matches = len(pattern.findall(sec_text_lower))
                if matches > 0:
                    base_val = 1.0 * min(2.0, 1.0 + 0.25 * (matches - 1))
                    weighted_val = round(base_val * multiplier, 2)
                    extracted_scores[display] = extracted_scores.get(display, 0.0) + weighted_val
                    skill_sections[display].add(sec_type)

            # Pass 2: Curated Tech Pattern Regex Library
            for tech_pat in TECH_REGEX_PATTERNS:
                matches = len(tech_pat.pattern.findall(sec_text))
                if matches > 0:
                    display = tech_pat.display
                    base_val = tech_pat.weight * min(2.0, 1.0 + 0.25 * (matches - 1))
                    weighted_val = round(base_val * multiplier, 2)
                    extracted_scores[display] = extracted_scores.get(display, 0.0) + weighted_val
                    skill_sections[display].add(sec_type)

            # Pass 3: Work-Domain Concepts
            for pattern, display, cat, weight in WORK_DOMAIN_PATTERNS:
                matches = len(pattern.findall(sec_text))
                if matches > 0:
                    base_val = weight * min(2.0, 1.0 + 0.2 * (matches - 1))
                    weighted_val = round(base_val * multiplier, 2)
                    extracted_scores[display] = extracted_scores.get(display, 0.0) + weighted_val
                    skill_sections[display].add(sec_type)

            # Pass 4: spaCy Technical Noun Chunk Compounds (skip company intro/perks)
            if sec_type != "company_intro":
                noun_phrases = self.noun_extractor.extract_technical_phrases(sec_text, NON_SKILL_STOPWORDS)
                for phrase, count in noun_phrases.items():
                    if phrase.lower() not in org_entities:
                        base_val = 0.85 * min(1.5, 1.0 + 0.15 * (count - 1))
                        weighted_val = round(base_val * multiplier, 2)
                        extracted_scores[phrase] = extracted_scores.get(phrase, 0.0) + weighted_val
                        skill_sections[phrase].add(sec_type)

            # Pass 5: spaCy NER Extraction for Unknown Products (skip company intro)
            if sec_type != "company_intro":
                try:
                    sec_doc = self.nlp(sec_text)
                    if hasattr(sec_doc, "ents"):
                        for ent in sec_doc.ents:
                            if ent.label_ == "PRODUCT":
                                prod_clean = re.sub(r"^[^\w]+", "", ent.text.strip())
                                prod_clean = re.sub(r"[\r\n]+", " ", prod_clean).strip()
                                prod_lower = prod_clean.lower()
                                if (
                                    len(prod_clean) > 2
                                    and len(prod_clean.split()) <= 3
                                    and prod_lower not in NON_SKILL_STOPWORDS
                                    and prod_lower not in org_entities
                                ):
                                    display = prod_clean.title()
                                    weighted_val = round(0.8 * multiplier, 2)
                                    extracted_scores[display] = extracted_scores.get(display, 0.0) + weighted_val
                                    skill_sections[display].add(sec_type)
                except Exception:
                    pass

        # 5. Filter & Clean Extracted Skills
        final_scores: Dict[str, float] = {}
        required_skills: List[str] = []
        preferred_skills: List[str] = []

        role_lower = role.lower() if role else ""

        for kw, score in extracted_scores.items():
            kw_clean = re.sub(r"^[^\w]+", "", kw)
            kw_clean = re.sub(r"[\r\n]+", " ", kw_clean).strip()
            kw_lower = kw_clean.lower()
            if (
                len(kw_clean) > 1
                and kw_lower not in NON_SKILL_STOPWORDS
                and kw_lower not in org_entities
                and (not role_lower or kw_lower != role_lower)
                and not kw_lower.endswith((" engineer", " developer", " architect", " team", " teams"))
                and not kw_lower.startswith((
                    "key responsibilities", "strong proficiency", "hands-on experience",
                    "bs/ms", "experience with", "experience building", "this role", "qualifications"
                ))
            ):
                final_scores[kw_clean] = round(score, 2)
                
                # Classify into required vs preferred based on originating sections
                sec_types = skill_sections.get(kw, set())
                if "required" in sec_types:
                    required_skills.append(kw_clean)
                elif "preferred" in sec_types:
                    preferred_skills.append(kw_clean)
                elif score >= 1.5:
                    required_skills.append(kw_clean)
                else:
                    preferred_skills.append(kw_clean)

        # Sort all skills by score descending
        sorted_skills = sorted(final_scores.keys(), key=lambda k: final_scores[k], reverse=True)
        required_skills = sorted(list(dict.fromkeys(required_skills)), key=lambda k: final_scores.get(k, 0), reverse=True)
        preferred_skills = sorted(list(dict.fromkeys(preferred_skills)), key=lambda k: final_scores.get(k, 0), reverse=True)

        return JDProfile(
            role=role,
            seniority=seniority,
            skills=sorted_skills,
            keywords=sorted_skills,
            keyword_scores=final_scores,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            raw_text=text
        )
