"""Flat cartoon drawing kit on skia: bright rounded shapes, soft shadows, glow, bold captions."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import math, numpy as np, skia

W = H = 1080
FD = ROOT + '/cartoon-version/fonts'
TF = {k: skia.Typeface.MakeFromFile(f'{FD}/Poppins-{k}.ttf') for k in ('Black', 'ExtraBold', 'Bold', 'SemiBold')}

def col(h, a=1.0):
    h = h.lstrip('#')
    if len(h) == 3: h = ''.join(ch*2 for ch in h)
    r, g, b = (int(h[i:i+2], 16) for i in (0, 2, 4))
    return skia.Color4f(r/255, g/255, b/255, a)
def mix(h1, h2, k):
    a = [int(h1.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)]; b = [int(h2.lstrip('#')[i:i+2], 16) for i in (0, 2, 4)]
    return '#' + ''.join(f'{int(x + (y - x)*k):02x}' for x, y in zip(a, b))

def ease(x): x = min(1, max(0, x)); return x*x*(3 - 2*x)
def eout(x): x = min(1, max(0, x)); return 1 - (1 - x)**3
def ein(x): x = min(1, max(0, x)); return x**3
def eio(x): x = min(1, max(0, x)); return 4*x**3 if x < 0.5 else 1 - (-2*x + 2)**3/2
def back(x, s=1.9):
    x = min(1, max(0, x)); return 1 + (s + 1)*(x - 1)**3 + s*(x - 1)**2
def elastic(x):
    x = min(1, max(0, x))
    if x in (0, 1): return x
    return 2**(-10*x)*math.sin((x*10 - 0.75)*(2*math.pi/3)) + 1
def seg(t, a, b): return min(1, max(0, (t - a)/(b - a)))
def lerp(a, b, k): return a + (b - a)*k

def P(c, a=1.0, aa=True, blur=0, stroke=0, cap=None):
    p = skia.Paint(AntiAlias=aa)
    p.setColor4f(col(c, a) if isinstance(c, str) else c)
    if blur: p.setMaskFilter(skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur))
    if stroke:
        p.setStyle(skia.Paint.kStroke_Style); p.setStrokeWidth(stroke)
        p.setStrokeCap(skia.Paint.kRound_Cap); p.setStrokeJoin(skia.Paint.kRound_Join)
    return p
def LG(x0, y0, x1, y1, cs, pos=None, a=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeLinear([skia.Point(x0, y0), skia.Point(x1, y1)], [col(c, a) for c in cs], pos))
    return p
def RG(x, y, r, cs, pos=None, a=1.0):
    p = skia.Paint(AntiAlias=True)
    p.setShader(skia.GradientShader.MakeRadial(skia.Point(x, y), max(r, 0.01), [col(c, a) if isinstance(c, str) else c for c in cs], pos))
    return p

def rr(c, x, y, w, h, r, paint): c.drawRoundRect(skia.Rect.MakeXYWH(x, y, w, h), r, r, paint)
def circ(c, x, y, r, paint): c.drawCircle(x, y, r, paint)
def poly(c, pts, paint, close=True):
    p = skia.Path(); p.moveTo(*pts[0])
    for q in pts[1:]: p.lineTo(*q)
    if close: p.close()
    c.drawPath(p, paint)
def smooth(c, pts, paint, close=False):
    """catmull rom through points"""
    p = skia.Path(); p.moveTo(*pts[0]); n = len(pts)
    for i in range(n - 1):
        p0 = pts[max(0, i - 1)]; p1 = pts[i]; p2 = pts[i + 1]; p3 = pts[min(n - 1, i + 2)]
        c1 = (p1[0] + (p2[0] - p0[0])/6, p1[1] + (p2[1] - p0[1])/6); c2 = (p2[0] - (p3[0] - p1[0])/6, p2[1] - (p3[1] - p1[1])/6)
        p.cubicTo(*c1, *c2, *p2)
    if close: p.close()
    c.drawPath(p, paint); return p

def shadow(c, x, y, w, h, a=0.25, blur=14):
    c.drawOval(skia.Rect.MakeXYWH(x - w/2, y - h/2, w, h), P('#000000', a, blur=blur))

def glow(c, x, y, r, hexc, a=1.0):
    c.drawCircle(x, y, r, RG(x, y, r, [col(hexc, a), col(hexc, a*0.35), col(hexc, 0)], [0, 0.35, 1]))

def font(size, w='ExtraBold'): return skia.Font(TF[w], size)
def text_w(s, size, w='ExtraBold'): return font(size, w).measureText(s)
def text(c, s, x, y, size, fill='#FFFFFF', w='ExtraBold', anchor='l', stroke=0, stroke_c='#101828', a=1.0, shadow_=0):
    f = font(size, w); tw = f.measureText(s)
    if anchor == 'c': x -= tw/2
    elif anchor == 'r': x -= tw
    if shadow_: c.drawString(s, x, y + shadow_, f, P('#000000', 0.35*a, blur=shadow_*0.8))
    if stroke:
        sp = P(stroke_c, a, stroke=stroke); c.drawString(s, x, y, f, sp)
    c.drawString(s, x, y, f, P(fill, a))
    return tw

# ---------------- the message: a chat bubble with a face ----------------
BUB = '#2ED47A'; BUB_D = '#1FA85E'; INK = '#10233A'
def bubble(c, x, y, s=1.0, t=0.0, look=(0, 0), blink=False, label='Hello!', locked=0.0, happy=0.0, squash=1.0, rot=0.0, a=1.0, scram=False):
    """centered at x,y. width 300*s. locked 0..1 slides a padlock on."""
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(s*(2 - squash)**0.5, s*squash)
    w, h = 300, 200
    shadow(c, 0, 128, 240, 30, 0.18*a, 12)
    body = skia.Path(); body.addRoundRect(skia.Rect.MakeXYWH(-w/2, -h/2, w, h), 70, 70)
    tail = skia.Path(); tail.moveTo(-w/2 + 40, h/2 - 30); tail.cubicTo(-w/2 + 20, h/2 + 20, -w/2 - 20, h/2 + 40, -w/2 - 34, h/2 + 44)
    tail.cubicTo(-w/2 + 20, h/2 + 40, -w/2 + 70, h/2 + 20, -w/2 + 100, h/2 - 10); tail.close()
    c.drawPath(tail, P(BUB_D, a))
    c.drawPath(body, LG(0, -h/2, 0, h/2, ['#4BE894', BUB, BUB_D], [0, 0.55, 1], a=a))
    c.drawRoundRect(skia.Rect.MakeXYWH(-w/2 + 26, -h/2 + 16, w - 110, 26), 13, 13, P('#FFFFFF', 0.28*a))   # shine
    # eyes
    ex = 52; ey = -18; lx, ly = look
    for sx in (-1, 1):
        cx = sx*ex
        if blink: c.drawRoundRect(skia.Rect.MakeXYWH(cx - 22, ey - 3, 44, 7), 4, 4, P(INK, a))
        else:
            c.drawOval(skia.Rect.MakeXYWH(cx - 26, ey - 32, 52, 64), P('#FFFFFF', a))
            c.drawCircle(cx + 9*lx, ey + 8*ly + 4, 15, P(INK, a))
            c.drawCircle(cx + 9*lx + 5, ey + 8*ly - 3, 5.5, P('#FFFFFF', a))
    # mouth
    m = skia.Path(); mw = 34 + 14*happy
    m.moveTo(-mw, 34); m.cubicTo(-mw*0.5, 34 + 26 + 14*happy, mw*0.5, 34 + 26 + 14*happy, mw, 34)
    c.drawPath(m, P(INK, a, stroke=9))
    # cheeks
    for sx in (-1, 1): c.drawOval(skia.Rect.MakeXYWH(sx*98 - 18, 22, 36, 18), P('#FF8FA3', 0.55*a))
    if locked > 0:
        ly_ = lerp(-260, -h/2 - 10, back(locked))
        padlock(c, 104, ly_, 0.8, a*min(1, locked*3))
    c.restore()

def padlock(c, x, y, s=1.0, a=1.0, open_=0.0):
    c.save(); c.translate(x, y); c.scale(s, s)
    sh = skia.Path(); sh.moveTo(-34, 0); sh.lineTo(-34, -34); sh.cubicTo(-34, -84, 34, -84, 34, -34)
    sh.lineTo(34, 0 - 30*open_)
    c.save(); c.translate(0, -26*open_); c.rotate(-24*open_)
    c.drawPath(sh, P('#9AA7B8', a, stroke=16)); c.restore()
    rr(c, -54, -8, 108, 86, 20, LG(0, -8, 0, 78, ['#FFD34E', '#F5A623'], a=a))
    rr(c, -54 + 10, -8 + 8, 60, 14, 7, P('#FFFFFF', 0.35*a))
    c.drawCircle(0, 28, 11, P('#8A5A00', a)); rr(c, -5, 30, 10, 26, 5, P('#8A5A00', a))
    c.restore()

# ---------------- captions: few words at a time, the key word highlighted ----------------
HI = '#FFD60A'
def caption(c, words, t, y=880, size=84, keys=(), max_w=940):
    """words: list of {'w','s','e'}; shows the current chunk; the spoken word pops and key words are yellow."""
    cur = [w for w in words if w['s'] - 0.05 <= t]
    if not cur: return
    last = cur[-1]
    if t > last['e'] + 0.5: return
    chunk = [w for w in words if w.get('chunk') == last['chunk']]
    f = font(size, 'Black')
    toks = [w['w'].upper() for w in chunk]
    sp = f.measureText(' ')*1.9
    ws = [f.measureText(s) for s in toks]
    # wrap into lines
    lines, cl, cw = [], [], 0
    for i, wv in enumerate(ws):
        if cl and cw + sp + wv > max_w: lines.append(cl); cl, cw = [], 0
        cw += (sp if cl else 0) + wv; cl.append(i)
    if cl: lines.append(cl)
    lh = size*1.08
    y0 = y - (len(lines) - 1)*lh
    for li, ln in enumerate(lines):
        tot = sum(ws[i] for i in ln) + sp*(len(ln) - 1)
        x = W/2 - tot/2
        for i in ln:
            w = chunk[i]; s = toks[i]
            on = w['s'] - 0.05 <= t
            if not on: x += ws[i] + sp; continue
            k = seg(t, w['s'] - 0.05, w['s'] + 0.09)
            sc = 0.7 + 0.3*back(k, 2.4)
            key = w.get('key', False)
            c.save(); c.translate(x + ws[i]/2, y0 + li*lh - size*0.35); c.scale(sc, sc); c.translate(-(x + ws[i]/2), -(y0 + li*lh - size*0.35))
            yy = y0 + li*lh
            if key:
                pad = 14
                rr(c, x - pad, yy - size*0.84 + 6, ws[i] + 2*pad, size*1.02, 20, P('#000000', 0.35, blur=5))
                rr(c, x - pad, yy - size*0.84, ws[i] + 2*pad, size*1.02, 20, P(HI))
                c.drawString(s, x, yy, f, P(INK))
            else:
                c.drawString(s, x, yy + 7, f, P('#000000', 0.45, blur=6))
                c.drawString(s, x, yy, f, P(INK, stroke=size*0.16))
                c.drawString(s, x, yy, f, P('#FFFFFF'))
            c.restore()
            x += ws[i] + sp

def label(c, s, x, y, size=40, bg='#FFFFFF', fg=INK, a=1.0, k=1.0, pointer=None):
    """a sticker style label that pops in (k 0..1)"""
    if k <= 0: return
    sc = back(k, 2.2)
    f = font(size, 'ExtraBold'); tw = f.measureText(s); pw, ph = tw + size*0.9, size*1.45
    c.save(); c.translate(x, y); c.scale(sc, sc)
    if pointer:
        px, py = pointer[0] - x, pointer[1] - y
        c.drawLine(0, 0, px/sc, py/sc, P(bg, a, stroke=6))
        c.drawCircle(px/sc, py/sc, 10, P(bg, a))
    rr(c, -pw/2, -ph/2 + 6, pw, ph, ph/2, P('#000000', 0.25*a, blur=6))
    rr(c, -pw/2, -ph/2, pw, ph, ph/2, P(bg, a))
    c.drawString(s, -tw/2, size*0.36, f, P(fg, a))
    c.restore()

def surface():
    s = skia.Surface(W, H); return s, s.getCanvas()
def to_array(s):
    return s.makeImageSnapshot().toarray(colorType=skia.kRGBA_8888_ColorType)[..., :3]
