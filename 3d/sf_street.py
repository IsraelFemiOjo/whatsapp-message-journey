import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
import fast3d
from deep import *
from PIL import Image, ImageDraw, ImageFilter

EXR = sys.argv[1] if len(sys.argv) > 1 else ROOT + '/3d/street2k.exr'
OUT = sys.argv[2] if len(sys.argv) > 2 else ROOT + '/3d/styleframe_street.png'
P = fast3d.load(EXR); H, W = P['I'].shape; S = W/1080
A = json.load(open(EXR.replace('.exr', '.json')))
def px(p): return (p[0]*W, p[1]*H)
I, N = P['I'], P['N']

M = {
    1: ('#4A3526', '#3B2A1F', '#2C2018', '#1E1611'),
    2: ('#2E313B', '#262932', '#1D2027', '#14161B'),
    3: ('#5A5E6C', '#4A4E5B', '#3A3D48', '#272933'),
    6: ('#D9782A', '#B25F1B', '#8A4712', '#57300C'),
    7: ('#9FDDF2', '#86C8E0', '#6AAAC4', '#4D869E'),
    8: ('#5E7F8D', '#4C6A77', '#3B5561', '#2A3E47'),
    9: ('#6B6F7A', '#555963', '#40434C', '#2C2E35'),
    10: ('#9095A2', '#777C89', '#5D616C', '#3F424A'),
    11: ('#FFEBC0', '#FFEBC0', '#FFEBC0', '#FFEBC0'),
    12: ('#1D2638', '#182031', '#131A28', '#0D121C'),
    13: ('#F6C51E', '#DDAA14', '#B78B0E', '#7C5E09'),
    14: ('#171D2C', '#141A28', '#111623', '#0C101A'),
    15: ('#15151A', '#15151A', '#15151A', '#15151A'),
    16: ('#101014', '#101014', '#101014', '#101014'),
}
# sky: city haze at night, warm near the horizon
bg = gradient_bg(H, W, '#0C1024', '#3A2A3C', seed=9)
yb = np.linspace(0, 1, H)[:, None, None]
bg = bg*(1 - np.clip((yb - 0.45)/0.2, 0, 1)*0.7) + hexrgb('#0A0B12')*np.clip((yb - 0.45)/0.2, 0, 1)*0.7

fib = [px(p) for p in A['fiber']]
k = min(range(len(fib)), key=lambda i: abs(fib[i][0] - 0.47*W))
pkx, pky = fib[k]
lampx, lampy = px(A['lamp'])
img = stylize_dark(P, bg, light=(-0.3, -0.7, 0.65), fog_k=90.0, seabed_id=-1, mats=M, hard_ids=(6, 10, 13, 3),
                   pools=[(pkx, pky, 110*S, GOLD, 0.3), (lampx, lampy + 330*S, 260*S, '#FFCF8A', 0.18)], ink='#E8D9C4', ink_k=0.6)

# soil strata on the cut face: gravel under the road, then banded earth
cut = (I == 1) & (N[..., 1] < -0.85)
yt = px(A['ground_top'])[1]; ybt = px(A['ground_bot'])[1]
yy, xx = np.mgrid[0:H, 0:W]
v = (yy - yt)/max(1, ybt - yt) + 0.03*np.sin(xx/(W*0.07)) + 0.015*np.sin(xx/(W*0.021) + 1)
gravel = cut & (v < 0.14)
dots = ht_dist(H, W, 9, 20) < 0.22
img[gravel & dots] = img[gravel & dots]*0.4 + hexrgb('#8C7A66')*0.6
for a, b, c in ((0.14, 0.17, '#5A4231'), (0.55, 0.58, '#2A1E16'), (0.8, 0.83, '#5A4231')):
    band = cut & (v > a) & (v < b); img[band] = img[band]*0.5 + hexrgb(c)*0.5
fine = ht_dist(H, W, 6, 70) < 0.12
img[cut & (v > 0.17) & fine] = img[cut & (v > 0.17) & fine]*0.7 + hexrgb('#6B5140')*0.3

# lit windows on the buildings: a grid, some rooms on
bld = (I == 12) & (N[..., 1] < -0.6)
cw, ch = int(22*S), int(30*S)
cx_, cy_ = xx//cw, yy//ch
hsh = (cx_*73856093 ^ cy_*19349663) % 100
inner = ((xx % cw) > 5*S) & ((xx % cw) < cw - 5*S) & ((yy % ch) > 7*S) & ((yy % ch) < ch - 7*S)
lit = bld & inner & (hsh < 34)
dim = bld & inner & (hsh >= 34) & (hsh < 60)
img[lit] = np.where((hsh[lit] % 3 == 0)[:, None], hexrgb('#9FC8E8'), hexrgb('#FFCB7A'))*0.85
img[dim] = img[dim]*0.6 + hexrgb('#3A4560')*0.4

# the fiber glows; the message is a pulse riding it, trail behind
g = glow_layer(H, W, [(x, y, 0.5, 0.3) for x, y in fib[k:k + 120]], CYAN, 3*S, 0.5)
g += glow_layer(H, W, [(x, y, 1.0, 0.2 + 0.8*((i - (k - 110))/110)**2) for i, (x, y) in enumerate(fib[max(0, k - 110):k + 1], start=max(0, k - 110))], GOLD, 3.5*S, 1.1)
g += glow_layer(H, W, [(pkx, pky, 1, 1)], GOLD, 42*S, 1.0)
g += glow_layer(H, W, [(pkx, pky, 1, 1)], '#FFF4D8', 9*S, 2.4)
g += glow_layer(H, W, [(lampx, lampy + 6*S, 1, 1)], '#FFD9A0', 30*S, 0.8)
img = img + g
img = vignette(img, 0.55)
img = img*(1 - 0.5*np.clip((yb - 0.88)/0.12, 0, 1))
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')

O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
C = lambda c, a=255: tuple(int(v) for v in hexrgb(c)) + (a,)
fm = font(MONO, 13*S); fmm = font(MONO_M, 13*S)
d.text((48*S, 44*S), '04 / 09', font=fmm, fill=C('#FFFFFF', 200))
d.line([(118*S, 53*S), (170*S, 53*S)], fill=C(CYAN, 160), width=int(1*S))
d.text((180*S, 44*S), 'UNDER THE STREET', font=fm, fill=C('#CFEAF5', 200))
d.text((W - 48*S, 44*S), 'ELAPSED', font=fm, fill=C('#CFEAF5', 170), anchor='ra')
d.text((W - 48*S, 62*S), '≈ 0.02 s', font=font(MONO_M, 30*S), fill=C('#FFFFFF', 240), anchor='ra')
# one label on the thing it names
ax, ay = pkx + 60*S, pky + 8*S
d.ellipse([ax - 4*S, ay - 4*S, ax + 4*S, ay + 4*S], outline=C('#FFFFFF', 220), width=int(1.4*S))
d.line([(ax, ay), (ax + 40*S, ay + 120*S), (ax + 200*S, ay + 120*S)], fill=C('#FFFFFF', 150), width=int(1*S))
d.text((ax + 48*S, ay + 94*S), 'GLASS FIBER', font=fmm, fill=C(CYAN))
d.text((ax + 48*S, ay + 126*S), 'about as thin as a hair', font=fm, fill=C('#F2E8DA', 220))
# headline, bottom left, on the dark earth
d.text((46*S, 820*S), 'Under the road.', font=font(SERIF_I, 70*S), fill=C('#FFFFFF', 245))
d.text((48*S, 910*S), 'Your message now travels as light in glass.', font=font(SERIF, 25*S), fill=C('#EFE3D3', 225))
# route strip
nodes = ['PHONE', 'TOWER', 'STREET', 'COAST', 'OCEAN', 'SERVER', 'PHONE']
sx0, sx1, sy = 48*S, W - 48*S, H - 44*S
cur = 2.35
d.line([(sx0, sy), (sx1, sy)], fill=C('#CFEAF5', 60), width=int(1*S))
d.line([(sx0, sy), (sx0 + (sx1 - sx0)*cur/6, sy)], fill=C(GOLD, 220), width=int(2*S))
for i, nm in enumerate(nodes):
    x = sx0 + (sx1 - sx0)*i/6; done = i <= 2
    d.ellipse([x - 4*S, sy - 4*S, x + 4*S, sy + 4*S], fill=C(GOLD if done else '#0A1422'), outline=C(GOLD if done else '#CFEAF5', 220), width=int(1.2*S))
    d.text((x, sy - 12*S), nm, font=font(MONO, 10*S), fill=C('#FFFFFF' if i == 2 else '#CFEAF5', 240 if i == 2 else 130), anchor='md')
halo = O.split()[3].filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(8*S)).point(lambda v: int(v*0.7))
im.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', (W, H), (8, 6, 6)).split(), halo)))
im.alpha_composite(O)
im.convert('RGB').resize((1080, 1080), Image.LANCZOS).save(OUT)
print('saved')
