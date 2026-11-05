# FastAPI app entrypoint
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import router
from config import get_settings

app = FastAPI(title="muybridge-cad", version="0.1.0", docs_url=None, redoc_url=None)

settings = get_settings()


@app.middleware("http")
async def request_size_limit(request: Request, call_next):
    """Reject oversized JSON before parsing it into a Pydantic model."""
    content_length = request.headers.get("content-length")
    try:
        body_size = int(content_length) if content_length else 0
    except ValueError:
        return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length header."})
    if body_size > settings.max_code_chars + 1_000_000:
        return JSONResponse(status_code=413, content={"detail": "Request body is too large."})
    return await call_next(request)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

# Keep generated files outside the application directory.
JOBS_ROOT = settings.jobs_root
JOBS_ROOT.mkdir(parents=True, exist_ok=True)
app.mount(
    "/jobs", StaticFiles(directory=str(JOBS_ROOT), check_dir=True), name="jobs"
)

app.include_router(router, prefix="/api")


@app.get("/")
def root() -> dict[str, str]:
    return {"name": "muybridge-cad", "status": "ok"}


@app.get("/api/health", include_in_schema=False)
def health() -> dict[str, object]:
    s = get_settings()
    return {
        "openscad_installed": s.openscad_bin is not None,
        "openscad_bin": s.openscad_bin,
        "llm_provider": s.llm_provider,
        "llm_configured": bool(s.effective_api_key),
        "critic_max_iterations": s.critic_max_iterations,
    }
