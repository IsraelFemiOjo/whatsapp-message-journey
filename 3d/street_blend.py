"""Style frame scene: Lagos street at night, ground cut open to show the fiber duct."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math
sys.path.insert(0, ROOT + '/shared')
import bpy, bmesh
import numpy as np
from mathutils import Vector
from scene3d import tracked_camera, render_setup, project

bpy.ops.wm.read_factory_settings(use_empty=True)
def box(name, x0, x1, y0, y1, z0, z1, idx, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1)/2, (y0 + y1)/2, (z0 + z1)/2))
    o = bpy.context.active_object; o.name = name; o.scale = (x1 - x0, y1 - y0, z1 - z0); o.pass_index = idx
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new('b', 'BEVEL'); b.width = bevel; b.segments = 3
    return o

DZ, DR = -1.25, 0.42          # duct depth and radius
# ground block, cut face at y = 0, with a groove where the duct runs
g = box('ground', -14, 14, 0, 12, -3.2, -0.14, 1)
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=DR + 0.02, depth=40, location=(0, 0, DZ), rotation=(0, math.radians(90), 0))
cutter = bpy.context.active_object
m = g.modifiers.new('bo', 'BOOLEAN'); m.operation = 'DIFFERENCE'; m.object = cutter
bpy.context.view_layer.objects.active = g; bpy.ops.object.modifier_apply(modifier='bo')
bpy.data.objects.remove(cutter)
# road layers: asphalt on top of a gravel bed
box('asphalt', -14, 14, 0, 7.6, -0.14, 0.0, 2)
box('kerb', -14, 14, 7.6, 7.85, -0.14, 0.24, 3, 0.03)
box('pavement', -14, 14, 7.85, 12, -0.14, 0.2, 3)
# the duct: back half of an orange conduit, sliced open by the cut
bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=DR, depth=28, location=(0, 0, DZ), rotation=(0, math.radians(90), 0))
d = bpy.context.active_object; d.pass_index = 6
bm = bmesh.new(); bm.from_mesh(d.data)
bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.calc_center_median().y < -0.01 and abs(f.calc_center_median().x) < 13.9], context='FACES')
bm.to_mesh(d.data); bm.free()
sol = d.modifiers.new('s', 'SOLIDIFY'); sol.thickness = 0.04
# fibers inside the duct: a small bundle, one of them carries our message
FIB = []
for k, (fy, fz) in enumerate([(0.18, -0.08), (0.24, 0.05), (0.12, 0.12), (0.30, -0.18), (0.08, -0.22)]):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.028 if k else 0.034, depth=28, location=(0, fy, DZ + fz), rotation=(0, math.radians(90), 0))
    f = bpy.context.active_object; f.pass_index = 7 if k == 0 else 8; FIB.append((fy, DZ + fz))
# a second, grey duct lower down (other services)
bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=0.26, depth=28, location=(0, 0.6, -2.35), rotation=(0, math.radians(90), 0))
bpy.context.active_object.pass_index = 9
# street furniture: lamp post on the pavement
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.07, depth=4.4, location=(3.2, 8.4, 2.4)); bpy.context.active_object.pass_index = 10
bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.05, depth=1.4, location=(3.2, 7.75, 4.55), rotation=(math.radians(90), 0, 0)); bpy.context.active_object.pass_index = 10
LAMP = (3.2, 7.1, 4.45)
box('lamphead', 3.05, 3.35, 6.85, 7.4, 4.4, 4.53, 11)
# buildings along the far side
rng = np.random.default_rng(7)
x = -14
while x < 14:
    w = rng.uniform(2.2, 4.2); h = rng.uniform(3.5, 9.0)
    box('bld', x, x + w - 0.2, 9.5, 12.0, 0.0, h, 12)
    x += w
# a yellow minibus with black stripes (Lagos style), parked on the road
bus = box('bus', -7.8, -2.6, 4.6, 6.6, 0.35, 2.35, 13, 0.18)
box('win', -7.6, -3.0, 4.55, 4.6, 1.45, 2.1, 14)
box('stripe', -7.82, -2.58, 4.57, 4.6, 1.0, 1.15, 15)
for wx in (-6.8, -3.6):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.4, depth=0.3, location=(wx, 4.58, 0.4), rotation=(math.radians(90), 0, 0)); bpy.context.active_object.pass_index = 16

cam, tgt = tracked_camera((-0.6, 1.2, -0.5), lens=26)
cam.location = (2.2, -5.0, 0.9)
render_setup(int(sys.argv[sys.argv.index('--') + 2]) if '--' in sys.argv else 2160)
bpy.context.view_layer.update()
out = sys.argv[sys.argv.index('--') + 1]
fy, fz = FIB[0]
A = {'fiber': [project(Vector((x, fy - 0.04, fz)), cam) for x in np.linspace(-14, 14, 400)], 'lamp': project(Vector(LAMP), cam),
     'duct_top': project(Vector((0, 0, DZ + DR)), cam), 'ground_top': project(Vector((0, 0, -0.14)), cam), 'ground_bot': project(Vector((0, 0, -3.2)), cam)}
json.dump(A, open(out.replace('.exr', '.json'), 'w'))
bpy.context.scene.render.filepath = out; bpy.ops.render.render(write_still=True)
print('done')
