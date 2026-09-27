import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..', '..')))
import sys, json, re, soundfile as sf, numpy as np
from kokoro_onnx import Kokoro
k = Kokoro(ROOT + '/tools/tts/models/kokoro_dur.onnx', ROOT + '/tools/tts/models/voices-v1.0.bin')
voice, speed = sys.argv[1], float(sys.argv[2])
lines = [l.strip() for l in open(ROOT + '/3d/v3/vo/script_new.txt') if l.strip()]
parts, words, t0 = [], [], 0.0
SR = 24000
for li, line in enumerate(lines):
    a, sr, tm = k.create_timed(line, voice=voice, speed=speed, lang='en-us', sentence_pause=0.14, clause_pause=0.06)
    strip = lambda x: re.sub(r"[ˈˌ\s.,!?;:—…\"]", "", x)
    stream = [p for p in tm if strip(p.phoneme)]
    tw = line.split(); pos = 0
    lens = [max(1, len(strip(k.tokenizer.phonemize(re.sub(r"[.,!?]", "", w), 'en-us')))) for w in tw]
    tot = sum(lens); scale = len(stream)/tot
    acc = 0.0
    for w, L in zip(tw, lens):
        i0 = int(round(acc)); acc += L*scale; i1 = max(i0 + 1, int(round(acc)))
        i0 = min(i0, len(stream) - 1); i1 = min(i1, len(stream))
        words.append({'w': w, 's': round(t0 + stream[i0].start, 3), 'e': round(t0 + stream[i1 - 1].end, 3), 'line': li})
    parts.append(a); t0 += len(a)/sr
    g_ = 0.3
    gap = np.zeros(int(g_*sr), np.float32); parts.append(gap); t0 += g_
audio = np.concatenate(parts)
sf.write(ROOT + '/3d/v3/vo/ref.wav', audio, SR)
json.dump(words, open(ROOT + '/3d/v3/vo/ref_words.json', 'w'), indent=0)
print(voice, round(len(audio)/SR, 2), 's', len(words), 'words')
