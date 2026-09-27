"""Phone screens for v3 (light mode, so the phone reads bright and clear), driven by narration time:
typing, send, and the message text itself morphing into ciphertext and back."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import sys, math, numpy as np
sys.path.insert(0, ROOT + '/3d')
from PIL import Image, ImageDraw, ImageFont
from chatui import F, wrap, W, H
import sjtl as T

BG, BAR, OUT_B, IN_B, GREEN, TXT, SUB = '#EFEAE2', '#008069', '#D9FDD3', '#FFFFFF', '#00A884', '#111B21', '#667781'
LOCK_B, LOCK_L, CI = '#FFF1C9', '#E0A21B', '#9A6700'
MONO = ImageFont.truetype(ROOT + '/3d/v3/fonts/JetBrainsMono-Bold.ttf', 40)
PLAIN = 'Hello from Lagos!'
CIPHER = 'U2FsdGVkX19qK3Zw='          # looks like real encrypted output (same length as the message)
GLY = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=#%&@$'
CUR = {'tau': 0.0}
TYPE0, TYPE1 = 1.85, 2.42

def seg(t, a, b): return min(1, max(0, (t - a)/(b - a)))
def ease(x): x = min(1, max(0, x)); return x*x*(3 - 2*x)
def back(x, s=1.7):
    x = min(1, max(0, x)); return 1 + (s + 1)*(x - 1)**3 + s*(x - 1)**2

def morph_chars(tau, t0, forward=True, per=0.035, flick=0.16):
    out = []; rng = np.random.default_rng(int(tau*30))
    for i in range(len(PLAIN)):
        a = t0 + i*per
        st = 0 if tau < a else (2 if tau < a + flick else 1)
        if not forward: st = {0: 1, 1: 0, 2: 2}[st]
        ch = PLAIN[i] if st == 0 else (CIPHER[i] if st == 1 else GLY[rng.integers(len(GLY))])
        out.append((ch, st))
    return out

def draw_msg(d, x, y, chars):
    fl = F(40); cx = x
    for ch, st in chars:
        f = fl if st == 0 else MONO
        d.text((cx, y), ch, font=f, fill=TXT if st == 0 else (CI if st == 1 else '#E0A21B'))
        cx += d.textlength(ch, font=f)

def _base(d, name, avatar):
    for y in range(300, H - 200, 90):
        for x in range((y//90) % 2*45, W, 90): d.ellipse([x, y, x + 5, y + 5], fill='#E2DACF')
    d.rectangle([0, 0, W, 290], fill=BAR)
    d.text((70, 38), '21:47', font=F(38, 600), fill='#FFFFFF')
    for i, h in enumerate((14, 20, 26, 32)): d.rectangle([W - 250 + i*16, 72 - h, W - 240 + i*16, 72], fill='#FFFFFF')
    d.rounded_rectangle([W - 150, 44, W - 80, 74], radius=8, outline='#FFFFFF', width=3); d.rectangle([W - 146, 48, W - 100, 70], fill='#FFFFFF')
    d.line([(58, 200), (82, 176), (58, 200), (82, 224)], fill='#FFFFFF', width=6, joint='curve')
    d.ellipse([110, 145, 220, 255], fill=avatar); d.text((165, 200), name[0], font=F(54, 600), fill='#FFFFFF', anchor='mm')
    d.text((250, 158), name, font=F(46, 600), fill='#FFFFFF'); d.text((250, 216), 'online', font=F(32), fill='#D9FDD3')
    d.rounded_rectangle([W/2 - 90, 330, W/2 + 90, 385], radius=14, fill='#FFFFFF'); d.text((W/2, 357), 'Today', font=F(30, 500), fill=SUB, anchor='mm')
    note = 'Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.'
    lines = wrap(d, note, F(29), W - 300); y0 = 420; h = 40*len(lines) + 40
    d.rounded_rectangle([130, y0, W - 130, y0 + h], radius=18, fill='#FFEECD')
    for i, l in enumerate(lines): d.text((W/2, y0 + 40 + i*40), l, font=F(29), fill='#54656F', anchor='mm')
    return y0 + h

def padlock(d, cx, cy, s, col):
    d.arc([cx - 14*s, cy - 30*s, cx + 14*s, cy - 2*s], 180, 360, fill=col, width=int(5*s))
    d.line([(cx - 14*s, cy - 16*s), (cx - 14*s, cy - 4*s)], fill=col, width=int(5*s)); d.line([(cx + 14*s, cy - 16*s), (cx + 14*s, cy - 4*s)], fill=col, width=int(5*s))
    d.rounded_rectangle([cx - 20*s, cy - 6*s, cx + 20*s, cy + 22*s], radius=int(6*s), fill=col)

def _input(d, text=None, cursor=False, press=0.0, mic=False):
    yi = H - 190
    d.rounded_rectangle([30, yi, W - 170, yi + 130], radius=65, fill='#FFFFFF')
    if text: d.text((110, yi + 65), text, font=F(40), fill=TXT, anchor='lm')
    else: d.text((110, yi + 65), 'Message', font=F(40), fill=SUB, anchor='lm')
    if cursor:
        x = 110 + (d.textlength(text, font=F(40)) if text else 0) + 6
        d.rectangle([x, yi + 38, x + 4, yi + 92], fill=GREEN)
    cx, cy, r = W - 95, yi + 65, 65*(1 - 0.14*press)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
    s = r/65
    if mic:
        d.rounded_rectangle([cx - 12, cy - 30, cx + 12, cy + 6], radius=12, fill='#FFFFFF'); d.arc([cx - 22, cy - 14, cx + 22, cy + 18], 0, 180, fill='#FFFFFF', width=5)
        d.line([(cx, cy + 18), (cx, cy + 28)], fill='#FFFFFF', width=5)
    else:
        d.polygon([(cx - 26*s, cy - 24*s), (cx + 30*s, cy), (cx - 26*s, cy + 24*s), (cx - 18*s, cy)], fill='#FFFFFF')
    return cx, cy

def sender(typed='', sent=False, ticks=0, cursor=True, press=0.0, scramble=None):
    """replaces chatui.screen inside the Lagos plate; reads narration time"""
    tau = CUR['tau']
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    ybase = _base(d, 'Kemi', '#C26A2E')
    send_t = T.wt(0, 'send') + 0.02; lock_t = T.wt(2, 'locks') + 0.05
    tw = max(d.textlength(PLAIN, font=F(40)), d.textlength(CIPHER, font=MONO)) + 10
    yb = ybase + 60
    info = {'text': ((W - 40 - tw - 200)/W, (yb + 30)/H, 40/H, tw/W), 'bubble': ((W - 40 - tw/2 - 115)/W, (yb + 55)/H)}
    is_sent = tau >= send_t + 0.05
    if is_sent:
        k = back(seg(tau, send_t + 0.05, send_t + 0.3), 2.0)
        x1 = W - 40; x0 = x1 - (tw + 230); dy = (1 - k)*260
        lk = seg(tau, lock_t, lock_t + 0.9)
        d.rounded_rectangle([x0, yb + dy, x1, yb + 110 + dy], radius=24, fill=OUT_B if lk < 0.05 else LOCK_B, outline=(LOCK_L if lk > 0.3 else None), width=4)
        chars = morph_chars(tau, lock_t) if tau >= lock_t else [(c, 0) for c in PLAIN]
        draw_msg(d, x0 + 30, yb + 30 + dy, chars)
        d.text((W - 110, yb + 90 + dy), '21:47', font=F(26), fill=SUB, anchor='rs')
        if lk > 0.4: padlock(d, x0 - 46, yb + 50 + dy, 1.3*back(seg(tau, lock_t + 0.35, lock_t + 0.6), 2.4), LOCK_L)
        cxk, cyk = W - 80, yb + 80 + dy
        d.ellipse([cxk - 12, cyk - 12, cxk + 12, cyk + 12], outline=SUB, width=3); d.line([(cxk, cyk), (cxk, cyk - 7), (cxk, cyk), (cxk + 6, cyk)], fill=SUB, width=3)
        cx, cy = _input(d, None, False, math.sin(math.pi*seg(tau, send_t - 0.1, send_t + 0.12)))
    else:
        n = int(len(PLAIN)*seg(tau, TYPE0, TYPE1))
        cx, cy = _input(d, PLAIN[:n], (int(tau*3) % 2 == 0) or 0 < n < len(PLAIN), math.sin(math.pi*seg(tau, send_t - 0.1, send_t + 0.12)))
    info['send'] = (cx/W, cy/H)
    return im, info

def receiver(text='', show=1.0, sender='Kemi', cursor=False):
    """replaces chatui.screen_recv inside the London plate"""
    tau = CUR['tau']
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    ybase = _base(d, 'Tolu', '#6B4FBB')
    tw = max(d.textlength(PLAIN, font=F(40)), d.textlength(CIPHER, font=MONO)) + 10
    yb = ybase + 60; info = {}
    info['bubble'] = ((40 + (tw + 190)/2)/W, (yb + 55)/H); info['text'] = (70/W, (yb + 30)/H, 40/H, tw/W)
    un_t = T.wt(10, 'unlocks') + 0.02
    if show > 0:
        x1 = 40 + (tw + 190)*back(show, 1.4)
        uk = seg(tau, un_t, un_t + 0.9)
        d.rounded_rectangle([40, yb, x1, yb + 110], radius=24, fill=IN_B if uk > 0.9 else LOCK_B, outline=(LOCK_L if uk < 0.7 else None), width=4)
        if show > 0.95:
            chars = morph_chars(tau, un_t, forward=False) if tau >= un_t else [(c, 1) for c in CIPHER]
            draw_msg(d, 70, yb + 30, chars)
            d.text((40 + tw + 170, yb + 90), '21:47', font=F(26), fill=SUB, anchor='rs')
            if uk < 0.9: padlock(d, 40 + tw + 230, yb + 50 - 60*ease(uk), 1.3, LOCK_L)
    _input(d, None, False, 0.0, mic=True)
    return im, info
