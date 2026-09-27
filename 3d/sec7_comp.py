"""Section 7 (35.5 to 45.0 s): London in the rain. The message arrives, unscrambles, two grey ticks, the end."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, os, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d')
from sjcomp import *
from chatui import screen_recv
from chatui import F as UIF
from PIL import Image, ImageDraw, ImageFilter

def mini_bubble(d, x, y, S, al, ticks=1):
    """the sender's view: their bubble with one grey tick"""
    C = lambda c, a=255: tuple(int(v) for v in hexrgb(c)) + (int(a*al),)
    w, h = 300*S, 58*S
    d.rounded_rectangle([x, y, x + w, y + h], radius=12*S, fill=C('#005C4B'))
    d.text((x + 16*S, y + 14*S), 'Hello from Lagos!', font=UIF(22*S), fill=C('#E9EDEF'))
    d.text((x + w - 58*S, y + h - 10*S), '21:47', font=UIF(14*S), fill=C('#9FC9BD'), anchor='rs')
    for k in range(ticks):
        tx = x + w - 34*S + k*8*S
        d.line([(tx, y + h - 20*S), (tx + 4*S, y + h - 15*S), (tx + 12*S, y + h - 27*S)], fill=C('#9FC9BD'), width=int(2.5*S))


EXR = ROOT + '/3d/phone2k.exr'
PH = load(EXR); A = json.load(open(EXR.replace('.exr', '.json')))
MP = {20: ('#3A3F4E', '#2A2E3A', '#1D2029', '#111318'), 21: ('#0B141A',)*4, 22: ('#4A5060',)*4}
_BG = {}
def london_bg(W, H, S):
    if W in _BG: return _BG[W]
    bg = gradient_bg(H, W, '#0B1220', '#05070C', seed=71)
    rng = np.random.default_rng(44)
    Bk = Image.new('RGB', (W, H)); db = ImageDraw.Draw(Bk)
    cols = ['#9FC8FF', '#CFE3FF', '#FFD9A0', '#FFB25A', '#FF4A3A', '#E8F0FF']
    for k in range(110):
        x = rng.uniform(-0.05, 1.05)*W; y = (0.55 + rng.normal(0, 0.12))*H if k < 80 else rng.uniform(0.15, 0.5)*H
        r = rng.uniform(8, 40)*S; c = hexrgb(cols[rng.integers(len(cols))])*rng.uniform(0.2, 0.55)
        db.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v) for v in c))
    bg = bg + np.array(Bk.filter(ImageFilter.GaussianBlur(12*S))).astype(np.float32)*0.9
    _BG[W] = bg
    return bg

def rain(W, H, S, t, streak):
    """drops and runs on the window glass, plus falling streaks early on"""
    L = Image.new('L', (W, H), 0); d = ImageDraw.Draw(L)
    rng = np.random.default_rng(9)
    for k in range(260):
        x = rng.uniform(0, W); y0 = rng.uniform(0, H); sp = rng.uniform(40, 160)*S
        y = (y0 + sp*(t - 35.5)) % H; r = rng.uniform(1.5, 4.5)*S
        ln = r*2 + streak*rng.uniform(80, 400)*S
        d.line([(x, y - ln), (x, y)], fill=int(90 + 60*rng.random()), width=max(1, int(r*0.9)))
        d.ellipse([x - r, y - r, x + r, y + r], fill=160)
    return np.array(L.filter(ImageFilter.GaussianBlur(1.5*S))).astype(np.float32)/255

def persp(Q, src):
    Mx = []
    for (x, y), (u, v) in zip(Q, src):
        Mx.append([x, y, 1, 0, 0, 0, -u*x, -u*y]); Mx.append([0, 0, 0, x, y, 1, -v*x, -v*y])
    return np.linalg.solve(np.array(Mx, float), np.array([c for p in src for c in p], float))
def homography(Q):
    src = [(0, 0), (1, 0), (1, 1), (0, 1)]; Mx = []
    for (u, v), (x, y) in zip(src, Q):
        Mx.append([u, v, 1, 0, 0, 0, -x*u, -x*v]); Mx.append([0, 0, 0, u, v, 1, -y*u, -y*v])
    h = np.linalg.solve(np.array(Mx, float), np.array([c for p in Q for c in p], float)); Hm = np.append(h, 1).reshape(3, 3)
    return lambda u, v: (lambda p: p[:2]/p[2])(Hm @ np.array([u, v, 1.0]))

def render(fi, W=2160):
    H = W; S = W/1080
    t = 35.5 + fi/24; tt = math.floor(t*12)/12
    P = PH
    if P['I'].shape[0] != H:
        def rs(v): return np.array(Image.fromarray(v.astype(np.float32)).resize((W, H), Image.NEAREST))
        P = {k: (rs(v) if v.ndim == 2 else np.stack([rs(v[..., c]) for c in range(v.shape[2])], -1)) for k, v in P.items()}
        P['I'] = P['I'].astype(np.int16)
    streak = 1 - ease(seg(t, 35.5, 36.6))
    bg = london_bg(W, H, S).copy()
    rn = rain(W, H, S, t, streak)
    bg = bg*(1 - rn[..., None]*0.35) + rn[..., None]*hexrgb('#CFE3FF')[None, None]*0.45
    img = stylize_dark(P, bg, light=(0.4, -0.8, 0.5), fog_k=1e6, seabed_id=-1, mats=MP, hard_ids=(22,), ink='#C9D6E6', ink_k=0.5)
    Q = [(q[0]*W, q[1]*H) for q in A['screen']]
    Hf = homography(Q)
    # the message arrives scrambled and unscrambles letter by letter
    arrive = ease(seg(t, 36.85, 37.1))
    k = int(len('Hello from Lagos!')*ease(seg(t, 37.3, 38.3)))
    shown = scramble('Hello from Lagos!', 17 - k, int(tt*12)) if k < 17 else 'Hello from Lagos!'
    shown = shown[::-1] if False else shown
    # unscramble from the left: first k letters are plain
    if k < 17:
        sc = scramble('Hello from Lagos!', 17, int(tt*12)); shown = 'Hello from Lagos!'[:k] + sc[k:]
    ui, info = screen_recv(shown, show=arrive)
    uiw, uih = ui.size
    co = persp(Q, [(0, 0), (uiw, 0), (uiw, uih), (0, uih)])
    warp = np.array(ui.transform((W, H), Image.PERSPECTIVE, tuple(co), Image.BICUBIC)).astype(np.float32)
    scr = P['I'] == 21
    on = ease(seg(t, 36.3, 36.7))
    img[scr] = img[scr]*(1 - on) + warp[scr]*1.05*on
    yy, xx = np.mgrid[0:H, 0:W]
    sheen = scr & (np.abs((xx - Q[0][0]) + (yy - Q[0][1])*0.55 - 0.42*((Q[2][0] - Q[0][0]) + (Q[2][1] - Q[0][1])*0.55)) < 70*S)
    img[sheen] = img[sheen]*0.93 + 255*0.07
    # the pulse drops in from above and lands in the bubble
    g = np.zeros((H, W, 3), np.float32)
    bx, by = Hf(*info['bubble'])
    if t < 37.05:
        k2 = ease(seg(t, 35.9, 36.95))
        px_, py_ = W/2 + (bx - W/2)*k2, H*0.5 + (by - H*0.5)*k2
        sz = 1 - 0.6*k2
        g += glow_layer(H, W, [(px_, py_, 1, 1)], GOLD, 55*S*sz, 1.3) + glow_layer(H, W, [(px_, py_, 1, 1)], '#FFF4D8', 12*S*sz, 2.4)
    elif t < 37.5:
        k3 = 1 - seg(t, 37.05, 37.5)
        g += glow_layer(H, W, [(bx, by, 1, 1)], GOLD, 140*S, 0.8*k3)
    img = img + g
    # push in on the message as it unscrambles, then pull back out for the last line
    zk = ease(seg(t, 37.0, 37.9))*(1 - ease(seg(40.4, 41.2) if False else seg(t, 40.4, 41.2)))
    if zk > 0.001:
        z = 1 + 0.55*zk; fx, fy = W/2 + (bx - W/2)*zk, H/2 + (by - H/2)*zk
        pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
        w2, h2 = W/z, H/z; x0 = min(max(0, fx - w2/2), W - w2); y0 = min(max(0, fy - h2/2), H - h2)
        img = np.array(pil.crop((int(x0), int(y0), int(x0 + w2), int(y0 + h2))).resize((W, H), Image.BICUBIC)).astype(np.float32)
    img = vignette(img, 0.6)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
    C = lambda c, al=255: tuple(int(v) for v in hexrgb(c)) + (int(al),)
    fade_text(d, (46*S, 790*S), 'Unscrambled here,', font(SERIF_I, 58*S), '#FFFFFF', inout(t, 37.3, 38.9))
    fade_text(d, (46*S, 850*S), 'on your friend\'s phone.', font(SERIF_I, 58*S), '#FFFFFF', inout(t, 37.3, 38.9))
    ta = inout(t, 39.0, 40.7)
    if ta > 0:
        fade_text(d, (46*S, 150*S), 'Two grey ticks.', font(SERIF_I, 58*S), '#FFFFFF', ta)
        fade_text(d, (48*S, 222*S), 'It means your message was delivered.', font(SERIF, 25*S), '#DDE6F2', ta)
        mini_bubble(d, 48*S, 270*S, S, ta, ticks=2)
    ea = seg(t, 40.9, 41.3)
    fade_text(d, (46*S, 150*S), 'Lagos to London.', font(SERIF_I, 64*S), '#FFFFFF', ea)
    fade_text(d, (46*S, 214*S), 'Under a second.', font(SERIF_I, 64*S), GOLD, seg(t, 41.4, 41.8))
    fade_text(d, (48*S, 970*S), 'Made with Claude Opus 5.5', font(MONO, 13*S), '#CFEAF5', 0.8*seg(t, 42.2, 42.8))
    el = 0.157 + 0.043*seg(t, 35.5, 37.1)
    header(d, W, S, C, '08 / 08', 'LONDON', f'≈ {el:.3f} s' if t < 37.1 else '≈ 0.2 s')
    cur = 5.0 + seg(t, 35.5, 37.0)
    kx, ky = route_strip(d, W, H, S, cur, C)
    d.ellipse([kx - 3.5*S, ky - 3.5*S, kx + 3.5*S, ky + 3.5*S], fill=C('#FFF4D8'))
    im = halo_composite(im, O, S)
    return im.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    out = ROOT + '/3d/fr/s7'; os.makedirs(out, exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'{out}/{fi:04d}.png')
