// ============================================================
//  N20 Motor + Encoder Mount Bracket
//  For: CAN-Bus Joint Controller project
//
//  Dimensions to verify against your actual N20 motor:
//    - Motor body diameter: 12mm (standard N20)
//    - Motor body length:   ~15mm
//    - Encoder body:        extends ~15mm behind motor
//    - Output shaft:        1.5mm or 3mm diameter
//    - Mounting holes:      M3 screws
//
//  Parts produced:
//    1. Base plate  — mounts to table/stand via M3 screws
//    2. Motor clamp — holds N20 motor body rigidly
//    3. Lever arm   — attaches to output shaft, sweeps visibly
//
//  Print settings: 0.2mm layer, 40% infill, PETG or PLA
//  No supports needed if printed in orientation shown.
// ============================================================

// ── Tuneable parameters ──────────────────────────────────────
motor_diameter   = 12.0;   // N20 body diameter (mm) — measure yours
motor_length     = 15.0;   // N20 body length (mm)
encoder_length   = 15.0;   // encoder extension behind motor
clamp_wall       = 3.0;    // wall thickness around motor
base_thickness   = 4.0;    // base plate thickness
base_width       = 50.0;   // base plate width
base_length      = 60.0;   // base plate length
m3_hole          = 3.2;    // M3 screw clearance hole
lever_length     = 70.0;   // lever arm length (tip to shaft center)
lever_width      = 8.0;    // lever arm width
lever_thickness  = 4.0;    // lever arm thickness
shaft_diameter   = 3.0;    // output shaft diameter — check yours (1.5 or 3mm)
tolerance        = 0.3;    // 3D print fit tolerance

// ── Derived values ───────────────────────────────────────────
motor_r        = motor_diameter / 2 + tolerance;
clamp_outer_r  = motor_r + clamp_wall;
clamp_height   = motor_length + encoder_length;
clamp_center_z = base_thickness + clamp_outer_r;

// ── Base plate ───────────────────────────────────────────────
module base_plate() {
    difference() {
        // Solid base
        cube([base_length, base_width, base_thickness]);

        // M3 mounting holes — 4 corners, 5mm from edges
        for (x = [8, base_length - 8])
            for (y = [8, base_width - 8])
                translate([x, y, -0.1])
                    cylinder(h = base_thickness + 0.2, r = m3_hole / 2, $fn = 20);
    }
}

// ── Motor clamp ──────────────────────────────────────────────
// Cylindrical collar that grips the N20 motor body.
// Clamp gap on one side allows slight squeeze with an M3 screw.
module motor_clamp() {
    clamp_x = base_length / 2;
    clamp_y = base_width / 2;

    translate([clamp_x, clamp_y, base_thickness]) {
        difference() {
            // Outer collar
            cylinder(h = clamp_height, r = clamp_outer_r, $fn = 40);

            // Inner bore for motor body
            translate([0, 0, -0.1])
                cylinder(h = clamp_height + 0.2, r = motor_r, $fn = 40);

            // Clamp gap slot (allows collar to flex closed slightly)
            translate([-0.8, -clamp_outer_r - 0.1, -0.1])
                cube([1.6, clamp_outer_r * 2 + 0.2, clamp_height + 0.2]);

            // M3 clamp screw hole (horizontal, through the gap)
            translate([-clamp_outer_r - 0.1, 0, clamp_height * 0.6])
                rotate([0, 90, 0])
                    cylinder(h = clamp_outer_r * 2 + 0.2, r = m3_hole / 2, $fn = 20);
        }
    }
}

// ── Lever arm ────────────────────────────────────────────────
// Attaches to output shaft. Press-fit hole for the shaft.
// Visual indicator of commanded vs actual position during demo.
module lever_arm() {
    difference() {
        union() {
            // Main arm body
            translate([-lever_width / 2, 0, 0])
                cube([lever_width, lever_length, lever_thickness]);

            // Hub around shaft hole (reinforcement)
            cylinder(h = lever_thickness + 3, r = lever_width / 2 + 2, $fn = 30);

            // Tip indicator bump so you can see the arm end clearly on video
            translate([-lever_width / 2, lever_length - lever_width, 0])
                cube([lever_width, lever_width, lever_thickness + 3]);
        }

        // Shaft press-fit hole (center of hub)
        translate([0, 0, -0.1])
            cylinder(h = lever_thickness + 3 + 0.2, r = (shaft_diameter + tolerance) / 2, $fn = 20);

        // Optional M2 set-screw hole through the side of hub
        translate([lever_width + 2, 0, lever_thickness / 2 + 1.5])
            rotate([0, 90, 0])
                cylinder(h = lever_width + 4, r = 1.1, $fn = 16);
    }
}

// ── Assembly ─────────────────────────────────────────────────
// Print base_plate + motor_clamp as one piece (they share the same Z=0).
// Print lever_arm separately (flat on build plate).

// Main bracket (base + clamp together)
base_plate();
motor_clamp();

// Lever arm — printed flat, shown offset here for visibility
translate([base_length + 15, base_width / 2, 0])
    lever_arm();
