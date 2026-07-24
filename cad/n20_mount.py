"""
N20 motor mount - rectangular U-channel test-fit version
Izzatbek's CAN bus project. All dims in mm, parametric below.

Design intent:
- Open-top rectangular channel: motor drops in from above.
- Channel supports gearbox + front of motor can ONLY; stops before the
  encoder PCB, which overhangs the open back end in free air.
- Front wall with an open-top vertical slot for the shaft: works for any
  vertical shaft offset, motor slides straight down during assembly.
- Base plate with 4 corner mounting holes.
- Print flat as oriented, no supports needed.

Based on NOMINAL N20 dims (12.0 x 10.0 body). Verify with caliper and
adjust MOTOR_W / MOTOR_H / clearance, then regenerate.
"""

import numpy as np
import trimesh
from trimesh.creation import box, cylinder

# ---------------- Parameters (edit after caliper check) ----------------
MOTOR_W      = 12.0   # motor body width  (measure!)
MOTOR_H      = 10.0   # motor body height (measure!)
CLEAR        = 0.4    # PETG fit clearance added to width
CHANNEL_LEN  = 16.0   # supported length (gearbox + front of can, stops before encoder)
WALL_T       = 3.0    # side/front wall thickness
FLOOR_T      = 3.0    # channel floor thickness
WALL_H       = 8.0    # side wall height above channel floor (motor sits proud)
FRONT_H_EXTRA= 2.0    # front wall rises this much above motor top
SLOT_W       = 5.5    # shaft slot width in front wall (shaft ~3mm + margin)
SLOT_DEPTH_FROM_FLOOR = 3.0  # slot bottom sits this far above channel floor

BASE_X       = 40.0   # base plate length (along motor axis)
BASE_Y       = 30.0   # base plate width
BASE_T       = 3.0    # base plate thickness
HOLE_D       = 3.4    # corner mounting holes (M3 clearance)
HOLE_INSET   = 5.0    # hole center inset from base corners
# -----------------------------------------------------------------------

inner_w   = MOTOR_W + CLEAR                 # channel inner width
outer_w   = inner_w + 2 * WALL_T
floor_top = BASE_T + FLOOR_T                # z where motor bottom rests
motor_top = floor_top + MOTOR_H
front_h_top = motor_top + FRONT_H_EXTRA

def B(sx, sy, sz, cx, cy, cz):
    b = box(extents=[sx, sy, sz])
    b.apply_translation([cx, cy, cz])
    return b

parts = []

# Base plate (centered at origin in XY, z: 0..BASE_T)
parts.append(B(BASE_X, BASE_Y, BASE_T, 0, 0, BASE_T / 2))

# Channel floor (z: BASE_T..floor_top), centered at x=0
parts.append(B(CHANNEL_LEN, outer_w, FLOOR_T, 0, 0, BASE_T + FLOOR_T / 2))

# Side walls (z: floor_top..floor_top+WALL_H)
wall_z = floor_top + WALL_H / 2
wall_y = inner_w / 2 + WALL_T / 2
parts.append(B(CHANNEL_LEN, WALL_T, WALL_H, 0,  wall_y, wall_z))
parts.append(B(CHANNEL_LEN, WALL_T, WALL_H, 0, -wall_y, wall_z))

# Front wall at shaft end (x negative side), from base top to front_h_top,
# built from 3 boxes forming an open-top U-slot (no boolean needed):
fw_x = -CHANNEL_LEN / 2 - WALL_T / 2
slot_bottom = floor_top + SLOT_DEPTH_FROM_FLOOR
fw_lower_h = slot_bottom - BASE_T
# lower solid band (full width)
parts.append(B(WALL_T, outer_w, fw_lower_h, fw_x, 0, BASE_T + fw_lower_h / 2))
# upper left / right segments flanking the slot
seg_w = (outer_w - SLOT_W) / 2
seg_h = front_h_top - slot_bottom
seg_y = SLOT_W / 2 + seg_w / 2
parts.append(B(WALL_T, seg_w, seg_h, fw_x,  seg_y, slot_bottom + seg_h / 2))
parts.append(B(WALL_T, seg_w, seg_h, fw_x, -seg_y, slot_bottom + seg_h / 2))

# Union all parts properly, then subtract corner holes
mount = trimesh.boolean.union(parts, engine='manifold')

holes = []
for sx in (1, -1):
    for sy in (1, -1):
        c = cylinder(radius=HOLE_D / 2, height=BASE_T + 2, sections=48)
        c.apply_translation([sx * (BASE_X / 2 - HOLE_INSET),
                             sy * (BASE_Y / 2 - HOLE_INSET),
                             BASE_T / 2])
        holes.append(c)
mount = trimesh.boolean.difference([mount] + holes, engine='manifold')

assert mount.is_watertight, "mesh not watertight!"
mount.export('/home/claude/n20_mount_test_fit.stl')

print(f"Watertight: {mount.is_watertight}")
print(f"Bounds (mm): {mount.bounds}")
print(f"Channel inner width: {inner_w:.1f} mm  (motor {MOTOR_W} + {CLEAR} clearance)")
print(f"Motor rests at z={floor_top:.1f}, top at z={motor_top:.1f}")
print(f"Shaft slot: {SLOT_W} mm wide, open from top down to z={slot_bottom:.1f}")
print(f"Encoder overhang: channel ends at x=+{CHANNEL_LEN/2:.0f}, base extends to x=+{BASE_X/2:.0f}")
