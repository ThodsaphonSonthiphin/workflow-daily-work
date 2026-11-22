#!/usr/bin/env python3
"""Tests for the problem-description walkthrough scripts
(skills/problem-description/scripts/assemble-walkthrough.py and check-walkthrough.py)
and for the references they assemble. Run: python test_walkthrough_scripts.py

The two scripts have hyphenated names and are run by path, so every test calls them
as a subprocess and works in a temporary directory.
"""
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.normpath(os.path.join(HERE, "..", "skills", "problem-description"))
REF = os.path.join(SKILL, "references")
SCR = os.path.join(SKILL, "scripts")
ENGINE = os.path.join(REF, "walkthrough-engine.html")
DRAWER = os.path.join(REF, "term-drilldown.html")
KIT = os.path.join(REF, "uml-kit.html")


def pack(mode):
    return os.path.join(REF, "mode-%s.html" % mode)


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


def run(script, *args):
    """Run one of the two scripts. Returns (exit code, stdout + stderr)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    r = subprocess.run([sys.executable, os.path.join(SCR, script)] + list(args),
                       capture_output=True, text=True, encoding="utf-8", env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def assemble(tmp, mode, name, *extra):
    """Assemble mode's pack into tmp/name. extra = more assembler arguments.
    Uses the pack's own demo unless extra names a bootstrap file."""
    out = os.path.join(tmp, name)
    args = ["--engine", ENGINE, "--mode", pack(mode), "--title", "test " + mode, "--out", out]
    if "--bootstrap" not in extra:
        args.append("--demo")
    code, text = run("assemble-walkthrough.py", *(args + list(extra)))
    assert code == 0, "assemble failed for %s: %s" % (mode, text)
    return out, text


def check(path):
    return run("check-walkthrough.py", path)


def broken(tmp, src_path, name, old, new, count=1):
    """Copy src_path to tmp/name with `old` replaced by `new`. `old` must be present."""
    text = read(src_path)
    assert old in text, "the text to break is not in the file: %r" % old
    return write(os.path.join(tmp, name), text.replace(old, new, count))


def css_section(path):
    m = re.search(r"/\*\s*=====\s*§CSS\b[^\n]*?\*/(.*?)/\*\s*=====\s*end\s*§CSS", read(path), re.S)
    assert m, "no §CSS section in " + path
    return m.group(1)


# ---------------------------------------------------------------------------
# Task 1 — the assembler: the existing packs, the viewport meta, the uml option
# ---------------------------------------------------------------------------

def test_existing_pack_demos_assemble_and_pass_the_checker():
    with tempfile.TemporaryDirectory() as tmp:
        for mode in ("diagram", "tables", "state-machine"):
            out, _ = assemble(tmp, mode, "demo-%s.html" % mode)
            code, text = check(out)
            assert code == 0, "%s demo failed the checker: %s" % (mode, text)
            assert "OK:" in text and "mode=%s" % mode in text, text


def test_assembled_page_has_a_viewport_meta():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "demo.html")
        assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in read(out)


def test_uml_option_inlines_only_the_kit_css():
    with tempfile.TemporaryDirectory() as tmp:
        kit = write(os.path.join(tmp, "kit.html"),
                    "<style>\n/* ===== §CSS  (test kit) ===== */\n"
                    "svg.uml { display: block; }\n/* ===== end §CSS ===== */\n</style>\n"
                    "<body><p id=\"kitBodyMarker\">skeleton</p></body>\n")
        out, said = assemble(tmp, "diagram", "demo.html", "--uml", kit)
        page = read(out)
        assert "svg.uml { display: block; }" in page, "the kit CSS was not inlined"
        assert "kitBodyMarker" not in page, "the kit body must not be inlined"
        assert "+ uml kit" in said, said


# ---------------------------------------------------------------------------
# Task 2 — the engine: keys, dots, controls above the narration; gates H and I
# ---------------------------------------------------------------------------

def test_engine_steps_on_the_arrow_keys_and_the_dots():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "demo.html")
        page = read(out)
        assert "function go(step)" in page
        assert "addEventListener('keydown'" in page
        assert "e.key === 'ArrowRight'" in page and "e.key === 'ArrowLeft'" in page
        assert "e.altKey || e.ctrlKey || e.metaKey || e.shiftKey" in page, "modifier keys must be left alone"
        assert "d.dataset.step = i" in page, "a step dot must carry its step number"
        assert "window.focus()" not in page.split("<script>")[1].replace("Never call window.focus()", ""), \
            "the engine must never take focus"


def test_engine_shows_a_focus_hint_and_controls_come_first():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "demo.html")
        page = read(out)
        assert 'id="keyHint"' in page and "document.hasFocus()" in page
        assert page.index('id="stepProgress"') < page.index('id="prevBtn"') < page.index('id="narration"'), \
            "order must be: step dots, controls, narration"
        assert "color-scheme: dark" in page


def test_engine_styles_a_table_and_a_note_inside_a_panel():
    css = css_section(ENGINE)
    assert ".wt-panel table" in css and ".wt-panel .tbl-wrap" in css and ".wt-note" in css


def test_gate_h_fails_without_the_arrow_key_listener():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "demo.html")
        bad = broken(tmp, out, "no-keys.html", "e.key === 'ArrowRight'", "e.key === 'x'")
        code, text = check(bad)
        assert code == 1 and "keydown" in text, text


def test_gate_i_fails_when_the_controls_follow_the_narration():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "demo.html")
        page = read(out)
        m = re.search(r'<div class="controls">.*?</div>\s*', page, re.S)
        assert m, "controls block not found"
        moved = page.replace(m.group(0), "", 1).replace("<!-- ===== MODE CONTENT", m.group(0) + "<!-- ===== MODE CONTENT", 1)
        bad = write(os.path.join(tmp, "controls-last.html"), moved)
        code, text = check(bad)
        assert code == 1 and "controls" in text, text


# ---------------------------------------------------------------------------
# Task 3 — the drawer: Esc closes it
# ---------------------------------------------------------------------------

DRAWER_BOOTSTRAP = """MODE = 'diagram';
const { setComp, setArrow, setLabel, setText } = modeRenderers[MODE];
const GLOSSARY = {
  'demo-key': { term: 'demo key', short: 'the lookup key the demo DB stores its value under.', seeAlso: [], source: 'authored' },
};
const scenes = [
  () => { setNarration('', 'Overview', 'The DB keeps one value under a <span class="term" data-term="demo-key">demo key</span>.'); },
  () => { setNarration('', 'Step 1', 'The client asks.'); setComp('compClient', 'firing'); setArrow('arrCS', 'active'); setLabel('lblCS', true); },
];
TOTAL = scenes.length - 1;
modeRenderers[MODE].assertRegistryComplete();
buildProgressDots();
render(0);
"""


def test_drawer_walkthrough_passes_and_closes_on_escape():
    with tempfile.TemporaryDirectory() as tmp:
        boot = write(os.path.join(tmp, "boot.js"), DRAWER_BOOTSTRAP)
        out, _ = assemble(tmp, "diagram", "with-drawer.html", "--drawer", DRAWER, "--bootstrap", boot)
        code, text = check(out)
        assert code == 0, text
        assert "with drawer" in text, text
        page = read(out)
        assert "e.key === 'Escape'" in page, "the drawer must close on Esc"
        assert page.count("addEventListener('keydown'") == 2, "one listener in the engine, one in the drawer"


# ---------------------------------------------------------------------------
# Task 4 — the UML kit and gate J
# ---------------------------------------------------------------------------

def panel(n, with_type=True, with_caption=True):
    """One supporting-diagram panel, for breaking gate J in controlled ways."""
    return ('<div class="wt-panel hidden" id="pnlT%d"><svg class="uml"%s viewBox="0 0 10 10"></svg>%s</div>\n'
            % (n, ' data-uml="class"' if with_type else "",
               '<div class="uml-cap">Answers: a test question.</div>' if with_caption else ""))


def with_panels(tmp, src_path, name, html):
    return broken(tmp, src_path, name, '<div class="narration" id="narration">',
                  html + '<div class="narration" id="narration">')


def test_uml_kit_has_a_css_section_and_two_captioned_skeletons():
    kit = read(KIT)
    css = css_section(KIT)
    assert "svg.uml" in css
    for cls in (".uml-box", ".uml-t", ".uml-line", ".uml-dep", ".uml-flow", ".uml-start",
                ".uml-end", ".uml-end-ring", ".uml-dia", ".uml-act", ".uml-cap"):
        assert cls in css, "kit CSS lacks " + cls
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b", css), "kit CSS must use :root tokens only, no hex colour"
    assert 'data-uml="class"' in kit and 'data-uml="activity"' in kit
    assert kit.count('<svg class="uml"') == 2 and kit.count('class="uml-cap"') == 2
    # every flow out of the decision is a drawn arrow with its guard
    assert "[yes]" in kit and "[no]" in kit


def test_gate_j_fails_on_a_picture_without_the_kit():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "demo.html")
        bad = with_panels(tmp, out, "pic-no-kit.html", panel(1))
        code, text = check(bad)
        assert code == 1 and "pass --uml" in text, text


def test_gate_j_fails_on_the_kit_without_a_picture():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "kit-no-pic.html", "--uml", KIT)
        code, text = check(out)
        assert code == 1 and "drop --uml" in text, text


def test_gate_j_passes_with_the_kit_and_a_captioned_typed_picture():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "demo.html", "--uml", KIT)
        good = with_panels(tmp, out, "kit-and-pic.html", panel(1))
        code, text = check(good)
        assert code == 0, text
        assert "uml kit" in text, text


def test_gate_j_fails_on_a_picture_without_a_type():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "demo.html", "--uml", KIT)
        bad = with_panels(tmp, out, "no-type.html", panel(1, with_type=False))
        code, text = check(bad)
        assert code == 1 and "data-uml" in text, text


def test_gate_j_fails_on_a_picture_without_a_caption():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "demo.html", "--uml", KIT)
        bad = with_panels(tmp, out, "no-caption.html", panel(1, with_caption=False))
        code, text = check(bad)
        assert code == 1 and "caption" in text, text


def test_gate_j_fails_on_more_than_three_pictures():
    with tempfile.TemporaryDirectory() as tmp:
        out, _ = assemble(tmp, "diagram", "demo.html", "--uml", KIT)
        bad = with_panels(tmp, out, "four-pics.html", panel(1) + panel(2) + panel(3) + panel(4))
        code, text = check(bad)
        assert code == 1 and "at most 3" in text, text


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except Exception as e:  # an AssertionError, or a file that does not exist yet
            failed += 1
            print(f"FAIL  {t.__name__}: {type(e).__name__}: {e}")
    print(f"{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(1 if failed else 0)
