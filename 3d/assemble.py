"""Put the sections in order: 1057 frames at 24 fps, with the coast dissolving into the map."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import os, numpy as np
from PIL import Image
B = ROOT + '/3d/fr'
OUT = f'{B}/all'; os.makedirs(OUT, exist_ok=True)
for f in os.listdir(OUT): os.remove(f'{OUT}/{f}')
seq = []
seq += [('s1', i) for i in range(0, 144)]
seq += [('s2', i) for i in range(0, 120)]
seq += [('s3', i) for i in range(0, 55)]
seq += [('x', i) for i in range(17)]
seq += [('s4', i) for i in range(17, 128)]
seq += [('s5', i) for i in range(0, 238)]
seq += [('s6', i) for i in range(0, 168)]
seq += [('s7', i) for i in range(0, 204)]
missing = []
for n, (s, i) in enumerate(seq):
    dst = f'{OUT}/{n:05d}.png'
    if s == 'x':
        a, b = f'{B}/s3/{55 + i:04d}.png', f'{B}/s4/{i:04d}.png'
        if not (os.path.exists(a) and os.path.exists(b)): missing.append((s, i)); continue
        k = (i + 1)/18; k = k*k*(3 - 2*k)
        A = np.array(Image.open(a)).astype(np.float32); Bm = np.array(Image.open(b)).astype(np.float32)
        Image.fromarray(np.clip(A*(1 - k) + Bm*k, 0, 255).astype(np.uint8)).save(dst)
    else:
        src = f'{B}/{s}/{i:04d}.png'
        if not os.path.exists(src): missing.append((s, i)); continue
        os.symlink(src, dst)
print(len(seq), 'frames', len(seq)/24, 's; missing', len(missing), missing[:5])
