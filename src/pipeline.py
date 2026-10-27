import logging
from typing import Optional
from dotenv import load_dotenv

from .models.config import PipelineConfig
from .models.experience import load_experiences_from_dir, SkillTaxonomy
from .models.resume import (
    TailoredResume, SelectedExperience, PipelineResult,
    load_contact_info, load_education, load_projects
)
from .parser.jd_parser import JDParser
from .ranker.experience_ranker import ExperienceRanker
from .ranker.bullet_ranker import select_bullets_mmr
from .ranker.skill_matcher import SkillMatcher
from .rewriter.chain import RewriterChain
from .renderer.latex_renderer import LatexRenderer
from .renderer.pdf_compiler import compile_pdf
from .reports.ats_report import generate_ats_report
from .reports.diff_report import generate_diff_report
from .reports.manifest import generate_manifest

logger = logging.getLogger(__name__)


class Pipeline:
    def __init__(self, config: Optional[PipelineConfig] = None):
        load_dotenv()
        
        self.config = config or PipelineConfig.load_from_yaml()
        
        self.embedding_model = None
        if not getattr(self.config, "offline", False):
            try:
                from fastembed import TextEmbedding
                self.embedding_model = TextEmbedding(model_name=self.config.embedding_model)
            except Exception as e:
                logger.info(f"FastEmbed loading note ({e}). Continuing with TF-IDF fallback...")

        self.parser = JDParser(embedding_model=self.embedding_model)
        self.exp_ranker = ExperienceRanker(config=self.config, embedding_model=self.embedding_model)
        self.taxonomy = SkillTaxonomy.load_from_yaml()
        self.skill_matcher = SkillMatcher(taxonomy=self.taxonomy)
        self.rewriter_chain = RewriterChain(config=self.config)
        self.renderer = LatexRenderer()

    def run(self, jd_text: str, company_profile_name: Optional[str] = None) -> PipelineResult:
        if not jd_text or len(jd_text.strip()) == 0:
            raise ValueError("Job Description text is empty.")

        # 1. Load Source of Truth Data
        all_experiences = load_experiences_from_dir()
        if not all_experiences:
            raise ValueError("No experience YAML files found in data/experiences/")

        contact_info = load_contact_info()
        education = load_education()
        projects = load_projects()

        # 2. Parse JD
        jd_profile = self.parser.parse(jd_text)

        # 3. Rank Experiences
        scored_exps = self.exp_ranker.rank(
            experiences=all_experiences,
            jd_profile=jd_profile,
            company_profile_name=company_profile_name
        )

        # 4. Rank Bullets (MMR) & Collect Bullets across Experiences
        selected_experiences: list[SelectedExperience] = []
        all_resume_tags = []
        used_tiers = set()
        
        # Intermediate structure to hold selected bullets per experience
        exp_bullets_map = []
        all_selected_bullet_objects = []

        for s_exp in scored_exps:
            bullets = select_bullets_mmr(
                bullets=s_exp.experience.bullets,
                jd_profile=jd_profile,
                embedding_model=self.embedding_model,
                max_k=self.config.max_bullets_per_experience,
                lambda_param=self.config.mmr_lambda
            )
            exp_bullets_map.append((s_exp, bullets))
            all_selected_bullet_objects.extend(bullets)

        # Execute Batch AI Rewriting (1 API call for all bullets)
        raw_bullet_texts = [sel_b.bullet.text for sel_b in all_selected_bullet_objects]
        raw_bullet_tags = [sel_b.bullet.tags for sel_b in all_selected_bullet_objects]
        rewritten_texts, rewriter_tiers = self.rewriter_chain.rewrite_batch(
            bullets=raw_bullet_texts,
            jd_keywords=jd_profile.keywords,
            bullets_tags=raw_bullet_tags,
            keyword_scores=getattr(jd_profile, "keyword_scores", {})
        )

        # Map rewritten results back to bullet objects
        for sel_b, r_text, r_tier in zip(all_selected_bullet_objects, rewritten_texts, rewriter_tiers):
            sel_b.rewritten_text = r_text
            sel_b.rewriter_tier = r_tier
            used_tiers.add(r_tier)
            all_resume_tags.extend(sel_b.bullet.tags)

        # Reconstruct SelectedExperience list
        for s_exp, bullets in exp_bullets_map:
            selected_experiences.append(
                SelectedExperience(
                    experience=s_exp.experience,
                    selected_title=s_exp.best_title,
                    selected_bullets=bullets,
                    composite_score=s_exp.score
                )
            )
            all_resume_tags.extend(s_exp.experience.tags)

        # Summarize rewriter tiers used
        if not used_tiers:
            overall_rewriter_tier = "None"
        elif len(used_tiers) == 1:
            overall_rewriter_tier = list(used_tiers)[0]
        else:
            overall_rewriter_tier = f"Mixed ({', '.join(sorted(used_tiers))})"

        # Concatenate full text of selected bullets for deep text scanning
        full_resume_text = " ".join([sel_b.rewritten_text or sel_b.bullet.text for sel_b in all_selected_bullet_objects])

        # Include candidate's project tech stacks and taxonomy skills in resume tags for matching
        for proj in projects:
            all_resume_tags.extend(proj.tech_stack)
        for sk in self.taxonomy.skills:
            all_resume_tags.append(sk.display)
            all_resume_tags.extend(sk.aliases)

        # 5. Match Skills using tags, full text, and section weighting
        match_result = self.skill_matcher.match(
            jd_skills=jd_profile.skills,
            resume_tags=all_resume_tags,
            resume_text=full_resume_text,
            required_skills=getattr(jd_profile, "required_skills", None),
            preferred_skills=getattr(jd_profile, "preferred_skills", None)
        )

        selected_skills = [item for item, _ in match_result.matched]
        if not selected_skills:
            selected_skills = list(dict.fromkeys([t.title() for t in all_resume_tags]))[:8]

        # Target Role from JD or default
        target_role = jd_profile.role or "Software Engineer"

        # 6. Assemble Tailored Resume Object (In-Memory)
        tailored_resume = TailoredResume(
            contact_info=contact_info,
            education=education,
            selected_experiences=selected_experiences,
            projects=projects,
            selected_skills=selected_skills,
            metadata={"rewriter_tier": overall_rewriter_tier, "target_role": target_role}
        )

        # 7. Render LaTeX
        latex_str = self.renderer.render(tailored_resume)

        # 8. Generate Reports
        ats_report = generate_ats_report(
            jd_profile,
            match_result,
            tailored_resume,
            keyword_scores=getattr(jd_profile, "keyword_scores", {})
        )

        diff_report = generate_diff_report(all_experiences, tailored_resume)
        manifest = generate_manifest(jd_text, tailored_resume, self.config)

        # 9. Optional PDF Compile (in ephemeral temp dir)
        pdf_bytes = None
        if self.config.output.compile_pdf:
            pdf_bytes = compile_pdf(latex_str)

        return PipelineResult(
            tailored_resume=tailored_resume,
            latex_string=latex_str,
            ats_report=ats_report,
            diff_report=diff_report,
            manifest=manifest,
            pdf_bytes=pdf_bytes
        )
