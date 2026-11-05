from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class CompilationResult:
    stl_path: Path
    stdout: str = ""
    stderr: str = ""


class CompilationError(Exception):
    """Raised when user CAD code fails to compile to a valid STL."""


class OpenSCADNotInstalledError(CompilationError):
    """The openscad binary is not available on PATH."""


@runtime_checkable
class Compiler(Protocol):
    def compile(self, code: str, out_path: Path) -> CompilationResult:
        ...


def get_compiler(code_type: str) -> Compiler:
    """Factory keyed by the user-selected CAD language."""
    if code_type == "openscad":
        from compiler.openscad import OpenSCADCompiler
        return OpenSCADCompiler()
    if code_type == "build123d":
        from compiler.build123d_runner import Build123dCompiler
        return Build123dCompiler()
    raise ValueError(f"unknown code_type: {code_type!r}")
