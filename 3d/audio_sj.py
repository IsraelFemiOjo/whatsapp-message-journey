"""Sound for the send journey: effects on real events, ambience that leads each place (J cuts), and an original score."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, math, numpy as np
sys.path.insert(0, ROOT + '/shared')
from sfx import *
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

DUR = 44.05
N = int(DUR*SR)
L = np.zeros(N); R = np.zeros(N)
def add(sig, t, g=1.0, pan=0.0, bus=None):
    i = int(t*SR)
    if i >= N or i + len(sig) <= 0: return
    if i < 0: sig = sig[-i:]; i = 0
    s = sig[:N - i]*g; a = (pan + 1)*math.pi/4
    L[i:i+len(s)] += s*math.cos(a)*1.2; R[i:i+len(s)] += s*math.sin(a)*1.2
def fade(sig, fi=0.1, fo=0.2):
    n = len(sig); e = np.ones(n); a, b = int(fi*SR), int(fo*SR)
    if a: e[:a] = np.linspace(0, 1, a)
    if b: e[-b:] = np.minimum(e[-b:], np.linspace(1, 0, b))
    return sig*e
def tt(d): return np.arange(int(d*SR))/SR
def bed(d, lo, hi, am=0.0, rate=0.3):
    t = tt(d); s = bp(noise(d), lo, hi)
    if am: s *= 1 - am + am*(0.5 + 0.5*np.sin(2*np.pi*rate*t + rng.uniform(0, 6)))
    return norm(s)
def tap():
    d = 0.06; t = tt(d)
    s = np.sin(2*np.pi*1800*t)*np.exp(-t/0.006) + 0.5*hp(noise(d), 3000)*np.exp(-t/0.004)
    return norm(s)
def digital(d, rate=40):
    """the scramble: fast soft data ticks"""
    s = np.zeros(int(d*SR)); x = 0.0
    while x < d - 0.02:
        f = rng.choice([2400, 3100, 3700, 4400]); c = np.sin(2*np.pi*f*tt(0.012))*np.exp(-tt(0.012)/0.003)
        i = int(x*SR); s[i:i+len(c)] += c*rng.uniform(0.3, 1.0); x += rng.exponential(1/rate)
    return norm(s*np.minimum(1, tt(d)/0.05)[:len(s)])
def whoom(f0=90, d=0.9):
    t = tt(d); s = np.sin(2*np.pi*np.cumsum(f0*(1 + 0.6*np.exp(-t/0.25)))/SR)*np.exp(-t/0.35)
    s += 0.4*lp(noise(d), 400)*np.exp(-t/0.3)
    return norm(s*np.minimum(1, t/0.02))
def zap():
    d = 0.35; t = tt(d); s = chirp(2400, 300, d, 0.4)*np.exp(-t/0.1) + 0.6*hp(noise(d), 2000)*np.exp(-t/0.05)
    return norm(s)
def rush(d, f0=300, f1=5000):
    return norm(fade(whoosh(d, f0, f1), 0.1, 0.15))
def rumble2(d, f=60):
    t = tt(d); s = lp(noise(d), f)*(0.8 + 0.2*np.sin(2*np.pi*0.2*t)) + 0.4*np.sin(2*np.pi*38*t)
    return norm(s)
def bloop(f=220):
    d = 0.6; t = tt(d); s = np.sin(2*np.pi*np.cumsum(f*(1 + 0.3*np.exp(-t/0.05)))/SR)*np.exp(-t/0.2)
    return norm(s)
def glass(f=3200):
    d = 1.2; t = tt(d); s = sum(np.sin(2*np.pi*f*r*t)*np.exp(-t/(0.5/(1 + i))) for i, r in enumerate((1, 1.51, 2.37)))
    return norm(s*np.minimum(1, t/0.001))
def ding():
    d = 1.0; t = tt(d)
    s = np.sin(2*np.pi*1318.5*t)*np.exp(-t/0.25) + 0.6*np.sin(2*np.pi*1975.5*t)*np.exp(-(t - 0.09).clip(0)/0.25)*(t > 0.09)
    return norm(s*np.minimum(1, t/0.002))
def tick_snd():
    d = 0.05; t = tt(d); return norm(np.sin(2*np.pi*2600*t)*np.exp(-t/0.008))

# ================= ambience beds, each arriving just before its picture =================
add(fade(bed(6.3, 150, 900, 0.3), 0.3, 0.4), 0.0, 0.05, -0.2)                 # Lagos night air
add(fade(bp(noise(6.0), 200, 700), 0.5, 0.5), 0.0, 0.015, 0.3)
add(fade(bed(4.6, 250, 1400, 0.4, 0.8), 0.25, 0.3), 6.55, 0.05, 0.2)            # street hum under the road
add(fade(bed(3.2, 120, 1800, 0.6, 0.35), 0.3, 0.5), 10.8, 0.08, 0.0)            # surf at the coast
add(fade(rumble2(9.6), 0.8, 0.8), 18.3, 0.22, 0.0)                               # the deep
add(fade(bed(9.0, 60, 400, 0.3, 0.1), 0.8, 0.6), 19.0, 0.08, 0.0)
add(fade(hum(7.2, 60)*0.5 + bed(7.2, 800, 4000, 0.1)*0.6, 0.25, 0.4), 28.25, 0.06, 0.1)   # server fans
add(fade(bed(8.8, 1500, 9000, 0.2, 2.0)*0.8 + bed(8.8, 300, 1200)*0.4, 0.3, 1.2), 35.25, 0.09, 0.0)   # rain on glass

# ================= events =================
add(tap(), 0.25, 0.5, 0.4)
add(zip_(0.14), 0.42, 0.18, 0.3)                                  # message pops into the chat
add(fade(digital(1.0), 0.05, 0.2), 1.25, 0.12, 0.2)                # scrambling
add(glass(2600), 2.05, 0.06, 0.1); add(shimmer(0.5), 2.1, 0.05)
for k in range(8): add(whoom(80 + 6*k), 2.35 + 0.3*k, 0.18*(1 - k/10), 0.0)   # radio rings
add(rush(1.2, 200, 3000), 2.4, 0.16, 0.0)
add(rush(2.0, 250, 4200), 3.8, 0.12, 0.2)
add(zap(), 5.82, 0.3, 0.0); add(thud(140, 60, 0.25), 5.85, 0.35)
add(fade(rush(0.9, 600, 6000), 0.02, 0.2), 6.0, 0.22)             # inside the fiber
add(fwoomp(0.5, 300, 2600), 6.75, 0.15)                            # out onto the street
add(rush(1.2, 300, 2400), 10.05, 0.1, 0.3)                         # rise toward the coast
add(click(2200), 12.0, 0.18, 0.0); add(bloop(330), 12.02, 0.08)    # into the landing station
add(rush(2.2, 200, 1800), 12.2, 0.1)
add(plink(1568), 15.3, 0.08, -0.3); add(plink(2093), 15.45, 0.06, 0.3)   # the route lights up
add(rush(1.2, 200, 1500), 17.6, 0.12)                              # dive toward the sea
add(fade(lp(noise(1.2), 500), 0.1, 0.8), 18.45, 0.25)              # breaking the surface, going under
for k in range(5): add(bloop(90 + 20*k), 18.9 + 0.35*k, 0.05, -0.4 + 0.2*k)
add(fade(bloop(160), 0.01, 0.3), 24.7, 0.2, 0.2); add(glass(1400), 24.75, 0.05, 0.2)   # the repeater flares
add(rush(1.8, 300, 3500), 26.4, 0.1)
add(glass(3600), 27.2, 0.1); add(fwoomp(0.9, 200, 4000), 28.0, 0.18)                # into one fiber, light fills
for k in range(6): add(beep(1760 + 220*(k % 3), 0.05), 29.4 + 0.45*k, 0.035, 0.4)
add(fade(digital(1.6, 18), 0.1, 0.3), 30.3, 0.06, 0.4)             # the scrambled copy on the server
add(tick_snd(), 31.95, 0.22, -0.3)                                  # one grey tick
add(rush(2.4, 300, 6000), 33.2, 0.22)                              # down the aisle, lights streak
add(fade(bed(1.4, 2000, 9000), 0.02, 0.8), 35.4, 0.12)             # the streaks become rain
add(ding(), 37.05, 0.22, 0.2)                                       # it arrives
add(fade(digital(1.0, 30), 0.02, 0.3), 37.3, 0.08, 0.2)            # unscrambling
add(tick_snd(), 39.05, 0.18, -0.3); add(tick_snd(), 39.13, 0.18, -0.3)   # two grey ticks
add(thud(90, 45, 0.5), 41.4, 0.35); add(chime(1174.7, 2.0), 41.42, 0.07); add(chime(1760, 2.0), 41.45, 0.05)
sfxL, sfxR = L.copy(), R.copy()

# ================= score: 104 bpm, D minor, cinematic electronic =================
BPM = 104; BEAT = 60/BPM; BAR = 4*BEAT; S16 = BEAT/4
def mtof(m): return 440*2**((m - 69)/12)
def saw(f, n, ph=0.0):
    dt = f/SR; p = (ph + dt*np.arange(n)) % 1.0; y = 2*p - 1
    m1 = p < dt; x = p[m1]/dt; y[m1] -= x + x - x*x - 1
    m2 = p > 1 - dt; x = (p[m2] - 1)/dt; y[m2] -= x*x + x + x + 1
    return y
def kick():
    n = int(0.4*SR); t = tt(0.4); s = np.sin(2*np.pi*np.cumsum(46 + 90*np.exp(-t/0.03))/SR)*np.exp(-t/0.26)
    return np.tanh(1.6*s)
def clap():
    n = int(0.3*SR); t = tt(0.3); s = np.zeros(n)
    for dly in (0.0, 0.011, 0.022):
        i = int(dly*SR); b = bp(rng.standard_normal(int(0.012*SR)), 900, 5000)*np.exp(-np.arange(int(0.012*SR))/SR/0.004); s[i:i+len(b)] += b
    return s + bp(rng.standard_normal(n), 1000, 6000)*np.exp(-t/0.11)*0.6
def hat(): n = int(0.04*SR); return hp(rng.standard_normal(n), 7000, 4)*np.exp(-np.arange(n)/SR/0.011)
def bass(m, d):
    n = int(d*SR); t = tt(d); f = mtof(m); s = lp(saw(f, n)*0.7 + np.sin(2*np.pi*f*t)*0.8, 700)
    return np.tanh(1.4*s*np.minimum(1, t/0.004)*np.exp(-t/0.3))
def pad(ms, d, cut=1500):
    n = int(d*SR); t = tt(d); Lp = np.zeros(n); Rp = np.zeros(n)
    for m in ms:
        for k, det in enumerate((-0.12, -0.05, 0.05, 0.12)):
            o = saw(mtof(m)*2**(det/12), n, rng.random())
            (Lp if k % 2 else Rp)[:] += o
    env = np.minimum(1, t/0.4)*np.minimum(1, (d - t)/0.4)
    return lp(Lp, cut)*env/len(ms)/2, lp(Rp, cut)*env/len(ms)/2
def pluck(m, d=0.4):
    n = int(d*SR); t = tt(d); f = mtof(m); s = saw(f, n)*0.6 + np.sin(2*np.pi*f*t)*0.5
    return (lp(s, 3800)*np.exp(-t/0.05)*0.5 + lp(s, 1100)*0.5)*np.exp(-t/0.18)*np.minimum(1, t/0.002)
DR = np.zeros(N); BS = np.zeros(N); PL = np.zeros(N); PR = np.zeros(N); AR = np.zeros(N)
def put(bus, sig, t, g=1.0):
    i = int(t*SR)
    if i >= N: return
    s = sig[:N - i]; bus[i:i+len(s)] += s*g
PROG = [(38, [62, 65, 69]), (34, [62, 65, 70]), (41, [60, 65, 69]), (36, [60, 64, 67])]   # Dm Bb F C
G0 = 0.25
def section(t):
    if t < 2.35: return 'intro'
    if 18.6 <= t < 25.8: return 'deep'
    if 25.8 <= t < 28.5: return 'rise'
    if 35.5 <= t < 41.4: return 'rain'
    if t >= 41.4: return 'end'
    return 'full'
kicks = []
b = 0
while G0 + b*BAR < DUR:
    root, ch = PROG[b % 4]; t0 = G0 + b*BAR; sec = section(t0 + 0.01)
    if sec != 'end':
        cut = 700 if sec == 'deep' else (1100 if sec in ('intro', 'rain') else 1700)
        lp_, rp_ = pad(ch, BAR + 0.4, cut); put(PL, lp_, t0, 1.0); put(PR, rp_, t0, 1.0)
    if sec == 'deep': put(BS, bass(root - 12, BAR*0.95), t0, 0.35)
    for s16 in range(16):
        t = t0 + s16*S16; sc = section(t + 1e-3)
        if t >= DUR: break
        if sc == 'full':
            if s16 in (0, 6, 10): put(DR, kick(), t, 0.85); kicks.append(t)
            if s16 in (4, 12): put(DR, clap(), t, 0.4)
            put(DR, hat(), t, 0.12 if s16 % 2 else 0.07)
            if s16 % 2 == 0: put(BS, bass(root, S16*1.7), t, 0.45)
        if sc == 'rise':
            put(DR, hat(), t, 0.05 + 0.1*(t - 25.8)/2.7)
            if s16 % 4 == 0: put(DR, kick(), t, 0.3 + 0.4*(t - 25.8)/2.7); kicks.append(t)
        if sc == 'rain' and s16 % 4 == 0: put(BS, bass(root, BEAT*0.9), t, 0.25)
        if sc in ('intro', 'full', 'rain') and s16 % 2 == 0:
            note = ch[[0, 1, 2, 1, 2, 0, 1, 2][(s16//2) % 8]] + 12
            put(AR, pluck(note), t, 0.16 if sc == 'full' else 0.11)
    b += 1
# final chord on "Under a second"
lp_, rp_ = pad([62, 65, 69, 74], 2.6, 1800); put(PL, lp_, 41.4, 1.2); put(PR, rp_, 41.4, 1.2)
put(BS, bass(38, 2.0), 41.4, 0.6); put(DR, kick(), 41.4, 0.9)
# sidechain pump and mix
duck = np.ones(N)
for k in kicks:
    i0 = int(k*SR); n = min(int(0.3*SR), N - i0)
    if n > 0: duck[i0:i0+n] = np.minimum(duck[i0:i0+n], 1 - 0.55*np.exp(-np.arange(n)/SR/0.09))
PL *= duck; PR *= duck
d_ = int(S16*3*SR); AL2 = AR.copy(); AR2 = AR.copy()
for k in range(1, 4):
    s = lp(AR[:-d_*k], 2600)*(0.3**k); (AR2 if k % 2 else AL2)[d_*k:] += s
ir = rng.standard_normal(int(1.4*SR))*np.exp(-tt(1.4)/0.45); ir = lp(ir, 5000)/np.sqrt(np.sum(ir**2))
revL = fftconvolve(PL*0.3 + AL2*0.3, ir)[:N]*0.35; revR = fftconvolve(PR*0.3 + AR2*0.3, ir)[:N]*0.35
ML = np.tanh(DR)*0.8 + BS*0.7 + PL*0.6 + AL2*0.6 + revL
MR = np.tanh(DR)*0.8 + BS*0.7 + PR*0.6 + AR2*0.6 + revR
t = np.arange(N)/SR
w = np.clip((t - 18.3)/0.4, 0, 1)*np.clip((25.9 - t)/0.5, 0, 1)          # under the sea: muffled
ML = ML*(1 - w) + lp(ML, 500)*w*1.1; MR = MR*(1 - w) + lp(MR, 500)*w*1.1
ML = hp(ML, 30); MR = hp(MR, 30)
mr = np.sqrt(np.mean(((ML + MR)/2)**2)); mg = 10**(-22/20)/max(mr, 1e-9)
Lo = sfxL + ML*mg; Ro = sfxR + MR*mg
def soft(x, th=0.6):
    y = np.copy(x); m = np.abs(x) > th; y[m] = np.sign(x[m])*(th + (1 - th)*np.tanh((np.abs(x[m]) - th)/(1 - th))); return y
Lo, Ro = soft(Lo), soft(Ro)
pk = max(np.abs(Lo).max(), np.abs(Ro).max()); Lo *= 0.84/pk; Ro *= 0.84/pk
fo = int(0.6*SR); Lo[-fo:] *= np.linspace(1, 0, fo); Ro[-fo:] *= np.linspace(1, 0, fo)
wavfile.write(ROOT + '/3d/mix.wav', SR, (np.stack([Lo, Ro], 1)*32767).astype(np.int16))
print('ok', DUR)
