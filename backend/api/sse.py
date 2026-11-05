"""Write event dictionaries in server-sent event format."""
from __future__ import annotations

import json
import logging
from typing import Iterable

from fastapi.responses import StreamingResponse

logger = logging.getLogger(__name__)


def _serialize(event: dict) -> bytes:
    type_ = event.get("type", "message")
    data = json.dumps(event, default=str)
    return f"event: {type_}\ndata: {data}\n\n".encode("utf-8")


def sse_response(generator: Iterable[dict]) -> StreamingResponse:
    def gen():
        try:
            for event in generator:
                yield _serialize(event)
        except GeneratorExit:
            raise
        except Exception:
            logger.exception("Unhandled exception while streaming job events")
            yield _serialize({"type": "error", "message": "The job failed unexpectedly. Check server logs."})
    return StreamingResponse(gen(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    })
