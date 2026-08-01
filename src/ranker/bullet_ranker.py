import numpy as np
from typing import List
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from ..models.experience import Bullet
from ..models.resume import SelectedBullet
from ..models.jd_profile import JDProfile


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

    # Calculate actual relevance scores
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

    # If count is <= max_k, return all bullets with their calculated real relevance scores
    if len(bullets) <= max_k:
        result = []
        for idx, bullet in enumerate(bullets):
            rel = round(float(relevance_scores[idx]), 3)
            result.append(
                SelectedBullet(
                    bullet=bullet,
                    relevance_score=rel,
                    diversity_score=1.0,
                    rewritten_text=bullet.text
                )
            )
        return result

    # MMR selection loop for len(bullets) > max_k
    selected_indices = []
    unselected_indices = list(range(len(bullets)))

    while len(selected_indices) < min(max_k, len(bullets)):
        mmr_scores = []
        for idx in unselected_indices:
            rel = relevance_scores[idx]
            if not selected_indices:
                max_sim = 0.0
            else:
                max_sim = max(sim_matrix[idx, s_idx] for s_idx in selected_indices)
            
            score = lambda_param * rel - (1 - lambda_param) * max_sim
            mmr_scores.append((score, idx))

        mmr_scores.sort(key=lambda x: x[0], reverse=True)
        best_idx = mmr_scores[0][1]
        selected_indices.append(best_idx)
        unselected_indices.remove(best_idx)

    result = []
    for idx in selected_indices:
        bullet = bullets[idx]
        rel = round(float(relevance_scores[idx]), 3)
        result.append(
            SelectedBullet(
                bullet=bullet,
                relevance_score=rel,
                diversity_score=1.0,
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
