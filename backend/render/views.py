"""Camera angle definitions for the inspection plate.

Twelve camera views at 30 degree azimuth increments, split across two elevation
tiers. Frames 3, 7, and 11 also show a cross-section slice.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class View:
    index: int
    azimuth: float
    elevation: float
    show_slice: bool
    slice_axis: str  # "x" | "y" | "z" plane normal

    @property
    def label(self) -> str:
        return f"{self.index:02d}  az={int(self.azimuth):>3} el={int(self.elevation):>2}"


def build_views() -> list[View]:
    views: list[View] = []
    slice_axes = ["z", "y", "x"]
    for i in range(12):
        az = (i % 6) * 30.0
        el = 15.0 if i < 6 else 60.0
        show_slice = i in (3, 7, 11)
        axis = slice_axes[(i // 4) % 3]
        views.append(View(index=i, azimuth=az, elevation=el, show_slice=show_slice, slice_axis=axis))
    return views
