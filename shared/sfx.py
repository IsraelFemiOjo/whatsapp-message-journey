import numpy as np
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(7)

def t_(d): return np.arange(int(d*SR))/SR
def env_ad(n, a, d):  # attack/decay exponential envelope
    t = np.arange(n)/SR
    e = np.minimum(1, t/max(a, 1e-4))*np.exp(-np.maximum(0, t - a)/max(d, 1e-4))
    return e
def lp(x, f, o=2): return sosfilt(butter(o, f, 'low', fs=SR, output='sos'), x)
def hp(x, f, o=2): return sosfilt(butter(o, f, 'high', fs=SR, output='sos'), x)
def bp(x, f1, f2, o=2): return sosfilt(butter(o, [f1, f2], 'band', fs=SR, output='sos'), x)
def noise(d): return rng.standard_normal(int(d*SR))
def chirp(f0, f1, d, curve=1.0):
    t = t_(d); f = f0 + (f1 - f0)*(t/d)**curve
    return np.sin(2*np.pi*np.cumsum(f)/SR)
def norm(x, peak=1.0):
    m = np.max(np.abs(x)) + 1e-9
    return x/m*peak

def thud(f0=110, f1=45, d=0.22):
    s = chirp(f0, f1, d, 0.6)*env_ad(int(d*SR), 0.003, 0.07)
    n = lp(noise(0.05), 900)*env_ad(int(0.05*SR), 0.001, 0.012)*0.5
    s[:len(n)] += n
    return norm(s)

def footstep(soft=True):
    d = 0.09
    n = lp(noise(d), 700 if soft else 1100)*env_ad(int(d*SR), 0.002, 0.02)
    s = chirp(90, 50, d)*env_ad(int(d*SR), 0.002, 0.03)*0.8
    return norm(n + s)

def patter():
    d = 0.05
    n = bp(noise(d), 900, 3200)*env_ad(int(d*SR), 0.001, 0.008)
    return norm(n)

def whoosh(d=0.35, f0=400, f1=2400):
    n = noise(d); out = np.zeros_like(n)
    seg = 256
    for i in range(0, len(n), seg):
        fc = f0 + (f1 - f0)*(i/len(n))
        out[i:i+seg] = bp(n[max(0, i-2048):i+seg], fc*0.7, min(fc*1.4, 20000))[-len(n[i:i+seg]):]
    e = np.sin(np.pi*np.linspace(0, 1, len(n)))**1.5
    return norm(out*e)

def zip_(d=0.13, up=True):
    f0, f1 = (700, 2600) if up else (2200, 700)
    s = chirp(f0, f1, d, 0.7)*np.sin(np.pi*np.linspace(0, 1, int(d*SR)))*0.35
    n = hp(noise(d), 2500)*np.sin(np.pi*np.linspace(0, 1, int(d*SR)))**2*0.5
    return norm(s + n)

def blip(f=880):
    d = 0.11
    s = chirp(f, f*1.5, d, 0.4)*env_ad(int(d*SR), 0.002, 0.04)
    s += 0.3*chirp(f*2, f*3, d, 0.4)*env_ad(int(d*SR), 0.002, 0.025)
    return norm(s)

def chime(f=1046.5, d=1.2, bright=1.0):
    t = t_(d); s = np.zeros_like(t)
    for ratio, amp, dec in ((1, 1.0, 0.55), (2.0, 0.35*bright, 0.3), (2.76, 0.25*bright, 0.22), (5.4, 0.12*bright, 0.1)):
        s += amp*np.sin(2*np.pi*f*ratio*t)*np.exp(-t/dec)
    s *= np.minimum(1, t/0.002)
    return norm(s)

def click(f=3200):
    d = 0.025
    s = np.sin(2*np.pi*f*t_(d))*env_ad(int(d*SR), 0.0005, 0.004)
    n = hp(noise(d), 3000)*env_ad(int(d*SR), 0.0003, 0.003)
    return norm(s + n)

def metal(f=220, d=0.5, decay=0.12, ratios=(1, 2.41, 3.93, 5.12, 6.8)):
    t = t_(d); s = np.zeros_like(t)
    for k, r in enumerate(ratios):
        s += np.sin(2*np.pi*f*r*t + k)*np.exp(-t/(decay/(1 + 0.4*k)))/(1 + 0.6*k)
    n = bp(noise(0.03), 1500, 6000)*env_ad(int(0.03*SR), 0.0005, 0.006)
    s[:len(n)] += 0.6*n
    return norm(s)

def clunk(): return norm(metal(160, 0.35, 0.07)*0.8 + np.pad(thud(120, 55, 0.2), (0, int(0.15*SR)))[:int(0.35*SR)])

def bwong(f=98, d=1.1, am=3.2):
    t = t_(d)
    s = np.zeros_like(t)
    for k, r in enumerate((1, 2.7, 5.2)):
        s += np.sin(2*np.pi*f*r*t)*np.exp(-t/(0.5/(1 + k)))/(1 + k)
    s *= (0.65 + 0.35*np.cos(2*np.pi*am*t))*np.exp(-t/0.45)
    return norm(s)

def creak(d=1.2):
    t = t_(d)
    f = 72 + 10*np.sin(2*np.pi*0.9*t) + 6*lp(rng.standard_normal(len(t)), 8)*30
    saw = 2*((np.cumsum(f)/SR) % 1) - 1
    s = lp(saw, 650)*(0.55 + 0.45*np.abs(np.sin(2*np.pi*6.5*t)))
    s *= np.minimum(1, t/0.15)*np.minimum(1, (d - t)/0.15)
    return norm(s)

def rumble(d=1.2, f=110, trem=11):
    t = t_(d)
    s = lp(noise(d), f)*(0.7 + 0.3*np.sin(2*np.pi*trem*t))
    s *= np.minimum(1, t/0.1)*np.minimum(1, (d - t)/0.15)
    return norm(s)

def crack():
    d = 0.3; s = np.zeros(int(d*SR))
    for k, (tt, a) in enumerate(((0.0, 1), (0.018, 0.7), (0.034, 0.8), (0.061, 0.5), (0.09, 0.35))):
        i = int(tt*SR); b = hp(noise(0.012), 1800)*env_ad(int(0.012*SR), 0.0002, 0.002)*a
        s[i:i+len(b)] += b
    th = thud(90, 40, 0.25)*0.5
    s[:len(th)] += th[:len(s)]
    return norm(s)

def fwoomp(d=0.55, f0=250, f1=2400):
    n = noise(d); t = t_(d)
    out = np.zeros_like(n); seg = 480
    for i in range(0, len(n), seg):
        fc = f0*(f1/f0)**min(1, i/(0.35*SR))
        out[i:i+seg] = lp(n[max(0, i-4096):i+seg], fc)[-len(n[i:i+seg]):]
    e = np.minimum(1, t/0.035)*np.exp(-np.maximum(0, t - 0.035)/0.18)
    low = chirp(70, 140, d)*e*0.4
    return norm(out*e + low)

def crackles(d=1.0, rate=16):
    s = np.zeros(int(d*SR)); tt = 0.0
    while True:
        tt += rng.exponential(1/rate)
        if tt >= d - 0.02: break
        i = int(tt*SR); a = (1 - tt/d)*rng.uniform(0.4, 1.0)
        b = bp(noise(0.01), 2000, 7000)*env_ad(int(0.01*SR), 0.0002, 0.0018)*a
        s[i:i+len(b)] += b
    return norm(s)

def motor(d, f0, f1, harm=True):
    t = t_(d); f = f0 + (f1 - f0)*np.minimum(1, (t/d))**0.6
    ph = 2*np.pi*np.cumsum(f)/SR
    s = np.sin(ph) + (0.5*np.sin(2*ph) + 0.25*np.sin(3*ph) if harm else 0)
    s = lp(s, 900) + 0.15*lp(noise(d), 400)
    return norm(s)

def ticks(d, rate0, rate1, f=2600):
    s = np.zeros(int(d*SR)); tt = 0.0
    while tt < d - 0.03:
        r = rate0 + (rate1 - rate0)*min(1, tt/d)
        tt += 1/max(r, 0.5)
        if tt >= d - 0.03: break
        c = click(f)*0.6; i = int(tt*SR); s[i:i+len(c)] += c[:len(s) - i]
    return s

def beep(f=988, d=0.09):
    t = t_(d)
    s = np.sin(2*np.pi*f*t) + 0.2*np.sin(2*np.pi*2*f*t)
    return norm(s*np.minimum(1, t/0.005)*np.minimum(1, (d - t)/0.02))

def plink(f=1568):
    d = 0.35; t = t_(d)
    s = np.sin(2*np.pi*f*t)*np.exp(-t/0.07) + 0.3*np.sin(2*np.pi*2*f*t)*np.exp(-t/0.04)
    return norm(s*np.minimum(1, t/0.001))

def fan(d, up=True):
    t = t_(d); x = t/d
    f = (60 + 190*x**0.7) if up else (250 - 190*x**0.8)
    a = (x**0.5) if up else (1 - x)**0.6
    ph = 2*np.pi*np.cumsum(f)/SR
    s = (np.sin(ph) + 0.4*np.sin(3*ph))*a + 0.3*bp(noise(d), 300, 1500)*a
    return norm(lp(s, 1600))

def ratchet(d=0.13, rate=34): return norm(ticks(d, rate, rate, 3600))

def boop(f=620):
    d = 0.08; t = t_(d)
    s = np.sin(2*np.pi*(f - 120*t/d)*t)*np.sin(np.pi*t/d)
    return norm(s)

def cardboard():
    d = 0.16
    n = lp(noise(d), 380)*env_ad(int(d*SR), 0.002, 0.035)
    s = chirp(120, 70, d)*env_ad(int(d*SR), 0.002, 0.04)*0.6
    return norm(n + s)

def hum(d, f=55):
    t = t_(d)
    s = np.sin(2*np.pi*f*t) + 0.5*np.sin(2*np.pi*2*f*t) + 0.2*lp(noise(d), 300)
    return norm(s)

def grind(d, judder=12):
    t = t_(d)
    saw = 2*((42*t) % 1) - 1
    s = lp(saw + 0.6*noise(d), 520)*(0.6 + 0.4*(np.sin(2*np.pi*judder*t) > 0))
    s *= np.minimum(1, t/0.08)*np.minimum(1, (d - t)/0.1)
    return norm(s)

def hiss(d=0.5):
    t = t_(d)
    return norm(hp(noise(d), 3000)*np.minimum(1, t/0.01)*np.exp(-t/0.16))

def boing(d=0.22):
    t = t_(d); f = 260 + 380*(t/d) + 30*np.sin(2*np.pi*22*t)
    s = np.sin(2*np.pi*np.cumsum(f)/SR)*np.sin(np.pi*t/d)
    return norm(s)

def shimmer(d=0.8):
    s = np.zeros(int(d*SR))
    for k in range(9):
        tt = rng.uniform(0, d*0.7); f = rng.choice([2093, 2349, 2637, 3136, 3520, 4186])
        c = plink(f)*rng.uniform(0.3, 0.7); i = int(tt*SR); s[i:i+len(c)] += c[:len(s) - i]
    return norm(s)

def roll(d):
    t = t_(d)
    s = lp(noise(d), 260)*(0.75 + 0.25*np.sin(2*np.pi*9*t))
    return norm(s*np.minimum(1, t/0.08)*np.minimum(1, (d - t)/0.15))

def kachunk():
    a = clunk(); b = metal(300, 0.3, 0.05)
    out = np.zeros(int(0.45*SR)); out[:len(a)] += a[:len(out)]*0.8
    i = int(0.07*SR); out[i:i+len(b)] += b[:len(out) - i]
    return norm(out)
