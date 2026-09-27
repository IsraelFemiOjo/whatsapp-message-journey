"""The v3 edit, locked to the narration. Output time is tau (seconds at 30 fps).
Each shot maps tau to the section's own source time through smooth keyframes, which gives the speed ramps."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import json, math, numpy as np
from scipy.interpolate import PchipInterpolator

FPS = 30
WORDS = json.load(open(ROOT + '/cartoon-version/words_3d.json'))
LINES = {}
for w in WORDS: LINES.setdefault(w['line'], []).append(w)
def wt(line, sub, k=0):
    hits = [w for w in LINES[line] if sub.lower() in w['w'].lower()]
    return hits[min(k, len(hits) - 1)]['s']
def lstart(l): return LINES[l][0]['s']
def lend(l): return LINES[l][-1]['e']
# ---- the new narration (Google AI Studio) and the warp from its timing onto the edit's timeline ----
NEW = json.load(open(ROOT + '/3d/v3/vo/gemini_words.json'))
NL = {}
for w in NEW: NL.setdefault(w['line'], []).append(w)
def nwt(line, sub, k=0):
    hits = [w for w in NL[line] if sub.lower() in w['w'].lower()]
    return hits[min(k, len(hits) - 1)]['s']
PAIRS = []
for l in range(12):
    PAIRS += [(lstart(l), NL[l][0]['s']), (lend(l), NL[l][-1]['e'])]
for ol, osub, ok, nl, nsub, nk in [(0, 'send', 0, 0, 'send', 0), 
        (2, 'locks', 0, 2, 'scrambles', 0), (2, 'you', 1, 2, 'you', 1), (2, 'friend', 0, 2, 'friend', 0), (2, 'not', 0, 2, 'not', 0), (2, 'whatsapp', 0, 2, 'whatsapp', 0),
        (4, 'light', 0, 4, 'light', 0), (4, 'glass', 0, 4, 'glass', 0),
        (5, 'coast', 0, 5, 'coast', 0), (5, 'dives', 0, 5, 'dives', 0), (5, 'ocean', 0, 5, 'atlantic', 0), (6, 'far', 0, 6, 'far', 0),
        (7, 'six', 0, 7, 'six', 0), (7, 'cable', 0, 7, 'cable', 0), (7, 'garden', 0, 7, 'garden', 0), (8, 'repeater', 0, 8, 'repeater', 0), (8, 'boosts', 0, 8, 'boosts', 0),
        (9, 'server', 0, 9, 'server', 0), (9, 'one', 0, 9, 'one', 0), (9, 'the', 1, 9, 'the', 1), (9, "can't", 0, 9, "can't", 0),
        (10, 'jumps', 0, 10, 'jumps', 0), (10, 'unlocks', 0, 10, 'unlocks', 0), (10, 'two', 0, 10, 'two', 0), (11, 'second', 0, 11, 'second', 0)]:
    PAIRS.append((wt(ol, osub, ok), nwt(nl, nsub, nk)))
PAIRS = [p for p in PAIRS if p[0] not in (lstart(6), lend(6))]
PAIRS = sorted(set(PAIRS), key=lambda p: p[1])
_o = [0.0]; _n = [0.0]
for o, n in PAIRS:
    if o > _o[-1] + 0.02 and n > _n[-1] + 0.02: _o.append(o); _n.append(n)
_o.append(_o[-1] + 10); _n.append(_n[-1] + 10)          # past the last anchor time runs at normal speed
def WARP(tn): return float(np.interp(tn, _n, _o))        # new narration time -> edit time
def UNWARP(to): return float(np.interp(to, _o, _n))      # edit time -> new narration time
END_NEW = NL[12][-1]['e'] + 0.7
BLUE = WARP(nwt(12, 'blue'))
END = WARP(END_NEW)

# (name, section, tau0, tau1, keyframes [(tau, src_t)], blend) ; blend: 'pair' mixes the two nearest renders, int n = motion blur samples
SHOTS = [
    ('opening', 'sec1_comp', 0.0, 1.88, [(0.0, 0.0), (1.88, 0.0)], None),
    ('lagos',  'sec1_comp', 1.84, 14.5, [(1.84, 0.0), (6.8, 0.56), (7.72, 1.62), (11.35, 2.2), (11.55, 2.3), (12.4, 3.25), (13.5, 4.75), (14.3, 5.8), (14.5, 5.97)], None),
    ('fiber',  'sec2_comp', 14.44, 18.3, [(14.44, 6.0), (15.25, 6.92), (17.55, 10.15), (18.3, 11.0)], None),
    ('coast',  'sec3_comp', 18.26, 21.15, [(18.26, 11.0), (20.45, 13.3), (21.15, 14.0)], None),
    ('map',    'sec4_comp', 20.45, 26.15, [(20.45, 13.3), (21.15, 14.0), (22.45, 15.4), (24.95, 17.6), (26.15, 18.6)], None),
    ('ocean',  'sec5_comp', 26.1, 32.8, [(26.1, 18.6), (27.0, 20.3), (29.2, 22.5), (31.72, 24.72), (32.12, 26.9), (32.8, 28.5)], 'pair'),
    ('server', 'sec6_comp', 32.76, 39.35, [(32.76, 28.5), (35.2, 29.9), (38.7, 31.85), (39.35, 35.5)], 'pair'),
    ('london', 'sec7_comp', 39.3, END + 0.3, [(39.3, 35.5), (40.25, 37.05), (42.4, 40.4), (43.3, 41.3), (45.7, 43.6), (END + 0.3, 43.6 + 0.9*(END + 0.3 - 45.7))], None),
]
SEC_START = {'sec1_comp': 0.0, 'sec2_comp': 6.0, 'sec3_comp': 11.0, 'sec4_comp': 13.3, 'sec5_comp': 18.6, 'sec6_comp': 28.5, 'sec7_comp': 35.5}
_MAPS = {}
def src_time(shot, tau):
    name = shot[0]
    if name not in _MAPS:
        k = np.array(shot[4]); _MAPS[name] = PchipInterpolator(k[:, 0], k[:, 1], extrapolate=True)
    return float(_MAPS[name](tau))
def speed(shot, tau):
    return float(_MAPS[shot[0]].derivative()(tau)) if shot[0] in _MAPS else 1.0

def active(tau):
    return [s for s in SHOTS if s[2] <= tau < s[3]]

# transitions between neighbouring shots: (tau_center, kind, half width)
TRANS = [(1.86, 'zoomthrough', 0.1), (14.47, 'zoomthrough', 0.12), (18.28, 'whip', 0.1), (20.8, 'dissolve', 0.35), (26.12, 'dive', 0.1),
         (32.78, 'zoomthrough', 0.1), (39.33, 'streak', 0.1)]
