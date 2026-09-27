"""A WhatsApp style dark mode chat screen (no logos), drawn at phone resolution."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
from PIL import Image, ImageDraw, ImageFont
FD = ROOT + '/3d/fonts/'
def F(size, w=400):
    f = ImageFont.truetype(FD + 'Inter', int(size))
    try: f.set_variation_by_axes([14, w])
    except Exception:
        try: f.set_variation_by_axes([w])
        except Exception: pass
    return f

W, H = 1100, 2400
BG, HEAD, IN_B, OUT_B, GREEN, TXT, SUB = '#0B141A', '#1F2C34', '#1F2C34', '#005C4B', '#00A884', '#E9EDEF', '#8696A0'

def wrap(d, text, font, maxw):
    words, lines, cur = text.split(), [], ''
    for w in words:
        t = (cur + ' ' + w).strip()
        if d.textlength(t, font=font) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur); return lines

def screen(typed='Hello from Lagos!', sent=False, ticks=0, cursor=True, press=0.0, scramble=None):
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    # faint wallpaper texture
    for y in range(260, H - 200, 90):
        for x in range((y//90) % 2*45, W, 90): d.ellipse([x, y, x + 4, y + 4], fill='#0F1B22')
    # status bar
    d.text((70, 38), '21:47', font=F(38, 600), fill=TXT)
    for i, h in enumerate((14, 20, 26, 32)): d.rectangle([W - 250 + i*16, 72 - h, W - 240 + i*16, 72], fill=TXT)
    d.rounded_rectangle([W - 150, 44, W - 80, 74], radius=8, outline=TXT, width=3); d.rectangle([W - 146, 48, W - 100, 70], fill=TXT)
    # header
    d.rectangle([0, 110, W, 290], fill=HEAD)
    d.line([(58, 200), (82, 176), (58, 200), (82, 224)], fill=TXT, width=6, joint='curve')
    d.ellipse([110, 145, 220, 255], fill='#6B4FBB'); d.text((165, 200), 'T', font=F(54, 600), fill='#FFFFFF', anchor='mm')
    d.text((250, 158), 'Tolu', font=F(46, 600), fill=TXT)
    d.text((250, 216), 'online', font=F(32), fill=SUB)
    # date chip and the encryption notice
    d.rounded_rectangle([W/2 - 90, 330, W/2 + 90, 385], radius=14, fill='#182229'); d.text((W/2, 357), 'Today', font=F(30, 500), fill=SUB, anchor='mm')
    note = 'Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.'
    lines = wrap(d, note, F(29), W - 300)
    y0 = 420; h = 40*len(lines) + 40
    d.rounded_rectangle([130, y0, W - 130, y0 + h], radius=18, fill='#182229')
    for i, l in enumerate(lines): d.text((W/2, y0 + 40 + i*40), l, font=F(29), fill='#FFD279', anchor='mm')
    # earlier today: the flight out
    y = y0 + h + 50
    def bubble(y, text, t, out=False):
        fl = F(40); tw = d.textlength(text, font=fl)
        if out:
            x1 = W - 40; x0 = x1 - tw - 230
            d.rounded_rectangle([x0, y, x1, y + 110], radius=24, fill=OUT_B)
            d.text((x0 + 30, y + 30), text, font=fl, fill=TXT); d.text((x1 - 70, y + 90), t, font=F(26), fill='#9FC9BD', anchor='rs')
            for k in range(2):
                xx = x1 - 56 + k*16; d.line([(xx, y + 76), (xx + 8, y + 86), (xx + 24, y + 64)], fill='#53BDEB', width=5)
        else:
            d.rounded_rectangle([40, y, 40 + tw + 190, y + 110], radius=24, fill=IN_B)
            d.text((70, y + 30), text, font=fl, fill=TXT); d.text((40 + tw + 170, y + 90), t, font=F(26), fill=SUB, anchor='rs')
        return y + 140
    # our message once sent
    info = {}
    m = typed if scramble is None else scramble
    fm = F(40); tw = d.textlength(m, font=fm); yb = y + 10
    info['text'] = ((W - 40 - tw - 200)/W, (yb + 30)/H, 40/H, tw/W)
    info['bubble'] = ((W - 40 - tw/2 - 115)/W, (yb + 55)/H)
    if sent:
        d.rounded_rectangle([W - 40 - tw - 230, yb, W - 40, yb + 110], radius=24, fill=OUT_B)
        d.text((W - 40 - tw - 200, yb + 30), m, font=fm, fill=TXT)
        if ticks == 0:   # waiting: a small clock
            cxk, cyk = W - 80, yb + 80
            d.ellipse([cxk - 12, cyk - 12, cxk + 12, cyk + 12], outline='#9FC9BD', width=3); d.line([(cxk, cyk), (cxk, cyk - 7), (cxk, cyk), (cxk + 6, cyk)], fill='#9FC9BD', width=3)
        d.text((W - 110, yb + 90), '21:47', font=F(26), fill='#9FC9BD', anchor='rs')
        for k in range(ticks):   # grey ticks
            x = W - 96 + k*16
            d.line([(x, yb + 76), (x + 8, yb + 86), (x + 24, yb + 64)], fill='#9FC9BD', width=5)
    # input bar
    yb = H - 190
    d.rounded_rectangle([30, yb, W - 170, yb + 130], radius=65, fill=HEAD)
    if not sent:
        d.text((110, yb + 65), typed, font=F(40), fill=TXT, anchor='lm')
        if cursor:
            x = 110 + d.textlength(typed, font=F(40)) + 6
            d.rectangle([x, yb + 38, x + 4, yb + 92], fill=GREEN)
    else:
        d.text((110, yb + 65), 'Message', font=F(40), fill=SUB, anchor='lm')
    cx, cy, r = W - 95, yb + 65, 65*(1 - 0.08*press)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
    # paper plane icon
    s = r/65
    d.polygon([(cx - 26*s, cy - 24*s), (cx + 30*s, cy), (cx - 26*s, cy + 24*s), (cx - 18*s, cy)], fill='#0B141A')
    info['send'] = (cx/W, cy/H)
    return im, info

if __name__ == '__main__':
    screen()[0].save('/tmp/claude-0/-home-claude/e60f5fed-daab-5351-a4b6-b1dafa018dc3/scratchpad/t/ui.png')


def screen_recv(text, show=1.0, sender='Kemi', cursor=False):
    """the friend's phone in London: the message arrives on the left"""
    im = Image.new('RGB', (W, H), BG); d = ImageDraw.Draw(im)
    for y in range(260, H - 200, 90):
        for x in range((y//90) % 2*45, W, 90): d.ellipse([x, y, x + 4, y + 4], fill='#0F1B22')
    d.text((70, 38), '21:47', font=F(38, 600), fill=TXT)
    for i, h in enumerate((14, 20, 26, 32)): d.rectangle([W - 250 + i*16, 72 - h, W - 240 + i*16, 72], fill=TXT)
    d.rounded_rectangle([W - 150, 44, W - 80, 74], radius=8, outline=TXT, width=3); d.rectangle([W - 146, 48, W - 110, 70], fill=TXT)
    d.rectangle([0, 110, W, 290], fill=HEAD)
    d.line([(58, 200), (82, 176), (58, 200), (82, 224)], fill=TXT, width=6, joint='curve')
    d.ellipse([110, 145, 220, 255], fill='#C26A2E'); d.text((165, 200), sender[0], font=F(54, 600), fill='#FFFFFF', anchor='mm')
    d.text((250, 158), sender, font=F(46, 600), fill=TXT); d.text((250, 216), 'online', font=F(32), fill=SUB)
    d.rounded_rectangle([W/2 - 90, 330, W/2 + 90, 385], radius=14, fill='#182229'); d.text((W/2, 357), 'Today', font=F(30, 500), fill=SUB, anchor='mm')
    note = 'Messages and calls are end-to-end encrypted. No one outside of this chat, not even WhatsApp, can read or listen to them.'
    lines = wrap(d, note, F(29), W - 300); y0 = 420; h = 40*len(lines) + 40
    d.rounded_rectangle([130, y0, W - 130, y0 + h], radius=18, fill='#182229')
    for i, l in enumerate(lines): d.text((W/2, y0 + 40 + i*40), l, font=F(29), fill='#FFD279', anchor='mm')
    yb = y0 + h + 60; info = {}
    fl = F(40); full = 'Hello from Lagos!'; tw = d.textlength(full, font=fl)
    info['bubble'] = ((40 + (tw + 190)/2)/W, (yb + 55)/H); info['text'] = (70/W, (yb + 30)/H, 40/H, tw/W)
    if show > 0:
        s = show
        x1 = 40 + (tw + 190)*s
        d.rounded_rectangle([40, yb, x1, yb + 110], radius=24, fill=IN_B)
        if s > 0.95:
            d.text((70, yb + 30), text, font=fl, fill=TXT); d.text((40 + tw + 170, yb + 90), '21:47', font=F(26), fill=SUB, anchor='rs')
    yb2 = H - 190
    d.rounded_rectangle([30, yb2, W - 170, yb2 + 130], radius=65, fill=HEAD)
    d.text((110, yb2 + 65), 'Message', font=F(40), fill=SUB, anchor='lm')
    cx, cy, r = W - 95, yb2 + 65, 65
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=GREEN)
    d.rounded_rectangle([cx - 12, cy - 30, cx + 12, cy + 6], radius=12, fill='#0B141A'); d.arc([cx - 22, cy - 14, cx + 22, cy + 18], 0, 180, fill='#0B141A', width=5)
    d.line([(cx, cy + 18), (cx, cy + 28)], fill='#0B141A', width=5)
    return im, info
