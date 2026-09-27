"""Everything drawn on top of the picture, on narration time."""
import math, numpy as np, skia
import mg, sjtl as T
from mg import *

WORDS = mg.make_chunks([dict(w) for w in T.NEW if w['line'] != 11])
CHAP = [(0.0, '01', 'LAGOS'), (11.5, '02', 'RADIO'), (14.47, '03', 'UNDER THE ROAD'), (18.28, '04', 'THE COAST'),
        (21.1, '05', 'THE ROUTE'), (26.12, '06', 'THE ATLANTIC'), (32.78, '07', 'THE SERVER'), (39.33, '08', 'LONDON')]
EL = [(0, 0.0), (2.6, 0.0), (14.5, 0.004), (18.3, 0.009), (21.1, 0.012), (26.1, 0.014), (32.8, 0.046), (39.3, 0.16), (40.3, 0.2), (99, 0.2)]
def elapsed(t):
    xs = [a for a, b in EL]; ys = [b for a, b in EL]
    v = float(np.interp(t, xs, ys))
    if t < 2.62: return '0.000 s'
    if t >= 40.3: return '≈ 0.2 s'
    return f'≈ {v:.3f} s'
def progress(t):
    idx = max(i for i, (a, _, _) in enumerate(CHAP) if t >= a)
    a = CHAP[idx][0]; b = CHAP[idx + 1][0] if idx + 1 < len(CHAP) else T.END
    return min(1, (idx + 0.9*mg.ease((t - a)/(b - a)))/7)

STAGES = [(0.0, 'PHONE'), (11.5, 'TOWER'), (14.47, 'ROAD'), (18.28, 'COAST'), (20.9, 'OCEAN'), (32.78, 'SERVER'), (39.33, 'PHONE')]
def stage_pos(t):
    xs = [a for a, _ in STAGES] + [T.END]
    for i in range(len(STAGES)):
        if t < xs[i + 1]:
            return i + 0.85*mg.ease((t - xs[i])/(xs[i + 1] - xs[i])) if i < 6 else 6.0
    return 6.0

def icon(c, kind, x, y, colr, s=1.0):
    p = P(colr, stroke=2.6*s)
    if kind == 'PHONE':
        rrect(c, x - 8*s, y - 13*s, 16*s, 26*s, 4*s, p); c.drawCircle(x, y + 8*s, 1.8*s, P(colr))
    elif kind == 'TOWER':
        c.drawLine(x - 8*s, y + 13*s, x, y - 11*s, p); c.drawLine(x + 8*s, y + 13*s, x, y - 11*s, p); c.drawLine(x - 4*s, y + 2*s, x + 4*s, y + 2*s, p)
        c.drawArc(skia.Rect.MakeXYWH(x - 13*s, y - 21*s, 26*s, 20*s), 200, 140, False, p)
    elif kind == 'ROAD':
        c.drawLine(x - 12*s, y + 12*s, x - 4*s, y - 12*s, p); c.drawLine(x + 12*s, y + 12*s, x + 4*s, y - 12*s, p); c.drawLine(x, y - 4*s, x, y + 4*s, p)
    elif kind == 'COAST':
        rrect(c, x - 9*s, y - 12*s, 12*s, 10*s, 2*s, p)
        pth = skia.Path(); pth.moveTo(x - 13*s, y + 6*s)
        for k in range(4): pth.quadTo(x - 10*s + k*7*s, y + 1*s, x - 6.5*s + k*7*s, y + 6*s)
        c.drawPath(pth, p)
    elif kind == 'OCEAN':
        for dy in (-5, 5):
            pth = skia.Path(); pth.moveTo(x - 13*s, y + dy*s)
            for k in range(4): pth.quadTo(x - 10*s + k*7*s, y + (dy - 5)*s, x - 6.5*s + k*7*s, y + dy*s)
            c.drawPath(pth, p)
    elif kind == 'SERVER':
        for k in range(3):
            rrect(c, x - 11*s, y - 12*s + k*9*s, 22*s, 7*s, 2*s, p); c.drawCircle(x + 6*s, y - 8.5*s + k*9*s, 1.5*s, P(colr))

def msg_badge(c, x, y, s=1.0, a=1.0, t=0.0):
    """the message itself: a little locked chat bubble riding the light"""
    y += math.sin(t*6.0)*3*s
    c.save(); c.translate(x, y - 52*s); c.scale(s, s)
    c.drawCircle(0, 30, 40, P(GOLD, 0.25*a, blur=18))
    pth = skia.Path(); pth.addRoundRect(skia.Rect.MakeXYWH(-34, -20, 68, 44), 14, 14)
    tail = skia.Path(); tail.moveTo(-6, 22); tail.lineTo(0, 34); tail.lineTo(8, 22); tail.close()
    c.drawPath(pth, P('#000000', 0.35*a, blur=6))
    c.drawPath(tail, P('#25D366', a)); c.drawPath(pth, P('#25D366', a)); c.drawPath(pth, P('#FFFFFF', 0.9*a, stroke=2.5))
    # padlock inside
    c.drawArc(skia.Rect.MakeXYWH(-7, -14, 14, 14), 180, 180, False, P('#FFFFFF', a, stroke=3)); c.drawLine(-7, -7, -7, -2, P('#FFFFFF', a, stroke=3)); c.drawLine(7, -7, 7, -2, P('#FFFFFF', a, stroke=3))
    rrect(c, -10, -3, 20, 16, 3, P('#FFFFFF', a))
    c.restore()

def hud_draw(c, t):
    x0, x1, y = 90, W - 90, 66
    pos = stage_pos(t)
    c.drawRoundRect(skia.Rect.MakeXYWH(40, 16, W - 80, 112), 30, 30, P('#0B0F2E', 0.6, blur=0))
    c.drawRoundRect(skia.Rect.MakeXYWH(40, 16, W - 80, 112), 30, 30, P('#FFFFFF', 0.12, stroke=1.5))
    c.drawLine(x0, y, x1, y, P('#FFFFFF', 0.25, stroke=3))
    c.drawLine(x0, y, x0 + (x1 - x0)*pos/6, y, P(GOLD, 0.95, stroke=4))
    cur = int(round(pos)) if abs(pos - round(pos)) < 0.2 else int(pos)
    for i, (_, name) in enumerate(STAGES):
        x = x0 + (x1 - x0)*i/6
        done = pos >= i - 0.05; here = i == int(math.floor(pos + 0.15))
        r = 27 if here else 22
        c.drawCircle(x, y, r, P(GOLD if here else ('#2A2F62' if not done else '#3A3568')))
        c.drawCircle(x, y, r, P(GOLD if done else '#8A90B8', 0.9, stroke=2))
        icon(c, name, x, y, INK if here else ('#FFD58A' if done else '#B8BEDC'), 1.15 if here else 0.95)
        txt(c, name, x, y + 50, 21 if here else 17, GOLD if here else '#C8CEEA', 'xb' if here else 'sb', 1.0 if here else 0.75, anchor='c', spacing=1.5)
    # the message moving along the tracker
    bx = x0 + (x1 - x0)*pos/6
    if abs(pos - round(pos)) > 0.08:
        c.drawCircle(bx, y, 9, P('#25D366')); c.drawCircle(bx, y, 9, P('#FFFFFF', stroke=2))
    # elapsed time under the tracker
    txt(c, 'ELAPSED', W - 60, 158, 16, '#DCE6FF', 'sb', 0.85, anchor='r', spacing=2)
    txt(c, elapsed(t), W - 60, 196, 36, '#FFFFFF', 'mono', 1.0, anchor='r')

def place_tag(c, t, t0, t1, title, sub):
    k = seg(t, t0, t0 + 0.5); ko = seg(t, t1 - 0.3, t1)
    if k <= 0 or ko >= 1: return
    a = 1 - ease(ko); y = 300
    c.save(); c.clipRect(skia.Rect.MakeXYWH(40, y - 80, 1000, 150))
    dy = (1 - eout5(k))*90
    # pin
    px, py = 78, y - 22 + dy
    pth = skia.Path(); pth.moveTo(px, py + 26); pth.cubicTo(px - 22, py, px - 20, py - 26, px, py - 26); pth.cubicTo(px + 20, py - 26, px + 22, py, px, py + 26); pth.close()
    c.drawPath(pth, P(GOLD, a)); c.drawCircle(px, py - 6, 7, P(INK, a))
    txt(c, title, 116, y + dy, 64, '#FFFFFF', 'xb', a)
    c.restore()
    sk = seg(t, t0 + 0.35, t0 + 0.8)
    if sk > 0: txt(c, sub, 118, y + 50, 30, '#FFE7B0', 'sb', a*eout(sk))

def ripple(c, p, t, t0, colr='#BFFFF0'):
    if p is None: return
    for j in range(3):
        k = seg(t, t0 + 0.08*j, t0 + 0.08*j + 0.6)
        if 0 < k < 1: c.drawCircle(p[0], p[1], 20 + 120*eout(k), P(colr, (1 - k)*0.9, stroke=4*(1 - k) + 1))

def burst(c, p, t, t0, colr=GOLD, n=14, r0=90, r1=260):
    if p is None: return
    k = seg(t, t0, t0 + 0.7)
    if not 0 < k < 1: return
    c.drawCircle(p[0], p[1], r0 + (r1 - r0)*eout(k), P(colr, (1 - k)*0.9, stroke=6*(1 - k) + 1))
    for i in range(n):
        an = i*2*math.pi/n + 0.3; rr = r0*0.8 + (r1*1.1)*eout(k)
        c.drawCircle(p[0] + math.cos(an)*rr, p[1] + math.sin(an)*rr, 6*(1 - k), P(colr, 1 - k))

def route_card(c, t):
    t0, t1 = T.lstart(1) - 0.05, T.lend(1) + 0.3
    k = seg(t, t0, t0 + 0.4); ko = seg(t, t1 - 0.3, t1)
    if k <= 0 or ko >= 1: return
    a = 1 - ease(ko); y = 330 - (1 - eout5(k))*30
    x0, x1 = 170, 910
    glass(c, 120, y - 62, 840, 124, 30, a*eout(k))
    tl, tn = T.wt(1, 'lagos'), T.wt(1, 'london')
    for x, name, tt in ((x0, 'LAGOS', tl - 0.15), (x1, 'LONDON', tn - 0.15)):
        pk = back(seg(t, tt, tt + 0.35), 2.4)
        if pk <= 0: continue
        c.save(); c.translate(x, y); c.scale(pk, pk)
        c.drawCircle(0, 0, 14, P(GOLD, a)); c.drawCircle(0, 0, 26, P(GOLD, 0.35*a, stroke=3))
        c.restore()
        txt(c, name, x + (34 if name == 'LAGOS' else -34), y + 12, 34, '#FFFFFF', 'xb', a*seg(t, tt, tt + 0.3), anchor='l' if name == 'LAGOS' else 'r', spacing=3)
    lk = eout(seg(t, tl + 0.15, tn + 0.1))
    if lk > 0:
        lx0, lx1 = x0 + 180, x1 - 210
        p = draw_path_k(c, [(lx0, y), (lx1, y)], lk, P(GOLD, a, stroke=4))
        dash = P('#FFFFFF', 0.35*a, stroke=3); dash.setPathEffect(skia.DashPathEffect.Make([10, 12], -t*60))
        c.drawLine(lx0, y, lx1, y, dash)
        if p: c.drawCircle(p[0], p[1], 16, P('#FFF4D8', a, blur=6)); c.drawCircle(p[0], p[1], 7, P('#FFFFFF', a))

def cipher_panel(c, t, t0, t1, cant):
    k = seg(t, t0, t0 + 0.4); ko = seg(t, t1 - 0.3, t1)
    if k <= 0 or ko >= 1: return
    a = 1 - ease(ko); s = back(k, 1.8)
    c.save(); c.translate(540, 320); c.scale(s, s)
    glass(c, -330, -92, 660, 184, 28, a)
    txt(c, 'WHAT THE SERVER SEES', 0, -44, 20, '#DCE6FF', 'sb', a, anchor='c', spacing=3)
    f = font(56, 'mono'); s_ = 'U2FsdGVkX19qK3Zw='; w_ = f.measureText(s_)
    c.drawString(s_, -w_/2, 34, f, P('#FFD58A', a))
    sx = -300 + 600*((t*1.3) % 1.0)
    c.drawRect(skia.Rect.MakeXYWH(sx, -14, 4, 64), P(CYAN, 0.7*a, blur=3))
    if t > cant:
        sk = back(seg(t, cant, cant + 0.3), 2.6)
        c.save(); c.translate(210, 76); c.rotate(-8); c.scale(sk, sk)
        rrect(c, -150, -34, 300, 68, 14, P(RED, a)); txt(c, "CAN'T READ IT", 0, 12, 30, '#FFFFFF', 'xb', a, anchor='c', shadow=False, spacing=1.5)
        c.restore()
    c.restore()

_FL = []
def _floor():
    if not _FL:
        p = skia.Paint(AntiAlias=True)
        p.setShader(skia.GradientShader.MakeLinear([skia.Point(0, 820), skia.Point(0, 1080)], [col('#05061A', 0.0), col('#05061A', 0.62)]))
        _FL.append(p)
    return _FL[0]

def draw(c, t, shot, A, tn=None):
    g = lambda k: A.get(k)
    if shot == 'opening':
        place_tag(c, t, 0.05, 1.7, 'Lagos, Nigeria', 'Tolu is texting Kemi in London')
    if A.get('vis', True) and g('pulse') and shot not in ('opening',):
        p = g('pulse')
        if -60 < p[0] < 1140 and -60 < p[1] < 1140:
            fade_in = 1.0 if shot != 'lagos' else seg(t, 10.45, 10.8)
            if shot == 'server' and t > 38.75: fade_in = 1 - seg(t, 38.75, 38.95)
            if fade_in > 0: msg_badge(c, p[0], p[1], 1.0, fade_in, t)
    if shot == 'lagos':
        ripple(c, g('send'), t, T.wt(0, 'send') - 0.02)
        route_card(c, t)
        burst(c, g('bubble'), t, T.wt(2, 'locks') + 0.1)
        chip(c, 330, 720, 'You', t, T.wt(2, 'you', 1) - 0.1, T.lend(2) - 0.4, icon='key')
        chip(c, 730, 720, 'Your friend', t, T.wt(2, 'friend') - 0.1, T.lend(2) - 0.4, icon='key')
        chip(c, 540, 830, 'WhatsApp', t, T.wt(2, 'not') - 0.05, T.lend(2) + 0.3, color='#FFFFFF', strike=T.wt(2, 'whatsapp') + 0.05)
        p = g('pulse')
        if p: callout(c, p[0], p[1], 'RADIO WAVES', 'to the nearest cell tower', t, T.wt(3, 'radio') - 0.1, T.lend(3) - 0.4, side=1, up=-1, L=150)
    elif shot == 'fiber':
        p = g('pulse')
        if p and t > 15.4: callout(c, p[0], p[1], 'GLASS FIBER', 'the message now travels as light', t, T.wt(4, 'glass') - 0.2, T.lend(4) + 0.1, side=-1, up=-1, L=170)
    elif shot == 'coast':
        st = g('station')
        if st: callout(c, st[0], st[1], 'LANDING STATION', 'where the cable meets the sea', t, T.wt(5, 'coast') - 0.1, T.wt(5, 'ocean'), side=1, up=-1, L=140)
    elif shot == 'map':
        la = seg(t, 21.3, 21.8)*(1 - seg(t, 25.4, 25.8))
        if la > 0:
            for key, name, side in (('lagos', 'LAGOS', 1), ('bude', 'UK', -1), ('london', 'LONDON', 1)):
                p = g(key)
                if p and -50 < p[0] < 1130 and -50 < p[1] < 1130:
                    c.drawCircle(p[0], p[1], 9, P(GOLD, la)); c.drawCircle(p[0], p[1], 18, P(GOLD, 0.4*la, stroke=2.5))
                    txt(c, name, p[0] + side*26, p[1] + 10, 28, '#FFFFFF', 'xb', la, anchor='l' if side > 0 else 'r', spacing=2)
            txt(c, 'Route simplified', 44, 900, 18, '#DCE6FF', 'md', 0.6*la)
        counter(c, 560, 560, t, T.wt(6, 'far') - 0.3, T.wt(7, 'six'), T.lstart(7) + 1.6)
    elif shot == 'ocean':
        p = g('pulse')
        if p:
            callout(c, p[0] - 60, p[1] + 12, 'UNDERSEA CABLE', 'about as thick as a garden hose', t, T.wt(7, 'cable') - 0.1, T.lend(7) + 0.3, side=-1, up=-1, L=150)
        reps = g('reps')
        if reps:
            r = min(reps, key=lambda q: abs(q[0] - 540))
            callout(c, r[0], r[1] - 14, 'REPEATER', 'boosts the light every ~70 km', t, T.wt(8, 'repeater') - 0.2, T.lend(8), side=1, up=-1, L=150, accent=GOLD)
    elif shot == 'server':
        led = g('led')
        if led: callout(c, led[0], led[1], 'WHATSAPP SERVER', 'it holds the message for a moment', t, T.wt(9, 'server') - 0.15, T.wt(9, 'one') - 0.05, side=-1, up=-1, L=160)
        tick_bubble(c, 540, 300, 1, t, T.wt(9, 'one') - 0.15, T.wt(9, 'the', 1) - 0.05)
        cipher_panel(c, t, T.wt(9, 'the', 1) - 0.05, T.lend(9) + 0.3, T.wt(9, "can't"))
    elif shot == 'london':
        place_tag(c, t, 39.4, 40.4, 'London, UK', "Kemi's phone")
        tick_bubble(c, 540, 270, 2, t, T.wt(10, 'two') - 0.15, T.lstart(11) - 0.05)
        end_title(c, t, T.lstart(11) + 0.3)
        tick_bubble(c, 540, 270, 2, t, T.BLUE - 0.35, T.END + 5, blue_t=T.BLUE + 0.25)
    # a soft dark floor under the captions so they read on any picture
    c.drawRect(skia.Rect.MakeXYWH(0, 820, W, 260), _floor())
    hud_draw(c, t)
    captions(c, WORDS, tn if tn is not None else t)
