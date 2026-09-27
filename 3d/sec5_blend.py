"""Section 5 (18.6 to 28.5 s): sink to the Atlantic floor, follow the pulse along the cable past a repeater, close in on the cable."""
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
def hfield(x, y):
    return (0.35*np.sin(x*0.21 + 1.3)*np.cos(y*0.13) + 0.07*np.sin(x*0.63 + y*0.27) + 0.03*np.sin(x*2.1 + y*1.7)
            + 0.9*np.exp(-((x + 7)**2 + (y - 26)**2)/30) + 0.6*np.exp(-((x - 9)**2 + (y - 14)**2)/18) - 0.02*y*0.2)
bpy.ops.mesh.primitive_grid_add(x_subdivisions=300, y_subdivisions=460, size=1)
sb = bpy.context.active_object; sb.scale = (60, 120, 1); bpy.ops.object.transform_apply(scale=True)
for v in sb.data.vertices:
    v.co.y += 30; v.co.z = float(hfield(v.co.x, v.co.y))
sb.data.update(); bpy.ops.object.shade_smooth(); sb.pass_index = 1
ys = np.linspace(-15, 90, 520)
xs = 3.2*np.sin(ys*0.11 + 0.9) + 0.9*np.sin(ys*0.27) - 1.0
PTS = [(float(x), float(y), float(hfield(x, y)) + 0.07) for x, y in zip(xs, ys)]
cu = bpy.data.curves.new('cable', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.075; cu.bevel_resolution = 4
sp = cu.splines.new('POLY'); sp.points.add(len(PTS) - 1)
for i, p in enumerate(PTS): sp.points[i].co = (*p, 1)
cab = bpy.data.objects.new('cable', cu); bpy.context.collection.objects.link(cab); cab.pass_index = 2
def repeater(i):
    p = Vector(PTS[i]); q = Vector(PTS[i + 3]); d = (q - p).normalized()
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.28, depth=1.5, location=p + Vector((0, 0, 0.2)))
    c = bpy.context.active_object; c.rotation_mode = 'QUATERNION'; c.rotation_quaternion = d.to_track_quat('Z', 'Y'); c.pass_index = 3
    bev = c.modifiers.new('b', 'BEVEL'); bev.width = 0.12; bev.segments = 8; bpy.ops.object.shade_smooth()
    for s in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.2, radius2=0.08, depth=0.5, location=p + Vector((0, 0, 0.2)) + d*s*0.95)
        k = bpy.context.active_object; k.rotation_mode = 'QUATERNION'; k.rotation_quaternion = (d*s).to_track_quat('Z', 'Y'); k.pass_index = 5
        bpy.ops.object.shade_smooth()
    return p
REP_I = [140, 400]
REPS = [repeater(i) for i in REP_I]
rng = np.random.default_rng(3)
for k in range(60):
    x, y = rng.uniform(-22, 22), rng.uniform(-10, 90)
    if abs(x - (3.2*math.sin(y*0.11 + 0.9) + 0.9*math.sin(y*0.27) - 1.0)) < 1.3: continue
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rng.uniform(0.15, 0.7), location=(x, y, float(hfield(x, y))))
    r = bpy.context.active_object; r.scale = (rng.uniform(0.8, 1.6), rng.uniform(0.8, 1.4), rng.uniform(0.4, 0.8))
    r.rotation_euler = tuple(rng.uniform(0, 3, 3)); r.pass_index = 4
CUM = [0] + list(np.cumsum([np.linalg.norm(np.subtract(PTS[i + 1], PTS[i])) for i in range(len(PTS) - 1)]))
def at_s(s):
    i = int(np.searchsorted(CUM, s) - 1); i = max(0, min(i, len(PTS) - 2))
    f = (s - CUM[i])/(CUM[i + 1] - CUM[i] + 1e-9)
    return Vector(np.add(PTS[i], np.multiply(np.subtract(PTS[i + 1], PTS[i]), f)))
S_REP = CUM[REP_I[0]]
def pulse_s(t):
    # arrives in view, slows as the camera settles, passes the repeater around 24.8 s, runs on
    return 4.0 + (S_REP - 4.0)*seg(t, 18.6, 24.8)**0.85 + 14.0*seg(t, 24.8, 28.5)**1.3
cam, tgt = tracked_camera((0, 0, 0), lens=30)
def cam_at(t):
    p = at_s(pulse_s(t)); ahead = at_s(pulse_s(t) + 3.0)
    d = (ahead - p).normalized(); side = d.cross(Vector((0, 0, 1))).normalized()
    top_c = p + Vector((0.0, -0.8, 40.0)); top_t = p
    hold_c = p - d*5.5 - side*2.4 + Vector((0, 0, 2.6)); hold_t = p + d*6 + Vector((0, 0, -0.4))
    close_c = p - d*0.9 - side*0.35 + Vector((0, 0, 0.28)); close_t = p + d*0.25
    k = ease(seg(t, 19.2, 21.4))
    c = top_c.lerp(hold_c, k); g = top_t.lerp(hold_t, k)
    m = ease(seg(t, 25.9, 27.6))
    c = c.lerp(close_c, m); g = g.lerp(close_t, m)
    return c, g, 30 + 8*m
render_setup(2160); finalize_materials()
out, first, last, res, step = args()
bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = res
A = {}
for f in range(first, last + 1, step):
    t = 18.6 + (f - 1)/FPS
    c, g, lens = cam_at(t)
    cam.location = c; tgt.location = g; cam.data.lens = lens; cam.data.clip_start = 0.01; cam.data.clip_end = 500
    bpy.context.view_layer.update()
    s = pulse_s(t)
    A[f] = {'t': t, 's': s, 'pulse': project(at_s(s), cam), 'reps': [project(r, cam) for r in REPS], 'cam': cam_info(cam)}
    bpy.context.scene.render.filepath = f'{out}/{f:04d}.exr'; bpy.ops.render.render(write_still=True)
json.dump({'anchors': A, 'pts': PTS, 'cum': CUM, 'rep_s': [CUM[i] for i in REP_I]}, open(f'{out}/anchors_{first}_{last}.json', 'w'))
print('done')
