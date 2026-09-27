"""Section 3 (11.0 to 14.0 s): the Lagos coast from the air. The cable leaves the landing station and runs into the sea.
Geography: coastline runs east to west, the Atlantic to the south (like the Lagos shoreline)."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math
sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
import bpy
import numpy as np
from mathutils import Vector
from sj3d import *

bpy.ops.wm.read_factory_settings(use_empty=True)
FPS = 24
def ease(x): x = min(1, max(0, x)); return x*x*(3 - 2*x)
def seg(t, a, b): return min(1, max(0, (t - a)/(b - a)))
rng = np.random.default_rng(12)
# land north of y = 0, beach from y = 0 down to y = -70, then the sea
box(-4000, 4000, 0, 3000, -0.5, 0.0, 1, name='land')
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -35, -0.25)); b = bpy.context.active_object
b.scale = (8000, 70, 1); bpy.ops.object.transform_apply(scale=True); b.rotation_euler = (math.atan2(0.5, 70), 0, 0); b.pass_index = 3
bpy.ops.mesh.primitive_plane_add(size=1, location=(0, -3070, -0.7)); s = bpy.context.active_object
s.scale = (8000, 6000, 1); bpy.ops.object.transform_apply(scale=True); s.pass_index = 5
# coastal road with its fiber, then the city behind it
box(-4000, 4000, 8, 20, 0, 0.05, 2, name='road')
for gx in range(-60, 61):
    for gy in range(0, 26):
        if rng.random() < 0.25: continue
        cx, cy = gx*34.0, 40 + gy*34.0
        if abs(cx) < 40 and cy < 90: continue
        w, d = rng.uniform(10, 24), rng.uniform(10, 24)
        h = rng.choice([rng.uniform(6, 15), rng.uniform(15, 30), rng.uniform(35, 70)], p=[0.6, 0.32, 0.08])
        box(cx - w/2, cx + w/2, cy - d/2, cy + d/2, 0, h, 12, name='bld')
# the cable landing station: a low building behind a fence, and the beach manhole
box(-14, 14, 30, 52, 0, 7, 40, name='station')
for x in np.arange(-22, 23, 2.2):
    rod((x, 26, 0), (x, 26, 2.2), 0.06, 41); rod((x, 56, 0), (x, 56, 2.2), 0.06, 41)
for y in np.arange(26, 57, 2.2):
    rod((-22, y, 0), (-22, y, 2.2), 0.06, 41); rod((22, y, 0), (22, y, 2.2), 0.06, 41)
box(-1.2, 1.2, -18, -15.6, -0.1, 0.25, 42, name='manhole')
# cable path: along the coast road from the west, into the station, then south under the beach and out to sea
ROAD = [(x, 14.0, -0.6) for x in np.linspace(-700, -8, 60)] + [(-8, 30, -0.6), (0, 38, -0.6)]
SEA = [(0, 38, -0.9), (0, 20, -1.2), (0, -17, -1.2), (0, -70, -2.0)] + [(0 - 0.00004*y*y, y, -2 - 0.02*(-70 - y)) for y in np.linspace(-120, -3200, 40)]
PATH = ROAD + SEA
seglen = [0] + list(np.cumsum([np.linalg.norm(np.subtract(PATH[i + 1], PATH[i])) for i in range(len(PATH) - 1)]))
TOT = seglen[-1]; S_STATION = seglen[len(ROAD) - 1]
def at_s(sv):
    i = int(np.searchsorted(seglen, sv) - 1); i = max(0, min(i, len(PATH) - 2))
    f = (sv - seglen[i])/(seglen[i + 1] - seglen[i] + 1e-9)
    return Vector(np.add(PATH[i], np.multiply(np.subtract(PATH[i + 1], PATH[i]), f)))
def pulse_s(t):
    # along the road to the station fast, a beat at the station, then down the beach and out to sea
    s1 = S_STATION*seg(t, 11.0, 12.0)**0.9
    s2 = 1500*seg(t, 12.15, 14.0)**1.8
    return s1 + s2
cam, tgt = tracked_camera((0, 0, 0), lens=30)
def cam_at(t):
    p = at_s(pulse_s(t))
    # oblique, following the pulse along the road (camera to the south east, looking north west over the beach)
    c1 = p + Vector((70, -120, 75)); g1 = p + Vector((-10, 10, 0))
    # rising, turning to straight down with north up
    k = ease(seg(t, 11.9, 13.4))
    alt = 75 + (4200 - 75)*ease(seg(t, 12.0, 14.0))**1.7
    c2 = Vector((p.x, p.y - 1.0, alt)); g2 = Vector((p.x, p.y, 0))
    c = c1.lerp(c2, k); g = g1.lerp(g2, k)
    return c, g, 30
render_setup(2160); finalize_materials()
out, first, last, res, step = args()
bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = res
A = {}
for f in range(first, last + 1, step):
    t = 11.0 + (f - 1)/FPS
    c, g, lens = cam_at(t)
    cam.location = c; tgt.location = g; cam.data.lens = lens; cam.data.clip_end = 20000
    # keep north up when looking straight down
    tr = cam.constraints[0]; tr.up_axis = 'UP_Y'
    bpy.context.view_layer.update()
    sv = pulse_s(t)
    A[f] = {'t': t, 'pulse': project(at_s(sv), cam), 's': sv, 'cam': cam_info(cam)}
    bpy.context.scene.render.filepath = f'{out}/{f:04d}.exr'; bpy.ops.render.render(write_still=True)
json.dump({'anchors': A, 'path': [list(p) for p in PATH], 'seglen': seglen, 's_station': S_STATION}, open(f'{out}/anchors_{first}_{last}.json', 'w'))
print('done')
