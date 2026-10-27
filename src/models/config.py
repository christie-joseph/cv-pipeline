import os
import yaml
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, model_validator


class ApiProviderConfig(BaseModel):
    name: str = "openrouter"
    api_url: str = "https://openrouter.ai/api/v1"
    api_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    api_key_env: str = "OPENROUTER_API_KEY"
    timeout_seconds: int = 10
    max_tokens: int = 100
    temperature: float = 0.3
    priority: int = 100  # Lower number = higher priority (e.g. 0 is top priority)
    enabled: bool = True


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
    providers: List[ApiProviderConfig] = Field(default_factory=list)
    ollama_model: str = "qwen2.5:1.5b"
    ollama_timeout: int = 30

    # Legacy fields for backwards compatibility
    api_url: str = ""
    api_model: str = ""
    timeout_seconds: int = 5

    @model_validator(mode="after")
    def populate_default_providers(self):
        # 1. If no providers specified but legacy fields exist, create a provider from legacy fields
        if not self.providers and self.api_url and self.api_model:
            self.providers = [
                ApiProviderConfig(
                    name="legacy_api",
                    api_url=self.api_url,
                    api_model=self.api_model,
                    api_key_env="LLM_API_KEY",
                    timeout_seconds=self.timeout_seconds,
                    priority=10
                )
            ]
        elif not self.providers:
            # Default provider stack with user-requested priority order:
            # 1st OpenRouter -> 2nd Gemini -> 3rd Cerebras -> 4th Groq
            self.providers = [
                ApiProviderConfig(
                    name="openrouter",
                    api_url="https://openrouter.ai/api/v1",
                    api_model="meta-llama/llama-3.3-70b-instruct:free",
                    api_key_env="OPENROUTER_API_KEY",
                    timeout_seconds=10,
                    priority=1
                ),
                ApiProviderConfig(
                    name="gemini",
                    api_url="https://generativelanguage.googleapis.com/v1beta/openai",
                    api_model="gemini-3.8-flash",

                    api_key_env="GEMINI_API_KEY",
                    timeout_seconds=10,
                    priority=2
                ),
                ApiProviderConfig(
                    name="cerebras",
                    api_url="https://api.cerebras.ai/v1",
                    api_model="llama3.1-8b",
                    api_key_env="CEREBRAS_API_KEY",
                    timeout_seconds=8,
                    priority=3
                ),
                ApiProviderConfig(
                    name="groq",
                    api_url="https://api.groq.com/openai/v1",
                    api_model="llama-3.3-70b-versatile",
                    api_key_env="GROQ_API_KEY",
                    timeout_seconds=5,
                    priority=4
                ),
            ]

        # 2. Check for dynamic CUSTOM_API_KEY in environment to auto-register top-priority custom provider
        custom_key = os.getenv("CUSTOM_API_KEY")
        if custom_key and len(custom_key.strip()) > 0:
            custom_name = os.getenv("CUSTOM_API_NAME", "custom")
            custom_url = os.getenv("CUSTOM_API_URL", "https://api.openai.com/v1")
            custom_model = os.getenv("CUSTOM_API_MODEL", "gpt-4o-mini")
            custom_priority = int(os.getenv("CUSTOM_API_PRIORITY", "0"))  # Priority 0 by default (top priority)

            # Avoid duplicate custom provider if already defined
            if not any(p.name == custom_name for p in self.providers):
                self.providers.append(
                    ApiProviderConfig(
                        name=custom_name,
                        api_url=custom_url,
                        api_model=custom_model,
                        api_key_env="CUSTOM_API_KEY",
                        timeout_seconds=10,
                        priority=custom_priority
                    )
                )

        # 3. Sort providers by priority (ascending: 0, 1, 2, 3...)
        self.providers.sort(key=lambda p: p.priority)
        return self


class OutputConfig(BaseModel):
    compile_pdf: bool = True
    open_pdf: bool = True
    show_ats_report: bool = True
    show_diff: bool = True
    show_manifest: bool = False
    copy_to_clipboard: bool = False
    debug: bool = False


class PipelineConfig(BaseModel):
    max_experiences: int = 3
    max_bullets_per_experience: int = 3
    minimum_similarity: float = 0.25
    mmr_lambda: float = 0.7
    debug: bool = False
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
