"""WhatsApp send journey, cartoon version. Every scene is drawn in code with skia."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, os, json, math, numpy as np, skia
from PIL import Image
from toon import *
from props import *
from props import _path

FPS = 30
VOICE = os.environ.get('VOICE', 'am_puck')
WORDS = json.load(open(ROOT + f'/cartoon-version/words_{VOICE}.json'))
END = WORDS[-1]['e'] + 1.1
LINES = {}
for w in WORDS: LINES.setdefault(w['line'], []).append(w)
T = {k: v[0]['s'] for k, v in LINES.items()}
def wt(line, sub, n=0):
    """start time of the n-th word in a line containing sub"""
    hits = [w for w in LINES[line] if sub.lower() in w['w'].lower()]
    return hits[min(n, len(hits) - 1)]['s']

# captions: short chunks, broken at punctuation, one highlighted key per chunk
KEYS = {0: ['whatsapp'], 1: ['lagos', 'london'], 2: ['locks', 'friend', 'whatsapp'], 3: ['radio', 'waves', 'tower'], 4: ['light', 'glass'],
        5: ['ocean'], 6: ['guess', 'far'], 7: ['six', 'thousand', 'kilometers', 'garden', 'hose'], 8: ['repeater', 'boosts'],
        9: ['server', 'grey', 'tick', "can't"], 10: ['unlocks', 'two', 'grey', 'ticks'], 11: ['second']}
ch = 0; cnt = 0
for i, w in enumerate(WORDS):
    if i and (WORDS[i - 1]['line'] != w['line'] or cnt >= 3 or WORDS[i - 1]['w'][-1] in '.,!?'):
        ch += 1; cnt = 0
    w['chunk'] = ch; cnt += 1
    base = w['w'].lower().strip('.,!?')
    w['key'] = any(base.startswith(k) for k in KEYS.get(w['line'], []))
# only one key per chunk: keep the first
seen = set()
for w in WORDS:
    if w['key']:
        if w['chunk'] in seen and not (w['line'] in (7, 9, 10)): w['key'] = False
        seen.add(w['chunk'])

GRAIN = [np.random.default_rng(i).normal(0, 2.2, (H, W, 1)).astype(np.float32) for i in range(4)]

def cam(c, cx, cy, z, rot=0.0):
    c.translate(W/2, H/2); c.scale(z, z); c.rotate(rot); c.translate(-cx, -cy)

def burst_bg(c, t, a='#FF9A62', b='#FF5E8A', cx=540, cy=470):
    c.drawRect(skia.Rect.MakeWH(W, H), RG(cx, cy, 900, [mix(a, '#FFFFFF', 0.25), a, b], [0, 0.45, 1]))
    for i in range(16):
        ang = i*math.pi*2/16 + t*0.15
        poly(c, [(cx, cy), (cx + math.cos(ang)*1500, cy + math.sin(ang)*1500), (cx + math.cos(ang + 0.11)*1500, cy + math.sin(ang + 0.11)*1500)], P('#FFFFFF', 0.07))

def stopwatch(c, x, y, s, t, a=1.0, txt=None):
    c.save(); c.translate(x, y); c.scale(s, s)
    circ(c, 4, 10, 92, P('#000000', 0.2*a, blur=10))
    rr(c, -18, -118, 36, 26, 8, P('#FF4D6D', a)); rr(c, -8, -98, 16, 16, 4, P('#C9D3DF', a))
    circ(c, 0, 0, 92, P('#FF4D6D', a)); circ(c, 0, 0, 74, P('#FFFFFF', a))
    for i in range(12):
        an = i*math.pi/6; c.drawLine(math.sin(an)*60, -math.cos(an)*60, math.sin(an)*68, -math.cos(an)*68, P(INK, a, stroke=5))
    an = t*math.pi*2*1.4
    c.drawLine(0, 0, math.sin(an)*56, -math.cos(an)*56, P('#FF4D6D', a, stroke=8)); circ(c, 0, 0, 9, P(INK, a))
    if txt: text(c, txt, 0, 150, 44, '#FFFFFF', 'Black', 'c', stroke=12, stroke_c=INK, a=a)
    c.restore()

def thumb(c, x, y, s=1.0, a=1.0):
    """a thumb coming in from the lower right, tip at x,y"""
    c.save(); c.translate(x, y); c.rotate(-32); c.scale(s, s)
    rr(c, -46, -10, 92, 420, 46, P('#000000', 0.18*a, blur=12))
    rr(c, -50, -20, 100, 420, 50, LG(-50, 0, 50, 0, ['#A86B45', '#8A5230'], a=a))
    rr(c, -32, -8, 64, 78, 30, P('#D9A07E', a)); rr(c, -24, 0, 22, 40, 11, P('#FFFFFF', 0.3*a))
    c.drawLine(-40, 120, 40, 120, P('#6E3F24', 0.35*a, stroke=4))
    c.restore()

def question_marks(c, x, y, k, t):
    for i, (dx, dy, r) in enumerate(((-250, -40, -18), (230, 110, 22))):
        kk = back(seg(k, i*0.12, i*0.12 + 0.5), 2.2)
        if kk <= 0: continue
        c.save(); c.translate(x + dx, y + dy + math.sin(t*4 + i)*8); c.rotate(r); c.scale(kk, kk)
        text(c, '?', 0, 30, 110, '#FFFFFF', 'Black', 'c', stroke=18, stroke_c=INK)
        c.restore()

# ================= scene 0: the hook =================
def s_hook(c, t):
    burst_bg(c, t)
    k_in = eout(seg(t, -0.2, 0.2))
    press_t = 0.42
    PX, PS = 330, 0.95
    ph_y = 425 + (1 - k_in)*600
    rot = -8 + 2*math.sin(t*1.3)
    sent = seg(t, press_t + 0.08, press_t + 0.4)
    phone(c, PX, ph_y, PS, rot, chat_screen(sent=sent, ticks=0, press=seg(t, press_t - 0.08, press_t + 0.12)/1.0, name='Kemi'))
    # thumb comes down on send, then away
    a_ = math.radians(rot)
    lx, ly = 118*PS, 310*PS
    bx, by = PX + lx*math.cos(a_) - ly*math.sin(a_), ph_y + lx*math.sin(a_) + ly*math.cos(a_)
    th = seg(t, 0.0, press_t) if t < press_t else 1 - seg(t, press_t + 0.1, press_t + 0.45)
    thumb(c, bx + 10 + (1 - eout(th))*300, by - 4 + (1 - eout(th))*260, 1.05, a=1.0)
    # the message jumps out of the phone, big, right beside it
    k = seg(t, press_t + 0.12, press_t + 0.7)
    if k > 0:
        bxk = lerp(PX + 60, 740, eout(k)); byk = lerp(ph_y - 100, 400, eout(k)) - math.sin(math.pi*k)*120
        sq = 1 + 0.25*math.sin(math.pi*seg(t, press_t + 0.12, press_t + 0.45))*(1 if k < 1 else 0)
        bubble(c, bxk, byk + math.sin(t*3)*6, 1.2*back(k, 2.0), look=(-0.5 + 0.3*math.sin(t*2), -0.2), blink=(2.35 < t < 2.47), happy=0.7, squash=1/sq, rot=12*(1 - eout(k)))
        question_marks(c, 740, 420, seg(t, 1.0, 1.8), t)
    sw = back(seg(t, wt(0, 'second') - 0.1, wt(0, 'second') + 0.3), 2.2)
    if sw > 0: stopwatch(c, 900, 150, 0.85*sw, t, txt='1 SEC')

# ================= scene 1: the map, Lagos to London =================
POLYS = json.load(open(ROOT + '/cartoon-version/map_polys.json'))
LAGOS = (3.39, 6.45); LONDON = (-0.13, 51.5); BUDE = (-4.54, 50.83)
def mproj(lon, lat): return lon*16, -lat*18.5
def map_draw(c, cx, cy, z, t, route_k=0.0, pins=(1, 1), route_col='#FFD60A', show_labels=1.0, far=False):
    c.drawRect(skia.Rect.MakeWH(W, H), LG(0, 0, 0, H, ['#3FA9F5', '#1E78D1']))
    c.save(); cam(c, *mproj(cx, cy), z)
    # soft wave lines on the sea
    for i in range(-30, 30):
        y = i*80
        c.drawLine(-2000, y, 2000, y, P('#FFFFFF', 0.05, stroke=3/z))
    for poly_ in POLYS:
        pts = [mproj(x, y) for x, y in poly_]
        p = skia.Path(); p.moveTo(*pts[0])
        for q in pts[1:]: p.lineTo(*q)
        p.close()
        c.save(); c.translate(6/z, 10/z); c.drawPath(p, P('#0E4F99', 0.45)); c.restore()
        c.drawPath(p, P('#8BE39A'))
        c.drawPath(p, P('#FFFFFF', 0.55, stroke=3/z))
    # route: along the west coast of Africa up to the UK
    if route_k > 0:
        way = [LAGOS, (2.0, 5.2), (-2, 4.2), (-8, 4.2), (-13.5, 7.5), (-17.8, 12.5), (-18.8, 18), (-17.6, 23), (-14.8, 27.5), (-11.6, 31.5),
               (-10.6, 36), (-10.8, 42), (-9.6, 46.5), (-6.6, 49.6), BUDE]
        pts = [mproj(*p) for p in way]
        path = skia.Path(); path.moveTo(*pts[0])
        for q in pts[1:]: path.lineTo(*q)
        pm = skia.PathMeasure(path, False); L = pm.getLength(); dst = skia.Path(); pm.getSegment(0, L*route_k, dst, True)
        c.drawPath(dst, P('#000000', 0.25, stroke=14/z, blur=4/z))
        c.drawPath(dst, P(route_col, stroke=10/z))
        pos, tan = pm.getPosTan(L*route_k)
        glow(c, pos.x(), pos.y(), 60/z, '#FFF3B0', 0.9); circ(c, pos.x(), pos.y(), 12/z, P('#FFFFFF'))
        # land leg to London
        lk = seg(route_k, 0.97, 1.0)
        if lk > 0:
            a0 = mproj(*BUDE); a1 = mproj(*LONDON)
            c.drawLine(a0[0], a0[1], lerp(a0[0], a1[0], lk), lerp(a0[1], a1[1], lk), P(route_col, stroke=8/z))
    for (ll, name, k) in ((LAGOS, 'LAGOS', pins[0]), (LONDON, 'LONDON', pins[1])):
        if k <= 0: continue
        x, y = mproj(*ll); kk = back(k, 2.4)
        c.save(); c.translate(x, y); c.scale(kk/z, kk/z)
        shadow(c, 0, 4, 40, 12, 0.3, 4)
        p = skia.Path(); p.moveTo(0, 0); p.cubicTo(-40, -50, -34, -96, 0, -96); p.cubicTo(34, -96, 40, -50, 0, 0); p.close()
        c.drawPath(p, P('#FF3D6E')); circ(c, 0, -62, 16, P('#FFFFFF'))
        if show_labels > 0: label(c, name, 170 if name == 'LONDON' else -170, -60, 44, '#FFFFFF', INK, k=show_labels)
        c.restore()
    c.restore()

def s_map1(c, t):
    t0 = T[1]
    zo = eio(seg(t, t0 - 0.12, t0 + 0.55))
    z = lerp(7.0, 0.95, zo)
    cx = lerp(LAGOS[0], 6.0, zo); cy = lerp(LAGOS[1], 27.0, zo)
    zi = ein(seg(t, T[2] - 0.35, T[2] + 0.05))
    z = z*(1 + 12*zi); cx = lerp(cx, LAGOS[0], min(1, zi*3)); cy = lerp(cy, LAGOS[1], min(1, zi*3))
    lon_k = seg(t, wt(1, 'london') - 0.1, wt(1, 'london') + 0.25)
    arc_k = eio(seg(t, wt(1, 'lagos') + 0.1, wt(1, 'london') + 0.3))
    map_draw(c, cx, cy, z, t, pins=(seg(t, t0 - 0.1, t0 + 0.2), lon_k), show_labels=1.0)
    # a dashed arc: the trip we are about to follow
    c.save(); cam(c, *mproj(cx, cy), z)
    a0 = mproj(*LAGOS); a1 = mproj(*LONDON)
    mid = ((a0[0] + a1[0])/2 - 260, (a0[1] + a1[1])/2)
    path = skia.Path(); path.moveTo(a0[0], a0[1] - 60); path.quadTo(mid[0], mid[1], a1[0], a1[1] - 60)
    pm = skia.PathMeasure(path, False); L = pm.getLength(); dst = skia.Path(); pm.getSegment(0, L*arc_k, dst, True)
    pp = P('#FFFFFF', stroke=9/z); pp.setPathEffect(skia.DashPathEffect.Make([26/z, 20/z], -t*80/z)); c.drawPath(dst, pp)
    c.restore()
    # our message rides the top of the Lagos pin
    x, y = mproj(*LAGOS)
    sx = W/2 + (x - mproj(cx, cy)[0])*z; sy = H/2 + (y - mproj(cx, cy)[1])*z
    bk = back(seg(t, t0, t0 + 0.4), 2)
    if bk > 0: bubble(c, sx + 150, sy - 120, 0.5*bk, look=(-0.6, -0.9) if lon_k > 0 else (-0.6, 0.3), happy=0.8, blink=(4.6 < t < 4.7))
    if zi > 0: c.drawRect(skia.Rect.MakeWH(W, H), P('#FFFFFF', 0.9*seg(zi, 0.6, 1.0)))

# ================= scene 2: locked =================
def lagos_skyline(c, base, cols, seed=1, windows=False, dx=0.0):
    r_ = np.random.default_rng(seed); x = -60 + dx
    while x < W + 60:
        w = r_.uniform(90, 170); h = r_.uniform(160, 420)
        building(c, x, base, w, h, cols[int(r_.integers(len(cols)))], seed=int(r_.integers(999)), windows=windows, roof='tank' if r_.random() < 0.3 else 'flat')
        x += w + r_.uniform(-10, 20)

def server_guy(c, x, y, s=1.0, t=0.0, look=(0, 0), squint=0.0, mag=0.0, sweat=0.0, happy=0.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    shadow(c, 0, 150, 220, 26, 0.25, 10)
    rr(c, -110, -140, 220, 280, 36, LG(0, -140, 0, 140, ['#B8C4D6', '#7F8DA3']))
    rr(c, -92, -122, 184, 20, 10, P('#FFFFFF', 0.3))
    for i in range(3):
        rr(c, -86, 40 + i*30, 172, 20, 8, P('#5E6B80'))
        circ(c, 66, 50 + i*30, 5, P('#39E07A' if (int(t*6) + i) % 3 else '#FFD60A'))
    for sx in (-1, 1):
        ex = sx*44
        h_ = 44*(1 - 0.75*squint)
        c.drawOval(skia.Rect.MakeXYWH(ex - 22, -58 - h_/2, 44, h_), P('#FFFFFF'))
        circ(c, ex + 8*look[0], -58 + 6*look[1], min(12, h_/2.4), P(INK))
    m = skia.Path(); m.moveTo(-26, 4); m.quadTo(0, 4 + 20*happy - 10*(1 - happy)*squint, 26, 4); c.drawPath(m, P(INK, stroke=8))
    if sweat > 0:
        d = skia.Path(); d.moveTo(96, -110); d.cubicTo(80, -84, 84, -66, 98, -66); d.cubicTo(112, -66, 114, -84, 96, -110)
        c.save(); c.translate(0, 30*sweat); c.drawPath(d, P('#7FD3FF', min(1, sweat*3))); c.restore()
    if mag > 0:
        c.save(); c.translate(-150 + 30*mag, -30); c.rotate(-20); c.scale(back(min(1, mag*1.5)), back(min(1, mag*1.5)))
        c.drawLine(0, 40, -40, 120, P('#6B4A2B', stroke=22)); circ(c, 0, 0, 58, P('#FFFFFF', 0.4)); circ(c, 0, 0, 58, P(INK, stroke=12))
        c.restore()
    c.restore()

def card(c, x, y, s, textv, k=1.0, bg='#FFFFFF', fg=INK, size=40, mono=False):
    if k <= 0: return
    f = font(size, 'ExtraBold'); tw = f.measureText(textv)
    kk = back(k, 2.0)
    c.save(); c.translate(x, y); c.scale(s*kk, s*kk)
    rr(c, -tw/2 - 30, -46 + 8, tw + 60, 92, 26, P('#000000', 0.25, blur=8))
    rr(c, -tw/2 - 30, -46, tw + 60, 92, 26, P(bg))
    c.drawString(textv, -tw/2, size*0.36, f, P(fg))
    c.restore()

SCR = '#k9@!f %2Lx&Q'
def scrambled(k, seed):
    base = 'Hello from Lagos!'
    r_ = np.random.default_rng(seed)
    return ''.join(ch if (ch == ' ' or i/len(base) >= k) else '#%&@$*!?'[int(r_.integers(8))] for i, ch in enumerate(base))

def s_lock(c, t):
    t0 = T[2]
    c.drawRect(skia.Rect.MakeWH(W, H), LG(0, 0, 0, H, ['#7C5CFF', '#FF8FB1']))
    lagos_skyline(c, H + 20, ['#9A7BFF', '#B58CFF', '#FFA3C4'], seed=11)
    zk = eout(seg(t, t0 - 0.05, t0 + 0.45))
    z = lerp(2.2, 1.0, zk)
    c.save(); c.translate(W/2, H/2); c.scale(z, z); c.translate(-W/2, -H/2)
    lock_t = wt(2, 'locks')
    lk = seg(t, lock_t - 0.05, lock_t + 0.35)
    imp = math.exp(-((t - lock_t - 0.3)/0.08)**2) if t > lock_t else 0
    bx, by = 540, 380 + math.sin(t*2.6)*6
    bubble(c, bx, by, 1.25, look=(0.0, -0.9) if lk < 1 else (0.2, 0.3), happy=0.5 - 0.3*imp, squash=1 - 0.18*imp, blink=(t0 + 2.6 < t < t0 + 2.7), locked=lk)
    # the words inside become gibberish the moment it is locked
    sk = seg(t, lock_t + 0.25, lock_t + 0.9)
    msg = scrambled(sk, int(t*10)) if 0 < sk < 1 else ('Hello from Lagos!' if sk <= 0 else SCR)
    card(c, 540, 660, 1.0, msg, k=seg(t, t0 - 0.1, t0 + 0.2), bg='#FFFFFF' if sk < 1 else '#1B2A4A', fg=INK if sk < 1 else '#FFD60A', size=46)
    c.restore()
    # you and your friend hold the only keys
    fk = seg(t, wt(2, 'only') - 0.1, wt(2, 'only') + 0.3)
    for i, (x, name, colr) in enumerate(((170, 'YOU', '#FFB547'), (910, 'FRIEND', '#4ECDC4'))):
        kk = back(seg(fk, i*0.25, i*0.25 + 0.6), 2.2)
        if kk <= 0: continue
        c.save(); c.translate(x, 470); c.scale(kk, kk)
        circ(c, 0, 8, 86, P('#000000', 0.2, blur=8)); circ(c, 0, 0, 86, P(colr))
        circ(c, 0, -22, 30, P('#FFFFFF', 0.95)); rr(c, -46, 16, 92, 50, 25, P('#FFFFFF', 0.95))
        text(c, name, 0, 138, 38, '#FFFFFF', 'Black', 'c', stroke=10, stroke_c=INK)
        # key
        c.save(); c.translate(56, -60); c.rotate(-30 + 8*math.sin(t*5))
        glow(c, 0, 0, 60, '#FFE066', 0.7); circ(c, 0, 0, 20, P('#FFD34E')); circ(c, 0, 0, 8, P(colr)); rr(c, 14, -6, 44, 12, 5, P('#FFD34E')); rr(c, 44, 0, 8, 16, 3, P('#FFD34E'))
        c.restore(); c.restore()
    # WhatsApp's own server takes a look and sees nothing it can read
    nk = seg(t, wt(2, 'whatsapp', 0) - 0.15, wt(2, 'whatsapp', 0) + 0.3)
    if nk > 0:
        sy = lerp(1300, 790, eout(nk))
        server_guy(c, 900, sy, 0.62, t, look=(-1, -0.6), squint=0.6, mag=seg(t, wt(2, 'whatsapp') + 0.1, wt(2, 'whatsapp') + 0.5), sweat=seg(t, wt(2, 'whatsapp') + 0.4, T[3]))
        c.save(); c.translate(900, sy - 150); c.scale(back(seg(t, wt(2, 'whatsapp') + 0.3, wt(2, 'whatsapp') + 0.6)), back(seg(t, wt(2, 'whatsapp') + 0.3, wt(2, 'whatsapp') + 0.6)))
        text(c, '???', 0, 0, 70, '#FFFFFF', 'Black', 'c', stroke=14, stroke_c=INK); c.restore()

# ================= scenes 3 to 5: street, fiber, coast (one wide world) =================
BASE = 700          # street level in world units
FIB_Y = 900         # the fiber under the road
TOWER_X = 1500
COAST_X = 4200
def street_world(c, t, cx, cy, z, comet_pos=None, comet_ang=0.0, bub=None):
    c.save(); cam(c, cx, cy, z)
    # sky and far skyline
    c.drawRect(skia.Rect.MakeLTRB(-2000, -3000, 8000, BASE + 10), LG(0, BASE - 1400, 0, BASE, ['#2E9BFF', '#8FD3FF', '#FFE3B8']))
    sun(c, 2300, BASE - 900, 90)
    for i, (x, y, s) in enumerate(((-100, -250, 1.3), (700, -120, 0.9), (1400, -300, 1.1), (2400, -180, 1.0), (3300, -260, 1.2), (4300, -150, 0.9))):
        cloud(c, x + (t*14) % 200, BASE - 700 + y, s, 0.95)
    r_ = np.random.default_rng(21); x = -800
    while x < COAST_X - 200:
        w = r_.uniform(110, 180); h = r_.uniform(300, 620)
        building(c, x, BASE, w, h, '#A6D6F5', windows=False); x += w - 10
    # main buildings
    r_ = np.random.default_rng(5); x = -700; i = 0
    while x < COAST_X - 350:
        w = r_.uniform(150, 230); h = r_.uniform(240, 470)
        if abs(x + w/2 - TOWER_X) > 150:
            building(c, x, BASE, w, h, LAGOS_B[i % len(LAGOS_B)], seed=i + 3, roof='tank' if i % 3 == 1 else 'flat')
        if i % 3 == 0: palm(c, x + w + 10, BASE, 1.0, math.sin(t*1.2 + i)*0.3)
        x += w + r_.uniform(20, 60); i += 1
    tower(c, TOWER_X, BASE, 640, t=t)
    # the sender's phone glowing in a window
    px, py = 380, BASE - 250
    glow(c, px, py, 160, '#FFFFFF', 0.7); rr(c, px - 40, py - 64, 80, 128, 18, P('#1B2A4A')); rr(c, px - 31, py - 54, 62, 108, 12, P('#8CF0B4'))
    # road
    c.drawRect(skia.Rect.MakeLTRB(-2000, BASE, COAST_X, BASE + 100), P('#4A5568'))
    for k in range(-20, 60): rr(c, k*160, BASE + 44, 80, 12, 6, P('#FFFFFF', 0.85))
    c.drawRect(skia.Rect.MakeLTRB(-2000, BASE + 100, COAST_X, BASE + 130), P('#CBD5E0'))
    for k, sp in ((0, 170), (1, -120)):
        bxw = ((t*sp + k*1500) % 4600) - 600
        danfo(c, bxw, BASE + (70 if k == 0 else 40), 1.0, t)
    # beach and sea
    c.drawRect(skia.Rect.MakeLTRB(COAST_X - 400, BASE + 20, COAST_X + 500, BASE + 140), P('#F7D794'))
    poly(c, [(COAST_X - 450, BASE + 130), (COAST_X - 400, BASE), (COAST_X + 600, BASE + 20), (COAST_X + 700, BASE + 140)], P('#F7D794'))
    # landing station
    lx = COAST_X - 150
    rr(c, lx - 110, BASE - 170, 220, 190, 16, P('#EEF2F7')); c.drawRect(skia.Rect.MakeXYWH(lx - 125, BASE - 190, 250, 34), P('#FF6F59'))
    rr(c, lx - 30, BASE - 90, 60, 110, 10, P('#64748B'))
    # sea surface and water body
    sea_x = COAST_X + 380
    c.drawRect(skia.Rect.MakeLTRB(sea_x, BASE + 30, 12000, 6000), LG(0, BASE, 0, BASE + 1600, ['#39B4F3', '#1373C8', '#0B4A96']))
    wave = [(x, BASE + 30 + 10*math.sin(x/60 + t*3)) for x in range(int(sea_x), 9000, 30)]
    c.drawPath(_path(wave), P('#FFFFFF', 0.9, stroke=10))
    # soil under the city
    soil_top = BASE + 130
    c.drawRect(skia.Rect.MakeLTRB(-2000, soil_top, sea_x, 5000), LG(0, soil_top, 0, soil_top + 900, ['#C98A52', '#A0643A', '#7A4A2B']))
    r2 = np.random.default_rng(8)
    for k in range(90):
        rx = r2.uniform(-1500, sea_x - 50); ry = soil_top + r2.uniform(60, 800)
        c.drawOval(skia.Rect.MakeXYWH(rx, ry, r2.uniform(24, 70), r2.uniform(14, 30)), P('#6E4226', 0.45))
    poly(c, [(sea_x, BASE + 30), (sea_x + 900, 2400), (sea_x - 50, 2400)], P('#D9B26E'))   # sloping sea floor near shore
    # fiber: down the tower leg, under the road, into the station, out to sea
    fib = FIB
    c.drawPath(_path(fib), P('#2C3E50', stroke=42)); c.drawPath(_path(fib), P('#5DD3F3', stroke=24)); c.drawPath(_path(fib), P('#E4FBFF', 0.9, stroke=7))
    c.restore()
    return fib

def fib_point(fib, s):
    """point and angle at arc length s along the fiber polyline"""
    acc = 0.0
    for (x0, y0), (x1, y1) in zip(fib[:-1], fib[1:]):
        L = math.hypot(x1 - x0, y1 - y0)
        if acc + L >= s:
            k = (s - acc)/L; return x0 + (x1 - x0)*k, y0 + (y1 - y0)*k, math.atan2(y1 - y0, x1 - x0)
        acc += L
    (x0, y0), (x1, y1) = fib[-2], fib[-1]; return x1, y1, math.atan2(y1 - y0, x1 - x0)
def fib_len(fib): return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(fib[:-1], fib[1:]))

SEA_X = COAST_X + 380
FIB = [(TOWER_X, BASE - 20), (TOWER_X, FIB_Y), (COAST_X - 150, FIB_Y), (COAST_X - 150, BASE - 20), (COAST_X - 40, BASE - 20), (COAST_X - 40, BASE + 24),
       (SEA_X, BASE + 56), (SEA_X + 500, BASE + 700), (SEA_X + 1100, 2300)]
def s_street(c, t):
    t3, t4, t5, t6 = T[3], T[4], T[5], T[6]
    top_tower = (TOWER_X, BASE - 640)
    phone_w = (380, BASE - 250)
    # camera path: close on the phone, pull back to see the tower, then down under the road, along to the coast, into the sea
    k_pull = eio(seg(t, t3 - 0.1, t3 + 0.9))
    cx = lerp(phone_w[0], 940, k_pull); cy = lerp(phone_w[1], BASE - 330, k_pull); z = lerp(2.4, 0.7, k_pull)
    # the message rides the radio waves to the tower
    fly = eio(seg(t, t3 + 0.5, wt(3, 'tower') + 0.35))
    bxw = lerp(phone_w[0], top_tower[0], fly); byw = lerp(phone_w[1], top_tower[1] + 40, fly) - math.sin(math.pi*fly)*260
    # it turns into light and runs through the fiber: at the station by "coast", in the water on "dives"
    light_t = wt(4, 'light')
    L = fib_len(FIB); s_st = fib_len(FIB[:5]); s_sea = fib_len(FIB[:7])
    t_st = T[5] + 0.15; t_sea = wt(5, 'dives') + 0.15; t_end = T[6] + 0.1
    if t <= light_t: s_fib = 0.0
    elif t < t_st: s_fib = s_st*seg(t, light_t, t_st)**1.25
    elif t < t_sea: s_fib = lerp(s_st, s_sea, seg(t, t_st, t_sea))
    else: s_fib = lerp(s_sea, L*0.95, seg(t, t_sea, t_end)**0.8)
    fx, fy, fa = fib_point(FIB, max(0.0, s_fib))
    k_down = eio(seg(t, t4 - 0.1, t4 + 0.8))
    if t >= t4 - 0.1:
        tcx = fx + 120; tcy = (fy - 170) if fy < BASE + 300 else fy - 60
        tcy = min(tcy, FIB_Y - 170) if s_fib < s_st else tcy
        cx = lerp(cx, tcx, k_down); cy = lerp(cy, tcy, k_down); z = lerp(z, 1.05, k_down)
    fib = street_world(c, t, cx, cy, z)
    # draw the traveller in screen space
    def to_s(x, y): return W/2 + (x - cx)*z, H/2 + (y - cy)*z
    if t < light_t:
        sx, sy = to_s(bxw, byw)
        radio_arcs(c, *to_s(*phone_w), t, dirn=-38, n=5, colr='#FF7A00', a=seg(t, t3 + 0.3, t3 + 0.6)*(1 - seg(t, wt(3, 'tower'), wt(3, 'tower') + 0.5)), spread=36)
        bubble(c, sx, sy, 0.62*z/0.7, look=(1, -0.5), happy=0.8, locked=1.0, rot=10*math.sin(t*6)*fly*(1 - fly)*4)
        if fly >= 1:
            glow(c, *to_s(*top_tower), 180*(1 - seg(t, wt(3, 'tower') + 0.35, wt(3, 'tower') + 0.8)), '#FFFFFF', 1.0)
    else:
        sx, sy = to_s(fx, fy)
        fl = 1 - seg(t, light_t, light_t + 0.3)
        glow(c, sx, sy, 320*fl + 1, '#FFFFFF', fl)
        comet(c, sx, sy, fa, t, 1.55)
        sk_ = (s_fib - s_sea)/500
        if 0 < sk_ < 1.4:
            wx, wy = to_s(SEA_X + 10, BASE + 32)
            for j in range(9):
                an = math.radians(-160 + j*18); r = 40 + 260*eout(min(1, sk_))
                circ(c, wx + math.cos(an)*r, wy + math.sin(an)*r*0.9 + 200*sk_**2, 18*(1 - min(1, sk_)*0.7)*z, P('#FFFFFF', 1 - seg(sk_, 0.8, 1.4)))
    label(c, 'RADIO WAVES', 540, 190, 52, '#FFFFFF', INK, k=seg(t, wt(3, 'radio') - 0.05, wt(3, 'radio') + 0.25)*(1 - seg(t, t4 - 0.2, t4)))
    label(c, 'GLASS FIBER', 540, 190, 52, '#5DD3F3', INK, k=seg(t, wt(4, 'glass') - 0.05, wt(4, 'glass') + 0.25)*(1 - seg(t, t5 - 0.2, t5)))
    label(c, 'LANDING STATION', 540, 190, 48, '#FFFFFF', INK, k=seg(t, t5 - 0.05, t5 + 0.25)*(1 - seg(t, wt(5, 'dives') + 0.2, wt(5, 'dives') + 0.4)))
    # splash when it hits the water
    sea_s = fib_len(FIB[:7]) - 60
    if s_fib > sea_s - 400:
        pass

# ================= scenes 6 to 8: the ocean floor =================
def ocean_bg(c, t, depth=1.0):
    top = mix('#3BB6F5', '#1766C2', depth); bot = mix('#1373C8', '#062E66', depth)
    c.drawRect(skia.Rect.MakeWH(W, H), LG(0, 0, 0, H, [top, bot]))
    light_rays(c, t, 0.08*(1 - 0.5*depth))

SEABED = 700
REP = [(0, 0)]
def s_ocean(c, t):
    t6, t7, t8, t9 = T[6], T[7], T[8], T[9]
    t_in = t6 - 0.15
    depth = eout(seg(t, t_in, t_in + 1.0))
    ocean_bg(c, t, 0.4 + 0.6*depth)
    # world scroll along the cable
    speed = 900
    xoff = (t - t_in)*speed
    shift = (1 - depth)*520
    yoff = -shift
    c.save(); c.translate(0, shift)
    # far rocks
    for i in range(-2, 12):
        x = i*260 - (xoff*0.35) % 260
        c.drawOval(skia.Rect.MakeXYWH(x, SEABED - 120 + (i % 3)*20, 300, 160), P('#0E4F99', 0.5))
    bed = [(x, SEABED + 26*math.sin((x + xoff)/180) + 10*math.sin((x + xoff)/57)) for x in range(-40, W + 80, 30)]
    p = skia.Path(); p.moveTo(-40, H + 400)
    for q in bed: p.lineTo(*q)
    p.lineTo(W + 80, H + 400); p.close()
    c.drawPath(p, LG(0, SEABED - 40, 0, H, ['#F4CB85', '#D99A56']))
    for i in range(-1, 9):
        x = i*170 - xoff % 170
        seaweed(c, x, SEABED + 26*math.sin((x + xoff)/180) + 18, 110 + (i*37 % 60), t + i, '#18A874' if i % 2 else '#27C28A')
    # km posts on the cable, so we feel the distance
    cy = lambda x: SEABED - 10 + 14*math.sin((x + xoff)/260)
    cab = [(x, cy(x)) for x in range(-40, W + 80, 20)]
    c.drawPath(_path(cab), P('#16202C', stroke=46)); c.drawPath(_path(cab), P('#344B63', stroke=30)); c.drawPath(_path(cab), P('#5C7A99', 0.6, stroke=8))
    comet_x = 420
    c.drawPath(_path([(x, y) for x, y in cab if x < comet_x]), P('#FFE066', 0.95, stroke=12))
    # repeater: reaches the traveller right on "boosts"
    tb = wt(8, 'boosts')
    rx = comet_x + (tb - t)*speed
    pulse = math.exp(-((t - tb)/0.25)**2)
    if -200 < rx < W + 200:
        repeater(c, rx, cy(rx) - 4, pulse, 1.3)
    REP[0] = (rx, cy(rx) + shift)
    c.restore()
    # the traveller
    boost = seg(t, wt(8, 'boosts'), wt(8, 'boosts') + 0.4)
    cyc = lerp(600, cy(comet_x) + shift - 6, depth)
    rise = ein(seg(t, t9 - 0.4, t9 - 0.05))
    cyc -= rise*900
    comet(c, comet_x - 6*(1 - depth), cyc, math.radians(55)*(1 - depth) - math.radians(80)*rise, t, 1.45 + 0.45*boost)
    if boost > 0:
        for i in range(8):
            y = 200 + i*80; L = 200 + 120*(i % 3); x = (W - ((t*2400 + i*300) % (W + 600)))
            c.drawLine(x, y, x + L, y, P('#FFFFFF', 0.35*boost*(1 - seg(t, t9 - 0.6, t9)), stroke=6))
    fish(c, 200 + math.sin(t*0.8)*60, 330, 1.1, '#FF9F1C', t=t); fish(c, 300 + math.sin(t*0.7 + 1)*40, 420, 0.75, '#FF6F91', t=t + 1)
    fish(c, 860 - (t*40) % 300, 260, 0.9, '#FFD60A', True, t=t + 2)
    bubbles_up(c, t, 26, a=0.45)
    # quick guess: how far?
    gk = seg(t, t6 - 0.05, t6 + 0.3)
    ans = wt(7, 'six')
    if gk > 0 and t < wt(7, 'garden') - 0.1:
        card(c, 540, 170, 1.0, 'HOW FAR?', k=gk*(1 - seg(t, ans - 0.1, ans)), bg=HI, fg=INK, size=64)
        # a spinning counter until the answer lands
        if t < ans:
            v = int((t*9973) % 9000) + 100
            txt = f'{v:,} KM'
        else:
            txt = '6,000+ KM'
        k2 = back(seg(t, ans - 0.05, ans + 0.3), 2.5) if t >= ans else 1.0
        c.save(); c.translate(540, 330); c.scale(k2, k2)
        f = font(120, 'Black'); tw = f.measureText(txt)
        rr(c, -tw/2 - 40, -110, tw + 80, 150, 40, P('#000000', 0.3, blur=10))
        rr(c, -tw/2 - 40, -118, tw + 80, 150, 40, P('#FFFFFF' if t >= ans else '#1B2A4A'))
        c.drawString(txt, -tw/2, 0, f, P(INK if t >= ans else '#FFD60A'))
        c.restore()
    # thick as a garden hose: cable end on, next to a hose
    hk = seg(t, wt(7, 'garden') - 0.2, wt(7, 'garden') + 0.2)*(1 - seg(t, T[8] - 0.3, T[8] - 0.05))
    if hk > 0:
        kk = back(hk, 1.8)
        c.save(); c.translate(540, 330); c.scale(kk*1.35, kk*1.35)
        rr(c, -330, -170, 660, 330, 50, P('#FFFFFF', 0.95))
        # cable cross-section
        cxs = -150
        circ(c, cxs, -10, 90, P('#16202C')); circ(c, cxs, -10, 74, P('#8E97A6'))
        circ(c, cxs, -10, 50, P('#E08A3C')); circ(c, cxs, -10, 30, P('#1B2A4A'))
        for i in range(6): circ(c, cxs + 16*math.cos(i*1.047), -10 + 16*math.sin(i*1.047), 6, P('#9FF0FF'))
        text(c, 'CABLE', cxs, 130, 38, INK, 'Black', 'c')
        text(c, '=', 0, 20, 90, INK, 'Black', 'c')
        # hose
        hx = 150
        circ(c, hx, -10, 90, P('#2BB24C')); circ(c, hx, -10, 62, P('#1E8A39')); circ(c, hx, -10, 44, P('#0F4F20'))
        text(c, 'HOSE', hx, 130, 38, INK, 'Black', 'c')
        c.restore()
    rpx, rpy = REP[0]
    label(c, 'REPEATER', min(max(rpx, 200), 880), rpy - 200, 50, '#FFFFFF', INK, k=seg(t, wt(8, 'repeater') - 0.05, wt(8, 'repeater') + 0.25)*(1 - seg(t, t9 - 0.4, t9 - 0.1)), pointer=(rpx, rpy - 50))
    card(c, 540, 200, 1.0, 'EVERY ~70 KM', k=seg(t, T[8] - 0.05, T[8] + 0.25)*(1 - seg(t, t9 - 0.3, t9)), bg=HI, fg=INK, size=62)

# ================= scene 9: the server =================
def s_server(c, t):
    t9 = T[9]
    c.drawRect(skia.Rect.MakeWH(W, H), LG(0, 0, 0, H, ['#2B3A67', '#1A2240']))
    # rows of racks in perspective, lights blinking
    for row in range(3):
        y = 330 + row*60; s_ = 0.6 + row*0.25
        for i in range(-1, 9):
            x = i*150*s_ + ((t*30*s_) % (150*s_)) - 60
            rr(c, x, y - 220*s_, 120*s_, 420*s_, 12*s_, P(mix('#5A6FB0', '#1A2240', 0.55 - row*0.25)))
            for j in range(6):
                rr(c, x + 10*s_, y - 200*s_ + j*62*s_, 100*s_, 40*s_, 6*s_, P(mix('#26345E', '#1A2240', 0.5 - row*0.2)))
                on = (int(t*5 + i*3 + j*7 + row) % 4) != 0
                circ(c, x + 90*s_, y - 180*s_ + j*62*s_, 5*s_, P('#39E07A' if on else '#FFD60A', 0.9))
    c.drawRect(skia.Rect.MakeXYWH(0, 760, W, 320), LG(0, 760, 0, H, ['#3B4B7A', '#26345E']))
    for i in range(12): c.drawLine(i*100 - 50, 760, i*160 - 400, H, P('#FFFFFF', 0.08, stroke=3))
    # the message arrives and the server catches it
    arr = eout(seg(t, t9 - 0.1, t9 + 0.45))
    sx = 540; sy = lerp(-200, 250, arr)
    tick_t = wt(9, 'one'); cant = wt(9, "can't")
    imp = math.exp(-((t - t9 - 0.45)/0.08)**2)
    server_guy(c, 540, 640, 1.75, t, look=(0, -1) if t < cant - 0.3 else (-0.8, -0.3), squint=0.7*seg(t, cant - 0.1, cant + 0.2), mag=seg(t, cant - 0.3, cant + 0.2),
               sweat=seg(t, cant + 0.2, T[10]), happy=seg(t, t9 + 0.4, t9 + 0.7)*(1 - seg(t, cant - 0.3, cant)))
    bubble(c, sx, sy + math.sin(t*3)*6, 0.95, look=(0, 0.6), happy=0.6, locked=1.0, squash=1 - 0.2*imp)
    # one grey tick
    tk = seg(t, tick_t - 0.05, tick_t + 0.45)
    if tk > 0:
        c.save(); c.translate(870, 200); kb = back(min(1, tk*1.6), 2); c.scale(kb, kb)
        circ(c, 0, 8, 120, P('#000000', 0.3, blur=10)); circ(c, 0, 0, 120, P('#FFFFFF')); c.restore()
        big_ticks(c, 870, 205, 1, tk, 1.6)
    if t > cant - 0.2:
        card(c, 290, 330, 1.0, SCR, k=seg(t, cant - 0.2, cant + 0.1), bg='#1B2A4A', fg='#FFD60A', size=46)
    label(c, 'WHATSAPP SERVER', 540, 90, 52, '#FFFFFF', INK, k=seg(t, wt(9, 'server') - 0.05, wt(9, 'server') + 0.25)*(1 - seg(t, cant - 0.4, cant - 0.2)))

# ================= scene 10: London =================
def london_bg(c, t):
    c.drawRect(skia.Rect.MakeWH(W, H), LG(0, 0, 0, H, ['#6F86B8', '#B7C6E6']))
    # Elizabeth Tower silhouette and buildings
    col_ = '#5A6E9C'
    for i, (x, w, h) in enumerate(((-20, 160, 380), (130, 140, 300), (740, 180, 340), (900, 200, 420))):
        rr(c, x, H - h - 120, w, h + 200, 8, P(col_))
    tx = 330
    rr(c, tx, H - 660, 110, 700, 6, P('#4D5F8C')); poly(c, [(tx - 10, H - 660), (tx + 55, H - 800), (tx + 120, H - 660)], P('#4D5F8C'))
    circ(c, tx + 55, H - 590, 40, P('#F4E9C8')); circ(c, tx + 55, H - 590, 40, P('#4D5F8C', stroke=6))
    c.drawLine(tx + 55, H - 590, tx + 55, H - 616, P('#4D5F8C', stroke=5)); c.drawLine(tx + 55, H - 590, tx + 74, H - 590, P('#4D5F8C', stroke=5))
    for i in range(5): cloud(c, i*260 - 60 + (t*10) % 60, 120 + (i % 2)*50, 1.2, 0.9, '#E3E9F5')
    # red bus passing
    bx = (t*220) % 1700 - 400
    c.save(); c.translate(bx, H - 160)
    rr(c, -170, -210, 340, 200, 26, P('#E63946'))
    for r in range(2):
        for i in range(5): rr(c, -150 + i*62, -196 + r*92, 48, 50, 8, P('#CFE8FF'))
    for wx in (-110, 110): circ(c, wx, -8, 28, P('#222')); circ(c, wx, -8, 11, P('#BFC7D5'))
    c.restore()
    c.drawRect(skia.Rect.MakeXYWH(0, H - 140, W, 140), P('#5B6477'))
    # rain
    r_ = np.random.default_rng(4)
    for i in range(120):
        x = r_.uniform(0, W); y = (r_.uniform(0, H) + t*900) % H
        c.drawLine(x, y, x - 8, y + 30, P('#FFFFFF', 0.35, stroke=3))

def s_london(c, t):
    t10 = T[10]
    london_bg(c, t)
    un = wt(10, 'unlocks')
    sk = seg(t, un, un + 0.8)
    arrive = seg(t, t10 + 0.2, t10 + 0.55)
    ph_in = eout(seg(t, t10 - 0.2, t10 + 0.3))
    PX, PY, PS = 520, 700 + (1 - ph_in)*600, 1.3
    phone(c, PX, PY, PS, 3, chat_screen(incoming=True, show_msg=arrive, typed='Hello from Lagos!', unlocked=sk, name='Tolu'))
    msg_x, msg_y = PX - 190*PS + 26*PS + 140*PS, PY - 390*PS + 16*PS + 250*PS + 48*PS
    # the bubble flies in and drops into the chat
    fk = seg(t, t10 - 0.1, t10 + 0.3)
    if fk < 1:
        bubble(c, lerp(-200, msg_x, eout(fk)), lerp(250, msg_y, eout(fk)), 0.8*(1 - 0.6*ein(fk)), look=(1, 0.4), happy=0.8, locked=1.0)
    # the lock pops open
    if t > un - 0.1:
        ok = seg(t, un - 0.1, un + 0.5)
        lx_, ly_ = msg_x + 230, msg_y - 40
        c.save(); c.translate(0, -140*eout(ok)); padlock(c, lx_, ly_, 1.1, a=1 - seg(t, un + 0.7, un + 1.1), open_=eout(seg(t, un - 0.05, un + 0.2))); c.restore()
        for i in range(12):
            an = i*math.pi*2/12; r = 60 + 240*eout(ok)
            circ(c, lx_ + math.cos(an)*r, ly_ + math.sin(an)*r, 12*(1 - ok), P(HI))
    tk = seg(t, wt(10, 'two') - 0.05, wt(10, 'two') + 0.6)
    if tk > 0:
        c.save(); c.translate(870, 190); kk = back(min(1, tk*1.6), 2); c.scale(kk, kk)
        circ(c, 0, 8, 125, P('#000000', 0.3, blur=10)); circ(c, 0, 0, 125, P('#FFFFFF')); c.restore()
        big_ticks(c, 872, 196, 2, tk, 1.45)

# ================= scene 11: the whole trip, under a second =================
def s_end(c, t):
    t11 = T[11]
    zo = eout(seg(t, t11 - 0.15, t11 + 0.6))
    z = lerp(3.0, 1.0, zo)
    map_draw(c, lerp(LONDON[0], 3.0, zo), lerp(LONDON[1], 30.0, zo), z, t, route_k=1.0, pins=(1, 1), show_labels=0)
    k = seg(t, wt(11, 'second') - 0.2, wt(11, 'second') + 0.15)
    stopwatch(c, 540, 470, 1.4*back(k, 2.2), t) if k > 0 else None
    if k > 0:
        c.save(); c.translate(540, 190); kk = back(k, 2.2); c.scale(kk, kk)
        f = font(92, 'Black'); s = 'UNDER 1 SECOND'; tw = f.measureText(s)
        rr(c, -tw/2 - 36, -96, tw + 72, 130, 36, P('#000000', 0.3, blur=10)); rr(c, -tw/2 - 36, -104, tw + 72, 130, 36, P(HI))
        c.drawString(s, -tw/2, 0, f, P(INK)); c.restore()

# ================= timeline =================
SCENES = [(0.0, T[1] - 0.05, s_hook), (T[1] - 0.25, T[2] + 0.02, s_map1), (T[2] - 0.02, T[3] - 0.05, s_lock),
          (T[3] - 0.15, T[6] - 0.1, s_street), (T[6] - 0.2, T[9] - 0.06, s_ocean), (T[9] - 0.06, T[10] - 0.05, s_server),
          (T[10] - 0.2, T[11] - 0.1, s_london), (T[11] - 0.2, END + 1, s_end)]
FLASH = [T[9] - 0.06]
def render_scene(fn, t):
    s, c = surface(); fn(c, t); return to_array(s).astype(np.float32)

def frame(i):
    t = i/FPS
    act = [(a, b, fn) for a, b, fn in SCENES if a <= t < b]
    if not act: act = [SCENES[-1]]
    if len(act) == 1:
        img = render_scene(act[-1][2], t)
    else:
        (a0, b0, f0), (a1, b1, f1) = act[0], act[-1]
        k = ease(seg(t, a1, b0))
        img = render_scene(f0, t)*(1 - k) + render_scene(f1, t)*k
    for tf in FLASH:
        fk = math.exp(-((t - tf)/0.07)**2)
        if fk > 0.01: img = img*(1 - fk) + 255*fk
    # whip pan into London
    wk = math.exp(-((t - (T[10] - 0.1))/0.1)**2)
    if wk > 0.05:
        acc = img.copy(); n = 9
        for j in range(1, n): acc += np.roll(img, int(j*14*wk), axis=1)
        img = acc/n
    s, c = surface()
    c.drawImage(skia.Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)), 0, 0) if False else None
    # captions on top
    cap_s, cc = surface()
    cc.clear(skia.Color4f(0, 0, 0, 0))
    caption(cc, WORDS, t, y=985, size=76)
    capa = cap_s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType).astype(np.float32)
    al = capa[..., 3:4]/255
    img = img*(1 - al) + capa[..., :3]
    img = img + GRAIN[i % 4]
    return np.clip(img, 0, 255).astype(np.uint8)

if __name__ == '__main__':
    out = ROOT + '/cartoon-version/frames'; os.makedirs(out, exist_ok=True)
    a, b = int(sys.argv[1]), int(sys.argv[2])
    step = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    for i in range(a, min(b, int(END*FPS)), step):
        Image.fromarray(frame(i)).save(f'{out}/{i:05d}.png', compress_level=1)
    print('done', a, b)
