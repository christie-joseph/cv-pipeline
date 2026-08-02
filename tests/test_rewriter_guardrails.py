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
