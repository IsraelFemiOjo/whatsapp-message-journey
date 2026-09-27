"""A quiet documentary bed under the narration: strings, a warm pad and sparse piano, following the journey.
Sampled instruments through FluidSynth, kept low so the voice leads."""
import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..')))
import sys, json, subprocess, mido
sys.path.insert(0, ROOT + '/3d/v3')
import sjtl as T

TPB = 480; BPM = 60
def tk(t): return int(round(t*TPB))           # at 60 bpm one beat is one second
ev = []
def n(t, ch, note, vel, dur):
    a = T.UNWARP(t); b = T.UNWARP(t + dur); ev.append((a, ch, note, vel, max(0.05, b - a)))

END = T.END
# chords per stretch of the journey (strings ch0, pad ch1): D major colour, a darker turn in the deep, home again in London
CH = [(0.0, [50, 57, 62, 66, 69], 'Lagos'), (7.6, [47, 54, 59, 62, 66], 'lock'), (11.4, [43, 50, 55, 59, 62], 'radio'),
      (14.45, [50, 57, 62, 64, 69], 'fiber'), (18.3, [45, 52, 57, 61, 64], 'coast'), (21.1, [47, 54, 59, 62, 66], 'map'),
      (24.55, [43, 50, 59, 62, 67], 'answer'), (26.1, [38, 45, 50, 53, 57], 'deep'), (29.2, [41, 48, 53, 57, 60], 'deep2'),
      (32.78, [43, 50, 55, 59, 62], 'server'), (36.3, [45, 52, 57, 60, 64], 'server2'), (39.33, [50, 57, 62, 66, 69], 'london'),
      (43.8, [38, 50, 57, 62, 66, 69, 74], 'final')]
for i, (t0, notes, name) in enumerate(CH):
    t1 = CH[i + 1][0] if i + 1 < len(CH) else END
    v = 52 if name not in ('answer', 'final') else 66
    for m in notes: n(t0, 0, m, v, t1 - t0 + 0.6)
    for m in notes[1:4]: n(t0, 1, m + 12, 44, t1 - t0 + 0.8)
# a low string pulse under the map guess, building to the answer
g0, ans = T.wt(6, 'far') - 0.4, T.wt(7, 'six')
t = g0; k = 0
while t < ans - 0.1:
    n(t, 2, 35, int(50 + 40*(t - g0)/(ans - g0)), 0.22); t += 0.5 - 0.2*(t - g0)/(ans - g0); k += 1
n(ans, 3, 38, 100, 3.0); n(ans, 3, 26, 90, 3.0)                  # soft timpani and low strings on the answer
# sparse piano: a few notes that answer the story beats
PIANO = [(0.4, 74), (1.3, 78), (2.62, 81), (4.3, 76), (5.3, 78), (6.2, 81), (7.75, 71), (8.8, 74), (9.35, 78),
         (15.4, 81), (15.9, 83), (16.4, 86), (18.6, 76), (19.3, 81), (27.0, 69), (31.72, 81), (35.18, 79), (40.5, 78), (40.8, 81), (41.3, 86), (43.85, 86), (43.85, 81), (43.85, 74)]
for t0, m in PIANO: n(t0, 4, m, 58 if t0 < 43 else 64, 1.6)
# a light celesta pulse while the message races under the road and through the server hall
for a, b, notes in ((15.3, 18.2, [74, 78, 81, 78]), (33.3, 36.2, [71, 74, 78, 74])):
    t = a; i = 0
    while t < b:
        n(t, 5, notes[i % 4], 40, 0.2); t += 0.25; i += 1

# the last beat: blue ticks, a small lift (already in new time)
for m in (74, 78, 81): ev.append((T.nwt(12, 'blue') + 0.25, 4, m + 12, 52, 1.6))
mid = mido.MidiFile(ticks_per_beat=TPB); tr = mido.MidiTrack(); mid.tracks.append(tr)
tr.append(mido.MetaMessage('set_tempo', tempo=mido.bpm2tempo(BPM), time=0))
for c, p, vol in ((0, 49, 88), (1, 89, 60), (2, 45, 70), (3, 47, 85), (4, 0, 80), (5, 8, 60)):
    tr.append(mido.Message('program_change', channel=c, program=p, time=0))
    tr.append(mido.Message('control_change', channel=c, control=7, value=vol, time=0))
    tr.append(mido.Message('control_change', channel=c, control=91, value=90, time=0))   # reverb send
msgs = []
for t0, c, m, v, d in ev:
    msgs.append((tk(t0), 1, mido.Message('note_on', channel=c, note=m, velocity=v)))
    msgs.append((tk(t0 + d), 0, mido.Message('note_off', channel=c, note=m, velocity=0)))
msgs.sort(key=lambda x: (x[0], x[1])); last = 0
for t_, _, m in msgs: m.time = t_ - last; last = t_; tr.append(m)
mid.save(ROOT + '/3d/v3/bed.mid')
subprocess.run(['fluidsynth', '-ni', '-g', '0.6', '-R', '1', '-r', '48000', '-F', ROOT + '/3d/v3/bed.wav',
                '/usr/share/sounds/sf2/FluidR3_GM.sf2', ROOT + '/3d/v3/bed.mid'], check=True, capture_output=True)
print('bed ok', len(ev))
