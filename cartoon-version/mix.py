"""Voice, cartoon sound effects on the picture's events, and the score ducked under the voice."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, json, math, numpy as np
sys.path.insert(0, ROOT + '/shared')
from sfx import *
from scipy.io import wavfile
from scipy.signal import resample_poly

words = json.load(open(ROOT + '/cartoon-version/words_am_puck.json'))
def wt(l, sub, k=0): return [x for x in words if x['line'] == l and sub.lower() in x['w'].lower()][k]['s']
T = {}
for w in words: T.setdefault(w['line'], w['s'])
DUR = words[-1]['e'] + 1.1
N = int(DUR*SR)
L = np.zeros(N); R = np.zeros(N)
def add(sig, t, g=1.0, pan=0.0):
    i = int(t*SR)
    if i >= N: return
    s = sig[:N - i]*g; a = (pan + 1)*math.pi/4
    L[i:i+len(s)] += s*math.cos(a)*1.41; R[i:i+len(s)] += s*math.sin(a)*1.41
def tt(d): return np.arange(int(d*SR))/SR
def pop(f=500):
    d = 0.16; t = tt(d); return norm(np.sin(2*np.pi*np.cumsum(f*(1 + 2.2*np.exp(-t/0.03)))/SR)*np.exp(-t/0.05))
def boing(f=180):
    d = 0.5; t = tt(d); return norm(np.sin(2*np.pi*np.cumsum(f*(1 + 0.35*np.sin(2*np.pi*14*t)*np.exp(-t/0.2)))/SR)*np.exp(-t/0.18))
def splash():
    d = 0.9; t = tt(d); s = bp(noise(d), 400, 6000)*np.exp(-t/0.16)*np.minimum(1, t/0.004) + 0.5*lp(noise(d), 600)*np.exp(-t/0.3)
    return norm(s)
def zap():
    d = 0.4; t = tt(d); return norm(chirp(300, 2600, d, 0.5)*np.exp(-t/0.15) + 0.4*hp(noise(d), 3000)*np.exp(-t/0.06))
def tick_s():
    d = 0.05; t = tt(d); return norm(np.sin(2*np.pi*2400*t)*np.exp(-t/0.008) + 0.3*hp(noise(d), 4000)*np.exp(-t/0.004))
def ding(f=1318.5):
    d = 1.0; t = tt(d); return norm(np.sin(2*np.pi*f*t)*np.exp(-t/0.3) + 0.5*np.sin(2*np.pi*f*1.5*t)*np.exp(-t/0.2))
def notif():
    return norm(np.concatenate([ding(1568)[:int(0.12*SR)], ding(2093)]))
def scramble_s(d=0.6):
    s = np.zeros(int(d*SR)); x = 0.0
    while x < d - 0.02:
        f = rng.choice([1800, 2400, 3100, 3700]); c = np.sin(2*np.pi*f*tt(0.012))*np.exp(-tt(0.012)/0.003)
        i = int(x*SR); s[i:i+len(c)] += c*rng.uniform(0.4, 1); x += rng.exponential(1/45)
    return norm(s)
def whoosh_s(d=0.45, f0=300, f1=3000): return norm(whoosh(d, f0, f1))

tap = wt(0, 'send') - 1.6 + 0.0
add(click(2600), 0.42, 0.5, -0.2)                               # thumb on send
add(zip_(0.14), 0.52, 0.35, 0.2); add(pop(420), 0.58, 0.55, 0.2)  # the message jumps out
add(pop(700), 1.0, 0.25, -0.4); add(pop(760), 1.12, 0.25, 0.4)   # question marks
add(tick_s(), wt(0, 'second') - 0.05, 0.3, 0.4); add(tick_s(), wt(0, 'second') + 0.2, 0.3, 0.4)
add(whoosh_s(0.5, 400, 3500), T[1] - 0.3, 0.45)                  # to the map
add(pop(520), T[1] + 0.05, 0.4, -0.2); add(pop(640), wt(1, 'london') - 0.05, 0.4, -0.3)
add(whoosh_s(0.45, 300, 5000), T[2] - 0.4, 0.5)                   # dive into Lagos
lk = wt(2, 'locks') + 0.25
add(clunk(), lk, 0.6); add(click(1800), lk + 0.02, 0.3)          # padlock slams on
add(scramble_s(0.65), lk + 0.2, 0.25, 0.1)
add(plink(2093), wt(2, 'only') + 0.05, 0.2, -0.5); add(plink(2637), wt(2, 'only') + 0.3, 0.2, 0.5)
add(boing(200), wt(2, 'whatsapp') + 0.05, 0.3, 0.4)              # the server pops up, confused
add(whoosh_s(0.5, 500, 3000), T[3] - 0.2, 0.4)
for k in range(5): add(blip(900 + 120*k), T[3] + 0.5 + k*0.3, 0.12, -0.3 + 0.15*k)   # radio waves
add(chime(1760, 0.8), wt(3, 'tower') + 0.35, 0.18, 0.3)
add(zap(), wt(4, 'light') - 0.02, 0.45)                          # becomes light
add(fade := norm(whoosh(2.6, 500, 2600)), wt(4, 'light') + 0.2, 0.22)
add(click(1400), T[5] + 0.15, 0.3)                                # into the station
add(splash(), wt(5, 'dives') + 0.2, 0.6)                          # into the sea
add(lp(noise(9.6), 300)*np.minimum(1, tt(9.6)/0.5)*np.minimum(1, (9.6 - tt(9.6))/0.4), T[6] - 0.3, 0.25)   # underwater rumble
for k in range(6): add(pop(300 + 60*k), T[6] + k*0.4, 0.06, -0.5 + 0.2*k)
add(pop(600), T[6] + 0.05, 0.35)                                  # HOW FAR card
add(ding(1318.5), wt(7, 'six') - 0.02, 0.35); add(thud(120, 50, 0.3), wt(7, 'six'), 0.4)   # the answer
add(pop(500), wt(7, 'garden') - 0.2, 0.35)
add(fwoomp(0.8, 200, 3000), wt(8, 'boosts') - 0.05, 0.4); add(chime(2349, 1.2), wt(8, 'boosts'), 0.15)
add(whoosh_s(0.6, 300, 4000), T[9] - 0.3, 0.45); add(splash(), T[9] - 0.2, 0.3)
add(thud(150, 60, 0.25), T[9] + 0.45, 0.45); add(pop(380), T[9] + 0.47, 0.3)   # lands on the server
add(tick_s(), wt(9, 'one') + 0.1, 0.5, 0.3)                       # one grey tick
add(boing(160), wt(9, "can't") - 0.1, 0.3, -0.3)
add(whoosh_s(0.45, 400, 6000), T[10] - 0.3, 0.55)                 # whip pan to London
add(notif(), T[10] + 0.4, 0.3, 0.1)
add(shimmer(0.8), wt(10, 'unlocks') - 0.05, 0.3); add(click(2800), wt(10, 'unlocks'), 0.35)
add(tick_s(), wt(10, 'two') + 0.1, 0.5, 0.3); add(tick_s(), wt(10, 'two') + 0.25, 0.5, 0.3)
add(whoosh_s(0.5, 300, 3000), T[11] - 0.3, 0.35)
add(chime(1174.7, 2.0), wt(11, 'second') + 0.02, 0.2); add(chime(1760, 2.0), wt(11, 'second') + 0.04, 0.12)

# voice
sr_v, v = wavfile.read(ROOT + '/cartoon-version/vo_proc.wav')
v = v.astype(np.float64)/32768
if v.ndim > 1: v = v.mean(1)
if sr_v != SR: v = resample_poly(v, SR, sr_v)
v = v[:N]; V = np.zeros(N); V[:len(v)] = v
# score
sr_m, m = wavfile.read(ROOT + '/cartoon-version/score.wav')
m = m.astype(np.float64)/32768
if sr_m != SR: m = resample_poly(m, SR, sr_m, axis=0)
ML = np.zeros(N); MR = np.zeros(N); n_ = min(N, len(m)); ML[:n_] = m[:n_, 0]; MR[:n_] = m[:n_, 1]
# duck the music under the voice
env = np.sqrt(np.clip(lp(V**2, 8), 0, None))
env = env/(env.max() + 1e-9)
duck = 1 - 0.45*np.clip(env*4, 0, 1)
duck = lp(duck, 6)
ML *= duck; MR *= duck
rv = np.sqrt(np.mean(V[np.abs(V) > 0.01]**2)); rm = np.sqrt(np.mean(((ML + MR)/2)**2))
mg = rv/rm*10**(-11/20)
print("nan", np.isnan(V).any(), np.isnan(ML).any(), np.isnan(L).any(), mg)
out_L = V + ML*mg + L*0.8
out_R = V + MR*mg + R*0.8
pk = max(np.abs(out_L).max(), np.abs(out_R).max())
out = np.stack([out_L, out_R], 1)/pk*0.9
fo = int(0.5*SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
wavfile.write(ROOT + '/cartoon-version/mix.wav', SR, (out*32767).astype(np.int16))
print('mix', DUR)
