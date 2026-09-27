import json, re, subprocess, numpy as np, soundfile as sf
y, sr = sf.read('gemini2.wav'); y = y.astype(np.float64)
dur = len(y)/sr
log = subprocess.run(['ffmpeg', '-i', 'gemini2.wav', '-af', 'silencedetect=noise=-42dB:d=0.3', '-f', 'null', '-'], capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
cuts = [(33.85, 34.92), (61.50, dur)]                    # the stray spoken "amused", and the tail
MAXP = 0.42
for a, b in zip(st, en):
    if b - a > MAXP and a > 0.1 and not (33.5 < a < 35.2):
        k = (b - a) - MAXP; cuts.append((a + MAXP/2, a + MAXP/2 + k))   # keep the pause, just shorter
if st and st[0] < 0.05 and en[0] > 0.12: cuts.append((0.0, en[0] - 0.08))
cuts.sort()
keep = []; t = 0.0
for a, b in cuts:
    if a > t: keep.append((t, a))
    t = max(t, b)
if t < dur: keep.append((t, dur))
parts = []; F = int(0.012*sr)
for a, b in keep:
    seg = y[int(a*sr):int(b*sr)].copy()
    if len(seg) > 2*F: seg[:F] *= np.linspace(0, 1, F); seg[-F:] *= np.linspace(1, 0, F)
    parts.append(seg)
out = np.concatenate(parts)
sf.write('cut.wav', out, sr)
json.dump({'keep': keep}, open('cutmap.json', 'w'))
print('cut length', round(len(out)/sr, 2), 'cuts', len(cuts))
