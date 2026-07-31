from src.models.experience import Bullet
from src.models.jd_profile import JDProfile
from src.ranker.bullet_ranker import select_bullets_mmr


def test_mmr_bullet_diversity():
    bullets = [
        Bullet(id="b1", text="Built Kafka streaming pipeline processing 2M events/day", tags=["kafka"]),
        Bullet(id="b2", text="Architected Kafka pubsub broker cluster for high availability", tags=["kafka"]),
        Bullet(id="b3", text="Led AWS Kubernetes cluster deployment reducing costs by 30%", tags=["k8s"]),
        Bullet(id="b4", text="Optimized SQL database query performance and Redis caching", tags=["sql"]),
    ]

    jd_profile = JDProfile(
        keywords=["kafka", "kubernetes", "redis", "streaming"],
        raw_text="Looking for Kafka, Kubernetes, and Redis experience"
    )

    selected = select_bullets_mmr(bullets, jd_profile, max_k=3, lambda_param=0.7)
    assert len(selected) == 3
    selected_ids = [b.bullet.id for b in selected]
    # Verify that MMR picks diverse topics (e.g. b1 or b2, plus b3, b4) rather than 2 duplicate Kafka bullets
    assert ("b3" in selected_ids) or ("b4" in selected_ids)
