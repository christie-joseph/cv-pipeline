from src.ranker.skill_matcher import SkillMatcher
from src.models.experience import SkillTaxonomy


def test_skill_matcher():
    taxonomy = SkillTaxonomy.load_from_yaml("data/skills.yaml")
    matcher = SkillMatcher(taxonomy=taxonomy)

    jd_skills = ["Confluent Kafka", "Java 17", "Postgres", "Terraform"]
    resume_tags = ["kafka", "java", "postgresql", "docker"]

    result = matcher.match(jd_skills, resume_tags)
    assert result.match_percentage > 50.0
    matched_names = [m[0] for m in result.matched]
    assert "Apache Kafka" in matched_names
    assert "Java" in matched_names
    assert "Terraform" in result.missing
