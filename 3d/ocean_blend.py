"""Style frame scene: the cable on the Atlantic floor."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math
sys.path.insert(0, ROOT + '/shared')
import bpy, bmesh
import numpy as np
from mathutils import Vector
from scene3d import tracked_camera, render_setup, project

bpy.ops.wm.read_factory_settings(use_empty=True)

def hfield(x, y):
    """gentle seabed: long swells, ripples and a few mounds"""
    return (0.35*np.sin(x*0.21 + 1.3)*np.cos(y*0.13) + 0.07*np.sin(x*0.63 + y*0.27) + 0.03*np.sin(x*2.1 + y*1.7)
            + 0.9*np.exp(-((x + 7)**2 + (y - 26)**2)/30) + 0.6*np.exp(-((x - 9)**2 + (y - 14)**2)/18) - 0.02*y*0.2)

# seabed
bpy.ops.mesh.primitive_grid_add(x_subdivisions=260, y_subdivisions=360, size=1)
sb = bpy.context.active_object; sb.scale = (46, 70, 1); bpy.ops.object.transform_apply(scale=True)
me = sb.data
for v in me.vertices:
    v.co.y += 30
    v.co.z = float(hfield(v.co.x, v.co.y))
me.update(); bpy.ops.object.shade_smooth(); sb.pass_index = 1

# the cable path along the floor
ys = np.linspace(-3, 64, 240)
xs = 3.2*np.sin(ys*0.11 + 0.9) + 0.9*np.sin(ys*0.27) - 1.0
pts = [(float(x), float(y), float(hfield(x, y)) + 0.07) for x, y in zip(xs, ys)]
cu = bpy.data.curves.new('cable', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.075; cu.bevel_resolution = 4
sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
cab = bpy.data.objects.new('cable', cu); bpy.context.collection.objects.link(cab); cab.pass_index = 2

# repeaters: capsules sitting on the cable
def repeater(i):
    p = Vector(pts[i]); q = Vector(pts[i + 3]); d = (q - p).normalized()
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.28, depth=1.5, location=p + Vector((0, 0, 0.2)))
    c = bpy.context.active_object; c.rotation_mode = 'QUATERNION'; c.rotation_quaternion = d.to_track_quat('Z', 'Y'); c.pass_index = 3
    bev = c.modifiers.new('b', 'BEVEL'); bev.width = 0.12; bev.segments = 8; bpy.ops.object.shade_smooth()
    for s in (-1, 1):   # tapered collars where the cable enters
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.2, radius2=0.08, depth=0.5, location=p + Vector((0, 0, 0.2)) + d*s*0.95)
        k = bpy.context.active_object; k.rotation_mode = 'QUATERNION'
        k.rotation_quaternion = (d*s).to_track_quat('Z', 'Y'); k.pass_index = 5; bpy.ops.object.shade_smooth()
    return p
R1 = repeater(47); R2 = repeater(130)

# rocks
rng = np.random.default_rng(3)
for k in range(26):
    x, y = rng.uniform(-14, 14), rng.uniform(1, 55)
    if abs(x - (3.2*math.sin(y*0.11 + 0.9) + 0.9*math.sin(y*0.27) - 1.0)) < 1.3: continue
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=rng.uniform(0.15, 0.7), location=(x, y, float(hfield(x, y))))
    r = bpy.context.active_object; r.scale = (rng.uniform(0.8, 1.6), rng.uniform(0.8, 1.4), rng.uniform(0.4, 0.8))
    r.rotation_euler = tuple(rng.uniform(0, 3, 3)); r.pass_index = 4

cam, tgt = tracked_camera((-0.8, 9.0, -0.5), lens=30)
cam.location = (2.6, -4.4, 3.3)
render_setup(int(sys.argv[sys.argv.index('--') + 2]) if '--' in sys.argv else 2160)
bpy.context.view_layer.update()
sc = bpy.context.scene
out = sys.argv[sys.argv.index('--') + 1]
A = {'cable': [project(Vector(p), cam) for p in pts], 'R1': project(R1, cam), 'R2': project(R2, cam)}
json.dump(A, open(out.replace('.exr', '.json'), 'w'))
sc.render.filepath = out; bpy.ops.render.render(write_still=True)
print('done')
