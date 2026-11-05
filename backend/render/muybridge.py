"""Render the 12-view inspection plate.

A 4x3 grid of matplotlib 3D subplots. Each frame draws the mesh wireframe from
its camera angle, a dashed bounding box with dimension labels, and (for 4
frames) a cross-sectional slice as a filled polygon. The result is a dark PNG
with the measured dimensions in the title.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless
import matplotlib.pyplot as plt
import numpy as np
import trimesh
from matplotlib.colors import to_rgba
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from render.views import View, build_views

# Plate colours.
_BG = "#0b0e14"
_PANEL = "#11151d"
_EDGE = "#56b4e9"
_SLICE = "#e69f00"
_BBOX = "#9ca3af"
_TEXT = "#e5e7eb"
_MUTED = "#9aa3af"


def _centered(mesh: trimesh.Trimesh) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return centered vertices, faces, and bounding-box extents."""
    v = np.asarray(mesh.vertices).copy()
    faces = np.asarray(mesh.faces)
    centroid = v.mean(axis=0)
    vc = v - centroid
    ext = mesh.bounding_box.extents
    return vc, faces, ext


def _draw_wireframe(ax, verts, faces, color=_EDGE, lw=0.4, alpha=0.9):
    # Plot only the unique edges of the mesh for a clean wireframe.
    edges = trimesh.geometry.faces_to_edges(faces)
    uniq = trimesh.geometry.unique_edges(edges) if hasattr(trimesh.geometry, "unique_edges") else np.unique(np.sort(edges, axis=1), axis=0)
    segs = verts[uniq]
    # Plot in chunks to keep matplotlib responsive for large meshes.
    lines = segs.reshape(-1, 2, 3)
    for ln in lines[:: max(1, len(lines) // 4000)]:
        ax.plot(ln[:, 0], ln[:, 1], ln[:, 2], color=color, lw=lw, alpha=alpha)
    if len(lines):
        # ensure at least the last edge renders
        ax.plot(lines[-1, :, 0], lines[-1, :, 1], lines[-1, :, 2], color=color, lw=lw, alpha=alpha)


def _draw_bbox(ax, ext, color=_BBOX):
    dx, dy, dz = ext / 2.0
    corners = np.array(
        [[-dx, -dy, -dz], [dx, -dy, -dz], [dx, dy, -dz], [-dx, dy, -dz],
         [-dx, -dy, dz], [dx, -dy, dz], [dx, dy, dz], [-dx, dy, dz]]
    )
    faces_idx = [
        [0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
        [2, 3, 7, 6], [1, 2, 6, 5], [0, 3, 7, 4],
    ]
    polys = [[corners[i] for i in face] for face in faces_idx]
    coll = Poly3DCollection(polys, facecolor=(0, 0, 0, 0), edgecolor=color, ls="--", lw=0.8)
    ax.add_collection3d(coll)
    ax.text(0, 0, dz + ext[2] * 0.08, f"Z {ext[2]:.1f}", color=color, fontsize=6, ha="center")
    ax.text(dx + ext[0] * 0.08, 0, 0, f"X {ext[0]:.1f}", color=color, fontsize=6, ha="left")
    ax.text(0, dy + ext[1] * 0.08, 0, f"Y {ext[1]:.1f}", color=color, fontsize=6, ha="center")


def _draw_slice(ax, mesh: trimesh.Trimesh, axis: str, color=_SLICE):
    """Draw cross-section through centered mesh origin along the given plane normal."""
    centroid = np.asarray(mesh.vertices).mean(axis=0)
    centered = mesh.copy()
    centered.apply_translation(-centroid)
    normal = {"x": [1, 0, 0], "y": [0, 1, 0], "z": [0, 0, 1]}.get(axis, [0, 0, 1])
    try:
        section = centered.section(plane_origin=[0, 0, 0], plane_normal=normal)
        if section is None:
            return
        polys = [pts for pts in section.discrete if len(pts) >= 3]
        if polys:
            coll = Poly3DCollection(
                polys,
                facecolor=to_rgba(color, alpha=0.55),
                edgecolor=color,
                lw=0.8,
            )
            ax.add_collection3d(coll)
    except Exception:
        pass


def render_plate(mesh: trimesh.Trimesh, out_path: Path) -> Path:
    """Render the 12-view plate and return its path."""
    views: list[View] = build_views()
    vc, faces, ext = _centered(mesh)
    max_ext = float(ext.max()) or 1.0

    fig = plt.figure(figsize=(14, 10), facecolor=_BG)
    fig.suptitle(
        f"Muybridge plate  {ext[0]:.2f} x {ext[1]:.2f} x {ext[2]:.2f} mm  "
        f"verts={len(vc)}  tris={len(faces)}",
        color=_TEXT, fontsize=11, y=0.98,
    )
    for idx, view in enumerate(views):
        ax = fig.add_subplot(3, 4, idx + 1, projection="3d")
        ax.set_facecolor(_PANEL)
        _draw_wireframe(ax, vc, faces)
        _draw_bbox(ax, ext)
        if view.show_slice:
            _draw_slice(ax, mesh, view.slice_axis)
        ax.view_init(elev=view.elevation, azim=view.azimuth)
        ax.set_xlim(-max_ext, max_ext)
        ax.set_ylim(-max_ext, max_ext)
        ax.set_zlim(-max_ext, max_ext)
        ax.set_box_aspect((1, 1, 1))
        ax.set_title(view.label, color=_MUTED, fontsize=7, pad=2)
        # Minimal chrome: hide gridlines/ticks for a clean contact sheet.
        for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
            axis.pane.set_facecolor(_PANEL)
            axis.pane.set_edgecolor((1, 1, 1, 0.06))
            axis.line.set_color((1, 1, 1, 0.1))
        ax.tick_params(colors=_MUTED, labelsize=5, pad=-2)
        ax.grid(False)

    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(str(out_path), dpi=130, facecolor=_BG)
    plt.close(fig)

    return out_path

