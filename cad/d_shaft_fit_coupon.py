"""
D-shaft fit test coupon.
Four D-shaped through-holes, shaft diameter 3.0mm nominal, varying
across-flat dimension. Push the motor shaft into each and find the one
that seats fully with no rotational play.

Hole 1 (1 dimple): across-flat 2.25
Hole 2 (2 dimples): across-flat 2.35
Hole 3 (3 dimples): across-flat 2.45
Hole 4 (4 dimples): across-flat 2.55

Bore diameter is 3.15 on all four (3.0 shaft + 0.15 PETG clearance).
Print flat, no supports, 0.15-0.2mm layers for hole accuracy.
"""

import numpy as np
import trimesh
from trimesh.creation import box, cylinder

BORE_D    = 3.15          # 3.0 shaft + clearance
FLATS     = [2.25, 2.35, 2.45, 2.55]
TILE_X    = 60.0
TILE_Y    = 18.0
TILE_Z    = 6.0           # thick enough to feel real engagement
SPACING   = 13.0
DIMPLE_D  = 1.6
DIMPLE_H  = 0.8

r = BORE_D / 2
tile = box(extents=[TILE_X, TILE_Y, TILE_Z])
tile.apply_translation([0, 0, TILE_Z / 2])

cuts = []
x0 = -SPACING * (len(FLATS) - 1) / 2

for i, f in enumerate(FLATS):
    cx = x0 + i * SPACING

    # D-profile tool = full cylinder minus the segment beyond the flat plane
    cyl = cylinder(radius=r, height=TILE_Z + 4, sections=96)
    cyl.apply_translation([cx, 2.0, TILE_Z / 2])

    flat_off = f - r                       # distance from center to flat face
    trim = box(extents=[BORE_D + 4, BORE_D + 4, TILE_Z + 6])
    # remove everything below y = -(flat_off)
    trim.apply_translation([cx, 2.0 - flat_off - (BORE_D + 4) / 2, TILE_Z / 2])
    d_tool = trimesh.boolean.difference([cyl, trim], engine='manifold')
    cuts.append(d_tool)

    # identification dimples: i+1 dots in a row below each hole
    for k in range(i + 1):
        dx = cx - (i * 1.1) + k * 2.2
        d = cylinder(radius=DIMPLE_D / 2, height=DIMPLE_H * 2, sections=32)
        d.apply_translation([dx, -5.5, TILE_Z])
        cuts.append(d)

coupon = trimesh.boolean.difference([tile] + cuts, engine='manifold')

assert coupon.is_watertight, "mesh not watertight!"
coupon.export('/home/claude/d_shaft_fit_coupon.stl')

print(f"Watertight: {coupon.is_watertight}")
print(f"Bounds (mm): {coupon.bounds}")
for i, f in enumerate(FLATS):
    print(f"  hole {i+1} ({i+1} dimple{'s' if i else ''}): bore {BORE_D}, across-flat {f}")
