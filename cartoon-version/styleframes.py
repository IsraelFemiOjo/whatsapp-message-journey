import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import json, numpy as np
from PIL import Image
from toon import *
from props import *
from props import _path

words = json.load(open(ROOT + '/cartoon-version/words_af_heart.json'))
for i, w in enumerate(words): w['chunk'] = i//3

def frame_a():
    s, c = surface()
    c.drawRect(skia.Rect.MakeWH(W, H), LG(0, 0, W, H, ['#FFB36B', '#FF6F91']))
    for i in range(14):
        a = i*math.pi*2/14
        poly(c, [(540, 520), (540 + math.cos(a)*1200, 520 + math.sin(a)*1200), (540 + math.cos(a + 0.12)*1200, 520 + math.sin(a + 0.12)*1200)], P('#FFFFFF', 0.08))
    phone(c, 540, 700, 0.95, -6, chat_screen(sent=1, ticks=0, press=0.5))
    bubble(c, 560, 300, 1.15, look=(0.3, 0.4), happy=1)
    ws = [dict(w) for w in words[:5]]
    for w in ws: w['chunk'] = 0
    ws[4]['key'] = True
    caption(c, ws, 1.3, y=1000, size=78)
    return to_array(s)

def frame_b():
    s, c = surface()
    sky(c, '#3FB8FF', '#BDEBFF')
    sun(c, 860, 170, 64)
    cloud(c, 220, 170, 1.0, 0.95); cloud(c, 700, 260, 0.7, 0.9)
    base = 760
    for i in range(9): building(c, -40 + i*130, base, 120, 380 + (i*97 % 180), '#9FD3F0', seed=40 + i, windows=False)
    xs = [-20, 150, 290, 430, 620, 780]
    hs = [330, 420, 280, 360, 300, 240]
    for i, (x, h) in enumerate(zip(xs, hs)):
        building(c, x, base, 150 + (i % 2)*30, h, LAGOS_B[i], seed=i, roof='tank' if i % 2 else 'flat')
    tower(c, 900, base, 600, t=0.3)
    palm(c, 110, base, 1.1, 0.2); palm(c, 600, base, 0.9, -0.1)
    c.drawRect(skia.Rect.MakeXYWH(0, base, W, 90), P('#4A5568'))
    for i in range(8): rr(c, 30 + i*140, base + 40, 70, 10, 5, P('#FFFFFF', 0.8))
    c.drawRect(skia.Rect.MakeXYWH(0, base + 90, W, 40), P('#CBD5E0'))
    danfo(c, 420, base + 70, 0.9, 0.2)
    soil(c, base + 130)
    # the phone in a window, waves to the tower
    rr(c, 318, 520, 70, 110, 16, P('#1B2A4A')); rr(c, 326, 530, 54, 90, 10, P('#8CF0B4'))
    glow(c, 353, 575, 130, '#FFFFFF', 0.8); rr(c, 318, 520, 70, 110, 16, P('#1B2A4A')); rr(c, 326, 530, 54, 90, 10, P('#8CF0B4'))
    radio_arcs(c, 353, 540, 0.35, dirn=-28, n=4, colr='#FF8A00', spread=40)
    bubble(c, 640, 360, 0.42, look=(1, -0.6), happy=0.6, locked=1.0)
    label(c, 'RADIO WAVES', 520, 250, 36, '#FFFFFF', INK, k=1.0)
    ws = [dict(w) for w in words if w['line'] == 2]
    for w in ws: w['chunk'] = 0
    for w in ws:
        if w['w'].lower().startswith('radio') or w['w'].lower().startswith('waves'): w['key'] = True
    caption(c, ws[:5], 10.2, y=1000, size=78)
    return to_array(s)

def frame_c():
    s, c = surface()
    c.drawRect(skia.Rect.MakeWH(W, H), LG(0, 0, 0, H, ['#1FA2E0', '#0B5FA8', '#093E78']))
    light_rays(c, 1.0, 0.10)
    # seabed
    bed = [(x, 820 + 30*math.sin(x/140) + 12*math.sin(x/53)) for x in range(-20, W + 60, 40)]
    p = skia.Path(); p.moveTo(-20, H + 10)
    for q in bed: p.lineTo(*q)
    p.lineTo(W + 60, H + 10); p.close()
    c.drawPath(p, LG(0, 780, 0, H, ['#F2C57C', '#D99A56']))
    for i in range(7): seaweed(c, 60 + i*160, 850, 120 + (i % 3)*40, 1.0 + i)
    for i, (x, y) in enumerate(((180, 880), (520, 900), (880, 870))):
        c.drawOval(skia.Rect.MakeXYWH(x - 50, y - 24, 100, 48), P('#B97A45'))
    # cable
    cab = [(x, 800 + 18*math.sin(x/220)) for x in range(-40, W + 80, 30)]
    c.drawPath(_path(cab), P('#1E2A3A', stroke=40)); c.drawPath(_path(cab), P('#34495E', stroke=26))
    c.drawPath(_path([(x, y) for x, y in cab if x < 560]), P('#FFE066', 0.9, stroke=10))
    repeater(c, 800, 800 + 18*math.sin(800/220) - 6, 0.3, 0.9)
    comet(c, 560, 790, 0.0, 1.0, 0.9)
    fish(c, 240, 380, 1.0, '#FF9F1C', t=1); fish(c, 330, 450, 0.7, '#FF6F91', t=2); fish(c, 820, 300, 0.9, '#FFD60A', True, t=3)
    bubbles_up(c, 3.0, 20)
    label(c, 'REPEATER', 800, 640, 36, '#FFFFFF', INK, k=1.0, pointer=(800, 770))
    # depth gauge
    rr(c, 950, 140, 90, 400, 45, P('#000000', 0.25))
    rr(c, 962, 152, 66, 376, 33, LG(0, 152, 0, 528, ['#7FD6FF', '#0B3C70']))
    text(c, '3.6 km', 995, 580, 34, '#FFFFFF', 'Black', 'c', stroke=8)
    ws = [dict(w) for w in words if w['line'] == 6]
    for w in ws: w['chunk'] = 0
    for w in ws:
        if 'repeater' in w['w'].lower(): w['key'] = True
    caption(c, ws, 30, y=1010, size=78)
    return to_array(s)

if __name__ == '__main__':
    out = '/tmp/claude-0/-home-claude/e60f5fed-daab-5351-a4b6-b1dafa018dc3/scratchpad'
    ims = [frame_a(), frame_b(), frame_c()]
    for i, im in enumerate(ims): Image.fromarray(im).save(ROOT + f'/cartoon-version/sf_{i}.png')
    strip = np.concatenate([np.array(Image.fromarray(im).resize((540, 540))) for im in ims], 1)
    Image.fromarray(strip).save(f'{out}/sf_strip.png')
