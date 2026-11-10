import trimesh
import numpy as np
from geometry.checks import (
    check_watertight,
    check_manifold,
    check_wall_thickness,
    check_bounding_box,
)
from schemas import Dims


def test_box_mesh_watertight_and_manifold():
    # 20x20x20 solid cube
    box = trimesh.creation.box(extents=(20, 20, 20))
    
    wt = check_watertight(box)
    assert wt.passed is True
    assert "watertight" in wt.message

    mf = check_manifold(box)
    assert mf.passed is True
    assert "positive" in mf.message


def test_bounding_box_checks():
    box = trimesh.creation.box(extents=(30, 20, 10))

    # Without target
    bb_no_target = check_bounding_box(box, None)
    assert bb_no_target.passed is True

    # Matching target
    target = Dims(x=30.0, y=20.0, z=10.0)
    bb_match = check_bounding_box(box, target)
    assert bb_match.passed is True

    # Exceeding target tolerance
    target_fail = Dims(x=50.0, y=20.0, z=10.0)
    bb_fail = check_bounding_box(box, target_fail)
    assert bb_fail.passed is False
    assert "Δ20.00" in bb_fail.message


def test_wall_thickness_solid_box():
    # Solid 20mm cube should have minimum wall thickness >= 1.0mm
    box = trimesh.creation.box(extents=(20, 20, 20))
    wt = check_wall_thickness(box)
    assert wt.passed is True
