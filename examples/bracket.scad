// L-shaped mounting bracket, 40x30x20mm, two M3 screw holes.
$fn = 48;

module m3_hole(h = 20) {
    cylinder(h = h, r = 1.6, center = true);
}

module bracket() {
    difference() {
        // Base L-body: two overlapping prisms forming an L.
        union() {
            translate([0, 0, 0])
                cube([40, 30, 4], center = false);     // horizontal floor
            translate([0, 0, 4])
                cube([4, 30, 16], center = false);        // vertical wall
        }
        // Two M3 through-holes in the long arm.
        translate([12, 15, 0]) m3_hole(h = 8);
        translate([28, 15, 0]) m3_hole(h = 8);
        // Countersinks on top of the floor.
        translate([12, 15, 3.2]) cylinder(h = 1, r = 3.0, center = true);
        translate([28, 15, 3.2]) cylinder(h = 1, r = 3.0, center = true);
    }
}

bracket();
