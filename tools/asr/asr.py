import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import sherpa_onnx, soundfile as sf, numpy as np, json, librosa
d = 'sherpa-onnx-zipformer-en-2023-06-26/'
import glob
enc = sorted(glob.glob(d + 'encoder*.onnx')); dec = sorted(glob.glob(d + 'decoder*.onnx')); jn = sorted(glob.glob(d + 'joiner*.onnx'))
pick = lambda L: [x for x in L if 'int8' not in x][0] if any('int8' not in x for x in L) else L[0]
rec = sherpa_onnx.OfflineRecognizer.from_transducer(encoder=pick(enc), decoder=pick(dec), joiner=pick(jn), tokens=d + 'tokens.txt', num_threads=2, decoding_method='greedy_search')
y, sr = librosa.load(ROOT + '/3d/v3/vo/gemini.wav', sr=16000)
s = rec.create_stream(); s.accept_waveform(16000, y); rec.decode_stream(s)
r = s.result
print(r.text)
json.dump({'text': r.text, 'tokens': list(r.tokens), 'timestamps': list(r.timestamps)}, open('asr.json', 'w'))
