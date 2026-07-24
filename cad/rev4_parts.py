"""
Rev 4: N20 vertical mount + slide-in front plate. No screws.

ASSEMBLY (this is the point of rev 4):
1. Front of the mount is open full height -> slide the motor in from the
   FRONT. Encoder end sits in the lower void, motor can sits in the grip
   band. (Rev 3 was closed on 4 sides in the grip band, which made this
   impossible - the encoder PCB can't pass down through the tube.)
2. Slide the FRONT PLATE down into the vertical grooves in the side walls.
   It bottoms out at the base of the grip band. Now the grip band is
   closed on all four faces and the motor cannot rock out under reaction
   torque.
3. The plate covers ONLY the grip band. The encoder void below stays open
   at the front - connector, ribbon and spinning disc remain in free air.

The plate stands ~2mm proud of the tower top so you can pull it back out
by hand for servicing. It is held by the grooves front-to-back and by
friction vertically.

Print both flat as oriented, no supports, brim ON.
"""

import numpy as np
import trimesh
from trimesh.creation import box, cylinder

# ---------------- Motor / cavity ----------------
MOTOR_W    = 12.0
MOTOR_D    = 10.0
CLEAR_W    = 0.5
CLEAR_D    = 0.4
VOID_H     = 13.0     # encoder free-air zone (open front, always)
GRIP_H     = 12.0     # closed by the front plate after assembly
WALL_T     = 4.0      # thicker: the grooves are cut into these
SPINE_T    = 4.0

# ---------------- Front plate / grooves ----------------
PLATE_T    = 2.5      # plate thickness
TONGUE     = 1.5      # how far the plate edges sit into each side wall
SLOT_CLEAR = 0.35     # sliding clearance (PETG); raise if it binds
FRONT_LIP  = 2.0      # wall material in front of the plate (retains it)
PLATE_PROUD= 2.0      # plate sticks up above tower top = finger grip

# ---------------- Base ----------------
BASE_SPAN  = 72.0
BASE_ARM   = 24.0
BASE_T     = 3.5
HOLE_D     = 3.4
HOLE_FROM_END = 7.0
# -----------------------------------------------------------------------

inner_w = MOTOR_W + CLEAR_W
inner_d = MOTOR_D + CLEAR_D
tower_h = VOID_H + GRIP_H
grip_z0 = BASE_T + VOID_H
top_z   = BASE_T + tower_h

outer_x   = inner_w/2 + WALL_T
slot_y0   = inner_d/2                              # groove starts at cavity front
slot_y1   = slot_y0 + PLATE_T + SLOT_CLEAR
wall_y1   = slot_y1 + FRONT_LIP                    # walls reach past the plate

def B(x0, x1, y0, y1, z0, z1):
    b = box(extents=[x1 - x0, y1 - y0, z1 - z0])
    b.apply_translation([(x0+x1)/2, (y0+y1)/2, (z0+z1)/2])
    return b

# ============================ MOUNT ======================================
parts = []
# Plus-shaped base, shaft axis at origin
parts.append(B(-BASE_SPAN/2, BASE_SPAN/2, -BASE_ARM/2, BASE_ARM/2, 0, BASE_T))
parts.append(B(-BASE_ARM/2, BASE_ARM/2, -BASE_SPAN/2, BASE_SPAN/2, 0, BASE_T))
# Spine (back wall)
parts.append(B(-outer_x, outer_x, -(inner_d/2 + SPINE_T), -inner_d/2, BASE_T, top_z))
# Side walls, full height, extending forward past the plate
parts.append(B( inner_w/2,  outer_x, -inner_d/2, wall_y1, BASE_T, top_z))
parts.append(B(-outer_x, -inner_w/2, -inner_d/2, wall_y1, BASE_T, top_z))

mount = trimesh.boolean.union(parts, engine='manifold')

cuts = []
# Vertical grooves for the front plate - open at the top, blind at grip_z0
for sx in (1, -1):
    gx0 = sx * inner_w/2
    gx1 = sx * (inner_w/2 + TONGUE + SLOT_CLEAR)
    cuts.append(B(min(gx0, gx1), max(gx0, gx1), slot_y0, slot_y1, grip_z0, top_z + 5))

# Base mounting holes
for dx, dy in [(BASE_SPAN/2 - HOLE_FROM_END, 0), (-(BASE_SPAN/2 - HOLE_FROM_END), 0),
               (0, BASE_SPAN/2 - HOLE_FROM_END), (0, -(BASE_SPAN/2 - HOLE_FROM_END))]:
    c = cylinder(radius=HOLE_D/2, height=BASE_T + 4, sections=48)
    c.apply_translation([dx, dy, BASE_T/2])
    cuts.append(c)

mount = trimesh.boolean.difference([mount] + cuts, engine='manifold')
assert mount.is_watertight, "mount not watertight!"
mount.export('/home/claude/n20_mount_rev4.stl')

# ========================= FRONT PLATE ===================================
plate_w = inner_w + 2 * TONGUE
plate_h = (top_z - grip_z0) + PLATE_PROUD
plate = B(-plate_w/2, plate_w/2, 0, PLATE_T, 0, plate_h)
assert plate.is_watertight
plate.export('/home/claude/n20_front_plate.stl')

print(f"MOUNT  watertight={mount.is_watertight}  volume={mount.volume:.0f} mm3")
print(f"       bounds={np.round(mount.bounds,1).tolist()}")
print(f"       cavity {inner_w:.1f} x {inner_d:.1f}")
print(f"       void (open front) z={BASE_T}..{grip_z0}")
print(f"       grip band (closed by plate) z={grip_z0}..{top_z}")
print(f"PLATE  {plate_w:.1f} wide x {PLATE_T} thick x {plate_h:.1f} tall,"
      f" volume={plate.volume:.0f} mm3")
print(f"       slides in grooves, bottoms at z={grip_z0}, stands"
      f" {PLATE_PROUD}mm proud for removal")
