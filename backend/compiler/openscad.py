from __future__ import annotations

import subprocess
import tempfile
import os
from pathlib import Path

from config import get_settings
from compiler.base import (
    CompilationError,
    CompilationResult,
    OpenSCADNotInstalledError,
)


def _limit_resources() -> None:
    try:
        import resource
        settings = get_settings()
        resource.setrlimit(resource.RLIMIT_CPU, (settings.compile_timeout_s, settings.compile_timeout_s + 1))
        resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024 * 1024, 128 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))
    except (ImportError, OSError, ValueError):
        pass


class OpenSCADCompiler:
    def compile(self, code: str, out_path: Path) -> CompilationResult:
        settings = get_settings()
        bin_path = settings.openscad_bin
        if bin_path is None:
            raise OpenSCADNotInstalledError(
                "The `openscad` binary was not found on PATH. "
                "Install it (`brew install openscad` on macOS) or set OPENSCAD_BIN."
            )

        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Write source to a temp .scad next to the output so relative paths resolve.
        with tempfile.NamedTemporaryFile(
            "w", suffix=".scad", dir=str(out_path.parent), delete=False
        ) as fh:
            fh.write(code)
            scad_path = Path(fh.name)

        try:
            proc = subprocess.run(
                [bin_path, "-o", str(out_path), str(scad_path)],
                capture_output=True,
                text=True,
                timeout=settings.compile_timeout_s,
                env={"PATH": os.environ.get("PATH", ""), "HOME": str(out_path.parent)},
                preexec_fn=_limit_resources if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired as exc:
            raise CompilationError(
                f"openscad timed out after {settings.compile_timeout_s}s"
            ) from exc
        finally:
            try:
                scad_path.unlink()
            except OSError:
                pass

        if proc.returncode != 0 or not out_path.exists():
            raise CompilationError(
                f"openscad failed (rc={proc.returncode}):\n{proc.stderr.strip()}"
            )

        return CompilationResult(stl_path=out_path, stdout=proc.stdout, stderr=proc.stderr)
