"""Section 3 compositor: 11.0 to 14.0 s. The Lagos coast at night from the air."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, os, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d')
from sjcomp import *
from PIL import Image, ImageDraw, ImageFilter

R3 = sys.argv[3] if len(sys.argv) > 3 else ROOT + '/3d/r3d/s3'
J = json.load(open(f'{R3}/anchors_1_73.json')); AN = J['anchors']; PATH = np.array(J['path']); SEG = np.array(J['seglen']); S_ST = J['s_station']
M3 = {1: ('#161A24', '#12151E', '#0E1118', '#0A0C12'), 2: ('#262A34', '#20232C', '#1A1D24', '#13151A'),
      3: ('#3B362F', '#322E28', '#29261F', '#1F1C17'), 5: ('#0C1C30', '#0B192B', '#091526', '#07111F'),
      12: ('#232C40', '#1C2335', '#161C2B', '#0F1420'), 40: ('#5A6272', '#4A5160', '#3A404D', '#2A2E38'),
      41: ('#8A909C',)*4, 42: ('#6A707C',)*4}
def near(f):
    ks = sorted(int(k) for k in AN); return str(min(ks, key=lambda k: abs(k - f)))
def at_s(s):
    i = int(np.clip(np.searchsorted(SEG, s) - 1, 0, len(PATH) - 2)); f = (s - SEG[i])/(SEG[i + 1] - SEG[i] + 1e-9)
    return PATH[i] + (PATH[i + 1] - PATH[i])*f

def render(fi, W=2160):
    H = W; S = W/1080
    t = 11.0 + fi/24
    key = near(fi - fi % 2 + 1); a = AN[key]
    P = load(f'{R3}/{int(key):04d}.exr')
    if P['I'].shape[0] != H:
        def rs(v): return np.array(Image.fromarray(v.astype(np.float32)).resize((W, H), Image.NEAREST))
        P = {k: (rs(v) if v.ndim == 2 else np.stack([rs(v[..., c]) for c in range(v.shape[2])], -1)) for k, v in P.items()}
        P['I'] = P['I'].astype(np.int16)
    proj = projector(a['cam'], W, H)
    bg = gradient_bg(H, W, '#0A0E20', '#2C2140', seed=33)
    img = stylize_dark(P, bg, light=(0.3, -0.5, 0.8), fog_k=2600.0, fog_col='#1A1830', seabed_id=-1, mats=M3,
                       hard_ids=(40, 41), ink='#AFC3DC', ink_k=0.45)
    img = windows(img, P, ids=(12,), cell=(2.6, 3.2), seed=13)
    I = P['I']
    # surf: foam lines rolling in along the shore, wet sand darker
    if 'P' in P:
        X = P['P']; sea = I == 5; beach = I == 3
        dy = -70 - X[..., 1]
        foam = sea & (dy > -2) & (dy < 40) & (np.sin(dy*0.55 + t*3.2 + 0.5*np.sin(X[..., 0]*0.03)) > 0.86)
        fa = np.clip(1 - dy/40, 0, 1)
        img[foam] = img[foam]*(1 - 0.6*fa[foam, None]) + 230*0.6*fa[foam, None]
        wet = beach & (X[..., 1] < -52)
        img[wet] = img[wet]*0.75
    # street lights along the coast road
    xs = np.arange(-2000, 2001, 30.0)
    pts, z = proj(np.c_[xs, np.full_like(xs, 21.0), np.full_like(xs, 7.0)])
    ok = (z > 1) & (pts[:, 0] > -40) & (pts[:, 0] < W + 40) & (pts[:, 1] > -40) & (pts[:, 1] < H + 40)
    f_ = a['cam']['lens']/a['cam']['sensor']
    Lp = Image.new('RGB', (W, H)); dl = ImageDraw.Draw(Lp)
    for (x, y), zz in zip(pts[ok], z[ok]):
        r = float(np.clip(1.2*f_*W/zz, 1.2*S, 14*S)); dl.ellipse([x - r, y - r, x + r, y + r], fill=(255, 186, 110))
    img += np.array(Lp.filter(ImageFilter.GaussianBlur(2.5*S))).astype(np.float32)*0.85
    # the cable: dashed where it is buried, faint under water; gold behind the pulse
    s_now = a['s']
    ss = np.linspace(max(0, s_now - 2500), min(SEG[-1], s_now + 1800), 700)
    cp = np.array([at_s(s) for s in ss]); cpx, cz = proj(cp)
    O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
    C = lambda c, al=255: tuple(int(v) for v in hexrgb(c)) + (int(al),)
    for i in range(0, len(ss) - 1):
        if cz[i] < 1 or cz[i + 1] < 1: continue
        ahead = ss[i] > s_now
        if ahead and (i // 4) % 2: continue
        col = '#8FE3FF' if ahead else '#FFD58A'
        d.line([tuple(cpx[i]), tuple(cpx[i + 1])], fill=C(col, 170 if ahead else 230), width=int((1.4 if ahead else 2.4)*S))
    g = np.zeros((H, W, 3), np.float32)
    behind = [(x, y, 1.0, 0.2 + 0.8*((s - (s_now - 2500))/2500)**2) for (x, y), s, zz in zip(cpx, ss, cz) if s <= s_now and zz > 1]
    g += glow_layer(H, W, behind, GOLD, 5*S, 0.9)
    px_, py_ = a['pulse'][0]*W, a['pulse'][1]*H
    g += glow_layer(H, W, [(px_, py_, 1, 1)], GOLD, 55*S, 1.2) + glow_layer(H, W, [(px_, py_, 1, 1)], '#FFF4D8', 12*S, 2.4)
    img = img + g
    img = vignette(img, 0.55)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    im.alpha_composite(O.filter(ImageFilter.GaussianBlur(2*S))); im.alpha_composite(O)
    O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
    fade_text(d, (46*S, 820*S), 'To the coast.', font(SERIF_I, 64*S), '#FFFFFF', inout(t, 11.15, 12.4))
    fade_text(d, (48*S, 902*S), 'A landing station, where cables meet the sea.', font(SERIF, 25*S), '#E6ECF5', inout(t, 11.3, 12.4))
    st, sz_ = proj([(0, 41, 7.5)])
    ca = inout(t, 12.0, 13.0)
    if ca > 0 and sz_[0] > 1:
        ax, ay = st[0]
        d.ellipse([ax - 4*S, ay - 4*S, ax + 4*S, ay + 4*S], outline=C('#FFFFFF', 220*ca), width=int(1.4*S))
        d.line([(ax, ay), (ax + 60*S, ay - 90*S), (ax + 230*S, ay - 90*S)], fill=C('#FFFFFF', 150*ca), width=int(1*S))
        d.text((ax + 68*S, ay - 116*S), 'CABLE LANDING STATION', font=font(MONO_M, 13*S), fill=C(CYAN, 255*ca))
        d.text((ax + 68*S, ay - 84*S), 'the fiber joins the undersea cable', font=font(MONO, 13*S), fill=C('#E6ECF5', 220*ca))
    el = 0.009 + 0.004*seg(t, 11.0, 14.0)
    header(d, W, S, C, '04 / 08', 'THE COAST', f'≈ {el:.3f} s')
    cur = 2.0 + seg(t, 11.0, 12.2)
    kx, ky = route_strip(d, W, H, S, cur, C)
    d.ellipse([kx - 3.5*S, ky - 3.5*S, kx + 3.5*S, ky + 3.5*S], fill=C('#FFF4D8'))
    im = halo_composite(im, O, S)
    return im.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    out = ROOT + '/3d/fr/s3'; os.makedirs(out, exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'{out}/{fi:04d}.png')
