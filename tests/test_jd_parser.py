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


def test_jd_parser_mid_level():
    parser = JDParser()
    
    # Explicit "Mid-Level"
    p1 = parser.parse("We need a Mid-level Software Engineer to join our team.")
    assert p1.seniority == "Mid-Level"
    
    # "Associate"
    p2 = parser.parse("Associate Backend Developer needed.")
    assert p2.seniority == "Mid-Level"
    
    # Un-qualified generic tech role
    p3 = parser.parse("Looking for a Fullstack Engineer with Python experience.")
    assert p3.seniority == "Mid-Level"
    
    # Un-qualified SWE
    p4 = parser.parse("SWE role at stealth startup")
    assert p4.seniority == "Mid-Level"
