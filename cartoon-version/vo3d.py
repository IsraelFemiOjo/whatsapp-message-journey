"""Documentary narration for the 3D cut.
Kokoro reads each sentence, then Praat reshapes the pitch and timing word by word from an emotion plan:
accents on the words that carry the meaning, real rises on the questions, a lower slower register for awe."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import re, json, math, numpy as np, soundfile as sf, parselmouth
from parselmouth.praat import call
from kokoro_onnx import Kokoro

k = Kokoro(ROOT + '/tools/tts/models/kokoro_dur.onnx', ROOT + '/tools/tts/models/voices-v1.0.bin')
V = 0.55*k.get_voice_style('bm_george') + 0.45*k.get_voice_style('bm_lewis')    # mature British narrator, a little deeper
SR = 24000

# Markup: *word* accent, ^ question rise on the last word, mood per line.
# mood: (speed, base semitones, range factor, pause after)
PLAN = [
    ("What *actually* happens in the *second* after you hit *send* on WhatsApp^", 'curious'),
    ("Let's *follow* one message. From *Lagos*, to *London*.", 'invite'),
    ("First, your phone *locks* it. Only *you* and your *friend* can read it. Not even *WhatsApp*.", 'reveal'),
    ("It shoots out as *radio* waves, to the *nearest* cell tower.", 'brisk'),
    ("Then it turns into *light*, and *races* through glass cables under the road.", 'excited'),
    ("At the coast, it *dives*. Into the *ocean*.", 'dramatic'),
    ("Quick guess. How *far* does it travel down there^", 'playful'),
    ("Over *six* *thousand* kilometers. In a cable about as thick as a *garden* hose.", 'awe'),
    ("Every seventy kilometers or so, a *repeater* *boosts* the light.", 'brisk'),
    ("Out of the sea, it reaches a WhatsApp *server*. *One* grey tick. The server *has* it. But it *can't* read it.", 'reveal'),
    ("Then it jumps to your *friend's* phone, and *unlocks*. *Two* grey ticks.", 'warm'),
    ("All of that, in *under* a *second*.", 'finale'),
]
MOOD = {'curious': (1.08, 0.0, 1.45, 0.10), 'invite': (1.12, 0.5, 1.35, 0.10), 'reveal': (1.08, 0.0, 1.4, 0.12),
        'brisk': (1.16, 0.3, 1.3, 0.08), 'excited': (1.18, 1.0, 1.45, 0.08), 'dramatic': (1.04, -0.3, 1.5, 0.12),
        'playful': (1.1, 0.8, 1.5, 0.75), 'awe': (0.98, -1.2, 1.4, 0.12), 'warm': (1.08, 0.2, 1.35, 0.12), 'finale': (0.96, -1.0, 1.35, 0.0)}
GLOBAL_ST = -1.3      # a touch lower overall for gravitas

def words_of(line):
    toks = line.split()
    out = []
    for w in toks:
        acc = w.startswith('*') or '*' in w
        q = w.endswith('^')
        clean = w.replace('*', '').replace('^', '?')
        out.append((clean, acc, q))
    return out

def timings(text, speed):
    a, sr, tm = k.create_timed(text, voice=V, speed=speed, lang='en-gb', sentence_pause=0.12, clause_pause=0.05)
    strip = lambda x: re.sub(r"[ˈˌ\s.,!?;:—…\"]", "", x)
    stream = [p for p in tm if strip(p.phoneme)]
    tw = text.split()
    lens = [max(1, len(strip(k.tokenizer.phonemize(re.sub(r"[.,!?]", "", w), 'en-gb')))) for w in tw]
    scale = len(stream)/sum(lens); acc = 0.0; spans = []
    for L in lens:
        i0 = int(round(acc)); acc += L*scale; i1 = max(i0 + 1, int(round(acc)))
        i0 = min(i0, len(stream) - 1); i1 = min(i1, len(stream))
        spans.append((stream[i0].start, stream[i1 - 1].end))
    return a, spans

def shape(audio, spans, words, mood):
    speed, base, rng_, _ = MOOD[mood]
    snd = parselmouth.Sound(audio.astype(np.float64), sampling_frequency=SR)
    manip = call(snd, "To Manipulation", 0.01, 60, 320)
    pt = call(manip, "Extract pitch tier")
    n = call(pt, "Get number of points")
    ts = np.array([call(pt, "Get time from index", i + 1) for i in range(n)])
    vs = np.array([call(pt, "Get value at index", i + 1) for i in range(n)])
    if n < 3: return audio, spans
    st = 12*np.log2(vs/np.median(vs))
    med = np.median(vs)
    # expand the melody around the speaker's middle so it stops sounding flat
    st2 = st*rng_
    # word accents: a smooth bump on the stressed part of each accented word
    dur = len(audio)/SR
    for (w, acc, q), (s0, s1) in zip(words, spans):
        if acc:
            c = s0 + 0.4*(s1 - s0); wdt = max(0.06, (s1 - s0)*0.45)
            st2 += 4.0*np.exp(-((ts - c)/wdt)**2)
    # a real question rise: the last word climbs from the current level instead of falling into creak
    for idx, ((w, acc, q), (s0, s1)) in enumerate(zip(words, spans)):
        if q:
            m = (ts >= s0 - 0.02) & (ts <= s1 + 0.15)
            if m.sum() >= 2:
                tv = ts[m]; ramp = (tv - tv.min())/max(0.05, tv.max() - tv.min())
                prev = (ts >= spans[max(0, idx - 2)][0]) & (ts < s0)
                anchor = np.median(st2[prev]) if prev.any() else np.median(st2)
                st2[m] = anchor - 0.8 + 8.0*ramp**1.25
    # sentence end falls gently unless it is a question
    if not any(q for _, _, q in words):
        s_last0, s_last1 = spans[-1]
        s_mid = s_last0 + 0.5*(s_last1 - s_last0)
        st2 -= np.where(ts > s_mid, 2.0*np.clip((ts - s_mid)/max(0.05, s_last1 - s_mid), 0, 1), 0)
    st2 += base + GLOBAL_ST
    new = med*2**(st2/12)
    pt2 = call("Create PitchTier", "shaped", 0, dur)
    for t_, v_ in zip(ts, new): call(pt2, "Add point", float(t_), float(v_))
    call([pt2, manip], "Replace pitch tier")
    # lengthen accented words a little, the way a narrator leans on them
    dt = call("Create DurationTier", "len", 0, dur)
    call(dt, "Add point", 0.0, 1.0)
    for (w, acc, q), (s0, s1) in zip(words, spans):
        if acc or q:
            call(dt, "Add point", max(0, s0 - 0.01), 1.0); call(dt, "Add point", s0 + 0.01, 1.08)
            call(dt, "Add point", s1 - 0.01, 1.08); call(dt, "Add point", s1 + 0.01, 1.0)
    call([dt, manip], "Replace duration tier")
    out = call(manip, "Get resynthesis (overlap-add)")
    y = np.array(out.values[0], dtype=np.float32)
    # map the word times through the stretch
    grid = np.linspace(0, dur, 4000)
    fac = np.ones_like(grid)
    for (w, acc, q), (s0, s1) in zip(words, spans):
        if acc or q: fac[(grid >= s0) & (grid <= s1)] = 1.08
    newt = np.concatenate([[0], np.cumsum(fac[1:]*np.diff(grid))])
    remap = lambda x: float(np.interp(x, grid, newt))
    spans2 = [(remap(a), remap(b)) for a, b in spans]
    # gentle loudness lift on accents
    g = np.ones(len(y))
    for (w, acc, q), (a_, b_) in zip(words, spans2):
        if acc:
            i0, i1 = int(a_*SR), min(len(y), int(b_*SR))
            g[i0:i1] = 1.18
    g = np.convolve(g, np.ones(480)/480, mode='same')
    return y*g, spans2

parts, allw, t0 = [], [], 0.0
for li, (line, mood) in enumerate(PLAN):
    words = words_of(line)
    text = ' '.join(w for w, _, _ in words)
    speed = MOOD[mood][0]*1.12
    a, spans = timings(text, speed)
    y, spans2 = shape(a, spans, words, mood)
    for (w, acc, q), (s0, s1) in zip(words, spans2):
        allw.append({'w': w, 's': round(t0 + s0, 3), 'e': round(t0 + s1, 3), 'line': li, 'acc': acc})
    parts.append(y); t0 += len(y)/SR
    gap = MOOD[mood][3]
    parts.append(np.zeros(int(gap*SR), np.float32)); t0 += gap
audio = np.concatenate(parts)
audio = audio/np.abs(audio).max()*0.9
sf.write(ROOT + '/cartoon-version/vo3d_raw.wav', audio, SR)
json.dump(allw, open(ROOT + '/cartoon-version/words_3d.json', 'w'), indent=0)
print('narration', round(len(audio)/SR, 2), 's', len(allw), 'words')
