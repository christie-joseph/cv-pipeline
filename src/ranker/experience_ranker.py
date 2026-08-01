import os
import re
import yaml
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models.experience import Experience
from ..models.jd_profile import JDProfile
from ..models.config import PipelineConfig


class ScoredExperience:
    def __init__(self, experience: Experience, score: float, best_title: str, orig_index: int):
        self.experience = experience
        self.score = score
        self.best_title = best_title
        self.orig_index = orig_index


class ExperienceRanker:
    def __init__(self, config: Optional[PipelineConfig] = None, embedding_model=None):
        self.config = config or PipelineConfig()
        self.embedding_model = embedding_model

    def rank(
        self,
        experiences: List[Experience],
        jd_profile: JDProfile,
        company_profile_name: Optional[str] = None
    ) -> List[ScoredExperience]:
        if not experiences:
            return []

        company_profile = self._load_company_profile(company_profile_name)
        scores: List[ScoredExperience] = []

        # Prepare texts
        exp_texts = [
            f"{e.company} {e.titles.default} {' '.join(e.tags)} " + " ".join([b.text for b in e.bullets[:5]])
            for e in experiences
        ]
        jd_text = jd_profile.raw_text or " ".join(jd_profile.keywords)

        # 1. TF-IDF Cosine Similarity
        tfidf_scores = self._compute_tfidf_scores(exp_texts, jd_text)

        # 2. Embedding Cosine Similarity
        emb_scores = self._compute_embedding_scores(exp_texts, jd_text)

        # Calculate composite score for each experience
        weights = self.config.weights
        for i, exp in enumerate(experiences):
            tfidf_s = tfidf_scores[i]
            emb_s = emb_scores[i]

            # 3. Skill Overlap Ratio (use filtered jd_skills only for denominator)
            exp_tags = {t.lower() for t in exp.tags + [t for b in exp.bullets for t in b.tags]}
            jd_skills_clean = {s.lower() for s in (jd_profile.skills or jd_profile.keywords)}
            overlap_count = len(exp_tags.intersection(jd_skills_clean))
            skill_s = (overlap_count / max(1, len(jd_skills_clean))) if jd_skills_clean else 0.5

            # 4. Importance Rating (1-10 mapped to 0.1-1.0)
            importance_s = min(1.0, max(0.1, exp.importance / 10.0))

            # 5. Company Profile Boost
            company_boost = 0.0
            if company_profile:
                tag_boosts = company_profile.get("tag_boosts", {})
                for tag in exp.tags:
                    if tag in tag_boosts:
                        company_boost += (tag_boosts[tag] - 1.0) * 0.1

            composite = (
                weights.tfidf * tfidf_s
                + weights.embedding * emb_s
                + weights.skill_overlap * skill_s
                + weights.importance * importance_s
                + weights.company_boost * company_boost
            )

            # Select Best Title Variant
            best_title = self._select_best_title(exp, jd_profile)

            scores.append(
                ScoredExperience(
                    experience=exp,
                    score=round(float(composite), 3),
                    best_title=best_title,
                    orig_index=i
                )
            )

        # Preserve chronological timeline continuity
        selected_in_chrono = []
        for i in range(len(scores)):
            s = scores[i]
            if len(selected_in_chrono) >= self.config.max_experiences:
                break

            # Check if any non-optional mandatory job appears LATER in chronological order
            has_mandatory_after = any(not scores[j].experience.optional for j in range(i + 1, len(scores)))

            if not s.experience.optional or s.score >= self.config.minimum_similarity or has_mandatory_after:
                selected_in_chrono.append(s)
            else:
                break

        if not selected_in_chrono:
            # Fallback to top N by score if all filtered out
            scores_by_val = sorted(scores, key=lambda x: x.score, reverse=True)
            return scores_by_val[: self.config.max_experiences]

        # Return experiences in source-of-truth chronological order
        return selected_in_chrono

    def _compute_tfidf_scores(self, exp_texts: List[str], jd_text: str) -> List[float]:
        try:
            docs = [jd_text] + exp_texts
            vec = TfidfVectorizer(stop_words="english")
            matrix = vec.fit_transform(docs)
            sims = cosine_similarity(matrix[1:], matrix[0]).flatten()
            return [float(s) for s in sims]
        except Exception:
            return [0.0] * len(exp_texts)

    def _compute_embedding_scores(self, exp_texts: List[str], jd_text: str) -> List[float]:
        if not self.embedding_model:
            return [0.5] * len(exp_texts)
        try:
            jd_emb = list(self.embedding_model.embed([jd_text]))[0]
            exp_embs = list(self.embedding_model.embed(exp_texts))
            sims = [
                float(np.dot(jd_emb, e_emb) / (np.linalg.norm(jd_emb) * np.linalg.norm(e_emb) + 1e-9))
                for e_emb in exp_embs
            ]
            return sims
        except Exception:
            return [0.0] * len(exp_texts)

    def _select_best_title(self, exp: Experience, jd_profile: JDProfile) -> str:
        all_variants = [exp.titles.default] + exp.titles.variants
        if not all_variants or not jd_profile.role:
            return exp.titles.default

        jd_role_clean = jd_profile.role.lower()
        best_title = exp.titles.default
        best_score = -1.0

        for title in all_variants:
            title_words = set(re.findall(r"\w+", title.lower()))
            role_words = set(re.findall(r"\w+", jd_role_clean))
            intersection = len(title_words.intersection(role_words))
            if intersection > best_score:
                best_score = intersection
                best_title = title

        return best_title

    def _load_company_profile(self, name: Optional[str]) -> Optional[Dict[str, Any]]:
        if not name:
            return None
        project_root = Path(__file__).resolve().parent.parent.parent
        file_path = str(project_root / "data" / "company_profiles" / f"{name}.yaml")
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return None
