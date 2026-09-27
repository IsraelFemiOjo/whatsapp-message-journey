"""Section 4 (13.3 to 18.6 s): pull back from the Lagos coast to the globe, the route lights up, then dive toward the pulse."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, os, json, math, numpy as np
sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
from sjcomp import *
from scene3d import catmull
from PIL import Image, ImageDraw, ImageFilter
from shapely.geometry import shape, Point, LineString, box as sbox
from shapely.ops import unary_union
from shapely.prepared import prep

land = unary_union([shape(f['geometry']) for f in json.load(open(ROOT + '/3d/geo/land50.geojson'))['features']])
# the 50m coastline is too coarse at street scale: square off the Lagos shore to match the straight beach in the coast shot
land = land.union(sbox(3.3, 6.409, 3.75, 6.6))
PL = prep(land)
LAGOS = (3.60, 6.385); BUDE = (-4.54, 50.83); LONDON = (-0.13, 51.51)
WAY = [LAGOS, (2.6, 5.6), (0.0, 4.9), (-3.5, 4.3), (-7.0, 3.9), (-10.2, 5.2), (-13.2, 8.0), (-16.4, 10.8), (-18.4, 13.4), (-18.6, 16.0),
       (-18.2, 19.5), (-17.6, 22.2), (-16.2, 24.6), (-14.4, 26.9), (-12.0, 29.4), (-10.6, 32.2), (-10.4, 35.3), (-10.5, 38.5),
       (-10.8, 41.8), (-10.2, 44.6), (-7.8, 47.2), (-5.9, 49.5), BUDE]
sm = catmull(WAY[:1] + WAY + WAY[-1:], 14)
ib = min(range(len(sm)), key=lambda i: (sm[i][0] - BUDE[0])**2 + (sm[i][1] - BUDE[1])**2); sm = sm[:ib + 1]
ROUTE = LineString(sm)
RPTS = np.array([ROUTE.interpolate(u, normalized=True).coords[0] for u in np.linspace(0, 1, 1500)])
# dot matrix land, precomputed
DOTS = []
for lat in np.arange(-12, 74, 0.42):
    for lon in np.arange(-45, 55, 0.42/math.cos(math.radians(lat))):
        if PL.contains(Point(lon, lat)): DOTS.append((lat, lon))
DOTS = np.array(DOTS)
RINGS = []
for g in (land.geoms if hasattr(land, 'geoms') else [land]):
    if g.bounds[2] < -50 or g.bounds[0] > 60 or g.bounds[3] < -15 or g.bounds[1] > 75: continue
    for r in [g.exterior] + list(g.interiors): RINGS.append(np.array(r.coords))
# city lights near Lagos for the close zoom
rng = np.random.default_rng(2)
def scatter(n, lon_c, lat_c, sd):
    pts = []
    while len(pts) < n:
        lon, lat = rng.normal(lon_c, sd*1.6), rng.normal(lat_c, sd)
        if PL.contains(Point(lon, lat)): pts.append((lat, lon))
    return np.array(pts)
CITY = np.concatenate([scatter(9000, 3.55, 6.45, 0.03), scatter(9000, 3.45, 6.52, 0.1), scatter(6000, 3.4, 6.6, 0.3)])
def ortho(lat, lon, lat0, lon0, R, cx, cy):
    la, lo = np.radians(lat), np.radians(lon); la0, lo0 = math.radians(lat0), math.radians(lon0)
    cosc = math.sin(la0)*np.sin(la) + math.cos(la0)*np.cos(la)*np.cos(lo - lo0)
    x = R*np.cos(la)*np.sin(lo - lo0)
    y = R*(math.cos(la0)*np.sin(la) - math.sin(la0)*np.cos(la)*np.cos(lo - lo0))
    return cx + x, cy - y, cosc

def pulse_u(t):
    return 0.42*seg(t, 14.5, 17.9)**1.25
def pulse_ll(t):
    if t < 14.0:   # still in the coast shot's frame: just off Lagos, heading south
        s2 = 1500*seg(t, 12.15, 14.0)**1.8
        return (LAGOS[0], 6.409 - 0.0006 - s2/111000.0)
    u = pulse_u(t); i = min(int(u*(len(RPTS) - 1)), len(RPTS) - 1)
    return tuple(RPTS[i])

def view(t, S):
    """camera over the globe: tight on Lagos, out to the whole route, then in again toward the pulse"""
    R_close = 1.365e6*S*(1.0 if t >= 14.0 else 1 + (14.0 - t)/0.7*0.73)
    R_wide = 1000*S
    out = ease(seg(t, 13.9, 15.4)); back_in = ease(seg(t, 17.7, 18.6))**1.5
    lr = math.log(R_close)*(1 - out) + math.log(R_wide)*out
    lr = lr*(1 - back_in) + math.log(60000*S)*back_in
    R = math.exp(lr)
    plon, plat = pulse_ll(t)
    wide_c = (27.5, -4.0)
    k = min(1.0, (R_wide/R))**1.5*(1 - back_in)*ease(seg(t, 13.9, 15.4))
    lat0 = plat*(1 - k) + wide_c[0]*k; lon0 = plon*(1 - k) + wide_c[1]*k
    return lat0, lon0, R

def render(fi, W=2160):
    H = W; S = W/1080
    t = 13.3 + fi/24
    lat0, lon0, R = view(t, S)
    cx, cy = W/2, H/2
    img = gradient_bg(H, W, '#081427', '#02040A', seed=4)
    yy, xx = np.mgrid[0:H, 0:W]
    rr = np.sqrt((xx - cx)**2 + (yy - cy)**2)
    if R < 20000*S:
        disc = rr < R
        img[disc] = img[disc]*0.6 + hexrgb('#0A1C33')*0.4
        img += (np.exp(-((rr - R)/(40*S))**2)*0.5)[..., None]*hexrgb('#3A7BB8')[None, None]*0.5
    else:
        img = img*0.6 + hexrgb('#0A1C33')*0.4
    # land: dot matrix when far, solid with city lights when close
    dotk = 1 - seg(math.log(R), math.log(2600*S), math.log(7000*S))
    D = Image.new('L', (W, H), 0); dd = ImageDraw.Draw(D)
    if dotk > 0:
        x, y, c = ortho(DOTS[:, 0], DOTS[:, 1], lat0, lon0, R, cx, cy)
        m = (c > 0.05) & (x > -10) & (x < W + 10) & (y > -10) & (y < H + 10)
        r = 1.9*S*(0.5 + 0.5*c[m])
        for xi, yi, ri, ci in zip(x[m], y[m], r, c[m]): dd.ellipse([xi - ri, yi - ri, xi + ri, yi + ri], fill=int((120 + 90*ci)*dotk))
    img += (np.array(D).astype(np.float32)/255)[..., None]*hexrgb('#7FAFC8')[None, None]*0.75
    # coastlines and land fill
    Cl = Image.new('L', (W, H), 0); dc = ImageDraw.Draw(Cl)
    Lf = Image.new('L', (W, H), 0); dlf = ImageDraw.Draw(Lf)
    for ring in RINGS:
        x, y, c = ortho(ring[:, 1], ring[:, 0], lat0, lon0, R, cx, cy)
        if c.max() <= 0: continue
        vis = c > 0
        if (x[vis].max() < -W or x[vis].min() > 2*W or y[vis].max() < -H or y[vis].min() > 2*H): continue
        segp = []
        for xi, yi, mi in zip(x, y, vis):
            if mi: segp.append((xi, yi))
            elif len(segp) > 1: dc.line(segp, fill=200, width=int(1.2*S*(1 + 1.5*(1 - dotk)))); segp = []
        if len(segp) > 1: dc.line(segp, fill=200, width=int(1.2*S*(1 + 1.5*(1 - dotk))))
    if dotk < 1:   # solid land when close: clip the land to the view and fill it
        ext = (W/2)/R*57.3*4.0
        vb = sbox(lon0 - ext/math.cos(math.radians(lat0)), lat0 - ext, lon0 + ext/math.cos(math.radians(lat0)), lat0 + ext)
        clip = land.intersection(vb)
        for gg in (clip.geoms if hasattr(clip, 'geoms') else [clip]):
            if gg.is_empty or gg.geom_type != 'Polygon': continue
            ex = np.array(gg.exterior.coords)
            x, y, c = ortho(ex[:, 1], ex[:, 0], lat0, lon0, R, cx, cy)
            dlf.polygon(list(zip(x, y)), fill=255)
    lf = np.array(Lf).astype(np.float32)/255*(1 - dotk)
    img = img*(1 - lf[..., None]*0.9) + hexrgb('#1C2436')[None, None]*lf[..., None]*0.9
    img += (np.array(Cl).astype(np.float32)/255)[..., None]*hexrgb('#9FD3EA')[None, None]*0.55
    if dotk < 1:   # city lights of Lagos
        x, y, c = ortho(CITY[:, 0], CITY[:, 1], lat0, lon0, R, cx, cy)
        m = (x > -20) & (x < W + 20) & (y > -20) & (y < H + 20)
        Ci = Image.new('RGB', (W, H)); dci = ImageDraw.Draw(Ci)
        rr_ = 1.3*S
        for k_, (xi, yi) in enumerate(zip(x[m], y[m])):
            col = (255, 196, 120) if k_ % 5 else (170, 205, 240)
            dci.ellipse([xi - rr_, yi - rr_, xi + rr_, yi + rr_], fill=col)
        img += np.array(Ci.filter(ImageFilter.GaussianBlur(1.2*S))).astype(np.float32)*0.55*(1 - dotk)
    # graticule when wide
    if R < 20000*S:
        G = Image.new('L', (W, H), 0); dg = ImageDraw.Draw(G)
        for lat in range(-60, 90, 10):
            lo = np.linspace(-80, 80, 300); x, y, c = ortho(np.full_like(lo, lat), lo, lat0, lon0, R, cx, cy); m = c > 0
            if m.sum() > 1: dg.line(list(zip(x[m], y[m])), fill=40, width=int(1*S))
        for lon in range(-60, 70, 10):
            la = np.linspace(-80, 85, 300); x, y, c = ortho(la, np.full_like(la, lon), lat0, lon0, R, cx, cy); m = c > 0
            if m.sum() > 1: dg.line(list(zip(x[m], y[m])), fill=40, width=int(1*S))
        img += (np.array(G).astype(np.float32)/255)[..., None]*hexrgb('#6FB7D6')[None, None]*0.6*dotk
    # the route: lit behind the pulse, faint dashes ahead
    plon, plat = pulse_ll(t)
    u = pulse_u(t)
    x, y, c = ortho(RPTS[:, 1], RPTS[:, 0], lat0, lon0, R, cx, cy)
    k = int(u*(len(RPTS) - 1))
    O = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(O)
    C = lambda cc, al=255: tuple(int(v) for v in hexrgb(cc)) + (int(al),)
    ahead_a = seg(t, 14.6, 15.4)
    for i in range(k, len(RPTS) - 8, 16):
        d.line([(x[i], y[i]), (x[i + 8], y[i + 8])], fill=C('#FFD58A', 110*ahead_a), width=int(1.4*S))
    px_, py_, _ = ortho(np.array([plat]), np.array([plon]), lat0, lon0, R, cx, cy); px_, py_ = float(px_[0]), float(py_[0])
    g = np.zeros((H, W, 3), np.float32)
    if t >= 14.0 and k > 1:
        g += glow_layer(H, W, [(x[i], y[i], 1.0, 0.35) for i in range(0, k, 2)], GOLD, 5*S, 0.7)
        Rt = Image.new('L', (W, H), 0); ImageDraw.Draw(Rt).line(list(zip(x[:k + 1], y[:k + 1])), fill=255, width=int(2.2*S), joint='curve')
        g += (np.array(Rt).astype(np.float32)/255)[..., None]*hexrgb('#FFD58A')[None, None]*0.9
    if t < 14.2:   # the short trail from the coast, before the route takes over
        lat_a = LAGOS[1] + 0.015; tr_x, tr_y, _ = ortho(np.linspace(lat_a, plat, 30), np.full(30, LAGOS[0]), lat0, lon0, R, cx, cy)
        g += glow_layer(H, W, [(a_, b_, 1.0, 0.2 + 0.8*(i/29)**2) for i, (a_, b_) in enumerate(zip(tr_x, tr_y))], GOLD, 7*S, 1.0)
    g += glow_layer(H, W, [(px_, py_, 1, 1)], GOLD, 55*S, 1.3) + glow_layer(H, W, [(px_, py_, 1, 1)], '#FFF4D8', 12*S, 2.4)
    img = img + g
    # sinking toward the water at the end: the map darkens into the sea
    sink = ease(seg(t, 18.05, 18.6))
    img = img*(1 - sink) + gradient_bg(H, W, '#0F2A4C', '#02050B', seed=7)*sink
    img = vignette(img, 0.5)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')
    # places and labels, once the view is wide
    la = seg(t, 15.0, 15.5)*(1 - seg(t, 17.6, 17.9))
    def place(ll, name, sub, dx, dy, anchor='la', dot=GOLD):
        xx_, yy_, cc = ortho(np.array([ll[1]]), np.array([ll[0]]), lat0, lon0, R, cx, cy); xq, yq = float(xx_[0]), float(yy_[0])
        d.ellipse([xq - 5*S, yq - 5*S, xq + 5*S, yq + 5*S], fill=C('#0A1422', 255*la), outline=C(dot, 255*la), width=int(2*S))
        d.text((xq + dx*S, yq + dy*S), name, font=font(MONO_M, 15*S), fill=C('#FFFFFF', 240*la), anchor=anchor)
        if sub: d.text((xq + dx*S, yq + (dy + 20)*S), sub, font=font(MONO, 11*S), fill=C('#CFEAF5', 170*la), anchor=anchor)
    if la > 0:
        place((3.39, 6.45), 'LAGOS', '', 14, -8)
        place(BUDE, 'BUDE, UK', 'cable lands', -14, 4, 'ra', dot=CYAN)
        place(LONDON, 'LONDON', '', 14, -14)
        bx, by, _ = ortho(np.array([BUDE[1]]), np.array([BUDE[0]]), lat0, lon0, R, cx, cy); lx_, ly_, _ = ortho(np.array([LONDON[1]]), np.array([LONDON[0]]), lat0, lon0, R, cx, cy)
        for i in range(0, 10, 2):
            t0, t1 = i/10, (i + 1)/10
            d.line([(bx[0] + (lx_[0] - bx[0])*t0, by[0] + (ly_[0] - by[0])*t0), (bx[0] + (lx_[0] - bx[0])*t1, by[0] + (ly_[0] - by[0])*t1)], fill=C('#FFD58A', 200*la), width=int(1.6*S))
        fade_text(d, (48*S, H - 64*S), 'Route drawn close to the coast. Exact cable path simplified.', font(MONO, 10*S), '#CFEAF5', 0.45*la)
    ha = inout(t, 15.4, 17.6)
    if ha > 0:
        lx0, ly0 = 60*S, 380*S
        d.line([(px_ - 12*S, py_ - 6*S), (lx0 + 300*S, ly0 + 70*S), (lx0, ly0 + 70*S)], fill=C('#FFFFFF', 150*ha), width=int(1*S))
        fade_text(d, (lx0, ly0 + 24*S), 'It goes under the sea.', font(SERIF_I, 34*S), '#FFFFFF', ha)
        fade_text(d, (lx0 + 2*S, ly0 + 82*S), 'Along the coast of West Africa to the UK.', font(MONO, 12*S), '#CFEAF5', ha)
    fade_text(d, (48*S, 880*S), 'Out to sea.', font(SERIF_I, 44*S), '#FFFFFF', inout(t, 13.4, 14.6))
    el = 0.009 + 0.004*seg(t, 13.3, 14.0) + 0.02*seg(t, 14.0, 18.6)
    header(d, W, S, C, '04 / 08' if t < 14.9 else '05 / 08', 'THE COAST' if t < 14.9 else 'THE ROUTE', f'≈ {el:.3f} s')
    cur = 3.0 + seg(t, 15.0, 18.6)
    kx, ky = route_strip(d, W, H, S, cur, C)
    d.ellipse([kx - 3.5*S, ky - 3.5*S, kx + 3.5*S, ky + 3.5*S], fill=C('#FFF4D8'))
    im = halo_composite(im, O, S, col=(4, 8, 16))
    return im.convert('RGB').resize((1080, 1080), Image.LANCZOS)

if __name__ == '__main__':
    out = ROOT + '/3d/fr/s4'; os.makedirs(out, exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    for fi in range(a, b):
        render(fi).save(f'{out}/{fi:04d}.png')
