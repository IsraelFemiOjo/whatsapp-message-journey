import sys, numpy as np
from PIL import Image
import anim
ts = [float(x) for x in sys.argv[1].split(',')]
ims = [Image.fromarray(anim.frame(int(t*anim.FPS))).resize((360, 360)) for t in ts]
cols = 6; rows = (len(ims) + cols - 1)//cols
S = Image.new('RGB', (360*cols, 360*rows))
for k, im in enumerate(ims): S.paste(im, ((k % cols)*360, (k//cols)*360))
S.save(sys.argv[2])
