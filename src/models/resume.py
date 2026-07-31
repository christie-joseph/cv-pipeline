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


class TailoredResume(BaseModel):
    selected_experiences: List[SelectedExperience] = Field(default_factory=list)
    selected_skills: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class PipelineResult(BaseModel):
    tailored_resume: TailoredResume
    latex_string: str
    ats_report: str = ""
    diff_report: str = ""
    manifest: str = ""
    pdf_bytes: Optional[bytes] = None
