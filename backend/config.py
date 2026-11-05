# Settings and runtime config
from __future__ import annotations

import os
import shutil
from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # HTTP/runtime limits. Set CORS_ORIGINS to a comma-separated list in deploys.
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    max_active_jobs: int = Field(default=2, ge=1, le=64)
    max_prompt_chars: int = Field(default=8_000, ge=1, le=100_000)
    max_code_chars: int = Field(default=100_000, ge=1, le=1_000_000)
    max_jobs: int = Field(default=1_000, ge=1, le=100_000)
    jobs_dir: str = ""

    # Review settings.
    critic_max_iterations: int = Field(default=3, ge=1, le=10)
    compile_timeout_s: int = Field(default=30, ge=1, le=300)
    min_wall_thickness_mm: float = 1.0
    bbox_tolerance_mm: float = 0.5
    wall_thickness_samples: int = Field(default=256, ge=0, le=20_000)

    # Vision model settings.
    llm_provider: Literal["anthropic", "openai"] = "anthropic"
    llm_model: str = "claude-sonnet-5-5"
    llm_api_key: str = ""
    anthropic_api_key: str = ""
    llm_base_url: str = ""
    llm_max_tokens: int = Field(default=4096, ge=64, le=32_000)

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def jobs_root(self):
        from pathlib import Path
        import tempfile
        return Path(self.jobs_dir).expanduser() if self.jobs_dir else Path(tempfile.gettempdir()) / "muybridge-jobs"

    @property
    def effective_api_key(self) -> str:
        if self.llm_provider == "anthropic":
            return self.llm_api_key or self.anthropic_api_key or os.getenv("ANTHROPIC_API_KEY", "")
        return self.llm_api_key

    @property
    def openscad_bin(self) -> str | None:
        override = os.getenv("OPENSCAD_BIN")
        if override:
            return override
        return shutil.which("openscad")


@lru_cache
def get_settings() -> Settings:
    return Settings()
