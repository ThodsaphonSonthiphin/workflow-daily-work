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
  G. JS syntax — node --check the assembled <script> (skipped when node is absent).
  H. Keyboard — the engine's keydown listener for ArrowRight/ArrowLeft is present (ADR 0356).
  I. Controls first — the buttons come before the narration (ADR 0358).
  J. UML kit — a kit picture needs the kit CSS and the kit CSS needs a picture; every
     picture declares its type and has a caption; at most 3 pictures (ADRs 0361, 0363, 0364).
  K. Sequence mode — the legend exists and every message declares its kind (ADR 0363).

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

    # A2. no unsubstituted authoring placeholder (the assembler fills the h1/title)
    if '[INSERT' in src:
        errs.append('unsubstituted "[INSERT…]" placeholder remains — pass --title to the assembler')

    # B. MODE + renderer registration (+ the renderer satisfies the registry/clear contract)
    mm = re.search(r"\bMODE\s*=\s*'([\w-]+)'", src)
    if not mm:
        errs.append("MODE is not set (expected MODE = '<mode>')")
    else:
        rm0 = re.search(r"modeRenderers\[\s*'" + re.escape(mm.group(1)) + r"'\s*\]\s*=", src)
        if not rm0:
            errs.append(f"modeRenderers['{mm.group(1)}'] is not registered")
        else:
            window = src[rm0.start():rm0.start() + 5000]
            if 'registry' not in window or not re.search(r'\bclear\s*\(', window):
                errs.append(f"modeRenderers['{mm.group(1)}'] is missing registry/clear (renderer contract)")

    # C. render runs RENDER_HOOKS first
    if not re.search(r'function render\s*\([^)]*\)\s*\{\s*RENDER_HOOKS\b', src):
        errs.append('render() does not run RENDER_HOOKS as its first statement')

    # D. drawer composition (only if a drawer is present)
    if 'id="termDrawer"' in src:
        if 'data-term="' not in src:
            errs.append('drawer assembled but no data-term spans use it — drop --drawer or mark terms')
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
    elif re.search(r'data-term="', src):
        # terms marked drillable but no drawer assembled: the .term styling and the click
        # handler both live in the drawer pack, so the spans render as inert plain text.
        errs.append('data-term spans present but no drawer assembled — pass --drawer or remove the spans')

    # E. scenes clean — no DOM-building / drawer references inside scenes (call/usage-shaped
    #    patterns, so narration text that merely mentions a name doesn't false-positive)
    sm = re.search(r'const scenes\s*=\s*\[(.*?)\];\s*TOTAL', src, re.S)
    if not sm:
        errs.append('could not locate `const scenes = [ ... ]; TOTAL`')
    else:
        scenes_body = sm.group(1)
        for pat in (r'createElement\s*\(', r'appendChild\s*\(', r'\bopenTerm\s*\(',
                    r'\bcloseDrawer\s*\(', r'\bhopTerm\s*\(', r'\bGLOSSARY\s*[\[.]',
                    r'\bdrawerStack\b', r"getElementById\(\s*['\"]termDrawer"):
            if re.search(pat, scenes_body):
                errs.append(f'scene code matches /{pat}/ — DOM-building/drawer must stay out of scenes')

        # F2. every id a scene setter targets must resolve to an id="" in the assembled DOM
        #     (catches a typo'd id that would silently no-op). setRowClass/setBadge take a
        #     logical id that maps to row<ID>/badge<ID>; all other setters use the literal id.
        #     The first argument is a string, or an array literal of strings (setMsg takes
        #     both). A built id is not read correctly here: 'm' + n is read as the id "m"
        #     (and fails), a template string or a variable is not read at all. Do not build one.
        dom_ids = set(re.findall(r'\bid="([^"]+)"', src))
        prefix = {'setRowClass': 'row', 'setBadge': 'badge'}
        id_setters = r"(setNode|setEdge|setComp|setArrow|setLabel|setText|setRowClass|setBadge|setCell|setRule|setLife|setMsg|show|hide)"
        targets = re.findall(id_setters + r"""\s*\(\s*['"]([^'"]+)['"]""", scenes_body)
        for setter, arr in re.findall(id_setters + r"\s*\(\s*\[([^\]]*)\]", scenes_body):
            targets += [(setter, sid) for sid in re.findall(r"""['"]([^'"]+)['"]""", arr)]
        for setter, sid in targets:
            want = prefix.get(setter, '') + sid
            if want not in dom_ids:
                errs.append(f"scene {setter}('{sid}') targets id \"{want}\" with no matching id=\"\" in the DOM (silent no-op)")

        # F3. sequence setters: the state must be one the pack styles. A mistyped state, or a
        #     lifeline state given to a message, leaves it unlit with no error in the page.
        seq_states = {'setLife': {'', 'active', 'firing', 'locked', 'blocked', 'done', 'error', 'dimmed'},
                      'setMsg': {'', 'active', 'done', 'error', 'magic', 'dimmed'}}
        for setter, state in re.findall(r"""\b(setLife|setMsg)\s*\(\s*(?:\[[^\]]*\]|['"][^'"]*['"])\s*,\s*['"]([^'"]*)['"]""", scenes_body):
            if state not in seq_states[setter]:
                errs.append(f"scene {setter}(…, '{state}'): unknown state — use '' or one of "
                            + ', '.join(sorted(s for s in seq_states[setter] if s)))

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

    # G. JS syntax -- node --check the assembled <script> (skip if node absent).
    #    The other checks are regex-shaped and miss real syntax errors (e.g. an
    #    apostrophe inside a single-quoted GLOSSARY string), which ship a blank page.
    import shutil, subprocess, tempfile, os
    _node = shutil.which('node')
    _sj = re.search(r'<script>(.*)</script>', src, re.S)
    if _node and _sj:
        _tf = tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8')
        _tf.write(_sj.group(1)); _tf.close()
        _r = subprocess.run([_node, '--check', _tf.name], capture_output=True, text=True)
        os.unlink(_tf.name)
        if _r.returncode != 0:
            _tail = _r.stderr.strip().splitlines()
            errs.append('JS syntax error in <script> (node --check): ' + (_tail[-1] if _tail else 'see node'))

    # H. keyboard -- the engine's arrow-key listener is present (ADR 0356). A walkthrough
    #    assembled from an engine copy that predates it has no way to step from the keyboard.
    if (not re.search(r"addEventListener\(\s*['\"]keydown['\"]", src)
            or not re.search(r"\.key\s*===\s*'ArrowRight'", src)
            or not re.search(r"\.key\s*===\s*'ArrowLeft'", src)):
        errs.append('engine keydown listener for ArrowRight/ArrowLeft is missing — assembled from a stale engine?')

    # I. controls first -- the buttons come before the narration (ADR 0358)
    _pb, _nb = src.find('id="prevBtn"'), src.find('id="narration"')
    if _pb == -1 or _nb == -1 or _pb > _nb:
        errs.append('controls are not above the narration (id="prevBtn" must come before id="narration") — stale engine?')

    # J. UML kit composition (ADRs 0361, 0363, 0364)
    _style = ''.join(re.findall(r'<style>(.*?)</style>', src, re.S))
    kit_present = 'svg.uml' in _style
    _pics = re.findall(r'<svg\b[^>]*\bclass="uml"[^>]*>', src)
    if _pics and not kit_present:
        errs.append('uml picture present but the UML kit CSS is not assembled — pass --uml')
    if kit_present and not _pics:
        errs.append('UML kit assembled but no <svg class="uml"> picture uses it — drop --uml')
    for _tag in _pics:
        if not re.search(r'\bdata-uml="[\w-]+"', _tag):
            errs.append('a <svg class="uml"> picture has no data-uml="<type>" attribute')
    _caps = len(re.findall(r'class="uml-cap"', src))
    if _caps < len(_pics):
        errs.append(f'{len(_pics)} uml picture(s) but only {_caps} uml-cap caption(s) — every picture needs its caption')
    if len(_pics) > 3:
        errs.append(f'{len(_pics)} uml pictures — a walkthrough has at most 3 supporting diagrams')

    # K. sequence mode (ADR 0363): the legend exists and every message declares its kind
    if mm and mm.group(1) == 'sequence':
        if 'id="seqLegend"' not in src:
            errs.append('sequence mode: no id="seqLegend" legend')
        for _tag in re.findall(r'<g\b[^>]*\bclass="(?:[^"]*\s)?seq-msg(?:\s[^"]*)?"[^>]*>', src):
            if not re.search(r'\bdata-kind="(call|reply|self)"', _tag):
                _mid = re.search(r'\bid="([^"]+)"', _tag)
                errs.append('sequence mode: message ' + (_mid.group(1) if _mid else '(no id)')
                            + ' has no data-kind of call, reply or self')

    if errs:
        for e in errs:
            print('FAIL:', e)
        sys.exit(1)
    mode = mm.group(1) if mm else '?'
    drawer = 'with drawer' if 'id="termDrawer"' in src else 'no drawer'
    uml = ', uml kit' if kit_present else ''
    print(f'OK: {pathlib.Path(path).name} — mode={mode} ({drawer}{uml}); self-contained, RENDER_HOOKS-first, scenes clean, order ok')


if __name__ == '__main__':
    main(sys.argv[1])
