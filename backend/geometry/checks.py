from __future__ import annotations

from collections import defaultdict
from pathlib import Path

import numpy as np
import trimesh

from config import get_settings
from geometry.report import Assertion


def _load(stl_path: Path) -> trimesh.Trimesh:
    mesh = trimesh.load(str(stl_path), force="mesh")
    if isinstance(mesh, trimesh.Scene):
        mesh = trimesh.util.concatenate([g for g in mesh.geometry.values()])
    return mesh


def check_watertight(mesh: trimesh.Trimesh) -> Assertion:
    wt = bool(mesh.is_watertight)
    return Assertion(
        name="watertight",
        passed=wt,
        value=wt,
        threshold=True,
        message="mesh is watertight" if wt else "mesh has holes / open boundaries",
    )


def check_manifold(mesh: trimesh.Trimesh) -> Assertion:
    # Edges should be shared by exactly two faces in a manifold solid
    edges = mesh.edges_unique
    face_count = np.zeros(len(edges), dtype=int)
    unique_index = {tuple(e): i for i, e in enumerate(edges)}
    for face in mesh.faces:
        for a, b in ((face[0], face[1]), (face[1], face[2]), (face[2], face[0])):
            key = tuple(sorted((int(a), int(b))))
            face_count[unique_index[key]] += 1

    non_manifold = int((face_count != 2).sum())
    is_volume = bool(mesh.is_volume)
    passed = non_manifold == 0 and is_volume
    return Assertion(
        name="manifold",
        passed=passed,
        value=f"{non_manifold} non-manifold edges",
        threshold="0 non-manifold edges",
        message=(
            "all edges shared by exactly two faces, volume positive"
            if passed
            else f"{non_manifold} edges not shared by two faces; is_volume={is_volume}"
        ),
    )


def check_wall_thickness(mesh: trimesh.Trimesh) -> Assertion:
    settings = get_settings()
    n = settings.wall_thickness_samples
    if n <= 0:
        return Assertion(
            name="wall_thickness",
            passed=True,
            value="n/a",
            threshold=f">= {settings.min_wall_thickness_mm} mm",
            message="no samples taken",
        )

    samples = mesh.sample(n)
    if len(samples) == 0:
        return Assertion(
            name="wall_thickness",
            passed=True,
            value="n/a",
            threshold=f">= {settings.min_wall_thickness_mm} mm",
            message="no surface samples available",
        )

    _, _, tri_id = trimesh.proximity.closest_point(mesh, samples)
    normals = mesh.face_normals[tri_id]

    # Offset ray origin slightly inward along the inward normal to avoid self-intersection
    eps = 1e-3
    origins = samples - normals * eps
    directions = -normals
    locations, ray_idx, _ = mesh.ray.intersects_location(origins, directions)

    if len(locations) == 0:
        return Assertion(
            name="wall_thickness",
            passed=False,
            value="no ray hits",
            threshold=f">= {settings.min_wall_thickness_mm} mm",
            message="inward rays did not hit opposite wall; geometry may be open",
        )

    # Group hits by originating ray and find the first opposite surface
    ray_hits = defaultdict(list)
    for loc, ri in zip(locations, ray_idx):
        d = float(np.linalg.norm(loc - origins[ri]))
        if d > 1e-4:
            ray_hits[ri].append(d + eps)

    if not ray_hits:
        return Assertion(
            name="wall_thickness",
            passed=False,
            value="no valid hits",
            threshold=f">= {settings.min_wall_thickness_mm} mm",
            message="all ray hits fell below minimum measurement tolerance",
        )

    min_per_ray = np.array([min(hits) for hits in ray_hits.values()])
    tmin = float(min_per_ray.min())
    tmean = float(min_per_ray.mean())
    tmax = float(min_per_ray.max())
    passed = tmin >= settings.min_wall_thickness_mm

    return Assertion(
        name="wall_thickness",
        passed=passed,
        value=f"min {tmin:.2f} / mean {tmean:.2f} / max {tmax:.2f} mm",
        threshold=f">= {settings.min_wall_thickness_mm} mm (min)",
        message=(
            f"min wall {tmin:.2f} mm"
            + ("" if passed else f" below {settings.min_wall_thickness_mm} mm")
        ),
    )


def check_bounding_box(mesh: trimesh.Trimesh, requested_dims=None) -> Assertion:
    settings = get_settings()
    ext = mesh.bounding_box.extents
    dims = {"x": float(ext[0]), "y": float(ext[1]), "z": float(ext[2])}

    def _get_dim(obj, axis):
        if obj is None:
            return None
        if isinstance(obj, dict):
            return obj.get(axis)
        return getattr(obj, axis, None)

    req_x = _get_dim(requested_dims, "x")
    req_y = _get_dim(requested_dims, "y")
    req_z = _get_dim(requested_dims, "z")

    if req_x is None and req_y is None and req_z is None:
        return Assertion(
            name="bounding_box",
            passed=True,
            value=f"{dims['x']:.2f} x {dims['y']:.2f} x {dims['z']:.2f} mm",
            threshold="none requested",
            message="dimensions measured (no target)",
        )

    tol = settings.bbox_tolerance_mm
    diffs = {}
    passed = True
    for axis, target in (("x", req_x), ("y", req_y), ("z", req_z)):
        if target is None:
            continue
        target_f = float(target)
        d = abs(dims[axis] - target_f)
        diffs[axis] = (dims[axis], target_f, d)
        if d > tol:
            passed = False

    msg = "; ".join(
        f"{k}: {v[0]:.2f} vs {v[1]:.2f} (Δ{v[2]:.2f})" for k, v in diffs.items()
    ) or "no axes requested"

    return Assertion(
        name="bounding_box",
        passed=passed,
        value=f"{dims['x']:.2f} x {dims['y']:.2f} x {dims['z']:.2f} mm",
        threshold=f"within ±{tol} mm of requested",
        message=msg,
    )


def run_checks(stl_path: Path, requested_dims=None):
    mesh = _load(stl_path)
    assertions = [
        check_watertight(mesh),
        check_manifold(mesh),
        check_wall_thickness(mesh),
        check_bounding_box(mesh, requested_dims),
    ]
    return mesh, assertions
