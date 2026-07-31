from pathlib import Path
from src.ranker.skill_matcher import SkillMatcher
from src.models.experience import SkillTaxonomy

project_root = Path(__file__).resolve().parent.parent


def test_skill_matcher():
    skills_path = str(project_root / "data" / "skills.yaml")
    taxonomy = SkillTaxonomy.load_from_yaml(skills_path)
    matcher = SkillMatcher(taxonomy=taxonomy)

    jd_skills = ["Confluent Kafka", "Java 17", "Postgres", "Terraform", "C++"]
    resume_tags = ["kafka", "java", "postgresql", "docker", "c++"]

    result = matcher.match(jd_skills, resume_tags)
    assert result.match_percentage > 50.0
    matched_names = [m[0] for m in result.matched]
    assert "Apache Kafka" in matched_names
    assert "Java" in matched_names
    assert "C++" in matched_names
    assert "Terraform" in result.missing
