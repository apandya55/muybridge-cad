# Anthropic and OpenAI-compatible vision/text model client
from __future__ import annotations

import base64

from config import get_settings
from critic.parser import parse_critique
from critic.prompts import (
    CODEGEN_SYSTEM,
    CODEGEN_USER,
    CRITIC_SYSTEM,
    CRITIC_USER,
)
from schemas import CodeType, CritiqueResult


def _format_dims(requested_dims) -> str:
    parts = []
    for axis in ("x", "y", "z"):
        v = getattr(requested_dims, axis, None)
        if v is not None:
            parts.append(f"{axis}={v}")
    return ", ".join(parts) or "none"


def _format_assertions(assertions: list) -> str:
    return "\n".join(
        f"  {'PASS' if a.passed else 'FAIL'}  {a.name}: {a.message}" for a in assertions
    )


class LLMClient:
    """Call the provider selected in the application settings."""

    def _call_anthropic(self, system: str, messages: list) -> str:
        import anthropic
        settings = get_settings()
        client = anthropic.Anthropic(api_key=settings.effective_api_key)
        resp = client.messages.create(
            model=settings.llm_model,
            max_tokens=settings.llm_max_tokens,
            system=system,
            messages=messages,
        )
        return resp.content[0].text

    def _call_openai(self, system: str, messages: list) -> str:
        import httpx
        settings = get_settings()
        base = settings.llm_base_url.rstrip("/")
        url = f"{base}/chat/completions"
        payload = {
            "model": settings.llm_model,
            "max_tokens": settings.llm_max_tokens,
            "messages": [{"role": "system", "content": system}, *messages],
        }
        r = httpx.post(
            url,
            json=payload,
            headers={"Authorization": f"Bearer {settings.effective_api_key}"},
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

    def _call(self, system: str, messages: list) -> str:
        p = get_settings().llm_provider
        if p == "anthropic":
            return self._call_anthropic(system, messages)
        return self._call_openai(system, messages)

    def _image_content(self, image_bytes: bytes) -> dict:
        b64 = base64.b64encode(image_bytes).decode()
        settings = get_settings()
        if settings.llm_provider == "anthropic":
            return {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}}
        return {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}}

    def draft_code(self, prompt: str, code_type: CodeType, requested_dims=None) -> str:
        lang = "OpenSCAD" if code_type == "openscad" else "build123d (Python)"
        dims = _format_dims(requested_dims) if requested_dims else "none"
        system = CODEGEN_SYSTEM.format(lang=lang)
        user = CODEGEN_USER.format(prompt=prompt, dims=dims, lang=lang)
        raw = self._call(system, [{"role": "user", "content": user}])
        import re
        m = re.search(r"```(?:python|openscad|scad)?\s*([\s\S]+?)```", raw, re.IGNORECASE)
        return m.group(1).strip() if m else raw.strip()

    def vision_critique(
        self,
        plate_bytes: bytes,
        assertions: list,
        code: str,
        code_type: CodeType,
        requested_dims=None,
    ) -> CritiqueResult:
        lang = "OpenSCAD" if code_type == "openscad" else "build123d"
        settings = get_settings()
        system = CRITIC_SYSTEM.format(lang=lang)
        user_text = CRITIC_USER.format(
            lang=lang,
            code=code,
            assertions=_format_assertions(assertions),
            dims=_format_dims(requested_dims) if requested_dims else "none",
        )
        content: list = [self._image_content(plate_bytes), {"type": "text", "text": user_text}]
        raw = self._call(system, [{"role": "user", "content": content}])
        return parse_critique(raw)
