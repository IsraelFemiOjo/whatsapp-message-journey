"""Fast stylisation of Blender passes (cached screen patterns, masked maths)."""
import numpy as np, OpenEXR, math
from PIL import Image, ImageFilter

_CACHE = {}
def _grid(H, W):
    k = ('g', H, W)
    if k not in _CACHE:
        y, x = np.mgrid[0:H, 0:W].astype(np.float32); _CACHE[k] = (x, y)
    return _CACHE[k]

def ht_dist(H, W, cell, angle):
    k = ('ht', H, W, cell, angle)
    if k not in _CACHE:
        x, y = _grid(H, W); a = math.radians(angle)
        u = (x*math.cos(a) + y*math.sin(a))/cell; v = (-x*math.sin(a) + y*math.cos(a))/cell
        _CACHE[k] = np.sqrt((u - np.round(u))**2 + (v - np.round(v))**2).astype(np.float32)
    return _CACHE[k]

def hatch_frac(H, W, period, angle):
    k = ('hf', H, W, period, angle)
    if k not in _CACHE:
        x, y = _grid(H, W); a = math.radians(angle)
        t = (x*math.cos(a) + y*math.sin(a))/period
        wob = np.sin((-x*math.sin(a) + y*math.cos(a))/37.0)*0.12
        _CACHE[k] = np.abs((t + wob) - np.round(t + wob)).astype(np.float32)
    return _CACHE[k]

def halftone(shape, amount, cell=11, angle=45):
    d = ht_dist(shape[0], shape[1], cell, angle)
    return d < np.sqrt(np.clip(amount, 0, 1)/math.pi)*1.05

def load(path):
    with OpenEXR.File(path) as f:
        ch = {}
        for p in f.parts:
            for k, v in p.channels.items(): ch[k] = v.pixels
    comb = ch['ViewLayer.Combined']
    N = np.stack([ch['ViewLayer.Normal.X'], ch['ViewLayer.Normal.Y'], ch['ViewLayer.Normal.Z']], -1).astype(np.float32)
    Z = ch['ViewLayer.Depth.Z'].astype(np.float32); I = np.rint(ch['ViewLayer.Object Index.X']).astype(np.int16)
    return dict(A=comb[..., 3], N=N, Z=Z, I=I)

def hexrgb(c): c = c.lstrip('#'); return np.array([int(c[i:i+2], 16) for i in (0, 2, 4)], np.float32)

MATS = {
    1: ('#45405E', '#2A2740', '#191727', '#0C0B14'),
    3: ('#45405E', '#2A2740', '#191727', '#0C0B14'),
    4: ('#4A4666', '#2E2B44', '#1C1A2A', '#0C0B14'),
    5: ('#5B5680', '#3A3656', '#232036', '#0C0B14'),
    6: ('#C8C4D6', '#9C98AE', '#6F6B84', '#3B3852'),
    7: ('#6E86B8', '#3E4F7C', '#1E2744', '#0C0B14'),
    9: ('#FFD27A', '#F6B24A', '#EE8A24', '#C4621A'),
    10: ('#1E1B2C', '#1E1B2C', '#1E1B2C', '#1E1B2C'),
    11: ('#FFE7A8', '#FFD27A', '#F6B24A', '#C4621A'),
    12: ('#3A4B7A', '#26345E', '#18223F', '#0C0B14'),
    13: ('#E9E4D6', '#CFC8B6', '#ADA692', '#6E6A5A'),
    14: ('#3A3550', '#2B2740', '#1E1B2C', '#0C0B14'),
    20: ('#4B4760', '#2C2A40', '#1A1828', '#0C0B14'),
    21: ('#31406E', '#22305A', '#161F3D', '#0C0B14'),
    23: ('#D5D3DE', '#AAA7B8', '#7C7990', '#45425A'),
    24: ('#E6E2EA', '#C8C3D0', '#A29CAE', '#6E6A7C'),
    25: ('#56526E', '#3A3652', '#262338', '#0C0B14'),
    26: ('#8A86A0', '#66627C', '#48445C', '#1E1B2C'),
    28: ('#3B4466', '#252B45', '#171A2C', '#0B0B14'),
    27: ('#F0B25A', '#D48C34', '#A8651E', '#5A3410'),
}
LENS_TINT = hexrgb('#BFD3E8')

def edges(I, Z, N, thick=5):
    Zm = np.where(I > 0, Z, 1e4).astype(np.float32)
    e = np.zeros(I.shape, bool)
    for dy, dx in ((0, 1), (1, 0)):
        I2 = np.roll(I, (dy, dx), (0, 1)); Z2 = np.roll(Zm, (dy, dx), (0, 1)); N2 = np.roll(N, (dy, dx), (0, 1))
        diff_obj = (I != I2) & ~(((I == 2) & (I2 == 1)) | ((I == 1) & (I2 == 2)) & False)
        e |= diff_obj
        e |= np.abs(Zm - Z2)/np.minimum(Zm, Z2) > 0.012
        e |= ((N*N2).sum(-1) < 0.8) & (I > 0) & (I2 > 0)
    img = Image.fromarray((e*255).astype(np.uint8))
    return np.array(img.filter(ImageFilter.MaxFilter(thick))) > 0

def stylize(P, bg, light=(-0.55, -0.65, 0.55), view=(0.55, -0.8, 0.25), rim_col='#7FA6FF', line_col='#141221', thick=5):
    H, W = P['I'].shape
    L = np.array(light, np.float32); L /= np.linalg.norm(L)
    V = np.array(view, np.float32); V /= np.linalg.norm(V)
    I = P['I']; out = bg.astype(np.float32).copy()
    fg = I > 0
    if not fg.any(): return out.astype(np.uint8)
    idx = np.nonzero(fg)
    N = P['N'][idx]
    ndl = N @ L
    rim = 1 - np.abs(N @ V)
    Iv = I[idx]
    ht = ht_dist(H, W, 12, 45)[idx]
    hf = hatch_frac(H, W, 10, -35)[idx]
    shade_amt = np.clip((0.35 - ndl)/0.9, 0, 1)
    dots = ht < np.sqrt(shade_amt*0.55/math.pi)*1.05
    hat = (hf < 0.32) & (ndl < -0.25)
    col = np.zeros((len(Iv), 3), np.float32)
    for k, (lit, mid, sh, dot) in MATS.items():
        m = Iv == k
        if not m.any(): continue
        c = np.where((ndl[m] > 0.35)[:, None], hexrgb(lit), np.where((ndl[m] > -0.05)[:, None], hexrgb(mid), hexrgb(sh)))
        c = np.where(dots[m][:, None], hexrgb(dot)*0.6 + c*0.4, c)
        c = np.where(hat[m][:, None], hexrgb(dot), c)
        if k not in (10,):
            c = np.where(((rim[m] > 0.72) & (ndl[m] > -0.2))[:, None], hexrgb(rim_col), c)
        col[m] = c
    lens = Iv == 2
    base = out[idx]
    col[lens] = base[lens]*0.62 + LENS_TINT*0.38
    out[idx] = col
    e = edges(I, P['Z'], P['N'], thick)
    out[e] = hexrgb(line_col)
    return out.clip(0, 255).astype(np.uint8)

def edges_only(P, bg, reveal_mask=None, line_col='#141221', thick=5):
    out = bg.copy()
    e = edges(P['I'], P['Z'], P['N'], thick)
    if reveal_mask is not None: e &= reveal_mask
    out[e] = hexrgb(line_col).astype(np.uint8)
    return out

def misregister(img, dx=6, dy=-3):
    out = img.copy()
    out[..., 0] = np.roll(img[..., 0], (dy, dx), (0, 1)); out[..., 2] = np.roll(img[..., 2], (-dy, -dx), (0, 1))
    return out
