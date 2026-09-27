"""Dark, cinematic stylizer for the send journey: light ink on deep navy, sonar contour lines, fog, glow."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, math, numpy as np
sys.path.insert(0, ROOT + '/shared')
import fast3d
from fast3d import hexrgb, ht_dist, edges
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FD = ROOT + '/3d/fonts/'
SERIF, SERIF_I, MONO, MONO_M = FD + 'InstrumentSerif-Regular.ttf', FD + 'InstrumentSerif-Italic.ttf', FD + 'IBMPlexMono-Regular.ttf', FD + 'IBMPlexMono-Medium.ttf'
CYAN = '#6FD3F2'; GOLD = '#FFC45E'; INK_L = '#9FD9EC'

def gradient_bg(H, W, top='#10284A', bottom='#03060D', seed=0):
    y = np.linspace(0, 1, H)[:, None, None]
    img = hexrgb(top)[None, None]*(1 - y**0.8) + hexrgb(bottom)[None, None]*(y**0.8)
    img = np.repeat(img, W, axis=1)
    rng = np.random.default_rng(seed)
    img += rng.normal(0, 2.2, (H, W, 1))            # fine grain
    return img

def god_rays(H, W, seed=1, strength=0.10):
    L = Image.new('L', (W, H), 0); d = ImageDraw.Draw(L)
    rng = np.random.default_rng(seed)
    for k in range(9):
        x0 = rng.uniform(-0.1, 1.0)*W; w0 = rng.uniform(0.02, 0.07)*W; sk = rng.uniform(0.25, 0.45)*W
        d.polygon([(x0, 0), (x0 + w0, 0), (x0 + w0 + sk + w0*2, H*0.75), (x0 + sk, H*0.75)], fill=int(rng.uniform(60, 150)))
    L = L.filter(ImageFilter.GaussianBlur(W*0.02))
    fade = np.linspace(1, 0, H)[:, None]**1.5
    return np.array(L).astype(np.float32)/255*fade*strength

MATS = {   # lit, mid, shadow, deep
    1: ('#194357', '#123445', '#0C2533', '#071722'),
    2: ('#1A2638', '#121B2A', '#0B111C', '#070B13'),
    3: ('#3A4E66', '#2A3A4F', '#1B2737', '#0F1722'),
    4: ('#1C3444', '#142736', '#0D1B27', '#08121B'),
    5: ('#33465C', '#253447', '#182333', '#0E1621'),
}

def stylize_dark(P, bg, light=(-0.35, -0.25, 0.9), fog_k=30.0, fog_col=None, contour_step=3.2, pools=(), mats=None, hard_ids=(2, 3, 5), seabed_id=1, ink=INK_L, ink_k=0.85):
    H, W = P['I'].shape
    Lv = np.array(light, np.float32); Lv /= np.linalg.norm(Lv)
    I = P['I']; Z = P['Z']; N = P['N']
    out = bg.copy()
    fg = I > 0
    ndl = (N @ Lv)
    lut = np.zeros((256, 4, 3), np.float32)
    for k, (lit, mid, sh, dp) in (mats or MATS).items():
        lut[k] = [hexrgb(lit), hexrgb(mid), hexrgb(sh), hexrgb(dp)]
    tone = (ndl <= 0.8).astype(np.int8) + (ndl <= 0.55) + (ndl <= 0.2)
    col = lut[np.clip(I, 0, 255), tone]
    # sand stipple on the seabed, denser where lit
    sb = I == seabed_id
    st = ht_dist(H, W, 7, 30) < np.sqrt(np.clip((ndl - 0.82)*0.9, 0, 0.18)/math.pi)
    col[sb & st] = col[sb & st]*0.4 + hexrgb('#5FA8C0')*0.6
    # cyan rim on hard surfaces
    V = np.array((0.3, -0.8, 0.5), np.float32); V /= np.linalg.norm(V)
    rim = 1 - np.abs(N @ V)
    hard = np.isin(I, hard_ids)
    col[hard & (rim > 0.72)] = hexrgb(CYAN)*0.85
    out[fg] = col[fg]
    # pools of light cast by glowing things (x, y, radius px, color, strength)
    if pools:
        yy, xx = np.mgrid[0:H, 0:W]
        for (px_, py_, r_, c_, k_) in pools:
            w_ = np.exp(-((xx - px_)**2 + ((yy - py_)*1.6)**2)/(2*r_*r_))*k_
            out[fg] += (w_[..., None]*hexrgb(c_)[None, None])[fg]
    # sonar contour lines: iso depth rings across the floor
    zc = np.where(sb, Z, 0)
    band = (np.floor(zc/contour_step) != np.floor(np.roll(zc, 1, 0)/contour_step)) | (np.floor(zc/contour_step) != np.floor(np.roll(zc, 1, 1)/contour_step))
    band &= sb & np.roll(sb, 1, 0) & np.roll(sb, 1, 1)
    band[:2] = False; band[:, :2] = False
    band = np.array(Image.fromarray(band.astype(np.uint8)*255).filter(ImageFilter.MaxFilter(3))) > 0
    a = np.clip(1.0 - Z/32, 0, 1)*0.28
    out[band] = out[band]*(1 - a[band, None]) + hexrgb('#4FB3D6')*a[band, None]
    # fog: fade into the water with distance
    f = 1 - np.exp(-np.where(fg, Z, 1e3)/fog_k)
    fc = bg if fog_col is None else np.broadcast_to(hexrgb(fog_col), bg.shape)
    out = out*(1 - f[..., None]) + fc*f[..., None]
    # light ink contours, fading with the fog
    e = edges(I, Z, N, 3)
    ea = np.clip(ink_k - f, 0, ink_k)
    out[e] = out[e]*(1 - ea[e, None]) + hexrgb(ink)*ea[e, None]
    return out

def glow_layer(H, W, pts, color, radius, strength):
    """additive glow from a list of (x, y, r_scale, a) points"""
    L = Image.new('RGB', (W, H), (0, 0, 0)); d = ImageDraw.Draw(L)
    c = tuple(int(v) for v in hexrgb(color))
    for x, y, rs, a in pts:
        r = radius*rs
        d.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v*a) for v in c))
    return np.array(L.filter(ImageFilter.GaussianBlur(radius*0.9))).astype(np.float32)*strength

def marine_snow(H, W, n, seed, t=0.0):
    rng = np.random.default_rng(seed)
    L = Image.new('L', (W, H), 0); d = ImageDraw.Draw(L)
    B = Image.new('L', (W, H), 0); db = ImageDraw.Draw(B)
    for k in range(n):
        x = (rng.uniform(0, W) + t*rng.uniform(-8, 8)) % W; y = (rng.uniform(0, H) + t*rng.uniform(10, 40)) % H
        r = rng.uniform(0.6, 2.2)*W/2160*2
        if rng.random() < 0.06:
            rb = rng.uniform(8, 26)*W/2160*2
            db.ellipse([x - rb, y - rb, x + rb, y + rb], fill=int(rng.uniform(20, 60)))
        else:
            d.ellipse([x - r, y - r, x + r, y + r], fill=int(rng.uniform(80, 220)))
    B = B.filter(ImageFilter.GaussianBlur(6))
    return (np.array(L).astype(np.float32) + np.array(B).astype(np.float32))/255

def font(path, size): return ImageFont.truetype(path, int(size))

_VIG = {}
def vignette(img, k=0.55):
    H, W = img.shape[:2]
    key = (H, W, k)
    if key not in _VIG:
        y, x = np.mgrid[0:H, 0:W]
        r = np.sqrt(((x - W/2)/(W/2))**2 + ((y - H/2)/(H/2))**2)
        _VIG[key] = (1 - k*np.clip(r - 0.55, 0, 1)**1.6)[..., None].astype(np.float32)
    return img*_VIG[key]
