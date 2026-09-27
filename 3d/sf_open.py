import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
import fast3d
from deep import *
from chatui import screen
from PIL import Image, ImageDraw, ImageFilter

EXR = sys.argv[1] if len(sys.argv) > 1 else ROOT + '/3d/phone2k.exr'
OUT = sys.argv[2] if len(sys.argv) > 2 else ROOT + '/3d/styleframe_open.png'
P = fast3d.load(EXR); H, W = P['I'].shape; S = W/1080
A = json.load(open(EXR.replace('.exr', '.json')))
Q = [(p[0]*W, p[1]*H) for p in A['screen']]      # TL TR BR BL

def persp_coeffs(dst, src):
    M = []
    for (x, y), (u, v) in zip(dst, src):
        M.append([x, y, 1, 0, 0, 0, -u*x, -u*y]); M.append([0, 0, 0, x, y, 1, -v*x, -v*y])
    B = np.array([c for p in src for c in p], float)
    return np.linalg.solve(np.array(M, float), B)
def on_screen(uv):
    """map a point in screen UV (0..1) to image pixels (bilinear on the quad is close enough here)"""
    u, v = uv
    top = (Q[0][0] + (Q[1][0] - Q[0][0])*u, Q[0][1] + (Q[1][1] - Q[0][1])*u)
    bot = (Q[3][0] + (Q[2][0] - Q[3][0])*u, Q[3][1] + (Q[2][1] - Q[3][1])*u)
    return (top[0] + (bot[0] - top[0])*v, top[1] + (bot[1] - top[1])*v)

# ---- background: Lagos at night, out of focus ----
bg = gradient_bg(H, W, '#140F22', '#07060C', seed=12)
rng = np.random.default_rng(21)
Bk = Image.new('RGB', (W, H), (0, 0, 0)); db = ImageDraw.Draw(Bk)
cols = ['#FFB25A', '#FF9A3C', '#FFD27A', '#FF5A4A', '#9FC8FF', '#F6C51E', '#FFE1B0']
for k in range(90):
    x = rng.uniform(-0.05, 1.05)*W; y = (0.52 + rng.normal(0, 0.1))*H if k < 50 else rng.uniform(0.1, 0.5)*H
    r = rng.uniform(8, 38)*S; c = hexrgb(cols[rng.integers(len(cols))])*rng.uniform(0.2, 0.6)
    db.ellipse([x - r, y - r, x + r, y + r], fill=tuple(int(v) for v in c))
Bk = np.array(Bk.filter(ImageFilter.GaussianBlur(10*S))).astype(np.float32)
# a band of street lights across the lower third (road in the distance)
band = Image.new('RGB', (W, H), (0, 0, 0)); dband = ImageDraw.Draw(band)
for k in range(40):
    x = k/40*W + rng.uniform(-10, 10)*S; y = 0.66*H + 0.04*H*math.sin(k*0.3); r = rng.uniform(6, 14)*S
    dband.ellipse([x - r, y - r, x + r, y + r], fill=(255, 176, 90))
band = np.array(band.filter(ImageFilter.GaussianBlur(7*S))).astype(np.float32)
bg = bg + Bk*0.9 + band*0.6
bg = np.array(Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3*S))).astype(np.float32)

MP = {20: ('#3A3F4E', '#2A2E3A', '#1D2029', '#111318'), 21: ('#0B141A',)*4, 22: ('#4A5060',)*4}
img = stylize_dark(P, bg, light=(0.4, -0.8, 0.5), fog_k=1e6, seabed_id=-1, mats=MP, hard_ids=(22,), ink='#C9D6E6', ink_k=0.5)

# ---- chat UI mapped onto the screen ----
ui, (bx, by) = screen(press=1.0)
uiw, uih = ui.size
coeffs = persp_coeffs(Q, [(0, 0), (uiw, 0), (uiw, uih), (0, uih)])
warp = ui.transform((W, H), Image.PERSPECTIVE, tuple(coeffs), Image.BICUBIC)
mask = Image.new('L', (W, H), 0); ImageDraw.Draw(mask).polygon(Q, fill=255)
scr_m = (np.array(mask) > 0) & (P['I'] == 21)
img[scr_m] = np.array(warp).astype(np.float32)[scr_m]*1.05
yy_, xx_ = np.mgrid[0:H, 0:W]
gl = scr_m & (np.abs((xx_ - Q[0][0]) + (yy_ - Q[0][1])*0.55 - 0.42*(Q[2][0] - Q[0][0] + (Q[2][1] - Q[0][1])*0.55)) < 70*S)
img[gl] = img[gl]*0.92 + 255*0.08
# screen light spills onto the scene
sc_c = np.mean(Q, axis=0)
img += glow_layer(H, W, [(sc_c[0], sc_c[1], 1, 1)], '#5FB8A8', 260*S, 0.25)

send = on_screen((bx, by))
# the tap: a soft ring and the birth of the pulse under the thumb
img += glow_layer(H, W, [(send[0], send[1], 1, 1)], '#7FFFE0', 40*S, 0.8)
img = vignette(img, 0.6)
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')

O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
C = lambda c, a=255: tuple(int(v) for v in hexrgb(c)) + (a,)
for k, rr in enumerate((46, 70)):
    d.ellipse([send[0] - rr*S, send[1] - rr*S, send[0] + rr*S, send[1] + rr*S], outline=C('#BFFFF0', 170 - 70*k), width=int(2*S))
d.text((48*S, 44*S), 'LAGOS', font=font(MONO_M, 14*S), fill=C('#FFFFFF', 230))
d.text((118*S, 44*S), '→  LONDON', font=font(MONO, 14*S), fill=C('#CFEAF5', 200))
d.text((W - 48*S, 44*S), 'ELAPSED', font=font(MONO, 13*S), fill=C('#CFEAF5', 170), anchor='ra')
d.text((W - 48*S, 62*S), '0.000 s', font=font(MONO_M, 30*S), fill=C('#FFFFFF', 240), anchor='ra')
d.text((46*S, 150*S), 'What happens', font=font(SERIF_I, 64*S), fill=C('#FFFFFF', 245))
d.text((46*S, 214*S), 'after you hit send.', font=font(SERIF_I, 64*S), fill=C('#FFFFFF', 245))
nodes = ['PHONE', 'TOWER', 'STREET', 'COAST', 'OCEAN', 'SERVER', 'PHONE']
sx0, sx1, sy = 48*S, W - 48*S, H - 44*S
d.line([(sx0, sy), (sx1, sy)], fill=C('#CFEAF5', 60), width=int(1*S))
for i, nm in enumerate(nodes):
    x = sx0 + (sx1 - sx0)*i/6; done = i == 0
    d.ellipse([x - 4*S, sy - 4*S, x + 4*S, sy + 4*S], fill=C(GOLD if done else '#0A1422'), outline=C(GOLD if done else '#CFEAF5', 220), width=int(1.2*S))
    d.text((x, sy - 12*S), nm, font=font(MONO, 10*S), fill=C('#FFFFFF' if done else '#CFEAF5', 240 if done else 130), anchor='md')
halo = O.split()[3].filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(8*S)).point(lambda v: int(v*0.6))
im.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, H), (6, 5, 10)).split(), halo)))
im.alpha_composite(O)
im.convert('RGB').resize((1080, 1080), Image.LANCZOS).save(OUT)
print('saved')
