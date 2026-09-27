import json, re, subprocess, numpy as np, librosa
exec(open('align.py').read().split("W = json.load")[0])      # reuses the DTW path (rt, gt)
W = json.load(open('ref_words.json'))
log = subprocess.run(['ffmpeg', '-i', 'gemini.wav', '-af', 'silencedetect=noise=-40dB:d=0.22', '-f', 'null', '-'], capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
dur = librosa.get_duration(path='gemini.wav')
sil = [(a, b) for a, b in zip(st, en[1:] if en and en[0] < (st[0] if st else 0) else en) if b - a >= 0.22]
lead = en[0] if en and (not st or en[0] < st[0] or st[0] < 0.01) else 0.0
if st and st[0] < 0.01: st = st[1:]; en = en[1:]
ug, ig = np.unique(gt, return_index=True); r_of_g = lambda t: float(np.interp(t, ug, rt[ig]))
# candidate boundaries between words in the reference
B = []
for i in range(len(W) - 1):
    punct = W[i]['w'][-1] in '.,?!'
    B.append((i, (W[i]['e'] + W[i + 1]['s'])/2, punct or W[i]['line'] != W[i + 1]['line']))
used = set(); anchors = []
for a, b in sil:
    if a < lead + 0.05 or b > dur - 0.05: continue
    rm = r_of_g((a + b)/2)
    best = min((abs(m - rm) + (0 if p else 0.45), i) for i, m, p in B if i not in used)
    if best[0] < 1.2:
        i = best[1]; used.add(i); anchors.append((i, a, b))
anchors.sort()
# keep monotone
clean = []; last_t = -1
for i, a, b in anchors:
    if a > last_t: clean.append((i, a, b)); last_t = b
# words between anchors get the speech span linearly from their reference times
end_speech = dur
for k in range(len(W) - 1, -1, -1): pass
bounds = [(-1, None, lead)] + clean + [(len(W) - 1, st[-1] if st and st[-1] > clean[-1][2] else dur, None)]
out = [None]*len(W)
for (i0, _, g0), (i1, g1, _) in zip(bounds[:-1], bounds[1:]):
    ws = list(range(i0 + 1, i1 + 1))
    if not ws: continue
    r0, r1 = W[ws[0]]['s'], W[ws[-1]]['e']
    for j in ws:
        f = lambda t: g0 + (t - r0)/(r1 - r0 + 1e-9)*(g1 - g0)
        out[j] = {'w': W[j]['w'], 'line': W[j]['line'], 's': round(f(W[j]['s']), 3), 'e': round(f(W[j]['e']), 3)}
ACC = {0: ['wondered', 'second'], 1: ['follow'], 2: ['scrambles', 'code', 'you', 'friend', 'whatsapp.'], 3: ['nearest', 'radio'],
       4: ['light,', 'glass'], 5: ['dives', 'atlantic.'], 6: ['far', 'think'], 7: ['six', 'thousand', 'garden'], 8: ['repeater', 'boosts'],
       9: ['server.', 'one', "can't", 'word'], 10: ["friend's", 'unlocks.', 'two'], 11: ['under', 'second.'], 12: ['blue', 'friend.']}
for w in out: w['acc'] = w['w'].lower() in ACC.get(w['line'], [])
json.dump(out, open('gemini_words.json', 'w'), indent=0)
print('anchors', len(clean), 'of', len(sil), 'silences')
L = {}
for w in out: L.setdefault(w['line'], []).append(w)
for k, v in L.items(): print(k, v[0]['s'], v[-1]['e'], ' '.join(f"{x['w']}@{x['s']:.2f}" for x in v))
