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
        assert "classList.toggle('off', document.hasFocus())" in page, "the hint is toggled with .off, never .hidden"
        assert 'class="key-hint off"' in page and ".key-hint.off { visibility: hidden; }" in page, \
            "the hint must keep its room, or the buttons jump under the first click (ADR 0381)"
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
    # a picture is never enlarged past its 540-unit design width (ADR 0382)
    assert re.search(r"svg\.uml\s*\{[^}]*max-width:\s*540px", css), "svg.uml needs max-width: 540px"
    assert all(v == "540" for v in re.findall(r'<svg class="uml"[^>]*viewBox="0 0 (\d+) ', kit))
    # the activity skeleton: two diamonds (decision, merge), and no action with two flows in (ADR 0383)
    act = kit[kit.index('data-uml="activity"'):]
    assert act.count('class="uml-dia"') == 2, "the branches must meet at a merge node"
    assert "nothing made," not in kit, "a branch is an action, not loose text"


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


# ---------------------------------------------------------------------------
# Task 5 — the sequence pack, gate K, and the scene-id pass for its setters
# ---------------------------------------------------------------------------

def sequence_demo(tmp, name="seq.html"):
    out, _ = assemble(tmp, "sequence", name, "--uml", KIT)
    return out


def test_sequence_demo_assembles_and_passes_the_checker():
    with tempfile.TemporaryDirectory() as tmp:
        code, text = check(sequence_demo(tmp))
        assert code == 0, text
        assert "mode=sequence" in text and "uml kit" in text, text


def test_sequence_pack_dashes_only_a_reply():
    css = css_section(pack("sequence"))
    assert re.search(r'\.seq-msg\[data-kind="reply"\]\s+\.seq-arrow\s*\{[^}]*stroke-dasharray', css), \
        "a reply must be dashed"
    # any rule that reaches an arrow and dashes it must be the reply rule
    for sel, body in re.findall(r"([^{}]*\.seq-arrow[^{}]*)\{([^}]*)\}", css):
        if "stroke-dasharray" in body:
            assert 'data-kind="reply"' in sel, "only a reply is dashed, not: " + sel.strip()


def test_sequence_pack_adds_no_new_hex_colour():
    known = set(h.lower() for h in re.findall(r"#[0-9a-fA-F]{3,8}\b", css_section(ENGINE) + css_section(pack("diagram"))))
    used = set(h.lower() for h in re.findall(r"#[0-9a-fA-F]{3,8}\b", css_section(pack("sequence"))))
    assert used <= known, "new hex colour(s) in the sequence pack: %s" % sorted(used - known)


def test_sequence_demo_follows_the_grid():
    html = read(pack("sequence"))
    xs = [int(x) for x in re.findall(r'<line class="seq-line" x1="(\d+)"', html)]
    n = len(xs)
    assert 2 <= n <= 5, "2 to 5 lifelines, found %d" % n
    assert xs == [round(1000 * (2 * i - 1) / (2 * n)) for i in range(1, n + 1)], xs
    width = min(180, 1000 / n - 20)
    heads = [(int(x), int(w)) for x, w in re.findall(r'<rect class="seq-head" x="(\d+)" y="12" width="(\d+)" height="70"', html)]
    assert heads == [(round(x - width / 2), round(width)) for x in xs], heads
    rows = [118 + 50 * k for k in range(12)]
    ys = [int(y) for y in re.findall(r'<path class="seq-arrow" d="M \d+ (\d+) ', html)]
    assert ys and all(y in rows for y in ys), "every message starts on a row: %s" % ys
    assert ys == sorted(ys), "messages are in row order"
    assert len(ys) <= 12, "12 messages or fewer"
    height = int(re.search(r'<svg class="seq" viewBox="0 0 1000 (\d+)"', html).group(1))
    assert height == max(ys) + 46, "H = last row + 46, got %d for last row %d" % (height, max(ys))
    ends = set(int(y) for y in re.findall(r'<line class="seq-line" [^>]*y2="(\d+)"', html))
    assert ends == {height - 14}, ends
    # a self-message: out 48, down 28, back; its label starts 16 clear of the loop (ADR 0384)
    for x, y, lx in re.findall(r'data-kind="self">\s*<path class="seq-arrow" d="M (\d+) (\d+) [^"]*"[^>]*/>\s*'
                               r'<g class="seq-label"><rect class="seq-label-bg" rx="5"/>\s*<text class="seq-label-text" x="(\d+)"', html):
        x0, y0 = int(x) - 4, int(y)
        assert x0 in xs, "a self-message starts 4 right of its lifeline"
        assert 'd="M %d %d L %d %d L %d %d L %d %d"' % (x0 + 4, y0, x0 + 52, y0, x0 + 52, y0 + 28, x0 + 10, y0 + 28) in html
        assert int(lx) == x0 + 68, "self label at x + 68, got %s" % lx
    assert html.count('data-kind="self">') == len(re.findall(r'data-kind="self">\s*<path class="seq-arrow" d="M \d+ \d+ [^"]*"[^>]*/>\s*<g class="seq-label"><rect class="seq-label-bg" rx="5"/>\s*<text class="seq-label-text" x="\d+"', html)) >= 1, \
        "every self-message must have the shape the check above reads"
    # the frame: header row h, box from yH - 26, height (yLast - yH) + 44
    box = re.search(r'<rect class="seq-frag-box" x="18" y="(\d+)" width="964" height="(\d+)"', html)
    y_box, h_box = int(box.group(1)), int(box.group(2))
    y_header = y_box + 26
    assert y_header in rows and y_header not in ys, "the frame header takes a row with no message"
    inside = [y for y in ys if y_header < y < y_box + h_box]
    assert h_box == (max(inside) - y_header) + 44, (h_box, inside)


def test_sequence_demo_exercises_what_the_pack_offers():
    html = read(pack("sequence"))
    for kind in ("call", "reply", "self"):
        assert 'data-kind="%s"' % kind in html, "the demo has no %s message" % kind
    assert 'class="seq-frag" data-op="opt"' in html
    assert 'data-default="' in html and 'id="seqLegend"' in html
    assert 'data-uml="class"' in html and 'data-uml="activity"' in html
    assert "class=\"wt-panel question hidden\"" in html
    assert "setMsg('m6', 'error')" in html, "the demo shows an error message"
    # no width typed on a label background, no id list typed in the registry
    assert not re.search(r'<rect class="seq-label-bg"[^>]*\bwidth=', html)
    assert "registry: { LIFELINES: [], MESSAGES: [] }" in html


def test_gate_k_fails_without_the_legend():
    with tempfile.TemporaryDirectory() as tmp:
        bad = broken(tmp, sequence_demo(tmp), "no-legend.html", 'id="seqLegend"', 'id="legendX"')
        code, text = check(bad)
        assert code == 1 and "sequence mode" in text and "seqLegend" in text, text


def test_gate_k_fails_on_a_message_without_a_kind():
    with tempfile.TemporaryDirectory() as tmp:
        bad = broken(tmp, sequence_demo(tmp), "no-kind.html", '<g class="seq-msg" id="m1" data-kind="call">', '<g class="seq-msg" id="m1">')
        code, text = check(bad)
        assert code == 1 and "sequence mode" in text and "m1" in text and "data-kind" in text, text


def test_gate_k_sees_a_message_that_carries_a_state_class():
    with tempfile.TemporaryDirectory() as tmp:
        bad = broken(tmp, sequence_demo(tmp), "state-no-kind.html", '<g class="seq-msg" id="m2" data-kind="call">', '<g class="seq-msg done" id="m2">')
        code, text = check(bad)
        assert code == 1 and "m2" in text and "data-kind" in text, text


def test_gate_k_fails_on_an_unknown_kind():
    with tempfile.TemporaryDirectory() as tmp:
        bad = broken(tmp, sequence_demo(tmp), "bad-kind.html", 'id="m3" data-kind="reply"', 'id="m3" data-kind="return"')
        code, text = check(bad)
        assert code == 1 and "m3" in text and "data-kind" in text, text


def test_scene_pass_catches_an_unknown_state_name():
    with tempfile.TemporaryDirectory() as tmp:
        # 'firing' is a lifeline state; on a message it would leave the arrow unlit
        bad = broken(tmp, sequence_demo(tmp), "bad-state.html", "setMsg('m1', 'active')", "setMsg('m1', 'firing')")
        code, text = check(bad)
        assert code == 1 and "unknown state" in text and "firing" in text, text
        bad = broken(tmp, sequence_demo(tmp), "bad-state-2.html", "setLife('lfUser', 'locked')", "setLife('lfUser', 'lokced')")
        code, text = check(bad)
        assert code == 1 and "lokced" in text, text


def test_sequence_setters_take_one_id_or_an_array():
    html = read(pack("sequence"))
    assert html.count("[].concat(ids).forEach") == 2, "setLife and setMsg both loop over [].concat(ids)"
    # the two kit pictures in the demo are the kit's own skeletons, mark for mark
    kit = read(KIT)
    for kind in ("class", "activity"):
        def marks(text):
            body = text[text.index('data-uml="%s"' % kind):]
            body = body[:body.index("</svg>")]
            return [l.strip() for l in body.splitlines()[1:] if l.strip() and not l.strip().startswith("<!--")]
        assert marks(html) == marks(kit), "the demo's %s picture has drifted from the kit skeleton" % kind


def test_scene_id_pass_catches_a_mistyped_message_id():
    with tempfile.TemporaryDirectory() as tmp:
        bad = broken(tmp, sequence_demo(tmp), "typo-msg.html", "setMsg('m1', 'active')", "setMsg('mTypo', 'active')")
        code, text = check(bad)
        assert code == 1 and "mTypo" in text, text


def test_scene_id_pass_catches_a_mistyped_id_inside_an_array():
    with tempfile.TemporaryDirectory() as tmp:
        bad = broken(tmp, sequence_demo(tmp), "typo-array.html", "setMsg(['m1', 'm2'], 'done')", "setMsg(['m1', 'mTypo'], 'done')")
        code, text = check(bad)
        assert code == 1 and "mTypo" in text, text


def test_scene_id_pass_catches_a_mistyped_lifeline_id():
    with tempfile.TemporaryDirectory() as tmp:
        bad = broken(tmp, sequence_demo(tmp), "typo-life.html", "setLife('lfUser', 'firing')", "setLife('lfTypo', 'firing')")
        code, text = check(bad)
        assert code == 1 and "lfTypo" in text, text


# ---------------------------------------------------------------------------
# Task 6 — SKILL.md says what the references now do
# ---------------------------------------------------------------------------

def flat(path):
    """The file's text with every run of whitespace collapsed, so a rewrap cannot break a test."""
    return " ".join(read(path).split())


def test_skill_md_teaches_the_sequence_mode_and_the_new_tie_break():
    s = flat(os.path.join(SKILL, "SKILL.md"))
    assert "`references/mode-sequence.html`" in s
    assert "**when in doubt → sequence**" in s
    assert "when in doubt → diagram" not in s, "the old tie-break is still in SKILL.md"
    assert "a future **timeline**" not in s
    assert "12 messages or fewer" in s
    assert "`setLife`/`setMsg`/`setText`" in s
    assert "Standard skeleton (sequence mode)" in s


def test_skill_md_teaches_supporting_diagrams_and_the_uml_rules():
    s = flat(os.path.join(SKILL, "SKILL.md"))
    assert "`references/uml-kit.html`" in s and "--uml references/uml-kit.html" in s
    assert "**At most 3**" in s and "**None is a correct number**" in s
    assert "dashed arrow = a reply" in s and "**never dashes**" in s
    assert "`#seqLegend`" in s and "`.uml-cap`" in s
    assert "Add no CSS of your own" in s
    assert "Never build an id (" in s
    assert "meet at a **merge**" in s and "540 units wide" in s
    assert "UML state machine" not in s, "no pack is called UML without a rule set and a legend (ADR 0386)"


def test_skill_md_names_the_keys_and_keeps_its_frontmatter():
    text = read(os.path.join(SKILL, "SKILL.md"))
    s = " ".join(text.split())
    assert "the `→` / `←` keys" in s and "step dot" in s
    lines = text.splitlines()
    assert lines[0] == "---" and lines[1] == "name: problem-description", lines[:2]
    assert lines[2].startswith("description: Use when the user wants an interactive step-by-step HTML walkthrough")
    assert lines[3] == "effort: max" and lines[4] == "---", lines[3:5]
    assert "${CLAUDE_PLUGIN_ROOT}" not in text, "SKILL.md refers to its own files with skill-relative paths"


# ---------------------------------------------------------------------------
# Task 7 — the plugin README
# ---------------------------------------------------------------------------

def test_plugin_readme_lists_four_modes_the_kit_and_the_keys():
    r = flat(os.path.normpath(os.path.join(HERE, "..", "README.md")))
    assert "- **sequence**: a UML sequence diagram" in r
    assert "**diagram** (default)" not in r, "diagram is no longer the default"
    assert "A tie between sequence and diagram goes to sequence." in r
    assert "`references/uml-kit.html`" in r
    assert "the `→` / `←` keys" in r


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
