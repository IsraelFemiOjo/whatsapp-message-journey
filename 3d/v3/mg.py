"""Motion graphics layer for v3 (skia): captions, callouts that draw themselves on, chips, counters, tick bubbles, titles, HUD."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import math, numpy as np, skia

W = H = 1080
FD = ROOT + '/3d/v3/fonts/'
TF = {'xb': skia.Typeface.MakeFromFile(FD + 'PlusJakartaSans-ExtraBold.ttf'), 'b': skia.Typeface.MakeFromFile(FD + 'PlusJakartaSans-Bold.ttf'),
      'sb': skia.Typeface.MakeFromFile(FD + 'PlusJakartaSans-SemiBold.ttf'), 'md': skia.Typeface.MakeFromFile(FD + 'PlusJakartaSans-Medium.ttf'),
      'mono': skia.Typeface.MakeFromFile(FD + 'JetBrainsMono-Bold.ttf'), 'monom': skia.Typeface.MakeFromFile(FD + 'JetBrainsMono-Medium.ttf')}
GOLD = '#FFC45E'; CYAN = '#5FE3FF'; PINK = '#FF5FA2'; INK = '#0B0F24'; RED = '#FF4D5E'

def col(h, a=1.0):
    h = h.lstrip('#'); return skia.Color4f(int(h[0:2], 16)/255, int(h[2:4], 16)/255, int(h[4:6], 16)/255, max(0, min(1, a)))
def P(c, a=1.0, blur=0, stroke=0):
    p = skia.Paint(AntiAlias=True); p.setColor4f(col(c, a))
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke); p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    return p
def font(sz, w='xb'): return skia.Font(TF[w], sz)
def seg(t, a, b): return min(1, max(0, (t - a)/(b - a)))
def ease(x): x = min(1, max(0, x)); return x*x*(3 - 2*x)
def eout(x): x = min(1, max(0, x)); return 1 - (1 - x)**3
def eout5(x): x = min(1, max(0, x)); return 1 - (1 - x)**5
def back(x, s=1.7):
    x = min(1, max(0, x)); return 1 + (s + 1)*(x - 1)**3 + s*(x - 1)**2
def inout(t, a, b, fi=0.25, fo=0.25): return seg(t, a, a + fi)*(1 - seg(t, b - fo, b))

def tw(s, sz, w='xb', spacing=0.0):
    f = font(sz, w); return f.measureText(s) + spacing*max(0, len(s) - 1)
def txt(c, s, x, y, sz, color='#FFFFFF', w='xb', a=1.0, anchor='l', spacing=0.0, shadow=True):
    f = font(sz, w); width = f.measureText(s) + spacing*max(0, len(s) - 1)
    if anchor == 'c': x -= width/2
    elif anchor == 'r': x -= width
    if spacing == 0:
        if shadow: c.drawString(s, x, y + sz*0.06, f, P('#000000', 0.45*a, blur=sz*0.12))
        c.drawString(s, x, y, f, P(color, a))
    else:
        cx = x
        for ch in s:
            if shadow: c.drawString(ch, cx, y + sz*0.06, f, P('#000000', 0.45*a, blur=sz*0.12))
            c.drawString(ch, cx, y, f, P(color, a)); cx += f.measureText(ch) + spacing
    return width

def rrect(c, x, y, w, h, r, paint): c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, paint)
def glass(c, x, y, w, h, r=18, a=1.0, tint='#0B0F2E'):
    rrect(c, x, y + 6, w, h, r, P('#000000', 0.35*a, blur=14))
    rrect(c, x, y, w, h, r, P(tint, 0.72*a))
    rrect(c, x, y, w, h, r, P('#FFFFFF', 0.16*a, stroke=1.5))

def draw_path_k(c, pts, k, paint):
    if k <= 0 or len(pts) < 2: return None
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    pm = skia.PathMeasure(p, False); L = pm.getLength(); dst = skia.Path(); pm.getSegment(0, L*min(1, k), dst, True)
    c.drawPath(dst, paint)
    pos, _ = pm.getPosTan(L*min(1, k)); return (pos.x(), pos.y())

# ---------------- captions: sentence case, words rise in, the accented words glow gold ----------------
def make_chunks(words):
    ch = 0; n = 0
    for i, w in enumerate(words):
        if i and (words[i - 1]['line'] != w['line'] or n >= 6 or words[i - 1]['w'][-1] in '.?!' or (words[i - 1]['w'][-1] == ',' and n >= 3)):
            ch += 1; n = 0
        w['chunk'] = ch; n += 1
    return words
def captions(c, words, t, y=990, sz=56, maxw=960):
    cur = [w for w in words if w['s'] - 0.08 <= t]
    if not cur: return
    last = cur[-1]
    chunk = [w for w in words if w['chunk'] == last['chunk']]
    end = chunk[-1]['e'] + 0.35
    nxt = [w for w in words if w['chunk'] == last['chunk'] + 1]
    if nxt: end = min(end, nxt[0]['s'] - 0.08)
    if t > end: return
    fa = 1 - seg(t, end - 0.12, end)
    f = font(sz, 'xb'); sp = f.measureText(' ')
    ws = [f.measureText(w['w']) for w in chunk]
    lines, cl, cw = [], [], 0
    for i, wv in enumerate(ws):
        if cl and cw + sp + wv > maxw: lines.append(cl); cl, cw = [], 0
        cw += (sp if cl else 0) + wv; cl.append(i)
    if cl: lines.append(cl)
    lh = sz*1.18; y0 = y - (len(lines) - 1)*lh
    for li, ln in enumerate(lines):
        tot = sum(ws[i] for i in ln) + sp*(len(ln) - 1); x = W/2 - tot/2
        for i in ln:
            w = chunk[i]
            k = seg(t, w['s'] - 0.08, w['s'] + 0.12)
            if k > 0:
                yy = y0 + li*lh + (1 - eout(k))*16
                a = eout(k)*fa
                color = GOLD if w.get('acc') else '#FFFFFF'
                c.drawString(w['w'], x, yy + 4, f, P('#000000', 0.55*a, blur=10))
                c.drawString(w['w'], x, yy, f, P('#05071A', 0.6*a, stroke=6))
                c.drawString(w['w'], x, yy, f, P(color, a))
            x += ws[i] + sp

# ---------------- callouts: ping, leader line draws on, label wipes in ----------------
def callout(c, ax, ay, title, sub, t, t0, t1, side=1, up=-1, L=160, dx=60, accent=CYAN):
    k_in = seg(t, t0, t0 + 0.55); k_out = seg(t, t1 - 0.3, t1)
    if k_in <= 0 or k_out >= 1: return
    a = 1 - ease(k_out)
    # ping
    pk = seg(t, t0, t0 + 0.6)
    c.drawCircle(ax, ay, 6 + 26*eout(pk), P(accent, (1 - pk)*0.9*a, stroke=2.5))
    c.drawCircle(ax, ay, 6, P('#FFFFFF', a)); c.drawCircle(ax, ay, 11, P(accent, a, stroke=2))
    ex, ey = ax + side*dx, ay + up*L*0.7
    fx = ex + side*L
    end = draw_path_k(c, [(ax, ay), (ex, ey), (fx, ey)], eout(seg(t, t0 + 0.05, t0 + 0.45)), P('#FFFFFF', 0.9*a, stroke=2.2))
    # label
    lk = eout5(seg(t, t0 + 0.3, t0 + 0.75))
    if lk > 0:
        tsz, ssz = 36, 25
        wt_ = max(tw(title, tsz, 'xb', 1.5), tw(sub, ssz, 'md')) + 40 if sub else tw(title, tsz, 'xb', 1.5) + 40
        hh = 60 + (38 if sub else 0)
        bx = fx if side > 0 else fx - wt_
        if bx + wt_ > W - 24: bx = W - 24 - wt_
        if bx < 24: bx = 24
        by = ey - hh - 10
        c.save(); c.clipRect(skia.Rect.MakeXYWH(bx if side > 0 else bx + wt_*(1 - lk), by - 20, wt_*lk, hh + 40))
        glass(c, bx, by, wt_, hh, 14, a)
        rrect(c, bx, by, 6, hh, 3, P(accent, a))
        txt(c, title, bx + 22, by + 44, tsz, '#FFFFFF', 'xb', a, spacing=1.5)
        if sub:
            sk = seg(t, t0 + 0.55, t0 + 1.1)
            n = int(len(sub)*sk)
            txt(c, sub[:n], bx + 22, by + 84, ssz, '#DCE6FF', 'md', a)
        c.restore()

def chip(c, x, y, label, t, t0, t1, icon=None, color='#FFFFFF', bg='#12163A', strike=None, sz=38):
    k = seg(t, t0, t0 + 0.4); ko = seg(t, t1 - 0.25, t1)
    if k <= 0 or ko >= 1: return
    s = back(k, 2.2)*(1 - 0.15*ease(ko)); a = 1 - ease(ko)
    w_ = tw(label, sz, 'xb') + (86 if icon else 44); h_ = sz*1.9
    c.save(); c.translate(x, y); c.scale(s, s)
    glass(c, -w_/2, -h_/2, w_, h_, h_/2, a, bg)
    ox = -w_/2 + 22
    if icon == 'key':
        c.drawCircle(ox + 14, 0, 11, P(GOLD, a, stroke=4)); c.drawLine(ox + 25, 0, ox + 46, 0, P(GOLD, a, stroke=4)); c.drawLine(ox + 40, 0, ox + 40, 8, P(GOLD, a, stroke=4))
        ox += 58
    txt(c, label, ox, sz*0.36, sz, color, 'xb', a, shadow=False)
    if strike is not None:
        sk = eout(seg(t, strike, strike + 0.3))
        if sk > 0:
            c.drawLine(-w_/2 + 14, 0, -w_/2 + 14 + (w_ - 28)*sk, 0, P(RED, a, stroke=6))
    c.restore()

def tick_bubble(c, x, y, n, t, t0, t1, label='Hello from Lagos!', s=1.35, blue_t=None):
    """the sender's view of the message with n grey ticks drawing on"""
    k = seg(t, t0, t0 + 0.45); ko = seg(t, t1 - 0.3, t1)
    if k <= 0 or ko >= 1: return
    a = 1 - ease(ko); sc = back(k, 1.9)*s
    c.save(); c.translate(x, y); c.scale(sc, sc)
    w_, h_ = 420, 92
    rrect(c, -w_/2, -h_/2 + 8, w_, h_, 26, P('#000000', 0.4*a, blur=14))
    rrect(c, -w_/2, -h_/2, w_, h_, 26, P('#005C4B', a))
    txt(c, label, -w_/2 + 26, 10, 32, '#E9EDEF', 'sb', a, shadow=False)
    txt(c, '21:47', w_/2 - 100, 32, 18, '#9FC9BD', 'md', a, shadow=False)
    for i in range(n):
        kk = eout(seg(t, t0 + 0.3 + i*0.22, t0 + 0.6 + i*0.22))
        if kk <= 0: continue
        ox = w_/2 - 44 + i*14
        blue = blue_t is not None and t >= blue_t + i*0.08
        draw_path_k(c, [(ox - 12, 18), (ox - 4, 26), (ox + 12, 8)], kk, P('#53BDEB' if blue else '#AEBAC1', a, stroke=4.5 + (1.5*math.exp(-((t - blue_t)/0.12)**2) if blue_t else 0)))
    c.restore()
    # the big label beside it
    return sc

def hud(c, t, chapter, name, elapsed, prog):
    # chapter tag
    a = 1.0
    txt(c, chapter, 44, 64, 22, GOLD, 'mono', a, shadow=True)
    c.drawLine(92, 57, 132, 57, P('#FFFFFF', 0.6, stroke=2))
    txt(c, name, 144, 64, 22, '#FFFFFF', 'b', 0.95, spacing=2.5)
    # elapsed timer
    txt(c, 'ELAPSED', W - 44, 50, 15, '#DCE6FF', 'sb', 0.8, anchor='r', spacing=2)
    txt(c, elapsed, W - 44, 90, 36, '#FFFFFF', 'mono', 1.0, anchor='r')
    # progress line with the journey's stops
    x0, x1, y = 44, W - 44, 112
    c.drawLine(x0, y, x1, y, P('#FFFFFF', 0.22, stroke=2))
    c.drawLine(x0, y, x0 + (x1 - x0)*prog, y, P(GOLD, 0.95, stroke=3))
    for i in range(8):
        x = x0 + (x1 - x0)*i/7
        c.drawCircle(x, y, 4, P(GOLD if prog*7 >= i - 1e-3 else '#6E7699', 1))
    c.drawCircle(x0 + (x1 - x0)*prog, y, 7, P('#FFF4D8', 1)); c.drawCircle(x0 + (x1 - x0)*prog, y, 14, P(GOLD, 0.35, blur=6))

def counter(c, x, y, t, t0, t_land, t1, final='6,000+ km', label='HOW FAR?'):
    k = seg(t, t0, t0 + 0.4); ko = seg(t, t1 - 0.3, t1)
    if k <= 0 or ko >= 1: return
    a = 1 - ease(ko)
    c.save(); c.translate(x, y); s = back(k, 2.0); c.scale(s, s)
    txt(c, label, 0, -70, 30, GOLD, 'xb', a, anchor='c', spacing=4)
    if t < t_land:
        v = int(abs(math.sin(t*37.1))*9000 + (t*3331) % 900)
        s_ = f'{v:,} km'; colr = '#FFFFFF'
        sc = 1.0
    else:
        s_ = final; colr = '#FFFFFF'; sc = back(seg(t, t_land, t_land + 0.35), 3.0)
    c.save(); c.scale(sc, sc)
    f = font(92, 'mono'); w_ = f.measureText(s_)
    glass(c, -w_/2 - 34, -86, w_ + 68, 124, 30, a, '#0B0F2E')
    if t >= t_land:
        fl = 1 - seg(t, t_land, t_land + 0.5)
        rrect(c, -w_/2 - 34, -86, w_ + 68, 124, 30, P(GOLD, 0.5*fl*a))
    c.drawString(s_, -w_/2, 8, f, P(colr, a))
    c.restore(); c.restore()

def end_title(c, t, t0):
    k1 = seg(t, t0, t0 + 0.5)
    if k1 <= 0: return
    sc = skia.Paint(AntiAlias=True)
    sc.setShader(skia.GradientShader.MakeRadial(skia.Point(W/2, 500), 620, [col('#05061A', 0.82*ease(k1)), col('#05061A', 0.55*ease(k1)), col('#05061A', 0.0)], [0, 0.55, 1]))
    c.drawRect(skia.Rect.MakeWH(W, H), sc)
    words = ['Under', 'a', 'second.']
    f = font(118, 'xb'); sp = f.measureText(' ')
    ws = [f.measureText(w) for w in words]; tot = sum(ws) + sp*2
    x = W/2 - tot/2; y = 560
    for i, w in enumerate(words):
        k = seg(t, t0 + 0.1 + i*0.12, t0 + 0.5 + i*0.12)
        if k <= 0: x += ws[i] + sp; continue
        yy = y + (1 - eout5(k))*90
        c.save(); c.clipRect(skia.Rect.MakeXYWH(x - 10, y - 130, ws[i] + 20, 175))
        c.drawString(w, x, yy + 8, f, P('#000000', 0.5, blur=16))
        c.drawString(w, x, yy, f, P(GOLD if i == 2 else '#FFFFFF'))
        c.restore()
        x += ws[i] + sp
    k2 = seg(t, t0 + 0.6, t0 + 1.0)
    if k2 > 0:
        txt(c, 'LAGOS', W/2 - 40, 400, 30, '#FFFFFF', 'xb', eout(k2), anchor='r', spacing=5)
        draw_path_k(c, [(W/2 - 22, 390), (W/2 + 22, 390)], eout(k2), P(GOLD, eout(k2), stroke=3))
        txt(c, 'LONDON', W/2 + 40, 400, 30, '#FFFFFF', 'xb', eout(k2), spacing=5)
