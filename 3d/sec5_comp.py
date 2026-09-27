"""Section 5 compositor: 18.6 to 28.5 s. Sinking to the Atlantic floor, along the cable, into the cable."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, os, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d')
from sjcomp import *
from PIL import Image, ImageDraw, ImageFilter

R3 = sys.argv[3] if len(sys.argv) > 3 else ROOT + '/3d/r3d/s5'
J = json.load(open(f'{R3}/anchors_1_239.json')); AN = J['anchors']; PTS = np.array(J['pts']); CUM = np.array(J['cum']); REP_S = J['rep_s']
def near(f):
    ks = sorted(int(k) for k in AN); return str(min(ks, key=lambda k: abs(k - f)))
def at_s(s):
    i = int(np.clip(np.searchsorted(CUM, s) - 1, 0, len(PTS) - 2)); f = (s - CUM[i])/(CUM[i + 1] - CUM[i] + 1e-9)
    return PTS[i] + (PTS[i + 1] - PTS[i])*f

def cross_section(W, H, S, cx, cy, r, alpha):
    """a cable cut open: jacket, steel wires, copper, the tube with its fibers"""
    L = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    A = lambda c, a=255: tuple(int(v) for v in hexrgb(c)) + (int(a*alpha),)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=A('#11151D'), outline=A('#9FD9EC'), width=max(1, int(2*S)))
    r2 = r*0.78
    d.ellipse([cx - r2, cy - r2, cx + r2, cy + r2], fill=A('#1F2633'))
    n = 22
    for k in range(n):   # armouring wires
        a = 2*math.pi*k/n; rw = r*0.085; x, y = cx + r*0.66*math.cos(a), cy + r*0.66*math.sin(a)
        d.ellipse([x - rw, y - rw, x + rw, y + rw], fill=A('#8E97A6'), outline=A('#C9D2DE'), width=max(1, int(1*S)))
    r3 = r*0.5
    d.ellipse([cx - r3, cy - r3, cx + r3, cy + r3], fill=A('#B8743A'))           # copper conductor
    r4 = r*0.36
    d.ellipse([cx - r4, cy - r4, cx + r4, cy + r4], fill=A('#0D1622'), outline=A('#D9E6F2'), width=max(1, int(1.2*S)))
    for k in range(8):   # fiber pairs
        a = 2*math.pi*k/8 + 0.2; rf = r*0.05; x, y = cx + r*0.2*math.cos(a), cy + r*0.2*math.sin(a)
        d.ellipse([x - rf, y - rf, x + rf, y + rf], fill=A('#BFEFFF'))
    rf = r*0.06
    d.ellipse([cx - rf, cy - rf, cx + rf, cy + rf], fill=A('#FFE3A3'))
    return L

def render(fi, W=2160):
    H = W; S = W/1080
    t = 18.6 + fi/24
    key = near(fi + 1 - (fi % 2)); a = AN[key]
    P = load(f'{R3}/{int(key):04d}.exr')
    if P['I'].shape[0] != H:
        def rs(v): return np.array(Image.fromarray(v.astype(np.float32)).resize((W, H), Image.NEAREST))
        P = {k: (rs(v) if v.ndim == 2 else np.stack([rs(v[..., c]) for c in range(v.shape[2])], -1)) for k, v in P.items()}
        P['I'] = P['I'].astype(np.int16)
    proj = projector(a['cam'], W, H)
    sinkk = ease(seg(t, 18.6, 20.6))
    top = hexrgb('#0F2A4C')*(1 - sinkk) + hexrgb('#0F2A4C')*sinkk
    bg = gradient_bg(H, W, '#123560' if t < 19.0 else '#0F2A4C', '#02050B', seed=7)
    bg += god_rays(H, W, 2, 0.24)[..., None]*hexrgb('#7FC4E8')[None, None]*(0.6 + 0.4*sinkk)
    px_, py_ = a['pulse'][0]*W, a['pulse'][1]*H
    rp = [(r[0]*W, r[1]*H, r[2]) for r in a['reps']]
    img = stylize_dark(P, bg, fog_k=22.0, pools=[(px_, py_, 170*S, GOLD, 0.55)] + [(x, y, 90*S, CYAN, 0.25) for x, y, z in rp if z > 0])
    # glow along the cable ahead (cyan) and the gold trail behind the pulse
    s_now = a['s']
    ss = np.linspace(max(0, s_now - 14), s_now + 40, 300)
    cp = np.array([at_s(s) for s in ss]); cpx, cz = proj(cp)
    ahead = [(x, y, 0.6, 0.3) for (x, y), s, z in zip(cpx, ss, cz) if s > s_now and z > 0.02]
    behind = [(x, y, 1.0, 0.25 + 0.75*((s - s_now + 14)/14)**2) for (x, y), s, z in zip(cpx, ss, cz) if s <= s_now and z > 0.02]
    g = glow_layer(H, W, ahead, CYAN, 6*S, 0.5) + glow_layer(H, W, behind, GOLD, 9*S, 1.1)
    g += glow_layer(H, W, [(px_, py_, 1, 1)], GOLD, 60*S, 1.3) + glow_layer(H, W, [(px_, py_, 1, 1)], '#FFF4D8', 16*S, 2.2)
    # repeaters: a status band, flaring as the pulse passes through
    for (x, y, z), rs_ in zip(rp, REP_S):
        if z <= 0: continue
        flare = math.exp(-((s_now - rs_)/0.9)**2)
        g += glow_layer(H, W, [(x, y - 4*S, 1, 1)], CYAN, 22*S, 0.9 + 2.5*flare)
    img = img + g
    snow = marine_snow(H, W, 900, 5, t=(t - 18.6)*(-60 if t < 20.6 else -8))
    img = img + snow[..., None]*hexrgb('#BFE6F5')[None, None]*0.55
    img = vignette(img, 0.6)
    yb = np.linspace(0, 1, H)[:, None, None]
    img = img*(1 - 0.55*np.clip((yb - 0.86)/0.14, 0, 1))
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    # the cutaway: the cable opens up at the pulse and we go into one fiber
    cut = ease(seg(t, 26.9, 27.6))
    if cut > 0:
        r = (60 + 900*ease(seg(t, 27.2, 28.35))**2)*S
        im.alpha_composite(cross_section(W, H, S, px_, py_, r, cut*(1 - seg(t, 28.2, 28.45))))
    O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
    C = lambda c, al=255: tuple(int(v) for v in hexrgb(c)) + (int(al),)
    # depth ruler: we sink to the average depth of the Atlantic
    x0 = W - 40*S; y0, y1 = 150*S, 560*S
    ra = seg(t, 18.7, 19.2)*(1 - seg(t, 26.6, 27.0))
    d.line([(x0, y0), (x0, y1)], fill=C('#CFEAF5', 110*ra), width=int(1*S))
    for k in range(0, 5001, 250):
        yy = y0 + (y1 - y0)*k/5000; big = k % 1000 == 0
        d.line([(x0 - (10 if big else 5)*S, yy), (x0, yy)], fill=C('#CFEAF5', (150 if big else 80)*ra), width=int(1*S))
        if big: d.text((x0 - 14*S, yy), f'{k:,} m', font=font(MONO, 11*S), fill=C('#CFEAF5', 150*ra), anchor='rm')
    depth = 3646*ease(seg(t, 18.6, 20.8))
    ym = y0 + (y1 - y0)*depth/5000
    d.polygon([(x0 + 3*S, ym), (x0 + 13*S, ym - 6*S), (x0 + 13*S, ym + 6*S)], fill=C(GOLD, 255*ra))
    d.text((x0 - 62*S, ym), f'{int(depth):,} m', font=font(MONO_M, 12*S), fill=C(GOLD, 230*ra), anchor='rm')
    # one idea at a time
    fade_text(d, (46*S, 92*S), 'Under the Atlantic', font(SERIF_I, 74*S), '#FFFFFF', inout(t, 20.6, 23.3))
    fade_text(d, (48*S, 186*S), 'On the ocean floor, thousands of meters down.', font(SERIF, 25*S), '#D8EDF6', inout(t, 20.8, 23.3))
    def callout(ax, ay, tx, ty, l1, l2, al):
        d.ellipse([ax - 4*S, ay - 4*S, ax + 4*S, ay + 4*S], outline=C('#FFFFFF', 220*al), width=int(1.4*S))
        d.line([(ax, ay), (ax + (tx - 8*S - ax)*0.35, ty + 8*S), (tx - 8*S, ty + 8*S)], fill=C('#FFFFFF', 150*al), width=int(1*S))
        d.text((tx, ty), l1, font=font(MONO_M, 13*S), fill=C(CYAN, 255*al)); d.text((tx, ty + 18*S), l2, font=font(MONO, 13*S), fill=C('#E6F4FA', 210*al))
    ca = inout(t, 23.4, 24.7)
    if ca > 0:
        cx2, cy2 = cpx[min(len(cpx) - 1, np.searchsorted(ss, s_now - 3))]
        callout(cx2 + 6*S, cy2, 330*S, 930*S, 'THE CABLE', 'about as thick as a garden hose', ca)
    ra2 = inout(t, 24.6, 26.0)
    if ra2 > 0 and rp[0][2] > 0:
        callout(rp[0][0] - 6*S, rp[0][1] - 12*S, 520*S, 330*S, 'REPEATER', 'boosts the light every ~70 km', ra2)
    el = 0.032 + 0.035*seg(t, 20.0, 27.0)
    header(d, W, S, C, '06 / 08', 'UNDER THE ATLANTIC', f'≈ {el:.3f} s')
    cur = 4.0 + 0.45*seg(t, 20.0, 28.5)
    kx, ky = route_strip(d, W, H, S, cur, C)
    d.ellipse([kx - 3.5*S, ky - 3.5*S, kx + 3.5*S, ky + 3.5*S], fill=C('#FFF4D8'))
    im = halo_composite(im, O, S, col=(4, 8, 16))
    # the fiber's light fills the frame, carrying us into the server hall
    fill = seg(t, 28.1, 28.5)
    if fill > 0:
        glowim = Image.fromarray(np.clip(glow_layer(H, W, [(W/2, H/2, 1, 1)], GOLD, 500*S*fill + 20*S, 2.2*fill), 0, 255).astype(np.uint8)).convert('RGBA')
        im = Image.fromarray(np.clip(np.array(im)[..., :3].astype(np.float32) + np.array(glowim)[..., :3], 0, 255).astype(np.uint8)).convert('RGBA')
    return im.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    out = ROOT + '/3d/fr/s5'; os.makedirs(out, exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'{out}/{fi:04d}.png')
