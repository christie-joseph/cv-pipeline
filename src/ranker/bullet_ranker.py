import re
import numpy as np
from typing import List, Dict
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models.experience import Bullet
from ..models.resume import SelectedBullet
from ..models.jd_profile import JDProfile
from .faang_scorer import score_bullet_faang


def _keyword_density_bonus(bullet_text: str, jd_keywords: List[str], keyword_scores: Dict[str, float]) -> float:
    """Returns a score boost [0.0, 0.25] based on matches of high-value JD keywords in the bullet."""
    text_lower = bullet_text.lower()
    bonus = 0.0
    for kw in jd_keywords[:15]:
        kw_lower = kw.lower()
        pattern = r"\b" + re.escape(kw_lower) + r"\b" if re.match(r"^\w", kw_lower) else re.escape(kw_lower)
        if re.search(pattern, text_lower):
            weight = keyword_scores.get(kw, 0.5)
            bonus += min(0.08, weight * 0.05)
    return min(0.25, bonus)


def select_bullets_mmr(
    bullets: List[Bullet],
    jd_profile: JDProfile,
    embedding_model=None,
    max_k: int = 3,
    lambda_param: float = 0.7
) -> List[SelectedBullet]:
    if not bullets:
        return []

    bullet_texts = [b.text for b in bullets]
    jd_text = jd_profile.raw_text or " ".join(jd_profile.keywords)

    # 1. Calculate actual relevance scores
    if embedding_model:
        try:
            jd_emb = list(embedding_model.embed([jd_text]))[0]
            bullet_embs = list(embedding_model.embed(bullet_texts))
            
            relevance_scores = [
                float(np.dot(jd_emb, b_emb) / (np.linalg.norm(jd_emb) * np.linalg.norm(b_emb) + 1e-9))
                for b_emb in bullet_embs
            ]

            # Vectorized pairwise similarity matrix computation
            sim_matrix = cosine_similarity(bullet_embs, bullet_embs)
        except Exception:
            relevance_scores, sim_matrix = _tfidf_scores(bullet_texts, jd_text)
    else:
        relevance_scores, sim_matrix = _tfidf_scores(bullet_texts, jd_text)

    # 2. Apply FAANG Heuristic Multipliers & Keyword Density Boosts
    kw_scores = getattr(jd_profile, "keyword_scores", {}) or {}
    for idx, bullet_text in enumerate(bullet_texts):
        faang_mult = score_bullet_faang(bullet_text)
        kw_bonus = _keyword_density_bonus(bullet_text, jd_profile.keywords, kw_scores)
        relevance_scores[idx] = (relevance_scores[idx] * faang_mult) + kw_bonus

    # If count is <= max_k, return all bullets with computed scores
    if len(bullets) <= max_k:
        result = []
        for idx, bullet in enumerate(bullets):
            rel = round(float(relevance_scores[idx]), 3)
            # Compute diversity relative to other bullets in the set
            other_indices = [j for j in range(len(bullets)) if j != idx]
            if other_indices:
                max_sim = max(float(sim_matrix[idx, o]) for o in other_indices)
                div_score = round(max(0.0, 1.0 - max_sim), 3)
            else:
                div_score = 1.0

            result.append(
                SelectedBullet(
                    bullet=bullet,
                    relevance_score=rel,
                    diversity_score=div_score,
                    rewritten_text=bullet.text
                )
            )
        return result

    # 3. MMR selection loop for len(bullets) > max_k
    selected_indices = []
    unselected_indices = list(range(len(bullets)))

    while len(selected_indices) < min(max_k, len(bullets)):
        mmr_scores = []
        for idx in unselected_indices:
            rel = relevance_scores[idx]
            if not selected_indices:
                max_sim = 0.0
            else:
                max_sim = max(float(sim_matrix[idx, s_idx]) for s_idx in selected_indices)
            
            score = lambda_param * rel - (1 - lambda_param) * max_sim
            mmr_scores.append((score, idx, max_sim))

        mmr_scores.sort(key=lambda x: x[0], reverse=True)
        best_choice = mmr_scores[0]
        best_idx = best_choice[1]
        selected_indices.append(best_idx)
        unselected_indices.remove(best_idx)

    # 4. Assemble final selected bullets with genuine diversity scores
    result = []
    for idx in selected_indices:
        bullet = bullets[idx]
        rel = round(float(relevance_scores[idx]), 3)
        other_selected = [s for s in selected_indices if s != idx]
        if other_selected:
            max_sim = max(float(sim_matrix[idx, s]) for s in other_selected)
            div_score = round(max(0.0, 1.0 - max_sim), 3)
        else:
            div_score = 1.0

        result.append(
            SelectedBullet(
                bullet=bullet,
                relevance_score=rel,
                diversity_score=div_score,
                rewritten_text=bullet.text
            )
        )
    return result


def _tfidf_scores(bullet_texts: List[str], jd_text: str):
    try:
        documents = [jd_text] + bullet_texts
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(documents)
        
        jd_vec = tfidf_matrix[0]
        bullet_vecs = tfidf_matrix[1:]
        
        relevance_scores = cosine_similarity(bullet_vecs, jd_vec).flatten()
        sim_matrix = cosine_similarity(bullet_vecs, bullet_vecs)
        return list(relevance_scores), sim_matrix
    except Exception:
        n = len(bullet_texts)
        return [0.0] * n, np.zeros((n, n))
