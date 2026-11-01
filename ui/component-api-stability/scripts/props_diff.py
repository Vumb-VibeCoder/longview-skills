#!/usr/bin/env python3
"""Compare the props of a TypeScript component between two versions of a file (regex-based, not a full parser).
Usage: python props_diff.py old.tsx new.tsx [InterfaceOrTypeName]
Finds `interface X {...}` / `type X = {...}` blocks (default: the first whose name ends in Props).
Classifies: REMOVED, ADDED_REQUIRED, OPTIONAL_TO_REQUIRED, TYPE_CHANGED (breaking); ADDED_OPTIONAL, REQUIRED_TO_OPTIONAL (safe).
Exit code 1 if any breaking change."""
import re, sys

def block(src, name=None):
    pat = re.compile(r'(?:interface\s+(\w+)(?:\s+extends[^{]+)?\s*\{|type\s+(\w+)\s*=\s*\{)')
    for m in pat.finditer(src):
        n = m.group(1) or m.group(2)
        if (name and n == name) or (not name and n.endswith('Props')):
            i, depth = m.end(), 1
            while i < len(src) and depth:
                depth += (src[i] == '{') - (src[i] == '}'); i += 1
            return n, src[m.end():i - 1]
    return None, None

def props(body):
    out = {}
    body = re.sub(r'/\*.*?\*/', '', re.sub(r'//[^\n]*', '', body), flags=re.S).replace('=>', ' returns ')
    depth, cur, parts = 0, '', []
    for ch in body:
        if ch in '{<(': depth += 1
        if ch in '}>)': depth -= 1
        if ch in ';,\n' and depth == 0:
            parts.append(cur); cur = ''
        else: cur += ch
    parts.append(cur)
    for p in parts:
        m = re.match(r'\s*(readonly\s+)?([\w$]+)(\?)?\s*:\s*(.+?)\s*$', p, re.S)
        if m: out[m.group(2)] = (bool(m.group(3)), re.sub(r'\s+', ' ', m.group(4)))
    return out

def main():
    if len(sys.argv) < 3: print(__doc__); sys.exit(2)
    nm = sys.argv[3] if len(sys.argv) > 3 else None
    n1, b1 = block(open(sys.argv[1], encoding='utf-8').read(), nm)
    n2, b2 = block(open(sys.argv[2], encoding='utf-8').read(), nm)
    if b1 is None or b2 is None: print('ERROR props type not found in one of the files (pass its name as 3rd argument)'); sys.exit(2)
    a, b = props(b1), props(b2); brk = []; safe = []
    for k in a:
        if k not in b: brk.append(f'REMOVED {k} (if renamed, keep the old name as a deprecated alias)')
    for k, (opt, t) in b.items():
        if k not in a:
            (safe if opt else brk).append(('ADDED_OPTIONAL ' if opt else 'ADDED_REQUIRED ') + k)
        else:
            oo, ot = a[k]
            if ot != t: brk.append(f'TYPE_CHANGED {k}: {ot} -> {t} (narrowing breaks callers; widening is safe only for inputs, not callbacks/outputs: check)')
            if oo and not opt: brk.append(f'OPTIONAL_TO_REQUIRED {k}')
            if not oo and opt: safe.append(f'REQUIRED_TO_OPTIONAL {k}')
    print(f'{n1}: {len(a)} props -> {n2}: {len(b)} props')
    for x in brk: print('BREAKING', x)
    for x in safe: print('safe    ', x)
    if not brk and not safe: print('no prop-level change detected')
    sys.exit(1 if brk else 0)

if __name__ == '__main__': main()
