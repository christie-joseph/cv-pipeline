import pytest
from src.rewriter.chain import _validate_rewrite_guardrails


def test_guardrails_metric_retention():
    original = "Optimized API response time by 50ms and reduced cloud cost by 30%."
    valid_rewrite = "Decreased API latency by 50ms, successfully reducing cloud overhead by 30%."
    assert _validate_rewrite_guardrails(original, valid_rewrite) == True

    invalid_rewrite = "Decreased API latency significantly and reduced cloud overhead by 40%."
    assert _validate_rewrite_guardrails(original, invalid_rewrite) == False


def test_guardrails_length_bounding():
    original = "Built a CI/CD pipeline using GitHub Actions."
    valid_expansion = "Architected an automated CI/CD deployment pipeline utilizing GitHub Actions."
    assert _validate_rewrite_guardrails(original, valid_expansion) == True

    hallucination = "Built a CI/CD pipeline using GitHub Actions. I also completely redesigned the frontend architecture in React and Vue, trained a deep learning model for natural language processing, and led a team of 15 engineers across three different time zones to deliver the product under budget."
    assert _validate_rewrite_guardrails(original, hallucination) == False

    too_short = "Pipeline built."
    assert _validate_rewrite_guardrails(original, too_short) == False


def test_guardrails_comma_and_scale_metrics():
    original = "Scaled backend service to handle 10,000 requests/sec, saving $1.5M in infrastructure."
    valid_rewrite = "Architected backend service processing 10,000 requests/sec, cutting infrastructure expense by $1.5M."
    assert _validate_rewrite_guardrails(original, valid_rewrite) == True

    dropped_scale = "Architected backend service processing requests, cutting expense by $1.5M."
    assert _validate_rewrite_guardrails(original, dropped_scale) == False


def test_guardrails_hallucination_detection():
    # Bullet with no metrics where LLM hallucinates new numbers/percentages
    original = "Built an automated web scraping tool for competitor market research."
    hallucination = "Engineered automated web scraper collecting 50K records daily and reducing runtime by 45%."
    assert _validate_rewrite_guardrails(original, hallucination) == False

    # Bullet with no team size where LLM hallucinates headcount
    original_team = "Mentored junior engineers and led code review sessions."
    hallucination_team = "Directly managed and mentored 12 junior software engineers."
    assert _validate_rewrite_guardrails(original_team, hallucination_team) == False
