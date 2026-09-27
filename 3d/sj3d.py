"""Shared Blender helpers for the send journey: world position AOV, render setup, camera export, simple builders."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, math, json
sys.path.insert(0, ROOT + '/shared')
import bpy, bmesh
import numpy as np
from mathutils import Vector, Euler, Matrix
from scene3d import render_setup as _rs, project, tracked_camera, catmull

def pos_material():
    m = bpy.data.materials.get('PAOV')
    if m: return m
    m = bpy.data.materials.new('PAOV'); m.use_nodes = True
    nt = m.node_tree; nt.nodes.clear()
    g = nt.nodes.new('ShaderNodeNewGeometry'); a = nt.nodes.new('ShaderNodeOutputAOV'); a.aov_name = 'P'
    nt.links.new(g.outputs['Position'], a.inputs['Color'])
    o = nt.nodes.new('ShaderNodeOutputMaterial'); d = nt.nodes.new('ShaderNodeBsdfDiffuse'); nt.links.new(d.outputs[0], o.inputs[0])
    return m

def finalize_materials():
    m = pos_material()
    for ob in bpy.data.objects:
        if ob.type in ('MESH', 'CURVE') and ob.data is not None:
            ob.data.materials.clear(); ob.data.materials.append(m)

def render_setup(res=2160):
    _rs(res)
    vl = bpy.context.scene.view_layers[0]
    if 'P' not in [a.name for a in vl.aovs]:
        av = vl.aovs.add(); av.name = 'P'; av.type = 'COLOR'

def box(x0, x1, y0, y1, z0, z1, idx, bevel=0.0, parent=None, name='box'):
    bpy.ops.mesh.primitive_cube_add(size=1, location=((x0 + x1)/2, (y0 + y1)/2, (z0 + z1)/2))
    o = bpy.context.active_object; o.name = name; o.scale = (x1 - x0, y1 - y0, z1 - z0); o.pass_index = idx
    bpy.ops.object.transform_apply(scale=True)
    if bevel:
        b = o.modifiers.new('b', 'BEVEL'); b.width = bevel; b.segments = 3
    if parent: o.parent = parent
    return o

def rod(p0, p1, r, idx, parent=None, verts=8):
    p0, p1 = Vector(p0), Vector(p1); d = p1 - p0
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=d.length, location=(p0 + p1)/2)
    o = bpy.context.active_object; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = d.to_track_quat('Z', 'Y'); o.pass_index = idx
    if parent: o.parent = parent
    return o

def cam_info(cam):
    sc = bpy.context.scene
    return {'M': [list(r) for r in cam.matrix_world], 'lens': cam.data.lens, 'sensor': cam.data.sensor_width}

def args():
    a = sys.argv[sys.argv.index('--') + 1:]
    return a[0], int(a[1]), int(a[2]), int(a[3]) if len(a) > 3 else 2160, int(a[4]) if len(a) > 4 else 2
