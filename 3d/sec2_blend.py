"""Section 2 (6.0 to 11.0 s): out of the fiber into the street cutaway, track the pulse, rise toward the coast."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math
sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
import bpy, bmesh
import numpy as np
from mathutils import Vector
from sj3d import *

bpy.ops.wm.read_factory_settings(use_empty=True)
FPS = 24
def ease(x): x = min(1, max(0, x)); return x*x*(3 - 2*x)
def seg(t, a, b): return min(1, max(0, (t - a)/(b - a)))
X0, X1 = -70, 70
DZ, DR = -1.25, 0.42
g = box(X0, X1, 0, 16, -3.2, -0.14, 1, name='ground')
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=DR + 0.02, depth=200, location=(0, 0, DZ), rotation=(0, math.radians(90), 0))
cutter = bpy.context.active_object
m = g.modifiers.new('bo', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cutter
bpy.context.view_layer.objects.active = g; bpy.ops.object.modifier_apply(modifier='bo'); bpy.data.objects.remove(cutter)
box(X0, X1, 0, 7.6, -0.14, 0.0, 2, name='asphalt')
box(X0, X1, 7.6, 7.85, -0.14, 0.24, 3, 0.03, name='kerb')
box(X0, X1, 7.85, 16, -0.14, 0.2, 3, name='pavement')
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=DR, depth=X1 - X0, location=(0, 0, DZ), rotation=(0, math.radians(90), 0))
d = bpy.context.active_object; d.pass_index = 6
bm = bmesh.new(); bm.from_mesh(d.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().y < -0.01 and abs(f.calc_center_median().x) < (X1 - X0)/2 - 0.1], context='FACES')
bm.to_mesh(d.data); bm.free()
sol = d.modifiers.new('s', 'SOLIDIFY'); sol.thickness = 0.04
FIB = []
for k, (fy, fz) in enumerate([(0.18, -0.08), (0.24, 0.05), (0.12, 0.12), (0.30, -0.18), (0.08, -0.22)]):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.028 if k else 0.034, depth=X1 - X0, location=(0, fy, DZ + fz), rotation=(0, math.radians(90), 0))
    bpy.context.active_object.pass_index = 7 if k == 0 else 8; FIB.append((fy, DZ + fz))
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.26, depth=X1 - X0, location=(0, 0.6, -2.35), rotation=(0, math.radians(90), 0))
bpy.context.active_object.pass_index = 9
LAMPS = []
for lx in np.arange(X0 + 6, X1, 16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.07, depth=4.4, location=(lx, 8.4, 2.4)); bpy.context.active_object.pass_index = 10
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.05, depth=1.4, location=(lx, 7.75, 4.55), rotation=(math.radians(90), 0, 0)); bpy.context.active_object.pass_index = 10
    box(lx - 0.15, lx + 0.15, 6.85, 7.4, 4.4, 4.53, 11, name='lamphead'); LAMPS.append((float(lx), 7.1, 4.45))
rng = np.random.default_rng(7)
x = X0
while x < X1:
    w = rng.uniform(2.6, 6.0); h = rng.uniform(4.0, 12.0)
    box(x, x + w - 0.25, 9.5, 13.0, 0.0, h, 12, name='bld')
    if rng.random() < 0.5:
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.5, depth=1.1, location=(x + w/2, 11.2, h + 0.9)); bpy.context.active_object.pass_index = 17
    x += w
def bus(x0, y0, idx=13):
    box(x0, x0 + 6.0, y0, y0 + 2.2, 0.35, 2.55, idx, 0.18, name='bus')
    box(x0 + 0.2, x0 + 5.6, y0 - 0.05, y0, 1.55, 2.3, 14, name='win')
    box(x0 - 0.02, x0 + 6.02, y0 - 0.03, y0, 1.1, 1.25, 15, name='stripe')
    for wx in (x0 + 1.2, x0 + 4.8):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.42, depth=0.3, location=(wx, y0 - 0.02, 0.42), rotation=(math.radians(90), 0, 0)); bpy.context.active_object.pass_index = 16
bus(-26, 3.2); bus(8, 4.6); bus(38, 3.4)

fy, fz = FIB[0]
def pulse_x(t): return -18 + 46*seg(t, 6.75, 10.9)**1.15
cam, tgt = tracked_camera((0, 0, 0), lens=26)
def cam_at(t):
    xp = pulse_x(t)
    p = Vector((xp, fy - 0.03, fz))
    wide_c = Vector((xp + 2.5, -4.9, 0.85)); wide_t = Vector((xp - 0.5, 1.2, -0.7))
    close_c = Vector((xp - 0.25, fy - 0.14, fz + 0.02)); close_t = p + Vector((0.6, 0.05, 0))
    k = ease(seg(t, 6.75, 7.7))
    c = close_c.lerp(wide_c, k); g = close_t.lerp(wide_t, k); lens = 20 + 6*k
    # rise at the end: crane up and look down the line toward the coast
    r = ease(seg(t, 10.05, 11.0))
    c = c.lerp(Vector((xp - 3.0, -4.2, 7.5)), r); g = g.lerp(Vector((xp + 5.0, 1.0, -1.0)), r)
    return c, g, lens
render_setup(2160); finalize_materials()
out, first, last, res, step = args()
bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = res
A = {}
for f in range(first, last + 1, step):
    t = 6.0 + (f - 1)/FPS
    c, gg, lens = cam_at(t)
    cam.location = c; tgt.location = gg; cam.data.lens = lens; cam.data.clip_start = 0.01
    bpy.context.view_layer.update()
    xp = pulse_x(t)
    A[f] = {'t': t, 'pulse': project(Vector((xp, fy - 0.03, fz)), cam), 'cam': cam_info(cam),
            'lamps': [project(Vector(l), cam) for l in LAMPS]}
    bpy.context.scene.render.filepath = f'{out}/{f:04d}.exr'; bpy.ops.render.render(write_still=True)
json.dump({'anchors': A, 'fiber': [fy, fz], 'lamps': LAMPS}, open(f'{out}/anchors_{first}_{last}.json', 'w'))
print('done')
