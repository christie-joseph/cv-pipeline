from src.parser.jd_parser import JDParser


def test_jd_parser_basic():
    parser = JDParser()
    sample_jd = """
    Senior Backend Engineer at Google.
    Looking for experience with Java, Spring Boot, Kafka, and Redis.
    Must have knowledge of distributed systems and Kubernetes.
    """
    profile = parser.parse(sample_jd)
    assert profile.seniority == "Senior"
    assert len(profile.keywords) > 0
    keywords_lower = [k.lower() for k in profile.keywords]
    assert any("java" in k for k in keywords_lower)
