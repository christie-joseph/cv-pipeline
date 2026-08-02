from pathlib import Path
from src.models.config import PipelineConfig
from src.models.experience import load_experiences_from_dir, SkillTaxonomy

project_root = Path(__file__).resolve().parent.parent


def test_config_loading():
    config_path = str(project_root / "config.yaml")
    config = PipelineConfig.load_from_yaml(config_path)
    assert config.max_experiences > 0
    assert config.max_bullets_per_experience > 0
    assert abs(config.weights.tfidf + config.weights.embedding + config.weights.skill_overlap + config.weights.importance + config.weights.company_boost - 1.0) < 1e-3


def test_experience_yaml_loading():
    exp_dir = str(project_root / "data" / "experiences")
    experiences = load_experiences_from_dir(exp_dir)
    assert len(experiences) >= 3
    for exp in experiences:
        assert exp.id
        assert exp.company
        assert exp.titles.default
        assert len(exp.bullets) > 0


def test_skills_taxonomy_loading():
    skills_path = str(project_root / "data" / "skills.yaml")
    taxonomy = SkillTaxonomy.load_from_yaml(skills_path)
    assert len(taxonomy.skills) > 0
    skill_ids = [s.id for s in taxonomy.skills]
    assert "kafka" in skill_ids
    assert "java" in skill_ids


def test_experience_date_normalization():
    from src.models.experience import Experience, TitleConfig
    exp1 = Experience(
        id="test1",
        company="Test Co",
        start="Jan 2020",
        end="current",
        titles=TitleConfig(default="Engineer")
    )
    assert exp1.end == "Present"

    exp2 = Experience(
        id="test2",
        company="Test Co",
        start="Jan 2020",
        end="now",
        titles=TitleConfig(default="Engineer")
    )
    assert exp2.end == "Present"


def test_education_sorting():
    from src.models.resume import load_education, _extract_end_year
    assert _extract_end_year("May 2021") == 2021
    assert _extract_end_year("Sep 2018 - Present") == 9999
    
    edu_list = load_education()
    if len(edu_list) >= 2:
        end_years = [_extract_end_year(e.dates) for e in edu_list]
        assert end_years == sorted(end_years, reverse=True)

