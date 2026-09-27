"""Clean 3D plates for the v3 edit: the old section compositors with every text layer switched off,
all rendered frames used (not just odd ones), full resolution returned, and a livelier palette."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import sys, os, glob, json, types, math, numpy as np
sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
from PIL import Image, ImageDraw
import deep

# text drawn with the old serif/mono fonts is dropped; the phone UI (Inter) still draws
_OLD = {deep.SERIF, deep.SERIF_I, deep.MONO, deep.MONO_M}
_orig_text = ImageDraw.ImageDraw.text
def _text(self, xy, text, fill=None, font=None, *a, **k):
    if font is not None and getattr(font, 'path', None) in _OLD: return
    return _orig_text(self, xy, text, fill, font, *a, **k)
ImageDraw.ImageDraw.text = _text

SRC = ROOT + '/3d'
import palette
def load_section(name, extra=(), pre=None):
    src = open(f'{SRC}/{name}.py').read()
    extra = list(palette.EXTRA.get(name, [])) + list(extra)
    src = src.split("if __name__ == '__main__':")[0]
    reps = [
        ("key = near(fi - fi % 2 + 1)", "key = near(fi + 1)"),
        ("key = near(fi + 1 - (fi % 2))", "key = near(fi + 1)"),
        ("f3 = fi - fi % 2 + 1; key = near(f3)", "f3 = fi + 1; key = near(f3)"),
        ("return im.convert('RGB').resize((1080, 1080), Image.LANCZOS)", "return im.convert('RGB')"),
        ("R3 = sys.argv[3] if len(sys.argv) > 3 else ", "R3 = "),
    ] + list(extra)
    for a, b in reps: src = src.replace(a, b)
    # merge the anchors of the in-between frames
    lines = src.split('\n')
    for i, l in enumerate(lines):
        if "AN = J['anchors']" in l:
            lines.insert(i + 1, "for _p in __import__('glob').glob(R3 + '/anchors_2_*.json'): AN.update(json.load(open(_p))['anchors'])")
            break
    src = '\n'.join(lines)
    m = types.ModuleType(name + '_v3'); m.__dict__['__file__'] = f'{SRC}/{name}.py'
    if pre: m.__dict__.update(pre)
    exec(compile(src, name + '_v3', 'exec'), m.__dict__)
    m.header = lambda *a, **k: None
    m.route_strip = lambda d, W, H, S, cur, C: (-100, -100)
    m.inout = lambda *a, **k: 0.0
    if name in palette.MATS:
        var, d = palette.MATS[name]; getattr(m, var).update(d)
    if name == 'sec5_comp':
        deep.MATS.update(palette.DEEP_MATS)
    return m

# ---------------- grade: livelier, richer colour on top of the same 3D look ----------------
def grade(img, sat=1.45, warm=(1.06, 1.0, 0.94), lift='#0B0E2A', contrast=1.1, bloom=0.35, gamma=1.0):
    x = (img.astype(np.float32)/255.0)**gamma
    lum = (x @ np.array([0.2126, 0.7152, 0.0722], np.float32))[..., None]
    x = lum + (x - lum)*sat                                   # saturation
    x = np.clip(x, 0, 1)
    x = 0.5 + (x - 0.5)*contrast
    sh = (1 - np.clip(lum*2.2, 0, 1))**2                      # tint the shadows so blacks are never dead grey
    x = x + sh*(np.array(deep.hexrgb(lift), np.float32)/255.0)*0.9
    x = x*np.array(warm, np.float32)
    x = np.clip(x, 0, 1)
    if bloom > 0:
        hi = np.clip((x - 0.62)/0.38, 0, 1)
        pil = Image.fromarray((hi*255).astype(np.uint8))
        from PIL import ImageFilter
        b1 = np.array(pil.filter(ImageFilter.GaussianBlur(x.shape[1]*0.006))).astype(np.float32)/255
        b2 = np.array(pil.filter(ImageFilter.GaussianBlur(x.shape[1]*0.025))).astype(np.float32)/255
        x = 1 - (1 - x)*(1 - bloom*(0.6*b1 + 0.8*b2))            # screen blend
    return (np.clip(x, 0, 1)*255).astype(np.uint8)
