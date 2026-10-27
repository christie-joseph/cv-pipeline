import pytest
from src.rewriter.rule_rewriter import RuleRewriter
from src.rewriter.sentence_restructurer import SentenceRestructurer
from src.rewriter.keyword_injector import KeywordInjector


def test_rule_rewriter_single_verb_replacement():
    rewriter = RuleRewriter()
    bullet = "worked on distributed caching tier in Redis"
    res = rewriter.rewrite(bullet, jd_keywords=["Redis"])
    assert "engineered" in res.lower()
    assert res.endswith(".")
    assert res[0].isupper()


def test_rule_rewriter_multi_verb_replacement():
    rewriter = RuleRewriter()
    # A single bullet with multiple weak verbs
    bullet = "worked on payment microservices and helped with API gateway integration"
    res = rewriter.rewrite(bullet, jd_keywords=["microservices", "API"])
    # Both "worked on" -> "engineered" and "helped with" -> "contributed to" should be replaced
    assert "engineered" in res.lower()
    assert "contributed to" in res.lower()
    assert "worked on" not in res.lower()
    assert "helped with" not in res.lower()


def test_rule_rewriter_edge_cases():
    rewriter = RuleRewriter()
    assert rewriter.rewrite("", []) == ""
    assert rewriter.rewrite("   ", []) == ""

    # Bullet with already strong verb and proper termination
    strong = "Spearheaded zero-downtime migration of PostgreSQL database cluster."
    res = rewriter.rewrite(strong, [])
    assert "Spearheaded" in res
    assert res.endswith(".")


def test_rule_rewriter_passive_and_filler_elimination():
    rewriter = RuleRewriter()
    bullet = "In this role, I was responsible for designing low-latency trading pipelines"
    res = rewriter.rewrite(bullet, ["trading"])
    assert not res.lower().startswith("in this role")
    assert "owned" in res.lower() or "designing" in res.lower()


def test_rule_rewriter_metric_preservation():
    rewriter = RuleRewriter()
    bullet = "optimized database query indexing, reducing latency by 45% and saving $200K"
    res = rewriter.rewrite(bullet, ["database"])
    assert "45%" in res
    assert "$200K" in res or "$200k" in res.lower()
