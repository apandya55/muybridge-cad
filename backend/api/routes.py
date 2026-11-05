"""HTTP routes for generation, validation, and compiled artifacts."""
from __future__ import annotations

import re
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.sse import sse_response
from config import get_settings
from critic.critic_loop import run_loop
from critic.llm_client import LLMClient
from jobs.store import store
from schemas import GenerateRequest, ValidateRequest

router = APIRouter()


def _jobs_root() -> Path:
    return get_settings().jobs_root


def _create_job(code_type: str):
    try:
        return store.create(code_type)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc), headers={"Retry-After": "10"}) from exc


def _valid_job_id(job_id: str) -> bool:
    return re.fullmatch(r"[a-f0-9]{32}", job_id) is not None


@router.post("/generate")
def generate(req: GenerateRequest):
    """Draft source from a description, then run the review loop."""
    job = _create_job(req.code_type)

    def stream():
        try:
            llm = LLMClient()
            yield {"type": "start", "job_id": job.job_id, "code_type": req.code_type,
                   "message": "drafting source"}
            code = llm.draft_code(req.prompt, req.code_type, req.requested_dims)
            store.update(job.job_id, code=code, status="running")
            yield {"type": "fix", "iteration": 0, "job_id": job.job_id, "code": code,
                   "message": "draft ready"}
            for event in run_loop(job_id=job.job_id, code=code, code_type=req.code_type,
                                  requested_dims=req.requested_dims):
                if event.get("code"):
                    store.update(job.job_id, code=event["code"])
                yield event
                if event.get("type") in ("success", "failed", "error"):
                    store.update(job.job_id, status=event["type"])
        except Exception:  # pragma: no cover
            store.update(job.job_id, status="error")
            yield {"type": "error", "message": "Code generation failed. Check server logs and configuration."}
        finally:
            if store.get(job.job_id) and store.get(job.job_id).status in {"queued", "running"}:
                store.update(job.job_id, status="error")

    return sse_response(stream())


@router.post("/validate")
def validate(req: ValidateRequest):
    """Review source supplied by the user."""
    job = _create_job(req.code_type)

    def stream():
        try:
            store.update(job.job_id, code=req.code, status="running")
            for event in run_loop(job_id=job.job_id, code=req.code, code_type=req.code_type,
                                  requested_dims=req.requested_dims):
                if event.get("code"):
                    store.update(job.job_id, code=event["code"])
                yield event
                if event.get("type") in ("success", "failed", "error"):
                    store.update(job.job_id, status=event["type"])
        except Exception:  # pragma: no cover
            store.update(job.job_id, status="error")
            yield {"type": "error", "message": "Validation failed unexpectedly. Check server logs."}
        finally:
            if store.get(job.job_id) and store.get(job.job_id).status in {"queued", "running"}:
                store.update(job.job_id, status="error")

    return sse_response(stream())


@router.get("/stl/{job_id}")
def get_stl(job_id: str):
    if not _valid_job_id(job_id):
        raise HTTPException(status_code=404, detail="STL not found")
    p = _jobs_root() / job_id / "part.stl"
    if not p.exists():
        raise HTTPException(status_code=404, detail="STL not found")
    return FileResponse(str(p), media_type="model/stl", filename="part.stl")


@router.get("/plate/{job_id}")
def get_plate(job_id: str):
    if not _valid_job_id(job_id):
        raise HTTPException(status_code=404, detail="plate not found")
    p = _jobs_root() / job_id / "plate.png"
    if not p.exists():
        raise HTTPException(status_code=404, detail="plate not found")
    return FileResponse(str(p), media_type="image/png", filename="plate.png")


@router.get("/job/{job_id}")
def get_job(job_id: str):
    if not _valid_job_id(job_id):
        raise HTTPException(status_code=404, detail="job not found")
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {"job_id": job.job_id, "code": job.code, "code_type": job.code_type,
            "status": job.status, "created_at": job.created_at.isoformat()}
