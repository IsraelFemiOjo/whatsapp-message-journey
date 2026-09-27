"""Section 6 compositor: 28.5 to 35.5 s. The server hall."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, os, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d')
from sjcomp import *
from chatui import F as UIF
from PIL import Image, ImageDraw, ImageFilter

R3 = sys.argv[3] if len(sys.argv) > 3 else ROOT + '/3d/r3d/s6'
J = json.load(open(f'{R3}/anchors_1_169.json')); AN = J['anchors']
M6 = {50: ('#1E222C', '#1A1E27', '#161921', '#11131A'), 51: ('#262B37', '#20242F', '#1A1E27', '#13161D'),
      52: ('#2E3443', '#282D3A', '#222632', '#1A1D26'), 53: ('#101218',)*4, 54: ('#DCE6F5',)*4, 55: ('#4A515F', '#3E4451', '#333844', '#262A33')}
def near(f):
    ks = sorted(int(k) for k in AN); return str(min(ks, key=lambda k: abs(k - f)))

def leds(img, P, t):
    if 'P' not in P: return img, None
    I, X = P['I'], P['P']
    m = I == 52
    ys, xs = np.nonzero(m)
    p = X[ys, xs]
    y0 = np.floor(p[:, 1]/0.65)*0.65 + 0.04
    u = (p[:, 1] - y0)/0.54; row = np.floor(p[:, 2]/0.0889); fv = p[:, 2]/0.0889 - row
    side = np.sign(p[:, 0])
    out = img.copy()
    seam = fv < 0.06
    out[ys[seam], xs[seam]] *= 0.55
    h = (np.floor(p[:, 1]/0.65).astype(np.int64)*7919 + row.astype(np.int64)*104729 + (side > 0)*31) % 997
    for k, (uc, col) in enumerate(((0.07, '#39E07A'), (0.11, '#39E07A'), (0.15, '#4FA8FF'))):
        on = (np.sin(t*(3 + (h % 7)) + h*0.37 + k) > -0.2) if k < 2 else (h % 3 == 0)
        dot = (np.abs(u - uc) < 0.012) & (np.abs(fv - 0.5) < 0.16) & on
        out[ys[dot], xs[dot]] = hexrgb(col)
    bar = (u > 0.62) & (u < 0.93) & (np.abs(fv - 0.5) < 0.1)
    out[ys[bar], xs[bar]] = out[ys[bar], xs[bar]]*0.5 + hexrgb('#0C0E14')*0.5
    return out, None

def floor_grid(img, P):
    if 'P' not in P: return img
    I, X = P['I'], P['P']
    m = I == 50
    ys, xs = np.nonzero(m); p = X[ys, xs]
    gx = np.abs(((p[:, 0] + 0.3) % 0.6) - 0.3) < 0.008; gy = np.abs(((p[:, 1]) % 0.6) - 0.3) < 0.008
    sel = gx | gy
    out = img.copy(); out[ys[sel], xs[sel]] = out[ys[sel], xs[sel]]*0.6 + hexrgb('#3A4252')*0.4
    return out

def zoom_blur(img, k, S):
    if k <= 0.01: return img
    H, W = img.shape[:2]; pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    acc = img.copy(); n = 7
    for i in range(1, n):
        s = 1 + 0.12*k*i/n
        w2, h2 = int(W*s), int(H*s)
        z = pil.resize((w2, h2), Image.BILINEAR).crop(((w2 - W)//2, (h2 - H)//2, (w2 - W)//2 + W, (h2 - H)//2 + H))
        acc += np.array(z).astype(np.float32)
    return acc/n

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

def render(fi, W=2160):
    H = W; S = W/1080
    t = 28.5 + fi/24; tt = math.floor(t*12)/12
    key = near(fi + 1 - (fi % 2)); a = AN[key]
    P = load(f'{R3}/{int(key):04d}.exr')
    if P['I'].shape[0] != H:
        def rs(v): return np.array(Image.fromarray(v.astype(np.float32)).resize((W, H), Image.NEAREST))
        P = {k: (rs(v) if v.ndim == 2 else np.stack([rs(v[..., c]) for c in range(v.shape[2])], -1)) for k, v in P.items()}
        P['I'] = P['I'].astype(np.int16)
    bg = gradient_bg(H, W, '#0A0C14', '#050608', seed=61)
    px_, py_ = a['pulse'][0]*W, a['pulse'][1]*H
    img = stylize_dark(P, bg, light=(0.2, -0.3, 0.93), fog_k=38.0, fog_col='#07080C', seabed_id=-1, mats=M6, hard_ids=(55,),
                       pools=[(px_, py_, 130*S, GOLD, 0.35)], ink='#7FA6C8', ink_k=0.5)
    img, _ = leds(img, P, t)
    img = floor_grid(img, P)
    strips = P['I'] == 54
    g = np.zeros((H, W, 3), np.float32)
    if strips.any():
        sl = Image.fromarray((strips*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(18*S))
        g += (np.array(sl).astype(np.float32)/255)[..., None]*hexrgb('#9FC4F0')[None, None]*0.35
    # the pulse, with a trail once it moves
    if t >= 31.9:
        g += glow_layer(H, W, [(px_, py_, 1, 1)], GOLD, 26*S, 0.9)
    g += glow_layer(H, W, [(px_, py_, 1, 1)], GOLD, 55*S, 1.2) + glow_layer(H, W, [(px_, py_, 1, 1)], '#FFF4D8', 12*S, 2.3)
    img = img + g
    img = zoom_blur(img, ease(seg(t, 33.6, 35.5)), S)
    if t < 28.9:   # still carrying the light from the fiber
        img = img + glow_layer(H, W, [(W/2, H/2, 1, 1)], GOLD, 520*S*(1 - seg(t, 28.5, 28.9)) + 20*S, 2.2*(1 - seg(t, 28.5, 28.9)))
    img = vignette(img, 0.6)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
    C = lambda c, al=255: tuple(int(v) for v in hexrgb(c)) + (int(al),)
    # what the server holds: the scrambled copy
    ch = inout(t, 30.2, 32.0)
    if ch > 0:
        s_ = scramble('Hello from Lagos!', 99, int(tt*6))
        bx, by = px_ + 40*S, py_ - 110*S
        d.rounded_rectangle([bx, by, bx + 330*S, by + 64*S], radius=10*S, fill=C('#0E1622', 225*ch), outline=C(GOLD, 200*ch), width=int(1.4*S))
        d.text((bx + 18*S, by + 32*S), s_, font=font(MONO_M, 22*S), fill=C('#FFD58A', 255*ch), anchor='lm')
        d.line([(px_ + 8*S, py_ - 8*S), (bx, by + 64*S)], fill=C('#FFFFFF', 140*ch), width=int(1*S))
    fade_text(d, (46*S, 92*S), 'A WhatsApp server.', font(SERIF_I, 64*S), '#FFFFFF', inout(t, 29.6, 31.9))
    fade_text(d, (48*S, 172*S), 'It passes the message on. It can\'t read it.', font(SERIF, 25*S), '#DDE6F2', inout(t, 29.8, 31.9))
    ta = inout(t, 31.9, 33.6)
    if ta > 0:
        fade_text(d, (46*S, 92*S), 'One grey tick.', font(SERIF_I, 64*S), '#FFFFFF', ta)
        fade_text(d, (48*S, 172*S), 'It means the server has your message.', font(SERIF, 25*S), '#DDE6F2', ta)
        mini_bubble(d, 48*S, 220*S, S, ta, ticks=1)
    el = 0.067 + 0.09*seg(t, 28.5, 35.5)
    header(d, W, S, C, '07 / 08', 'THE SERVER', f'≈ {el:.3f} s')
    cur = 4.45 + 0.55*seg(t, 28.5, 30.0) + 0.5*seg(t, 33.0, 35.5)
    kx, ky = route_strip(d, W, H, S, cur, C)
    d.ellipse([kx - 3.5*S, ky - 3.5*S, kx + 3.5*S, ky + 3.5*S], fill=C('#FFF4D8'))
    im = halo_composite(im, O, S)
    return im.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    out = ROOT + '/3d/fr/s6'; os.makedirs(out, exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'{out}/{fi:04d}.png')
