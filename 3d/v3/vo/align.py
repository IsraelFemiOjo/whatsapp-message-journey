import json, numpy as np, librosa
SR = 16000; HOP = 160
def feat(p):
    y, _ = librosa.load(p, sr=SR)
    m = librosa.feature.mfcc(y=y, sr=SR, n_mfcc=20, hop_length=HOP, n_fft=512)[1:]
    m = (m - m.mean(1, keepdims=True))/(m.std(1, keepdims=True) + 1e-6)
    e = librosa.feature.rms(y=y, hop_length=HOP, frame_length=512)[0]
    e = np.log(e + 1e-5); e = (e - e.mean())/e.std()
    return np.vstack([m, 2.5*e[None, :m.shape[1]]]), y
R, yr = feat('ref.wav'); G, yg = feat('gemini.wav')
D, wp = librosa.sequence.dtw(X=R, Y=G, metric='cosine', step_sizes_sigma=np.array([[1, 1], [0, 1], [1, 0], [2, 1], [1, 2]]),
                             weights_add=np.array([0, 0.3, 0.3, 0.1, 0.1]))
wp = wp[::-1]
rt = wp[:, 0]*HOP/SR; gt = wp[:, 1]*HOP/SR
# monotone map from reference time to gemini time
u, idx = np.unique(rt, return_index=True)
g_of_r = lambda t: float(np.interp(t, u, gt[idx]))
W = json.load(open('ref_words.json'))
out = []
for w in W:
    out.append({'w': w['w'], 'line': w['line'], 's': round(g_of_r(w['s']), 3), 'e': round(g_of_r(w['e']), 3)})
# accents: keep the words that carried emphasis in the direction
ACC = {0: ['wondered', 'second'], 1: ['follow', 'lagos', 'london'], 2: ['scrambles', 'code', 'you', 'friend', 'whatsapp.'], 3: ['radio', 'nearest'],
       4: ['light,', 'glass'], 5: ['dives', 'atlantic.'], 6: ['guess.', 'far'], 7: ['six', 'thousand', 'garden'], 8: ['repeater', 'boosts'],
       9: ['server.', 'one', "can't", 'word'], 10: ["friend's", 'unlocks.', 'two'], 11: ['under', 'second.'], 12: ['blue', 'friend.']}
for w in out:
    w['acc'] = w['w'].lower() in ACC.get(w['line'], [])
json.dump(out, open('gemini_words.json', 'w'), indent=0)
L = {}
for w in out: L.setdefault(w['line'], []).append(w)
for k, v in L.items(): print(k, v[0]['s'], v[-1]['e'], ' '.join(f"{x['w']}@{x['s']:.2f}" for x in v))
