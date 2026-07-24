// ============================================================
//  N20 Motor Mount Bracket — BODY ONLY
//  Print this file as one STL.
//
//  Dimensions from Waveshare N20 DC Gear Motor datasheet:
//    Motor body diameter : 12mm
//    Motor body length   : 24mm
//    Encoder length      : 10mm
//    Shaft diameter      : 3mm
//
//  Print settings: 0.2mm layer, 40% infill, PETG or PLA
//  No supports needed.
// ============================================================

motor_diameter  = 12.0;
motor_length    = 24.0;
encoder_length  = 10.0;
clamp_wall      = 3.0;
base_thickness  = 4.0;
base_width      = 55.0;
base_length     = 65.0;
m3_hole         = 3.2;
tolerance       = 0.3;

motor_r       = motor_diameter / 2 + tolerance;
clamp_outer_r = motor_r + clamp_wall;
clamp_height  = motor_length + encoder_length;  // 34mm total
clamp_x       = base_length / 2;
clamp_y       = base_width / 2;

// Cable slot dimensions — for encoder ribbon cable exit
cable_slot_w  = 8.0;   // wide enough for 6-wire ribbon
cable_slot_d  = 3.0;   // depth into collar wall

difference() {
    union() {
        // ── Base plate ────────────────────────────────────
        cube([base_length, base_width, base_thickness]);

        // ── Motor clamp collar ────────────────────────────
        translate([clamp_x, clamp_y, base_thickness])
            cylinder(h = clamp_height, r = clamp_outer_r, $fn = 48);
    }

    // M3 corner mounting holes
    for (x = [9, base_length - 9])
        for (y = [9, base_width - 9])
            translate([x, y, -0.1])
                cylinder(h = base_thickness + 0.2, r = m3_hole / 2, $fn = 20);

    // Inner bore for motor body (full height)
    translate([clamp_x, clamp_y, base_thickness - 0.1])
        cylinder(h = clamp_height + 0.2, r = motor_r, $fn = 48);

    // Clamp gap slot — one side, allows collar to flex with M3 screw
    translate([clamp_x - 0.9, clamp_y - clamp_outer_r - 0.1, base_thickness - 0.1])
        cube([1.8, clamp_outer_r * 2 + 0.2, clamp_height + 0.2]);

    // M3 clamp screw hole — horizontal through collar walls
    translate([clamp_x - clamp_outer_r - 0.1, clamp_y, base_thickness + clamp_height * 0.65])
        rotate([0, 90, 0])
            cylinder(h = clamp_outer_r * 2 + 0.2, r = m3_hole / 2, $fn = 20);

    // Cable routing slot — at encoder end (top of collar)
    // Encoder ribbon exits here cleanly instead of bending around the collar
    translate([clamp_x - cable_slot_w / 2,
               clamp_y + motor_r - 0.1,
               base_thickness + motor_length])
        cube([cable_slot_w, cable_slot_d + 0.1, encoder_length + 0.2]);
}
