from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "Gotinha"
    app_version: str = "0.1.0"
    fastapi_host: str = "0.0.0.0"
    fastapi_port: int = 8000
    precision_mode: Literal["balanced", "max_precision"] = "max_precision"
    chunk_size: int = 1000
    chunk_overlap: int = 150
    default_top_k: int = 8
    max_top_k: int = 8
    min_relevance_score: float = 0.51
    min_overlap_terms: int = 3
    documents_dir: str = "pdf/atencao_basica"
    auto_ingest_on_startup: bool = True
    groq_api_key: str | None = None
    groq_model: str = "llama-3.1-70b-versatile"
    groq_temperature: float = 0.0
    groq_base_url: str = "https://api.groq.com/openai/v1/chat/completions"
    groq_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
    )

    @model_validator(mode="after")
    def apply_precision_profile(self) -> "Settings":
        profile_defaults = {
            "balanced": {
                "chunk_size": 1200,
                "chunk_overlap": 150,
                "default_top_k": 3,
                "min_relevance_score": 0.3,
                "min_overlap_terms": 2,
                "groq_temperature": 0.1,
            },
            "max_precision": {
                "chunk_size": 1200,
                "chunk_overlap": 200,
                "default_top_k": 6,
                "min_relevance_score": 0.75,
                "min_overlap_terms": 3,
                "groq_temperature": 0.8,
            },
        }[self.precision_mode]
        explicit_fields = set(self.model_fields_set)

        for field_name, value in profile_defaults.items():
            if field_name not in explicit_fields:
                setattr(self, field_name, value)

        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
