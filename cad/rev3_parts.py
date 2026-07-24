"""
Rev 3: N20 vertical mount + lever arm. No screws required.

MOUNT changes vs rev 2:
- Grip band is now a CLOSED rectangular tube (spine + 2 sides + front wall).
  The motor is captured on all four faces where it matters, so reaction
  torque can't rock it out of the open front. Motor still drops in from
  the top and slides down behind the front wall.
- Encoder void (lower zone) keeps a fully open front: connector, ribbon
  and the spinning encoder disc stay in free air, untouched.
- Base is now a plus/cross footprint spanning 75mm instead of a small
  rectangle - contains the lever's swing envelope so it can't tip, while
  using ~half the plastic (and print time) of a solid plate.

LEVER:
- D-shaped bore keyed to the motor's D-shaft (no more friction-only round
  bore, so it can't slip out of registration with the encoder).
- Tapered arm ending in a point = readable index for video.
- Press fit; a drop of glue is the documented fallback if loose.

All dims mm. Print both flat as oriented, no supports, brim ON.
"""

import numpy as np
import trimesh
from trimesh.creation import box, cylinder, extrude_polygon
from shapely.geometry import Polygon

# ---------------- Motor / cavity (confirmed roughly correct in rev 2) ----
MOTOR_W   = 12.0
MOTOR_D   = 10.0
CLEAR_W   = 0.5
CLEAR_D   = 0.4
VOID_H    = 13.0    # encoder free-air zone
GRIP_H    = 12.0    # closed-tube grip band
WALL_T    = 3.0
SPINE_T   = 4.0
FRONT_T   = 3.0     # NEW front wall (grip band only)

# ---------------- Base ----------------
BASE_SPAN = 75.0    # tip-to-tip of the cross arms
BASE_ARM  = 24.0    # width of each arm
BASE_T    = 3.5
HOLE_D    = 3.4
HOLE_FROM_END = 7.0

# ---------------- Lever ----------------
BORE_D      = 3.10   # 3.0 shaft + light clearance
BORE_FLAT   = 2.40   # across-flat (between your ~2.2 reading and 2.5 spec)
HUB_D       = 10.0
HUB_H       = 7.0
ARM_LEN     = 60.0   # shaft axis to tip
ARM_T       = 4.0
ARM_W_ROOT  = 10.0
ARM_W_TIP   = 3.6
# -------------------------------------------------------------------------

inner_w = MOTOR_W + CLEAR_W
inner_d = MOTOR_D + CLEAR_D
tower_h = VOID_H + GRIP_H
grip_z0 = BASE_T + VOID_H
top_z   = BASE_T + tower_h

def B(x0, x1, y0, y1, z0, z1):
    b = box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b

# ============================ MOUNT ======================================
parts = []

# Plus-shaped base, shaft axis centred at origin
parts.append(B(-BASE_SPAN/2, BASE_SPAN/2, -BASE_ARM/2, BASE_ARM/2, 0, BASE_T))
parts.append(B(-BASE_ARM/2, BASE_ARM/2, -BASE_SPAN/2, BASE_SPAN/2, 0, BASE_T))

outer_x = inner_w/2 + WALL_T

# Spine (back wall), full height
parts.append(B(-outer_x, outer_x, -(inner_d/2 + SPINE_T), -inner_d/2, BASE_T, top_z))

# Side walls, full height
parts.append(B(inner_w/2, outer_x, -inner_d/2, inner_d/2 + FRONT_T, BASE_T, top_z))
parts.append(B(-outer_x, -inner_w/2, -inner_d/2, inner_d/2 + FRONT_T, BASE_T, top_z))

# NEW front wall - grip band ONLY, so the encoder void stays open below
parts.append(B(-outer_x, outer_x, inner_d/2, inner_d/2 + FRONT_T, grip_z0, top_z))

mount = trimesh.boolean.union(parts, engine='manifold')

# Mounting holes near each arm tip
cuts = []
for dx, dy in [(BASE_SPAN/2 - HOLE_FROM_END, 0), (-(BASE_SPAN/2 - HOLE_FROM_END), 0),
               (0, BASE_SPAN/2 - HOLE_FROM_END), (0, -(BASE_SPAN/2 - HOLE_FROM_END))]:
    c = cylinder(radius=HOLE_D/2, height=BASE_T + 4, sections=48)
    c.apply_translation([dx, dy, BASE_T/2])
    cuts.append(c)
mount = trimesh.boolean.difference([mount] + cuts, engine='manifold')

assert mount.is_watertight, "mount not watertight!"
mount.export('/home/claude/n20_mount_rev3.stl')

# ============================ LEVER ======================================
hub = cylinder(radius=HUB_D/2, height=HUB_H, sections=96)
hub.apply_translation([0, 0, HUB_H/2])

poly = Polygon([
    (-HUB_D/2 + 1.0, -ARM_W_ROOT/2),
    (ARM_LEN - 10.0, -ARM_W_TIP/2),
    (ARM_LEN, 0.0),
    (ARM_LEN - 10.0,  ARM_W_TIP/2),
    (-HUB_D/2 + 1.0,  ARM_W_ROOT/2),
])
arm = extrude_polygon(poly, height=ARM_T)

lever = trimesh.boolean.union([hub, arm], engine='manifold')

# D-shaped bore through the hub
r = BORE_D / 2
cyl = cylinder(radius=r, height=HUB_H + 6, sections=96)
cyl.apply_translation([0, 0, HUB_H/2])
flat_off = BORE_FLAT - r
trim = box(extents=[BORE_D + 6, BORE_D + 6, HUB_H + 8])
trim.apply_translation([0, -flat_off - (BORE_D + 6)/2, HUB_H/2])
d_bore = trimesh.boolean.difference([cyl, trim], engine='manifold')

lever = trimesh.boolean.difference([lever, d_bore], engine='manifold')

assert lever.is_watertight, "lever not watertight!"
lever.export('/home/claude/lever_arm.stl')

print(f"MOUNT  watertight={mount.is_watertight}  volume={mount.volume:.0f} mm3")
print(f"       bounds={mount.bounds.tolist()}")
print(f"       cavity {inner_w:.1f} x {inner_d:.1f}; void z={BASE_T}..{grip_z0}"
      f" (open front); closed grip z={grip_z0}..{top_z}")
print(f"LEVER  watertight={lever.is_watertight}  volume={lever.volume:.0f} mm3")
print(f"       bore {BORE_D} dia, {BORE_FLAT} across-flat, hub {HUB_D}x{HUB_H},"
      f" arm {ARM_LEN}mm")
