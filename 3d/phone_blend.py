"""Opening shot: a phone held at night in Lagos. Screen corners exported so the chat UI can be mapped on."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math
sys.path.insert(0, ROOT + '/shared')
import bpy
from mathutils import Vector, Euler
from scene3d import tracked_camera, render_setup, project

bpy.ops.wm.read_factory_settings(use_empty=True)
PW, PH, PD = 0.74, 1.56, 0.075
root = bpy.data.objects.new('phone', None); bpy.context.collection.objects.link(root)
bpy.ops.mesh.primitive_cube_add(size=1)
body = bpy.context.active_object; body.scale = (PW, PD, PH); bpy.ops.object.transform_apply(scale=True)
b = body.modifiers.new('b', 'BEVEL'); b.width = 0.09; b.segments = 10; body.pass_index = 20; body.parent = root
bpy.ops.object.shade_smooth()
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -PD/2 - 0.001, 0))
scr = bpy.context.active_object; scr.scale = (PW - 0.05, 0.002, PH - 0.05); bpy.ops.object.transform_apply(scale=True)
b = scr.modifiers.new('b', 'BEVEL'); b.width = 0.065; b.segments = 8; scr.pass_index = 21; scr.parent = root
# side buttons
for z in (0.35, 0.18):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(PW/2 + 0.006, 0, z)); o = bpy.context.active_object; o.scale = (0.012, 0.03, 0.12); o.pass_index = 22; o.parent = root
root.rotation_euler = Euler((math.radians(-10), math.radians(-5), math.radians(-14)))
root.location = (0, 0, 0)
cam, tgt = tracked_camera((-0.42, 0, -0.2), lens=46)
cam.location = (0.55, -2.7, -0.7)
render_setup(int(sys.argv[sys.argv.index('--') + 2]) if '--' in sys.argv else 2160)
bpy.context.view_layer.update()
out = sys.argv[sys.argv.index('--') + 1]
sw, sh = (PW - 0.05)/2, (PH - 0.05)/2
corners = [root.matrix_world @ Vector((x, -PD/2 - 0.003, z)) for x, z in ((-sw, sh), (sw, sh), (sw, -sh), (-sw, -sh))]
A = {'screen': [project(c, cam) for c in corners]}
json.dump(A, open(out.replace('.exr', '.json'), 'w'))
bpy.context.scene.render.filepath = out; bpy.ops.render.render(write_still=True)
print('done')
