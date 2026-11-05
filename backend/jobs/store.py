# In-memory job state
from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from config import get_settings


@dataclass
class Job:
    job_id: str
    code: str = ""
    code_type: str = "build123d"
    status: str = "running"  # running | success | failed | error
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()

    def create(self, code_type: str) -> Job:
        with self._lock:
            active = sum(job.status in {"queued", "running"} for job in self._jobs.values())
            if active >= get_settings().max_active_jobs:
                raise RuntimeError("The service is at capacity. Try again shortly.")
            job = Job(job_id=uuid.uuid4().hex, code_type=code_type)
            self._jobs[job.job_id] = job
            if len(self._jobs) > get_settings().max_jobs:
                finished = sorted((j for j in self._jobs.values() if j.status not in {"queued", "running"}), key=lambda j: j.created_at)
                for old in finished[: max(0, len(self._jobs) - get_settings().max_jobs)]:
                    self._jobs.pop(old.job_id, None)
        return job

    def update(self, job_id: str, **fields) -> None:
        with self._lock:
            job = self._jobs.get(job_id)
            if job:
                for k, v in fields.items():
                    setattr(job, k, v)

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self._jobs.get(job_id)


store = JobStore()
