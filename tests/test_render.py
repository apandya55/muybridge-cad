import trimesh
from render.views import build_views
from render.muybridge import render_plate


def test_build_views_count_and_angles():
    views = build_views()
    assert len(views) == 12
    # Check 6 lower tier (15 deg) and 6 upper tier (60 deg)
    assert all(v.elevation == 15.0 for v in views[:6])
    assert all(v.elevation == 60.0 for v in views[6:])
    # Check cross sections enabled for 3 frames
    slices = [v for v in views if v.show_slice]
    assert len(slices) == 3


def test_render_plate_output(tmp_path):
    mesh = trimesh.creation.box(extents=(15, 10, 5))
    out_png = tmp_path / "test_plate.png"
    result = render_plate(mesh, out_png)
    assert result.exists()
    assert result.stat().st_size > 1000
