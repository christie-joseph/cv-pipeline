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


def test_skill_matcher_full_text():
    skills_path = str(project_root / "data" / "skills.yaml")
    taxonomy = SkillTaxonomy.load_from_yaml(skills_path)
    matcher = SkillMatcher(taxonomy=taxonomy)

    jd_skills = ["Terraform", "Kubernetes"]
    # Tags leave out terraform
    resume_tags = ["docker"]
    resume_text = "Architected cloud infrastructure using Terraform to provision microservices in Kubernetes."

    result = matcher.match(jd_skills, resume_tags, resume_text=resume_text)
    matched_names = [m[0] for m in result.matched]
    assert "Terraform" in matched_names
    assert "Kubernetes" in matched_names
    assert result.match_percentage == 100.0
