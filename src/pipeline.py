import logging
from typing import Optional
from dotenv import load_dotenv

from .models.config import PipelineConfig
from .models.experience import load_experiences_from_dir, SkillTaxonomy
from .models.resume import TailoredResume, SelectedExperience, PipelineResult
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

        # 2. Parse JD
        jd_profile = self.parser.parse(jd_text)

        # 3. Rank Experiences
        scored_exps = self.exp_ranker.rank(
            experiences=all_experiences,
            jd_profile=jd_profile,
            company_profile_name=company_profile_name
        )

        # 4. Rank Bullets (MMR) & Apply Rewriting Chain
        selected_experiences: list[SelectedExperience] = []
        all_resume_tags = []
        used_tiers = set()

        for s_exp in scored_exps:
            bullets = select_bullets_mmr(
                bullets=s_exp.experience.bullets,
                jd_profile=jd_profile,
                embedding_model=self.embedding_model,
                max_k=self.config.max_bullets_per_experience,
                lambda_param=self.config.mmr_lambda
            )

            # Rewrite each bullet
            rewritten_bullets = []
            for sel_b in bullets:
                rewritten_text, tier = self.rewriter_chain.rewrite(
                    bullet_text=sel_b.bullet.text,
                    jd_keywords=jd_profile.keywords
                )
                sel_b.rewritten_text = rewritten_text
                sel_b.rewriter_tier = tier
                used_tiers.add(tier)
                rewritten_bullets.append(sel_b)

                # Collect tags ONLY from selected bullets
                all_resume_tags.extend(sel_b.bullet.tags)

            selected_experiences.append(
                SelectedExperience(
                    experience=s_exp.experience,
                    selected_title=s_exp.best_title,
                    selected_bullets=rewritten_bullets,
                    composite_score=s_exp.score
                )
            )

            # Collect tags from selected experience top-level tags
            all_resume_tags.extend(s_exp.experience.tags)

        # Summarize rewriter tiers used
        if not used_tiers:
            overall_rewriter_tier = "None"
        elif len(used_tiers) == 1:
            overall_rewriter_tier = list(used_tiers)[0]
        else:
            overall_rewriter_tier = f"Mixed ({', '.join(sorted(used_tiers))})"

        # 5. Match Skills using tags ONLY from selected experiences and bullets
        match_result = self.skill_matcher.match(
            jd_skills=jd_profile.skills,
            resume_tags=all_resume_tags
        )

        selected_skills = [item for item, _ in match_result.matched]
        if not selected_skills:
            selected_skills = list(dict.fromkeys([t.title() for t in all_resume_tags[:8]]))

        # 6. Assemble Tailored Resume Object (In-Memory)
        tailored_resume = TailoredResume(
            selected_experiences=selected_experiences,
            selected_skills=selected_skills,
            metadata={"rewriter_tier": overall_rewriter_tier}
        )

        # 7. Render LaTeX
        latex_str = self.renderer.render(tailored_resume)

        # 8. Generate Reports
        ats_report = generate_ats_report(jd_profile, match_result, tailored_resume)
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
