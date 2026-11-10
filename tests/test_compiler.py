import pytest
from pathlib import Path
from compiler.base import CompilationError, get_compiler
from compiler.build123d_runner import Build123dCompiler
from compiler.openscad import OpenSCADCompiler


def test_build123d_valid_compilation(tmp_path):
    code = """
from build123d import *
with BuildPart() as bp:
    Box(20, 20, 10)
part = bp.part
"""
    out_stl = tmp_path / "part.stl"
    compiler = Build123dCompiler()
    res = compiler.compile(code, out_stl)
    assert res.stl_path.exists()
    assert res.stl_path.stat().st_size > 0


def test_build123d_syntax_error(tmp_path):
    code = "this is total gibberish def broken"
    out_stl = tmp_path / "part.stl"
    compiler = Build123dCompiler()
    with pytest.raises(CompilationError):
        compiler.compile(code, out_stl)


def test_build123d_fallback_part_discovery(tmp_path):
    # Code that defines a solid without explicitly setting `part = ...`
    code = """
from build123d import *
with BuildPart() as bp:
    Box(15, 15, 15)
"""
    out_stl = tmp_path / "part.stl"
    compiler = Build123dCompiler()
    res = compiler.compile(code, out_stl)
    assert res.stl_path.exists()
    assert res.stl_path.stat().st_size > 0


def test_get_compiler_lookup():
    assert isinstance(get_compiler("build123d"), Build123dCompiler)
    assert isinstance(get_compiler("openscad"), OpenSCADCompiler)
