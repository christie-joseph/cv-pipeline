import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from .experience import Bullet, Experience


class SelectedBullet(BaseModel):
    bullet: Bullet
    relevance_score: float = 0.0
    diversity_score: float = 0.0
    rewritten_text: str = ""
    rewriter_tier: str = "None"


class SelectedExperience(BaseModel):
    experience: Experience
    selected_title: str
    selected_bullets: List[SelectedBullet] = Field(default_factory=list)
    composite_score: float = 0.0


class EducationItem(BaseModel):
    institution: str
    location: str
    degree: str
    dates: str


class ProjectItem(BaseModel):
    id: str
    title: str
    tech_stack: List[str] = Field(default_factory=list)
    dates: str
    bullets: List[str] = Field(default_factory=list)


class ContactInfo(BaseModel):
    name: str = "Candidate Name"
    phone: str = ""
    email: str = ""
    linkedin: str = ""
    github: str = ""
    location: str = ""


class TailoredResume(BaseModel):
    contact_info: ContactInfo = Field(default_factory=ContactInfo)
    education: List[EducationItem] = Field(default_factory=list)
    selected_experiences: List[SelectedExperience] = Field(default_factory=list)
    projects: List[ProjectItem] = Field(default_factory=list)
    selected_skills: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    tailored_resume: TailoredResume
    latex_string: str
    ats_report: str = ""
    diff_report: str = ""
    manifest: str = ""
    pdf_bytes: Optional[bytes] = None


def load_contact_info() -> ContactInfo:
    """Loads contact info. Prefers data/contact/personal/contact.yaml if available."""
    project_root = Path(__file__).resolve().parent.parent.parent
    personal_path = project_root / "data" / "contact" / "personal" / "contact.yaml"
    default_path = project_root / "data" / "contact.yaml"

    target_path = personal_path if personal_path.exists() else default_path
    if not target_path.exists():
        return ContactInfo()

    with open(target_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        return ContactInfo(**data)


def load_education() -> List[EducationItem]:
    """Loads education history. Prefers data/education/personal/education.yaml if available."""
    project_root = Path(__file__).resolve().parent.parent.parent
    personal_path = project_root / "data" / "education" / "personal" / "education.yaml"
    default_path = project_root / "data" / "education.yaml"

    target_path = personal_path if personal_path.exists() else default_path
    if not target_path.exists():
        return []

    with open(target_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        items = data.get("education", [])
        return [EducationItem(**item) for item in items]


def load_projects() -> List[ProjectItem]:
    """Loads projects. Prefers data/projects/personal/projects.yaml if available."""
    project_root = Path(__file__).resolve().parent.parent.parent
    personal_path = project_root / "data" / "projects" / "personal" / "projects.yaml"
    default_path = project_root / "data" / "projects.yaml"

    target_path = personal_path if personal_path.exists() else default_path
    if not target_path.exists():
        return []

    with open(target_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
        items = data.get("projects", [])
        return [ProjectItem(**item) for item in items]
