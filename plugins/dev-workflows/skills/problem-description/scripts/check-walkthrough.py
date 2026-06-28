#!/usr/bin/env python3
"""Post-assembly self-test for an assembled problem-description walkthrough (Phase 2).

There is no build step, so this static check is the safety net that catches a
splice that produced a byte-perfectly-self-contained file that is silently broken.
Run it on every assembled walkthrough before declaring done.

Checks:
  A. Self-contained — no external <script src>/<link href> (data: URIs ok).
  B. MODE is set and modeRenderers[MODE] is registered.
  C. render(step) runs RENDER_HOOKS as its FIRST statement (drawer/hooks fire before paint).
  D. If a term-drilldown drawer is present: closeDrawer defined, pushed to RENDER_HOOKS,
     GLOSSARY present, and every data-term / seeAlso key resolves (drawer composition).
  E. Scenes are clean — no createElement/appendChild and no drawer refs inside scenes[]
     (idempotency + orthogonality).
  F. Source order — engine modeRenderers declaration < pack registration < MODE assignment.

Usage: python check-walkthrough.py ASSEMBLED.html
"""
import re, sys, pathlib


def main(path):
    src = pathlib.Path(path).read_text(encoding='utf-8')
    errs = []

    # A. self-contained
    for m in re.finditer(r'<(script|link)\b[^>]*\b(src|href)\s*=\s*["\']([^"\']+)["\']', src, re.I):
        if not m.group(3).startswith('data:'):
            errs.append(f'external resource not allowed: <{m.group(1)} {m.group(2)}="{m.group(3)}">')

    # B. MODE + renderer registration
    mm = re.search(r"\bMODE\s*=\s*'([\w-]+)'", src)
    if not mm:
        errs.append("MODE is not set (expected MODE = '<mode>')")
    elif not re.search(r"modeRenderers\[\s*'" + re.escape(mm.group(1)) + r"'\s*\]\s*=", src):
        errs.append(f"modeRenderers['{mm.group(1)}'] is not registered")

    # C. render runs RENDER_HOOKS first
    if not re.search(r'function render\s*\([^)]*\)\s*\{\s*RENDER_HOOKS\b', src):
        errs.append('render() does not run RENDER_HOOKS as its first statement')

    # D. drawer composition (only if a drawer is present)
    if 'id="termDrawer"' in src:
        if 'function closeDrawer' not in src:
            errs.append('drawer present but closeDrawer() not defined')
        if not re.search(r'RENDER_HOOKS\.push\s*\(\s*closeDrawer\s*\)', src):
            errs.append('drawer present but closeDrawer not pushed to RENDER_HOOKS')
        gm = re.search(r'const GLOSSARY\s*=\s*\{(.*?)\n\};', src, re.S)
        if not gm:
            errs.append('drawer present but GLOSSARY missing')
        else:
            keys = set(re.findall(r"^\s*'([\w-]+)'\s*:\s*\{", gm.group(1), re.M))
            for t in re.findall(r'data-term="([^"]+)"', src):
                if t not in keys:
                    errs.append(f'data-term="{t}" has no GLOSSARY entry')
            for arr in re.findall(r'seeAlso\s*:\s*\[([^\]]*)\]', gm.group(1)):
                for k in re.findall(r"'([\w-]+)'", arr):
                    if k not in keys:
                        errs.append(f'seeAlso "{k}" has no GLOSSARY entry')

    # E. scenes clean
    sm = re.search(r'const scenes\s*=\s*\[(.*?)\];\s*TOTAL', src, re.S)
    if not sm:
        errs.append('could not locate `const scenes = [ ... ]; TOTAL`')
    else:
        for bad in ('createElement', 'appendChild', 'openTerm', 'closeDrawer', 'termDrawer', 'GLOSSARY', 'drawerStack'):
            if bad in sm.group(1):
                errs.append(f'scene code references "{bad}" — must stay out of scenes')

    # F. source order
    decl = src.find('const modeRenderers')
    regm = re.search(r"modeRenderers\[\s*'[\w-]+'\s*\]\s*=", src)
    reg = regm.start() if regm else -1
    setm = re.search(r"\bMODE\s*=\s*'[\w-]+'", src)
    setpos = setm.start() if setm else -1
    if decl == -1:
        errs.append('engine `const modeRenderers` declaration missing')
    elif not (decl < reg < setpos):
        errs.append('source order wrong: expect engine modeRenderers decl < pack registration < MODE assignment')

    if errs:
        for e in errs:
            print('FAIL:', e)
        sys.exit(1)
    mode = mm.group(1) if mm else '?'
    drawer = 'with drawer' if 'id="termDrawer"' in src else 'no drawer'
    print(f'OK: {pathlib.Path(path).name} — mode={mode} ({drawer}); self-contained, RENDER_HOOKS-first, scenes clean, order ok')


if __name__ == '__main__':
    main(sys.argv[1])
