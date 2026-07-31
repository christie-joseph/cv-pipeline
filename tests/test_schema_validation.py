import pytest
from src.models.config import PipelineConfig
from src.models.experience import load_experiences_from_dir, SkillTaxonomy


def test_config_loading():
    config = PipelineConfig.load_from_yaml("config.yaml")
    assert config.max_experiences > 0
    assert config.max_bullets_per_experience > 0
    assert abs(config.weights.tfidf + config.weights.embedding + config.weights.skill_overlap + config.weights.importance + config.weights.company_boost - 1.0) < 1e-3


def test_experience_yaml_loading():
    experiences = load_experiences_from_dir("data/experiences")
    assert len(experiences) >= 3
    for exp in experiences:
        assert exp.id
        assert exp.company
        assert exp.titles.default
        assert len(exp.bullets) > 0


def test_skills_taxonomy_loading():
    taxonomy = SkillTaxonomy.load_from_yaml("data/skills.yaml")
    assert len(taxonomy.skills) > 0
    skill_ids = [s.id for s in taxonomy.skills]
    assert "kafka" in skill_ids
    assert "java" in skill_ids
