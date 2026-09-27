"""Section 6 (28.5 to 35.5 s): a server hall. The pulse is held in a server, then sent on down the aisle."""
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
box(-6, 6, -6, 60, -0.05, 0, 50, name='floor')
box(-6, 6, -6, 60, 3.4, 3.5, 53, name='ceiling')
for y in np.arange(-4, 58, 3.0):   # light strips
    box(-0.4, 0.4, y, y + 1.6, 3.33, 3.4, 54, name='strip')
RACKS = []
for side in (-1, 1):
    for k in range(92):
        y0 = k*0.65
        xf = side*1.25                       # front face toward the aisle
        x0, x1 = (xf, xf + side*1.1) if side > 0 else (xf - 1.1, xf)
        box(min(x0, x1), max(x0, x1), y0, y0 + 0.62, 0, 2.2, 51, name='rack')
        # front panel, slightly proud, where the lights live
        fx = xf - side*0.012
        box(min(fx, fx + side*0.01), max(fx, fx + side*0.01), y0 + 0.04, y0 + 0.58, 0.08, 2.12, 52, name='panel')
        RACKS.append((side, y0))
    # cable tray above each row
    box(side*1.5 - 0.3, side*1.5 + 0.3, -4, 58, 2.55, 2.62, 55, name='tray')
# the server holding our message: right row, rack 8, light at 1.25 m
LED = Vector((1.25 - 0.03, 8*0.65 + 0.31, 1.25))
TRAY = Vector((1.5, 8*0.65 + 0.31, 2.62))
FAR = Vector((1.5, 58, 2.62))
def pulse_pos(t):
    if t < 31.9: return LED.copy()
    k = seg(t, 31.9, 32.4)
    if t < 32.4: return LED.lerp(TRAY, ease(k))
    return TRAY.lerp(FAR, seg(t, 32.4, 35.5)**1.7)
cam, tgt = tracked_camera((0, 0, 0), lens=30)
def cam_at(t):
    p = pulse_pos(t)
    close_c = LED + Vector((-0.12, -0.02, 0.01)); close_t = LED
    wide_c = LED + Vector((-1.9, -2.6, 0.35)); wide_t = LED + Vector((0.2, 1.0, 0.1))
    k = ease(seg(t, 28.9, 30.8))
    c = close_c.lerp(wide_c, k); g = close_t.lerp(wide_t, k)
    # chase down the aisle once it leaves
    ch = ease(seg(t, 32.2, 33.4))
    chase_c = p + Vector((-1.4, -3.2, -0.4)); chase_t = p + Vector((-0.3, 4.0, -0.3))
    c = c.lerp(chase_c, ch); g = g.lerp(chase_t, ch)
    return c, g, 26 + 6*(1 - k) - 4*ch
render_setup(2160); finalize_materials()
out, first, last, res, step = args()
bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = res
A = {}
for f in range(first, last + 1, step):
    t = 28.5 + (f - 1)/FPS
    c, g, lens = cam_at(t)
    cam.location = c; tgt.location = g; cam.data.lens = lens; cam.data.clip_start = 0.005
    bpy.context.view_layer.update()
    A[f] = {'t': t, 'pulse': project(pulse_pos(t), cam), 'led': project(LED, cam), 'cam': cam_info(cam)}
    bpy.context.scene.render.filepath = f'{out}/{f:04d}.exr'; bpy.ops.render.render(write_still=True)
json.dump({'anchors': A, 'led': list(LED), 'tray': list(TRAY), 'far': list(FAR)}, open(f'{out}/anchors_{first}_{last}.json', 'w'))
print('done')
