# er-diagram Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `er-diagram` skill to the `dev-workflows` plugin: the agent writes one ER model (JSON), and a bundled Python script checks it, lays it out, draws a tiered ER page in the look of the hand-drawn page, embeds the model in the page, and takes the model back out of a published page for an update.

**Architecture:** `scripts/er_diagram.py` is the one entry (`build`, `extract`). It uses a small standard-library package `scripts/erlib/`: `model` (fixed lists, load), `check` (errors and TBD warnings), `measure` (estimated text widths), `layout` (every position from the model's order), `svg` (drawing and the PNG check copy), `page` (template, sections, legend, embedded model). `scripts/render_png.js` turns the check SVG into a PNG with `@resvg/resvg-js`. The page template, the made-up Bookshop example, the model contract and the tests sit beside them in the skill folder.

**Tech Stack:** Python 3.11+ standard library only (`json`, `html`, `re`, `dataclasses`, `unicodedata`, `unittest`); Node 18+ with `@resvg/resvg-js@2.6.2` (optional, for the PNG); Mermaid 10.9.1 from cdnjs in the page.

**Spec:** `docs/superpowers/specs/2026-11-27-er-diagram-design.md` (ADRs `workflow-daily-work-0398` to `0409`). Read it before Task 1.

## Global Constraints

- Python: standard library only; no PyYAML, no third-party package (spec section 4).
- Every file committed for this skill holds **no client schema, client names or client ticket numbers**; the only example is the made-up "Bookshop order sync" (ADR 0409). Before each commit, look at the staged diff for client data.
- Script paths in `SKILL.md` are skill-relative (`scripts/er_diagram.py`), never `${CLAUDE_PLUGIN_ROOT}/skills/...` (repo CLAUDE.md).
- Skills stay harness-neutral: name actions, not one harness's tools (repo CLAUDE.md).
- Fixed lists (ADRs 0402, 0403): box kinds `table`, `endpoint`; line kinds `fk`, `same-value`, `flow`; highlight and note kinds `problem`, `change`; column keys `PK`, `FK`, `AK`, `IX`, `UQ`; multiplicities `1`, `0..1`, `*`, `1..*`; page languages `th`, `en`.
- Sizes of the hand-drawn page: table header 48, row 20, bottom 6, footnote 18; endpoint height 80; first box y 70; gap between boxes 18.
- The model block in the page: `<script type="application/json" id="er-model">`, with every `<` written as `\u003c`.
- Colours (light / dark): `--bad` `#a8492a` / `#e58a65`, `--good` `#2d7a4c` / `#72c595`; all tokens are copied in Task 7.
- PNG renderer: `@resvg/resvg-js@2.6.2`; never a headless browser (it hangs on Pon's PC).
- Commits: **only after Pon says to commit** (ask once before Task 1; with a no, do every step except `git commit`). Never add a `Co-Authored-By` or any other Claude attribution line. Conventional subjects, as the repo uses (`feat(er-diagram): ...`).
- Do not touch the files that are not this work: `daily-state.md`, `plugins/dev-workflows/skills/guide-and-verify/SKILL.md`, `docs/adr/workflow-daily-work-0290-*`, `docs/adr/workflow-daily-work-0291-*`, `docs/reflections/2026-11.md`. `git status` also shows most files under `skills/` as modified: that is line-ending noise (`core.autocrlf true`; `git diff` shows nothing). Never stage a path you did not change.
- Run every Python command from the repo root `C:\Repo\workflow-daily-work`. The test command is `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`.

## File structure

| File | Responsibility |
|---|---|
| `plugins/dev-workflows/skills/er-diagram/SKILL.md` | the run the agent follows (Task 11) |
| `.../er-diagram/references/er-model.md` | the ER model contract, the only place its schema is defined (Task 11) |
| `.../er-diagram/scripts/er_diagram.py` | CLI entry: `build`, `extract` (Task 9) |
| `.../er-diagram/scripts/erlib/__init__.py` | package marker (Task 2) |
| `.../er-diagram/scripts/erlib/model.py` | fixed lists, load, dump, box walk (Task 2) |
| `.../er-diagram/scripts/erlib/check.py` | `check(model) -> (errors, warnings)` (Task 2) |
| `.../er-diagram/scripts/erlib/measure.py` | `text_width(text, size, mono=False)` (Task 3) |
| `.../er-diagram/scripts/erlib/layout.py` | `layout(model) -> Layout` (Tasks 3-5) |
| `.../er-diagram/scripts/erlib/svg.py` | `draw_svg`, `check_svg`, `SVG_CSS`, `LIGHT` (Task 6) |
| `.../er-diagram/scripts/erlib/page.py` | `inline`, `legend`, `build_page`, `embed_model`, `extract_model` (Task 7) |
| `.../er-diagram/scripts/render_png.js` | SVG to PNG (Task 10) |
| `.../er-diagram/assets/er-page-template.html` | the page shell (Task 7) |
| `.../er-diagram/assets/example-bookshop.er.json` | the made-up example and test input (Task 8) |
| `.../er-diagram/tests/helpers.py` | shared test data (Task 2) |
| `.../er-diagram/tests/test_*.py` | unit and CLI tests (Tasks 2-9) |
| `plugins/dev-workflows/commands/er-diagram.md` | thin command wrapper (Task 11) |
| `plugins/dev-workflows/skills/problem-description/SKILL.md`, `.../sa-doc/SKILL.md` | one "not for" clause each (Task 12) |
| `PLAYBOOK.md`, both manifests, `skills/` tree | registration (Task 12) |

`...` below means `plugins/dev-workflows/skills`.

---

### Task 1: Branch and design commit

**Files:**
- Commit only: `CONTEXT.md`, `docs/adr/workflow-daily-work-0398-*.md` ... `docs/adr/workflow-daily-work-0409-*.md`, `docs/superpowers/specs/2026-11-27-er-diagram-design.md`, `docs/superpowers/plans/2026-11-27-er-diagram.md`

**Interfaces:**
- Consumes: nothing.
- Produces: branch `er-diagram-skill` that holds the design.

- [ ] **Step 1: Ask Pon for the go to commit** (once, for the whole plan). Record the answer; with a no, skip every `git commit` step below.

- [ ] **Step 2: Check that `CONTEXT.md` holds only the ER diagram hunk**

Run: `git diff --stat -- CONTEXT.md` and `git diff -- CONTEXT.md`
Expected: one added section "## ER diagram skill terms (dev-workflows plugin)" with the term **ER model** and nothing else. If other hunks show, stop and ask Pon.

- [ ] **Step 3: Create the branch from `main`**

Run: `git switch -c er-diagram-skill`
Expected: `Switched to a new branch 'er-diagram-skill'` (the uncommitted files come along; nothing is staged).

- [ ] **Step 4: Stage the design files only**

```bash
git add CONTEXT.md docs/superpowers/specs/2026-11-27-er-diagram-design.md docs/superpowers/plans/2026-11-27-er-diagram.md
git add docs/adr/workflow-daily-work-0398-*.md docs/adr/workflow-daily-work-0399-*.md docs/adr/workflow-daily-work-040*.md
git diff --cached --stat
```
Expected: 15 files (CONTEXT.md, 12 ADRs 0398-0409, the spec, this plan). No `0290`, `0291`, `daily-state.md`, `guide-and-verify`, `reflections`.

- [ ] **Step 5: Commit**

```bash
git commit -m "docs(er-diagram): design of the tiered ER page skill: ADRs 0398-0409, spec, plan, ER model term"
```

---

### Task 2: Model lists and the check

**Files:**
- Create: `.../er-diagram/scripts/erlib/__init__.py`
- Create: `.../er-diagram/scripts/erlib/model.py`
- Create: `.../er-diagram/scripts/erlib/check.py`
- Create: `.../er-diagram/tests/helpers.py`
- Test: `.../er-diagram/tests/test_check.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `erlib.model`: `BOX_KINDS`, `LINE_KINDS`, `HIGHLIGHT_KINDS`, `NOTE_KINDS`, `COLUMN_KEYS`, `MULTS`, `LANGS`, `TBD`, `load(path) -> dict`, `dump(model, path)`, `boxes(model) -> iterator of (tier_index, box_dict)`, `is_tbd(value) -> bool`. `erlib.check.check(model) -> (list[str] errors, list[str] warnings)`. Error texts used later: `"line r1→c1: no multiplicity at end c1"`; warning texts `"<box>: <field> TBD"`, `"<box>.<column>: <field> TBD"`, `"line a→b: <field> TBD"`. `tests/helpers.py`: `SKILL`, `EXAMPLE`, `col()`, `table()`, `small_model()`, `example()`, `box(model, id)`.

- [ ] **Step 1: Write the package marker and the test helpers**

`.../er-diagram/scripts/erlib/__init__.py`:
```python
"""er-diagram library: model, check, measure, layout, svg, page (ADRs 0398-0409)."""
```

`.../er-diagram/tests/helpers.py`:
```python
"""Shared test data for the er-diagram tests. Importing it puts scripts/ on sys.path."""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(SKILL, "scripts"))
EXAMPLE = os.path.join(SKILL, "assets", "example-bookshop.er.json")


def col(name, type_="text", key=None, short=None):
    c = {"name": name, "type": type_, "short": short or name.lower()}
    if key:
        c["key"] = key
    return c


def table(id_, *cols, **extra):
    t = {"kind": "table", "id": id_, "rowMeaning": f"1 row = 1 {id_}",
         "purpose": f"{id_} purpose", "columns": list(cols)}
    t.update(extra)
    return t


def small_model():
    """Three tiers: one endpoint, two raw tables, two current tables; a flow, two same-value
    lines into one row, and two fk lines to one column (a bus)."""
    return {
        "erModel": 1,
        "page": {"title": "Small Test", "heading": "Small", "lang": "en"},
        "tiers": [
            {"id": "api", "title": "API",
             "boxes": [{"kind": "endpoint", "id": "E1", "lines": ["one", "two"]}]},
            {"id": "raw", "title": "Raw", "boxes": [
                table("r1", col("RawId", "bigint", "PK"), col("Run", "bigint", "FK"), col("K")),
                table("r2", col("RawId", "bigint", "PK"), col("Run", "bigint", "FK"), col("K"))]},
            {"id": "cur", "title": "Current", "boxes": [
                table("c1", col("K", key="PK"), col("Name")),
                table("run", col("Id", "bigint", "PK"))]},
        ],
        "lines": [
            {"kind": "flow", "from": {"box": "E1"}, "to": {"box": "r1"},
             "label": "Land", "tooltip": "E1 lands in r1", "mult": ["1", "*"]},
            {"kind": "same-value", "from": {"box": "r1", "column": "K"}, "to": {"box": "c1", "column": "K"},
             "label": "K = K", "tooltip": "r1 to c1", "mult": ["*", "1"]},
            {"kind": "same-value", "from": {"box": "r2", "column": "K"}, "to": {"box": "c1", "column": "K"},
             "label": "K = K (2)", "tooltip": "r2 to c1", "mult": ["*", "0..1"]},
            {"kind": "fk", "from": {"box": "r1", "column": "Run"}, "to": {"box": "run", "column": "Id"},
             "label": "FK: Run = Id", "tooltip": "r1 to run", "mult": ["*", "1"]},
            {"kind": "fk", "from": {"box": "r2", "column": "Run"}, "to": {"box": "run", "column": "Id"},
             "label": "FK: Run = Id", "tooltip": "r2 to run", "mult": ["*", "1"]},
        ],
    }


def example():
    with open(EXAMPLE, encoding="utf-8") as f:
        return json.load(f)


def box(model, id_):
    for tier in model["tiers"]:
        for b in tier["boxes"]:
            if b["id"] == id_:
                return b
    raise KeyError(id_)
```

- [ ] **Step 2: Write the failing tests**

`.../er-diagram/tests/test_check.py`:
```python
"""Tests for erlib.check (ADR 0405; spec section 7)."""
import unittest

from helpers import box, small_model
from erlib.check import check


class CheckTest(unittest.TestCase):
    def errors(self, model):
        return check(model)[0]

    def test_valid_model_has_no_errors_and_no_warnings(self):
        self.assertEqual(check(small_model()), ([], []))

    def test_unknown_box_kind(self):
        m = small_model()
        box(m, "r1")["kind"] = "view"
        self.assertIn("box r1: unknown kind 'view'", self.errors(m))

    def test_unknown_line_kind(self):
        m = small_model()
        m["lines"][1]["kind"] = "join"
        self.assertIn("line r1→c1: unknown kind 'join'", self.errors(m))

    def test_box_id_used_twice(self):
        m = small_model()
        box(m, "r2")["id"] = "r1"
        self.assertIn("box r1: id used twice", self.errors(m))

    def test_line_end_names_no_box(self):
        m = small_model()
        m["lines"][1]["to"]["box"] = "cx"
        self.assertIn("line r1→cx: end to names no box 'cx'", self.errors(m))

    def test_line_end_names_a_missing_column(self):
        m = small_model()
        m["lines"][1]["to"]["column"] = "Nope"
        self.assertIn("line r1→c1: column c1.Nope is not in the model", self.errors(m))

    def test_same_value_line_on_an_endpoint(self):
        m = small_model()
        m["lines"][0]["kind"] = "same-value"
        self.assertIn("line E1→r1: a same-value line must join two tables; E1 is an endpoint", self.errors(m))

    def test_fk_end_without_a_column(self):
        m = small_model()
        del m["lines"][3]["from"]["column"]
        self.assertIn("line r1→run: end from has no column", self.errors(m))

    def test_table_without_row_meaning(self):
        m = small_model()
        box(m, "c1")["rowMeaning"] = ""
        self.assertIn("table c1: no rowMeaning", self.errors(m))

    def test_table_without_purpose(self):
        m = small_model()
        del box(m, "c1")["purpose"]
        self.assertIn("table c1: no purpose", self.errors(m))

    def test_line_without_label(self):
        m = small_model()
        m["lines"][1]["label"] = " "
        self.assertIn("line r1→c1: no label", self.errors(m))

    def test_line_without_tooltip(self):
        m = small_model()
        del m["lines"][1]["tooltip"]
        self.assertIn("line r1→c1: no tooltip", self.errors(m))

    def test_no_multiplicity_at_one_end(self):
        m = small_model()
        m["lines"][1]["mult"] = ["*", ""]
        self.assertIn("line r1→c1: no multiplicity at end c1", self.errors(m))

    def test_unknown_multiplicity(self):
        m = small_model()
        m["lines"][1]["mult"] = ["*", "many"]
        self.assertIn("line r1→c1: unknown multiplicity 'many'", self.errors(m))

    def test_highlight_without_a_note(self):
        m = small_model()
        box(m, "c1")["highlight"] = {"kind": "change"}
        self.assertIn("box c1: highlight without a note", self.errors(m))

    def test_unknown_highlight_kind(self):
        m = small_model()
        m["lines"][1]["highlight"] = {"kind": "warning", "note": "x"}
        self.assertIn("line r1→c1: unknown highlight kind 'warning'", self.errors(m))

    def test_unknown_column_key(self):
        m = small_model()
        box(m, "c1")["columns"][1]["key"] = "XX"
        self.assertIn("column c1.Name: unknown key 'XX'", self.errors(m))

    def test_page_without_title(self):
        m = small_model()
        del m["page"]["title"]
        self.assertIn("page: no title", self.errors(m))

    def test_unknown_note_kind(self):
        m = small_model()
        m["notes"] = [{"kind": "info", "heading": "h", "paragraphs": ["p"]}]
        self.assertIn("note h: unknown kind 'info'", self.errors(m))

    def test_tbd_is_a_warning_not_an_error(self):
        m = small_model()
        box(m, "c1")["purpose"] = "TBD"
        box(m, "c1")["columns"][1]["desc"] = "TBD"
        self.assertEqual(check(m), ([], ["c1: purpose TBD", "c1.Name: desc TBD"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: Run the tests to see them fail**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'erlib.check'`.

- [ ] **Step 4: Write `model.py`**

`.../er-diagram/scripts/erlib/model.py`:
```python
"""ER model: the fixed lists and loading (ADRs 0402, 0403; spec section 4)."""
import json

BOX_KINDS = ("table", "endpoint")
LINE_KINDS = ("fk", "same-value", "flow")
HIGHLIGHT_KINDS = ("problem", "change")
NOTE_KINDS = HIGHLIGHT_KINDS
COLUMN_KEYS = ("PK", "FK", "AK", "IX", "UQ")
MULTS = ("1", "0..1", "*", "1..*")
LANGS = ("th", "en")
TBD = "TBD"


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def dump(model, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(model, f, ensure_ascii=False, indent=2)
        f.write("\n")


def boxes(model):
    """Yield (tier_index, box) in model order."""
    for ti, tier in enumerate(model.get("tiers", [])):
        for box in tier.get("boxes", []):
            yield ti, box


def is_tbd(value):
    return isinstance(value, str) and value.strip().upper() == TBD
```

- [ ] **Step 5: Write `check.py`**

`.../er-diagram/scripts/erlib/check.py`:
```python
"""Check an ER model before it is drawn (ADR 0405; spec section 7).

check(model) -> (errors, warnings). An error stops the page; a warning names a TBD value.
"""
from .model import (BOX_KINDS, COLUMN_KEYS, HIGHLIGHT_KINDS, LANGS, LINE_KINDS,
                    MULTS, NOTE_KINDS, is_tbd)


def _missing(value):
    if value is None:
        return True
    if isinstance(value, str):
        return value.strip() == ""
    if isinstance(value, (list, dict)):
        return len(value) == 0
    return False


def _line_name(line):
    a = (line.get("from") or {}).get("box", "?")
    b = (line.get("to") or {}).get("box", "?")
    return f"line {a}→{b}"


def _highlight(errors, item, hl):
    if hl is None:
        return
    kind = hl.get("kind") if isinstance(hl, dict) else hl
    if kind not in HIGHLIGHT_KINDS:
        errors.append(f"{item}: unknown highlight kind {kind!r}")
        return
    if _missing(hl.get("note")):
        errors.append(f"{item}: highlight without a note")


def _required(errors, warnings, item, warn_name, obj, fields):
    for f in fields:
        value = obj.get(f)
        if _missing(value):
            errors.append(f"{item}: no {f}")
        elif is_tbd(value):
            warnings.append(f"{warn_name}: {f} TBD")


def _check_page(model, errors, warnings):
    page = model.get("page")
    if not isinstance(page, dict):
        errors.append("page: missing")
        return
    for f in ("title", "heading", "lang"):
        if _missing(page.get(f)):
            errors.append(f"page: no {f}")
    if page.get("lang") and page["lang"] not in LANGS:
        errors.append(f"page: unknown lang {page['lang']!r}")
    for f in ("eyebrow", "intro"):
        if is_tbd(page.get(f)):
            warnings.append(f"page: {f} TBD")


def _check_table(box, bid, errors, warnings):
    _required(errors, warnings, f"table {bid}", bid, box, ("rowMeaning", "purpose"))
    cols = box.get("columns")
    if _missing(cols):
        errors.append(f"table {bid}: no columns")
        return
    seen = set()
    for col in cols:
        name = col.get("name")
        if _missing(name):
            errors.append(f"table {bid}: a column has no name")
            continue
        if name in seen:
            errors.append(f"column {bid}.{name}: name used twice")
        seen.add(name)
        _required(errors, warnings, f"column {bid}.{name}", f"{bid}.{name}", col, ("type", "short"))
        key = col.get("key")
        if not _missing(key) and key not in COLUMN_KEYS:
            errors.append(f"column {bid}.{name}: unknown key {key!r}")
        if is_tbd(col.get("desc")):
            warnings.append(f"{bid}.{name}: desc TBD")
        _highlight(errors, f"column {bid}.{name}", col.get("highlight"))


def _check_boxes(model, errors, warnings):
    ids = {}
    tiers = model.get("tiers")
    if _missing(tiers):
        errors.append("model: no tiers")
        return ids
    for n, tier in enumerate(tiers, 1):
        tname = tier.get("id") or f"#{n}"
        for f in ("id", "title", "boxes"):
            if _missing(tier.get(f)):
                errors.append(f"tier {tname}: no {f}")
        for box in tier.get("boxes") or []:
            bid = box.get("id")
            if _missing(bid):
                errors.append(f"tier {tname}: a box has no id")
                continue
            if bid in ids:
                errors.append(f"box {bid}: id used twice")
            ids[bid] = box
            kind = box.get("kind")
            if kind not in BOX_KINDS:
                errors.append(f"box {bid}: unknown kind {kind!r}")
                continue
            _highlight(errors, f"box {bid}", box.get("highlight"))
            if kind == "table":
                _check_table(box, bid, errors, warnings)
            else:
                lines = box.get("lines")
                if not isinstance(lines, list) or not 1 <= len(lines) <= 2 or any(_missing(s) for s in lines):
                    errors.append(f"endpoint {bid}: lines must hold 1 or 2 texts")
                if is_tbd(box.get("purpose")):
                    warnings.append(f"{bid}: purpose TBD")
    return ids


def _check_lines(model, ids, errors, warnings):
    for line in model.get("lines") or []:
        name = _line_name(line)
        kind = line.get("kind")
        if kind not in LINE_KINDS:
            errors.append(f"{name}: unknown kind {kind!r}")
            continue
        for which in ("from", "to"):
            end = line.get(which) or {}
            bid = end.get("box")
            box = ids.get(bid)
            if box is None:
                errors.append(f"{name}: end {which} names no box {bid!r}")
                continue
            column = end.get("column")
            if box.get("kind") == "endpoint":
                if kind != "flow":
                    errors.append(f"{name}: a {kind} line must join two tables; {bid} is an endpoint")
                elif not _missing(column):
                    errors.append(f"{name}: end {which} names a column on endpoint {bid}")
                continue
            if _missing(column):
                if kind != "flow":
                    errors.append(f"{name}: end {which} has no column")
                continue
            if column not in {c.get("name") for c in box.get("columns") or []}:
                errors.append(f"{name}: column {bid}.{column} is not in the model")
        _required(errors, warnings, name, name, line, ("label", "tooltip"))
        mult = line.get("mult")
        ends = [(line.get("from") or {}).get("box"), (line.get("to") or {}).get("box")]
        if not isinstance(mult, list) or len(mult) != 2:
            errors.append(f"{name}: mult must hold two values")
        else:
            for m, end in zip(mult, ends):
                if _missing(m):
                    errors.append(f"{name}: no multiplicity at end {end}")
                elif m not in MULTS:
                    errors.append(f"{name}: unknown multiplicity {m!r}")
        _highlight(errors, name, line.get("highlight"))


def _check_notes(model, errors):
    for n, note in enumerate(model.get("notes") or [], 1):
        name = f"note {note.get('heading') or n}"
        if note.get("kind") not in NOTE_KINDS:
            errors.append(f"{name}: unknown kind {note.get('kind')!r}")
        for f in ("heading", "paragraphs"):
            if _missing(note.get(f)):
                errors.append(f"{name}: no {f}")


def check(model):
    errors, warnings = [], []
    _check_page(model, errors, warnings)
    ids = _check_boxes(model, errors, warnings)
    _check_lines(model, ids, errors, warnings)
    _check_notes(model, errors)
    return errors, warnings
```

- [ ] **Step 6: Run the tests to see them pass**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: 20 tests, `OK`.

- [ ] **Step 7: Commit**

```bash
git add plugins/dev-workflows/skills/er-diagram/scripts/erlib plugins/dev-workflows/skills/er-diagram/tests
git commit -m "feat(er-diagram): ER model lists and the check: errors stop the page, TBD is a warning (ADRs 0402, 0403, 0405)"
```

---

### Task 3: Text widths, box sizes and vertical placement

**Files:**
- Create: `.../er-diagram/scripts/erlib/measure.py`
- Create: `.../er-diagram/scripts/erlib/layout.py`
- Test: `.../er-diagram/tests/test_layout_boxes.py`

**Interfaces:**
- Consumes: `helpers.small_model`, `helpers.box`.
- Produces: `erlib.measure.text_width(text: str, size: float, mono: bool = False) -> float`. In `erlib.layout`: constants `HEAD, ROW, BOTTOM, FOOT, EP_H, TOP, BOX_GAP, TIER_PAD, LANE, LANE_START, INSIDE_START, LABEL_PAD, MULT_ROOM, WIDEN, MAX_TRIES, SPREAD, SAFETY`; dataclasses `Box(id, kind, tier, data, w, h, x, y, col_x)` with `row_y(column) -> float` and `mid_y`; `Label(text, x, y, anchor, cls, w)` with `rect() -> (x0, y0, x1, y1)`; `Route(...)` (fields listed in Step 3); `Tier(title, subtitle, x0, x1, inner_w, inside_w)`; `Layout(width, height, tiers, boxes, routes, errors)`; functions `_size_boxes(model) -> (dict[str, Box], list[Tier])`, `_place_vertical(model, boxes, n_tiers) -> None`.

- [ ] **Step 1: Write the failing tests**

`.../er-diagram/tests/test_layout_boxes.py`:
```python
"""Tests for text widths, box sizes and vertical placement (spec section 5, rules 2-3)."""
import unittest

from helpers import box, small_model
from erlib.measure import text_width
from erlib.layout import BOTTOM, BOX_GAP, FOOT, HEAD, ROW, TOP, _place_vertical, _size_boxes


def placed(model):
    boxes, tiers = _size_boxes(model)
    _place_vertical(model, boxes, len(tiers))
    return boxes, tiers


class MeasureTest(unittest.TestCase):
    def test_mono_width_is_six_tenths_of_the_size_per_character(self):
        self.assertAlmostEqual(text_width("RawId", 12, mono=True), 36.0)

    def test_thai_marks_take_no_width(self):
        self.assertEqual(text_width("ที่", 10), text_width("ท", 10))


class BoxTest(unittest.TestCase):
    def test_tables_in_one_tier_share_width_and_column_starts(self):
        boxes, _ = placed(small_model())
        self.assertEqual(boxes["r1"].w, boxes["r2"].w)
        self.assertEqual(boxes["r1"].col_x, boxes["r2"].col_x)

    def test_table_height_counts_rows_and_footnotes(self):
        m = small_model()
        box(m, "c1")["footnotes"] = ["a", "b"]
        boxes, _ = placed(m)
        self.assertEqual(boxes["c1"].h, HEAD + ROW * 2 + BOTTOM + FOOT * 2)

    def test_first_box_starts_at_top(self):
        boxes, _ = placed(small_model())
        self.assertEqual(boxes["c1"].y, TOP)

    def test_endpoint_is_centred_level_with_its_table(self):
        boxes, _ = placed(small_model())
        self.assertEqual(boxes["E1"].mid_y, boxes["r1"].mid_y)

    def test_box_goes_below_when_its_level_place_is_taken(self):
        boxes, _ = placed(small_model())
        self.assertEqual(boxes["r2"].y, boxes["r1"].y + boxes["r1"].h + BOX_GAP)

    def test_row_y_is_the_middle_of_the_row(self):
        boxes, _ = placed(small_model())
        r1 = boxes["r1"]
        self.assertEqual(r1.row_y("K"), r1.y + HEAD + ROW * 2 + 10)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'erlib.measure'`.

- [ ] **Step 3: Write `measure.py` and the first part of `layout.py`**

`.../er-diagram/scripts/erlib/measure.py`:
```python
"""Estimated text widths for the layout (spec section 5, rule 3). No font file is read."""
import unicodedata

# Thai marks that sit above or below a letter take no width.
_ZERO = set(range(0x0E31, 0x0E32)) | set(range(0x0E34, 0x0E3B)) | set(range(0x0E47, 0x0E4F))


def text_width(text, size, mono=False):
    width = 0.0
    for ch in str(text):
        cp = ord(ch)
        if cp in _ZERO or unicodedata.combining(ch):
            continue
        if mono:
            width += 0.6 * size
        elif 0x0E00 <= cp <= 0x0E7F:
            width += 0.56 * size
        elif ch == " ":
            width += 0.28 * size
        elif ch.isupper() or ch.isdigit():
            width += 0.62 * size
        else:
            width += 0.52 * size
    return width
```

`.../er-diagram/scripts/erlib/layout.py`:
```python
"""Layout: every position from the ER model's order (ADR 0401 and its amendment; spec section 5).

The agent never writes a coordinate. layout(model) returns a Layout whose `errors` is empty when
every label and multiplicity is clear of everything else.
"""
from dataclasses import dataclass, field

from .measure import text_width

HEAD, ROW, BOTTOM, FOOT = 48, 20, 6, 18   # table sizes of the hand-drawn page
EP_H = 80                                  # endpoint height
TOP = 70                                   # first box y, below the tier title
BOX_GAP = 18
TIER_PAD = 12                              # box inset from the tier band
LANE = 12                                  # lane spacing
LANE_START = 28                            # first gap lane, from the tier band's right edge
INSIDE_START = 40                          # first inside lane, from the boxes' right edge
LABEL_PAD = 8
MULT_ROOM = 40                             # room for the right multiplicity before the next band
WIDEN, MAX_TRIES = 24, 20
SPREAD = 6
SAFETY = 1.08                              # estimated widths run a little short of real fonts


@dataclass
class Box:
    id: str
    kind: str
    tier: int
    data: dict
    w: float = 0
    h: float = 0
    x: float = 0
    y: float = 0
    col_x: tuple = (10, 0, 0, 0)           # name, type, key, description; from the box's x

    def row_y(self, column):
        for i, col in enumerate(self.data.get("columns", [])):
            if col["name"] == column:
                return self.y + HEAD + ROW * i + 10
        raise KeyError(column)

    @property
    def mid_y(self):
        return self.y + self.h / 2


@dataclass
class Label:
    text: str
    x: float
    y: float                                # text baseline
    anchor: str                             # "start" or "end"
    cls: str
    w: float

    def rect(self):
        x0 = self.x if self.anchor == "start" else self.x - self.w
        return (x0, self.y - 11, x0 + self.w, self.y + 2)


@dataclass
class Route:
    index: int                              # position in model["lines"]
    line: dict
    left: Box
    right: Box
    y_left: float
    y_right: float
    kind: str                               # "gap", "bus", "multi" or "inside"
    reverse: bool = False                   # the line's "from" box is the right-hand box
    group: str = ""                         # bus id; members are not checked against each other
    head: bool = True                       # False for a bus member after the first
    y_free: float = 0                       # height a multi-tier line crosses at
    key_left: tuple = ()
    key_right: tuple = ()
    right_rank: int = 0                     # place among the lines that enter one row
    right_n: int = 1
    points: list = field(default_factory=list)
    label: Label = None
    mults: list = field(default_factory=list)


@dataclass
class Tier:
    title: str
    subtitle: str
    x0: float = 0
    x1: float = 0
    inner_w: float = 0
    inside_w: float = 0


@dataclass
class Layout:
    width: float
    height: float
    tiers: list
    boxes: dict
    routes: list
    errors: list


def _size_boxes(model):
    """Box sizes: tables of one tier share one width and column starts (spec 5, rules 2-3)."""
    boxes, tiers = {}, []
    for ti, tier in enumerate(model["tiers"]):
        t = Tier(tier.get("title", ""), tier.get("subtitle", ""))
        tables = [b for b in tier["boxes"] if b["kind"] == "table"]
        endpoints = [b for b in tier["boxes"] if b["kind"] == "endpoint"]
        table_w, col_x = 0, (10, 0, 0, 0)
        if tables:
            cols = [c for b in tables for c in b["columns"]]
            name_w = max(text_width(c["name"], 12, mono=True) for c in cols)
            type_w = max(text_width(c["type"], 11.5, mono=True) for c in cols)
            desc_w = max(text_width(c["short"], 11.5) for c in cols)
            has_key = any(c.get("key") for c in cols)
            type_x = 10 + name_w * SAFETY + 16
            key_x = type_x + type_w * SAFETY + 12
            desc_x = key_x + (28 if has_key else 0)
            col_x = (10, round(type_x), round(key_x), round(desc_x))
            head_w = max(max(text_width(b["id"], 13, mono=True) + 50 for b in tables),
                         max(text_width(b["rowMeaning"], 11.5) + 24 for b in tables),
                         max((text_width(f, 11.5) + 20 for b in tables for f in b.get("footnotes", [])),
                             default=0))
            table_w = round(max(desc_x + desc_w * SAFETY + 14, head_w * SAFETY))
        ep_w = 0
        if endpoints:
            ep_w = round(max(max(text_width(b["id"], 14) + 24,
                                 *(text_width(s, 11.5) + 24 for s in b["lines"])) for b in endpoints) * SAFETY)
            ep_w = max(ep_w, 160)
        t.inner_w = max(table_w, ep_w)
        for b in tier["boxes"]:
            if b["kind"] == "table":
                boxes[b["id"]] = Box(b["id"], "table", ti, b, w=table_w, col_x=col_x,
                                     h=HEAD + ROW * len(b["columns"]) + BOTTOM + FOOT * len(b.get("footnotes", [])))
            else:
                boxes[b["id"]] = Box(b["id"], "endpoint", ti, b, w=ep_w, h=EP_H)
        tiers.append(t)
    return boxes, tiers


def _first_partner_right(lines, box, boxes):
    """The box in the next tier on the right that this box's first line (model order) joins."""
    for line in lines:
        a, b = boxes[line["from"]["box"]], boxes[line["to"]["box"]]
        if a is box and b.tier == box.tier + 1:
            return b
        if b is box and a.tier == box.tier + 1:
            return a
    return None


def _place_vertical(model, boxes, n_tiers):
    """Tiers from right to left; boxes top to bottom in model order, centred level with their
    first partner on the right when that place is free (ADR 0401 amendment)."""
    lines = model.get("lines", [])
    for ti in range(n_tiers - 1, -1, -1):
        cursor = TOP
        for b in model["tiers"][ti]["boxes"]:
            box = boxes[b["id"]]
            y = cursor
            other = _first_partner_right(lines, box, boxes)
            if other is not None:
                want = other.y + (other.h - box.h) / 2
                if want > cursor:
                    y = want
            box.y = round(y)
            cursor = box.y + box.h + BOX_GAP
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: 28 tests, `OK`.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/skills/er-diagram/scripts/erlib/measure.py plugins/dev-workflows/skills/er-diagram/scripts/erlib/layout.py plugins/dev-workflows/skills/er-diagram/tests/test_layout_boxes.py
git commit -m "feat(er-diagram): text widths, box sizes and vertical placement level with the partner box (ADR 0401)"
```

---

### Task 4: Lines, lanes, bus, labels, multiplicities and x positions

**Files:**
- Modify: `.../er-diagram/scripts/erlib/layout.py` (append)
- Test: `.../er-diagram/tests/test_layout_routes.py`

**Interfaces:**
- Consumes: Task 3's dataclasses, `_size_boxes`, `_place_vertical`, constants.
- Produces: `_assign(spans: list[(lo, hi, key)]) -> (dict[key, lane], lane_count)`; `_layout_once(model, extra: dict) -> Layout` (no overlap check yet; `extra` maps `("gap", g)` or `("inside", t)` to added px). Every `Route` of the result has `points` (from the line's `from` box to its `to` box), `label` (`None` only for bus members after the first), `mults` (list of `Label`, class `er-mult`).

- [ ] **Step 1: Write the failing tests**

`.../er-diagram/tests/test_layout_routes.py`:
```python
"""Tests for lines, lanes, bus, labels and multiplicities (spec section 5, rules 4-7)."""
import unittest

from helpers import small_model
from erlib.layout import SPREAD, _assign, _layout_once


def lay(model=None):
    return _layout_once(model or small_model(), {})


def route(layout, index):
    return next(r for r in layout.routes if r.index == index)


def add_line(model, kind, a, b, label, mult, col_a=None, col_b=None):
    line = {"kind": kind, "from": {"box": a}, "to": {"box": b}, "label": label,
            "tooltip": f"{a} to {b}", "mult": mult}
    if col_a:
        line["from"]["column"] = col_a
    if col_b:
        line["to"]["column"] = col_b
    model["lines"].append(line)
    return len(model["lines"]) - 1


class LaneTest(unittest.TestCase):
    def test_lines_share_a_lane_only_when_their_spans_do_not_overlap(self):
        lanes, count = _assign([(0, 10, "a"), (30, 40, "b"), (5, 35, "c")])
        self.assertEqual((lanes["a"], lanes["b"], lanes["c"], count), (0, 0, 1, 2))


class RouteTest(unittest.TestCase):
    def test_fk_lines_to_one_column_share_one_bus(self):
        layout = lay()
        a, b = route(layout, 3), route(layout, 4)
        self.assertEqual((a.kind, b.kind), ("bus", "bus"))
        self.assertEqual(a.points[1][0], b.points[1][0])
        self.assertIsNotNone(a.label)
        self.assertIsNone(b.label)

    def test_lines_into_one_row_are_spread(self):
        layout = lay()
        a, b = route(layout, 1), route(layout, 2)
        self.assertEqual(round(b.y_right - a.y_right), 2 * SPREAD)

    def test_lower_line_into_a_shared_row_has_its_label_below(self):
        layout = lay()
        a, b = route(layout, 1), route(layout, 2)
        self.assertLess(a.label.y, a.y_right)
        self.assertGreater(b.label.y, b.y_right)

    def test_labels_sit_right_of_every_lane_in_their_gap(self):
        layout = lay()
        gap = [r for r in layout.routes if r.kind in ("gap", "bus") and r.left.tier == 1]
        lane_xs = [x for r in gap for x, _ in r.points if x not in (r.left.x + r.left.w, r.right.x)]
        for r in gap:
            if r.label:
                self.assertGreater(r.label.x, max(lane_xs))

    def test_every_line_starts_at_its_from_box_and_ends_at_its_to_box(self):
        layout = lay()
        r = route(layout, 1)
        self.assertEqual(r.points[0][0], layout.boxes["r1"].x + layout.boxes["r1"].w)
        self.assertEqual(r.points[-1][0], layout.boxes["c1"].x)

    def test_reversed_line_starts_at_its_from_box(self):
        m = small_model()
        m["lines"][1]["from"], m["lines"][1]["to"] = m["lines"][1]["to"], m["lines"][1]["from"]
        r = route(lay(m), 1)
        self.assertTrue(r.reverse)
        self.assertEqual(r.points[0][0], r.right.x)

    def test_inside_tier_line_runs_in_a_lane_right_of_its_boxes(self):
        m = small_model()
        i = add_line(m, "same-value", "c1", "run", "K = Id", ["1", "*"], "K", "Id")
        layout = lay(m)
        r = route(layout, i)
        c1 = layout.boxes["c1"]
        self.assertEqual(r.kind, "inside")
        self.assertGreater(r.points[1][0], c1.x + c1.w)

    def test_line_across_two_tiers_crosses_clear_of_the_boxes_between(self):
        m = small_model()
        i = add_line(m, "flow", "E1", "c1", "skip", ["1", "*"])
        layout = lay(m)
        r = route(layout, i)
        self.assertEqual(r.kind, "multi")
        for b in (layout.boxes["r1"], layout.boxes["r2"]):
            self.assertFalse(b.y - 8 < r.y_free < b.y + b.h + 8)

    def test_same_multiplicity_leaving_one_row_is_drawn_once(self):
        m = small_model()
        i = add_line(m, "same-value", "r1", "c1", "K = Name", ["*", "1"], "K", "Name")
        layout = lay(m)
        left = [mm for r in (route(layout, 1), route(layout, i)) for mm in r.mults if mm.anchor == "start"]
        self.assertEqual(len(left), 1)

    def test_every_line_end_has_a_multiplicity(self):
        layout = lay()
        texts = sorted(m.text for r in layout.routes for m in r.mults)
        # 5 lines: E1 "1"/r1 "*"; r1 "*"/c1 "1"; r2 "*"/c1 "0..1"; bus: two sources "*", one target "1"
        self.assertEqual(texts, sorted(["1", "*", "*", "1", "*", "0..1", "*", "*", "1"]))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: FAIL with `ImportError: cannot import name '_assign'`.

- [ ] **Step 3: Append the routing code to `layout.py`**

Append to `.../er-diagram/scripts/erlib/layout.py`:
```python


def _attach_y(box, end):
    column = end.get("column")
    return box.row_y(column) if column else box.mid_y


def _make_routes(model, boxes):
    routes = []
    for i, line in enumerate(model.get("lines", [])):
        a, b = boxes[line["from"]["box"]], boxes[line["to"]["box"]]
        ya, yb = _attach_y(a, line["from"]), _attach_y(b, line["to"])
        if b.tier < a.tier:
            left, right, yl, yr, rev = b, a, yb, ya, True
        else:
            left, right, yl, yr, rev = a, b, ya, yb, False
        if a.tier == b.tier:
            kind = "inside"
        elif right.tier - left.tier == 1:
            kind = "gap"
        else:
            kind = "multi"
        routes.append(Route(i, line, left, right, yl, yr, kind, reverse=rev))
    groups = {}
    for r in routes:
        if r.line["kind"] == "fk" and r.kind == "gap" and not r.reverse:
            groups.setdefault((r.right.id, r.line["to"]["column"], r.left.tier), []).append(r)
    for (box_id, column, _), members in groups.items():
        if len(members) >= 2:
            for k, r in enumerate(members):
                r.kind, r.group, r.head = "bus", f"{box_id}.{column}", k == 0
    _spread(routes)
    return routes


def _spread(routes):
    """Lines that leave or enter one row are spread over it (spec 5, rule 4)."""
    ends = {}
    for r in routes:
        r.key_left = (r.left.id, "R", r.y_left)
        ends.setdefault(r.key_left, []).append((r, "left"))
        r.key_right = (r.right.id, "R" if r.kind == "inside" else "L", r.y_right)
        if r.head:
            ends.setdefault(r.key_right, []).append((r, "right"))
    for members in ends.values():
        n = len(members)
        for k, (r, which) in enumerate(members):
            off = 0 if n == 1 else -SPREAD + 2 * SPREAD * k / (n - 1)
            if which == "left":
                r.y_left += off
            else:
                r.y_right += off
                r.right_rank, r.right_n = k, n
    heads = {r.group: r for r in routes if r.kind == "bus" and r.head}
    for r in routes:
        if r.kind == "bus" and not r.head:
            r.y_right = heads[r.group].y_right


def _free_y(y, boxes, lo_tier, hi_tier):
    """The height nearest to y that no box of the tiers between covers (spec 5, rule 6)."""
    blocked = [(b.y - 8, b.y + b.h + 8) for b in boxes.values() if lo_tier < b.tier < hi_tier]

    def free(v):
        return all(not (lo < v < hi) for lo, hi in blocked)

    if free(y):
        return y
    candidates = [v for lo, hi in blocked for v in (lo, hi) if free(v)]
    return min(candidates, key=lambda v: (abs(v - y), v))


def _assign(spans):
    """Lanes for vertical spans: two spans share a lane only when they do not overlap."""
    ends, out = [], {}
    for lo, hi, key in sorted(spans, key=lambda s: (s[0], s[1])):
        for k, end in enumerate(ends):
            if end + 10 < lo:
                ends[k] = hi
                out[key] = k
                break
        else:
            ends.append(hi)
            out[key] = len(ends) - 1
    return out, len(ends)


def _label_cls(line):
    return "flow-label" if line["kind"] == "flow" else "er-link-label"


def _label_w(line):
    if line["kind"] == "flow":
        return text_width(line["label"], 11.5) * SAFETY
    return text_width(line["label"], 11, mono=True)


def _label_band(r):
    """Label above its last segment; below it for the lowest line of a shared row."""
    below = r.right_n >= 2 and r.right_rank == r.right_n - 1
    return (r.y_right + 4, r.y_right + 17) if below else (r.y_right - 17, r.y_right - 4)


def _label_columns(items):
    """items: (key, top, bottom, width). Labels that would touch go to the next column."""
    cols, widths, out = [], [], {}
    for key, top, bottom, w in sorted(items, key=lambda t: t[1]):
        for c, spans in enumerate(cols):
            if all(bottom + 2 <= t or top >= b + 2 for t, b in spans):
                spans.append((top, bottom))
                widths[c] = max(widths[c], w)
                out[key] = c
                break
        else:
            cols.append([(top, bottom)])
            widths.append(w)
            out[key] = len(cols) - 1
    return out, widths


def _dedupe(points):
    out = []
    for x, y in points:
        p = (round(x, 1), round(y, 1))
        if not out or out[-1] != p:
            out.append(p)
    return out


def _mult_text(r, which):
    first, second = r.line["mult"]
    if r.reverse:
        first, second = second, first
    return first if which == "left" else second


def _mult_label(r, which, text, pos):
    if which == "left":
        x, y, anchor = r.left.x + r.left.w + 4, r.y_left, "start"
    elif r.kind == "inside":
        x, y, anchor = r.right.x + r.right.w + 4, r.y_right, "start"
    else:
        x, y, anchor = r.right.x - 5, r.y_right, "end"
    return Label(text, x, y - 5 if pos == "above" else y + 15, anchor, "er-mult",
                 text_width(text, 12, mono=True))


def _place_mults(routes):
    """One multiplicity per line end; ends on one row with the same text share one (spec 5, rule 7)."""
    groups = {}
    for r in routes:
        groups.setdefault(r.key_left, []).append((r, "left"))
        if r.head:
            groups.setdefault(r.key_right, []).append((r, "right"))
    for key, members in groups.items():
        members.sort(key=lambda m: m[0].y_left if m[1] == "left" else m[0].y_right)
        default = "above" if key[1] == "R" else "below"
        texts = [_mult_text(r, which) for r, which in members]
        if len(set(texts)) == 1:
            r, which = members[0] if default == "above" else members[-1]
            r.mults.append(_mult_label(r, which, texts[0], default))
        else:
            last = len(members) - 1
            for k, (r, which) in enumerate(members):
                pos = "above" if k == 0 else "below" if k == last else default
                r.mults.append(_mult_label(r, which, texts[k], pos))


def _layout_once(model, extra):
    """One layout pass. extra: {("gap", g) or ("inside", t): px} added by the overlap retry."""
    boxes, tiers = _size_boxes(model)
    _place_vertical(model, boxes, len(tiers))
    routes = _make_routes(model, boxes)
    n = len(tiers)
    gap_spans = {g: [] for g in range(n - 1)}
    in_spans = {t: [] for t in range(n)}
    gap_labels = {g: [] for g in range(n - 1)}
    bus_span = {}
    for r in routes:
        lo, hi = min(r.y_left, r.y_right), max(r.y_left, r.y_right)
        if r.kind == "gap":
            if r.y_left != r.y_right:
                gap_spans[r.left.tier].append((lo, hi, ("r", r.index)))
        elif r.kind == "bus":
            b_lo, b_hi = bus_span.get(r.group, (r.y_right, r.y_right))
            bus_span[r.group] = (min(b_lo, r.y_left), max(b_hi, r.y_left))
        elif r.kind == "multi":
            r.y_free = _free_y(r.y_left, boxes, r.left.tier, r.right.tier)
            if r.y_free != r.y_left:
                gap_spans[r.left.tier].append(
                    (min(r.y_left, r.y_free), max(r.y_left, r.y_free), ("m1", r.index)))
            if r.y_free != r.y_right:
                gap_spans[r.right.tier - 1].append(
                    (min(r.y_free, r.y_right), max(r.y_free, r.y_right), ("m2", r.index)))
        else:
            in_spans[r.left.tier].append((lo, hi, ("i", r.index)))
        if r.kind != "inside" and r.head:
            top, bottom = _label_band(r)
            gap_labels[r.right.tier - 1].append((r.index, top, bottom, _label_w(r.line)))
    for r in routes:
        if r.kind == "bus" and r.head:
            lo, hi = bus_span[r.group]
            gap_spans[r.left.tier].append((lo, hi, ("b", r.group)))
    gap_lanes = {g: _assign(s) for g, s in gap_spans.items()}
    in_lanes = {t: _assign(s) for t, s in in_spans.items()}
    gap_cols = {g: _label_columns(items) for g, items in gap_labels.items()}
    in_label_w = {t: max((_label_w(r.line) for r in routes if r.kind == "inside" and r.left.tier == t),
                         default=0) for t in range(n)}

    x = 10
    for t_i, t in enumerate(tiers):
        t.x0 = x
        for b in boxes.values():
            if b.tier == t_i:
                b.x = x + TIER_PAD
        n_in = in_lanes[t_i][1]
        t.inside_w = 0 if n_in == 0 else (INSIDE_START + LANE * n_in + LABEL_PAD + in_label_w[t_i]
                                          + extra.get(("inside", t_i), 0))
        t.x1 = x + TIER_PAD + t.inner_w + t.inside_w + TIER_PAD
        if t_i < n - 1:
            widths = gap_cols[t_i][1]
            label_w = sum(widths) + 12 * max(len(widths) - 1, 0)
            x = (t.x1 + LANE_START + LANE * gap_lanes[t_i][1] + LABEL_PAD + extra.get(("gap", t_i), 0)
                 + label_w + MULT_ROOM)
    width = tiers[-1].x1 + 10
    height = max(b.y + b.h for b in boxes.values()) + 30

    def gap_lane_x(g, key):
        return tiers[g].x1 + LANE_START + LANE * gap_lanes[g][0][key]

    for r in routes:
        start = r.left.x + r.left.w
        if r.kind == "inside":
            t = r.left.tier
            ix = r.left.x + tiers[t].inner_w + INSIDE_START + LANE * in_lanes[t][0][("i", r.index)]
            pts = [(start, r.y_left), (ix, r.y_left), (ix, r.y_right), (r.right.x + r.right.w, r.y_right)]
            lx = (r.left.x + tiers[t].inner_w + INSIDE_START + LANE * in_lanes[t][1] + LABEL_PAD
                  + extra.get(("inside", t), 0))
            r.label = Label(r.line["label"], lx, (r.y_left + r.y_right) / 2 + 4, "start",
                            _label_cls(r.line), _label_w(r.line))
        else:
            end = r.right.x
            if r.kind == "gap":
                if r.y_left == r.y_right:
                    pts = [(start, r.y_left), (end, r.y_right)]
                else:
                    lx = gap_lane_x(r.left.tier, ("r", r.index))
                    pts = [(start, r.y_left), (lx, r.y_left), (lx, r.y_right), (end, r.y_right)]
            elif r.kind == "bus":
                bx = gap_lane_x(r.left.tier, ("b", r.group))
                pts = [(start, r.y_left), (bx, r.y_left), (bx, r.y_right)] + ([(end, r.y_right)] if r.head else [])
            else:
                pts = [(start, r.y_left)]
                if r.y_free != r.y_left:
                    l1 = gap_lane_x(r.left.tier, ("m1", r.index))
                    pts += [(l1, r.y_left), (l1, r.y_free)]
                if r.y_free != r.y_right:
                    l2 = gap_lane_x(r.right.tier - 1, ("m2", r.index))
                    pts += [(l2, r.y_free), (l2, r.y_right)]
                pts.append((end, r.y_right))
            if r.head:
                g = r.right.tier - 1
                cols, widths = gap_cols[g]
                c = cols[r.index]
                lx = (tiers[g].x1 + LANE_START + LANE * gap_lanes[g][1] + LABEL_PAD + extra.get(("gap", g), 0)
                      + sum(widths[:c]) + 12 * c)
                top, _ = _label_band(r)
                r.label = Label(r.line["label"], lx, top + 11, "start", _label_cls(r.line), _label_w(r.line))
        pts = _dedupe(pts)
        r.points = pts[::-1] if r.reverse else pts
    _place_mults(routes)
    return Layout(width, height, tiers, boxes, routes, [])
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: 39 tests, `OK`.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/skills/er-diagram/scripts/erlib/layout.py plugins/dev-workflows/skills/er-diagram/tests/test_layout_routes.py
git commit -m "feat(er-diagram): lines in lanes, FK bus, spread rows, labels right of the lanes, one multiplicity per end (ADR 0401)"
```

---

### Task 5: Overlap check and retry

**Files:**
- Modify: `.../er-diagram/scripts/erlib/layout.py` (append)
- Test: `.../er-diagram/tests/test_layout_overlap.py`

**Interfaces:**
- Consumes: Task 4's `_layout_once`, `Label`, `MAX_TRIES`, `WIDEN`.
- Produces: `layout(model) -> Layout` (the public entry; `errors` lists `"overlap: ..."` texts, sorted, when an overlap stays after `MAX_TRIES` widenings); `_overlaps(boxes, routes) -> list[(message, area)]`.

- [ ] **Step 1: Write the failing tests**

`.../er-diagram/tests/test_layout_overlap.py`:
```python
"""Tests for the overlap check and the retry (ADR 0405 error 6; spec section 5, rule 8)."""
import unittest
from unittest import mock

from helpers import small_model
from erlib.layout import MAX_TRIES, Label, _layout_once, _overlaps, layout


class OverlapTest(unittest.TestCase):
    def test_small_model_lays_out_with_no_overlap(self):
        self.assertEqual(layout(small_model()).errors, [])

    def test_two_labels_on_one_place_are_reported(self):
        lay = _layout_once(small_model(), {})
        a, b = lay.routes[1], lay.routes[2]
        a.label = Label("aaa", 5000, 5000, "start", "er-link-label", 30)
        b.label = Label("bbb", 5005, 5002, "start", "er-link-label", 30)
        found = _overlaps(lay.boxes, lay.routes)
        self.assertTrue(any("label 'aaa'" in msg and "label 'bbb'" in msg for msg, _ in found), found)

    def test_a_label_on_a_box_is_reported(self):
        lay = _layout_once(small_model(), {})
        c1 = lay.boxes["c1"]
        lay.routes[1].label = Label("zzz", c1.x + 20, c1.y + 30, "start", "er-link-label", 30)
        found = _overlaps(lay.boxes, lay.routes)
        self.assertTrue(any("touches box c1" in msg for msg, _ in found), found)

    def test_an_overlap_that_stays_is_an_error_after_the_last_try(self):
        with mock.patch("erlib.layout._overlaps", return_value=[("overlap: stays", ("gap", 0))]) as fake:
            lay = layout(small_model())
        self.assertEqual(lay.errors, ["overlap: stays"])
        self.assertEqual(fake.call_count, MAX_TRIES + 1)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: FAIL with `ImportError: cannot import name '_overlaps'`.

- [ ] **Step 3: Append the overlap code to `layout.py`**

Append to `.../er-diagram/scripts/erlib/layout.py`:
```python


def _rect_hit(a, b, margin=0.0):
    return a[0] < b[2] - margin and b[0] < a[2] - margin and a[1] < b[3] - margin and b[1] < a[3] - margin


def _seg_rect(p, q):
    return (min(p[0], q[0]) - 0.5, min(p[1], q[1]) - 0.5, max(p[0], q[0]) + 0.5, max(p[1], q[1]) + 0.5)


def _name(r):
    return f"line {r.line['from']['box']}→{r.line['to']['box']}"


def _area(r):
    return ("inside", r.left.tier) if r.kind == "inside" else ("gap", r.right.tier - 1)


def _related(r, r2):
    return r2 is r or bool(r.group and r.group == r2.group)


def _segments(routes, skip):
    for r2 in routes:
        if _related(skip, r2):
            continue
        for p, q in zip(r2.points, r2.points[1:]):
            yield r2, _seg_rect(p, q)


def _place_inside_labels(routes):
    """Move each inside-tier label along its lane until it is clear of other lines and labels."""
    placed = []
    for r in routes:
        if r.kind != "inside":
            continue
        lo, hi = sorted((r.y_left, r.y_right))
        mid = (lo + hi) / 2 + 4
        tries = [mid] + [mid + s * d for d in range(14, int(hi - lo) + 14, 14) for s in (-1, 1)]
        for y in tries:
            r.label.y = y
            rect = r.label.rect()
            if any(_rect_hit(rect, other) for other in placed):
                continue
            if any(_rect_hit(rect, seg) for _, seg in _segments(routes, r)):
                continue
            break
        else:
            r.label.y = mid
        placed.append(r.label.rect())


def _overlaps(boxes, routes):
    """Every label or multiplicity that touches another, a box, or another line."""
    texts = []
    for r in routes:
        if r.label:
            texts.append((r.label.rect(), r, f"label '{r.label.text}'"))
        for m in r.mults:
            texts.append((m.rect(), r, f"multiplicity '{m.text}'"))
    box_rects = [(b.id, (b.x, b.y, b.x + b.w, b.y + b.h)) for b in boxes.values()]
    found = []
    for i, (rect, r, what) in enumerate(texts):
        where = f"{what} of {_name(r)}"
        for rect2, r2, what2 in texts[i + 1:]:
            if not _related(r, r2) and _rect_hit(rect, rect2, 1):
                found.append((f"overlap: {where} touches {what2} of {_name(r2)}", _area(r)))
        for bid, br in box_rects:
            if _rect_hit(rect, br):
                found.append((f"overlap: {where} touches box {bid}", _area(r)))
        for r2, seg in _segments(routes, r):
            if _rect_hit(rect, seg):
                found.append((f"overlap: {where} touches {_name(r2)}", _area(r)))
                break
    return found


def layout(model):
    """Lay out a checked model. On an overlap, widen that gap by WIDEN px and try again,
    at most MAX_TRIES times; an overlap after that is an error (ADR 0401 rule 6, ADR 0405)."""
    extra = {}
    for _ in range(MAX_TRIES + 1):
        lay = _layout_once(model, extra)
        _place_inside_labels(lay.routes)
        found = _overlaps(lay.boxes, lay.routes)
        if not found:
            return lay
        for _, area in found:
            extra[area] = extra.get(area, 0) + WIDEN
    lay.errors = sorted({message for message, _ in found})
    return lay
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: 43 tests, `OK`. If `test_small_model_lays_out_with_no_overlap` fails, print `layout(small_model()).errors`, find which rule of spec section 5 the overlap breaks, and fix the layout code; do not change the test model.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/skills/er-diagram/scripts/erlib/layout.py plugins/dev-workflows/skills/er-diagram/tests/test_layout_overlap.py
git commit -m "feat(er-diagram): overlap check with widen-and-retry; an overlap that stays is an error (ADRs 0401, 0405)"
```

---

### Task 6: Drawing the SVG and the PNG check copy

**Files:**
- Create: `.../er-diagram/scripts/erlib/svg.py`
- Test: `.../er-diagram/tests/test_svg.py`

**Interfaces:**
- Consumes: `layout(model) -> Layout`, `HEAD`, `ROW`, `BOTTOM`, `FOOT`.
- Produces: `erlib.svg.SVG_CSS: str` (one rule per line, every rule starts with `svg.er `), `LIGHT: dict[str, str]` (light colour tokens without `--`), `draw_svg(layout, model) -> str` (starts with `<svg class="er"`), `check_svg(svg: str) -> str` (no `var(--`, no `:hover`, light background rect).

- [ ] **Step 1: Write the failing tests**

`.../er-diagram/tests/test_svg.py`:
```python
"""Tests for the SVG drawing (ADRs 0402, 0403; spec section 6) and the check copy (spec section 8)."""
import unittest

from helpers import box, small_model
from erlib.layout import layout
from erlib.svg import check_svg, draw_svg


def svg_of(model):
    return draw_svg(layout(model), model)


class SvgTest(unittest.TestCase):
    def test_every_box_and_every_line_is_drawn(self):
        m = small_model()
        svg = svg_of(m)
        for id_ in ("E1", "r1", "r2", "c1", "run"):
            self.assertIn(f">{id_}</text>", svg)
        self.assertEqual(svg.count('<g class="er-link">'), len(m["lines"]))

    def test_kinds_use_their_classes(self):
        svg = svg_of(small_model())
        self.assertIn('class="ep-box"', svg)
        self.assertIn('class="rel"', svg)
        self.assertIn('class="fk"', svg)
        self.assertIn('class="flow" d=', svg)
        self.assertIn('marker-end="url(#er-arrow)"', svg)

    def test_table_tooltip_carries_purpose_and_highlight_note(self):
        m = small_model()
        box(m, "c1")["highlight"] = {"kind": "change", "note": "new key"}
        svg = svg_of(m)
        self.assertIn("<title>c1: c1 purpose (new key)</title>", svg)
        self.assertIn('class="er-box chg"', svg)

    def test_problem_line_uses_the_bad_class_and_its_note(self):
        m = small_model()
        m["lines"][1]["highlight"] = {"kind": "problem", "note": "one row only"}
        svg = svg_of(m)
        self.assertIn('class="rel bad"', svg)
        self.assertIn("<title>r1 to c1 (one row only)</title>", svg)

    def test_column_tooltip_uses_desc_and_falls_back_to_short(self):
        m = small_model()
        box(m, "c1")["columns"][0]["desc"] = "the key of c1"
        svg = svg_of(m)
        self.assertIn("<title>K: the key of c1</title>", svg)
        self.assertIn("<title>Name: name</title>", svg)

    def test_text_is_escaped(self):
        m = small_model()
        box(m, "c1")["purpose"] = "a <b> & c"
        self.assertIn("a &lt;b&gt; &amp; c", svg_of(m))

    def test_check_copy_has_no_css_variables_and_a_background(self):
        out = check_svg(svg_of(small_model()))
        self.assertTrue(out.startswith("<svg"))
        self.assertNotIn("var(--", out)
        self.assertNotIn(":hover", out)
        self.assertNotIn("transparent", out)
        self.assertIn('fill="#f4f6f5"', out)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'erlib.svg'`.

- [ ] **Step 3: Write `svg.py`**

`.../er-diagram/scripts/erlib/svg.py`:
```python
"""Draw the ER diagram as SVG with the hand-drawn page's classes (ADRs 0402, 0403; spec 6),
and a copy with the light colours resolved for the PNG check (ADR 0406; spec 8)."""
import html
import re

from .layout import BOTTOM, FOOT, HEAD, ROW

SVG_CSS = """
svg.er .tier { fill: var(--band); stroke: var(--line); stroke-dasharray: 6 5; stroke-width: 1.5; }
svg.er .tier.alt { fill: var(--band2); }
svg.er .tier-title { font: 700 17px var(--font-display); fill: var(--fg); }
svg.er .tier-sub { font: 12px var(--font-body); fill: var(--muted); }
svg.er .er-box { fill: var(--surface); stroke: var(--line); stroke-width: 1.2; }
svg.er .er-box.chg { stroke: var(--good); stroke-width: 2.5; }
svg.er .er-box.bad { stroke: var(--bad); stroke-width: 2.5; }
svg.er .er-head { fill: var(--accent-soft); }
svg.er .er-head.chg { fill: var(--good-soft); }
svg.er .er-head.bad { fill: var(--bad-soft); }
svg.er .er-name { font: 600 13px var(--font-mono); fill: var(--fg); }
svg.er .er-sub { font: 11.5px var(--font-body); fill: var(--muted); }
svg.er .er-sub.chg { fill: var(--good); font-weight: 600; }
svg.er .er-sub.bad { fill: var(--bad); font-weight: 600; }
svg.er .er-col { font: 12px var(--font-mono); fill: var(--fg); }
svg.er .er-col.key { font-weight: 600; }
svg.er .er-col.chg { fill: var(--good); font-weight: 600; }
svg.er .er-col.bad { fill: var(--bad); font-weight: 600; }
svg.er .er-type { font: 11.5px var(--font-mono); fill: var(--muted); }
svg.er .er-key { font: 600 11px var(--font-mono); fill: var(--accent); }
svg.er .er-key.chg { fill: var(--good); }
svg.er .er-key.bad { fill: var(--bad); }
svg.er .er-desc { font: 11.5px var(--font-body); fill: var(--muted); }
svg.er .er-desc.chg { fill: var(--good); font-weight: 600; }
svg.er .er-desc.bad { fill: var(--bad); font-weight: 600; }
svg.er .ep-box { fill: var(--surface); stroke: var(--accent); stroke-width: 1.5; }
svg.er .ep-box.chg { stroke: var(--good); stroke-width: 2.5; }
svg.er .ep-box.bad { stroke: var(--bad); stroke-width: 2.5; }
svg.er .ep-name { font: 600 14px var(--font-body); fill: var(--fg); }
svg.er .ep-sub { font: 11.5px var(--font-body); fill: var(--muted); }
svg.er .flow { fill: none; stroke: var(--accent); stroke-width: 2; }
svg.er .flow.chg { stroke: var(--good); }
svg.er .flow.bad { stroke: var(--bad); }
svg.er .er-arrowhead { fill: var(--accent); }
svg.er .flow-label { font: 600 11.5px var(--font-body); fill: var(--accent); }
svg.er .fk { fill: none; stroke: var(--fg); stroke-width: 1.4; }
svg.er .fk.chg { stroke: var(--good); stroke-width: 2.2; }
svg.er .fk.bad { stroke: var(--bad); stroke-width: 2.2; }
svg.er .rel { fill: none; stroke: var(--muted); stroke-width: 1.4; stroke-dasharray: 5 4; }
svg.er .rel.chg { stroke: var(--good); stroke-width: 2.2; stroke-dasharray: none; }
svg.er .rel.bad { stroke: var(--bad); stroke-width: 2.2; stroke-dasharray: none; }
svg.er .er-mult { font: 600 12px var(--font-mono); fill: var(--muted); }
svg.er .er-mult.chg { fill: var(--good); }
svg.er .er-mult.bad { fill: var(--bad); }
svg.er .er-link-label { font: 11px var(--font-mono); fill: var(--fg); }
svg.er .er-link-label.chg, svg.er .flow-label.chg { fill: var(--good); font-weight: 600; }
svg.er .er-link-label.bad, svg.er .flow-label.bad { fill: var(--bad); font-weight: 600; }
svg.er .note { font: 11.5px var(--font-body); fill: var(--muted); }
svg.er .er-hit { fill: transparent; pointer-events: all; }
svg.er .er-row:hover .er-hit { fill: var(--accent-soft); }
svg.er .er-info { cursor: help; }
svg.er .er-info-dot { fill: var(--surface); stroke: var(--accent); stroke-width: 1.5; }
svg.er .er-info:hover .er-info-dot { fill: var(--accent-soft); }
svg.er .er-info-i { font: 700 12px Georgia, 'Times New Roman', serif; fill: var(--accent); pointer-events: none; }
svg.er .er-link { cursor: help; }
svg.er .er-link-hit { fill: none; stroke: transparent; stroke-width: 12; pointer-events: stroke; }
svg.er .er-link:hover .rel, svg.er .er-link:hover .fk { stroke: var(--accent); stroke-width: 2.6; }
svg.er .er-link:hover .flow { stroke-width: 3; }
""".strip()

LIGHT = {"bg": "#f4f6f5", "surface": "#ffffff", "fg": "#18211d", "muted": "#5a6a63", "line": "#d3dcd8",
         "accent": "#1d6a86", "accent-soft": "#e3eff4", "bad": "#a8492a", "bad-soft": "#f8e9e3",
         "good": "#2d7a4c", "good-soft": "#e3f2e8", "band": "#eef2f0", "band2": "#e8eeeb"}

_LINE_CLS = {"fk": "fk", "same-value": "rel", "flow": "flow"}
_HL_CLS = {"problem": "bad", "change": "chg"}


def esc(s):
    return html.escape(str(s), quote=True)


def _t(x, y, s, cls, anchor="start"):
    return f'<text class="{cls}" x="{x:g}" y="{y:g}" text-anchor="{anchor}">{esc(s)}</text>'


def _sfx(item):
    h = item.get("highlight")
    return f" {_HL_CLS[h['kind']]}" if h else ""


def _with_note(text, item):
    h = item.get("highlight")
    return f"{text} ({h['note']})".strip() if h else text


def _table(b):
    d, x, y, w, h = b.data, b.x, b.y, b.w, b.h
    sfx = _sfx(d)
    _, tx, kx, dx = b.col_x
    out = [f'<rect class="er-box{sfx}" x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="6"/>',
           f'<path class="er-head{sfx}" d="M {x:g} {y + 6:g} q 0 -6 6 -6 h {w - 12:g} q 6 0 6 6 v {HEAD - 6} h {-w:g} z"/>',
           _t(x + 10, y + 20, b.id, "er-name"),
           _t(x + 10, y + 39, d["rowMeaning"], "er-sub" + sfx),
           f'<g class="er-info"><title>{esc(b.id)}: {esc(_with_note(d["purpose"], d))}</title>'
           f'<circle class="er-info-dot" cx="{x + w - 18:g}" cy="{y + 18:g}" r="9"/>'
           f'<text class="er-info-i" x="{x + w - 18:g}" y="{y + 22:g}" text-anchor="middle">i</text></g>']
    for i, c in enumerate(d["columns"]):
        cy = y + HEAD + ROW * i + 15
        csfx = _sfx(c)
        cls = "er-col" + (csfx if csfx else (" key" if c.get("key") == "PK" else ""))
        out.append(f'<g class="er-row"><title>{esc(c["name"])}: {esc(_with_note(c.get("desc") or c["short"], c))}</title>')
        out.append(f'<rect class="er-hit" x="{x + 1:g}" y="{cy - 14:g}" width="{w - 2:g}" height="{ROW}"/>')
        out.append(_t(x + 10, cy, c["name"], cls))
        out.append(_t(x + tx, cy, c["type"], "er-type"))
        if c.get("key"):
            out.append(_t(x + kx, cy, c["key"], "er-key" + csfx))
        out.append(_t(x + dx, cy, c["short"], "er-desc" + csfx))
        out.append("</g>")
    for k, note in enumerate(d.get("footnotes", [])):
        out.append(_t(x + 10, y + HEAD + ROW * len(d["columns"]) + BOTTOM + 13 + FOOT * k, note, "note"))
    return out


def _endpoint(b):
    d = b.data
    sfx = _sfx(d)
    tip = _with_note(d.get("purpose") or "", d).strip()
    out = [f'<g class="er-info"><title>{esc(b.id)}: {esc(tip)}</title>'] if tip else []
    out.append(f'<rect class="ep-box{sfx}" x="{b.x:g}" y="{b.y:g}" width="{b.w:g}" height="{b.h:g}" rx="6"/>')
    out.append(_t(b.x + 12, b.y + 24, b.id, "ep-name"))
    for k, s in enumerate(d["lines"]):
        out.append(_t(b.x + 12, b.y + 46 + 18 * k, s, "ep-sub"))
    if tip:
        out.append("</g>")
    return out


def _route(r):
    line = r.line
    sfx = _sfx(line)
    d = "M " + " L ".join(f"{x:g} {y:g}" for x, y in r.points)
    marker = ' marker-end="url(#er-arrow)"' if line["kind"] == "flow" and r.head else ""
    out = [f'<g class="er-link"><title>{esc(_with_note(line["tooltip"], line))}</title>',
           f'<path class="er-link-hit" d="{d}"/>',
           f'<path class="{_LINE_CLS[line["kind"]]}{sfx}" d="{d}"{marker}/>']
    for m in r.mults:
        out.append(_t(m.x, m.y, m.text, "er-mult" + sfx, m.anchor))
    if r.label:
        out.append(_t(r.label.x, r.label.y, r.label.text, r.label.cls + sfx, r.label.anchor))
    out.append("</g>")
    return out


def _aria(model):
    titles = ", ".join(t.get("title", "") for t in model["tiers"])
    return f"ER diagram in {len(model['tiers'])} tiers: {titles}"


def draw_svg(lay, model):
    parts = []
    for i, t in enumerate(lay.tiers):
        parts.append(f'<rect class="tier{" alt" if i % 2 else ""}" x="{t.x0:g}" y="6" '
                     f'width="{t.x1 - t.x0:g}" height="{lay.height - 12:g}" rx="10"/>')
        parts.append(_t(t.x0 + 14, 30, t.title, "tier-title"))
        if t.subtitle:
            parts.append(_t(t.x0 + 14, 50, t.subtitle, "tier-sub"))
    for b in lay.boxes.values():
        parts.extend(_table(b) if b.kind == "table" else _endpoint(b))
    for r in lay.routes:
        parts.extend(_route(r))
    defs = ('<defs><marker id="er-arrow" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto">'
            '<polygon class="er-arrowhead" points="0 0, 10 4, 0 8"/></marker></defs>')
    return (f'<svg class="er" viewBox="0 0 {lay.width:g} {lay.height:g}" xmlns="http://www.w3.org/2000/svg" '
            f'role="img" aria-label="{esc(_aria(model))}">{defs}' + "\n".join(parts) + "</svg>")


def check_svg(svg):
    """The SVG with light colours and installed fonts written in, for a renderer that reads no
    CSS variables (spec section 8)."""
    rules = []
    for rule in SVG_CSS.splitlines():
        if ":hover" in rule:
            continue
        rule = rule.replace("svg.er ", "")
        rule = rule.replace("var(--font-mono)", "Consolas, monospace")
        rule = rule.replace("var(--font-body)", "Tahoma, sans-serif").replace("var(--font-display)", "Tahoma, sans-serif")
        rule = re.sub(r"var\(--([a-z0-9-]+)\)", lambda m: LIGHT[m.group(1)], rule)
        rules.append(rule.replace("transparent", "none"))
    head, rest = svg.split(">", 1)
    return (f'{head}><style>{" ".join(rules)}</style>'
            f'<rect width="100%" height="100%" fill="{LIGHT["bg"]}"/>{rest}')
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: 50 tests, `OK`.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/skills/er-diagram/scripts/erlib/svg.py plugins/dev-workflows/skills/er-diagram/tests/test_svg.py
git commit -m "feat(er-diagram): draw the SVG with the hand-drawn classes, highlights and tooltips; PNG check copy (ADRs 0402, 0403, 0406)"
```

---

### Task 7: The page: template, sections, legend, embedded model

**Files:**
- Create: `.../er-diagram/assets/er-page-template.html`
- Create: `.../er-diagram/scripts/erlib/page.py`
- Test: `.../er-diagram/tests/test_page.py`

**Interfaces:**
- Consumes: `erlib.svg.SVG_CSS`.
- Produces: `erlib.page.inline(text) -> str`, `legend(model) -> str`, `embed_model(model) -> str`, `extract_model(page_html: str) -> dict` (raises `ValueError` when no block), `build_page(model, svg: str) -> str`, `LEGEND: dict`. Template placeholders: `{{LANG}}`, `{{TITLE}}`, `{{SVG_CSS}}`, `{{HEADER}}`, `{{OVERVIEW}}`, `{{DIAGRAM}}`, `{{NOTES}}`, `{{MODEL}}`.

- [ ] **Step 1: Write the failing tests**

`.../er-diagram/tests/test_page.py`:
```python
"""Tests for the page (ADRs 0399, 0404; spec sections 4 and 6)."""
import unittest

from helpers import small_model
from erlib.page import build_page, extract_model, inline, legend


class PageTest(unittest.TestCase):
    def test_inline_allows_code_and_bold_and_escapes_the_rest(self):
        self.assertEqual(inline("a `x<y` and **b** <i>"), "a <code>x&lt;y</code> and <b>b</b> &lt;i&gt;")

    def test_model_round_trips_through_the_page(self):
        m = small_model()
        m["page"]["intro"] = "ends with </script> here"
        page = build_page(m, "<svg></svg>")
        self.assertEqual(extract_model(page), m)
        self.assertNotIn("</script> here", page)

    def test_extract_finds_the_model_behind_a_host_wrapper(self):
        page = ("<!doctype html><html><head><style>x</style></head><body>\n"
                + build_page(small_model(), "<svg></svg>"))
        self.assertEqual(extract_model(page), small_model())

    def test_extract_without_a_model_block_is_an_error(self):
        with self.assertRaises(ValueError):
            extract_model("<html></html>")

    def test_legend_lists_only_what_the_page_uses(self):
        m = small_model()
        self.assertIn("blue = data moves", legend(m))
        m["lines"] = [x for x in m["lines"] if x["kind"] != "flow"]
        text = legend(m)
        self.assertNotIn("blue = data moves", text)
        self.assertIn("same value", text)
        self.assertIn("<b>PK</b> primary key", text)
        self.assertNotIn("<b>AK</b>", text)
        self.assertNotIn("green = changed", text)

    def test_legend_shows_a_used_highlight(self):
        m = small_model()
        m["lines"][1]["highlight"] = {"kind": "change", "note": "n"}
        self.assertIn("green = changed", legend(m))

    def test_note_section_takes_its_kind_and_escapes_rows(self):
        m = small_model()
        m["notes"] = [{"kind": "problem", "heading": "Bad key", "paragraphs": ["p **x**"],
                       "before": {"tag": "old", "rows": "a < b", "result": "r"}}]
        page = build_page(m, "<svg></svg>")
        self.assertIn('<section class="problem"><h2>Bad key</h2><p>p <b>x</b></p>', page)
        self.assertIn('<div class="rows">a &lt; b</div>', page)

    def test_overview_comes_first_and_its_mermaid_is_escaped(self):
        m = small_model()
        m["overview"] = {"heading": "Flow", "mermaid": 'flowchart LR\n  A["a<br/>b"] --> B'}
        page = build_page(m, "<svg></svg>")
        self.assertIn("<h2>1. Flow</h2>", page)
        self.assertIn("a&lt;br/&gt;b", page)
        self.assertIn("<h2>2. ER diagram by system</h2>", page)

    def test_without_overview_the_diagram_is_section_one(self):
        self.assertIn("<h2>1. ER diagram by system</h2>", build_page(small_model(), "<svg></svg>"))

    def test_page_has_no_placeholder_left_and_loads_mermaid(self):
        page = build_page(small_model(), "<svg></svg>")
        self.assertNotIn("{{", page)
        self.assertIn("https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js", page)
        self.assertIn("<title>Small Test</title>", page)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'erlib.page'`.

- [ ] **Step 3: Write the template**

`.../er-diagram/assets/er-page-template.html`:
```html
<!doctype html>
<html lang="{{LANG}}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Anuphan:wght@500;700&family=IBM+Plex+Sans+Thai:wght@400;600&family=IBM+Plex+Mono:wght@400;600&display=swap">
<style>
  :root {
    --bg: #f4f6f5; --surface: #ffffff; --fg: #18211d; --muted: #5a6a63; --line: #d3dcd8;
    --accent: #1d6a86; --accent-soft: #e3eff4; --bad: #a8492a; --bad-soft: #f8e9e3; --good: #2d7a4c; --good-soft: #e3f2e8; --band: #eef2f0; --band2: #e8eeeb;
    --font-display: 'Anuphan', 'IBM Plex Sans Thai', 'Tahoma', sans-serif;
    --font-body: 'IBM Plex Sans Thai', 'Tahoma', 'Segoe UI', sans-serif;
    --font-mono: 'IBM Plex Mono', 'Consolas', monospace;
    color-scheme: light;
  }
  @media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
    --bg: #101714; --surface: #17201c; --fg: #e3ebe7; --muted: #95a59d; --line: #2a3631;
    --accent: #6bb8d4; --accent-soft: #16303a; --bad: #e58a65; --bad-soft: #3a211a; --good: #72c595; --good-soft: #17301f; --band: #131c18; --band2: #17211c; color-scheme: dark } }
  :root[data-theme="dark"] {
    --bg: #101714; --surface: #17201c; --fg: #e3ebe7; --muted: #95a59d; --line: #2a3631;
    --accent: #6bb8d4; --accent-soft: #16303a; --bad: #e58a65; --bad-soft: #3a211a; --good: #72c595; --good-soft: #17301f; --band: #131c18; --band2: #17211c; color-scheme: dark }

  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--fg); font-family: var(--font-body); font-size: 15px; line-height: 1.65;
         padding-left: max(16px, env(safe-area-inset-left, 0px)); padding-right: max(16px, env(safe-area-inset-right, 0px)); }
  main { max-width: 1180px; margin: 0 auto; padding-block: 32px 64px; display: grid; gap: 40px; }
  h1, h2 { font-family: var(--font-display); text-wrap: balance; margin: 0; line-height: 1.25; }
  h1 { font-size: 30px; }
  h2 { font-size: 21px; }
  p { margin: 0; max-width: 68ch; }
  code { font-family: var(--font-mono); font-size: 0.88em; background: var(--accent-soft); padding: 1px 5px; border-radius: 4px; }
  .eyebrow { font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: var(--muted); }
  header { display: grid; gap: 10px; }
  section { display: grid; gap: 14px; min-width: 0; }
  .diagram { background: var(--surface); border: 1px solid var(--line); border-radius: 8px; padding: 16px; overflow-x: auto; }
  .diagram pre.mermaid { margin: 0; background: transparent; }
  .legend { display: flex; flex-wrap: wrap; gap: 8px 22px; font-size: 13px; color: var(--muted); }
  .legend b { color: var(--fg); font-family: var(--font-mono); font-weight: 600; }
  .problem, .change { border-left: 4px solid var(--bad); background: var(--surface); border-radius: 0 8px 8px 0; padding: 20px 22px; display: grid; gap: 14px; }
  .change { border-left-color: var(--good); }
  .problem h2 { color: var(--bad); }
  .change h2 { color: var(--good); }
  .compare { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 16px; }
  .compare > div { min-width: 0; display: grid; gap: 8px; align-content: start; }
  .tag { display: inline-block; font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 999px; }
  .tag.bad { background: var(--bad-soft); color: var(--bad); }
  .tag.good { background: var(--good-soft); color: var(--good); }
  .rows { font-family: var(--font-mono); font-size: 13px; background: var(--bg); border: 1px solid var(--line); border-radius: 6px;
          padding: 10px 12px; overflow-x: auto; white-space: pre; line-height: 1.6; }
  .note { font-size: 13px; color: var(--muted); }
  .diagram svg.er { display: block; width: 100%; min-width: 1200px; height: auto; }
  .diagram.wide { width: min(1920px, calc(100vw - 32px)); margin-left: calc(50% - min(960px, 50vw - 16px)); }
{{SVG_CSS}}
</style>
</head>
<body>
<main>
{{HEADER}}
{{OVERVIEW}}
{{DIAGRAM}}
{{NOTES}}
</main>
<script type="application/json" id="er-model">{{MODEL}}</script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/10.9.1/mermaid.min.js"></script>
<script>
  (function () {
    if (!window.mermaid || !document.querySelector('pre.mermaid')) return;
    var dark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;
    try {
      mermaid.initialize({ startOnLoad: false, theme: dark ? 'dark' : 'neutral' });
      mermaid.run({ querySelector: 'pre.mermaid:not([data-processed])' });
    } catch (e) { /* the flow stays as text */ }
  })();
</script>
</body>
</html>
```

- [ ] **Step 4: Write `page.py`**

`.../er-diagram/scripts/erlib/page.py`:
```python
"""The ER page: template, sections, legend and the embedded ER model (ADRs 0399, 0404; spec 4, 6)."""
import html
import json
import os
import re

from .svg import SVG_CSS

SKILL = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TEMPLATE = os.path.join(SKILL, "assets", "er-page-template.html")
_MODEL_RE = re.compile(r"""<script[^>]*\bid=["']?er-model["']?[^>]*>(.*?)</script>""", re.S)

LEGEND = {
    "th": {
        "flow": "<b>→</b> สีฟ้า = ข้อมูลไหลหรือถูกคำนวณ",
        "fk": "<b>────</b> foreign key จริงใน database",
        "same-value": "<b>- - -</b> เชื่อมด้วยค่าเดียวกัน แต่ไม่มี foreign key",
        "mult": "จำนวนที่ปลายเส้น (* = หลายแถว)",
        "keys": {"PK": "primary key", "FK": "foreign key", "AK": "alternate key",
                 "IX": "index (ไม่ unique)", "UQ": "unique"},
        "change": "สีเขียว = เปลี่ยน (ชี้เมาส์ดูเหตุผล)",
        "problem": "สีส้มแดง = ปัญหา (ชี้เมาส์ดูเหตุผล)",
        "hint": ("ทุกกล่องมีบรรทัด \"1 แถว =\" ใต้ชื่อตาราง. ชี้เมาส์ที่ (i) เพื่อดูว่าตารางมีไว้ทำอะไร, "
                 "ที่คอลัมน์เพื่อดูคำอธิบายเต็ม, ที่เส้นเพื่อดูความสัมพันธ์."),
        "overview": "ข้อมูลไหลอย่างไร",
        "diagram": "ER diagram แยกตามระบบ",
        "status": "สถานะ:",
    },
    "en": {
        "flow": "<b>→</b> blue = data moves or is computed",
        "fk": "<b>────</b> a real foreign key in the database",
        "same-value": "<b>- - -</b> joined by the same value, no foreign key",
        "mult": "rows at each end of a line (* = many)",
        "keys": {"PK": "primary key", "FK": "foreign key", "AK": "alternate key",
                 "IX": "index (not unique)", "UQ": "unique"},
        "change": "green = changed (hover for why)",
        "problem": "red-orange = problem (hover for why)",
        "hint": ("Each box shows what one row means under its name. Hover (i) for what a table is for, "
                 "a column for its full description, a line for the relationship."),
        "overview": "How the data flows",
        "diagram": "ER diagram by system",
        "status": "Status:",
    },
}


def inline(text):
    """Plain text with two marks: `code` and **bold** (spec section 4)."""
    out = html.escape(str(text), quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    return re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", out)


def embed_model(model):
    return json.dumps(model, ensure_ascii=False, indent=2).replace("<", "\\u003c")


def extract_model(page_html):
    match = _MODEL_RE.search(page_html)
    if not match:
        raise ValueError("no ER model block (script id er-model) in the page")
    return json.loads(match.group(1))


def _highlight_kinds(model):
    kinds = set()

    def add(item):
        h = item.get("highlight")
        if h:
            kinds.add(h["kind"])

    for tier in model["tiers"]:
        for b in tier["boxes"]:
            add(b)
            for c in b.get("columns", []):
                add(c)
    for line in model.get("lines", []):
        add(line)
    return kinds


def legend(model):
    words = LEGEND[model["page"]["lang"]]
    lines = model.get("lines", [])
    items = [words[k] for k in ("flow", "fk", "same-value") if any(x["kind"] == k for x in lines)]
    mults = [m for m in ("1", "0..1", "*", "1..*") if any(m in x["mult"] for x in lines)]
    if mults:
        items.append(f"<b>{' · '.join(mults)}</b> {words['mult']}")
    cols = [c for tier in model["tiers"] for b in tier["boxes"] for c in b.get("columns", [])]
    keys = [k for k in ("PK", "FK", "AK", "IX", "UQ") if any(c.get("key") == k for c in cols)]
    if keys:
        items.append(" · ".join(f"<b>{k}</b> {words['keys'][k]}" for k in keys))
    kinds = _highlight_kinds(model)
    items.extend(words[k] for k in ("change", "problem") if k in kinds)
    return '<div class="legend">' + "".join(f"<span>{i}</span>" for i in items) + "</div>"


def _header(page):
    eyebrow = f'<div class="eyebrow">{inline(page["eyebrow"])}</div>' if page.get("eyebrow") else ""
    intro = f"<p>{inline(page['intro'])}</p>" if page.get("intro") else ""
    return f"<header>{eyebrow}<h1>{inline(page['heading'])}</h1>{intro}</header>"


def _overview(model, number, words):
    ov = model.get("overview")
    if not ov:
        return ""
    text = f"<p>{inline(ov['text'])}</p>" if ov.get("text") else ""
    flow = (f'<div class="diagram"><pre class="mermaid">{html.escape(ov["mermaid"], quote=False)}</pre></div>'
            if ov.get("mermaid") else "")
    return f"<section><h2>{number}. {inline(ov.get('heading') or words['overview'])}</h2>{text}{flow}</section>"


def _diagram(model, svg, number, words):
    d = model.get("diagram") or {}
    text = f"<p>{inline(d['text'])}</p>" if d.get("text") else ""
    return (f"<section><h2>{number}. {inline(d.get('heading') or words['diagram'])}</h2>"
            f'<p class="note">{words["hint"]}</p>{text}{legend(model)}'
            f'<div class="diagram wide">{svg}</div></section>')


def _side(block, tag_cls):
    if not block:
        return ""
    rows = f'<div class="rows">{html.escape(block["rows"], quote=False)}</div>' if block.get("rows") else ""
    result = f'<p class="note">{inline(block["result"])}</p>' if block.get("result") else ""
    return f'<div><span class="tag {tag_cls}">{inline(block.get("tag", ""))}</span>{rows}{result}</div>'


def _note(note, words):
    paras = "".join(f"<p>{inline(p)}</p>" for p in note["paragraphs"])
    compare = ""
    if note.get("before") or note.get("after"):
        compare = f'<div class="compare">{_side(note.get("before"), "bad")}{_side(note.get("after"), "good")}</div>'
    status = f"<p><b>{words['status']}</b> {inline(note['status'])}</p>" if note.get("status") else ""
    return f'<section class="{note["kind"]}"><h2>{inline(note["heading"])}</h2>{paras}{compare}{status}</section>'


def build_page(model, svg):
    words = LEGEND[model["page"]["lang"]]
    with open(TEMPLATE, encoding="utf-8") as f:
        template = f.read()
    overview = _overview(model, 1, words)
    parts = {
        "{{LANG}}": model["page"]["lang"],
        "{{TITLE}}": html.escape(model["page"]["title"]),
        "{{SVG_CSS}}": SVG_CSS,
        "{{HEADER}}": _header(model["page"]),
        "{{OVERVIEW}}": overview,
        "{{DIAGRAM}}": _diagram(model, svg, 2 if overview else 1, words),
        "{{NOTES}}": "".join(_note(n, words) for n in model.get("notes") or []),
        "{{MODEL}}": embed_model(model),
    }
    return re.sub(r"\{\{[A-Z_]+\}\}", lambda m: parts[m.group(0)], template)
```

- [ ] **Step 5: Run the tests to see them pass**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: 60 tests, `OK`.

- [ ] **Step 6: Commit**

```bash
git add plugins/dev-workflows/skills/er-diagram/assets/er-page-template.html plugins/dev-workflows/skills/er-diagram/scripts/erlib/page.py plugins/dev-workflows/skills/er-diagram/tests/test_page.py
git commit -m "feat(er-diagram): page template, sections, legend from what is used, ER model embedded and extracted (ADRs 0399, 0404)"
```

---

### Task 8: The made-up example: Bookshop order sync

**Files:**
- Create: `.../er-diagram/assets/example-bookshop.er.json`
- Test: `.../er-diagram/tests/test_example.py`

**Interfaces:**
- Consumes: `check`, `layout`, `draw_svg`, `build_page`.
- Produces: the example file used by Task 9's CLI tests: 4 tiers, 9 tables, 4 endpoints, 17 lines, exactly one TBD (`order.Status: desc TBD`).

- [ ] **Step 1: Write the failing tests**

`.../er-diagram/tests/test_example.py`:
```python
"""The made-up Bookshop example builds clean (ADR 0409; spec section 11)."""
import unittest

from helpers import example
from erlib.check import check
from erlib.layout import layout
from erlib.page import build_page, extract_model
from erlib.svg import draw_svg


class ExampleTest(unittest.TestCase):
    def test_example_checks_clean_with_one_tbd(self):
        self.assertEqual(check(example()), ([], ["order.Status: desc TBD"]))

    def test_example_lays_out_with_no_overlap(self):
        self.assertEqual(layout(example()).errors, [])

    def test_example_page_draws_every_table_and_line_and_round_trips(self):
        m = example()
        svg = draw_svg(layout(m), m)
        for tier in m["tiers"]:
            for b in tier["boxes"]:
                self.assertIn(f">{b['id']}</text>", svg)
        self.assertEqual(svg.count('<g class="er-link">'), len(m["lines"]))
        self.assertEqual(extract_model(build_page(m, svg)), m)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: FAIL with `FileNotFoundError` for `example-bookshop.er.json`.

- [ ] **Step 3: Write the example**

`.../er-diagram/assets/example-bookshop.er.json`:
```json
{
  "erModel": 1,
  "page": {
    "title": "Bookshop Order Sync",
    "eyebrow": "Bookshop · order sync · ตัวอย่างที่แต่งขึ้น",
    "heading": "ข้อมูลของ order sync เก็บที่ไหนบ้าง",
    "intro": "order sync อ่าน order จาก Shop API ทุกชั่วโมง เก็บลง PostgreSQL สองชั้น แล้วเขียน order row ใน CRM ให้ทีมขายใช้. หน้านี้แสดงทุกตาราง รวม `order_line` ที่เปลี่ยน key เป็นเลข line แล้ว.",
    "lang": "th"
  },
  "overview": {
    "heading": "ข้อมูลไหลอย่างไร",
    "text": "ทุก run เขียนสองชั้นจากข้อมูลชุดเดียวกัน: `shop_raw` เป็นสมุดบันทึก และ `shop` เป็นสถานะปัจจุบัน. run ปกติ **ไม่อ่าน** `shop_raw`; มีแค่ rebuild ที่อ่าน.",
    "mermaid": "flowchart LR\n  subgraph API[\"Shop API\"]\n    E1[\"OrdersChanged\"]\n    E2[\"OrderLinesChanged\"]\n    E3[\"Deletions\"]\n    E4[\"Customers\"]\n  end\n  subgraph RAW[\"PostgreSQL · shop_raw · สมุดบันทึก\"]\n    R[\"4 ตาราง (1 ต่อ endpoint)<br/>เพิ่มอย่างเดียว\"]\n  end\n  subgraph CUR[\"PostgreSQL · shop · สถานะปัจจุบัน\"]\n    C[\"order, order_line, customer\"]\n  end\n  subgraph CRM[\"CRM\"]\n    D[\"crm_order\"]\n  end\n  API -->|\"1 Land\"| RAW\n  API -->|\"2 Store\"| CUR\n  RAW -.->|\"rebuild เท่านั้น\"| CUR\n  CUR -->|\"3 Publish\"| CRM"
  },
  "diagram": {
    "heading": "ER diagram แยกตามระบบ",
    "text": "ครบทุกตารางและทุกคอลัมน์ตาม model ในโค้ด. `crm_order` แสดงเฉพาะคอลัมน์ที่ sync เขียน."
  },
  "tiers": [
    {
      "id": "api",
      "title": "Shop API",
      "subtitle": "endpoint ที่ sync อ่าน",
      "boxes": [
        { "kind": "endpoint", "id": "OrdersChanged", "lines": ["OrderId, OrderNo,", "CustomerId, Status"] },
        { "kind": "endpoint", "id": "OrderLinesChanged", "lines": ["LinePk (เลข line), OrderId,", "Isbn, Qty"] },
        { "kind": "endpoint", "id": "Deletions", "lines": ["Entity, SourceId", "(ใช้แค่ order, line)"] },
        { "kind": "endpoint", "id": "Customers", "lines": ["CustomerId, Name,", "Email, Inactive"] }
      ]
    },
    {
      "id": "raw",
      "title": "PostgreSQL · shop_raw",
      "subtitle": "สมุดบันทึก: เพิ่มอย่างเดียว",
      "boxes": [
        {
          "kind": "table",
          "id": "raw_orders",
          "rowMeaning": "1 แถว = อ่าน order 1 ครั้ง",
          "purpose": "เก็บทุก record ที่อ่านจาก OrdersChanged ไว้เป็นประวัติ ใช้ตอน rebuild",
          "columns": [
            { "name": "RawId", "type": "bigint", "key": "PK", "short": "เลขแถว (รันเอง)", "desc": "เลขรันของแถว เพิ่มขึ้นเอง" },
            { "name": "SyncRunId", "type": "bigint", "key": "FK", "short": "run ที่ land แถวนี้", "desc": "run ที่ land แถวนี้ → sync_run.RunId (FK)" },
            { "name": "LoadedAt", "type": "timestamptz", "short": "เวลาที่ land" },
            { "name": "SourceId", "type": "text", "short": "OrderId", "desc": "OrderId ของ order (ดึงจาก JSON)" },
            { "name": "Payload", "type": "jsonb", "short": "JSON ดิบจาก API", "desc": "JSON ทั้งก้อนตามที่ API ส่งมา ไม่แก้ไข" }
          ]
        },
        {
          "kind": "table",
          "id": "raw_order_lines",
          "rowMeaning": "1 แถว = อ่าน order line 1 ครั้ง",
          "purpose": "เก็บทุก line ที่อ่านจาก OrderLinesChanged เป็นประวัติ; เลข line อยู่ใน SourceId",
          "columns": [
            { "name": "RawId", "type": "bigint", "key": "PK", "short": "เลขแถว (รันเอง)", "desc": "เลขรันของแถว เพิ่มขึ้นเอง" },
            { "name": "SyncRunId", "type": "bigint", "key": "FK", "short": "run ที่ land แถวนี้", "desc": "run ที่ land แถวนี้ → sync_run.RunId (FK)" },
            { "name": "LoadedAt", "type": "timestamptz", "short": "เวลาที่ land" },
            { "name": "SourceId", "type": "text", "short": "LinePk (เลข line)", "desc": "เลข line ของร้าน" },
            { "name": "Payload", "type": "jsonb", "short": "JSON ดิบจาก API", "desc": "JSON ทั้งก้อนตามที่ API ส่งมา ไม่แก้ไข" }
          ]
        },
        {
          "kind": "table",
          "id": "raw_deletions",
          "rowMeaning": "1 แถว = อ่านรายการลบ 1 ครั้ง",
          "purpose": "เก็บทุกรายการลบที่อ่านจาก Deletions; sync ใช้แค่ Entity \"order\" และ \"line\"",
          "columns": [
            { "name": "RawId", "type": "bigint", "key": "PK", "short": "เลขแถว (รันเอง)", "desc": "เลขรันของแถว เพิ่มขึ้นเอง" },
            { "name": "SyncRunId", "type": "bigint", "key": "FK", "short": "run ที่ land แถวนี้", "desc": "run ที่ land แถวนี้ → sync_run.RunId (FK)" },
            { "name": "LoadedAt", "type": "timestamptz", "short": "เวลาที่ land" },
            { "name": "SourceId", "type": "text", "short": "id ของสิ่งที่ถูกลบ", "desc": "SourceId: id ของสิ่งที่ถูกลบ (line = LinePk, order = OrderId)" },
            { "name": "Payload", "type": "jsonb", "short": "JSON ดิบจาก API", "desc": "JSON ทั้งก้อนตามที่ API ส่งมา ไม่แก้ไข" }
          ]
        },
        {
          "kind": "table",
          "id": "raw_customers",
          "rowMeaning": "1 แถว = อ่าน customer 1 ครั้ง",
          "purpose": "เก็บทุก customer ที่อ่านจาก Customers เป็นประวัติ",
          "columns": [
            { "name": "RawId", "type": "bigint", "key": "PK", "short": "เลขแถว (รันเอง)", "desc": "เลขรันของแถว เพิ่มขึ้นเอง" },
            { "name": "SyncRunId", "type": "bigint", "key": "FK", "short": "run ที่ land แถวนี้", "desc": "run ที่ land แถวนี้ → sync_run.RunId (FK)" },
            { "name": "LoadedAt", "type": "timestamptz", "short": "เวลาที่ land" },
            { "name": "SourceId", "type": "text", "short": "CustomerId" },
            { "name": "Payload", "type": "jsonb", "short": "JSON ดิบจาก API", "desc": "JSON ทั้งก้อนตามที่ API ส่งมา ไม่แก้ไข" }
          ]
        }
      ]
    },
    {
      "id": "shop",
      "title": "PostgreSQL · shop",
      "subtitle": "สถานะปัจจุบัน: แก้ทับ",
      "boxes": [
        {
          "kind": "table",
          "id": "order",
          "rowMeaning": "1 แถว = 1 order",
          "purpose": "สถานะปัจจุบันของแต่ละ order; ใช้สร้าง order row ใน CRM",
          "columns": [
            { "name": "OrderId", "type": "text", "key": "PK", "short": "เลข order ของร้าน" },
            { "name": "OrderNo", "type": "text", "short": "เลขที่ให้ลูกค้าเห็น" },
            { "name": "CustomerId", "type": "text", "key": "IX", "short": "ลูกค้า" },
            { "name": "PlacedOn", "type": "timestamptz", "short": "วันที่สั่ง (UTC)" },
            { "name": "Status", "type": "text", "short": "สถานะ", "desc": "TBD" },
            { "name": "DeletedInShop", "type": "bool", "short": "ร้านลบ order แล้ว" },
            { "name": "LastSyncedAt", "type": "timestamptz", "short": "sync เขียนล่าสุดเมื่อ" }
          ]
        },
        {
          "kind": "table",
          "id": "order_line",
          "rowMeaning": "1 แถว = 1 line ของร้าน",
          "purpose": "สถานะปัจจุบันของทุก line: หนังสือเล่มไหน กี่เล่ม ใน order ไหน. หนังสือเล่มเดียวมีได้หลาย line",
          "highlight": { "kind": "change", "note": "key เปลี่ยนจาก order + หนังสือ เป็นเลข line: ทุก line มีแถวของตัวเอง" },
          "columns": [
            { "name": "LinePk", "type": "text", "key": "PK", "short": "เลข line (primary key)",
              "highlight": { "kind": "change", "note": "เลข line ของร้าน = primary key" } },
            { "name": "OrderId", "type": "text", "key": "IX", "short": "order" },
            { "name": "Isbn", "type": "text", "short": "หนังสือ (ISBN)" },
            { "name": "Qty", "type": "int", "short": "จำนวน" },
            { "name": "DeletedInShop", "type": "bool", "short": "ร้านลบ line นี้แล้ว" },
            { "name": "ShopUpdatedAt", "type": "timestamptz", "short": "เวลาที่แก้ในร้าน" },
            { "name": "LastSyncedAt", "type": "timestamptz", "short": "sync เขียนล่าสุดเมื่อ" }
          ]
        },
        {
          "kind": "table",
          "id": "customer",
          "rowMeaning": "1 แถว = 1 ลูกค้า",
          "purpose": "สถานะปัจจุบันของลูกค้า: ชื่อ, email และ Inactive",
          "columns": [
            { "name": "CustomerId", "type": "text", "key": "PK", "short": "เลขลูกค้า" },
            { "name": "Name", "type": "text", "short": "ชื่อที่แสดง" },
            { "name": "Email", "type": "text", "short": "email" },
            { "name": "Inactive", "type": "bool", "short": "true = ไม่นับ" },
            { "name": "LastSyncedAt", "type": "timestamptz", "short": "sync เขียนล่าสุดเมื่อ" }
          ]
        },
        {
          "kind": "table",
          "id": "sync_run",
          "rowMeaning": "1 แถว = sync รัน 1 รอบ",
          "purpose": "บันทึกแต่ละรอบที่ sync รัน; ตาราง raw ทุกตัวชี้มาที่นี่",
          "columns": [
            { "name": "RunId", "type": "bigint", "key": "PK", "short": "เลข run" },
            { "name": "Mode", "type": "text", "short": "hourly / rebuild" },
            { "name": "StartedAt", "type": "timestamptz", "short": "เวลาเริ่ม" },
            { "name": "FinishedAt", "type": "timestamptz", "short": "เวลาจบ" },
            { "name": "Status", "type": "text", "short": "running / succeeded / failed" }
          ]
        }
      ]
    },
    {
      "id": "crm",
      "title": "CRM",
      "subtitle": "ที่ทีมขายใช้",
      "boxes": [
        {
          "kind": "table",
          "id": "crm_order",
          "rowMeaning": "1 แถว = order row ของ 1 order",
          "purpose": "order row ใน CRM ที่ทีมขายใช้ตามงาน; sync เป็นคนเขียนแถวนี้",
          "columns": [
            { "name": "crm_shoporderid", "type": "text", "key": "AK", "short": "เลข order ของร้าน (ใช้หาแถว)" },
            { "name": "crm_status", "type": "choice", "short": "สถานะ order" },
            { "name": "crm_customername", "type": "text", "short": "ชื่อลูกค้า" },
            { "name": "crm_customeremail", "type": "text", "short": "email ลูกค้า" },
            { "name": "crm_bookcount", "type": "int", "short": "จำนวนหนังสือที่ยังไม่ถูกลบ" }
          ],
          "footnotes": ["แสดงเฉพาะคอลัมน์ที่ sync เขียน", "AK = alternate key"]
        }
      ]
    }
  ],
  "lines": [
    { "kind": "flow", "from": { "box": "OrdersChanged" }, "to": { "box": "raw_orders" }, "label": "Land",
      "tooltip": "Land: ทุก record ที่อ่านจาก OrdersChanged ถูกเพิ่มลง shop_raw.raw_orders หนึ่งแถว (ไม่แก้ ไม่ลบ)", "mult": ["1", "*"] },
    { "kind": "flow", "from": { "box": "OrderLinesChanged" }, "to": { "box": "raw_order_lines" }, "label": "Land",
      "tooltip": "Land: ทุก record ที่อ่านจาก OrderLinesChanged ถูกเพิ่มลง shop_raw.raw_order_lines หนึ่งแถว", "mult": ["1", "*"] },
    { "kind": "flow", "from": { "box": "Deletions" }, "to": { "box": "raw_deletions" }, "label": "Land",
      "tooltip": "Land: ทุก record ที่อ่านจาก Deletions ถูกเพิ่มลง shop_raw.raw_deletions หนึ่งแถว", "mult": ["1", "*"] },
    { "kind": "flow", "from": { "box": "Customers" }, "to": { "box": "raw_customers" }, "label": "Land",
      "tooltip": "Land: ทุก record ที่อ่านจาก Customers ถูกเพิ่มลง shop_raw.raw_customers หนึ่งแถว", "mult": ["1", "*"] },
    { "kind": "same-value", "from": { "box": "raw_orders", "column": "SourceId" }, "to": { "box": "order", "column": "OrderId" },
      "label": "SourceId = OrderId", "tooltip": "raw_orders → order: หลายแถว raw (อ่านหลายครั้ง) เป็นของ order เดียว; ไม่มี FK", "mult": ["*", "1"] },
    { "kind": "same-value", "from": { "box": "raw_order_lines", "column": "SourceId" }, "to": { "box": "order_line", "column": "LinePk" },
      "label": "SourceId = LinePk (PK)", "tooltip": "raw_order_lines → order_line: เลข line = LinePk; หลายแถว raw ต่อ 1 line",
      "mult": ["*", "1"], "highlight": { "kind": "change", "note": "เลข line เป็น primary key แล้ว: 1 line มีแถวเดียว" } },
    { "kind": "same-value", "from": { "box": "raw_deletions", "column": "SourceId" }, "to": { "box": "order_line", "column": "LinePk" },
      "label": "line: SourceId = LinePk", "tooltip": "raw_deletions (Entity line) → order_line: หาแถวด้วยเลข line แล้วตั้ง DeletedInShop = true ที่แถวนั้นแถวเดียว", "mult": ["*", "0..1"] },
    { "kind": "same-value", "from": { "box": "raw_deletions", "column": "SourceId" }, "to": { "box": "order", "column": "OrderId" },
      "label": "order: SourceId = OrderId", "tooltip": "raw_deletions (Entity order) → order: SourceId = OrderId แล้วตั้ง DeletedInShop = true", "mult": ["*", "0..1"] },
    { "kind": "same-value", "from": { "box": "raw_customers", "column": "SourceId" }, "to": { "box": "customer", "column": "CustomerId" },
      "label": "SourceId = CustomerId", "tooltip": "raw_customers → customer: SourceId = CustomerId", "mult": ["*", "1"] },
    { "kind": "fk", "from": { "box": "raw_orders", "column": "SyncRunId" }, "to": { "box": "sync_run", "column": "RunId" },
      "label": "FK: SyncRunId = RunId", "tooltip": "ตาราง raw ทุกตัว → sync_run: SyncRunId = RunId; หลายแถว raw ต่อ 1 run; FK จริงชุดเดียวใน database", "mult": ["*", "1"] },
    { "kind": "fk", "from": { "box": "raw_order_lines", "column": "SyncRunId" }, "to": { "box": "sync_run", "column": "RunId" },
      "label": "FK: SyncRunId = RunId", "tooltip": "raw_order_lines → sync_run: SyncRunId = RunId", "mult": ["*", "1"] },
    { "kind": "fk", "from": { "box": "raw_deletions", "column": "SyncRunId" }, "to": { "box": "sync_run", "column": "RunId" },
      "label": "FK: SyncRunId = RunId", "tooltip": "raw_deletions → sync_run: SyncRunId = RunId", "mult": ["*", "1"] },
    { "kind": "fk", "from": { "box": "raw_customers", "column": "SyncRunId" }, "to": { "box": "sync_run", "column": "RunId" },
      "label": "FK: SyncRunId = RunId", "tooltip": "raw_customers → sync_run: SyncRunId = RunId", "mult": ["*", "1"] },
    { "kind": "same-value", "from": { "box": "order", "column": "OrderId" }, "to": { "box": "order_line", "column": "OrderId" },
      "label": "OrderId", "tooltip": "order → order_line: 1 order มีได้หลาย line; เชื่อมด้วย OrderId (ไม่มี FK, มี index)", "mult": ["1", "*"] },
    { "kind": "same-value", "from": { "box": "customer", "column": "CustomerId" }, "to": { "box": "order", "column": "CustomerId" },
      "label": "CustomerId", "tooltip": "customer → order: ลูกค้า 1 คนมีได้หลาย order (ไม่มี FK, มี index)", "mult": ["1", "*"] },
    { "kind": "same-value", "from": { "box": "order", "column": "OrderId" }, "to": { "box": "crm_order", "column": "crm_shoporderid" },
      "label": "OrderId = crm_shoporderid", "tooltip": "order → crm_order: order หนึ่งมี order row 0 หรือ 1 แถว", "mult": ["1", "0..1"] },
    { "kind": "flow", "from": { "box": "order_line" }, "to": { "box": "crm_order" }, "label": "นับหนังสือ",
      "tooltip": "sync อ่านทุก line ของ order ที่ยังไม่ถูกลบ แล้วเขียน crm_bookcount", "mult": ["*", "1"] }
  ],
  "notes": [
    {
      "kind": "change",
      "heading": "order_line: 1 แถว = 1 line ของร้าน (key = LinePk)",
      "paragraphs": [
        "key เดิมคือ order + หนังสือ จึงเก็บ \"order O-7, หนังสือ 978-0\" ได้แถวเดียว. ถ้าร้านมีสอง line ของหนังสือเล่มเดียวกัน (L-1 และ L-2) แถวนั้นจดเลขได้อันเดียว. วันที่ร้านลบ L-2 sync จึงเอาหนังสือออกทั้งที่ L-1 ยังอยู่.",
        "key ใหม่คือ `LinePk`: ทุก line มีแถวของตัวเอง."
      ],
      "before": {
        "tag": "เดิม: 1 แถว = 1 order × 1 หนังสือ",
        "rows": "shop_raw.raw_order_lines   (มีครบทุก line)\n RawId 1 · {\"LinePk\":\"L-1\", \"OrderId\":\"O-7\", \"Isbn\":\"978-0\"}\n RawId 2 · {\"LinePk\":\"L-2\", \"OrderId\":\"O-7\", \"Isbn\":\"978-0\"}\n\nshop.order_line   (แถวเดียว จดได้ line เดียว)\n O-7 · 978-0 · LinePk L-2 · DeletedInShop true",
        "result": "ผล: crm_bookcount = 0"
      },
      "after": {
        "tag": "ใหม่: 1 แถว = 1 line (PK = LinePk)",
        "rows": "shop.order_line\n LinePk · OrderId · Isbn  · DeletedInShop\n L-1    · O-7     · 978-0 · false\n L-2    · O-7     · 978-0 · true",
        "result": "ผล: crm_bookcount = 1 (L-1 ยังอยู่)"
      },
      "status": "ตัวอย่างที่แต่งขึ้นสำหรับ skill `er-diagram`; ไม่มีระบบจริง."
    }
  ]
}
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: 63 tests, `OK`. If `test_example_lays_out_with_no_overlap` fails, print `layout(example()).errors`. First decide whether the overlap breaks a rule of spec section 5 (then fix `layout.py` and add a test for that case to `test_layout_routes.py`); only an overlap that the rules allow is fixed in the example, by the order of lines or boxes or a shorter label, as the skill tells agents to do.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/skills/er-diagram/assets/example-bookshop.er.json plugins/dev-workflows/skills/er-diagram/tests/test_example.py
git commit -m "feat(er-diagram): made-up Bookshop order sync example, clean check and layout (ADR 0409)"
```

---

### Task 9: The command-line entry

**Files:**
- Create: `.../er-diagram/scripts/er_diagram.py`
- Test: `.../er-diagram/tests/test_cli.py`

**Interfaces:**
- Consumes: `erlib.model.load/dump/boxes`, `erlib.check.check`, `erlib.layout.layout`, `erlib.svg.draw_svg/check_svg`, `erlib.page.build_page/extract_model`.
- Produces: `python scripts/er_diagram.py build <model.json> --out <page.html>` (writes the page and `<page>.check.svg`; prints `page: ...`, `check svg: ...`, `<n> tiers, <n> tables, <n> endpoints, <n> lines`, one `  TBD <warning>` line each, `<n> TBD`; exit 0) or prints `<n> error(s); no page written:` and one `  ERROR <error>` line each (exit 1); `python scripts/er_diagram.py extract <page.html> --out <model.json>` (exit 0). Exit 2 when a file cannot be read.

- [ ] **Step 1: Write the failing tests**

`.../er-diagram/tests/test_cli.py`:
```python
"""Tests for scripts/er_diagram.py (spec section 2, steps 2 and 4)."""
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

from helpers import EXAMPLE, SKILL, example, small_model
from erlib.model import dump, load

SCRIPT = os.path.join(SKILL, "scripts", "er_diagram.py")


def run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, encoding="utf-8")


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_build_writes_the_page_and_the_check_svg_and_lists_tbd(self):
        out = os.path.join(self.tmp, "page.html")
        p = run("build", EXAMPLE, "--out", out)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertTrue(os.path.exists(out))
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "page.check.svg")))
        self.assertIn("4 tiers, 9 tables, 4 endpoints, 17 lines", p.stdout)
        self.assertIn("  TBD order.Status: desc TBD", p.stdout)
        self.assertIn("1 TBD", p.stdout)

    def test_build_with_errors_writes_no_page(self):
        m = small_model()
        m["lines"][1]["mult"] = ["*", ""]
        src = os.path.join(self.tmp, "bad.json")
        dump(m, src)
        out = os.path.join(self.tmp, "bad.html")
        p = run("build", src, "--out", out)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)
        self.assertFalse(os.path.exists(out))
        self.assertIn("  ERROR line r1→c1: no multiplicity at end c1", p.stdout)

    def test_extract_gives_back_the_same_model(self):
        out = os.path.join(self.tmp, "page.html")
        self.assertEqual(run("build", EXAMPLE, "--out", out).returncode, 0)
        back = os.path.join(self.tmp, "back.json")
        p = run("extract", out, "--out", back)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(load(back), example())

    def test_a_missing_model_file_exits_2(self):
        p = run("build", os.path.join(self.tmp, "none.json"), "--out", os.path.join(self.tmp, "x.html"))
        self.assertEqual(p.returncode, 2)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the tests to see them fail**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: 3 CLI tests FAIL (the script does not exist: Python returns 2, `can't open file`). `test_a_missing_model_file_exits_2` passes already, for that same reason; it guards the real exit 2 once the script exists.

- [ ] **Step 3: Write `er_diagram.py`**

`.../er-diagram/scripts/er_diagram.py`:
```python
#!/usr/bin/env python3
"""er-diagram: check, lay out and draw a tiered ER page from an ER model, or take the model back
out of a page (ADRs 0398-0409).

Usage:
  python er_diagram.py build <model.json> --out <page.html>
  python er_diagram.py extract <page.html> --out <model.json>

Exit codes: 0 done (TBD warnings may be printed), 1 errors in the model (no page written),
2 cannot run (a file cannot be read).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from erlib import model as er_model  # noqa: E402
from erlib.check import check  # noqa: E402
from erlib.layout import layout  # noqa: E402
from erlib.page import build_page, extract_model  # noqa: E402
from erlib.svg import check_svg, draw_svg  # noqa: E402


def _write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def cmd_build(args):
    try:
        model = er_model.load(args.model)
    except (OSError, ValueError) as e:
        print(f"cannot read {args.model}: {e}", file=sys.stderr)
        return 2
    errors, warnings = check(model)
    lay = None
    if not errors:
        lay = layout(model)
        errors = lay.errors
    if errors:
        print(f"{len(errors)} error(s); no page written:")
        for e in errors:
            print(f"  ERROR {e}")
        return 1
    svg = draw_svg(lay, model)
    check_path = os.path.splitext(args.out)[0] + ".check.svg"
    _write(args.out, build_page(model, svg))
    _write(check_path, check_svg(svg))
    kinds = [b["kind"] for _, b in er_model.boxes(model)]
    print(f"page: {args.out}")
    print(f"check svg: {check_path}")
    print(f"{len(model['tiers'])} tiers, {kinds.count('table')} tables, "
          f"{kinds.count('endpoint')} endpoints, {len(model.get('lines', []))} lines")
    for w in warnings:
        print(f"  TBD {w}")
    print(f"{len(warnings)} TBD")
    return 0


def cmd_extract(args):
    try:
        with open(args.page, encoding="utf-8") as f:
            model = extract_model(f.read())
    except (OSError, ValueError) as e:
        print(f"cannot extract the ER model from {args.page}: {e}", file=sys.stderr)
        return 2
    er_model.dump(model, args.out)
    print(f"model: {args.out}")
    return 0


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Draw a tiered ER page from an ER model, or take the model back out.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    build = sub.add_parser("build", help="check the model, then write the page and its .check.svg")
    build.add_argument("model")
    build.add_argument("--out", required=True)
    extract = sub.add_parser("extract", help="take the ER model out of a page")
    extract.add_argument("page")
    extract.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    return cmd_build(args) if args.cmd == "build" else cmd_extract(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests to see them pass**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: 67 tests, `OK`.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/skills/er-diagram/scripts/er_diagram.py plugins/dev-workflows/skills/er-diagram/tests/test_cli.py
git commit -m "feat(er-diagram): build and extract commands; errors write no page, TBDs are listed (ADRs 0399, 0405)"
```

---

### Task 10: PNG render and the look check

**Files:**
- Create: `.../er-diagram/scripts/render_png.js`

**Interfaces:**
- Consumes: the `.check.svg` that `build` writes.
- Produces: `node scripts/render_png.js <in.svg> <out.png>`: exit 0 and prints the PNG path; exit 2 with `no PNG renderer: ...` when `@resvg/resvg-js` cannot be loaded.

- [ ] **Step 1: Write the script**

`.../er-diagram/scripts/render_png.js`:
```js
#!/usr/bin/env node
// SVG to PNG for the er-diagram look check (ADR 0406). Usage: node render_png.js <in.svg> <out.png>
// Needs @resvg/resvg-js (2.6.2 tested): npm install it in a temporary folder and set NODE_PATH
// to that folder's node_modules. Exit 2 when it is missing: the agent then reports
// "not checked by eye: no PNG renderer".
const fs = require('fs');

let Resvg;
try {
  ({ Resvg } = require('@resvg/resvg-js'));
} catch (e) {
  console.error('no PNG renderer: @resvg/resvg-js is not installed. Run "npm install @resvg/resvg-js@2.6.2" ' +
    'in a temporary folder and set NODE_PATH to its node_modules.');
  process.exit(2);
}

const [inPath, outPath] = process.argv.slice(2);
if (!inPath || !outPath) {
  console.error('usage: node render_png.js <in.svg> <out.png>');
  process.exit(2);
}
const svg = fs.readFileSync(inPath, 'utf8');
const png = new Resvg(svg, {
  fitTo: { mode: 'width', value: 2000 },
  font: { loadSystemFonts: true, defaultFontFamily: 'Tahoma' },
}).render().asPng();
fs.writeFileSync(outPath, png);
console.log(outPath);
```

- [ ] **Step 2: Check the missing-module path**

Run (PowerShell): `Remove-Item Env:NODE_PATH -ErrorAction SilentlyContinue; node plugins/dev-workflows/skills/er-diagram/scripts/render_png.js x.svg x.png; $LASTEXITCODE`
Expected: `no PNG renderer: ...` and `2`.

- [ ] **Step 3: Install the renderer in a temporary folder** (outside the repo; use the session scratchpad)

Run (PowerShell):
```powershell
$r = Join-Path $env:TEMP 'er-diagram-resvg'
New-Item -ItemType Directory -Force $r | Out-Null
npm install --prefix $r @resvg/resvg-js@2.6.2
$env:NODE_PATH = Join-Path $r 'node_modules'
```
Expected: `added ... packages`. If the install fails (no network, policy), write that down for the report and skip Step 4: the skill then reports "not checked by eye".

- [ ] **Step 4: Build the example, render it, and look at it**

Run (PowerShell, same session as Step 3):
```powershell
$o = Join-Path $env:TEMP 'er-diagram-example'
New-Item -ItemType Directory -Force $o | Out-Null
python plugins/dev-workflows/skills/er-diagram/scripts/er_diagram.py build plugins/dev-workflows/skills/er-diagram/assets/example-bookshop.er.json --out "$o\bookshop.html"
node plugins/dev-workflows/skills/er-diagram/scripts/render_png.js "$o\bookshop.check.svg" "$o\bookshop.png"
```
Expected: `1 TBD` from `build`, then the PNG path. Open `bookshop.png` with the image reader and check, item by item: four tier bands with titles; 4 endpoints level with their raw tables and straight "Land" arrows; 9 tables with every column, type, key and short description; the FK bus from the 4 raw tables into `sync_run.RunId` with one label; the two lines from `raw_deletions.SourceId` spread, with one `*`; the green border on `order_line`, green `LinePk` row and green line `SourceId = LinePk (PK)`; the two inside-tier lines in the `shop` tier with their labels; the `crm_order` footnotes; no text on text, no text on a line. Write down each fault found. A fault in the layout rules is fixed in `layout.py` with a new test; then run all tests and this step again.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/skills/er-diagram/scripts/render_png.js
git commit -m "feat(er-diagram): PNG render for the look check with resvg-js; plain exit 2 when it is missing (ADR 0406)"
```

---

### Task 11: SKILL.md, the model contract, the command

**Files:**
- Create: `.../er-diagram/SKILL.md`
- Create: `.../er-diagram/references/er-model.md`
- Create: `plugins/dev-workflows/commands/er-diagram.md`

**Interfaces:**
- Consumes: the commands and file names of Tasks 7-10.
- Produces: the skill an agent loads.

- [ ] **Step 1: Write `SKILL.md`**

`.../er-diagram/SKILL.md`:
~~~markdown
---
name: er-diagram
description: "Make or update a tiered ER page of a real system's data: one tier per system (an API, database schemas, Dataverse or a CRM), every table and column with type, key and short description, what one row means, an (i) purpose tooltip on each table, and every relationship line with a label, a tooltip and both multiplicities (real foreign keys solid, same-value joins dashed, data flows as arrows), problem and change highlights, light and dark. The agent writes one ER model (JSON); a bundled script lays it out, draws and checks the page, and the model is kept inside the published page, so a later update starts from the link. Use when the user says ทำ ER diagram, วาด ER diagram ของ, ER diagram ของตาราง, data model page, ข้อมูลเก็บที่ไหนบ้าง, tiered ER diagram, update the ER page, แก้ ER page. Do NOT use for a full SA&D document (sa-doc), for a problem explained step by step even when it shows tables (problem-description), or for a diagram that is not tables and their relationships (answer it directly)."
effort: max
---

# ER diagram

One page that shows where a system keeps its data: every table and column, what one row means,
what each table is for, and how the tables join, across systems. You write the content as an
**ER model**; `scripts/er_diagram.py` places, draws and checks. You never write a coordinate.

## The one rule: Source-or-TBD

Every name, type, key, description, row meaning, purpose and tooltip comes from a source you
read. When no source states it, write `TBD`, never a plausible value. The build lists every `TBD`
before you publish, and the user decides.

## Steps

1. **Pick the mode.** A link to a published ER page, a page title, or a path to a page in
   `docs/er-diagram/` means **update**. Anything else is a **new** page.
2. **Get the facts (new) or the model (update).**
   - New: read the sources in this order. (a) The schema in the open project: EF model builder,
     entity classes, migrations, SQL DDL - names, types, keys, foreign keys, indexes. (b) No
     schema there and the system is Dataverse: its table metadata through the Web API, read-only.
     (c) Neither: ask the user where the schema is. A fact that is only in a live database: ask
     the user first; then read the schema only, read-only, never row data. Descriptions, row
     meanings, purposes and tooltips come from ADRs, tickets and docs.
   - Update: get the page (the published page by its link or title, or the local file) and run
     `python scripts/er_diagram.py extract <page.html> --out <work>/model.json`. The model is
     found anywhere in the file, also behind a host's wrapper.
3. **Write or change the ER model** in a temporary work folder, following
   `references/er-model.md`. On an update, change only what changed and keep the order.
4. **Build:** `python scripts/er_diagram.py build <work>/model.json --out <work>/<topic>.html`.
   Exit 1 lists every error with the item name and writes no page: fix the model and build again.
   Exit 0 writes the page and `<work>/<topic>.check.svg`, and lists every `TBD`.
5. **Look at it.** Run `node scripts/render_png.js <work>/<topic>.check.svg <work>/<topic>.png` and
   look at the PNG: every tier, table, column and line there, nothing on top of anything. Fix a
   fault in the model - the order of tiers, boxes or lines, or a shorter label - never with a
   coordinate, and go back to step 4. If the script exits 2 (no renderer), run
   `npm install @resvg/resvg-js@2.6.2` in a temporary folder and set `NODE_PATH` to its
   `node_modules`; if that fails, go on and say "not checked by eye: no PNG renderer" in the report.
6. **TBD.** If the build listed any `TBD`, show the list to the user and ask: publish now, or give
   the facts first.
7. **Publish.** If your harness can publish an HTML page as a shareable artifact, publish the page
   there and follow that mechanism's own rules (for example, a required first-step call before a
   new artifact, or reading the published version before an update). On an update, publish to the
   same place. With no such mechanism, save the page to `<open project>/docs/er-diagram/<topic>.html`
   (create the folder) and give its full path; an update then starts from that file. `<topic>` is
   a lowercase-kebab name from `page.title`.
8. **Report.** The link or path; the counts the build printed (tiers, tables, endpoints, lines);
   every `TBD` left; whether you looked at the PNG; where each part came from (code file,
   metadata, ADR, ticket).

## What you control in the picture

- The order of `tiers` (left to right), of `boxes` in a tier (top to bottom), and of `lines`.
  A box is placed level with the box its **first** line joins in the next tier on its right, so
  put the line that should decide a box's height first.
- Label texts: short labels fit better.
- Nothing else. Positions, lanes, the FK bus, label columns and multiplicity places are computed
  (spec rules in `references/er-model.md`).

## Kinds (fixed)

| Kind | Drawn as | Use for |
|---|---|---|
| `table` | box with columns | a database table |
| `endpoint` | box with an accent border and 1-2 text lines | a source that is not a table: an API, a file, a queue |
| `fk` | solid line | a real foreign key in the database |
| `same-value` | dashed line | the same value joins two tables, no foreign key |
| `flow` | accent arrow with a bold label | data moves or is computed, not a key |

Highlights: `problem` (red-orange) and `change` (green), on a table, a column or a line, each
with a `note` that goes into the tooltip. A new kind is a change to this skill, never a one-page
invention.

## Files

- `scripts/er_diagram.py` - `build`, `extract`.
- `scripts/render_png.js` - the PNG for step 5.
- `references/er-model.md` - the ER model contract.
- `assets/example-bookshop.er.json` - a whole worked model (made up) to copy patterns from.
- `assets/er-page-template.html` - the page shell; do not edit it per page.
~~~

- [ ] **Step 2: Write the model contract**

`.../er-diagram/references/er-model.md`:
~~~markdown
# The ER model - contract

The one JSON file the agent writes for a tiered ER page (ADR 0398). This file is the only place
its schema is defined. `assets/example-bookshop.er.json` is a whole worked model.

Write it one key per line (indent 2), UTF-8. `scripts/er_diagram.py build` checks it before it
draws anything.

## Shape

```json
{
  "erModel": 1,
  "page": { "title": "...", "eyebrow": "...", "heading": "...", "intro": "...", "lang": "th" },
  "overview": { "heading": "...", "text": "...", "mermaid": "flowchart LR\n ..." },
  "diagram": { "heading": "...", "text": "..." },
  "tiers": [ { "id": "...", "title": "...", "subtitle": "...", "boxes": [ ... ] } ],
  "lines": [ { "kind": "same-value", "from": { "box": "a", "column": "X" }, "to": { "box": "b", "column": "Y" },
               "label": "X = Y", "tooltip": "...", "mult": ["*", "1"] } ],
  "notes": [ { "kind": "change", "heading": "...", "paragraphs": ["..."],
               "before": { "tag": "...", "rows": "...", "result": "..." },
               "after": { "tag": "...", "rows": "...", "result": "..." }, "status": "..." } ]
}
```

## Fields

| Object | Required | Optional |
|---|---|---|
| `page` | `title` (2-4 words, the browser tab), `heading`, `lang` (`th` or `en`: the language of the legend) | `eyebrow`, `intro` |
| `overview` | - (the whole object is optional) | `heading`, `text`, `mermaid` |
| `diagram` | - | `heading`, `text` |
| tier | `id`, `title`, `boxes` (at least one) | `subtitle` |
| table box | `kind: "table"`, `id`, `rowMeaning` ("1 แถว = ..."), `purpose`, `columns` (at least one) | `footnotes` (short lines in the box), `highlight` |
| endpoint box | `kind: "endpoint"`, `id`, `lines` (1 or 2) | `purpose`, `highlight` |
| column | `name`, `type`, `short` | `key` (`PK`, `FK`, `AK`, `IX`, `UQ`), `desc` (the tooltip; `short` when absent), `highlight` |
| line | `kind` (`fk`, `same-value`, `flow`), `from`, `to`, `label`, `tooltip`, `mult` (two of `1`, `0..1`, `*`, `1..*`: the `from` end, then the `to` end) | `highlight` |
| line end | `box` | `column` (required for `fk` and `same-value`; a `flow` end without one attaches at the middle of the box) |
| highlight | `kind` (`problem`, `change`), `note` | - |
| note section | `kind` (`problem`, `change`), `heading`, `paragraphs` | `before`, `after` (each `tag`, `rows`, `result`), `status` |

- A box `id` is the name drawn on the box; it is unique in the model.
- `fk` and `same-value` join two tables; `flow` joins any two boxes.
- Any text may be `TBD` except `page.title`, `page.heading`, `page.lang`, ids, kinds, keys and
  multiplicities. Every `TBD` is listed before publishing.
- Text is plain. In `intro`, `text`, `paragraphs`, `status` and `result`, `` `x` `` becomes code
  and `**x**` becomes bold. `rows` is shown as it is, in a monospace box. No HTML.

## Errors (no page is written)

1. A kind, key or multiplicity not in the lists above.
2. A missing required field; a box id used twice.
3. A line end that names a box or column not in the model; an `fk` or `same-value` end with no
   column, or on an endpoint.
4. A table without `rowMeaning` or `purpose`.
5. A line without `label`, `tooltip`, or both `mult` values.
6. A highlight without a `note`.
7. A label or multiplicity that still overlaps something after the layout has widened the gap 20
   times: change the order or the label.

## How the script places things

1. Tiers left to right in model order; boxes top to bottom in model order, 18 px apart.
2. A box is centred level with the box its first line (model order) joins in the next tier on its
   right, when that place is free; otherwise it goes below the box above it.
3. Tables of one tier share one width and column starts.
4. Lines between neighbouring tiers: out of the right edge of the left box, in a lane of the gap,
   into the left edge of the right box, at the rows of their columns. Lanes are shared only when
   the lines do not overlap. Lines on one row are spread over it.
5. Two or more `fk` lines into one column from one tier share one bus.
6. Lines inside one tier use lanes at the right edge of that tier; lines across several tiers go
   round the boxes between.
7. Labels sit above the last segment, right of all lanes (below it for the lowest of several lines
   into one row). Multiplicities sit at each end; one row's ends with the same text share one.
~~~

- [ ] **Step 3: Write the command**

`plugins/dev-workflows/commands/er-diagram.md`:
```markdown
---
description: Make or update a tiered ER page of a system's data - every table and column, what one row means, purpose tooltips, every relationship with label and both multiplicities - from one ER model that a bundled script lays out, draws and checks; the model rides inside the published page so an update starts from the link.
argument-hint: "[the system, schema or tables to draw - or the link of an ER page to update]"
---

Use the **`er-diagram`** skill to make or update the ER page.

Argument: $ARGUMENTS
```

- [ ] **Step 4: Check the paths the skill names exist**

Run (PowerShell): `'scripts/er_diagram.py','scripts/render_png.js','references/er-model.md','assets/example-bookshop.er.json','assets/er-page-template.html' | ForEach-Object { "$_ " + (Test-Path "plugins/dev-workflows/skills/er-diagram/$_") }`
Expected: every line ends with `True`.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/skills/er-diagram/SKILL.md plugins/dev-workflows/skills/er-diagram/references/er-model.md plugins/dev-workflows/commands/er-diagram.md
git commit -m "feat(er-diagram): the skill, the ER model contract and /dev-workflows:er-diagram (ADRs 0398-0408)"
```

---

### Task 12: Neighbours, PLAYBOOK, manifests, generated tree, final checks

**Files:**
- Modify: `plugins/dev-workflows/skills/problem-description/SKILL.md` (description line)
- Modify: `plugins/dev-workflows/skills/sa-doc/SKILL.md` (description line)
- Modify: `PLAYBOOK.md` (router edge after the `sa-doc` edge; table row after the `sa-doc` row)
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
- Regenerate: `skills/`

**Interfaces:**
- Consumes: everything above.
- Produces: the registered, installable skill.

- [ ] **Step 1: Add the "not for" clauses (ADR 0408)**

In `plugins/dev-workflows/skills/problem-description/SKILL.md`, replace
`only when an interactive HTML artifact would clearly help.`
with
`only when an interactive HTML artifact would clearly help. Not for an ER page of a system's tables and their relationships (er-diagram).`

In `plugins/dev-workflows/skills/sa-doc/SKILL.md`, replace
`Do NOT use for a single ad-hoc diagram, for explaining a problem interactively (problem-description), or for reviewing an existing document (scrutinize).`
with
`Do NOT use for a single ad-hoc diagram, for a single ER page of a system's tables (er-diagram), for explaining a problem interactively (problem-description), or for reviewing an existing document (scrutinize).`

- [ ] **Step 2: Add the PLAYBOOK edge and row**

In `PLAYBOOK.md`, after the line
`    WORK -- need a full SA/design document --> SAD["sa-doc"]`
add
`    WORK -- need an ER page of a system's tables --> ERD["er-diagram<br/>(/dev-workflows:er-diagram)"]`

After the row
`| need a full SA&D document (use cases, diagrams, data dictionary) | \`sa-doc\` |`
add
`| need an ER page of a system's tables - every table and column, what one row means, every relationship with both multiplicities, across systems; update it later from its link | \`er-diagram\` (\`/dev-workflows:er-diagram\`) |`

- [ ] **Step 3: Update both manifests, in the same way**

Find the version to use: `git log --all --format=%H -- plugins/dev-workflows/.claude-plugin/plugin.json` then read the highest `"version"` on any branch (`git show <hash>:plugins/dev-workflows/.claude-plugin/plugin.json | Select-String '"version"'` per hash). The new version is that maximum + 0.1.0 (from `0.70.0` it is `0.71.0`).

In both `plugins/dev-workflows/.claude-plugin/plugin.json` and the `dev-workflows` entry of `.claude-plugin/marketplace.json`:
- replace the sentence
  `Documents: sa-doc (full SA&D document — use cases, diagrams, data dictionary, architecture — generated from one validated model; Markdown canonical, PDF optional).`
  with
  `Documents: sa-doc (full SA&D document — use cases, diagrams, data dictionary, architecture — generated from one validated model; Markdown canonical, PDF optional). er-diagram (/dev-workflows:er-diagram - a tiered ER page of a real system's data from one ER model: every table and column, what one row means, purpose tooltips, every relationship with a label and both multiplicities, problem and change highlights; a bundled script lays it out, draws and checks it, and the model rides inside the published page so an update starts from the link; ADRs 0398-0409).`
- set `"version"` of `dev-workflows` to the new version (only the `dev-workflows` entry in `marketplace.json`).

In `plugin.json` only, after `"thinking-tricks"` in `keywords`, add `"er-diagram"`, `"entity-relationship"`, `"data-model"`, `"schema-diagram"`, `"tiered-diagram"` (keep the JSON valid: a comma after `"thinking-tricks"`).

Run: `python -c "import json; [json.load(open(p, encoding='utf-8')) for p in ('plugins/dev-workflows/.claude-plugin/plugin.json', '.claude-plugin/marketplace.json')]; print('json ok')"`
Expected: `json ok`.

- [ ] **Step 4: Regenerate and check the generated tree**

Run: `python scripts/generate_skills_tree.py` then `python scripts/check_skills_tree.py`
Expected: the check exits 0. Then `git status --short -- skills/er-diagram skills/problem-description skills/sa-doc` shows the new `skills/er-diagram/` and the two changed `SKILL.md` files; `git diff --stat -- skills/problem-description/SKILL.md skills/sa-doc/SKILL.md` shows 1 line changed in each (line-ending noise shows no lines).

- [ ] **Step 5: Run every test once more**

Run: `python -m unittest discover -s plugins/dev-workflows/skills/er-diagram/tests -v`
Expected: 67 tests, `OK`.

- [ ] **Step 6: Look at the staged diff for client data, then commit**

```bash
git add plugins/dev-workflows/skills/problem-description/SKILL.md plugins/dev-workflows/skills/sa-doc/SKILL.md PLAYBOOK.md plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json skills/er-diagram skills/problem-description/SKILL.md skills/sa-doc/SKILL.md
git diff --cached --stat
```
Read the staged diff and the whole branch diff (`git diff main --stat`) for any client schema, client names or client ticket numbers (Global Constraints). Then:
```bash
git commit -m "feat(er-diagram): register the skill: neighbour clauses, PLAYBOOK row and edge, dev-workflows 0.71.0, generated tree (ADRs 0407, 0408)"
```
(If Step 3 found a higher version on another branch, write that version + 0.1.0 instead of `0.71.0`, in the manifests and here.)

- [ ] **Step 7: Install the live copies** (not automatic; the live skills are plain copies)

Run (PowerShell):
```powershell
foreach ($s in 'er-diagram','problem-description','sa-doc') {
  $dst = Join-Path $HOME ".claude\skills\$s"
  if (Test-Path $dst) { Remove-Item -Recurse -Force $dst }
  Copy-Item -Recurse "skills\$s" $dst
}
Get-ChildItem "$HOME\.claude\skills\er-diagram" -Recurse -File | Measure-Object | Select-Object -ExpandProperty Count
```
Expected: the file count of `skills/er-diagram` (no `__pycache__`).

- [ ] **Step 8: The end-to-end checks of spec section 11 that are not unit tests**

1. **Publish and update from the link.** Build the Bookshop example, publish it (step 7 of the skill), then in a **new session** with no local file: ask for "update the ER page <link>: add column `Note text` to `customer`". Expected: `extract` gives back the published model, the build passes, the page is published to the same link, and the new column shows.
2. **Light and dark.** Open the published page in light and in dark: every tier, box, line and highlight readable in both.
3. **The client page, on Pon's PC only (ADR 0409).** Run the skill on the client project the hand-drawn page came from (the reference folder named in the session handoff); write the model into that folder, never into a repo. Expected: the build passes; the PNG shows every table, column and line of the hand-drawn page. Report the result as counts and pass/fail only, without the client's data.

Write the results of 1-3 into the report to Pon. A failure is fixed with a test first, then this step again.
