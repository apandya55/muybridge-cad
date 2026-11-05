from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from config import get_settings

CodeType = Literal["openscad", "build123d"]


class Dims(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)

    x: float | None = Field(default=None, gt=0, le=10_000)
    y: float | None = Field(default=None, gt=0, le=10_000)
    z: float | None = Field(default=None, gt=0, le=10_000)


class GenerateRequest(BaseModel):
    """Describe a part and have the service draft its source code."""
    prompt: str = Field(..., min_length=1, max_length=get_settings().max_prompt_chars)
    code_type: CodeType = "build123d"
    requested_dims: Dims = Field(default_factory=Dims)


class ValidateRequest(BaseModel):
    """Compile and review source code supplied by the user."""
    code: str = Field(..., min_length=1, max_length=get_settings().max_code_chars)
    code_type: CodeType = "build123d"
    requested_dims: Dims = Field(default_factory=Dims)


class Assertion(BaseModel):
    name: str
    passed: bool
    value: float | str | None = None
    threshold: float | str | None = None
    message: str = ""


class CritiqueResult(BaseModel):
    approved: bool
    errors: list[str] = Field(default_factory=list)
    critique: str = ""
    suggested_code: str = ""


class SSEEvent(BaseModel):
    type: Literal[
        "start", "compiling", "assertions", "plate",
        "critique", "fix", "success", "failed", "error",
    ]
    iteration: int = 0
    message: str = ""
    code: str | None = None
    assertions: list[Assertion] | None = None
    plate_url: str | None = None
    stl_url: str | None = None
    critique: CritiqueResult | None = None
    job_id: str | None = None
    code_type: CodeType | None = None
