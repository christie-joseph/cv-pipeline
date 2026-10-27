import pytest
from src.parser.jd_parser import JDParser


def test_jd_parser_multi_pass_and_scores():
    parser = JDParser()
    jd = """
    # Google - Senior Backend Engineer
    Looking for a Senior Backend Engineer to design distributed systems.
    Must have hands-on experience with Kafka, Kafka, and Redis.
    Expertise in Python, FastAPI, and Kubernetes is required.
    Familiarity with gRPC and Zero-Downtime Deployments is a plus.
    """
    profile = parser.parse(jd)
    assert profile.role == "Senior Backend Engineer"
    assert profile.seniority == "Senior"
    assert "Apache Kafka" in profile.skills
    assert "Redis" in profile.skills
    assert "Python" in profile.skills
    assert "FastAPI" in profile.skills
    assert "Kubernetes" in profile.skills
    assert "gRPC" in profile.skills
    assert "Zero-Downtime Deployments" in profile.skills

    # Frequency boost verification: Kafka mentioned multiple times should have higher score than single mention
    assert profile.keyword_scores["Apache Kafka"] > profile.keyword_scores["Redis"]

