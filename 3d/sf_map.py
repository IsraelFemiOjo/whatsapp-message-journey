"""Style frame: the map moment. Dark orthographic globe, dot matrix land, one route lit Lagos to the UK."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
from deep import *
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import shape, Point, LineString
from shapely.ops import unary_union
from shapely.prepared import prep

W = H = 2160; S = W/1080
LAT0, LON0 = 29.0, -4.0          # globe centre
R = 1000*S; CX, CY = 560*S, 560*S

def ortho(lat, lon):
    la, lo = np.radians(lat), np.radians(lon); la0, lo0 = math.radians(LAT0), math.radians(LON0)
    cosc = math.sin(la0)*np.sin(la) + math.cos(la0)*np.cos(la)*np.cos(lo - lo0)
    x = R*np.cos(la)*np.sin(lo - lo0)
    y = R*(math.cos(la0)*np.sin(la) - math.sin(la0)*np.cos(la)*np.cos(lo - lo0))
    return CX + x, CY - y, cosc

land = [shape(f['geometry']) for f in json.load(open(ROOT + '/3d/geo/land50.geojson'))['features']]
L = unary_union(land); PL = prep(L)

# ---- background: deep space navy, globe disc with a soft atmosphere ----
img = gradient_bg(H, W, '#081427', '#02040A', seed=4)
yy, xx = np.mgrid[0:H, 0:W]
rr = np.sqrt((xx - CX)**2 + (yy - CY)**2)
disc = rr < R
img[disc] = img[disc]*0.6 + hexrgb('#0A1C33')*0.4
atm = np.exp(-((rr - R)/(40*S))**2)*0.5
img += atm[..., None]*hexrgb('#3A7BB8')[None, None]*0.5

# graticule, faint
G = Image.new('L', (W, H), 0); dg = ImageDraw.Draw(G)
for lat in range(-60, 90, 10):
    lo = np.linspace(-80, 80, 400); x, y, c = ortho(np.full_like(lo, lat), lo); m = c > 0
    pts = list(zip(x[m], y[m]));
    if len(pts) > 1: dg.line(pts, fill=40, width=int(1*S))
for lon in range(-60, 70, 10):
    la = np.linspace(-80, 85, 400); x, y, c = ortho(la, np.full_like(la, lon)); m = c > 0
    pts = list(zip(x[m], y[m]))
    if len(pts) > 1: dg.line(pts, fill=40, width=int(1*S))
img += (np.array(G).astype(np.float32)/255)[..., None]*hexrgb('#6FB7D6')[None, None]*0.6

# dot matrix land
D = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(D)
step = 0.42
for lat in np.arange(-10, 72, step):
    for lon in np.arange(-40, 50, step/math.cos(math.radians(lat))):
        if not PL.contains(Point(lon, lat)): continue
        x, y, c = ortho(lat, lon)
        if c <= 0.05: continue
        r = 1.9*S*(0.5 + 0.5*c)
        dd.ellipse([x - r, y - r, x + r, y + r], fill=int(120 + 90*c))
img += (np.array(D).astype(np.float32)/255)[..., None]*hexrgb('#7FAFC8')[None, None]*0.75

# coastlines, thin
C = Image.new('L', (W, H), 0); dc = ImageDraw.Draw(C)
geoms = L.geoms if hasattr(L, 'geoms') else [L]
for g in geoms:
    for ring in [g.exterior] + list(g.interiors):
        lon, lat = np.array(ring.coords).T
        x, y, c = ortho(lat, lon); m = c > 0
        seg = []
        for xi, yi, mi in zip(x, y, m):
            if mi: seg.append((xi, yi))
            elif len(seg) > 1: dc.line(seg, fill=150, width=int(1.2*S)); seg = []
        if len(seg) > 1: dc.line(seg, fill=150, width=int(1.2*S))
img += (np.array(C).astype(np.float32)/255)[..., None]*hexrgb('#9FD3EA')[None, None]*0.55

# ---- the route: offshore, following the coast, Lagos to Bude (approximate) ----
LAGOS = (3.39, 6.45); BUDE = (-4.54, 50.83); LONDON = (-0.13, 51.51)
WAY = [LAGOS, (2.6, 5.6), (0.0, 4.9), (-3.5, 4.3), (-7.0, 3.9), (-10.2, 5.2), (-13.2, 8.0), (-16.4, 10.8), (-18.4, 13.4), (-18.6, 16.0),
       (-18.2, 19.5), (-17.6, 22.2), (-16.2, 24.6), (-14.4, 26.9), (-12.0, 29.4), (-10.6, 32.2), (-10.4, 35.3), (-10.5, 38.5),
       (-10.8, 41.8), (-10.2, 44.6), (-7.8, 47.2), (-5.9, 49.5), BUDE]
from scene3d import catmull
sm = catmull(WAY[:1] + WAY + WAY[-1:], 12)
ib = min(range(len(sm)), key=lambda i: (sm[i][0] - BUDE[0])**2 + (sm[i][1] - BUDE[1])**2)
sm = sm[:ib + 1]
dense = LineString(sm)
bad = [p for p in WAY[1:-1] if L.contains(Point(*p))]
print('waypoints on land:', bad)
pts = [dense.interpolate(t, normalized=True).coords[0] for t in np.linspace(0, 1, 700)]
rx, ry, rc = ortho(np.array([p[1] for p in pts]), np.array([p[0] for p in pts]))
u_pk = 0.62
k = int(u_pk*len(pts))
glow = glow_layer(H, W, [(x, y, 1.0, 0.35) for x, y in zip(rx, ry)], GOLD, 5*S, 0.7)
glow += glow_layer(H, W, [(x, y, 1.0, 0.25 + 0.75*(i/k)**3) for i, (x, y) in enumerate(zip(rx[:k], ry[:k]))], GOLD, 8*S, 1.2)
glow += glow_layer(H, W, [(rx[k], ry[k], 1, 1)], GOLD, 55*S, 1.4)
glow += glow_layer(H, W, [(rx[k], ry[k], 1, 1)], '#FFF4D8', 12*S, 2.4)
img = img + glow
Rt = Image.new('L', (W, H), 0); ImageDraw.Draw(Rt).line(list(zip(rx, ry)), fill=255, width=int(2.2*S), joint='curve')
img += (np.array(Rt).astype(np.float32)/255)[..., None]*hexrgb('#FFD58A')[None, None]*0.9
# London leg: last stretch overland, dashed
lx0, ly0, _ = ortho(BUDE[1], BUDE[0]); lx1, ly1, _ = ortho(LONDON[1], LONDON[0])
img = vignette(img, 0.5)
im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
Cc = lambda c, a=255: tuple(int(v) for v in hexrgb(c)) + (a,)
for i in range(0, 10, 2):
    t0, t1 = i/10, (i + 1)/10
    d.line([(lx0 + (lx1 - lx0)*t0, ly0 + (ly1 - ly0)*t0), (lx0 + (lx1 - lx0)*t1, ly0 + (ly1 - ly0)*t1)], fill=Cc('#FFD58A', 200), width=int(1.6*S))
def place(lonlat, name, sub, dx, dy, anchor='la', dot=GOLD):
    x, y, _ = ortho(lonlat[1], lonlat[0])
    d.ellipse([x - 5*S, y - 5*S, x + 5*S, y + 5*S], fill=Cc('#0A1422'), outline=Cc(dot), width=int(2*S))
    d.text((x + dx*S, y + dy*S), name, font=font(MONO_M, 15*S), fill=Cc('#FFFFFF', 240), anchor=anchor)
    if sub: d.text((x + dx*S, y + (dy + 20)*S), sub, font=font(MONO, 11*S), fill=Cc('#CFEAF5', 170), anchor=anchor)
place(LAGOS, 'LAGOS', 'you, 0.000 s', 14, -8)
place(BUDE, 'BUDE, UK', 'cable lands', -14, 4, 'ra', dot=CYAN)
place(LONDON, 'LONDON', 'your friend', 14, -14)
# chapter + timer
d.text((48*S, 44*S), '06 / 09', font=font(MONO_M, 13*S), fill=Cc('#FFFFFF', 200))
d.line([(118*S, 53*S), (170*S, 53*S)], fill=Cc(CYAN, 160), width=int(1*S))
d.text((180*S, 44*S), 'THE ROUTE', font=font(MONO, 13*S), fill=Cc('#CFEAF5', 200))
d.text((W - 48*S, 44*S), 'ELAPSED', font=font(MONO, 13*S), fill=Cc('#CFEAF5', 170), anchor='ra')
d.text((W - 48*S, 62*S), '≈ 0.05 s', font=font(MONO_M, 30*S), fill=Cc('#FFFFFF', 240), anchor='ra')
# one plain label, on the thing it names
px_, py_ = rx[k], ry[k]
d.line([(px_ - 14*S, py_ + 6*S), (px_ - 110*S, py_ + 70*S), (px_ - 330*S, py_ + 70*S)], fill=Cc('#FFFFFF', 150), width=int(1*S))
d.text((px_ - 330*S, py_ + 24*S), 'It goes under the sea.', font=font(SERIF_I, 34*S), fill=Cc('#FFFFFF', 245))
d.text((px_ - 328*S, py_ + 82*S), 'Along the coast of West Africa to the UK.', font=font(MONO, 12*S), fill=Cc('#CFEAF5', 210))
d.text((48*S, H - 40*S), 'Route drawn close to the coast. Exact cable path simplified.', font=font(MONO, 10*S), fill=Cc('#CFEAF5', 110))
halo = Image.new('RGBA', (W, H), (0, 0, 0, 0)); halo.putalpha(O.split()[3].filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(8*S)))
halo = Image.merge('RGBA', (*Image.new('RGB', (W, H), (4, 8, 16)).split(), halo.split()[3].point(lambda v: int(v*0.85))))
im.alpha_composite(halo)
im.alpha_composite(O)
im.convert('RGB').resize((1080, 1080), Image.LANCZOS).save(ROOT + '/3d/styleframe_map.png')
print('ok', len(pts))
