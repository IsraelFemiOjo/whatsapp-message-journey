import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
import fast3d
from deep import *
from PIL import Image, ImageDraw, ImageFilter

EXR = sys.argv[1] if len(sys.argv) > 1 else ROOT + '/3d/ocean2k.exr'
OUT = sys.argv[2] if len(sys.argv) > 2 else ROOT + '/3d/styleframe_ocean.png'
P = fast3d.load(EXR); H, W = P['I'].shape; S = W/1080
A = json.load(open(EXR.replace('.exr', '.json')))
def px(p): return (p[0]*W, p[1]*H)

bg = gradient_bg(H, W, '#0F2A4C', '#02050B')
bg += god_rays(H, W, 2, 0.24)[..., None]*hexrgb('#7FC4E8')[None, None]

u_pk = 0.0375
cab0 = [px(p) for p in A['cable']]; _p = cab0[int(u_pk*len(cab0))]
img = stylize_dark(P, bg, fog_k=22.0, pools=[(_p[0], _p[1], 170*S, GOLD, 0.55), (px(A['R1'])[0], px(A['R1'])[1], 90*S, CYAN, 0.25)])
# ---- the cable glows faintly; the message is a golden pulse inside it with a light trail ----
cab = [px(p) for p in A['cable']]
u_pk = 0.0375
n = len(cab); ipk = int(u_pk*n)
trail = [(x, y, 1.0, 0.25 + 0.75*(k/ipk)**2) for k, (x, y) in enumerate(cab[:ipk + 1])]
g = glow_layer(H, W, [(x, y, 0.6, 0.35) for x, y in cab[ipk:int(0.6*n)]], CYAN, 6*S, 0.5)
g += glow_layer(H, W, trail, GOLD, 9*S, 1.1)
pkx, pky = cab[ipk]
g += glow_layer(H, W, [(pkx, pky, 1.0, 1.0)], GOLD, 60*S, 1.3)
g += glow_layer(H, W, [(pkx, pky, 1.0, 1.0)], '#FFF4D8', 16*S, 2.2)
# repeater: a cyan status band
rx, ry = px(A['R1'])
g += glow_layer(H, W, [(rx, ry - 4*S, 1.0, 1.0)], CYAN, 22*S, 0.9)
img = img + g
# marine snow over everything, a little brighter up close
snow = marine_snow(H, W, 900, 5)
img = img + snow[..., None]*hexrgb('#BFE6F5')[None, None]*0.55
img = vignette(img, 0.6)
yb = np.linspace(0, 1, H)[:, None, None]
img = img*(1 - 0.55*np.clip((yb - 0.86)/0.14, 0, 1))
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')

# ---- overlay: editorial type, sonar ruler, callouts, route strip ----
O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
C = lambda c, a=255: tuple(int(v) for v in hexrgb(c)) + (a,)
fm = font(MONO, 13*S); fmm = font(MONO_M, 13*S); fsI = font(SERIF_I, 74*S); fs = font(SERIF, 25*S)
# the padlock riding in the pulse: the message is encrypted the whole way
lx, ly = pkx - 2*S, pky - 58*S
d.rounded_rectangle([lx - 15*S, ly - 3*S, lx + 15*S, ly + 21*S], radius=4*S, fill=C('#FFE3A3', 245))
d.arc([lx - 10*S, ly - 19*S, lx + 10*S, ly + 3*S], 180, 360, fill=C('#FFE3A3', 245), width=int(3.6*S))
d.ellipse([lx - 3*S, ly + 5*S, lx + 3*S, ly + 11*S], fill=C('#7A4A0A')); d.line([(lx, ly + 10*S), (lx, ly + 16*S)], fill=C('#7A4A0A'), width=int(2.4*S))
# top left chapter mark
d.text((48*S, 44*S), '05 / 08', font=fmm, fill=C('#FFFFFF', 200))
d.line([(118*S, 53*S), (170*S, 53*S)], fill=C(CYAN, 160), width=int(1*S))
d.text((180*S, 44*S), 'UNDER THE ATLANTIC', font=fm, fill=C('#CFEAF5', 200))
# top right elapsed counter
d.text((W - 48*S, 44*S), 'ELAPSED', font=fm, fill=C('#CFEAF5', 170), anchor='ra')
d.text((W - 48*S, 62*S), '≈ 0.06 s', font=font(MONO_M, 30*S), fill=C('#FFFFFF', 240), anchor='ra')
# depth ruler on the right
x0 = W - 40*S; y0, y1 = 150*S, 560*S
d.line([(x0, y0), (x0, y1)], fill=C('#CFEAF5', 110), width=int(1*S))
for k in range(0, 5001, 250):
    yy = y0 + (y1 - y0)*k/5000; big = k % 1000 == 0
    d.line([(x0 - (10 if big else 5)*S, yy), (x0, yy)], fill=C('#CFEAF5', 150 if big else 80), width=int(1*S))
    if big: d.text((x0 - 14*S, yy), f'{k:,} m', font=font(MONO, 11*S), fill=C('#CFEAF5', 150), anchor='rm')
ym = y0 + (y1 - y0)*3646/5000
d.polygon([(x0 + 3*S, ym), (x0 + 13*S, ym - 6*S), (x0 + 13*S, ym + 6*S)], fill=C(GOLD))
d.text((x0 - 62*S, ym), 'AVG. ATLANTIC DEPTH\n3,646 m', font=font(MONO, 10*S), fill=C(GOLD, 230), anchor='rm', align='right')
# callouts: thin leaders, mono labels
def callout(ax, ay, tx, ty, lines, align='la'):
    d.ellipse([ax - 4*S, ay - 4*S, ax + 4*S, ay + 4*S], outline=C('#FFFFFF', 220), width=int(1.4*S))
    ex = tx - 8*S if align == 'la' else tx + 8*S
    d.line([(ax, ay), (ax + (ex - ax)*0.35, ty + 8*S), (ex, ty + 8*S)], fill=C('#FFFFFF', 150), width=int(1*S))
    for i, (s, f, c) in enumerate(lines):
        d.text((tx if align == 'la' else tx, ty + i*18*S), s, font=f, fill=c, anchor=align)
callout(pkx + 10*S, pky + 4*S, 600*S, 800*S, [('YOUR MESSAGE', fmm, C(GOLD)), ('a pulse of light, still locked', fm, C('#E6F4FA', 210))])
callout(rx - 6*S, ry - 12*S, 520*S, 330*S, [('REPEATER', fmm, C(CYAN)), ('boosts the light every ~70 km', fm, C('#E6F4FA', 210))])
cx2, cy2 = cab[5]
callout(cx2 + 8*S, cy2, 330*S, 930*S, [('THE CABLE', fmm, C(CYAN)), ('about as thick as a garden hose', fm, C('#E6F4FA', 210))])
# title block, bottom left
d.text((46*S, 92*S), 'Under the Atlantic', font=fsI, fill=C('#FFFFFF', 245))
body = ['Lagos to Portugal: 6,900 km of cable', 'on the ocean floor. The pulse crosses it', 'in about 35 thousandths of a second.']
for i, s in enumerate(body): d.text((48*S, 186*S + i*30*S), s, font=fs, fill=C('#D8EDF6', 225))
# route strip along the bottom
nodes = ['PHONE', 'TOWER', 'STREET', 'COAST', 'OCEAN', 'SERVER', 'PHONE']
sx0, sx1, sy = 48*S, W - 48*S, H - 44*S
d.line([(sx0, sy), (sx1, sy)], fill=C('#CFEAF5', 60), width=int(1*S))
cur = 4.35
d.line([(sx0, sy), (sx0 + (sx1 - sx0)*cur/6, sy)], fill=C(GOLD, 220), width=int(2*S))
for i, nm in enumerate(nodes):
    x = sx0 + (sx1 - sx0)*i/6; done = i <= 4
    d.ellipse([x - 4*S, sy - 4*S, x + 4*S, sy + 4*S], fill=C(GOLD if done else '#0A1422'), outline=C(GOLD if done else '#CFEAF5', 220), width=int(1.2*S))
    d.text((x, sy - 12*S), nm, font=font(MONO, 10*S), fill=C('#FFFFFF' if i == 4 else '#CFEAF5', 240 if i == 4 else 130), anchor='md')
xk = sx0 + (sx1 - sx0)*cur/6
O2 = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(O2).ellipse([xk - 10*S, sy - 10*S, xk + 10*S, sy + 10*S], fill=C(GOLD, 200))
O = Image.alpha_composite(O2.filter(ImageFilter.GaussianBlur(6*S)), O)
ImageDraw.Draw(O).ellipse([xk - 3.5*S, sy - 3.5*S, xk + 3.5*S, sy + 3.5*S], fill=C('#FFF4D8'))
im.alpha_composite(O)
im.convert('RGB').resize((1080, 1080), Image.LANCZOS).save(OUT)
print('saved', OUT)
