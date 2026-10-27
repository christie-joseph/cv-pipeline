import pytest
from src.parser.section_segmenter import SectionSegmenter


def test_section_segmenter_standard_jd():
    segmenter = SectionSegmenter()
    jd_text = """
    # Google - Senior Backend Software Engineer

    About the Company:
    Google is a global technology leader in search and cloud computing. We offer great benefits.

    Key Responsibilities:
    * Design and architect distributed microservices.
    * Optimize high-throughput event processing pipelines.

    Minimum Qualifications:
    * 5+ years of experience with Java or Go.
    * Deep expertise in Distributed Systems and Kubernetes.
    * Hands-on experience with Apache Kafka.

    Preferred Qualifications:
    * Experience with GCP and BigQuery.
    * Knowledge of gRPC and Protobuf.
    """

    sections = segmenter.segment(jd_text)
    assert len(sections) >= 4

    types = [s.section_type for s in sections]
    assert "company_intro" in types
    assert "responsibilities" in types
    assert "required" in types
    assert "preferred" in types

    req_sec = next(s for s in sections if s.section_type == "required")
    assert req_sec.weight_multiplier == 1.8
    assert "Java" in req_sec.content
    assert "Distributed Systems" in req_sec.content

    pref_sec = next(s for s in sections if s.section_type == "preferred")
    assert pref_sec.weight_multiplier == 1.2
    assert "GCP" in pref_sec.content

    intro_sec = next(s for s in sections if s.section_type == "company_intro")
    assert intro_sec.weight_multiplier == 0.2


def test_section_segmenter_empty_and_plain():
    segmenter = SectionSegmenter()
    assert segmenter.segment("") == []
    assert segmenter.segment("   ") == []

    plain_jd = "Looking for a Python software developer with Docker experience."
    sections = segmenter.segment(plain_jd)
    assert len(sections) == 1
    assert sections[0].section_type == "general"
    assert sections[0].weight_multiplier == 1.0
