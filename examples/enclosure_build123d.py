# Simple electronic enclosure base, ~50x40x20mm, with a cutout.
# Convention: assign the finished solid to the top-level name `part`.
from build123d import *

with BuildPart() as bp:
    with BuildSketch() as sk:
        Rectangle(50, 40)
        fillet(sk.vertices(), radius=3)
    extrude(amount=20)
    # Hollow the inside, leaving 2mm walls and floor.
    offset(amount=-2, mode=Mode.SUBTRACT)
    # Top cutout for a cable.
    with Locations((0, 0, 20)):
        with BuildSketch() as cut:
            Rectangle(20, 6)
        extrude(amount=-5, mode=Mode.SUBTRACT)
    # Four M3 stand-off holes in the corners.
    for x in (-20, 20):
        for y in (-14, 14):
            with Locations((x, y, 0)):
                Hole(radius=1.6, depth=20)

part = bp.part
