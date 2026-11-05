# Extract and validate critique JSON from LLM output
from __future__ import annotations

import json
import re

from schemas import CritiqueResult

_JSON_FENCE_RE = re.compile(r"```json\s*([\s\S]+?)\s*```", re.IGNORECASE)
_BARE_JSON_RE = re.compile(r"\{[\s\S]+\}", re.DOTALL)


def _extract_json(text: str) -> str | None:
    # Prefer a fenced block.
    m = _JSON_FENCE_RE.search(text)
    if m:
        return m.group(1)
    # Fall back to the last bare JSON object.
    matches = list(_BARE_JSON_RE.finditer(text))
    return matches[-1].group(0) if matches else None


def parse_critique(text: str) -> CritiqueResult:
    raw = _extract_json(text)
    if raw is None:
        return CritiqueResult(
            approved=False,
            errors=["LLM response did not contain a JSON block"],
            critique=text[:200],
            suggested_code="",
        )
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return CritiqueResult(
            approved=False,
            errors=[f"JSON parse error: {exc}"],
            critique=raw[:200],
            suggested_code="",
        )
    return CritiqueResult(
        approved=bool(data.get("approved", False)),
        errors=list(data.get("errors", [])),
        critique=str(data.get("critique", "")),
        suggested_code=str(data.get("suggested_code", "")),
    )
