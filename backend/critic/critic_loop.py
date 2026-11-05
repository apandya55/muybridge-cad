"""Compile, check, render, and review a part until it passes.

`run_loop` yields event dictionaries for the API layer. A pass can include a
model-suggested repair, subject to the configured iteration limit.
"""
from __future__ import annotations

import logging
from pathlib import Path

from compiler.base import CompilationError, OpenSCADNotInstalledError, get_compiler
from config import get_settings
from critic.llm_client import LLMClient
from geometry.checks import run_checks
from geometry.report import all_passed
from render.muybridge import render_plate
from schemas import CodeType, CritiqueResult, SSEEvent

logger = logging.getLogger(__name__)


def _make_job_dir(job_id: str) -> Path:
    root = get_settings().jobs_root / job_id
    root.mkdir(parents=True, exist_ok=True)
    return root


def run_loop(
    *,
    job_id: str,
    code: str,
    code_type: CodeType,
    requested_dims=None,
):
    """Yield SSEEvent dicts. Caller serializes to the wire."""
    settings = get_settings()
    job_dir = _make_job_dir(job_id)
    llm = LLMClient()
    current_code = code
    stl_path = job_dir / "part.stl"

    yield SSEEvent(type="start", job_id=job_id, code_type=code_type, message="starting").model_dump()

    for i in range(1, settings.critic_max_iterations + 1):
        yield SSEEvent(type="compiling", iteration=i, code=current_code, message=f"compiling pass {i}").model_dump()
        try:
            compiler = get_compiler(code_type)
            compiler.compile(current_code, stl_path)
        except OpenSCADNotInstalledError as e:
            logger.warning("OpenSCAD unavailable: %s", e)
            yield SSEEvent(type="error", iteration=i, message="OpenSCAD is unavailable. Install it or select build123d.").model_dump()
            return
        except CompilationError as e:
            yield SSEEvent(type="compiling", iteration=i, message=f"compile failed: {e}").model_dump()
            try:
                fixed = _ask_fix_from_error(llm, current_code, code_type, str(e), requested_dims)
            except Exception:
                logger.exception("LLM compile repair failed")
                yield SSEEvent(type="error", iteration=i, message="The model could not repair the compile error. Check provider configuration and server logs.").model_dump()
                return
            current_code = fixed
            yield SSEEvent(type="fix", iteration=i, code=current_code, message="applied compile repair").model_dump()
            continue

        try:
            mesh, assertions = run_checks(stl_path, requested_dims)
        except Exception:
            logger.exception("Geometry checks failed for job %s", job_id)
            yield SSEEvent(type="error", iteration=i, message="Geometry checks failed. Check server logs.").model_dump()
            return
        yield SSEEvent(type="assertions", iteration=i, assertions=assertions, message="checks complete").model_dump()

        try:
            png_path = render_plate(mesh, job_dir / "plate.png")
        except Exception:
            logger.exception("Plate render failed for job %s", job_id)
            yield SSEEvent(type="error", iteration=i, message="The inspection plate could not be rendered. Check server logs.").model_dump()
            return
        plate_url = f"/jobs/{job_id}/plate.png"
        stl_url = f"/jobs/{job_id}/part.stl"
        yield SSEEvent(type="plate", iteration=i, plate_url=plate_url, stl_url=stl_url, message="inspection plate ready").model_dump()

        if not settings.effective_api_key:
            passed = all_passed(assertions)
            critique = CritiqueResult(
                approved=passed,
                errors=[] if passed else [a.message for a in assertions if not a.passed],
                critique=(
                    "Geometric assertions verified. Vision review skipped (no LLM API key configured)."
                    if passed
                    else "Geometric assertions failed. Vision review skipped (no LLM API key configured)."
                ),
                suggested_code="",
            )
            yield SSEEvent(type="critique", iteration=i, critique=critique, message="checks evaluated").model_dump()
            if passed:
                yield SSEEvent(type="success", iteration=i, code=current_code, plate_url=plate_url, stl_url=stl_url, message="validation passed").model_dump()
                return
            yield SSEEvent(type="failed", iteration=i, code=current_code, message="geometric checks failed").model_dump()
            return

        try:
            critique = llm.vision_critique(
                png_path.read_bytes(), assertions, current_code, code_type, requested_dims
            )
        except Exception:
            logger.exception("Vision critic failed for job %s", job_id)
            yield SSEEvent(type="error", iteration=i, message="The vision critic failed. Check provider configuration and server logs.").model_dump()
            return

        yield SSEEvent(type="critique", iteration=i, critique=critique, message="review complete").model_dump()

        if critique.approved and all_passed(assertions):
            yield SSEEvent(type="success", iteration=i, code=current_code, plate_url=plate_url, stl_url=stl_url, message="validation passed").model_dump()
            return

        # Use the review's source when it supplied one.
        new_code = critique.suggested_code.strip()
        if not new_code:
            try:
                new_code = _ask_fix_from_error(llm, current_code, code_type, critique.critique or "see critique", requested_dims)
            except Exception:
                logger.exception("LLM critic repair failed for job %s", job_id)
                yield SSEEvent(type="error", iteration=i, message="The model could not produce a repair. Check server logs.").model_dump()
                return
        current_code = new_code
        yield SSEEvent(type="fix", iteration=i, code=current_code, message="applied review repair").model_dump()

    yield SSEEvent(type="failed", iteration=settings.critic_max_iterations, code=current_code, message="max iterations reached without passing").model_dump()


def _ask_fix_from_error(llm: LLMClient, code: str, code_type: CodeType, error: str, requested_dims) -> str:
    """Text-only call asking the LLM to fix code given an error/critique."""
    from critic.prompts import CODEGEN_SYSTEM
    lang = "OpenSCAD" if code_type == "openscad" else "build123d (Python)"
    system = CODEGEN_SYSTEM.format(lang=lang)
    user = (
        f"The following {lang} code failed or was critiqued:\n```{lang}\n{code}\n```\n\n"
        f"Problem:\n{error}\n\nReturn ONLY the corrected full code in a single fenced block."
    )
    raw = llm._call(system, [{"role": "user", "content": user}])
    import re
    m = re.search(r"```(?:python|openscad|scad)?\s*([\s\S]+?)```", raw, re.IGNORECASE)
    return m.group(1).strip() if m else raw.strip()
