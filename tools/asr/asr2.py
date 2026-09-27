import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import sherpa_onnx, numpy as np, json, librosa, re, subprocess
d = 'sherpa-onnx-zipformer-en-2023-06-26/'
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=d + 'encoder-epoch-99-avg-1.onnx', decoder=d + 'decoder-epoch-99-avg-1.onnx', joiner=d + 'joiner-epoch-99-avg-1.onnx', tokens=d + 'tokens.txt', num_threads=2, decoding_method='greedy_search')
y, sr = librosa.load(ROOT + '/3d/v3/vo/gemini.wav', sr=16000)
log = subprocess.run(['ffmpeg', '-i', ROOT + '/3d/v3/vo/gemini.wav', '-af', 'silencedetect=noise=-42dB:d=0.3', '-f', 'null', '-'], capture_output=True, text=True).stderr
st = [float(x) for x in re.findall(r'silence_start: ([\d.]+)', log)]; en = [float(x) for x in re.findall(r'silence_end: ([\d.]+)', log)]
# speech chunks between silences
edges = sorted(set([0.0] + [ (a + b)/2 for a, b in zip(st, en) if b > a] + [len(y)/sr]))
words = []
for a, b in zip(edges[:-1], edges[1:]):
    seg = y[int(a*sr):int(b*sr)]
    if len(seg) < 1600: continue
    s = rec.create_stream(); s.accept_waveform(sr, np.concatenate([np.zeros(3200, np.float32), seg, np.zeros(3200, np.float32)])); rec.decode_stream(s)
    r = s.result
    print(f'{a:6.2f}-{b:6.2f}  {r.text}')
    # word timestamps from tokens (tokens starting with the word marker)
    cur = None
    for tok, ts in zip(r.tokens, r.timestamps):
        t = a + ts - 0.2
        if tok.startswith('▁') or cur is None:
            if cur: words.append(cur)
            cur = {'w': tok.replace('▁', ''), 's': round(t, 3)}
        else: cur['w'] += tok
    if cur: words.append(cur)
json.dump(words, open('asr_words.json', 'w'), indent=0)
