// ============================================================
//  N20 Motor Lever Arm — SEPARATE PRINT
//  Print this file flat on the build plate.
//
//  Attaches to the 3mm output shaft of the N20 motor.
//  The tip bump makes the arm clearly visible in demo video.
//
//  Print settings: 0.2mm layer, 40% infill, PETG or PLA
// ============================================================

shaft_diameter  = 3.0;
tolerance       = 0.3;
lever_length    = 75.0;   // tip to shaft center
lever_width     = 9.0;
lever_thickness = 5.0;
hub_r           = lever_width / 2 + 2.5;

difference() {
    union() {
        // Main arm
        translate([-lever_width / 2, 0, 0])
            cube([lever_width, lever_length, lever_thickness]);

        // Hub reinforcement around shaft
        cylinder(h = lever_thickness + 4, r = hub_r, $fn = 36);

        // Tip bump — visually distinct end for demo video
        translate([-lever_width / 2, lever_length - lever_width, 0])
            cube([lever_width, lever_width, lever_thickness + 4]);
    }

    // Shaft press-fit hole
    translate([0, 0, -0.1])
        cylinder(h = lever_thickness + 4.2, r = (shaft_diameter + tolerance) / 2, $fn = 24);

    // M2 set-screw hole through hub side (optional — for extra grip on shaft)
    translate([hub_r + 0.1, 0, (lever_thickness + 4) / 2])
        rotate([0, 90, 0])
            cylinder(h = hub_r * 2 + 0.2, r = 1.1, $fn = 16);
}
