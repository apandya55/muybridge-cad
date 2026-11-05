"""Compile build123d source in a restricted subprocess.

The user's code is expected to build a part bound to the top-level name `part`
(the documented convention). We append an export hook that reads the target
STL path from the MBRIDGE_OUT env var and writes it, then run the combined
script with `python3 -I` (isolated imports) so the user's code cannot pull in
local modules via sys.path tricks.
"""
from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

from config import get_settings
from compiler.base import CompilationError, CompilationResult

# The hook exports `part` (or the last Shape value) to MBRIDGE_OUT.
_EXPORT_HOOK = textwrap.dedent(
    """\n
    # Export hook added by the compiler.
    import os as __mb_os
    __mb_out = __mb_os.environ.get("MBRIDGE_OUT")
    if not __mb_out:
        raise SystemExit("MBRIDGE_OUT not set")
    try:
        from build123d import export_stl, Compound, Shape, BuildPart
    except Exception as __e:
        raise SystemExit(f"build123d import failed: {__e}")
    __mb_part = globals().get("part")
    if __mb_part is None:
        for __v in list(globals().values()):
            if isinstance(__v, BuildPart) and getattr(__v, "part", None):
                __mb_part = __v.part
                break
    if __mb_part is None:
        __mb_cands = [v for v in globals().values() if isinstance(v, (Shape, Compound))]
        if not __mb_cands:
            raise SystemExit("no build123d `part` found; assign your object to `part`")
        __mb_part = __mb_cands[-1]
    try:
        export_stl(__mb_part, __mb_out)
    except Exception as __e:
        raise SystemExit(f"export failed: {__e}")
    """
)


def _limit_resources() -> None:
    """Apply process limits before running CAD source on POSIX hosts."""
    try:
        import resource
        settings = get_settings()
        resource.setrlimit(resource.RLIMIT_CPU, (settings.compile_timeout_s, settings.compile_timeout_s + 1))
        resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024 * 1024, 128 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_NOFILE, (1024, 1024))
    except (ImportError, OSError, ValueError):
        pass


class Build123dCompiler:
    def compile(self, code: str, out_path: Path) -> CompilationResult:
        settings = get_settings()
        out_path = Path(out_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        full_script = code + "\n" + _EXPORT_HOOK
        env = {
            "PATH": os.environ.get("PATH", ""),
            "HOME": str(out_path.parent),
            "MBRIDGE_OUT": str(out_path),
        }
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", full_script],
                capture_output=True,
                text=True,
                timeout=settings.compile_timeout_s,
                env=env,
                preexec_fn=_limit_resources if os.name == "posix" else None,
            )
        except subprocess.TimeoutExpired as exc:
            raise CompilationError(
                f"build123d timed out after {settings.compile_timeout_s}s"
            ) from exc

        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        if proc.returncode != 0 or not out_path.exists():
            tail = "\n".join((stderr or stdout).strip().splitlines()[-10:])
            raise CompilationError(f"build123d failed (rc={proc.returncode}):\n{tail}")
        return CompilationResult(stl_path=out_path, stdout=stdout, stderr=stderr)
