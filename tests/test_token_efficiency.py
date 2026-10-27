import json
from src.rewriter.chain import _needs_rewrite


def test_compact_prompt_payload_structure():
    keywords = ["Kafka", "Kubernetes", "AWS", "Go", "Docker", "gRPC", "PostgreSQL", "Redis"]
    bullets = [
        "Architected multi-region Kubernetes platform across AWS managing 120+ microservices.",
        "Designed high-throughput gRPC communication mesh, cutting P99 latency from 180ms to 42ms."
    ]

    compact_payload = {
        "kw": [k for k in keywords[:8] if len(k) > 1],
        "b": bullets
    }
    user_prompt = json.dumps(compact_payload, separators=(",", ":"))

    # Assert machine-dense payload is extremely compact
    assert len(user_prompt) < 320
    assert "Target Job Keywords:" not in user_prompt
    assert "Instructions:" not in user_prompt


def test_selective_rewriter_filter():
    keywords = ["Kubernetes", "AWS", "Go", "Microservices"]

    # Bullet already has 2 keywords ("Kubernetes", "AWS") AND a metric ("120+") -> Should SKIP rewriting!
    bullet_saturated = "Architected multi-region Kubernetes platform across AWS managing 120+ microservices."
    assert _needs_rewrite(bullet_saturated, keywords) is False

    # Bullet has no target keywords -> Needs rewriting!
    bullet_unaligned = "Collaborated with team members to resolve tickets."
    assert _needs_rewrite(bullet_unaligned, keywords) is True
