import os
import glob
import yaml
from pathlib import Path
import pytest

from src.models.experience import Experience
from src.models.resume import ContactInfo, EducationItem, ProjectItem


def test_dummy_experiences_neutrality():
    # Explicitly test public sample files (ignoring personal overlay)
    project_root = Path(__file__).resolve().parent.parent
    dir_path = project_root / "data" / "experiences"

    sample_files = sorted(
        [f for f in glob.glob(str(dir_path / "*.yaml")) if os.path.isfile(f)]
    )
    assert len(sample_files) >= 5

    experiences = []
    for fp in sample_files:
        with open(fp, "r", encoding="utf-8") as f:
            experiences.append(Experience(**yaml.safe_load(f)))

    companies = [e.company.lower() for e in experiences]
    # Check that biased sample company names are completely removed
    assert "amazon" not in companies
    assert "stealth fintech startup" not in companies
    assert "university distributed systems lab" not in companies

    # Check realistic domains are present
    assert any("nimbus" in c for c in companies)
    assert any("paystream" in c for c in companies)
    assert any("pixelforge" in c for c in companies)
    assert any("datavault" in c for c in companies)
    assert any("codecraft" in c for c in companies)

    # Check bullet metrics and tags
    for exp in experiences:
        assert len(exp.bullets) >= 3
        for b in exp.bullets:
            assert len(b.text) > 20
            assert isinstance(b.tags, list)


def test_dummy_contact_info_neutrality():
    project_root = Path(__file__).resolve().parent.parent
    contact_file = project_root / "data" / "contact.yaml"
    with open(contact_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    contact = ContactInfo(**data)

    assert "Alex Morgan" in contact.name
    assert "example.com" in contact.email or "alex" in contact.email.lower()


def test_dummy_education_neutrality():
    project_root = Path(__file__).resolve().parent.parent
    edu_file = project_root / "data" / "education.yaml"
    with open(edu_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    items = [EducationItem(**item) for item in data.get("education", [])]
    assert len(items) >= 1
    assert "Tech State University" in items[0].institution


def test_dummy_projects_neutrality():
    project_root = Path(__file__).resolve().parent.parent
    proj_file = project_root / "data" / "projects.yaml"
    with open(proj_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    projects = [ProjectItem(**item) for item in data.get("projects", [])]
    assert len(projects) >= 3
    titles = [p.title.lower() for p in projects]
    assert any("key-value store" in t or "distributed" in t for t in titles)
    assert any("event stream" in t or "processor" in t for t in titles)
