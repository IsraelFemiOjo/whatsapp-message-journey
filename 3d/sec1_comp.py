"""Section 1 compositor: 0 to 6 s."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, os, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d')
from sjcomp import *
from chatui import screen
from PIL import Image, ImageDraw, ImageFilter

R3 = sys.argv[3] if len(sys.argv) > 3 else ROOT + '/3d/r3d/s1'
J = json.load(open(f'{R3}/anchors_1_145.json'))
AN = J['anchors']; P_START = np.array(J['P_START']); ANT = np.array(J['ANT']); LIGHTS = np.array(J['lights'])
PH0 = np.array((0, 0, 20.0))
TEXT = 'Hello from Lagos!'
M1 = {1: ('#141824', '#10131D', '#0C0F17', '#080A10'), 2: ('#1E212B', '#191C24', '#14161D', '#0E1015'),
      12: ('#232C40', '#1C2335', '#161C2B', '#0F1420'), 13: ('#5E6878', '#4A5362', '#39404D', '#262B34'),
      14: ('#3A3F4B', '#2E323C', '#23262E', '#17191F'), 20: ('#3A3F4E', '#2A2E3A', '#1D2029', '#111318'),
      21: ('#0B141A',)*4, 22: ('#4A5060',)*4, 30: ('#9AA3B5', '#7C8597', '#5F6778', '#3F4552'),
      31: ('#D8DDE6', '#B9BFCB', '#969CA8', '#6A6F7A'), 32: ('#C9CED8', '#A9AEB9', '#878C97', '#5E626B')}

def near(f):
    ks = sorted(int(k) for k in AN); return str(min(ks, key=lambda k: abs(k - f)))

def homography(Q):
    src = [(0, 0), (1, 0), (1, 1), (0, 1)]
    Mx = []
    for (u, v), (x, y) in zip(src, Q):
        Mx.append([u, v, 1, 0, 0, 0, -x*u, -x*v]); Mx.append([0, 0, 0, u, v, 1, -y*u, -y*v])
    h = np.linalg.solve(np.array(Mx, float), np.array([c for p in Q for c in p], float))
    Hm = np.append(h, 1).reshape(3, 3)
    def f(u, v):
        p = Hm @ np.array([u, v, 1.0]); return p[:2]/p[2]
    return f

def elapsed(t):
    if t < 0.25: return 0.0
    return 0.004*seg(t, 0.25, 2.4) + 0.001*seg(t, 2.4, 5.9)

def render(fi, W=2160):
    H = W; S = W/1080
    t = fi/24; f3 = fi - fi % 2 + 1; key = near(f3); a = AN[key]; tt = math.floor(t*12)/12
    P = load(f'{R3}/{int(key):04d}.exr')
    if P['I'].shape[0] != H:
        from PIL import Image as _I
        def rs(v): return np.array(_I.fromarray(v.astype(np.float32)).resize((W, H), _I.NEAREST))
        P = {k: (rs(v) if v.ndim == 2 else np.stack([rs(v[..., c]) for c in range(v.shape[2])], -1)) for k, v in P.items()}
        P['I'] = P['I'].astype(np.int16)
    proj = projector(a['cam'], W, H)
    # ---- sky ----
    bg = gradient_bg(H, W, '#0A0E20', '#2C2140', seed=31)
    rng = np.random.default_rng(3)
    st = Image.new('L', (W, H), 0); ds = ImageDraw.Draw(st)
    for k in range(260):
        x, y = rng.uniform(0, W), rng.uniform(0, H*0.55); r = rng.uniform(0.5, 1.5)*S
        ds.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(40, 160)))
    bg += (np.array(st).astype(np.float32)/255)[..., None]*200
    img = stylize_dark(P, bg, light=(0.35, -0.55, 0.75), fog_k=260.0, fog_col='#1E1A30', seabed_id=-1, mats=M1,
                       hard_ids=(20, 22, 30, 31, 32), ink='#AFC3DC', ink_k=0.55)
    img = windows(img, P, ids=(12,), seed=5)
    # ---- street lights and the tower's red light ----
    L = np.zeros((H, W, 3), np.float32)
    pts, z = proj(LIGHTS)
    ok = (z > 0.5) & (pts[:, 0] > -50) & (pts[:, 0] < W + 50) & (pts[:, 1] > -50) & (pts[:, 1] < H + 50)
    f_ = a['cam']['lens']/a['cam']['sensor']
    gl = [(x, y, 1.0, min(1, 60/zz)) for (x, y), zz in zip(pts[ok], z[ok])]
    rad = np.clip(0.7*f_*W/np.maximum(z[ok], 1), 1.5*S, 30*S)
    Lp = Image.new('RGB', (W, H)); dl = ImageDraw.Draw(Lp)
    for (x, y), r, zz in zip(pts[ok], rad, z[ok]):
        c = tuple(int(v*min(1, 90/zz)) for v in (255, 186, 110)); dl.ellipse([x - r, y - r, x + r, y + r], fill=c)
    L += np.array(Lp.filter(ImageFilter.GaussianBlur(3*S))).astype(np.float32)*0.9
    tlp, tz = proj([ANT + np.array([-(ANT[0] - 40), 0, 0]) * 0 + np.array([40 - ANT[0], 160 - ANT[1], 39.1 - ANT[2]])])
    if tz[0] > 0 and (int(t*2) % 2 == 0):
        L += glow_layer(H, W, [(tlp[0][0], tlp[0][1], 1, 1)], '#FF4A3A', max(6*S, 5*f_*W/tz[0]), 1.0)
    img = img + L
    # ---- phone screen ----
    Q = [(q[0]*W, q[1]*H) for q in a['screen']]
    Hf = homography(Q)
    sent = t >= 0.42
    ui, info = screen(typed=TEXT, sent=sent, ticks=0, cursor=(not sent) and (int(t*2) % 2 == 0), press=1.0 if 0.25 <= t < 0.42 else 0.0)
    uiw, uih = ui.size
    src = [(0, 0), (uiw, 0), (uiw, uih), (0, uih)]
    Mx = []
    for (x, y), (u, v) in zip(Q, src):
        Mx.append([x, y, 1, 0, 0, 0, -u*x, -u*y]); Mx.append([0, 0, 0, x, y, 1, -v*x, -v*y])
    co = np.linalg.solve(np.array(Mx, float), np.array([c for p in src for c in p], float))
    warp = np.array(ui.transform((W, H), Image.PERSPECTIVE, tuple(co), Image.BICUBIC)).astype(np.float32)
    scr = P['I'] == 21
    img[scr] = warp[scr]*1.05
    # glass sheen
    yy, xx = np.mgrid[0:H, 0:W]
    sheen = scr & (np.abs((xx - Q[0][0]) + (yy - Q[0][1])*0.55 - 0.42*((Q[2][0] - Q[0][0]) + (Q[2][1] - Q[0][1])*0.55)) < 70*S*abs(Q[1][0] - Q[0][0])/620/S*1.0 + 1)
    img[sheen] = img[sheen]*0.93 + 255*0.07
    # ---- rack focus: phone sharp, city soft; pull focus to the city as we leave the phone ----
    zph = np.median(P['Z'][scr]) if scr.any() else 0.3
    strength = 1.0*(1 - ease(seg(t, 2.3, 3.2)))
    img = dof(img, P['Z'], P['I'], zph, strength, S)
    # ---- radio rings: expanding shells drawn as three great circles each ----
    O3 = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ring_ts = [2.35 + 0.3*k for k in range(8)]
    ang = np.linspace(0, 2*np.pi, 160)
    for k, t0 in enumerate(ring_ts):
        if t < t0: continue
        r = 1.2*(t - t0) + 38*(t - t0)**2
        if r > 170: continue
        al = 200*(1 - r/170)**1.2
        for plane in range(3):
            if plane == 0: circ = np.c_[np.cos(ang)*r, np.sin(ang)*r, np.zeros_like(ang)]
            elif plane == 1: circ = np.c_[np.cos(ang)*r, np.zeros_like(ang), np.sin(ang)*r]
            else: circ = np.c_[np.zeros_like(ang), np.cos(ang)*r, np.sin(ang)*r]
            pp, zz = proj(circ + PH0)
            segpts = []
            for (x, y), zv in zip(pp, zz):
                if zv > 0.02 and -W < x < 2*W and -H < y < 2*H: segpts.append((x, y))
                else:
                    polyline(O3, segpts, '#8FE3FF', 1.6*S, al*(0.9 if plane == 0 else 0.45)); segpts = []
            polyline(O3, segpts, '#8FE3FF', 1.6*S, al*(0.9 if plane == 0 else 0.45))
    O3b = O3.filter(ImageFilter.GaussianBlur(3*S))
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    im.alpha_composite(O3b); im.alpha_composite(O3)
    img = np.array(im)[..., :3].astype(np.float32)
    # ---- the message: a copy lifts off, scrambles, and becomes the pulse ----
    O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
    C = lambda c, al=255: tuple(int(v) for v in hexrgb(c)) + (int(al),)
    tu, tv, th, tw = info['text']
    p0 = Hf(tu, tv); p1 = Hf(tu, tv + th); scale = abs(p1[1] - p0[1])/th/2400 if abs(p1[1] - p0[1]) > 0 else 1
    txt_px = np.linalg.norm(Hf(tu, tv + th) - Hf(tu, tv))
    if 0.9 <= t < 2.45:
        lift = ease(seg(t, 0.9, 1.3))
        k = int(len(TEXT)*ease(seg(t, 1.25, 1.95)))
        s_ = scramble(TEXT, k, int(tt*12))
        origin = Hf(tu, tv - 0.012*lift)
        col = '#FFFFFF' if k < len(TEXT) else '#FFD58A'
        collapse = ease(seg(t, 2.05, 2.4))
        fsz = max(4, txt_px*(1.05 + 0.1*lift)*(1 - 0.85*collapse))
        bx, by = Hf(*info['bubble'])
        ox = origin[0] + (bx - origin[0] - fsz*len(TEXT)*0.26)*collapse*0.0
        tx = origin[0]*(1 - collapse) + (bx - fsz*len(TEXT)*0.27)*collapse
        ty = origin[1] - 2.3*txt_px*lift
        fade_text(d, (tx, ty), s_, font(MONO_M, fsz), col, (0.35 + 0.65*lift)*(1 - collapse))
    # label: plain, one at a time
    fade_text(d, (48*S, 150*S), 'What happens', font(SERIF_I, 64*S), '#FFFFFF', 1 - seg(t, 0.85, 1.1))
    fade_text(d, (48*S, 214*S), 'after you hit send.', font(SERIF_I, 64*S), '#FFFFFF', 1 - seg(t, 0.85, 1.1))
    fade_text(d, (48*S, 880*S), 'Scrambled on your phone first.', font(SERIF_I, 44*S), '#FFFFFF', inout(t, 1.2, 2.5))
    fade_text(d, (50*S, 940*S), 'Not even WhatsApp can read it.', font(MONO, 14*S), '#CFEAF5', inout(t, 1.35, 2.5))
    fade_text(d, (48*S, 880*S), 'Radio waves to the nearest tower.', font(SERIF_I, 44*S), '#FFFFFF', inout(t, 2.9, 4.6))
    # tap rings on the send button
    if 0.25 <= t < 0.9:
        sx, sy = Hf(*info['send'])
        for j in range(2):
            rr = (30 + 60*seg(t, 0.25 + 0.1*j, 0.85))*S
            al = 200*(1 - seg(t, 0.25 + 0.1*j, 0.85))
            d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], outline=C('#BFFFF0', al), width=int(2*S))
    header(d, W, S, C, '01 / 08' if t < 2.5 else '02 / 08', 'LAGOS  →  LONDON' if t < 2.5 else 'RADIO', f'{"≈ " if t >= 0.25 else ""}{elapsed(t):.3f} s')
    cur = 0.0 if t < 2.5 else seg(t, 2.5, 5.9)
    kx, ky = route_strip(d, W, H, S, cur, C)
    # ---- the pulse and its trail ----
    g = np.zeros((H, W, 3), np.float32)
    if t >= 2.05:
        born = ease(seg(t, 2.05, 2.45))
        pp, zz = proj([a_ for a_ in [np.array(AN[key]['pulse'])]] and [P_START + (ANT - P_START)*0])
        px_, py_ = a['pulse'][0]*W, a['pulse'][1]*H
        if t >= 2.5:
            u = seg(t, 2.5, 5.85)**1.6
            us = np.linspace(max(0, u - 0.05), u, 40)
            trail, tz = proj(P_START[None] + (ANT - P_START)[None]*us[:, None])
            g += glow_layer(H, W, [(x, y, 1.0, 0.2 + 0.8*(i/39)**2) for i, (x, y) in enumerate(trail) if tz[i] > 0.02], GOLD, 7*S, 1.0)
        if a['pulse'][2] > 0.01:
            g += glow_layer(H, W, [(px_, py_, 1, 1)], GOLD, 55*S*born, 1.2)
            g += glow_layer(H, W, [(px_, py_, 1, 1)], '#FFF4D8', 12*S*born, 2.4)
    # impact at the antenna, then the panel fills the frame
    if 5.8 <= t < 6.05:
        k = seg(t, 5.8, 5.95)*(1 - seg(t, 5.95, 6.05))
        g += glow_layer(H, W, [(W/2, H/2, 1, 1)], GOLD, 300*S, 1.5*k)
    img = img + g
    img = vignette(img, 0.55)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    ImageDraw.Draw(O).ellipse([kx - 3.5*S, ky - 3.5*S, kx + 3.5*S, ky + 3.5*S], fill=C('#FFF4D8'))
    im = halo_composite(im, O, S)
    return im.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    out = ROOT + '/3d/fr/s1'; os.makedirs(out, exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'{out}/{fi:04d}.png')
