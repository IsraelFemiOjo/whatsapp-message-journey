import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import sys, time, numpy as np
sys.path.insert(0, ROOT + '/3d/v3')
from PIL import Image
import render
ts = [float(x) for x in sys.argv[1].split(',')]
ims = []
for t in ts:
    t0 = time.time(); im = render.frame(int(round(t*30))); print(t, round(time.time() - t0, 1), flush=True)
    ims.append(Image.fromarray(im).resize((360, 360)))
cols = 6; rows = (len(ims) + cols - 1)//cols
S = Image.new('RGB', (360*cols, 360*rows))
for k, im in enumerate(ims): S.paste(im, ((k % cols)*360, (k//cols)*360))
S.save(sys.argv[2])
