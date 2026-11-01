#!/usr/bin/env python3
"""Scan CSS/SCSS/JS/TS/JSX/TSX/HTML/Vue/Svelte for hard-coded design values. Standard library only.
Usage: python ui_scan.py <dir> [--json]
Reports: raw colors, px sizes, font sizes and z-indexes used OUTSIDE token definitions, and how many distinct values exist.
Token definitions (skipped as violations): lines declaring CSS custom properties (--x:), SCSS vars ($x:), or inside files named tokens/theme/variables."""
import os, re, sys, json, collections
EXT = {'.css', '.scss', '.sass', '.less', '.js', '.jsx', '.ts', '.tsx', '.html', '.vue', '.svelte'}
SKIP = {'node_modules', '.git', 'dist', 'build', '.next', 'coverage'}
COLOR = re.compile(r'#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b|\brgba?\([^)]*\)|\bhsla?\([^)]*\)')
FONT = re.compile(r'font-size\s*:\s*([\d.]+(?:px|rem|em))|fontSize\s*:\s*[\'"]?([\d.]+(?:px|rem|em)?)')
SPACE = re.compile(r'\b(?:margin|padding|gap|top|left|right|bottom)(?:-[a-z]+)?\s*:\s*([\d.]+px)')
ZIDX = re.compile(r'z-index\s*:\s*(-?\d+)|zIndex\s*:\s*(-?\d+)')
TOKENFILE = re.compile(r'(token|theme|variables|palette|colors)', re.I)

def norm(c): return c.lower().replace(' ', '')

def scan(root):
    viol = collections.defaultdict(list)
    seen = {k: collections.Counter() for k in ('color', 'font', 'space', 'z')}
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP]
        for f in fn:
            if os.path.splitext(f)[1] not in EXT: continue
            p = os.path.join(dp, f); is_tok = bool(TOKENFILE.search(f))
            try: lines = open(p, encoding='utf-8', errors='replace').read().splitlines()
            except OSError: continue
            for i, ln in enumerate(lines, 1):
                s = ln.strip()
                if s.startswith(('//', '/*', '*')): continue
                is_def = is_tok or re.match(r'(--[\w-]+|\$[\w-]+|@[\w-]+)\s*:', s)
                for m in COLOR.finditer(ln):
                    seen['color'][norm(m.group())] += 1
                    if not is_def: viol['color'].append((p, i, m.group()))
                for m in FONT.finditer(ln):
                    v = m.group(1) or m.group(2); v = v + 'px' if v.replace('.', '', 1).isdigit() else v; seen['font'][v] += 1
                    if not is_def: viol['font'].append((p, i, v))
                for m in SPACE.finditer(ln):
                    seen['space'][m.group(1)] += 1
                    if not is_def and m.group(1) not in ('0px', '1px'): viol['space'].append((p, i, m.group(1)))
                for m in ZIDX.finditer(ln):
                    v = m.group(1) or m.group(2); seen['z'][v] += 1
                    if not is_def: viol['z'].append((p, i, v))
    return viol, seen

def main():
    if len(sys.argv) < 2: print(__doc__); sys.exit(2)
    if not os.path.isdir(sys.argv[1]): print('ERROR not a directory'); sys.exit(2)
    viol, seen = scan(sys.argv[1])
    if '--json' in sys.argv:
        print(json.dumps({'violations': {k: len(v) for k, v in viol.items()}, 'distinct': {k: len(v) for k, v in seen.items()}}, indent=2)); return
    for k in ('color', 'font', 'space', 'z'):
        v = viol.get(k, [])
        print(f"{k}: {len(v)} hard-coded uses, {len(seen[k])} distinct values")
        top = collections.Counter(x[2] for x in v).most_common(5)
        if top: print('   most repeated:', ', '.join(f'{a} x{n}' for a, n in top))
        for p, i, val in v[:3]: print(f'   e.g. {p}:{i} {val}')
    near = near_dupes(seen['color'])
    if near: print('near-duplicate colors (likely the same intent drifted):', '; '.join(f'{a} ~ {b}' for a, b in near[:8]))

def hexrgb(c):
    if c.startswith('#'):
        h = c[1:]
        if len(h) == 3: h = ''.join(x * 2 for x in h)
        if len(h) >= 6: return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return None

def near_dupes(counter, tol=12):
    cs = [(c, hexrgb(c)) for c in counter if hexrgb(c)]; out = []
    for i in range(len(cs)):
        for j in range(i + 1, len(cs)):
            a, b = cs[i][1], cs[j][1]
            if cs[i][0] != cs[j][0] and sum(abs(x - y) for x, y in zip(a, b)) <= tol: out.append((cs[i][0], cs[j][0]))
    return out

if __name__ == '__main__': main()
