"""Section 2 compositor: 6.0 to 11.0 s. Inside the fiber, out into the street cutaway, rise toward the coast."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, os, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d')
from sjcomp import *
from PIL import Image, ImageDraw, ImageFilter

R3 = sys.argv[3] if len(sys.argv) > 3 else ROOT + '/3d/r3d/s2'
J = json.load(open(f'{R3}/anchors_1_121.json')); AN = J['anchors']; FY, FZ = J['fiber']
M2 = {
    1: ('#4A3526', '#3B2A1F', '#2C2018', '#1E1611'), 2: ('#2E313B', '#262932', '#1D2027', '#14161B'),
    3: ('#5A5E6C', '#4A4E5B', '#3A3D48', '#272933'), 6: ('#D9782A', '#B25F1B', '#8A4712', '#57300C'),
    7: ('#9FDDF2', '#86C8E0', '#6AAAC4', '#4D869E'), 8: ('#5E7F8D', '#4C6A77', '#3B5561', '#2A3E47'),
    9: ('#6B6F7A', '#555963', '#40434C', '#2C2E35'), 10: ('#9095A2', '#777C89', '#5D616C', '#3F424A'),
    11: ('#FFEBC0',)*4, 12: ('#1D2638', '#182031', '#131A28', '#0D121C'), 13: ('#F6C51E', '#DDAA14', '#B78B0E', '#7C5E09'),
    14: ('#171D2C', '#141A28', '#111623', '#0C101A'), 15: ('#15151A',)*4, 16: ('#101014',)*4, 17: ('#5E6878', '#4A5362', '#39404D', '#262B34'),
}
def near(f):
    ks = sorted(int(k) for k in AN); return str(min(ks, key=lambda k: abs(k - f)))

def tunnel(W, H, S, t):
    """inside the glass: rings rushing past, light streaks, the pulse just ahead"""
    img = gradient_bg(H, W, '#06101E', '#030710', seed=40)
    L = Image.new('RGB', (W, H)); d = ImageDraw.Draw(L)
    cx, cy = W/2, H/2
    sp = 1.0; v = 26.0
    for i in range(40):
        z = ((i*sp - v*(t - 6.0)) % 40) + 0.35
        r = 420*S/z
        if r < 3*S: continue
        a = min(1, 3/z)*min(1, (40 - z)/6)
        c = tuple(int(x*a) for x in (110, 210, 245))
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=c, width=max(1, int(2.2*S*min(1, 2/z) + 1)))
    rng = np.random.default_rng(8)
    for k in range(70):
        ang = rng.uniform(0, 2*np.pi); z0 = (rng.uniform(0, 30) - v*1.3*(t - 6.0)) % 30 + 0.4
        r0, r1 = 380*S/z0, 380*S/max(z0 - 1.6, 0.3)
        a = min(1, 2.5/z0)
        d.line([(cx + r0*math.cos(ang), cy + r0*math.sin(ang)), (cx + r1*math.cos(ang), cy + r1*math.sin(ang))], fill=tuple(int(x*a) for x in (200, 240, 255)), width=max(1, int(1.5*S)))
    img += np.array(L.filter(ImageFilter.GaussianBlur(1.2*S))).astype(np.float32)
    img += np.array(L.filter(ImageFilter.GaussianBlur(9*S))).astype(np.float32)*0.8
    img += glow_layer(H, W, [(cx, cy, 1, 1)], GOLD, 60*S, 1.3) + glow_layer(H, W, [(cx, cy, 1, 1)], '#FFF4D8', 12*S, 2.4)
    return img

def street(fi, W, H, S, t):
    key = near(fi - fi % 2 + 1); a = AN[key]
    P = load(f'{R3}/{int(key):04d}.exr')
    if P['I'].shape[0] != H:
        def rs(v): return np.array(Image.fromarray(v.astype(np.float32)).resize((W, H), Image.NEAREST))
        P = {k: (rs(v) if v.ndim == 2 else np.stack([rs(v[..., c]) for c in range(v.shape[2])], -1)) for k, v in P.items()}
        P['I'] = P['I'].astype(np.int16)
    proj = projector(a['cam'], W, H)
    I, N = P['I'], P['N']
    bg = gradient_bg(H, W, '#0C1024', '#3A2A3C', seed=9)
    pkx, pky = a['pulse'][0]*W, a['pulse'][1]*H
    lamps = [(l[0]*W, l[1]*H, l[2]) for l in a['lamps']]
    pools = [(pkx, pky, 110*S, GOLD, 0.3)] + [(x, y + 300*S, 240*S, '#FFCF8A', 0.16) for x, y, z in lamps if z > 0 and -300*S < x < W + 300*S]
    img = stylize_dark(P, bg, light=(-0.3, -0.7, 0.65), fog_k=140.0, seabed_id=-1, mats=M2, hard_ids=(6, 10, 13, 3),
                       pools=pools, ink='#E8D9C4', ink_k=0.6)
    # soil strata from true depth below the road (world z)
    if 'P' in P:
        cut = (I == 1) & (N[..., 1] < -0.85)
        zz = P['P'][..., 2]; xw = P['P'][..., 0]
        v = (-zz - 0.14)/3.06 + 0.03*np.sin(xw*0.9) + 0.015*np.sin(xw*2.7 + 1)
        dots = ht_dist(H, W, 9, 20) < 0.22
        gr = cut & (v < 0.14)
        img[gr & dots] = img[gr & dots]*0.4 + hexrgb('#8C7A66')*0.6
        for lo, hi, c in ((0.14, 0.17, '#5A4231'), (0.55, 0.58, '#2A1E16'), (0.8, 0.83, '#5A4231')):
            b = cut & (v > lo) & (v < hi); img[b] = img[b]*0.5 + hexrgb(c)*0.5
    img = windows(img, P, ids=(12,), cell=(1.6, 2.6), seed=9)
    # fiber glow and the pulse
    xs = np.linspace(-70, 70, 700)
    fpts, fz_ = proj(np.c_[xs, np.full_like(xs, FY - 0.03), np.full_like(xs, FZ)])
    xp_now = -18 + 46*seg(t, 6.75, 10.9)**1.15
    ahead = [(x, y, 0.5, 0.3) for (x, y), xx, z in zip(fpts, xs, fz_) if z > 0.05 and xp_now < xx < xp_now + 30]
    behind = [(x, y, 1.0, 0.15 + 0.85*max(0, 1 - (xp_now - xx)/12)**2) for (x, y), xx, z in zip(fpts, xs, fz_) if z > 0.05 and xp_now - 12 < xx <= xp_now]
    g = glow_layer(H, W, ahead, CYAN, 3*S, 0.5) + glow_layer(H, W, behind, GOLD, 3.5*S, 1.1)
    g += glow_layer(H, W, [(pkx, pky, 1, 1)], GOLD, 42*S, 1.0) + glow_layer(H, W, [(pkx, pky, 1, 1)], '#FFF4D8', 9*S, 2.4)
    g += glow_layer(H, W, [(x, y + 6*S, 1, 1) for x, y, z in lamps if z > 0], '#FFD9A0', 28*S, 0.8)
    img = img + g
    zph = float(np.median(P['Z'][np.abs(P['Z'] - P['Z']) == 0][:1])) if False else None
    # focus: soft on the far street while we are right up against the fiber
    k = 1 - ease(seg(t, 6.8, 7.7))
    if k > 0.01:
        img = dof(img, P['Z'], I, 0.3, 0.9*k, S)
    return img, (pkx, pky)

def render(fi, W=2160):
    H = W; S = W/1080
    t = 6.0 + fi/24; tt = math.floor(t*12)/12
    if t < 6.8:
        img = tunnel(W, H, S, t); pk = (W/2, H/2)
    else:
        img, pk = street(fi, W, H, S, t)
    if 6.75 <= t < 7.0:   # the tunnel opens like an iris onto the street
        k = ease(seg(t, 6.75, 7.0))
        tun = tunnel(W, H, S, t); st, pk = street(fi, W, H, S, t)
        yy, xx = np.mgrid[0:H, 0:W]
        m = (np.sqrt((xx - W/2)**2 + (yy - H/2)**2) < k*W*0.8)[..., None]
        img = np.where(m, st, tun)
    if t < 6.12:   # carry the impact flash in from the antenna
        img = img + glow_layer(H, W, [(W/2, H/2, 1, 1)], GOLD, 300*S, 1.5*(1 - seg(t, 6.0, 6.12)))
    img = vignette(img, 0.55)
    yb = np.linspace(0, 1, H)[:, None, None]
    img = img*(1 - 0.45*np.clip((yb - 0.88)/0.12, 0, 1))
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
    C = lambda c, al=255: tuple(int(v) for v in hexrgb(c)) + (int(al),)
    fade_text(d, (48*S, 880*S), 'From the tower into fiber.', font(SERIF_I, 44*S), '#FFFFFF', inout(t, 6.15, 6.95, 0.2, 0.2))
    fade_text(d, (46*S, 820*S), 'Under the road.', font(SERIF_I, 70*S), '#FFFFFF', inout(t, 7.4, 9.1))
    fade_text(d, (48*S, 910*S), 'It travels as light in glass.', font(SERIF, 25*S), '#EFE3D3', inout(t, 7.6, 9.1))
    ca = inout(t, 9.1, 10.2)
    if ca > 0:
        ax, ay = pk[0] + 50*S, pk[1] + 8*S
        d.ellipse([ax - 4*S, ay - 4*S, ax + 4*S, ay + 4*S], outline=C('#FFFFFF', 220*ca), width=int(1.4*S))
        d.line([(ax, ay), (ax + 40*S, ay + 110*S), (ax + 200*S, ay + 110*S)], fill=C('#FFFFFF', 150*ca), width=int(1*S))
        d.text((ax + 48*S, ay + 84*S), 'GLASS FIBER', font=font(MONO_M, 13*S), fill=C(CYAN, 255*ca))
        d.text((ax + 48*S, ay + 116*S), 'about as thin as a hair', font=font(MONO, 13*S), fill=C('#F2E8DA', 220*ca))
    el = 0.005 + 0.004*seg(t, 6.0, 11.0)
    header(d, W, S, C, '02 / 08' if t < 6.9 else '03 / 08', 'RADIO' if t < 6.9 else 'UNDER THE STREET', f'≈ {el:.3f} s')
    cur = 1.0 + seg(t, 6.3, 7.4) + seg(t, 10.2, 11.0)
    kx, ky = route_strip(d, W, H, S, cur, C)
    d.ellipse([kx - 3.5*S, ky - 3.5*S, kx + 3.5*S, ky + 3.5*S], fill=C('#FFF4D8'))
    im = halo_composite(im, O, S, col=(8, 6, 6))
    return im.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    out = ROOT + '/3d/fr/s2'; os.makedirs(out, exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'{out}/{fi:04d}.png')
