import sherpa_onnx, numpy as np, librosa, re, subprocess, json, sys
d = 'sherpa-onnx-zipformer-en-2023-06-26/'
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=d + 'encoder-epoch-99-avg-1.onnx', decoder=d + 'decoder-epoch-99-avg-1.onnx', joiner=d + 'joiner-epoch-99-avg-1.onnx', tokens=d + 'tokens.txt', num_threads=2, decoding_method='modified_beam_search')
p = sys.argv[1]
y, sr = librosa.load(p, sr=16000)
log = subprocess.run(['ffmpeg', '-i', p, '-af', 'silencedetect=noise=-42dB:d=0.3', '-f', 'null', '-'], capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
edges = sorted(set([0.0] + [(a + b)/2 for a, b in zip(st, en) if b > a] + [len(y)/sr]))
words = []
PAD = 0.2
for a, b in zip(edges[:-1], edges[1:]):
    seg = y[int(a*sr):int(b*sr)]
    if len(seg) < 1600: continue
    s = rec.create_stream(); s.accept_waveform(sr, np.concatenate([np.zeros(int(PAD*sr), np.float32), seg, np.zeros(int(PAD*sr), np.float32)])); rec.decode_stream(s)
    r = s.result; cur = None
    for tok, ts in zip(r.tokens, r.timestamps):
        t = a + ts - PAD
        if tok.startswith('▁') or tok.startswith(' ') or cur is None:
            if cur: words.append(cur)
            cur = {'w': tok.replace('▁', '').strip(), 's': round(max(a, t), 3)}
        else: cur['w'] += tok
    if cur: words.append(cur)
# word ends: next word start, or the start of the next silence
sil = list(zip(st, en))
for i, w in enumerate(words):
    nxt = words[i + 1]['s'] if i + 1 < len(words) else len(y)/sr
    ss = [x for x, _ in sil if w['s'] < x < nxt]
    w['e'] = round(min([nxt] + ss), 3)
json.dump(words, open(sys.argv[2], 'w'), indent=0)
print(' '.join(f"{w['w']}@{w['s']:.2f}-{w['e']:.2f}" for w in words))
