import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import sys; sys.path.insert(0, ROOT + '/3d/v3')
from PIL import Image
import render
ts = [1.0, 10.9, 12.8, 23.8, 37.9, 40.8]
ims = [Image.fromarray(render.frame(int(t*30))).resize((540, 540), Image.LANCZOS) for t in ts]
S = Image.new('RGB', (540*3 + 20, 540*2 + 10), (255, 255, 255))
for k, im in enumerate(ims): S.paste(im, ((k % 3)*550, (k//3)*550))
S.save(ROOT + '/3d/v3/v3_preview_frames.jpg', quality=92)
