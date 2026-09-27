"""v3 frame renderer: plates from the 3D sections on narration time, 2D camera moves, motion transitions, then the motion graphics layer."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import sys, os, math, json, numpy as np
sys.path.insert(0, ROOT + '/3d/v3'); sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
from PIL import Image, ImageFilter
import skia
import sjtl as T, plates, ui, mg

PW = 1620; S0 = 1080/PW
MODS = {}
def mod(sec):
    if sec in MODS: return MODS[sec]
    extra = []
    if sec == 'sec1_comp': extra = [("if 0.25 <= t < 0.9:", "if False:"), ("f3 = fi + 1; key = near(f3)", "f3 = fi + 1; key = near(KEY_OVR if KEY_OVR else f3)"),
                                    ("strength = 1.0*(1 - ease(seg(t, 2.3, 3.2)))", "strength = DOF_OVR if DOF_OVR is not None else 1.0*(1 - ease(seg(t, 2.3, 3.2)))")]
    if sec == 'sec5_comp': extra = [("ra = seg(t, 18.7, 19.2)*(1 - seg(t, 26.6, 27.0))", "ra = 0.0")]
    m = plates.load_section(sec, extra) if sec != 'sec1_comp' else plates.load_section(sec, extra, pre={'KEY_OVR': None, 'DOF_OVR': None})
    if sec == 'sec1_comp': m.screen = ui.sender
    if sec == 'sec7_comp': m.screen_recv = ui.receiver
    if sec == 'sec4_comp':
        m.pulse_u = lambda t: 1.0*min(1, max(0, (t - 14.6)/3.0))**1.1
    MODS[sec] = m
    return m

def frame_index(sec, src): return (src - T.SEC_START[sec])*24

# ---------------- anchors in plate pixels ----------------
def anchors(sec, m, fi, src):
    A = {}
    Wp = PW; Hp = PW; S = Wp/1080
    if sec in ('sec1_comp', 'sec2_comp', 'sec3_comp', 'sec5_comp', 'sec6_comp'):
        key = m.near(m.KEY_OVR if (sec == 'sec1_comp' and m.KEY_OVR) else fi + 1); a = m.AN[key]
        A['pulse'] = (a['pulse'][0]*Wp, a['pulse'][1]*Hp)
        A['vis'] = bool(a['pulse'][2] > 0.01) if sec == 'sec1_comp' else True
        if sec == 'sec1_comp' and src < 2.05: A['vis'] = False
        if sec == 'sec2_comp' and src < 6.8: A['pulse'] = (Wp/2, Hp/2)
        proj = m.projector(a['cam'], Wp, Hp)
        if sec == 'sec1_comp':
            Q = [(q[0]*Wp, q[1]*Hp) for q in a['screen']]; Hf = m.homography(Q)
            _, info = ui.sender()
            A['bubble'] = tuple(Hf(*info['bubble'])); A['send'] = tuple(Hf(*info['send']))
            A['screen'] = Q
            p, z = proj([m.ANT]); A['ant'] = tuple(p[0])
        if sec == 'sec3_comp':
            p, z = proj([(0, 41, 7.5)]); A['station'] = tuple(p[0]) if z[0] > 1 else None
        if sec == 'sec5_comp':
            A['reps'] = [(r[0]*Wp, r[1]*Hp) for r in a['reps'] if r[2] > 0]
        if sec == 'sec6_comp':
            A['led'] = (a['led'][0]*Wp, a['led'][1]*Hp)
    elif sec == 'sec4_comp':
        lat0, lon0, R = m.view(src, S)
        def pt(lon, lat):
            x, y, c = m.ortho(np.array([lat]), np.array([lon]), lat0, lon0, R, Wp/2, Hp/2); return (float(x[0]), float(y[0]))
        plon, plat = m.pulse_ll(src)
        A['pulse'] = pt(plon, plat); A['lagos'] = pt(3.39, 6.45); A['bude'] = pt(*m.BUDE); A['london'] = pt(*m.LONDON); A['R'] = R
    elif sec == 'sec7_comp':
        Q = [(q[0]*Wp, q[1]*Hp) for q in m.A['screen']]; Hf = m.homography(Q)
        _, info = ui.receiver(show=1.0)
        bx, by = Hf(*info['bubble'])
        t = src
        zk = m.ease(m.seg(t, 37.0, 37.9))*(1 - m.seg(t, 40.4, 41.2))
        if zk > 0.001:
            z = 1 + 0.55*zk; fx, fy = Wp/2 + (bx - Wp/2)*zk, Hp/2 + (by - Hp/2)*zk
            w2 = Wp/z; x0 = min(max(0, fx - w2/2), Wp - w2); y0 = min(max(0, fy - w2/2), Hp - w2)
            bx, by = (bx - int(x0))*z, (by - int(y0))*z
        A['bubble'] = (bx, by); A['pulse'] = (bx, by); A['vis'] = False
        if src < 37.05:
            k2 = m.ease(m.seg(src, 35.9, 36.95)); A['pulse'] = (Wp/2 + (bx - Wp/2)*k2, Hp*0.5 + (by - Hp*0.5)*k2); A['vis'] = src > 35.6
    A['src'] = src
    return A

def render_plate(shot, tau):
    sec = shot[1]; m = mod(sec)
    src = T.src_time(shot, tau); spd = abs(T.speed(shot, tau))
    ui.CUR['tau'] = tau
    fi = frame_index(sec, src)
    if sec == 'sec1_comp':
        if shot[0] == 'opening':
            m.KEY_OVR = int(round(81 - 8*mg.seg(tau, 0.0, 1.85))); m.DOF_OVR = 0.12
        else:
            m.KEY_OVR = None; m.DOF_OVR = None
    if spd > 2.2:           # fast: average a few samples across the frame for real motion blur
        n = min(5, int(math.ceil(spd/1.1)))
        offs = np.linspace(-0.5, 0.5, n)*spd*(24/30)
        acc = None
        for o in offs:
            im = np.asarray(m.render(fi + o, W=PW), np.float32)
            acc = im if acc is None else acc + im
        img = acc/n
    elif shot[5] == 'pair' and sec not in ('sec4_comp', 'sec7_comp'):
        f0 = math.floor(fi); w1 = fi - f0
        # pair only when the nearest rendered frames differ
        img = np.asarray(m.render(f0, W=PW), np.float32)
        if w1 > 0.15:
            img = img*(1 - w1) + np.asarray(m.render(f0 + 1, W=PW), np.float32)*w1
    else:
        img = np.asarray(m.render(fi, W=PW), np.float32)
    return img, anchors(sec, m, fi, src), src

# ---------------- 2D camera ----------------
def smoothstep(x): return mg.ease(x)
def cam2d(name, tau, A):
    """zoom, centre (plate px), rotation (rad), shake (px)"""
    z = 1.0; cx, cy = PW/2, PW/2; rot = 0.0; sh = (0.0, 0.0)
    def punch(t0, amt, dur=0.5):
        k = mg.seg(tau, t0, t0 + dur); return amt*math.sin(math.pi*min(1, k*1.6))*(1 - k) if 0 < k < 1 else 0.0
    def shake(t0, amp, dur=0.35):
        k = mg.seg(tau, t0, t0 + dur)
        if not 0 < k < 1: return (0.0, 0.0)
        e = amp*(1 - k)**2; return (e*math.sin(tau*93.0), e*math.cos(tau*71.0))
    if name == 'opening':
        z = 1.0 + 0.1*mg.seg(tau, 0.0, 1.5)
        q = A.get('screen')
        if q:
            sx = sum(p[0] for p in q)/4; sy = sum(p[1] for p in q)/4
            pk = mg.seg(tau, 1.35, 1.86)**2.5
            z += 3.2*pk; cx = lerp(PW/2, sx, min(1, 0.3 + pk)); cy = lerp(PW/2, sy, min(1, 0.3 + pk))
    elif name == 'lagos':
        send = T.wt(0, 'send'); lock = T.wt(2, 'locks')
        # open tight on the thumb and the input bar, ease out as the bubble springs up
        z = 2.3 - 1.15*smoothstep(mg.seg(tau, 2.4, 3.5)) + 0.05*smoothstep(mg.seg(tau, 3.6, 6.6))
        z += punch(send, 0.05) + punch(lock + 0.1, 0.09, 0.6)
        z -= 0.15*smoothstep(mg.seg(tau, 11.3, 12.3))
        b = A.get('bubble', (PW/2, PW/2)); sd = A.get('send', b)
        k0 = 1 - smoothstep(mg.seg(tau, 2.4, 3.4))
        fx = lerp(b[0], sd[0] - 120, k0); fy = lerp(b[1], sd[1] - 60, k0)
        k = 1 - smoothstep(mg.seg(tau, 11.3, 12.0))
        cx = PW/2 + (fx - PW/2)*(0.35 + 0.65*k0)*k; cy = PW/2 + (fy - PW/2)*(0.35 + 0.65*k0)*k
        rot = math.radians(-1.5*math.sin(tau*0.6))*(1 - smoothstep(mg.seg(tau, 11.3, 12.0)))
        s1 = shake(send, 6); s2 = shake(lock + 0.1, 10)
        sh = (s1[0] + s2[0], s1[1] + s2[1])
        # push into the antenna before we go through it
        pk = mg.ein(mg.seg(tau, 13.85, 14.47)) if hasattr(mg, 'ein') else mg.seg(tau, 13.85, 14.47)**3
        if pk > 0:
            p = A.get('pulse', (PW/2, PW/2)); z = max(z, 1.0) + 2.6*pk; cx = lerp(cx, p[0], min(1, pk*2)); cy = lerp(cy, p[1], min(1, pk*2))
    elif name == 'fiber':
        z = 1.0 + 1.3*(1 - mg.eout(mg.seg(tau, 14.44, 14.9)))
        z += 0.04*math.sin(tau*0.9)
        rot = math.radians(4*(1 - mg.eout(mg.seg(tau, 14.44, 15.0))))
    elif name == 'coast':
        z = 1.05 + 0.03*mg.seg(tau, 18.3, 21.0)
    elif name == 'ocean':
        z = 1.0 + 0.6*(1 - mg.eout(mg.seg(tau, 26.1, 26.6))) + punch(T.wt(8, 'boosts'), 0.07)
        sh = shake(T.wt(8, 'boosts'), 9)
        pk = mg.seg(tau, 32.55, 32.8)**3
        if pk > 0:
            p = A.get('pulse', (PW/2, PW/2)); z += 2.2*pk; cx = lerp(cx, p[0], pk); cy = lerp(cy, p[1], pk)
    elif name == 'server':
        z = 1.0 + 0.8*(1 - mg.eout(mg.seg(tau, 32.76, 33.3))) + 0.08*smoothstep(mg.seg(tau, 33.3, 38.6))
        z += punch(T.wt(9, 'one'), 0.04)
        led = A.get('led', (PW/2, PW/2)); k = 0.3*smoothstep(mg.seg(tau, 33.3, 38.6))
        cx = PW/2 + (led[0] - PW/2)*k; cy = PW/2 + (led[1] - PW/2)*k
    elif name == 'london':
        z = 1.0 + 0.25*(1 - mg.eout(mg.seg(tau, 39.3, 39.9)))
        zk = smoothstep(mg.seg(tau, 39.95, 40.55))*(1 - smoothstep(mg.seg(tau, 42.0, 42.9)))
        z += 1.1*zk
        b = A.get('bubble', (PW/2, PW/2))
        cx = PW/2 + (b[0] - PW/2)*zk; cy = PW/2 + (b[1] - PW/2)*zk
        sh = shake(T.wt(10, 'unlocks') + 0.1, 6)
    return z, cx, cy, rot, sh

def lerp(a, b, k): return a + (b - a)*k
mg.ein = lambda x: min(1, max(0, x))**3

def apply_cam(img, z, cx, cy, rot, sh):
    """plate (PW) -> 1080 output, zoom about (cx, cy); returns image and a point mapper"""
    z = max(1.0, z)
    half = PW/(2*z)
    cx = min(max(cx, half), PW - half); cy = min(max(cy, half), PW - half)
    sc = z*S0                       # plate px -> output px
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    pre = 1.0
    if sc < 1.0:
        pre = sc; pil = pil.resize((int(round(PW*pre)), int(round(PW*pre))), Image.LANCZOS)
    rem = sc/pre
    cr, sr = math.cos(rot), math.sin(rot)
    cxp, cyp = cx*pre, cy*pre
    # output (u, v) -> source: s = C + R(-rot)((u,v) - 540 - sh)/rem
    a = cr/rem; b = sr/rem; d = -sr/rem; e = cr/rem
    c0 = cxp - a*(540 + sh[0]) - b*(540 + sh[1]); f0 = cyp - d*(540 + sh[0]) - e*(540 + sh[1])
    out = pil.transform((1080, 1080), Image.AFFINE, (a, b, c0, d, e, f0), Image.BICUBIC)
    def mp(p):
        if p is None: return None
        x, y = p[0]*pre - cxp, p[1]*pre - cyp
        u = (cr*x - sr*y)*rem + 540 + sh[0]; v = (sr*x + cr*y)*rem + 540 + sh[1]
        return (u, v)
    return np.asarray(out, np.float32), mp

def radial_blur(img, k, cx=540, cy=540, n=7, spread=0.18):
    if k <= 0.02: return img
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)); acc = img.copy()
    for i in range(1, n):
        s = 1 + spread*k*i/n
        w2 = int(1080*s); z = pil.resize((w2, w2), Image.BILINEAR)
        ox, oy = int(cx*s - cx), int(cy*s - cy)
        acc += np.asarray(z.crop((ox, oy, ox + 1080, oy + 1080)), np.float32)
    return acc/n
def hblur(img, k, n=9, dist=90):
    if k <= 0.02: return img
    acc = img.copy()
    for i in range(1, n): acc += np.roll(img, int(dist*k*(i/n - 0.5)*2), axis=1)
    return acc/n
def add_glow(img, k, color='#FFE2A0', r=0.7):
    if k <= 0.01: return img
    yy, xx = np.mgrid[0:1080, 0:1080]
    g = np.exp(-(((xx - 540)**2 + (yy - 540)**2)/(2*(1080*r)**2)))[..., None]
    c = np.array([int(color[i:i+2], 16) for i in (1, 3, 5)], np.float32)
    return img*(1 - 0.85*k*g) + c*0.85*k*g + 255*0.25*k

# ---------------- one output frame ----------------
GRADE = {'opening': dict(sat=1.15, contrast=1.04, bloom=0.32, gamma=0.78), 'lagos': dict(sat=1.15, contrast=1.06, bloom=0.12, gamma=0.88),
         'fiber': dict(sat=1.18, contrast=1.05, bloom=0.34, gamma=0.8), 'coast': dict(sat=1.15, contrast=1.04, bloom=0.3, gamma=0.78),
         'map': dict(sat=1.15, contrast=1.04, bloom=0.25, gamma=0.82), 'ocean': dict(sat=1.1, contrast=1.04, bloom=0.3, gamma=0.88),
         'server': dict(sat=1.2, contrast=1.05, bloom=0.35, gamma=0.75), 'london': dict(sat=1.2, contrast=1.04, bloom=0.32, gamma=0.78)}
def shot_image(shot, tau):
    img, A, src = render_plate(shot, tau)
    z, cx, cy, rot, sh = cam2d(shot[0], tau, A)
    out, mp = apply_cam(img, z, cx, cy, rot, sh)
    out = plates.grade(out.astype(np.uint8), **GRADE[shot[0]]).astype(np.float32)
    OA = {k: (mp(v) if isinstance(v, tuple) else ([mp(p) for p in v] if isinstance(v, list) and v and isinstance(v[0], tuple) else v)) for k, v in A.items()}
    return out, OA

def frame(n):
    tau_new = n/T.FPS
    tau = T.WARP(tau_new)
    act = T.active(tau)
    if not act: act = [T.SHOTS[-1]]
    # hard cuts at each transition centre, except the coast to map dissolve
    names = [s[0] for s in act]
    if len(act) > 1:
        if names[:2] == ['coast', 'map']:
            k = mg.ease(mg.seg(tau, 20.45, 21.15))
            a0, A0 = shot_image(act[0], tau); a1, A1 = shot_image(act[1], tau)
            img = a0*(1 - k) + a1*k; A = A1 if k > 0.5 else A0; cur = act[1] if k > 0.5 else act[0]
        else:
            tc = [tr for tr in T.TRANS if act[0][2] <= tr[0] <= act[0][3] and act[1][2] <= tr[0] <= act[1][3]]
            tcc = tc[0][0] if tc else act[1][2]
            cur = act[0] if tau < tcc else act[1]
            img, A = shot_image(cur, tau)
    else:
        cur = act[0]; img, A = shot_image(cur, tau)
    # transition effects around each cut
    for tc, kind, hw in T.TRANS:
        d = tau - tc
        if abs(d) > 0.45: continue
        if kind in ('zoomthrough', 'dive'):
            k = math.exp(-(d/0.12)**2)
            img = radial_blur(img, k, n=8, spread=0.35)
            img = add_glow(img, math.exp(-(d/0.06)**2)*0.9, '#FFE2A0' if kind == 'zoomthrough' else '#9FE8FF')
        elif kind == 'whip':
            k = math.exp(-(d/0.1)**2)
            img = hblur(img, k, n=11, dist=260)
            img = add_glow(img, math.exp(-(d/0.05)**2)*0.35, '#FFFFFF', 0.9)
        elif kind == 'streak':
            img = add_glow(img, math.exp(-(d/0.07)**2)*0.8, '#FFFFFF', 0.8)
    base = np.clip(img, 0, 255).astype(np.uint8)
    # ---- motion graphics ----
    rgba = np.dstack([base, np.full((1080, 1080), 255, np.uint8)])
    surf = skia.Surface(1080, 1080); c = surf.getCanvas()
    c.drawImage(skia.Image.fromarray(rgba), 0, 0)
    import overlay
    overlay.draw(c, tau, cur[0], A, tau_new)
    out = surf.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
    return out

if __name__ == '__main__':
    od = ROOT + '/3d/v3/frames'; os.makedirs(od, exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2]); step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    N = int(T.END_NEW*T.FPS)
    for n in range(a, min(b, N), step):
        p = f'{od}/{n:05d}.png'
        if os.path.exists(p) and os.environ.get('SKIP') == '1': continue
        Image.fromarray(frame(n)).save(p, compress_level=1)
    print('done', a, b)
