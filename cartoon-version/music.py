"""Score for the cartoon cut: 124 bpm, D major (Bm G D A), played by sampled instruments through FluidSynth.
Sections follow the picture: groove, a ticking breakdown for the quick guess, a drop on the answer, a lighter server bit, a build, a last hit."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..')))
import json, subprocess, mido

BPM = 124; BEAT = 60/BPM; S16 = BEAT/4
G0 = 0.42                     # first downbeat lands on the send tap
TPB = 480
def tick(t): return int(round(t/BEAT*TPB))

words = json.load(open(ROOT + '/cartoon-version/words_am_puck.json'))
def wt(l, sub): return [x for x in words if x['line'] == l and sub.lower() in x['w'].lower()][0]['s']
END = words[-1]['e'] + 1.1
def q8(t): return G0 + round((t - G0)/(BEAT/2))*(BEAT/2)
GUESS0, ANSWER = q8(wt(6, 'guess') - 0.25), q8(wt(7, 'six'))
SERVER0, LONDON0, FINAL = q8(wt(9, 'out')), q8(wt(10, 'jumps')), q8(wt(11, 'second'))
BOOST = q8(wt(8, 'boosts')); LIGHT = q8(wt(4, 'light')); DIVE = q8(wt(5, 'dives'))

ev = []   # (time, channel, note, vel, dur)
def n(t, ch, note, vel, dur):
    if t < END: ev.append((t, ch, note, vel, dur))
PROG = [(35, [59, 62, 66]), (31, [55, 59, 62]), (38, [62, 66, 69]), (33, [57, 61, 64])]   # Bm G D A
BAR = 4*BEAT
def section(t):
    if t < G0: return 'pre'
    if GUESS0 <= t < ANSWER: return 'guess'
    if SERVER0 <= t < LONDON0: return 'light'
    if LONDON0 <= t < FINAL: return 'build'
    if t >= FINAL: return 'end'
    return 'full'

# riser into the first hit
n(0.0, 6, 60, 90, G0 + 0.05)
b = 0
while G0 + b*BAR < END:
    root, ch = PROG[b % 4]; t0 = G0 + b*BAR
    for s in range(16):
        t = t0 + s*S16; sec = section(t)
        if t >= END or sec == 'end': continue
        if sec in ('full', 'build'):
            if s % 4 == 0: n(t, 9, 36, 118, S16)                                   # kick on every beat
            if s in (4, 12): n(t, 9, 38, 100, S16); n(t, 9, 39, 70, S16)           # snare and clap
            n(t, 9, 42, 70 if s % 2 else 45, S16/2)                                 # sixteenth hats
            if s in (6, 14): n(t, 9, 46, 60, S16*2)
            if s % 2 == 0 or s in (3, 11): n(t, 0, root, 100, S16*1.6)              # driving bass
            n(t, 1, ch[0], 72 if s % 4 == 0 else 52, S16*0.7)                        # muted guitar chug
            if s % 2 == 0: n(t, 2, ch[[0, 1, 2, 1, 2, 0, 1, 2][(s//2) % 8]] + 12, 64, S16*1.5)   # pizzicato ostinato
        elif sec == 'light':
            if s in (0, 10): n(t, 9, 36, 100, S16)
            if s in (4, 12): n(t, 9, 39, 80, S16)
            if s % 2 == 0: n(t, 9, 42, 50, S16/2)
            if s in (0, 6, 10): n(t, 0, root, 90, S16*3)
            if s % 2 == 0: n(t, 2, ch[[0, 1, 2, 1][(s//2) % 4]] + 12, 58, S16*1.5)
        elif sec == 'guess':
            if s % 2 == 0: n(t, 7, 76 if s % 4 == 0 else 72, 100, S16)             # a clock ticking while you guess
            if s == 0: n(t, 0, root - 12 + 12, 70, BAR*0.95)
        if sec == 'build' and t > FINAL - BAR:                                       # snare roll into the last hit
            n(t, 9, 38, int(60 + 60*(t - (FINAL - BAR))/BAR), S16/2)
    sec0 = section(t0 + 0.01)
    if sec0 in ('full', 'build', 'light', 'guess'):
        for m in ch: n(t0, 4, m - 12, 48 if sec0 != 'guess' else 60, BAR)          # string pad
    b += 1
# brass stabs and crashes on the big moments
for t in (G0, LIGHT, DIVE, ANSWER, BOOST):
    n(t, 9, 49, 110, BEAT*2)
    for m in (62, 66, 69, 74): n(t, 3, m, 105, BEAT*0.6)
n(FINAL, 9, 49, 120, BEAT*4); n(FINAL, 9, 36, 127, BEAT)
for m in (50, 62, 66, 69, 74): n(FINAL, 3, m, 112, BEAT*3)
for m in (38, 50): n(FINAL, 0, m, 110, BEAT*4)
for m in (62, 66, 69, 74): n(FINAL, 4, m, 80, BEAT*5)

mid = mido.MidiFile(ticks_per_beat=TPB)
tr = mido.MidiTrack(); mid.tracks.append(tr)
tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM), time=0))
for chn, prog in ((0, 33), (1, 28), (2, 45), (3, 61), (4, 48), (6, 119), (7, 115)):
    tr.append(mido.Message('program_change', channel=chn, program=prog, time=0))
for chn, vol in ((0, 110), (1, 70), (2, 88), (3, 92), (4, 60), (6, 90), (7, 76), (9, 105)):
    tr.append(mido.Message('control_change', channel=chn, control=7, value=vol, time=0))
tr.append(mido.Message('control_change', channel=2, control=10, value=40, time=0))
tr.append(mido.Message('control_change', channel=1, control=10, value=88, time=0))
msgs = []
for t, chn, note, vel, dur in ev:
    msgs.append((tick(t), 1, mido.Message('note_on', channel=chn, note=int(note), velocity=int(min(127, vel)))))
    msgs.append((tick(t + dur), 0, mido.Message('note_off', channel=chn, note=int(note), velocity=0)))
msgs.sort(key=lambda x: (x[0], x[1]))
last = 0
for tk, _, m in msgs:
    m.time = tk - last; last = tk; tr.append(m)
mid.save(ROOT + '/cartoon-version/score.mid')
subprocess.run(['fluidsynth', '-ni', '-g', '0.7', '-R', '1', '-C', '1', '-r', '48000', '-F', ROOT + '/cartoon-version/score.wav',
                '/usr/share/sounds/sf2/FluidR3_GM.sf2', ROOT + '/cartoon-version/score.mid'], check=True, capture_output=True)
print('score', len(ev), 'notes', round(END, 2), 's')
