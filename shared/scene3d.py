"""Blender scene builder: stylised (not photoreal) 3D glasses. Renders data passes only; the look is made in numpy."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import bpy, math, sys
from mathutils import Vector
from shapely.geometry import Polygon
from shapely.ops import unary_union

S = 1/250.0
WAY_OUT = [(-168, -104), (-60, -112), (90, -112), (176, -124), (192, -100), (177, -40), (150, 40), (96, 90), (0, 100), (-96, 88), (-148, 46), (-170, -20)]
WAY_IN = [(-148, -78), (-50, -86), (100, -84), (160, -92), (154, -40), (132, 32), (86, 72), (0, 82), (-84, 70), (-130, 34), (-150, -12)]
CLUB_BROW = [(-172, -108), (-60, -116), (90, -116), (180, -126), (194, -100), (178, -52), (120, -64), (0, -68), (-120, -62), (-168, -46)]
OFF = 196

def catmull(pts, n=10):
    P = pts + pts[:3]
    out = []
    for i in range(len(pts)):
        p0, p1, p2, p3 = P[i], P[i+1], P[i+2], P[i+3]
        for k in range(n):
            t = k/n; t2, t3 = t*t, t*t*t
            out.append(tuple(0.5*((2*p1[j]) + (-p0[j] + p2[j])*t + (2*p0[j] - 5*p1[j] + 4*p2[j] - p3[j])*t2 + (-p0[j] + 3*p1[j] - 3*p2[j] + p3[j])*t3) for j in (0, 1)))
    return out

def rim(pts, mirror):
    return [((-(x) - OFF) if mirror else (x + OFF), y) for x, y in catmull(pts)]

def to_xz(poly_pts):
    return [(x*S, -y*S) for x, y in poly_pts]

def curve_from_polygon(name, poly, extrude, bevel, index):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
    cu.extrude = extrude; cu.bevel_depth = bevel; cu.bevel_resolution = 3
    rings = [list(poly.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in poly.interiors]
    for ring in rings:
        sp = cu.splines.new('POLY'); sp.points.add(len(ring) - 1)
        for i, (x, y) in enumerate(ring): sp.points[i].co = (x, y, 0, 1)
        sp.use_cyclic_u = True
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    ob.rotation_euler = (math.radians(90), 0, 0)
    ob.pass_index = index
    return ob

def build_glasses(style='wayfarer', camera=True, chunky=1.0):
    outs = [Polygon(to_xz(rim(WAY_OUT if style == 'wayfarer' else CLUB_BROW, m))) for m in (False, True)]
    ins = [Polygon(to_xz(rim(WAY_IN, m))) for m in (False, True)]
    bridge = Polygon(to_xz([(-40, -106), (40, -106), (34, -62), (0, -70), (-34, -62)]))
    frame = unary_union(outs + [bridge])
    if style == 'wayfarer':
        for i in ins: frame = frame.difference(i)
    else:
        for i in ins: frame = frame.difference(i)
    frames = [frame] if frame.geom_type == 'Polygon' else list(frame.geoms)
    obs = []
    for k, f in enumerate(frames):
        obs.append(curve_from_polygon(f'frame{k}', f, 0.035*chunky, 0.012*chunky, 1))
    if style == 'clubmaster':
        # thin wire rims under the brow
        for i in ins:
            ring = i.buffer(0.018).difference(i.buffer(0.004))
            obs.append(curve_from_polygon('wire', ring, 0.008, 0.004, 6))
    for k, i in enumerate(ins):
        l = curve_from_polygon(f'lens{k}', i.buffer(0.004), 0.006, 0.0, 2)
        l.location.y = 0.0
        obs.append(l)
    # temples: side profile in the YZ plane
    prof = [(0.00, 0.07), (0.05, 0.075), (1.10, 0.035), (1.30, 0.0), (1.45, -0.22), (1.42, -0.25), (1.26, -0.03), (1.08, 0.0), (0.05, 0.005), (0.0, 0.0)]
    for side in (-1, 1):
        cu = bpy.data.curves.new('temple', 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'
        cu.extrude = 0.02; cu.bevel_depth = 0.008; cu.bevel_resolution = 2
        sp = cu.splines.new('POLY'); pts = catmull(prof, 6); sp.points.add(len(pts) - 1)
        for i, (a, b) in enumerate(pts): sp.points[i].co = (a, b, 0, 1)
        sp.use_cyclic_u = True
        ob = bpy.data.objects.new('temple', cu); bpy.context.collection.objects.link(ob)
        ob.rotation_euler = (math.radians(90), 0, math.radians(90))
        hx = side*((OFF + 186)*S)
        ob.location = (hx - side*0.02, 0.03, 0.36)
        ob.pass_index = 3
        obs.append(ob)
    cam_pos = ((OFF + 170)*S, -0.045, 100*S)
    if camera:
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.034, depth=0.012, location=(cam_pos[0], -0.040, cam_pos[2]), rotation=(math.radians(90), 0, 0))
        bpy.context.active_object.pass_index = 4
        bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=0.021, depth=0.014, location=(cam_pos[0], -0.043, cam_pos[2]), rotation=(math.radians(90), 0, 0))
        bpy.context.active_object.pass_index = 7
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=0.014, depth=0.01, location=(-cam_pos[0], -0.040, cam_pos[2]), rotation=(math.radians(90), 0, 0))
    bpy.context.active_object.pass_index = 5
    return obs

def setup_render(path, res=2160, cam_loc=(5.3, -4.1, 2.3), target=(0.05, 0.62, -0.1), lens=72):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.samples = 1
    sc.cycles.use_denoising = False
    sc.cycles.filter_width = 0.01
    sc.cycles.max_bounces = 0
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.film_transparent = True
    vl = sc.view_layers[0]
    vl.use_pass_z = True; vl.use_pass_normal = True; vl.use_pass_object_index = True
    sc.render.image_settings.media_type = 'MULTI_LAYER_IMAGE'
    sc.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
    sc.render.image_settings.color_depth = '32'
    sc.render.filepath = path
    cd = bpy.data.cameras.new('cam'); cd.lens = lens
    co = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(co)
    co.location = cam_loc
    d = Vector(target) - Vector(cam_loc)
    co.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    sc.camera = co
    return co

if __name__ == '__main__':
    out = sys.argv[sys.argv.index('--') + 1] if '--' in sys.argv else ROOT + '/shared/r3d/test.exr'
    bpy.ops.wm.read_factory_settings(use_empty=True)
    build_glasses('wayfarer')
    setup_render(out)
    bpy.ops.render.render(write_still=True)
    print('rendered', out)

# ---------------- Spark (our original guide) ----------------
def build_spark(r=0.14):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=48, ring_count=24, location=(0, 0, 0))
    body = bpy.context.active_object; body.name = 'spark'; body.pass_index = 9
    bpy.ops.object.shade_smooth()
    parts = [body]
    for s in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r*0.13, segments=16, ring_count=8, location=(s*r*0.33, -r*0.93, r*0.05))
        e = bpy.context.active_object; e.scale = (0.75, 0.5, 1.2); e.pass_index = 10; e.parent = body
        parts.append(e)
    # four-point star tuft on a short stalk
    star = [(0, 0.42), (0.09, 0.09), (0.42, 0), (0.09, -0.09), (0, -0.42), (-0.09, -0.09), (-0.42, 0), (-0.09, 0.09)]
    cu = bpy.data.curves.new('star', 'CURVE'); cu.dimensions = '2D'; cu.fill_mode = 'BOTH'; cu.extrude = 0.025*r/0.14; cu.bevel_depth = 0.01
    sp = cu.splines.new('POLY'); sp.points.add(len(star) - 1)
    for i, (a, b) in enumerate(star): sp.points[i].co = (a*r, b*r, 0, 1)
    sp.use_cyclic_u = True
    so = bpy.data.objects.new('star', cu); bpy.context.collection.objects.link(so)
    so.rotation_euler = (math.radians(90), 0, 0); so.location = (r*0.1, 0, r*1.55); so.pass_index = 11; so.parent = body
    bpy.ops.mesh.primitive_cylinder_add(radius=r*0.035, depth=r*0.5, location=(r*0.05, 0, r*1.15))
    st = bpy.context.active_object; st.pass_index = 10; st.parent = body; st.rotation_euler = (0, math.radians(8), 0)
    parts += [so, st]
    # smile: a small bevelled arc on the sphere surface
    cm = bpy.data.curves.new('mouth', 'CURVE'); cm.dimensions = '3D'; cm.bevel_depth = r*0.028; cm.bevel_resolution = 2
    sp = cm.splines.new('POLY'); n = 9; sp.points.add(n - 1)
    for i in range(n):
        a = math.radians(-140 + 100*i/(n - 1))
        x = r*0.16*math.cos(a); z = -r*0.16 + r*0.10*math.sin(a)
        y = -math.sqrt(max(r*r - x*x - z*z, 0))*1.005
        sp.points[i].co = (x, y, z, 1)
    mo = bpy.data.objects.new('mouth', cm); bpy.context.collection.objects.link(mo); mo.pass_index = 10; mo.parent = body
    return body

def key(ob, frame, loc=None, scale=None, rot=None):
    if loc is not None: ob.location = loc; ob.keyframe_insert('location', frame=frame)
    if scale is not None: ob.scale = scale if hasattr(scale, '__len__') else (scale, scale, scale); ob.keyframe_insert('scale', frame=frame)
    if rot is not None: ob.rotation_euler = rot; ob.keyframe_insert('rotation_euler', frame=frame)

def tracked_camera(target, lens=72):
    cd = bpy.data.cameras.new('cam'); cd.lens = lens
    co = bpy.data.objects.new('cam', cd); bpy.context.collection.objects.link(co)
    em = bpy.data.objects.new('target', None); bpy.context.collection.objects.link(em); em.location = target
    c = co.constraints.new('TRACK_TO'); c.target = em; c.track_axis = 'TRACK_NEGATIVE_Z'; c.up_axis = 'UP_Y'
    bpy.context.scene.camera = co
    return co, em

def render_setup(res=2160):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.samples = 1; sc.cycles.use_denoising = False
    sc.cycles.filter_width = 0.01; sc.cycles.max_bounces = 0
    sc.render.resolution_x = sc.render.resolution_y = res; sc.render.film_transparent = True
    sc.render.fps = 24
    vl = sc.view_layers[0]; vl.use_pass_z = True; vl.use_pass_normal = True; vl.use_pass_object_index = True
    sc.render.image_settings.media_type = 'MULTI_LAYER_IMAGE'
    sc.render.image_settings.file_format = 'OPEN_EXR_MULTILAYER'
    sc.render.image_settings.color_depth = '16'

def project(ob_or_co, cam):
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    co = ob_or_co.matrix_world.translation if hasattr(ob_or_co, 'matrix_world') else Vector(ob_or_co)
    v = world_to_camera_view(sc, cam, co)
    return [v.x, 1 - v.y, v.z]

def build_charm():
    """Muse Charm: a small keychain device with a ~2-inch screen (shape simplified; no mascot on screen)."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, 0))
    b = bpy.context.active_object; b.scale = (0.62, 0.16, 0.72); b.pass_index = 13
    bev = b.modifiers.new('bev', 'BEVEL'); bev.width = 0.14; bev.segments = 8
    bpy.ops.object.shade_smooth()
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, -0.082, 0.02))
    s_ = bpy.context.active_object; s_.scale = (0.5, 0.01, 0.56); s_.pass_index = 12
    bev = s_.modifiers.new('bev', 'BEVEL'); bev.width = 0.08; bev.segments = 6
    s_.parent = b
    bpy.ops.mesh.primitive_torus_add(major_radius=0.1, minor_radius=0.022, location=(0, 0, 0.47), rotation=(math.radians(90), 0, 0))
    r = bpy.context.active_object; r.pass_index = 6; r.parent = b
    # lanyard strap loop
    cu = bpy.data.curves.new('strap', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 0.028; cu.bevel_resolution = 2
    sp = cu.splines.new('POLY'); pts = [(0, 0, 0.52), (-0.18, 0.02, 0.9), (-0.1, 0.04, 1.4), (0.1, 0.04, 1.4), (0.18, 0.02, 0.9), (0, 0, 0.52)]
    pts = catmull([(p[0], p[2]) for p in pts[:-1]], 8)
    sp.points.add(len(pts) - 1)
    for i, (x, z) in enumerate(pts): sp.points[i].co = (x, 0.02, z, 1)
    sp.use_cyclic_u = True
    st = bpy.data.objects.new('strap', cu); bpy.context.collection.objects.link(st); st.pass_index = 14; st.parent = b
    return b
