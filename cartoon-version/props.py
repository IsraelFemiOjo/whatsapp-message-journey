"""Props for the scenes: phone, Lagos street, tower, underground, coast, ocean, server, London."""
import math, numpy as np, skia
from toon import *

rng = np.random.default_rng(3)

def phone(c, x, y, s=1.0, rot=0.0, screen=None, a=1.0):
    """a rounded phone; screen(c, w, h) draws the UI in local coords"""
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s, s)
    w, h = 380, 780
    rr(c, -w/2 + 16, -h/2 + 30, w, h, 64, P('#000000', 0.25*a, blur=26))
    rr(c, -w/2, -h/2, w, h, 64, LG(-w/2, 0, w/2, 0, ['#3A4A66', '#27344C'], a=a))
    rr(c, -w/2 + 16, -h/2 + 16, w - 32, h - 32, 50, P('#0E1726', a))
    c.save(); c.clipRRect(skia.RRect.MakeRectXY(skia.Rect.MakeXYWH(-w/2 + 16, -h/2 + 16, w - 32, h - 32), 50, 50), True)
    c.translate(-w/2 + 16, -h/2 + 16)
    if screen: screen(c, w - 32, h - 32)
    c.restore()
    rr(c, -44, -h/2 + 30, 88, 24, 12, P('#05090F', a))
    rr(c, -w/2 + 30, -h/2 + 30, 26, h - 140, 13, P('#FFFFFF', 0.06*a))
    c.restore()

def chat_screen(sent=0.0, ticks=0, typed='Hello from Lagos!', press=0.0, name='Tolu', incoming=False, show_msg=1.0, unlocked=1.0):
    def draw(c, w, h):
        rr(c, 0, 0, w, h, 0, LG(0, 0, 0, h, ['#E8F4EC', '#D6ECDD']))
        # header
        rr(c, 0, 0, w, 130, 0, P('#1E9E5A'))
        circ(c, 60, 86, 30, P('#FFB547'))
        text(c, name[0], 60, 98, 32, '#7A4A00', 'Black', 'c')
        text(c, name, 104, 84, 30, '#FFFFFF', 'Bold'); text(c, 'online', 104, 112, 20, '#CFF5DE', 'SemiBold')
        # messages
        if incoming:
            if show_msg > 0:
                k = back(show_msg, 1.6)
                c.save(); c.translate(26, 250); c.scale(k, k)
                rr(c, 0, 0, 312, 100, 26, P('#FFFFFF'))
                msg = typed if unlocked >= 1 else ''.join(ch if (i/len(typed)) < unlocked or ch == ' ' else '#%&@$*'[i % 6] for i, ch in enumerate(typed))
                text(c, msg, 20, 62, 29, INK, 'Bold')
                c.restore()
        else:
            if sent > 0:
                k = back(min(1, sent*1.2), 1.6)
                c.save(); c.translate(w - 26, 260); c.scale(k, k)
                rr(c, -290, 0, 290, 104, 26, P('#C8F7C5'))
                text(c, typed, -268, 52, 26, INK, 'SemiBold')
                tx = -64
                for i in range(ticks):
                    c.drawPath(_tick(tx + i*14, 82), P('#7B8794', stroke=4))
                c.restore()
        # input bar
        rr(c, 16, h - 104, w - 110, 80, 40, P('#FFFFFF'))
        if not incoming and sent <= 0: text(c, typed, 42, h - 52, 24, INK, 'SemiBold')
        else: text(c, 'Message', 42, h - 52, 24, '#9AA5B1', 'SemiBold')
        bx, by = w - 56, h - 64
        pr = 1 - 0.18*math.sin(math.pi*min(1, press))
        circ(c, bx, by, 38*pr, P('#1E9E5A'))
        tri = [(bx - 12*pr, by - 16*pr), (bx + 18*pr, by), (bx - 12*pr, by + 16*pr), (bx - 6*pr, by)]
        poly(c, tri, P('#FFFFFF'))
    return draw

def _tick(x, y):
    p = skia.Path(); p.moveTo(x, y - 2); p.lineTo(x + 6, y + 5); p.lineTo(x + 18, y - 10); return p

def big_ticks(c, x, y, n, k, s=1.0, color='#7B8794'):
    """large ticks drawn in one after another, like the chat app's"""
    c.save(); c.translate(x, y); c.scale(s, s)
    paths = []
    for i in range(n):
        kk = seg(k, i*0.3, i*0.3 + 0.5)
        if kk <= 0: continue
        ox = i*40 - (n - 1)*20
        p = skia.Path(); p.moveTo(ox - 40, -2); p.lineTo(ox - 12, 26); p.lineTo(ox + 40, -34)
        pm = skia.PathMeasure(p, False); L = pm.getLength(); dst = skia.Path(); pm.getSegment(0, L*eout(kk), dst, True)
        paths.append(dst)
    for d in paths: c.drawPath(d, P('#FFFFFF', stroke=26))
    for d in paths: c.drawPath(d, P(color, stroke=14))
    c.restore()

# ---------------- Lagos ----------------
LAGOS_B = ['#FF8A5B', '#FFC857', '#4ECDC4', '#F76C8F', '#7C83FD', '#FFA45B', '#3DC1A5', '#FF6F59']
def sky(c, top='#56C2FF', bot='#CDEFFF'):
    c.drawRect(skia.Rect.MakeWH(W, H), LG(0, 0, 0, H, [top, bot]))

def sun(c, x, y, r=70):
    glow(c, x, y, r*3, '#FFF3B0', 0.6); circ(c, x, y, r, P('#FFE066'))

def cloud(c, x, y, s=1.0, a=1.0, colr='#FFFFFF'):
    c.save(); c.translate(x, y); c.scale(s, s)
    for dx, dy, r in ((-60, 10, 42), (-10, -14, 58), (50, 4, 46), (90, 18, 32)):
        circ(c, dx, dy, r, P(colr, a))
    rr(c, -100, 10, 220, 46, 23, P(colr, a))
    c.restore()

def building(c, x, base, w, h, colr, seed=0, roof='flat', a=1.0, windows=True):
    r_ = np.random.default_rng(seed)
    d = mix(colr, '#1B2A4A', 0.25)
    rr(c, x, base - h, w, h, 10, P(colr, a))
    c.drawRect(skia.Rect.MakeXYWH(x + w*0.72, base - h + 6, w*0.28, h - 6), P(d, 0.35*a))   # shade side
    ww, wh = 22, 28
    nx = max(1, int((w - 20)//40)); ny = max(1, int((h - 40)//56)) if windows else 0
    for i in range(nx):
        for j in range(ny):
            wx = x + 16 + i*((w - 32 - ww)/max(1, nx - 1) if nx > 1 else 0) + (0 if nx > 1 else (w - 32 - ww)/2)
            wy = base - h + 24 + j*56
            lit = r_.random() < 0.3
            rr(c, wx, wy, ww, wh, 5, P('#FFF4C2' if lit else mix(colr, '#1B2A4A', 0.45), a))
    if roof == 'tank':
        rr(c, x + w*0.2, base - h - 30, 34, 30, 6, P('#3A86FF', a))
        rr(c, x + w*0.2 - 4, base - h - 36, 42, 10, 5, P('#2B6FDB', a))

def palm(c, x, base, s=1.0, sway=0.0):
    c.save(); c.translate(x, base); c.scale(s, s)
    trunk = [(0, 0), (6 + sway*4, -60), (16 + sway*10, -120), (30 + sway*16, -180)]
    smooth(c, trunk, P('#9C6B3F', stroke=16))
    tx, ty = trunk[-1]
    for ang in (-160, -120, -60, -20, 20):
        a = math.radians(ang + sway*8)
        p = skia.Path(); p.moveTo(tx, ty)
        ex, ey = tx + math.cos(a)*90, ty + math.sin(a)*40 + 30
        p.quadTo(tx + math.cos(a)*50, ty + math.sin(a)*60 - 20, ex, ey)
        p.quadTo(tx + math.cos(a)*45, ty + math.sin(a)*40 - 4, tx, ty)
        c.drawPath(p, P('#2FB36B'))
    c.restore()

def danfo(c, x, base, s=1.0, t=0.0):
    """a yellow minibus"""
    c.save(); c.translate(x, base); c.scale(s, s)
    bob = math.sin(t*18)*1.5
    shadow(c, 0, 0, 280, 22, 0.25, 8)
    c.translate(0, bob)
    body = skia.Path(); body.addRoundRect(skia.Rect.MakeXYWH(-130, -110, 260, 90), 26, 26)
    c.drawPath(body, P('#FFC61A'))
    c.drawRect(skia.Rect.MakeXYWH(-130, -58, 260, 12), P('#1B1B1B'))
    c.drawRect(skia.Rect.MakeXYWH(-130, -40, 260, 8), P('#1B1B1B'))
    for i in range(4): rr(c, -112 + i*56, -98, 44, 34, 8, P('#9ED8F5'))
    rr(c, 90, -98, 34, 34, 8, P('#9ED8F5'))
    for wx in (-80, 80):
        circ(c, wx, -18, 24, P('#222')); circ(c, wx, -18, 10, P('#BFC7D5'))
    c.restore()

def tower(c, x, base, h=560, a=1.0, t=0.0):
    """red and white lattice mast with antenna panels"""
    top = base - h
    lw = 8
    L = P('#E63946', a, stroke=lw)
    xs0, xs1 = 60, 16
    for sgn in (-1, 1):
        c.drawLine(x + sgn*xs0, base, x + sgn*xs1, top + 40, L)
    n = 9
    for i in range(n):
        y0 = base - i*(h - 40)/n; y1 = base - (i + 1)*(h - 40)/n
        w0 = lerp(xs0, xs1, i/n); w1 = lerp(xs0, xs1, (i + 1)/n)
        cc = P('#FFFFFF' if i % 2 else '#E63946', a, stroke=6)
        c.drawLine(x - w0, y0, x + w1, y1, cc); c.drawLine(x + w0, y0, x - w1, y1, cc)
        c.drawLine(x - w1, y1, x + w1, y1, cc)
    c.drawLine(x, top + 40, x, top - 40, P('#E63946', a, stroke=8))
    for sgn in (-1, 1):
        rr(c, x + sgn*30 - 11, top + 10, 22, 90, 8, P('#F1F5F9', a))
    rr(c, x - 11, top - 4, 22, 84, 8, P('#E2E8F0', a))
    blink = 0.5 + 0.5*math.sin(t*6)
    glow(c, x, top - 44, 40, '#FF4D4D', 0.8*blink*a); circ(c, x, top - 44, 9, P('#FF4D4D', a))

def radio_arcs(c, x, y, t, dirn=0.0, n=4, colr='#FFFFFF', a=1.0, spread=70):
    """waves travelling out from x,y toward angle dirn (degrees)"""
    for i in range(n):
        ph = (t*1.6 + i/n) % 1.0
        r = 40 + ph*420
        al = a*(1 - ph)**1.2
        rect = skia.Rect.MakeXYWH(x - r, y - r, 2*r, 2*r)
        p = P(colr, al, stroke=14*(1 - ph*0.6))
        c.drawArc(rect, dirn - spread/2, spread, False, p)

# ---------------- underground and sea ----------------
def soil(c, y0, x0=-4000, x1=6000):
    c.drawRect(skia.Rect.MakeLTRB(x0, y0, x1, y0 + 1600), LG(0, y0, 0, y0 + 700, ['#B7773E', '#8C5530', '#6B3F25']))
    for i in range(60):
        rx = rng.uniform(x0, x1); ry = y0 + rng.uniform(40, 650)
        c.drawOval(skia.Rect.MakeXYWH(rx, ry, rng.uniform(20, 60), rng.uniform(12, 30)), P('#6B3F25', 0.5))

def fiber_tube(c, pts, t, glow_k=1.0, width=34):
    c.drawPath(_path(pts), P('#2C3E50', stroke=width + 14))
    c.drawPath(_path(pts), P('#5DD3F3', 0.9, stroke=width))
    c.drawPath(_path(pts), P('#D9F7FF', 0.9, stroke=width*0.3))

def _path(pts):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    return p

def comet(c, x, y, ang, t, s=1.0, face=True):
    """the message as a streak of light, still with its face"""
    c.save(); c.translate(x, y); c.rotate(math.degrees(ang)); c.scale(s, s)
    for i in range(10):
        k = i/10
        c.drawOval(skia.Rect.MakeXYWH(-40 - k*300, -24*(1 - k), 80 + 40*(1 - k), 48*(1 - k)), P('#FFF3B0', 0.18*(1 - k), blur=6))
    glow(c, 0, 0, 120, '#FFE066', 0.9)
    circ(c, 0, 0, 46, RG(0, -10, 50, ['#FFFFFF', '#FFE066']))
    if face:
        c.rotate(-math.degrees(ang))
        for sx in (-1, 1):
            c.drawOval(skia.Rect.MakeXYWH(sx*16 - 7, -14, 14, 18), P(INK))
        m = skia.Path(); m.moveTo(-12, 10); m.quadTo(0, 22, 12, 10); c.drawPath(m, P(INK, stroke=5))
    c.restore()

def fish(c, x, y, s=1.0, colr='#FF9F1C', flip=False, t=0.0):
    c.save(); c.translate(x, y); c.scale(-s if flip else s, s)
    wig = math.sin(t*10)*0.25
    p = skia.Path(); p.moveTo(-40, 0); p.lineTo(-70, -22 + wig*20); p.lineTo(-70, 22 + wig*20); p.close()
    c.drawPath(p, P(mix(colr, '#000000', 0.15)))
    c.drawOval(skia.Rect.MakeXYWH(-50, -26, 100, 52), P(colr))
    circ(c, 24, -6, 8, P('#FFFFFF')); circ(c, 26, -6, 4, P(INK))
    c.restore()

def seaweed(c, x, base, h, t, colr='#1FB57A'):
    pts = [(x + math.sin(t*1.5 + k*0.8)*10*k, base - k*h/5) for k in range(6)]
    smooth(c, pts, P(colr, stroke=14))

def repeater(c, x, y, pulse=0.0, s=1.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    glow(c, 0, 0, 160 + 120*pulse, '#5DF2FF', 0.35 + 0.6*pulse)
    rr(c, -80, -34, 160, 68, 30, LG(0, -34, 0, 34, ['#9AA9BC', '#5F6E83']))
    rr(c, -60, -24, 60, 12, 6, P('#FFFFFF', 0.35))
    circ(c, 48, 0, 12, P('#5DF2FF'))
    c.restore()

def bubbles_up(c, t, n=24, x0=0, x1=W, seed=5, a=0.5):
    r_ = np.random.default_rng(seed)
    for i in range(n):
        bx = r_.uniform(x0, x1); sp = r_.uniform(60, 160); ph = r_.uniform(0, H)
        by = H - ((ph + t*sp) % (H + 100)); r = r_.uniform(4, 12)
        c.drawCircle(bx + math.sin(t*2 + i)*8, by, r, P('#FFFFFF', a, stroke=2.5))

def light_rays(c, t, a=0.18):
    for i in range(6):
        x = 100 + i*190 + math.sin(t*0.5 + i)*30
        poly(c, [(x, -20), (x + 80, -20), (x + 260, H), (x + 60, H)], P('#FFFFFF', a*(0.5 + 0.5*math.sin(t + i*1.3))))
