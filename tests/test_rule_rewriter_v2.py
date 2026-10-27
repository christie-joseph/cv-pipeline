import pytest
from src.rewriter.rule_rewriter import RuleRewriter
from src.rewriter.sentence_restructurer import SentenceRestructurer
from src.rewriter.keyword_injector import KeywordInjector


def test_sentence_restructurer_passive_and_filler():
    restructurer = SentenceRestructurer()
    raw = "In this role, I was responsible for developing high throughput APIs"
    stripped = restructurer.strip_filler(raw)
    assert not stripped.lower().startswith("in this role")
    assert not stripped.lower().startswith("i was responsible for")

    passive = "The microservice was implemented by me"
    active = restructurer.passive_to_active(passive)
    assert "implemented" in active


def test_sentence_restructurer_impact_first():
    restructurer = SentenceRestructurer()
    raw = "Optimized database indexes, reducing latency by 45%"
    impact = restructurer.impact_first(raw)
    assert impact.lower().startswith("reduced latency by 45%")


def test_rule_rewriter_full_pipeline():
    rewriter = RuleRewriter()
    bullet = "worked on backend services in Java, reducing latency by 30%"
    jd_keywords = ["Java", "Kafka", "Backend"]
    bullet_tags = ["java", "kafka"]
    keyword_scores = {"Kafka": 1.5, "Java": 1.0}

    result = rewriter.rewrite(
        bullet_text=bullet,
        jd_keywords=jd_keywords,
        bullet_tags=bullet_tags,
        keyword_scores=keyword_scores
    )

    assert result.endswith(".")
    assert "engineered" in result or "engineered" in result.lower() or "reduced" in result.lower()
    # Ensure metrics preserved
    assert "30%" in result
