"""Final sound for v3: narration on top, a quiet documentary bed, ambience for each place, and soft sounds on the motion."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import sys, math, numpy as np
sys.path.insert(0, ROOT + '/shared'); sys.path.insert(0, ROOT + '/3d/v3')
from sfx import *
from scipy.io import wavfile
from scipy.signal import resample_poly
import sjtl as T

DUR = T.END_NEW; N = int(DUR*SR)
L = np.zeros(N); R = np.zeros(N)
def add(sig, t, g=1.0, pan=0.0, new=False):
    i = int((t if new else T.UNWARP(t))*SR)
    if i >= N or i < 0: return
    s = sig[:N - i]*g; a = (pan + 1)*math.pi/4
    L[i:i+len(s)] += s*math.cos(a)*1.41; R[i:i+len(s)] += s*math.sin(a)*1.41
def tt(d): return np.arange(int(d*SR))/SR
def fade(s, a=0.3, b=0.5):
    e = np.ones(len(s)); ia, ib = int(a*SR), int(b*SR)
    if ia: e[:ia] = np.linspace(0, 1, ia)
    if ib: e[-ib:] = np.minimum(e[-ib:], np.linspace(1, 0, ib))
    return s*e
def bed_noise(d, lo, hi, am=0.2, rate=0.3):
    t = tt(d); s = bp(noise(d), lo, hi)
    return norm(s*(1 - am + am*(0.5 + 0.5*np.sin(2*np.pi*rate*t))))
def key_click():
    d = 0.03; t = tt(d); return norm(np.sin(2*np.pi*2100*t)*np.exp(-t/0.004) + 0.5*hp(noise(d), 3500)*np.exp(-t/0.003))
def glitch(d=0.7):
    s = np.zeros(int(d*SR)); x = 0.0
    while x < d - 0.02:
        f = rng.choice([1500, 2200, 2900, 3600, 4400]); c = np.sin(2*np.pi*f*tt(0.014))*np.exp(-tt(0.014)/0.004)
        i = int(x*SR); s[i:i+len(c)] += c*rng.uniform(0.3, 1); x += rng.exponential(1/55)
    return norm(s*np.minimum(1, tt(d)/0.03)[:len(s)])
def soft_pop(f=600):
    d = 0.14; t = tt(d); return norm(np.sin(2*np.pi*np.cumsum(f*(1 + 1.5*np.exp(-t/0.02)))/SR)*np.exp(-t/0.04))
def boom(f=55, d=1.6):
    t = tt(d); return norm(np.sin(2*np.pi*np.cumsum(f*(1 + 0.8*np.exp(-t/0.08)))/SR)*np.exp(-t/0.5) + 0.3*lp(noise(d), 200)*np.exp(-t/0.3))
def tick_s():
    d = 0.05; t = tt(d); return norm(np.sin(2*np.pi*2600*t)*np.exp(-t/0.008))

# ---- ambience, each one arriving a moment before its picture ----
add(fade(bed_noise(14.8, 150, 900, 0.3), 0.6, 0.5), 0.0, 0.035)                 # Lagos evening air
add(fade(bed_noise(4.2, 250, 1500, 0.4, 0.8), 0.3, 0.4), 14.3, 0.04, 0.2)        # street under the road
add(fade(bed_noise(3.4, 120, 1800, 0.6, 0.35), 0.3, 0.6), 18.0, 0.07)            # surf
add(fade(lp(noise(6.9), 260), 0.6, 0.6), 26.0, 0.16)                             # the deep
add(fade(hum(6.7, 60)*0.4 + bed_noise(6.7, 800, 4000, 0.1)*0.5, 0.3, 0.5), 32.6, 0.05, 0.1)   # server fans
add(fade(bed_noise(6.4, 1500, 9000, 0.2, 2.0)*0.7 + bed_noise(6.4, 300, 1200)*0.3, 0.3, 1.0), 39.1, 0.07)   # London rain

# ---- sounds on the motion ----
n = len('Hello from Lagos!')
add(whoosh(0.5, 300, 5000), 1.45, 0.2); add(thud(120, 50, 0.2), 1.86, 0.18)          # zoom from the city into the phone
for i in range(n): add(key_click(), 1.87 + 0.55*i/n + rng.uniform(-0.01, 0.01), 0.1, 0.3)
send = T.wt(0, 'send')
add(click(2400), send, 0.3, 0.3); add(zip_(0.14), send + 0.06, 0.18, 0.3); add(soft_pop(520), send + 0.08, 0.25, 0.3)
add(whoosh(0.5, 400, 2600), 2.9, 0.12, -0.2)                                  # camera eases out
add(soft_pop(700), T.wt(1, 'lagos') - 0.12, 0.16, -0.4); add(soft_pop(760), T.wt(1, 'london') - 0.12, 0.16, 0.4)
lock = T.wt(2, 'locks')
add(glitch(0.75), lock + 0.05, 0.16, 0.2); add(clunk(), lock + 0.35, 0.3, 0.2)   # the words turn to code, the lock lands
add(soft_pop(640), T.wt(2, 'you', 1) - 0.08, 0.14, -0.3); add(soft_pop(700), T.wt(2, 'friend') - 0.08, 0.14, 0.3)
add(soft_pop(500), T.wt(2, 'not') - 0.05, 0.14); add(zip_(0.12, up=False), T.wt(2, 'whatsapp') + 0.05, 0.12)
add(whoosh(1.0, 200, 2000), 11.3, 0.14)                                       # pull back over the city
for k in range(6): add(fwoomp(0.4, 120 + 20*k, 900), 11.6 + 0.35*k, 0.05*(1 - k/8))   # radio rings
add(whoosh(0.6, 500, 6000), 14.05, 0.22); add(thud(130, 55, 0.25), 14.45, 0.25)       # through the antenna
add(fade(whoosh(0.9, 600, 5000), 0.02, 0.2), 14.5, 0.14)                      # inside the glass
add(whoosh(0.35, 800, 7000), 18.1, 0.2, 0.4)                                  # whip to the coast
add(click(1600), T.wt(5, 'coast') + 0.2, 0.1)
add(fwoomp(0.8, 200, 2400), T.wt(5, 'dives') + 0.05, 0.16)
# the counter spinning, then the answer lands
far = T.wt(6, 'far') - 0.3; ans = T.wt(7, 'six')
t = far
while t < ans - 0.05: add(tick_s(), t, 0.05, 0.2); t += 0.07
add(boom(), ans, 0.35); add(chime(1174.7, 1.5), ans + 0.02, 0.07)
add(whoosh(0.7, 300, 3000), 25.8, 0.16); add(fade(lp(noise(1.0), 500), 0.05, 0.6), 26.1, 0.2)   # into the sea
add(fwoomp(0.8, 150, 1800), T.wt(8, 'boosts') - 0.03, 0.2); add(chime(1760, 1.2), T.wt(8, 'boosts'), 0.06)
add(whoosh(0.5, 400, 5000), 32.5, 0.2); add(shimmer(0.6), 32.75, 0.08)       # through the fiber into the hall
add(tick_s(), T.wt(9, 'one') + 0.35, 0.3, 0.2)
for k in range(5): add(beep(2400 + 300*(k % 2), 0.04), 36.5 + 0.3*k, 0.035, -0.2)   # scanning
add(bp(noise(0.25), 150, 400)*np.exp(-tt(0.25)/0.08), T.wt(9, "can't") + 0.02, 0.18)
add(whoosh(0.7, 300, 7000), 38.6, 0.26)                                       # it jumps
add(chime(1318.5, 0.9), T.wt(10, 'jumps') + 1.5, 0.08); add(chime(1760, 0.9), T.wt(10, 'jumps') + 1.62, 0.06)   # arrives
add(shimmer(0.7), T.wt(10, 'unlocks'), 0.1)
add(tick_s(), T.wt(10, 'two') + 0.35, 0.3, 0.2); add(tick_s(), T.wt(10, 'two') + 0.57, 0.3, 0.2)
add(boom(48, 2.0), T.wt(11, 'second') - 0.02, 0.2)
bt = T.nwt(12, 'blue')
add(tick_s(), bt + 0.25, 0.3, 0.2, new=True); add(tick_s(), bt + 0.33, 0.3, 0.2, new=True); add(chime(1567.98, 1.2), bt + 0.3, 0.07, new=True)
sfxL, sfxR = L.copy(), R.copy()

def load(p):
    sr, x = wavfile.read(p); x = x.astype(np.float64)/32768
    if x.ndim == 1: x = np.stack([x, x], 1)
    if sr != SR: x = resample_poly(x, SR, sr, axis=0)
    out = np.zeros((N, 2)); m = min(N, len(x)); out[:m] = x[:m]; return out
V = load(ROOT + '/3d/v3/vo/gemini_proc.wav')[:, 0]
B = load(ROOT + '/3d/v3/bed.wav')
# the bed dips a little under the voice
env = np.sqrt(np.clip(lp(V**2, 6), 0, None)); env = env/(env.max() + 1e-9)
duck = lp(1 - 0.35*np.clip(env*4, 0, 1), 4)
rv = np.sqrt(np.mean(V[np.abs(V) > 0.01]**2)); rb = np.sqrt(np.mean(B**2)) + 1e-9
bg = rv/rb*10**(-17/20)
out = np.zeros((N, 2))
out[:, 0] = V + B[:, 0]*bg*duck + sfxL*0.55
out[:, 1] = V + B[:, 1]*bg*duck + sfxR*0.55
out /= np.abs(out).max()/0.9
fo = int(0.6*SR); out[-fo:] *= np.linspace(1, 0, fo)[:, None]
wavfile.write(ROOT + '/3d/v3/mix3d.wav', SR, (out*32767).astype(np.int16))
print('mix', DUR)
