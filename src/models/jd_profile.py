from typing import List, Optional
from pydantic import BaseModel, Field


class JDProfile(BaseModel):
    role: Optional[str] = None
    seniority: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    raw_text: str = ""
