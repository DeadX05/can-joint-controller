"""
N20 vertical tower mount - rev 2 (shaft-up, matches original design intent
and the validated horizontal-plane PID tuning).

Concept:
- Full-height rectangular U-tower: spine (back wall) + two side walls,
  FRONT FACE FULLY OPEN. Motor drops in from the top, shaft up.
- Lower interior = encoder void: encoder PCB + connector + spinning disc
  hang in free air, connector/ribbon exit through the open front.
  NOTHING touches or supports the encoder end.
- Upper interior = grip band: walls friction-grip the motor can flats.
- Zip-tie slots through both side walls near the top of the grip zone:
  a tie wraps around the motor pressing it against the spine if the
  friction fit alone is loose.
- Base plate with 4 corner M3 holes, extended forward as a cable apron.

Nominal N20 dims assumed (12.0 wide x 10.0 deep, encoder protrusion ~6mm).
Verify with caliper after the fit test and regenerate - all parametric.
Print flat as oriented, brim ON (PETG warp history), no supports needed.
"""

import trimesh
from trimesh.creation import box, cylinder

# ---------------- Parameters (edit after caliper check) ----------------
MOTOR_W    = 12.0   # motor width across the flat faces (X)
MOTOR_D    = 10.0   # motor depth front-to-back (Y)
CLEAR_W    = 0.5    # total width clearance  (inner X = MOTOR_W + CLEAR_W)
CLEAR_D    = 0.4    # total depth clearance  (inner Y = MOTOR_D + CLEAR_D)

VOID_H     = 13.0   # encoder free-air zone height above base top
GRIP_H     = 12.0   # friction grip band height above the void
WALL_T     = 3.0    # side wall thickness
SPINE_T    = 4.0    # back wall thickness

BASE_W     = 30.0   # base X
BASE_D     = 40.0   # base Y (extends forward as cable apron)
BASE_T     = 3.0
HOLE_D     = 3.4
HOLE_INSET = 5.0

ZT_SLOT_W  = 4.0    # zip-tie slot width (vertical extent)
ZT_SLOT_T  = 2.5    # zip-tie slot thickness (Y extent)
# -----------------------------------------------------------------------

inner_w = MOTOR_W + CLEAR_W
inner_d = MOTOR_D + CLEAR_D
tower_h = VOID_H + GRIP_H
top_z   = BASE_T + tower_h

# Y layout: spine at the back, open front toward +Y, tower shifted rearward
spine_back_y  = -BASE_D / 2 + 4.0            # 4mm rear margin on base
spine_front_y = spine_back_y + SPINE_T
cavity_front_y = spine_front_y + inner_d      # side walls end here (open front)

def B(x0, x1, y0, y1, z0, z1):
    b = box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2])
    return b

parts = []

# Base plate
parts.append(B(-BASE_W/2, BASE_W/2, -BASE_D/2, BASE_D/2, 0, BASE_T))

# Spine (back wall), full height
parts.append(B(-(inner_w/2 + WALL_T), inner_w/2 + WALL_T,
               spine_back_y, spine_front_y, BASE_T, top_z))

# Side walls, full height, front face open
parts.append(B(inner_w/2, inner_w/2 + WALL_T,
               spine_front_y, cavity_front_y, BASE_T, top_z))
parts.append(B(-(inner_w/2 + WALL_T), -inner_w/2,
               spine_front_y, cavity_front_y, BASE_T, top_z))

mount = trimesh.boolean.union(parts, engine='manifold')

# Subtractions: corner holes + zip-tie slots
cuts = []
for sx in (1, -1):
    for sy in (1, -1):
        c = cylinder(radius=HOLE_D/2, height=BASE_T + 2, sections=48)
        c.apply_translation([sx * (BASE_W/2 - HOLE_INSET),
                             sy * (BASE_D/2 - HOLE_INSET), BASE_T/2])
        cuts.append(c)

# Zip-tie slots through both side walls, near top of grip band, near the
# front edge so the tie presses the motor back against the spine.
zt_z0 = top_z - 5.0 - ZT_SLOT_W
zt_z1 = top_z - 5.0
zt_y0 = cavity_front_y - 1.5 - ZT_SLOT_T
zt_y1 = cavity_front_y - 1.5
cuts.append(B(inner_w/2 - 1, inner_w/2 + WALL_T + 1, zt_y0, zt_y1, zt_z0, zt_z1))
cuts.append(B(-(inner_w/2 + WALL_T + 1), -(inner_w/2 - 1), zt_y0, zt_y1, zt_z0, zt_z1))

mount = trimesh.boolean.difference([mount] + cuts, engine='manifold')

assert mount.is_watertight, "mesh not watertight!"
mount.export('/home/claude/n20_vertical_mount.stl')

print(f"Watertight: {mount.is_watertight}")
print(f"Bounds (mm): {mount.bounds}")
print(f"Cavity: {inner_w:.1f} wide x {inner_d:.1f} deep, open front")
print(f"Encoder void: base+{0:.0f}..+{VOID_H:.0f} (z={BASE_T}..{BASE_T+VOID_H})")
print(f"Grip band: z={BASE_T+VOID_H}..{top_z} ({GRIP_H}mm of friction contact)")
print(f"Tower top at z={top_z} - gearbox + shaft protrude above")
print(f"Zip-tie slots at z={zt_z0:.0f}..{zt_z1:.0f}")
