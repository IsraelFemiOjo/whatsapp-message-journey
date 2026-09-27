"""Shared compositing helpers for the send journey."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import sys, math, json, numpy as np
sys.path.insert(0, ROOT + '/3d'); sys.path.insert(0, ROOT + '/shared')
import OpenEXR
from deep import *
from PIL import Image, ImageDraw, ImageFilter

def load(path):
    with OpenEXR.File(path) as f:
        ch = {}
        for p in f.parts:
            for k, v in p.channels.items(): ch[k] = v.pixels
    N = np.stack([ch['ViewLayer.Normal.X'], ch['ViewLayer.Normal.Y'], ch['ViewLayer.Normal.Z']], -1).astype(np.float32)
    out = dict(A=ch['ViewLayer.Combined'][..., 3], N=N, Z=ch['ViewLayer.Depth.Z'].astype(np.float32),
               I=np.rint(ch['ViewLayer.Object Index.X']).astype(np.int16))
    if 'ViewLayer.P' in ch: out['P'] = ch['ViewLayer.P'][..., :3].astype(np.float32)
    return out

def projector(cam, W, H):
    M = np.array(cam['M'], np.float64); Minv = np.linalg.inv(M); f = cam['lens']/cam['sensor']
    def proj(pts):
        pts = np.atleast_2d(np.asarray(pts, np.float64))
        ph = np.c_[pts, np.ones(len(pts))] @ Minv.T
        z = -ph[:, 2]
        x = 0.5 + f*ph[:, 0]/np.maximum(z, 1e-6); y = 0.5 - f*ph[:, 1]/np.maximum(z, 1e-6)
        return np.c_[x*W, y*H], z
    return proj

def windows(img, P, ids=(12,), cell=(2.3, 3.1), frac=0.34, seed=0, strength=0.9):
    if 'P' not in P: return img
    I, N, X = P['I'], P['N'], P['P']
    m = np.isin(I, ids) & (np.abs(N[..., 2]) < 0.3)
    if not m.any(): return img
    ys, xs = np.nonzero(m)
    p = X[ys, xs]; n = N[ys, xs]
    along = np.where(np.abs(n[:, 1]) > np.abs(n[:, 0]), p[:, 0], p[:, 1])
    other = np.where(np.abs(n[:, 1]) > np.abs(n[:, 0]), p[:, 1], p[:, 0])
    cu, cv = along/cell[0], p[:, 2]/cell[1]
    fu, fv = cu - np.floor(cu), cv - np.floor(cv)
    inside = (fu > 0.22) & (fu < 0.78) & (fv > 0.28) & (fv < 0.78) & (p[:, 2] > 1.2)
    h = (np.floor(cu).astype(np.int64)*73856093 ^ np.floor(cv).astype(np.int64)*19349663 ^ np.floor(other).astype(np.int64)*83492791 ^ seed) % 1000
    lit = inside & (h < frac*1000)
    dim = inside & ~lit
    col = np.where((h % 5 == 0)[:, None], hexrgb('#A9CCF0'), np.where((h % 7 == 0)[:, None], hexrgb('#FFE6B8'), hexrgb('#FFC370')))
    out = img.copy()
    sel = lit
    out[ys[sel], xs[sel]] = out[ys[sel], xs[sel]]*(1 - strength) + col[sel]*strength
    out[ys[dim], xs[dim]] = out[ys[dim], xs[dim]]*0.75 + hexrgb('#26304A')*0.25
    return out

def dof(img, Z, I, focus, strength, S, levels=(5, 14, 30)):
    """cheap depth of field: blend between blurred copies by circle of confusion"""
    if strength <= 1e-3: return img
    z = np.where(I > 0, Z, 1e5)
    coc = np.clip(strength*np.abs(1 - focus/np.maximum(z, 1e-4)), 0, 1)
    pil = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    stack = [img] + [np.array(pil.filter(ImageFilter.GaussianBlur(r*S))).astype(np.float32) for r in levels]
    idx = coc*len(levels); lo = np.floor(idx).astype(int); fr = (idx - lo)[..., None]
    out = np.zeros_like(img)
    for k in range(len(stack)):
        wk = np.where(lo == k, 1 - fr[..., 0], 0) + np.where(lo == k - 1, fr[..., 0], 0)
        out += stack[k]*wk[..., None]
    return out

def polyline(L, pts, color, width, alpha=255):
    if len(pts) > 1: ImageDraw.Draw(L).line([tuple(p) for p in pts], fill=tuple(int(v) for v in hexrgb(color)) + (int(alpha),), width=max(1, int(width)), joint='curve')

CHARSET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/='
def scramble(text, k, seed):
    """first k characters scrambled; changes with seed so it churns on twos"""
    rng = np.random.default_rng(seed)
    return ''.join((CHARSET[rng.integers(len(CHARSET))] if (i < k and c != ' ') else c) for i, c in enumerate(text))

def route_strip(d, W, H, S, cur, C):
    nodes = ['PHONE', 'TOWER', 'STREET', 'COAST', 'OCEAN', 'SERVER', 'PHONE']
    sx0, sx1, sy = 48*S, W - 48*S, H - 44*S
    d.line([(sx0, sy), (sx1, sy)], fill=C('#CFEAF5', 60), width=int(1*S))
    d.line([(sx0, sy), (sx0 + (sx1 - sx0)*cur/6, sy)], fill=C(GOLD, 220), width=int(2*S))
    for i, nm in enumerate(nodes):
        x = sx0 + (sx1 - sx0)*i/6; done = i <= cur + 1e-6; here = abs(i - round(cur)) < 0.5
        d.ellipse([x - 4*S, sy - 4*S, x + 4*S, sy + 4*S], fill=C(GOLD if done else '#0A1422'), outline=C(GOLD if done else '#CFEAF5', 220), width=int(1.2*S))
        d.text((x, sy - 12*S), nm, font=font(MONO, 10*S), fill=C('#FFFFFF' if here else '#CFEAF5', 240 if here else 130), anchor='md')
    return sx0 + (sx1 - sx0)*cur/6, sy

def header(d, W, S, C, chapter, name, elapsed, alpha=255):
    d.text((48*S, 44*S), chapter, font=font(MONO_M, 13*S), fill=C('#FFFFFF', int(200*alpha/255)))
    d.line([(118*S, 53*S), (170*S, 53*S)], fill=C(CYAN, int(160*alpha/255)), width=int(1*S))
    d.text((180*S, 44*S), name, font=font(MONO, 13*S), fill=C('#CFEAF5', int(200*alpha/255)))
    d.text((W - 48*S, 44*S), 'ELAPSED', font=font(MONO, 13*S), fill=C('#CFEAF5', 170), anchor='ra')
    d.text((W - 48*S, 62*S), elapsed, font=font(MONO_M, 30*S), fill=C('#FFFFFF', 240), anchor='ra')

def halo_composite(im, O, S, col=(6, 5, 10), k=0.65):
    halo = O.split()[3].filter(ImageFilter.GaussianBlur(9*S)).point(lambda v: min(255, int(v*k*2.2)))
    im.alpha_composite(Image.merge('RGBA', (*Image.new('RGB', im.size, col).split(), halo)))
    im.alpha_composite(O)
    return im

def fade_text(d, xy, s, f, col, a, anchor='la'):
    if a <= 0: return
    c = tuple(int(v) for v in hexrgb(col)) + (int(255*min(1, a)),)
    d.text(xy, s, font=f, fill=c, anchor=anchor)

def ease(x): x = min(1, max(0, x)); return x*x*(3 - 2*x)
def seg(t, a, b): return min(1, max(0, (t - a)/(b - a)))
def inout(t, a, b, fi=0.25, fo=0.25): return seg(t, a, a + fi)*(1 - seg(t, b - fo, b))
