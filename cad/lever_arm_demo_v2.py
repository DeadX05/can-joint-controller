"""
Lever arm - demo build.

Changes from the previous lever:
- Thickness 4.0 -> 3.5 mm and a tapered lightening slot down the arm.
  Together these remove roughly a quarter of the mass. Overshoot on fast
  steps scales with the lever's rotational inertia, so a lighter arm
  settles with less excursion past the target - the behaviour visible in
  the step captures (0->-45 overshot to -47.4 before recovering).
- Bore OVERSIZED to 3.40 mm dia / 2.60 mm across-flat (from 3.10 / 2.40).
  The previous bore bound halfway onto the shaft: PETG holes print
  ~0.1-0.3 mm undersized, so a 3.10 nominal hole was an interference fit on
  the 3.0 mm shaft. It is the one dimension that decides whether the part
  seats, so it is the change that matters here.

D-bore keys the lever to the motor's D-shaft so it cannot slip. A round
bore transmits torque by friction alone; if it slips, the encoder and the
lever silently disagree and every reported angle becomes wrong.

Print: hub down, flat on the bed, no supports, 0.2 mm layers, 3
perimeters, ~30% infill. Bore prints as a vertical hole in this
orientation, which is where dimensional accuracy is best.
"""

import trimesh
from trimesh.creation import cylinder, extrude_polygon
from shapely.geometry import Polygon

# ---- Bore (do not edit without a fit test) ----
BORE_D     = 3.40    # oversized: PETG bores shrink 0.1-0.3mm
BORE_FLAT  = 2.60    # flat relieved to match

# ---- Hub ----
HUB_D      = 10.0
HUB_H      = 5.5

# ---- Arm ----
ARM_LEN    = 60.0    # shaft axis to tip
ARM_T      = 3.5
ARM_W_ROOT = 10.0
ARM_W_TIP  = 3.6

# ---- Lightening slot ----
SLOT_X0, SLOT_HW0 = 13.0, 2.2
SLOT_X1, SLOT_HW1 = 33.0, 1.3

# ---- Build ----
hub = cylinder(radius=HUB_D / 2, height=HUB_H, sections=96)
hub.apply_translation([0, 0, HUB_H / 2])

arm_poly = Polygon([
    (-HUB_D / 2 + 1.0, -ARM_W_ROOT / 2),
    (ARM_LEN - 10.0,   -ARM_W_TIP / 2),
    (ARM_LEN,           0.0),
    (ARM_LEN - 10.0,    ARM_W_TIP / 2),
    (-HUB_D / 2 + 1.0,  ARM_W_ROOT / 2),
])
arm = extrude_polygon(arm_poly, height=ARM_T)

lever = trimesh.boolean.union([hub, arm], engine='manifold')

cuts = []

# D-shaped bore through the hub
r = BORE_D / 2
cyl = cylinder(radius=r, height=HUB_H + 6, sections=96)
cyl.apply_translation([0, 0, HUB_H / 2])
flat_off = BORE_FLAT - r
trim = trimesh.creation.box(extents=[BORE_D + 6, BORE_D + 6, HUB_H + 8])
trim.apply_translation([0, -flat_off - (BORE_D + 6) / 2, HUB_H / 2])
cuts.append(trimesh.boolean.difference([cyl, trim], engine='manifold'))

# Tapered lightening slot through the arm
slot_poly = Polygon([
    (SLOT_X0, -SLOT_HW0),
    (SLOT_X1, -SLOT_HW1),
    (SLOT_X1,  SLOT_HW1),
    (SLOT_X0,  SLOT_HW0),
])
slot = extrude_polygon(slot_poly, height=ARM_T + 4)
slot.apply_translation([0, 0, -2])
cuts.append(slot)

lever = trimesh.boolean.difference([lever] + cuts, engine='manifold')

assert lever.is_watertight, "lever not watertight!"
lever.export('/home/claude/lever_arm_demo_v2.stl')

print(f"watertight = {lever.is_watertight}")
print(f"volume     = {lever.volume:.0f} mm3")
print(f"bounds     = {lever.bounds.tolist()}")
print(f"bore       = {BORE_D} dia, {BORE_FLAT} across-flat")
print(f"arm        = {ARM_LEN} mm, {ARM_T} mm thick")
