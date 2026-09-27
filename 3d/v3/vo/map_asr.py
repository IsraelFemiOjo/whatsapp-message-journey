import os as _os; ROOT = _os.environ.get('PROJECT_ROOT', _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..', '..', '..')))
import json, re, difflib
A = json.load(open(ROOT + '/tools/asr/asr_fast.json'))
lines = [l.strip() for l in open('script_new.txt') if l.strip()]
S = []
for li, l in enumerate(lines):
    for w in l.split(): S.append({'w': w, 'line': li})
norm = lambda s: re.sub(r"[^a-z']", '', s.lower())
a_n = [norm(w['w']) for w in A]; s_n = [norm(w['w']) for w in S]
sm = difflib.SequenceMatcher(None, s_n, a_n, autojunk=False)
t = [None]*len(S)
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag == 'equal' or (tag == 'replace' and (i2 - i1) == (j2 - j1)):
        for k in range(i2 - i1): t[i1 + k] = (A[j1 + k]['s'], A[j1 + k]['e'])
    elif tag == 'replace':
        # spread the script words across the heard span
        s0, s1 = A[j1]['s'], A[j2 - 1]['e']
        n = i2 - i1
        for k in range(n): t[i1 + k] = (s0 + (s1 - s0)*k/n, s0 + (s1 - s0)*(k + 1)/n)
# fill any gaps by interpolation
for i in range(len(S)):
    if t[i] is None:
        p = max(j for j in range(i) if t[j]) if any(t[:i]) else None
        q = min(j for j in range(i + 1, len(S)) if t[j]) if any(t[i + 1:]) else None
        a = t[p][1] if p is not None else 0.0; b = t[q][0] if q is not None else a + 0.3
        t[i] = (a, b)
ACC = {0: ['wondered', 'second'], 1: ['follow'], 2: ['scrambles', 'code', 'you', 'friend', 'whatsapp'], 3: ['nearest', 'tower', 'radio'],
       4: ['light', 'glass'], 5: ['dives', 'atlantic'], 6: ['far', 'think'], 7: ['six', 'thousand', 'garden'], 8: ['repeater', 'boosts'],
       9: ['server', 'one', "can't", 'word'], 10: ["friend's", 'unlocks', 'two'], 11: ['under', 'second'], 12: ['blue', 'friend']}
out = []
for w, (s, e) in zip(S, t):
    out.append({'w': w['w'], 'line': w['line'], 's': round(s, 3), 'e': round(e, 3), 'acc': norm(w['w']) in ACC.get(w['line'], [])})
json.dump(out, open('gemini_words.json', 'w'), indent=0)
L = {}
for w in out: L.setdefault(w['line'], []).append(w)
for k, v in L.items(): print(k, v[0]['s'], v[-1]['e'], ' '.join(f"{x['w']}@{x['s']:.2f}" for x in v))
