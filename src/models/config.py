import os
import yaml
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field, model_validator


class WeightsConfig(BaseModel):
    tfidf: float = 0.35
    embedding: float = 0.30
    skill_overlap: float = 0.20
    importance: float = 0.10
    company_boost: float = 0.05

    @model_validator(mode="after")
    def normalize_weights(self):
        total = self.tfidf + self.embedding + self.skill_overlap + self.importance + self.company_boost
        if abs(total - 1.0) > 1e-4 and total > 0:
            self.tfidf /= total
            self.embedding /= total
            self.skill_overlap /= total
            self.importance /= total
            self.company_boost /= total
        return self


class RewriterConfig(BaseModel):
    enabled: bool = True
    api_url: str = "https://generativelanguage.googleapis.com/v1beta/openai"
    api_model: str = "gemini-2.5-flash"
    ollama_model: str = "qwen2.5:1.5b"
    timeout_seconds: int = 5


class OutputConfig(BaseModel):
    compile_pdf: bool = True
    open_pdf: bool = True
    show_ats_report: bool = True
    show_diff: bool = True
    show_manifest: bool = True
    copy_to_clipboard: bool = False


class PipelineConfig(BaseModel):
    max_experiences: int = 3
    max_bullets_per_experience: int = 3
    minimum_similarity: float = 0.25
    mmr_lambda: float = 0.7
    weights: WeightsConfig = Field(default_factory=WeightsConfig)
    embedding_model: str = "BAAI/bge-small-en-v1.5"
    rewriter: RewriterConfig = Field(default_factory=RewriterConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    rewriter_prompt: str = (
        "Rewrite only wording to align with job description keywords.\n"
        "Do not add unverified facts.\n"
        "Do not remove metrics or numbers.\n"
        "Do not change technologies or specific tool names.\n"
        "Keep changes subtle and professional.\n"
        "Return exactly one sentence.\n"
    )

    @classmethod
    def load_from_yaml(cls, path: Optional[str] = None) -> "PipelineConfig":
        if not path:
            project_root = Path(__file__).resolve().parent.parent.parent
            path = str(project_root / "config.yaml")

        if not os.path.exists(path):
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)
