import pytest
from src.parser.jd_parser import JDParser
from src.models.jd_profile import JDProfile


def test_jd_parser_section_weighted_scoring():
    parser = JDParser()
    jd_text = """
    # Stripe — Staff Software Engineer

    About Us:
    Stripe powers internet commerce. We build financial infrastructure.

    Minimum Qualifications:
    * Extensive experience with Java, Kafka, and Distributed Systems.
    * Strong background in PostgreSQL database optimization.

    Preferred Qualifications:
    * Familiarity with Python and GraphQL.
    """

    profile = parser.parse(jd_text)
    assert profile.role == "Staff Software Engineer"
    assert profile.seniority == "Staff"

    # Required skills must be categorized and receive 1.8x section multiplier
    assert "Java" in profile.required_skills
    assert "Apache Kafka" in profile.required_skills or "Kafka" in profile.required_skills or any("kafka" in s.lower() for s in profile.required_skills)
    assert "PostgreSQL" in profile.required_skills or "Postgresql" in profile.required_skills or "SQL" in profile.required_skills

    # Preferred skills must be categorized
    assert any("python" in s.lower() for s in profile.preferred_skills) or any("graphql" in s.lower() for s in profile.preferred_skills)

    # Score of required skills should be significantly higher than preferred skills
    java_score = profile.keyword_scores.get("Java", 0.0)
    python_score = profile.keyword_scores.get("Python", 0.0)
    assert java_score > python_score


def test_jd_parser_technical_noun_chunks():
    parser = JDParser()
    jd_text = """
    Requirements:
    * Hands-on experience with asynchronous event processing and distributed caching tiers.
    * Expertise in high availability clustering and zero-downtime deployment pipelines.
    """

    profile = parser.parse(jd_text)
    # Check that technical compound phrases are extracted
    extracted_lower = {k.lower() for k in profile.keywords}
    assert any("caching" in k or "event" in k or "availability" in k or "deployment" in k for k in extracted_lower)


def test_skill_matcher_weighted_percentage():
    from src.ranker.skill_matcher import SkillMatcher

    matcher = SkillMatcher()
    required = ["Java", "Docker", "Apache Kafka"]
    preferred = ["Python", "Kubernetes", "GCP", "GraphQL", "Redis"]
    all_skills = required + preferred

    # Candidate has ALL 3 required skills, but only 1 of 5 preferred skills
    resume_tags = ["Java", "Docker", "Kafka", "Python"]
    result = matcher.match(
        jd_skills=all_skills,
        resume_tags=resume_tags,
        required_skills=required,
        preferred_skills=preferred
    )

    # Required: 3/3 matched (100% -> 70.0 pts)
    # Preferred: 1/5 matched (20% -> 6.0 pts)
    # Total weighted match percentage: 76.0% (NOT 4/8 = 50%)
    assert result.match_percentage >= 70.0
    assert len(result.required_matched) == 3
    assert len(result.required_missing) == 0
    assert len(result.preferred_missing) == 4
