"""Section 1 (0 to 6 s): tap, scramble on the phone, radio out over Lagos at night, into the tower antenna."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math
sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
import bpy
import numpy as np
from mathutils import Vector, Euler
from sj3d import *

bpy.ops.wm.read_factory_settings(use_empty=True)
FPS = 24
def ease(x): x = min(1, max(0, x)); return x*x*(3 - 2*x)
def seg(t, a, b): return min(1, max(0, (t - a)/(b - a)))

# ---------------- the phone, held on a balcony 20 m up ----------------
PH0 = Vector((0, 0, 20.0))
SC = 0.1
PW, PHh, PD = 0.74*SC, 1.56*SC, 0.075*SC
phone = bpy.data.objects.new('phone', None); bpy.context.collection.objects.link(phone)
bpy.ops.mesh.primitive_cube_add(size=1); b = bpy.context.active_object; b.scale = (PW, PD, PHh); bpy.ops.object.transform_apply(scale=True)
bv = b.modifiers.new('b', 'BEVEL'); bv.width = 0.009; bv.segments = 10; b.pass_index = 20; b.parent = phone; bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -PD/2 - 0.0001, 0)); s = bpy.context.active_object
s.scale = (PW - 0.005, 0.0002, PHh - 0.005); bpy.ops.object.transform_apply(scale=True)
bv = s.modifiers.new('b', 'BEVEL'); bv.width = 0.0065; bv.segments = 8; s.pass_index = 21; s.parent = phone
for z in (0.035, 0.018):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(PW/2 + 0.0006, 0, z)); o = bpy.context.active_object; o.scale = (0.0012, 0.003, 0.012); o.pass_index = 22; o.parent = phone
phone.location = PH0; phone.rotation_euler = Euler((math.radians(-10), math.radians(-5), math.radians(-14)))
bpy.context.view_layer.update()
sw, sh = (PW - 0.005)/2, (PHh - 0.005)/2
def on_screen(u, v):   # screen uv (0,0 top left) to world
    return phone.matrix_world @ Vector((-sw + 2*sw*u, -PD/2 - 0.0003, sh - 2*sh*v))
CORNERS = [on_screen(0, 0), on_screen(1, 0), on_screen(1, 1), on_screen(0, 1)]
BUBBLE_UV = (0.7075, 0.2896)
SEND_UV = (0.9136, 0.948)
P_START = on_screen(*BUBBLE_UV)

# ---------------- Lagos at night: a low city with a few towers ----------------
rng = np.random.default_rng(4)
for gx in range(-9, 10):
    for gy in range(-2, 16):
        cx, cy = gx*24.0, gy*24.0 + 12
        if abs(cx) < 30 and cy < 40: continue            # our own block stays open
        if abs(gx*24.0 - 40) < 14 and abs(gy*24.0 + 12 - 160) < 14: continue   # the tower's lot
        for k in range(int(rng.integers(1, 4))):
            w, d = rng.uniform(7, 15), rng.uniform(7, 15)
            h = rng.choice([rng.uniform(6, 14), rng.uniform(14, 26), rng.uniform(30, 55)], p=[0.62, 0.3, 0.08])
            x0 = cx + rng.uniform(-9, 9) - w/2; y0 = cy + rng.uniform(-9, 9) - d/2
            # keep the sight line from the phone to the tower clear of tall blocks
            lx, ly = x0 + w/2, y0 + d/2
            if 0 < ly < 170 and abs(lx - 40*ly/160) < 22: h = min(h, rng.uniform(5, 12))
            box(x0, x0 + w, y0, y0 + d, 0, h, 12, name='bld')
            if h < 26 and rng.random() < 0.6:   # rooftop water tanks, a Lagos signature
                for q in range(int(rng.integers(1, 3))):
                    tx_, ty_ = x0 + rng.uniform(1.5, w - 1.5), y0 + rng.uniform(1.5, d - 1.5)
                    bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=rng.uniform(0.7, 1.1), depth=1.6, location=(tx_, ty_, h + 1.3))
                    bpy.context.active_object.pass_index = 13
                    box(tx_ - 0.9, tx_ + 0.9, ty_ - 0.9, ty_ + 0.9, h, h + 0.5, 14, name='stand')
# our balcony: a low wall in front of the camera at the start, out of focus
box(-400, 400, -100, 500, -0.2, 0, 1, name='ground')
# roads: long strips (lit later by street lights)
LIGHTS = []
for gy in range(-2, 16):
    y = gy*24.0
    box(-240, 240, y - 3, y + 3, 0, 0.02, 2, name='road')
    for x in np.arange(-230, 231, 18): LIGHTS.append((float(x), y + 3.5, 7.0))
for gx in range(-9, 10):
    x = gx*24.0 + 12
    box(x - 3, x + 3, -40, 380, 0, 0.02, 2, name='road')

# ---------------- the cell tower: lattice mast, three sector panels, a dish ----------------
TX, TY, TH = 40.0, 160.0, 34.0
tower = bpy.data.objects.new('tower', None); bpy.context.collection.objects.link(tower); tower.location = (TX, TY, 0)
legs = []
for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
    legs.append((sx, sy))
    rod((sx*2.4, sy*2.4, 0), (sx*0.7, sy*0.7, TH), 0.12, 30, tower)
for k in range(12):
    z0, z1 = k*TH/12, (k + 1)*TH/12
    w0, w1 = 2.4 - 1.7*z0/TH, 2.4 - 1.7*z1/TH
    for (ax, ay), (bx, by) in zip(legs, legs[1:] + legs[:1]):
        rod((ax*w0, ay*w0, z0), (bx*w1, by*w1, z1), 0.045, 30, tower)
        rod((bx*w0, by*w0, z0), (ax*w1, ay*w1, z1), 0.045, 30, tower)
box(-1.3, 1.3, -1.3, 1.3, TH - 0.2, TH, 30, parent=tower, name='platform')
ANT = None
for a in (0, 120, 240):
    r = math.radians(a - 90)
    px, py = 1.25*math.cos(r), 1.25*math.sin(r)
    o = box(-0.18, 0.18, -0.07, 0.07, -0.8, 0.8, 31, 0.03, name='panel'); o.parent = tower
    o.location = (px, py, TH + 1.2); o.rotation_euler = (0, 0, r + math.pi/2)
    if a == 0: ANT = (Vector((TX, TY, 0)) + Vector((px, py - 0.075, TH + 1.25)))
bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.55, depth=0.3, location=(TX + 1.0, TY + 1.0, TH - 2.5), rotation=(math.radians(90), 0, math.radians(35)))
bpy.context.active_object.pass_index = 32
rod((TX, TY, TH), (TX, TY, TH + 5), 0.05, 30)
TOP_LIGHT = (TX, TY, TH + 5.1)

# ---------------- camera and the pulse ----------------
cam, tgt = tracked_camera((0, 0, 0), lens=46)
C0 = PH0 + Vector((0.055, -0.27, -0.07)); T0 = PH0 + Vector((-0.042, 0, -0.02))
def pulse_pos(t):
    if t < 2.2: return P_START.copy()
    u = ease(seg(t, 2.2, 5.85))
    u = seg(t, 2.2, 5.85)**1.25
    return P_START.lerp(ANT, u)
NRM = (phone.matrix_world.to_3x3() @ Vector((0, -1, 0))).normalized()
D = (ANT - P_START).normalized()
UP = Vector((0, 0, 1)); SIDE = D.cross(UP).normalized()
CLOSE = P_START + NRM*0.085
WIDE_C = PH0 - D*4.2 + UP*1.1 - SIDE*0.8
WIDE_T = PH0 + D*30
def pulse_pos(t):
    if t < 2.5: return P_START.copy()
    u = seg(t, 2.5, 5.85)**1.6
    return P_START.lerp(ANT, u)
def cam_at(t):
    if t < 0.5: return C0, T0, 46
    if t < 2.2:   # push in on the bubble while it scrambles
        k = ease(seg(t, 0.5, 1.7))
        return C0.lerp(CLOSE, k), T0.lerp(P_START, k), 46 + 6*k
    if t < 3.3:   # pull back out through the glass: phone, rings, the city and the tower beyond
        k = ease(seg(t, 2.2, 3.3))
        return CLOSE.lerp(WIDE_C, k), P_START.lerp(WIDE_T, k), 52 - 20*k
    # chase the pulse to the tower, pushing into the antenna panel at the end
    p = pulse_pos(t)
    k = ease(seg(t, 3.3, 3.9))
    back = 5.5*(1 - ease(seg(t, 4.2, 5.8))) + 0.5*(1 - ease(seg(t, 5.75, 6.0)))
    chase = p - D*back + UP*(0.9*(1 - ease(seg(t, 4.6, 5.8))))
    c = WIDE_C.lerp(chase, k)
    g = WIDE_T.lerp(p + D*6, k)
    return c, g, 32 + 12*ease(seg(t, 4.5, 5.9))

render_setup(2160); finalize_materials()
out, first, last, res, step = args()
bpy.context.scene.render.resolution_x = bpy.context.scene.render.resolution_y = res
A = {}
for f in range(first, last + 1, step):
    t = (f - 1)/FPS
    c, g, lens = cam_at(t)
    cam.location = c; tgt.location = g; cam.data.lens = lens; cam.data.clip_start = 0.005
    bpy.context.view_layer.update()
    p = pulse_pos(t)
    A[f] = {'t': t, 'screen': [project(q, cam) for q in CORNERS], 'pulse': project(p, cam), 'phone': project(PH0, cam),
            'ant': project(ANT, cam), 'toplight': project(Vector(TOP_LIGHT), cam), 'cam': cam_info(cam),
            'lights': [project(Vector(l), cam) for l in LIGHTS]}
    bpy.context.scene.render.filepath = f'{out}/{f:04d}.exr'; bpy.ops.render.render(write_still=True)
json.dump({'anchors': A, 'P_START': list(P_START), 'ANT': list(ANT), 'lights': LIGHTS}, open(f'{out}/anchors_{first}_{last}.json', 'w'))
print('done')
