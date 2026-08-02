import os
import glob
import yaml
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator, field_validator


class Bullet(BaseModel):
    id: str
    text: str
    tags: List[str] = Field(default_factory=list)


class TitleConfig(BaseModel):
    default: str
    variants: List[str] = Field(default_factory=list)


class Experience(BaseModel):
    id: str
    company: str
    start: str
    end: str
    importance: int = 5
    optional: bool = False
    tags: List[str] = Field(default_factory=list)
    titles: TitleConfig
    bullets: List[Bullet] = Field(default_factory=list)

    @field_validator("end", mode="before")
    @classmethod
    def normalize_end_date(cls, v: str) -> str:
        if isinstance(v, str) and v.strip().lower() in ("current", "now"):
            return "Present"
        return v

    @model_validator(mode="after")
    def check_bullet_ids(self):
        seen = set()
        for b in self.bullets:
            if b.id in seen:
                raise ValueError(f"Duplicate bullet ID '{b.id}' in experience '{self.id}'")
            seen.add(b.id)
        return self


def load_experiences_from_dir(dir_path: Optional[str] = None) -> List[Experience]:
    """Loads experience YAML files. If data/experiences/personal/ exists and has files, loads personal data."""
    if not dir_path:
        project_root = Path(__file__).resolve().parent.parent.parent
        dir_path = str(project_root / "data" / "experiences")

    if not os.path.exists(dir_path):
        return []

    # Check for git-ignored personal directory overlay
    personal_dir = os.path.join(dir_path, "personal")
    personal_files = []
    if os.path.exists(personal_dir):
        personal_files = glob.glob(os.path.join(personal_dir, "*.yaml")) + glob.glob(os.path.join(personal_dir, "*.yml"))

    # If personal files exist, load from personal_dir; otherwise load top-level sample files
    if personal_files:
        target_files = sorted(personal_files)
    else:
        target_files = sorted(
            [f for f in glob.glob(os.path.join(dir_path, "*.yaml")) + glob.glob(os.path.join(dir_path, "*.yml"))
             if os.path.isfile(f)]
        )

    experiences = []
    for file_path in target_files:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data:
                experiences.append(Experience(**data))
    return experiences


class SkillItem(BaseModel):
    id: str
    display: str
    aliases: List[str] = Field(default_factory=list)
    category: Optional[str] = None


class SkillTaxonomy(BaseModel):
    skills: List[SkillItem] = Field(default_factory=list)

    @classmethod
    def load_from_yaml(cls, file_path: Optional[str] = None) -> "SkillTaxonomy":
        if not file_path:
            project_root = Path(__file__).resolve().parent.parent.parent
            file_path = str(project_root / "data" / "skills.yaml")

        if not os.path.exists(file_path):
            return cls()
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)
