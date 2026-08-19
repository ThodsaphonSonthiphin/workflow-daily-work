# Decision-map Milestones and Readability Implementation Plan

> **SUPERSEDED IN PART — implemented, then corrected by the final fix wave**
> (commits `4602667`, `7870ddd`, `d5208e1`, `fb0d26e`, and the residual
> correction `f77ded8`).
> Every task below shipped. Five details this plan specifies are no longer
> true of the code, so do not regenerate requirements from them:
>
> - `milestone_line` now **strips** the label (this plan's version did not, so
>   a padded label broke the byte-identical no-op on the first re-chart);
> - `merge_milestones` resolves a duplicated stored slug **first**-wins, like
>   every projection, and dedupes the stored order before comparing it;
> - `milestone_progress` counts **distinct** members, and `lint` names a key
>   repeated inside one milestone;
> - the member-union plan detail reads `adds 1 ticket to an existing
>   milestone`, not `adds 1 milestone member line` — the union edits a stored
>   line rather than adding one;
> - the GitHub `Snapshot` discards the unparsable milestone lines as `_`
>   rather than storing them in `_bad_milestone_lines`, which nothing read.
>
> ADR 0102 is also restated correctly in the contract: a new ticket renders
> its Question **above** the position diagram, i.e. the diagram sits *below*
> `## Question`.

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give a decision map an ordering dimension — named, ordered milestones grouping its tickets — and make the map document and ticket cards readable, so a session can see what ships first instead of re-deciding it every time.

**Architecture:** Two new tool-owned marker regions on the map document (`decision-map:milestones` and `decision-map:notes`) carry the whole feature; all grammar, merge, projection and lint logic lands in `map_core.py` so both shipping backends answer identically, and each backend only wires its own read/plan/render paths to the shared functions. Everything stays additive: `chart` appends milestones and unions members, reports anything divergent, and never removes — moves and reorders are hand edits, exactly as fog-line deletion already is.

**Tech Stack:** Python 3 stdlib only (`re`, `json`, `pathlib`, `unittest`), `pytest` as the runner, `gh` CLI for the GitHub backend (mocked in tests by `fake_github.py`).

**Spec:** The ADR set written in the grilling session that preceded this plan — all in `docs/adr/`:

- `workflow-daily-work-0094` — ordering intent is milestone grouping, not per-ticket priority
- `workflow-daily-work-0095` — a milestone is first-class structure, not a task-ticket emulation
- `workflow-daily-work-0096` — membership and order live on the map, in one generated region
- `workflow-daily-work-0097` — a ticket belongs to at most one milestone, the first that needs it
- `workflow-daily-work-0098` — declared additively through `chart`; moves and reorders are hand edits
- `workflow-daily-work-0099` — the session surface groups the frontier by milestone and recommends into the nearest one
- `workflow-daily-work-0100` — offered at chart time and once per session on a big unmilestoned map
- `workflow-daily-work-0101` — map Notes become an append-only bullet region; the Destination stays one line
- `workflow-daily-work-0102` — a new ticket renders its Question above the position diagram
- `workflow-daily-work-0103` — the decisions index groups by milestone, matching the frontier

Read also `plugins/decision-map/references/data-contracts.md` (the contract both backends answer to) and `CONTEXT.md`'s **Milestone** term.

## Global Constraints

- **Python 3 stdlib only.** No new dependencies in any script under `plugins/decision-map/scripts/`.
- **Run every test from `plugins/decision-map/scripts/`**, which is where the modules import each other by bare name: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q`. Baseline on `main` at commit `27a79d7`: **238 passed, 143 subtests passed**. Every task ends with this suite green.
- **Never pipe a test run through `tail`/`head` when the exit code matters** — a pipe reports the last command's status, so a red suite reads as exit 0. Redirect to a file and check `$?` on the bare command.
- **The marker invariant is absolute.** Every user-supplied string written into a document goes through `map_core.one_line()` (flatten, then escape) or `map_core.scrub()`. Never escape before flattening. Every new paired region must be added to `MAP_REGIONS` so `assert_regions` covers it on every write.
- **Additive means union** (ADR 0057/0058): never remove, never reorder, never overwrite. Re-running identical input must be a byte-identical no-op. A value the additive path declines to apply is reported in `divergence`, never silently dropped.
- **Ordering is key-ascending on every backend** for `map.json.tickets[]` and all three `frontier.json` buckets (ADR 0062). This plan does **not** change that; milestone ordering is carried as separate data the consumer sorts by.
- **`- (none)`** (`map_core.EMPTY_LIST_LINE`) is the tool-owned placeholder for an empty list region, dropped as soon as a real line arrives.
- **Keys and milestone slugs both match** `[A-Za-z0-9][A-Za-z0-9_-]*` and **must not contain `--`** (`map_core.validate_key`) — a slug is a marker payload.
- **Line endings:** normalise to `\n` on read (`map_core.norm_eol`), write `\n`.
- **Version bump:** `plugins/decision-map/.claude-plugin/plugin.json` and the `decision-map` entry in `.claude-plugin/marketplace.json` must both report **`0.10.0`** (global max across every ref and worktree is `0.9.2` on `main`; a feature bumps the minor).
- **No new ADRs are needed for this plan** — the ten above are the decisions. If implementation forces a *new* choice, write an ADR minted from the global max (`docs/adr/`, prefix `workflow-daily-work-`).

---

## File Structure

| File | Responsibility after this plan |
|---|---|
| `plugins/decision-map/scripts/map_core.py` | **All** milestone logic: region constants, the line grammar (render + parse), the membership/progress projections, validation, the map-body render, the merge, the grouped decisions index, and the four new lint rules. Both backends call it; nothing is written twice. |
| `plugins/decision-map/scripts/local_map_ops.py` | Wires the local backend: `read_map`/`frontier` projections, the `chart` plan's new merge details, the reindex call, and the new ticket-file template. |
| `plugins/decision-map/scripts/github_map_ops.py` | The same wiring for GitHub: `Snapshot.ticket_json`/`map_json`, `frontier`, `render_ticket_issue_body`, and `_plan_map`'s scalar-field selection. |
| `plugins/decision-map/scripts/test_local_map_ops.py` | Tests for `map_core`'s pure functions (it already imports `map_core`) plus the local backend. |
| `plugins/decision-map/scripts/test_github_map_ops.py` | GitHub backend tests, against `fake_github.py`. |
| `plugins/decision-map/references/data-contracts.md` | The contract: the new regions, the `map_input.json` / `map.json` / `frontier.json` additions, the new lint rules, the new merge details. |
| `plugins/decision-map/skills/chart-map/SKILL.md` | Step 2 gains the "what ships first" question; Step 3's `map_input.json` template gains `milestones`. |
| `plugins/decision-map/skills/work-map/SKILL.md` | Step 1 renders the frontier grouped by milestone; Step 2's recommendation becomes two-level; Step 5 covers milestone graduation; the one-line offer for an unmilestoned map. |

---

### Task 1: The milestone line grammar and its projections (map_core)

Pure functions only — no backend touches them yet, so the suite must stay green
on the existing 238 tests plus the new ones.

**Files:**
- Modify: `plugins/decision-map/scripts/map_core.py` (add after the `EMPTY_LIST_LINE` block, around line 110, and after `merge_region_lines`)
- Test: `plugins/decision-map/scripts/test_local_map_ops.py`

**Interfaces:**
- Consumes: `map_core.one_line`, `map_core.region_body`, `map_core.norm_eol`, `map_core.EMPTY_LIST_LINE`
- Produces:
  - `MILESTONES_START` / `MILESTONES_END` / `NOTES_START` / `NOTES_END` — region marker strings
  - `milestone_line(slug, label, members) -> str`
  - `parse_milestones(map_text) -> (list[dict], list[str])` — `[{"slug": str, "label": str|None, "members": list[str]}]` and the raw lines that did not parse
  - `milestone_index(map_text) -> (list[dict], dict[str, str], list[str])` — the milestones, `{ticket key: milestone slug}` (first occurrence wins), and the unparsable lines
  - `milestone_progress(milestones, status_by_key) -> list[dict]` — `[{"slug","label","closed","total","complete"}]`
  - `notes_lines(value) -> list[str]`
  - `milestone_lines_for(milestones) -> list[str]`

- [ ] **Step 1: Write the failing tests**

Add to `test_local_map_ops.py`, at the end of the file:

```python
class MilestoneGrammarTest(unittest.TestCase):
    """The line grammar is the whole feature's storage format, so it must
    round-trip EXACTLY: render -> parse -> render is byte-identical, or the
    byte-identical no-op guarantee breaks on every re-chart."""

    def test_renders_slug_label_and_members(self):
        self.assertEqual(
            map_core.milestone_line("mvp-search", "demo the search page",
                                    ["auth-model", "api-limits"]),
            "- `mvp-search` demo the search page [auth-model, api-limits]")

    def test_renders_without_a_label_and_without_members(self):
        self.assertEqual(map_core.milestone_line("polish", None, []),
                         "- `polish` []")

    def test_round_trips_every_shape(self):
        # A label containing brackets is the case a naive regex gets wrong:
        # members are anchored to the END of the line and cannot contain
        # brackets, so the LAST group is unambiguously the member list.
        for slug, label, members in (
                ("mvp-search", "demo the search page", ["auth-model", "api-limits"]),
                ("polish", None, []),
                ("weird", "ship [the] thing", ["one"]),
                ("solo", "a label", []),
        ):
            line = map_core.milestone_line(slug, label, members)
            text = (map_core.MILESTONES_START + "\n" + line + "\n"
                    + map_core.MILESTONES_END)
            got, bad = map_core.parse_milestones(text)
            self.assertEqual(bad, [], line)
            self.assertEqual(len(got), 1, line)
            self.assertEqual(got[0]["slug"], slug, line)
            self.assertEqual(got[0]["label"], label, line)
            self.assertEqual(got[0]["members"], members, line)
            self.assertEqual(
                map_core.milestone_line(got[0]["slug"], got[0]["label"],
                                        got[0]["members"]),
                line)

    def test_a_label_is_flattened_and_escaped(self):
        # one_line, not raw interpolation: a newline in a label would inject a
        # second line into the region and a marker would forge a region.
        line = map_core.milestone_line(
            "m1", "one\n<!-- decision-map:fog:start -->", ["k"])
        self.assertNotIn("\n", line)
        self.assertNotIn(map_core.MARKER_PREFIX, line)

    def test_absent_region_parses_as_empty_not_as_an_error(self):
        self.assertEqual(map_core.parse_milestones("# a map with no region"),
                         ([], []))
        self.assertEqual(map_core.parse_milestones(None), ([], []))

    def test_placeholder_and_blank_lines_are_not_milestones(self):
        text = (map_core.MILESTONES_START + "\n" + map_core.EMPTY_LIST_LINE
                + "\n\n" + map_core.MILESTONES_END)
        self.assertEqual(map_core.parse_milestones(text), ([], []))

    def test_an_unparsable_line_is_reported_never_skipped(self):
        # Silently skipping it would shrink a milestone without saying so --
        # the reader sees a smaller group and believes it.
        text = (map_core.MILESTONES_START + "\n- mvp-search: auth-model\n"
                + map_core.MILESTONES_END)
        got, bad = map_core.parse_milestones(text)
        self.assertEqual(got, [])
        self.assertEqual(bad, ["- mvp-search: auth-model"])

    def test_index_maps_each_member_to_its_first_milestone(self):
        text = map_core.MILESTONES_START + "\n" + "\n".join([
            map_core.milestone_line("one", None, ["a", "b"]),
            map_core.milestone_line("two", None, ["b", "c"]),
        ]) + "\n" + map_core.MILESTONES_END
        ms, by_key, bad = map_core.milestone_index(text)
        self.assertEqual([m["slug"] for m in ms], ["one", "two"])
        # 'b' is a lint error (exclusivity), but the projection must still be
        # deterministic: the FIRST milestone that needs it wins (ADR 0097).
        self.assertEqual(by_key, {"a": "one", "b": "one", "c": "two"})
        self.assertEqual(bad, [])

    def test_progress_counts_closed_members_and_flags_completeness(self):
        ms = [{"slug": "one", "label": "first", "members": ["a", "b"]},
              {"slug": "two", "label": None, "members": ["c"]},
              {"slug": "empty", "label": None, "members": []}]
        got = map_core.milestone_progress(
            ms, {"a": "closed", "b": "open", "c": "closed"})
        self.assertEqual(got, [
            {"slug": "one", "label": "first", "closed": 1, "total": 2,
             "complete": False},
            {"slug": "two", "label": None, "closed": 1, "total": 1,
             "complete": True},
            # An empty milestone is never "complete" -- it has shipped nothing,
            # and reporting it done would send the reader to the next group.
            {"slug": "empty", "label": None, "closed": 0, "total": 0,
             "complete": False},
        ])

    def test_a_member_with_no_ticket_counts_in_total_and_never_as_closed(self):
        got = map_core.milestone_progress(
            [{"slug": "one", "label": None, "members": ["a", "ghost"]}],
            {"a": "closed"})
        self.assertEqual(got[0], {"slug": "one", "label": None, "closed": 1,
                                  "total": 2, "complete": False})

    def test_notes_lines_accepts_a_string_a_list_or_nothing(self):
        self.assertEqual(map_core.notes_lines(None), [])
        self.assertEqual(map_core.notes_lines(""), [])
        self.assertEqual(map_core.notes_lines("one thing"), ["one thing"])
        self.assertEqual(map_core.notes_lines(["a", "b"]), ["a", "b"])

    def test_milestone_lines_for_falls_back_to_the_placeholder(self):
        self.assertEqual(map_core.milestone_lines_for([]),
                         [map_core.EMPTY_LIST_LINE])
        self.assertEqual(
            map_core.milestone_lines_for(
                [{"slug": "one", "label": None, "members": ["a"]}]),
            ["- `one` [a]"])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py -k Milestone -q`
Expected: FAIL — `AttributeError: module 'map_core' has no attribute 'MILESTONES_START'`

- [ ] **Step 3: Add the constants**

In `map_core.py`, immediately after the `SCOPE_START` / `SCOPE_END` pair (around line 83):

```python
# The ordering dimension (ADR 0094-0099). A milestone is a named, ordered,
# shippable increment: the group of decision tickets that must all close before
# building that increment can begin. Membership and order live HERE, on the map,
# in one region -- not as a field on each ticket -- because "what ships first" is
# a map-level statement and declaring or regrouping N tickets would otherwise be
# N writes (ADR 0096).
MILESTONES_START = "<!-- decision-map:milestones:start -->"
MILESTONES_END = "<!-- decision-map:milestones:end -->"
# Notes is a LIST, not a paragraph (ADR 0101). Measured on a live map, its
# content was a ~450-word single line whose actual shape was a sequence of dated
# amendments -- a list forced to impersonate a paragraph.
NOTES_START = "<!-- decision-map:notes:start -->"
NOTES_END = "<!-- decision-map:notes:end -->"
```

Then extend `MAP_REGIONS` (around line 94) so `assert_regions` covers both on
every write:

```python
MAP_REGIONS = ((DECISIONS_START, DECISIONS_END),
               (NOTES_START, NOTES_END),
               (MILESTONES_START, MILESTONES_END),
               (FOG_START, FOG_END),
               (SCOPE_START, SCOPE_END))
```

- [ ] **Step 4: Add the grammar and the projections**

In `map_core.py`, after `count_added_lines` (around line 405):

```python
# The milestone line grammar. Anchored at BOTH ends, with the member list last
# and forbidden from containing brackets, so the trailing group is unambiguously
# the members even when a human's label contains brackets of its own. Order is
# LINE ORDER, never a rendered number: a numbered list would have to be
# renumbered on every insert, which is a rewrite of lines the additive
# guarantee promises never to touch.
_MILESTONE_LINE_RE = re.compile(
    r"^- `(?P<slug>[A-Za-z0-9][A-Za-z0-9_-]*)`"
    r"(?: (?P<label>.*?))? \[(?P<members>[^\[\]]*)\]$")


def milestone_line(slug, label, members):
    """One milestone as its stored line.

    `slug` and every member are validated keys (safe slugs), so they need no
    escaping -- but the LABEL is free user text and goes through one_line:
    flatten first, escape second, exactly as every other user string does. A
    newline there would inject a second line into the region; a marker there
    would forge a region.

    The slug pattern above deliberately ACCEPTS "--", matching SAFE_SLUG_RE
    rather than validate_key: the "--" rule belongs at mint time, and a reader
    that refused such a slug would turn a hand-written milestone into an
    unparsable line instead of a readable one whose slug `lint` can name. Do not
    "fix" this by tightening the pattern -- it is the same split SAFE_SLUG_RE
    already documents for ticket keys.
    """
    lab = f" {one_line(label)}" if label else ""
    return f"- `{slug}`{lab} [{', '.join(members)}]"


def milestone_lines_for(milestones):
    """The rendered lines for a milestone list, placeholder when it is empty."""
    lines = [milestone_line(m["slug"], m.get("label"), m.get("members") or [])
             for m in milestones]
    return lines or [EMPTY_LIST_LINE]


def parse_milestones(map_text):
    """-> ([{slug, label, members}, ...], [unparsable raw line, ...])

    A line the grammar cannot read is REPORTED, never skipped. Skipping it would
    hide its members, so the map would advertise a smaller milestone than it has
    and the reader would believe it -- the same absence-read-as-a-fact shape
    ADR 0061 exists to prevent. `lint` turns the second list into findings.

    An absent region parses as empty rather than raising: a map charted before
    milestones existed is legal, and every read path must survive it.
    """
    body = region_body(norm_eol(map_text or ""), MILESTONES_START, MILESTONES_END)
    if body is None:
        return [], []
    out, bad = [], []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line == EMPTY_LIST_LINE:
            continue
        m = _MILESTONE_LINE_RE.match(line)
        if m is None:
            bad.append(line)
            continue
        out.append({
            "slug": m.group("slug"),
            "label": (m.group("label") or "").strip() or None,
            "members": [x.strip() for x in m.group("members").split(",")
                        if x.strip()],
        })
    return out, bad


def milestone_index(map_text):
    """-> (milestones, {ticket key: milestone slug}, unparsable lines)

    A ticket belongs to at most ONE milestone -- the first that needs it
    (ADR 0097): a decision closed once serves every later milestone
    automatically, so nothing is re-done per increment. A key listed twice is a
    lint error, but this projection still has to be deterministic, so first
    occurrence wins rather than last.
    """
    milestones, bad = parse_milestones(map_text)
    by_key = {}
    for m in milestones:
        for key in m["members"]:
            by_key.setdefault(key, m["slug"])
    return milestones, by_key, bad


def milestone_progress(milestones, status_by_key):
    """-> [{slug, label, closed, total, complete}], in map order.

    `total` counts declared members, including one whose ticket is missing --
    that member can never be closed, so the milestone reads as incomplete and
    `lint`'s milestone-unknown-ticket names it. Counting only the members that
    resolve would let a deleted ticket silently complete a milestone.

    An EMPTY milestone is never complete: it has shipped nothing, and calling it
    done would send the reader on to the next group.
    """
    out = []
    for m in milestones:
        members = m.get("members") or []
        closed = sum(1 for k in members if status_by_key.get(k) == "closed")
        out.append({"slug": m["slug"], "label": m.get("label"),
                    "closed": closed, "total": len(members),
                    "complete": bool(members) and closed == len(members)})
    return out


def notes_lines(value):
    """The map's notes as a list of lines, whatever shape the input used.

    A bare string stays legal as a one-bullet list (ADR 0101), so every existing
    map_input.json keeps working unchanged.
    """
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return list(value)
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t1.txt 2>&1; echo "exit=$?"`
Expected: `exit=0`, and the count has risen by the 12 new tests (250 passed)

- [ ] **Step 6: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/map_core.py plugins/decision-map/scripts/test_local_map_ops.py
git commit -m "feat(decision-map): milestone line grammar and projections (ADRs 0094-0097)"
```

---

### Task 2: Validate `milestones` and a list-valued `notes` in chart input

**Files:**
- Modify: `plugins/decision-map/scripts/map_core.py` (`validate_chart_input`, around lines 765-772)
- Test: `plugins/decision-map/scripts/test_local_map_ops.py`

**Interfaces:**
- Consumes: `map_core.require`, `map_core.validate_key`, `map_core.ChartValidationError`, `map_core.notes_lines`
- Produces: `validate_chart_input` accepting `inp["map"]["milestones"]` — a list of `{"slug": str, "label": str|None, "members": list[str]}` — and `inp["map"]["notes"]` as `str` **or** `list[str]`. Raises `ChartValidationError` before anything is written.

- [ ] **Step 1: Write the failing tests**

Add to `test_local_map_ops.py`:

```python
class MilestoneInputValidationTest(unittest.TestCase):
    """Validation runs BEFORE any write (dry run included), so a bad input
    costs an error message rather than a half-charted map."""

    def _inp(self, **mapkw):
        inp = copy.deepcopy(INPUT)
        inp["map"].update(mapkw)
        return inp

    def test_a_valid_milestones_list_passes(self):
        map_core.validate_chart_input(self._inp(milestones=[
            {"slug": "mvp", "label": "demo the search page",
             "members": ["auth-model", "api-limits"]},
            {"slug": "polish", "members": []},
        ]))

    def test_milestones_must_be_a_list(self):
        with self.assertRaises(map_core.ChartValidationError):
            map_core.validate_chart_input(self._inp(milestones={"slug": "mvp"}))

    def test_a_milestone_must_be_an_object_with_a_slug(self):
        for bad in ([("mvp",)], ["mvp"], [{"label": "no slug"}]):
            with self.assertRaises(map_core.ChartValidationError):
                map_core.validate_chart_input(self._inp(milestones=bad))

    def test_a_milestone_slug_obeys_the_key_rule(self):
        # The slug is a marker payload on a tracker, so '--' breaks the HTML
        # comment exactly as it does in a ticket key.
        for bad in ("mvp--search", "../evil", "has space", ""):
            with self.assertRaises(map_core.ChartValidationError):
                map_core.validate_chart_input(
                    self._inp(milestones=[{"slug": bad, "members": []}]))

    def test_a_member_obeys_the_key_rule(self):
        with self.assertRaises(map_core.ChartValidationError):
            map_core.validate_chart_input(self._inp(
                milestones=[{"slug": "mvp", "members": ["../evil"]}]))

    def test_two_milestones_cannot_share_a_slug(self):
        with self.assertRaises(map_core.ChartValidationError):
            map_core.validate_chart_input(self._inp(milestones=[
                {"slug": "mvp", "members": ["auth-model"]},
                {"slug": "mvp", "members": ["api-limits"]}]))

    def test_one_input_cannot_place_a_ticket_in_two_milestones(self):
        # Exclusivity is checked at the input too, not only by lint: an input
        # that contradicts itself has no defensible interpretation.
        with self.assertRaises(map_core.ChartValidationError) as e:
            map_core.validate_chart_input(self._inp(milestones=[
                {"slug": "mvp", "members": ["auth-model"]},
                {"slug": "polish", "members": ["auth-model"]}]))
        self.assertIn("auth-model", str(e.exception))

    def test_a_label_must_be_a_string_when_present(self):
        with self.assertRaises(map_core.ChartValidationError):
            map_core.validate_chart_input(
                self._inp(milestones=[{"slug": "mvp", "label": 7, "members": []}]))

    def test_notes_may_be_a_string_or_a_list_of_strings(self):
        map_core.validate_chart_input(self._inp(notes="one line"))
        map_core.validate_chart_input(self._inp(notes=["one", "two"]))

    def test_notes_rejects_any_other_shape(self):
        for bad in (7, {"a": 1}, ["ok", 7]):
            with self.assertRaises(map_core.ChartValidationError):
                map_core.validate_chart_input(self._inp(notes=bad))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py -k MilestoneInputValidation -q`
Expected: FAIL — the valid-input test passes vacuously but every rejection test fails with `ChartValidationError not raised`

- [ ] **Step 3: Add the validation**

In `validate_chart_input`, replace the `notes` line and the list loop
(currently lines 769-771):

```python
    require(where_map, m, "notes", str, False)
    for field in ("notYetSpecified", "outOfScope"):
        require(where_map, m, field, list, False)
```

with:

```python
    # notes is str OR list[str] (ADR 0101): the region stores a list, and a bare
    # string stays legal as a one-bullet list so existing inputs keep working.
    # `require` checks one declared type, so this pair of shapes is checked here.
    notes = m.get("notes")
    if notes is not None and not (
            isinstance(notes, str)
            or (isinstance(notes, list) and all(isinstance(x, str) for x in notes))):
        raise ChartValidationError(
            f"{where_map}: field 'notes' must be a string or a list of strings, "
            f"got {notes!r}")
    for field in ("notYetSpecified", "outOfScope"):
        require(where_map, m, field, list, False)
    _validate_milestones(where_map, m)
```

And add this helper immediately above `validate_chart_input`:

```python
def _validate_milestones(where_map, m):
    """Validate map.milestones before anything is written.

    Exclusivity is checked HERE as well as in lint: an input placing one ticket
    in two milestones has no defensible interpretation, and applying either
    reading would store a map the user did not describe. A member naming a
    ticket that does not exist is NOT an error here -- a milestone may legally
    be declared ahead of the tickets that will fill it, and lint reports the
    ones that never arrive.
    """
    milestones = m.get("milestones")
    if milestones is None:
        return
    if not isinstance(milestones, list):
        raise ChartValidationError(
            f"{where_map}: field 'milestones' must be a list, got "
            f"{type(milestones).__name__}")
    slugs, owner = set(), {}
    for i, ms in enumerate(milestones):
        if not isinstance(ms, dict):
            raise ChartValidationError(
                f"{where_map}: milestones[{i}] must be an object, got "
                f"{type(ms).__name__}")
        where = f"{where_map}: milestones[{i}]"
        slug = require(where, ms, "slug", str, True)
        validate_key(slug, "milestone slug")
        if slug in slugs:
            raise ChartValidationError(
                f"{where_map}: milestone slug {slug!r} appears twice; "
                "slugs are unique within a map")
        slugs.add(slug)
        require(where, ms, "label", str, False)
        for key in require(where, ms, "members", list, False) or []:
            validate_key(key, "milestone member")
            if key in owner and owner[key] != slug:
                raise ChartValidationError(
                    f"{where_map}: ticket {key!r} is listed in both milestone "
                    f"{owner[key]!r} and {slug!r}; a ticket belongs to at most "
                    "one milestone -- the first that needs it")
            owner[key] = slug
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t2.txt 2>&1; echo "exit=$?"`
Expected: `exit=0`

- [ ] **Step 5: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/map_core.py plugins/decision-map/scripts/test_local_map_ops.py
git commit -m "feat(decision-map): validate map.milestones and list-valued notes (ADRs 0097, 0101)"
```

---

### Task 3: Render and additively merge the two new regions

This is the task that changes what a **new** map document looks like, on both
backends, so existing assertions about map bodies must be updated here.

**Files:**
- Modify: `plugins/decision-map/scripts/map_core.py` (`render_map_body` ~426, `merge_map_lists` ~494, new `merge_milestones` and `scalar_fields_for`)
- Modify: `plugins/decision-map/scripts/local_map_ops.py` (import + `_plan_map_md` ~333)
- Modify: `plugins/decision-map/scripts/github_map_ops.py` (import + `_plan_map` ~895)
- Test: `plugins/decision-map/scripts/test_local_map_ops.py`, `plugins/decision-map/scripts/test_github_map_ops.py`

**Interfaces:**
- Consumes: Task 1's `notes_lines`, `milestone_lines_for`, `parse_milestones`, `MILESTONES_START/END`, `NOTES_START/END`; existing `merge_region_lines`, `region_text`, `replace_region`, `count_added_lines`, `map_merge_detail`, `FORCE_COST`
- Produces:
  - `render_map_body` emits `## Destination`, `## Notes` (region), `## Milestones` (region), `## Decisions so far`, `## Not yet specified`, `## Out of scope` — in that order
  - `merge_map_lists(text, m) -> (new_text, added, divergences)` — `added` now may include `("notes", n)`, `("milestone", n)` and `("milestone member", n)`
  - `scalar_fields_for(stored_text, fields) -> tuple` — drops `"notes"` when the map carries a notes region

- [ ] **Step 1: Write the failing tests**

Add to `test_local_map_ops.py`:

```python
class MapBodyRegionsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _chart(self, inp):
        ops.chart(self.root, inp, real=True)
        return (self.root / inp["target"]["slug"] / "map.md").read_text(
            encoding="utf-8")

    def test_a_new_map_carries_both_new_regions_in_order(self):
        inp = copy.deepcopy(INPUT)
        inp["map"]["notes"] = ["use grill-with-docs", "scrutinize is frozen"]
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it", "members": ["auth-model"]}]
        text = self._chart(inp)
        for marker in (map_core.NOTES_START, map_core.NOTES_END,
                       map_core.MILESTONES_START, map_core.MILESTONES_END):
            self.assertIn(marker, text)
        self.assertIn("- use grill-with-docs\n- scrutinize is frozen", text)
        self.assertIn("- `mvp` demo it [auth-model]", text)
        # Reading order: where we are going, the standing constraints, the plan
        # for what ships first, then the history that plan groups.
        self.assertLess(text.index("## Destination"), text.index("## Notes"))
        self.assertLess(text.index("## Notes"), text.index("## Milestones"))
        self.assertLess(text.index("## Milestones"),
                        text.index("## Decisions so far"))

    def test_a_string_notes_renders_as_one_bullet(self):
        text = self._chart(copy.deepcopy(INPUT))       # INPUT's notes is a str
        self.assertIn("- use grill-with-docs", text)

    def test_an_empty_milestones_region_holds_the_placeholder(self):
        text = self._chart(copy.deepcopy(INPUT))
        body = map_core.region_body(text, map_core.MILESTONES_START,
                                    map_core.MILESTONES_END)
        self.assertEqual(body.strip(), map_core.EMPTY_LIST_LINE)

    def test_an_identical_re_chart_is_byte_identical(self):
        inp = copy.deepcopy(INPUT)
        inp["map"]["notes"] = ["one", "two"]
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it", "members": ["auth-model"]}]
        first = self._chart(inp)
        self.assertEqual(self._chart(copy.deepcopy(inp)), first)

    def test_a_new_milestone_is_appended_and_announced(self):
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [{"slug": "mvp", "members": ["auth-model"]}]
        self._chart(inp)
        nxt = copy.deepcopy(INPUT)
        nxt["tickets"] = []
        nxt["map"]["milestones"] = [{"slug": "polish", "members": ["api-limits"]}]
        plan = ops.chart(self.root, nxt, real=False)
        entry = next(e for e in plan["planned"] if e["path"].endswith("map.md"))
        self.assertEqual(entry["action"], "merge")
        self.assertIn("1 milestone line", entry["detail"])
        ops.chart(self.root, copy.deepcopy(nxt), real=True)
        text = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        ms, bad = map_core.parse_milestones(text)
        self.assertEqual(bad, [])
        # Appended, never reordered: the earlier milestone keeps its position.
        self.assertEqual([m["slug"] for m in ms], ["mvp", "polish"])

    def test_a_new_member_is_unioned_into_an_existing_milestone(self):
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [{"slug": "mvp", "members": ["auth-model"]}]
        self._chart(inp)
        nxt = copy.deepcopy(INPUT)
        nxt["tickets"] = []
        nxt["map"]["milestones"] = [{"slug": "mvp", "members": ["api-limits"]}]
        plan = ops.chart(self.root, nxt, real=False)
        entry = next(e for e in plan["planned"] if e["path"].endswith("map.md"))
        self.assertIn("1 milestone member line", entry["detail"])
        ops.chart(self.root, copy.deepcopy(nxt), real=True)
        ms, _ = map_core.parse_milestones(
            (self.root / "example-effort" / "map.md").read_text(encoding="utf-8"))
        self.assertEqual(ms[0]["members"], ["auth-model", "api-limits"])

    def test_a_differing_label_diverges_and_is_left_unapplied(self):
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it", "members": ["auth-model"]}]
        self._chart(inp)
        nxt = copy.deepcopy(INPUT)
        nxt["tickets"] = []
        nxt["map"]["milestones"] = [
            {"slug": "mvp", "label": "SHIP IT", "members": ["auth-model"]}]
        out = ops.chart(self.root, nxt, real=True)
        self.assertTrue(any("mvp" in d and "label" in d for d in out["divergence"]))
        text = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        self.assertIn("demo it", text)
        self.assertNotIn("SHIP IT", text)

    def test_moving_a_member_to_another_milestone_diverges(self):
        # Exclusivity holds against what is STORED, not just within one input:
        # applying the move would remove the member from its first milestone,
        # and additive never removes (ADR 0098) -- moves are hand edits.
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [{"slug": "mvp", "members": ["auth-model"]},
                                    {"slug": "polish", "members": []}]
        self._chart(inp)
        nxt = copy.deepcopy(INPUT)
        nxt["tickets"] = []
        nxt["map"]["milestones"] = [{"slug": "polish", "members": ["auth-model"]}]
        out = ops.chart(self.root, nxt, real=True)
        self.assertTrue(any("auth-model" in d for d in out["divergence"]))
        ms, _ = map_core.parse_milestones(
            (self.root / "example-effort" / "map.md").read_text(encoding="utf-8"))
        self.assertEqual({m["slug"]: m["members"] for m in ms},
                         {"mvp": ["auth-model"], "polish": []})

    def test_a_reordered_input_diverges_and_the_stored_order_stands(self):
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [{"slug": "one", "members": []},
                                    {"slug": "two", "members": []}]
        self._chart(inp)
        nxt = copy.deepcopy(INPUT)
        nxt["tickets"] = []
        nxt["map"]["milestones"] = [{"slug": "two", "members": []},
                                    {"slug": "one", "members": []}]
        out = ops.chart(self.root, nxt, real=True)
        self.assertTrue(any("order" in d for d in out["divergence"]))
        ms, _ = map_core.parse_milestones(
            (self.root / "example-effort" / "map.md").read_text(encoding="utf-8"))
        self.assertEqual([m["slug"] for m in ms], ["one", "two"])

    def test_a_map_predating_the_regions_reports_rather_than_repairs(self):
        # Inserting the markers would mean guessing where a pre-marker list
        # ended -- the pattern that cost three review rounds.
        self._chart(copy.deepcopy(INPUT))
        p = self.root / "example-effort" / "map.md"
        text = p.read_text(encoding="utf-8")
        for start, end in ((map_core.MILESTONES_START, map_core.MILESTONES_END),
                           (map_core.NOTES_START, map_core.NOTES_END)):
            text = map_core.region_re(start, end).sub("", text)
        p.write_text(text, encoding="utf-8")
        nxt = copy.deepcopy(INPUT)
        nxt["tickets"] = []
        nxt["map"]["notes"] = ["a new note"]
        nxt["map"]["milestones"] = [{"slug": "mvp", "members": ["auth-model"]}]
        out = ops.chart(self.root, nxt, real=True)
        self.assertTrue(any("predates the milestones region" in d
                            for d in out["divergence"]))
        self.assertTrue(any("predates the notes region" in d
                            for d in out["divergence"]))

    def test_a_string_notes_on_a_legacy_map_keeps_the_scalar_behaviour(self):
        # A map whose Notes is still a paragraph must not start reporting a
        # "predates the region" divergence on every re-chart for a field that
        # already worked -- only a LIST notes needs the region.
        self._chart(copy.deepcopy(INPUT))
        p = self.root / "example-effort" / "map.md"
        p.write_text(
            map_core.region_re(map_core.NOTES_START, map_core.NOTES_END).sub(
                "use grill-with-docs\n", p.read_text(encoding="utf-8")),
            encoding="utf-8")
        nxt = copy.deepcopy(INPUT)
        nxt["tickets"] = []
        out = ops.chart(self.root, nxt, real=True)
        self.assertFalse(any("notes" in d for d in out["divergence"]),
                         out["divergence"])

    def test_notes_is_not_double_reported_when_the_region_exists(self):
        # With a notes REGION present the value is merged like fog, so the
        # scalar containment check must not also call it a divergence.
        inp = copy.deepcopy(INPUT)
        inp["map"]["notes"] = ["first"]
        self._chart(inp)
        nxt = copy.deepcopy(INPUT)
        nxt["tickets"] = []
        nxt["map"]["notes"] = ["second"]
        out = ops.chart(self.root, nxt, real=True)
        self.assertEqual([d for d in out["divergence"] if "notes" in d], [])
        text = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        self.assertIn("- first", text)
        self.assertIn("- second", text)
```

And add to `test_github_map_ops.py`, so the two backends are proven to agree:

```python
class GitHubMapRegionsTest(unittest.TestCase):
    """The regions are byte-identical across backends (ADR 0062), which is what
    lets one flow skill read either."""

    def test_a_new_map_issue_carries_both_new_regions(self):
        m = {"title": "t", "destination": "d", "notes": ["one", "two"],
             "milestones": [{"slug": "mvp", "label": "demo it",
                             "members": ["auth-model"]}]}
        body = gh.render_map_issue_body(m, "billing")
        self.assertIn(map_core.NOTES_START, body)
        self.assertIn(map_core.MILESTONES_START, body)
        self.assertIn("- `mvp` demo it [auth-model]", body)
        self.assertIn("- one\n- two", body)

    def test_the_shared_body_matches_the_local_backend_below_the_prologue(self):
        m = {"title": "t", "destination": "d", "notes": ["n"],
             "milestones": [{"slug": "mvp", "members": ["k"]}]}
        shared = map_core.render_map_body(m, "")
        self.assertTrue(gh.render_map_issue_body(m, "billing").endswith(shared))
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t3.txt 2>&1; echo "exit=$?"; grep -c FAILED /tmp/t3.txt`
Expected: non-zero exit; the new tests fail with `AssertionError` on the missing markers

- [ ] **Step 3: Render the new regions**

In `map_core.py`, replace `render_map_body`'s return (lines 445-455) with:

```python
    notes = region_text(NOTES_START, NOTES_END,
                        merge_region_lines("", notes_lines(m.get("notes"))))
    miles = region_text(MILESTONES_START, MILESTONES_END,
                        milestone_lines_for(m.get("milestones") or []))
    fog = region_text(FOG_START, FOG_END,
                      merge_region_lines("", m.get("notYetSpecified") or []))
    oos = region_text(SCOPE_START, SCOPE_END,
                      merge_region_lines("", m.get("outOfScope") or []))
    return (
        prologue +
        f"## Destination\n{one_line(m['destination'])}\n\n"
        f"## Notes\n\n{notes}\n\n"
        f"## Milestones\n\n{miles}\n\n"
        f"## Decisions so far\n\n{DECISIONS_START}\n{DECISIONS_END}\n\n"
        f"## Not yet specified\n\n{fog}\n\n"
        f"## Out of scope\n\n{oos}\n")
```

Update its docstring: the destination is still a single flattened line
(ADR 0101 keeps it one breath), but notes is now a list region, so the
`one_line` note applies to `destination` alone.

- [ ] **Step 4: Merge the notes region and add the scalar-field selector**

In `map_core.py`, inside `merge_map_lists`, replace the fixed loop tuple with a
built list so notes participates only when it should:

```python
    div, added = [], []
    regions = [(FOG_START, FOG_END, m.get("notYetSpecified") or [],
                "notYetSpecified", "fog"),
               (SCOPE_START, SCOPE_END, m.get("outOfScope") or [],
                "outOfScope", "out-of-scope")]
    # Notes joins the merge only when the map HAS the region, or when the input
    # declares a list. A string notes on a map whose Notes is still a paragraph
    # keeps the scalar behaviour it has always had (ADR 0101) -- otherwise every
    # existing map would start reporting a divergence for a field that works.
    if (isinstance(m.get("notes"), list)
            or region_body(text, NOTES_START, NOTES_END) is not None):
        regions.insert(0, (NOTES_START, NOTES_END, notes_lines(m.get("notes")),
                           "notes", "notes"))
    for start, end, items, label, noun in regions:
```

(the loop body below is unchanged), and immediately before the `return`, fold in
the milestone merge:

```python
    text, ms_added, ms_div = merge_milestones(text, m.get("milestones") or [])
    added += ms_added
    div += ms_div
    return text, added, div
```

Then add, above `merge_map_lists`:

```python
def scalar_fields_for(stored_text, fields=SCALAR_MAP_FIELDS):
    """The scalar fields still worth a containment check on this document.

    `notes` drops out once the map carries a notes region: there the value is a
    LIST merged like fog, and a containment check on the flattened body would
    report a divergence for text the merge had just applied -- noise, in exactly
    the channel whose whole value is that users read it.
    """
    if region_body(norm_eol(stored_text or ""), NOTES_START, NOTES_END) is None:
        return tuple(fields)
    return tuple(f for f in fields if f != "notes")


def merge_milestones(text, wanted):
    """Union `wanted` into the stored milestones region.

    -> (new_text, added, divergences). `added` is [(noun, count), ...] for
    map_merge_detail, using two nouns because they are different acts to
    approve: a new GROUP appears in the plan as "1 milestone line", a group
    gaining a ticket as "1 milestone member line".

    Additive, with three things deliberately NOT applied and reported instead
    (ADR 0098) -- each would have to remove or reorder a stored line:

    - a differing label;
    - a member the map already places in a DIFFERENT milestone (the move would
      have to remove it from the first one; exclusivity is ADR 0097);
    - a different relative order of milestones that both already exist.

    A map predating the region is reported, never repaired: inserting the
    markers means guessing where a pre-marker list ended.
    """
    if not wanted:
        return text, [], []
    body = region_body(text, MILESTONES_START, MILESTONES_END)
    if body is None:
        return text, [], [
            f"this map predates the milestones region, so its {len(wanted)} "
            "milestone(s) were not merged. Add the milestones markers to the "
            f"map body by hand to enable merging; re-charting would also fix "
            f"it, but {FORCE_COST}"]
    stored, bad = parse_milestones(text)
    div = []
    if bad:
        div.append(
            f"the milestones region holds {len(bad)} line(s) this tool cannot "
            f"read (first: {bad[0]!r}), so they took no part in the merge. "
            "`lint` names every one of them")
    by_slug = {m["slug"]: m for m in stored}
    owner = {k: m["slug"] for m in stored for k in m["members"]}
    new_groups, new_members = 0, 0

    stored_order = [m["slug"] for m in stored]
    shared = [s["slug"] for s in wanted if s["slug"] in by_slug]
    if [s for s in stored_order if s in shared] != shared:
        div.append(
            "the input lists existing milestones in a different order "
            f"({', '.join(shared)}); the stored order stands. Reorder the "
            "milestones region by hand to change it")

    for want in wanted:
        slug = want["slug"]
        label = want.get("label")
        members = want.get("members") or []
        got = by_slug.get(slug)
        if got is None:
            keep = []
            for key in members:
                if key in owner and owner[key] != slug:
                    div.append(
                        f"ticket {key!r} is already in milestone "
                        f"{owner[key]!r}, so it was not added to {slug!r}: a "
                        "ticket belongs to at most one milestone. Move it by "
                        "hand if that is what you meant")
                    continue
                if key not in keep:
                    keep.append(key)
                    owner[key] = slug
            entry = {"slug": slug, "label": label, "members": keep}
            stored.append(entry)
            by_slug[slug] = entry
            new_groups += 1
            continue
        if label and one_line(label) != (got["label"] or ""):
            div.append(
                f"milestone {slug!r}'s label in the input differs from the map "
                "as stored; left unchanged. Edit the milestones region by hand "
                "to change it")
        for key in members:
            if key in got["members"]:
                continue
            if key in owner and owner[key] != slug:
                div.append(
                    f"ticket {key!r} is already in milestone {owner[key]!r}, so "
                    f"it was not added to {slug!r}: a ticket belongs to at most "
                    "one milestone. Move it by hand if that is what you meant")
                continue
            got["members"].append(key)
            owner[key] = slug
            new_members += 1

    merged = region_text(MILESTONES_START, MILESTONES_END,
                         milestone_lines_for(stored))
    text = replace_region(text, MILESTONES_START, MILESTONES_END,
                          merged[len(MILESTONES_START):-len(MILESTONES_END)])
    added = []
    if new_groups:
        added.append(("milestone", new_groups))
    if new_members:
        added.append(("milestone member", new_members))
    return text, added, div
```

- [ ] **Step 5: Point both backends' scalar checks at the selector**

In `local_map_ops.py`, add `scalar_fields_for` to the `map_core` import block
alongside `_scalar_divergences`, then in `_plan_map_md` replace:

```python
    div = _scalar_divergences(m, existing)
```

with:

```python
    div = _scalar_divergences(m, existing, fields=_scalar_fields_for(existing))
```

In `github_map_ops.py`, import `scalar_fields_for` and in `_plan_map` replace:

```python
    div += scalar_divergences(m, existing, fields=("destination", "notes"))
```

with:

```python
    div += scalar_divergences(
        m, existing, fields=scalar_fields_for(existing, ("destination", "notes")))
```

- [ ] **Step 6: Update the existing assertions this changes**

Run the suite and fix every failure that is an old assertion about the map
body's text — the two real changes are that `## Notes` now holds a region rather
than a bare paragraph, and that `## Milestones` sits between Notes and
Decisions. Do **not** weaken an assertion to make it pass: if a test asserted
`"## Notes\nuse grill-with-docs"`, assert the bullet form instead.

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t3b.txt 2>&1; echo "exit=$?"; grep -E "^(FAILED|ERROR)" /tmp/t3b.txt`

- [ ] **Step 7: Run the full suite to verify it passes**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t3c.txt 2>&1; echo "exit=$?"; tail -2 /tmp/t3c.txt`
Expected: `exit=0`

- [ ] **Step 8: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/
git commit -m "feat(decision-map): render and additively merge the milestones and notes regions (ADRs 0098, 0101)"
```

---

### Task 4: Four lint rules for the milestones region

**Files:**
- Modify: `plugins/decision-map/scripts/map_core.py` (`lint_findings`, around line 1083, next to the fog rule)
- Test: `plugins/decision-map/scripts/test_local_map_ops.py`

**Interfaces:**
- Consumes: Task 1's `milestone_index`; existing `_finding`, `LINT_ERROR`, `LINT_WARNING`
- Produces: findings with rules `milestone-line-unparsable`, `milestone-duplicate-slug`, `milestone-duplicate-member`, `milestone-unknown-ticket`. The first two carry `ticket: None` (they are map-level, like `gist-budget`); the last two name the member key. No signature change — `lint_findings` already receives `map_text`.

- [ ] **Step 1: Write the failing tests**

Add to `test_local_map_ops.py`:

```python
class MilestoneLintTest(unittest.TestCase):
    """Each rule exists because a flow skill or an ADR states the invariant in
    prose and nothing enforced it. Prose is advisory; this is the deterministic
    half."""

    def _map_text(self, *lines):
        return ("## Milestones\n\n" + map_core.MILESTONES_START + "\n"
                + "".join(ln + "\n" for ln in lines) + map_core.MILESTONES_END
                + "\n\n" + map_core.FOG_START + "\n" + map_core.EMPTY_LIST_LINE
                + "\n" + map_core.FOG_END + "\n")

    def _tickets(self, *keys):
        return [{"key": k, "name": k, "status": "open", "assignee": None,
                 "blockedBy": [], "gist": None, "resolution": None,
                 "type": "task"} for k in keys]

    def _rules(self, findings):
        return [f["rule"] for f in findings]

    def test_a_clean_milestones_region_produces_nothing(self):
        findings = map_core.lint_findings(
            self._map_text("- `mvp` demo it [a, b]", "- `polish` [c]"),
            self._tickets("a", "b", "c"))
        self.assertEqual(findings, [])

    def test_an_unparsable_line_is_an_error(self):
        findings = map_core.lint_findings(
            self._map_text("- mvp: a, b"), self._tickets("a", "b"))
        self.assertIn("milestone-line-unparsable", self._rules(findings))
        bad = next(f for f in findings
                   if f["rule"] == "milestone-line-unparsable")
        self.assertEqual(bad["severity"], map_core.LINT_ERROR)
        self.assertIsNone(bad["ticket"])
        self.assertIn("- mvp: a, b", bad["message"])

    def test_two_milestones_sharing_a_slug_is_an_error(self):
        findings = map_core.lint_findings(
            self._map_text("- `mvp` [a]", "- `mvp` [b]"),
            self._tickets("a", "b"))
        f = next(f for f in findings if f["rule"] == "milestone-duplicate-slug")
        self.assertEqual(f["severity"], map_core.LINT_ERROR)
        self.assertIn("mvp", f["message"])

    def test_a_ticket_in_two_milestones_is_an_error_naming_the_ticket(self):
        findings = map_core.lint_findings(
            self._map_text("- `mvp` [a]", "- `polish` [a]"),
            self._tickets("a"))
        f = next(f for f in findings
                 if f["rule"] == "milestone-duplicate-member")
        self.assertEqual(f["severity"], map_core.LINT_ERROR)
        self.assertEqual(f["ticket"], "a")
        self.assertIn("mvp", f["message"])
        self.assertIn("polish", f["message"])

    def test_a_member_with_no_ticket_is_an_error_naming_the_key(self):
        # It can never close, so the milestone can never complete -- and the
        # progress line silently reads "1/2 forever" without this.
        findings = map_core.lint_findings(
            self._map_text("- `mvp` [a, ghost]"), self._tickets("a"))
        f = next(f for f in findings
                 if f["rule"] == "milestone-unknown-ticket")
        self.assertEqual(f["severity"], map_core.LINT_ERROR)
        self.assertEqual(f["ticket"], "ghost")

    def test_a_closed_member_is_not_a_finding(self):
        tickets = self._tickets("a")
        tickets[0].update(status="closed", gist="answered",
                          resolution="```mermaid\ngraph TD\n A-->B\n```\n"
                                     "Detail: docs/adr/x.md\n")
        self.assertEqual(
            map_core.lint_findings(self._map_text("- `mvp` [a]"), tickets), [])

    def test_a_map_with_no_milestones_region_produces_no_milestone_findings(self):
        findings = map_core.lint_findings(
            map_core.FOG_START + "\n" + map_core.EMPTY_LIST_LINE + "\n"
            + map_core.FOG_END + "\n", self._tickets("a"))
        self.assertEqual([r for r in self._rules(findings)
                          if r.startswith("milestone-")], [])
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py -k MilestoneLint -q`
Expected: FAIL — `StopIteration` on each `next(...)`, because no milestone rule exists

- [ ] **Step 3: Add the rules**

In `lint_findings`, immediately before the `by_tokens = [...]` fog block
(around line 1083):

```python
    # The milestones region (ADRs 0097, 0098). Every rule here is an ERROR: each
    # one makes the region describe a plan the map does not have, and the
    # session surface reads that region to decide what to work on next -- a
    # wrong group or a phantom member misroutes the next session rather than
    # merely looking untidy. Moves and reorders are hand edits by design, so a
    # hand-broken region is the expected failure mode, not an exotic one.
    milestones, _by_key, unparsable = milestone_index(map_text or "")
    for line in unparsable:
        errors.append(_finding(
            "milestone-line-unparsable", LINT_ERROR, None,
            f"the milestones line {line!r} is not in the form "
            "'- `slug` optional label [key, key]', so its members are invisible "
            "to every command; the map advertises a smaller milestone than it "
            "has"))
    seen_slugs, owner = {}, {}
    for m in milestones:
        slug = m["slug"]
        if slug in seen_slugs:
            errors.append(_finding(
                "milestone-duplicate-slug", LINT_ERROR, None,
                f"milestone {slug!r} is declared twice; the projection takes "
                "the first, so the second's members are silently unreachable"))
        seen_slugs.setdefault(slug, m)
        for key in m["members"]:
            if key in owner and owner[key] != slug:
                errors.append(_finding(
                    "milestone-duplicate-member", LINT_ERROR, key,
                    f"{key!r} is a member of both {owner[key]!r} and {slug!r}; "
                    "a ticket belongs to at most one milestone -- the first "
                    "that needs it -- so remove it from one of them by hand"))
            owner.setdefault(key, slug)
            if key not in keys:
                errors.append(_finding(
                    "milestone-unknown-ticket", LINT_ERROR, key,
                    f"milestone {slug!r} lists {key!r}, which is not a ticket "
                    "on this map; it can never close, so the milestone can "
                    "never complete and its progress reads short for ever"))
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t4.txt 2>&1; echo "exit=$?"`
Expected: `exit=0`

- [ ] **Step 5: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/map_core.py plugins/decision-map/scripts/test_local_map_ops.py
git commit -m "feat(decision-map): lint the milestones region - four rules (ADRs 0097, 0098)"
```

---

### Task 5: Group the decisions index by milestone, on both backends

`decisions_region`'s entries gain the ticket key (it is needed to group), so
both `_reindex_decisions` callers change in this same task — the suite stays
green throughout.

**Files:**
- Modify: `plugins/decision-map/scripts/map_core.py` (`decisions_region` ~527)
- Modify: `plugins/decision-map/scripts/local_map_ops.py` (`_reindex_decisions` ~696)
- Modify: `plugins/decision-map/scripts/github_map_ops.py` (`_reindex_decisions` ~1501)
- Test: `plugins/decision-map/scripts/test_local_map_ops.py`, `plugins/decision-map/scripts/test_github_map_ops.py`

**Interfaces:**
- Consumes: Task 1's `milestone_index`
- Produces: `decisions_region(entries, milestones=None) -> str`, where `entries` is `[(key, title, link, gist), ...]` — **four**-tuples now — and `milestones` is the parsed list. With `milestones` `None` or empty, the output is today's flat list.

- [ ] **Step 1: Write the failing tests**

Add to `test_local_map_ops.py`:

```python
class DecisionsIndexGroupingTest(unittest.TestCase):
    ENTRIES = [("a", "A?", "tickets/a.md", "yes"),
               ("b", "B?", "tickets/b.md", "no"),
               ("z", "Z?", "tickets/z.md", "maybe")]

    def test_no_milestones_renders_todays_flat_list(self):
        got = map_core.decisions_region(self.ENTRIES)
        self.assertIn("- [A?](tickets/a.md) — yes\n", got)
        self.assertNotIn("####", got)

    def test_grouped_by_milestone_in_map_order_with_an_unassigned_tail(self):
        ms = [{"slug": "two", "label": "second", "members": ["b"]},
              {"slug": "one", "label": None, "members": ["a"]}]
        got = map_core.decisions_region(self.ENTRIES, ms)
        # Milestone order comes from the REGION, not from the keys.
        self.assertLess(got.index("#### two"), got.index("#### one"))
        self.assertIn("#### two — second\n", got)
        self.assertLess(got.index("#### one"), got.index("(unassigned)"))
        # Unassigned decisions are a tail group, never dropped.
        self.assertIn("- [Z?](tickets/z.md) — maybe", got.split("(unassigned)")[1])

    def test_a_milestone_with_no_closed_decision_is_not_rendered(self):
        ms = [{"slug": "empty", "label": None, "members": ["nobody"]},
              {"slug": "one", "label": None, "members": ["a"]}]
        got = map_core.decisions_region(self.ENTRIES, ms)
        self.assertNotIn("#### empty", got)

    def test_entries_stay_key_ascending_inside_a_group(self):
        ms = [{"slug": "one", "label": None, "members": ["b", "a"]}]
        got = map_core.decisions_region(self.ENTRIES, ms)
        group = got.split("#### one")[1]
        self.assertLess(group.index("[A?]"), group.index("[B?]"))

    def test_the_region_markers_still_frame_it_exactly_once(self):
        got = map_core.decisions_region(
            self.ENTRIES, [{"slug": "one", "label": None, "members": ["a"]}])
        self.assertEqual(got.count(map_core.DECISIONS_START), 1)
        self.assertEqual(got.count(map_core.DECISIONS_END), 1)


class LocalGroupedIndexTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_resolving_writes_a_grouped_index(self):
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it", "members": ["auth-model"]}]
        ops.chart(self.root, inp, real=True)
        ops.resolve(self.root, "example-effort", "auth-model",
                    "per-tenant keys", "docs/adr/x.md", _DIAGRAM_BODY)
        text = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        body = map_core.region_body(text, map_core.DECISIONS_START,
                                   map_core.DECISIONS_END)
        self.assertIn("#### mvp — demo it", body)
        self.assertIn("per-tenant keys", body)

    def test_an_unmilestoned_map_keeps_the_flat_index(self):
        ops.chart(self.root, copy.deepcopy(INPUT), real=True)
        ops.resolve(self.root, "example-effort", "auth-model",
                    "per-tenant keys", "docs/adr/x.md", _DIAGRAM_BODY)
        body = map_core.region_body(
            (self.root / "example-effort" / "map.md").read_text(encoding="utf-8"),
            map_core.DECISIONS_START, map_core.DECISIONS_END)
        self.assertNotIn("####", body)
```

Add to `test_github_map_ops.py` an equivalent for the tracker: chart with a
milestone, `resolve` one ticket, then assert the map issue body's decisions
region contains `#### mvp`. Follow the file's existing pattern for building a
`FakeGitHub`, charting `INPUT` with `--real`, and reading the map issue body
back — reuse whatever helper the neighbouring `resolve` tests already use
rather than writing a new one.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -k "Grouped or GroupingTest" -q`
Expected: FAIL — `ValueError: not enough values to unpack` (the three-tuple unpack in `decisions_region`) and `#### mvp` absent

- [ ] **Step 3: Rewrite `decisions_region`**

Replace it in `map_core.py` with:

```python
def decisions_region(entries, milestones=None):
    """The "Decisions so far" index, regenerated in full inside its own region.

    The index is a projection of the tickets, not accumulated state, so it is
    rebuilt wholesale. There is no per-line pattern to match and nothing outside
    the region is read or touched -- which is what stops a user-authored,
    index-shaped line elsewhere in the map body from being substituted away, and
    stops a multi-line gist from splitting one entry into an orphanable pair.

    `entries` is [(key, title, link, gist), ...]. **Ordered by ticket key
    (ascending)** within each group, not by when each decision was resolved, so
    the index is a deterministic function of state; the caller sorts, this only
    formats.

    `milestones` is the map's parsed milestone list. Given one, the index is
    GROUPED to match the frontier the reader sees in the same session (ADR
    0103): one `#### ` heading per milestone in MAP order -- not key order,
    because the whole point of a milestone list is that its order is chosen --
    then an "(unassigned)" tail. A milestone with no closed decision yet is
    omitted rather than rendered empty, and with no milestones at all the output
    is the flat list this function has always produced, so an unmilestoned map
    is unchanged.
    """
    lines = []

    def render(group):
        for _key, title, link, gist in group:
            lines.append(f"- [{title}]({link}) — {gist}".rstrip() + "\n")

    if not milestones:
        render(entries)
    else:
        by_key = {}
        for m in milestones:
            for key in m["members"]:
                by_key.setdefault(key, m["slug"])
        remaining = list(entries)
        for m in milestones:
            group = [e for e in remaining if by_key.get(e[0]) == m["slug"]]
            if not group:
                continue
            heading = f"#### {m['slug']}"
            if m.get("label"):
                heading += f" — {m['label']}"
            lines.append(heading + "\n\n")
            render(group)
            lines.append("\n")
            remaining = [e for e in remaining if e not in group]
        if remaining:
            lines.append("#### (unassigned)\n\n")
            render(remaining)
    return f"{DECISIONS_START}\n{''.join(lines).rstrip(chr(10))}\n{DECISIONS_END}\n"
```

- [ ] **Step 4: Feed both backends' reindex the keys and the milestones**

In `local_map_ops.py`'s `_reindex_decisions`, change the entry tuple and pass
the milestones parsed from the map it is about to rewrite:

```python
    entries = []
    for key in _all_tickets(root, slug):
        fm, _ = _load_ticket(root, slug, key)
        if fm.get("status") != "closed":
            continue
        entries.append((key, fm.get("title") or key, f"tickets/{key}.md",
                        fm.get("gist") or ""))
    map_path = _map_dir(root, slug) / "map.md"
    map_md = map_path.read_text(encoding="utf-8")
    milestones, _by_key, _bad = _milestone_index(map_md)
    region = _decisions_region(entries, milestones)
```

(the `_DECISIONS_BLOCK_RE` substitution and the legacy fallback below are
unchanged — delete the now-duplicated `map_md` read that followed).

In `github_map_ops.py`'s `_reindex_decisions`, do the same: build four-tuples
with the key first, parse the milestones out of the map body the function
already holds (`snap.map.get("body")`, through `norm_eol`), and pass them to
`decisions_region`.

- [ ] **Step 5: Run the full suite to verify it passes**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t5.txt 2>&1; echo "exit=$?"; grep -E "^(FAILED|ERROR)" /tmp/t5.txt`
Expected: `exit=0`

- [ ] **Step 6: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/
git commit -m "feat(decision-map): group the decisions index by milestone (ADR 0103)"
```

---

### Task 6: The local backend's `read` and `frontier` carry milestones

**Files:**
- Modify: `plugins/decision-map/scripts/local_map_ops.py` (`read_map` ~557, `frontier` ~572)
- Test: `plugins/decision-map/scripts/test_local_map_ops.py`

**Interfaces:**
- Consumes: Task 1's `milestone_index`, `milestone_progress`
- Produces:
  - `read_map` returns `{"backend", "map", "milestones": [{slug,label,members}], "tickets": [...]}` and every ticket dict gains `"milestone": slug|None`
  - `frontier` returns `{"frontier", "blocked", "claimed", "milestones": [{slug,label,closed,total,complete}]}` and every bucket entry gains `"milestone": slug|None`

- [ ] **Step 1: Write the failing tests**

```python
class LocalMilestoneProjectionTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it",
             "members": ["auth-model", "rollout-order"]},
            {"slug": "later", "members": []}]
        ops.chart(self.root, inp, real=True)

    def tearDown(self):
        self.tmp.cleanup()

    def test_read_carries_the_ordered_milestones_and_per_ticket_membership(self):
        out = ops.read_map(self.root, "example-effort")
        self.assertEqual([m["slug"] for m in out["milestones"]],
                         ["mvp", "later"])
        self.assertEqual(out["milestones"][0]["label"], "demo it")
        self.assertEqual(out["milestones"][0]["members"],
                         ["auth-model", "rollout-order"])
        by_key = {t["key"]: t for t in out["tickets"]}
        self.assertEqual(by_key["auth-model"]["milestone"], "mvp")
        # An unassigned ticket says so explicitly rather than omitting the key.
        self.assertIsNone(by_key["api-limits"]["milestone"])

    def test_frontier_carries_progress_and_per_entry_membership(self):
        out = ops.frontier(self.root, "example-effort")
        mvp = next(m for m in out["milestones"] if m["slug"] == "mvp")
        self.assertEqual((mvp["closed"], mvp["total"], mvp["complete"]),
                         (0, 2, False))
        entry = next(e for e in out["frontier"] if e["id"] == "auth-model")
        self.assertEqual(entry["milestone"], "mvp")
        blocked = next(e for e in out["blocked"] if e["id"] == "rollout-order")
        self.assertEqual(blocked["milestone"], "mvp")

    def test_progress_moves_when_a_member_closes(self):
        ops.resolve(self.root, "example-effort", "auth-model", "answered",
                    "docs/adr/x.md", _DIAGRAM_BODY)
        out = ops.frontier(self.root, "example-effort")
        mvp = next(m for m in out["milestones"] if m["slug"] == "mvp")
        self.assertEqual((mvp["closed"], mvp["total"], mvp["complete"]),
                         (1, 2, False))

    def test_a_claimed_entry_also_carries_its_milestone(self):
        ops.claim(self.root, "example-effort", "auth-model", "grill-1200")
        out = ops.frontier(self.root, "example-effort")
        self.assertEqual(out["claimed"][0]["milestone"], "mvp")

    def test_an_unmilestoned_map_reports_an_empty_list_not_a_missing_key(self):
        # The key is always present so a consumer never branches on absence.
        tmp = tempfile.TemporaryDirectory()
        try:
            root = Path(tmp.name)
            inp = copy.deepcopy(INPUT)
            inp["target"]["slug"] = "plain"
            ops.chart(root, inp, real=True)
            self.assertEqual(ops.read_map(root, "plain")["milestones"], [])
            self.assertEqual(ops.frontier(root, "plain")["milestones"], [])
        finally:
            tmp.cleanup()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py -k LocalMilestoneProjection -q`
Expected: FAIL — `KeyError: 'milestones'`

- [ ] **Step 3: Project in `read_map`**

```python
def read_map(root, slug):
    map_path = _map_dir(root, slug) / "map.md"
    map_md = map_path.read_text(encoding="utf-8")
    title = map_md.splitlines()[0].lstrip("# ").strip()
    dest = ""
    dm = re.search(r"## Destination\n(.+?)(\n\n|\n##)", map_md, re.DOTALL)
    if dm:
        dest = dm.group(1).strip()
    milestones, by_key, _bad = _milestone_index(map_md)
    tickets = []
    for key in _all_tickets(root, slug):
        t = _ticket_json(root, slug, key)
        # Always present, null when unassigned: "not yet scheduled" is a legal
        # state (ADR 0097), and a consumer must not have to branch on absence.
        t["milestone"] = by_key.get(key)
        tickets.append(t)
    return {"backend": "local",
            "map": {"id": slug, "name": title,
                    "url": map_path.as_posix(),
                    "destination": dest},
            "milestones": milestones,
            "tickets": tickets}
```

- [ ] **Step 4: Project in `frontier`**

Read the map text once at the top (the existence assertion already reads it —
keep the value instead of discarding it), then tag each bucket entry and append
the progress list:

```python
def frontier(root, slug):
    # ... existing docstring ...
    map_md = (_map_dir(root, slug) / "map.md").read_text(encoding="utf-8")
    milestones, by_key, _bad = _milestone_index(map_md)

    out = {"frontier": [], "blocked": [], "claimed": []}
    tickets = {t: _ticket_json(root, slug, t) for t in _all_tickets(root, slug)}
    for key, t in tickets.items():
        # ... existing body, with `"milestone": by_key.get(key)` added to each
        # of the three entry dicts ...
    # The progress the session surface groups by (ADR 0099). Counted over EVERY
    # ticket, closed included -- a milestone's progress is closed/total, and the
    # buckets above deliberately hold only the open ones.
    out["milestones"] = _milestone_progress(
        milestones, {k: t["status"] for k, t in tickets.items()})
    return out
```

- [ ] **Step 5: Run the full suite to verify it passes**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t6.txt 2>&1; echo "exit=$?"`
Expected: `exit=0`

- [ ] **Step 6: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/local_map_ops.py plugins/decision-map/scripts/test_local_map_ops.py
git commit -m "feat(decision-map): local read/frontier carry milestones and progress (ADR 0099)"
```

---

### Task 7: A new ticket renders its Question above the position diagram

**Files:**
- Modify: `plugins/decision-map/scripts/map_core.py` (`set_graph_region` ~573)
- Modify: `plugins/decision-map/scripts/local_map_ops.py` (`chart`'s create path, ~515-519)
- Test: `plugins/decision-map/scripts/test_local_map_ops.py`

**Interfaces:**
- Consumes: `map_core.position_diagram_region`
- Produces: a freshly created local ticket file whose body is `## Question`, the question, then the graph region; `set_graph_region` inserting into a legacy ticket **below** the Question section

- [ ] **Step 1: Write the failing tests**

```python
class TicketCardOrderTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_new_ticket_leads_with_its_question(self):
        # The card's identity is its question; the position diagram is context
        # glanced at second (ADR 0102).
        ops.chart(self.root, copy.deepcopy(INPUT), real=True)
        text = (self.root / "example-effort" / "tickets" / "auth-model.md"
                ).read_text(encoding="utf-8")
        self.assertLess(text.index("## Question"),
                        text.index(map_core.GRAPH_START))
        self.assertIn("per-tenant or shared?", text)

    def test_the_graph_region_is_still_exactly_one_pair(self):
        ops.chart(self.root, copy.deepcopy(INPUT), real=True)
        text = (self.root / "example-effort" / "tickets" / "auth-model.md"
                ).read_text(encoding="utf-8")
        self.assertEqual(text.count(map_core.GRAPH_START), 1)
        self.assertEqual(text.count(map_core.GRAPH_END), 1)

    def test_wiring_an_edge_still_re_renders_the_diagram_in_place(self):
        ops.chart(self.root, copy.deepcopy(INPUT), real=True)
        text = (self.root / "example-effort" / "tickets" / "rollout-order.md"
                ).read_text(encoding="utf-8")
        self.assertIn('P0["auth-model"] --> ME', text)
        self.assertLess(text.index("## Question"),
                        text.index(map_core.GRAPH_START))

    def test_an_identical_re_chart_leaves_a_ticket_byte_identical(self):
        ops.chart(self.root, copy.deepcopy(INPUT), real=True)
        p = self.root / "example-effort" / "tickets" / "rollout-order.md"
        before = p.read_bytes()
        ops.chart(self.root, copy.deepcopy(INPUT), real=True)
        self.assertEqual(p.read_bytes(), before)

    def test_a_legacy_ticket_gains_the_region_below_its_question(self):
        body = "\n## Question\n\nwhich one?\n"
        got = map_core.set_graph_region(
            body, map_core.position_diagram_region("k", [], []))
        self.assertLess(got.index("## Question"), got.index(map_core.GRAPH_START))
        self.assertIn("which one?", got)

    def test_a_legacy_ticket_with_a_later_section_keeps_it_below_the_diagram(self):
        # Inserted before the NEXT heading, so the diagram lands inside the
        # Question section rather than after a resolution block.
        body = "\n## Question\n\nwhich one?\n\n## Notes from a comment\n\nhi\n"
        got = map_core.set_graph_region(
            body, map_core.position_diagram_region("k", [], []))
        self.assertLess(got.index(map_core.GRAPH_START),
                        got.index("## Notes from a comment"))

    def test_a_ticket_with_no_question_heading_still_gets_one_region(self):
        got = map_core.set_graph_region(
            "loose text\n", map_core.position_diagram_region("k", [], []))
        self.assertEqual(got.count(map_core.GRAPH_START), 1)
        self.assertIn("loose text", got)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py -k TicketCardOrder -q`
Expected: FAIL — the diagram still precedes `## Question`

- [ ] **Step 3: Change the create template**

In `local_map_ops.py`'s `chart`, replace the `_save_ticket` call in the create
pass:

```python
        _save_ticket(root, slug, t["key"], fm,
                     f"\n## Question\n\n{_scrub(t['question'])}\n\n"
                     f"{_position_diagram_region(t['key'], [], [])}")
```

- [ ] **Step 4: Change `set_graph_region`'s legacy insertion point**

```python
def set_graph_region(body, region):
    """Replace the graph region, or insert one into a ticket that predates it.

    Insertion goes BELOW the "## Question" section, because the card's identity
    is its question and the position diagram is context read second (ADR 0102):
    before the next "## " heading if there is one, so the diagram lands inside
    the Question section rather than after a resolution block, and otherwise at
    the end. A ticket with no Question heading at all gets the region appended --
    never guess at the boundary of content the tool did not write, the same
    conservative rule _reindex_decisions applies to a legacy map.md.

    `region` already carries its own trailing newline
    (position_diagram_region's contract), and the block matched by `block_re`
    extends through that same optional trailing newline (region_re's `\\n?`), so
    the substitution is used as-is.
    """
    block_re = region_re(GRAPH_START, GRAPH_END)
    if block_re.search(body):
        return block_re.sub(lambda _m: region, body, count=1)
    heading = "## Question"
    i = body.find(heading)
    if i < 0:
        return body.rstrip("\n") + "\n\n" + region
    nxt = body.find("\n## ", i + len(heading))
    if nxt < 0:
        return body.rstrip("\n") + "\n\n" + region
    return body[:nxt + 1] + region + "\n" + body[nxt + 1:]
```

- [ ] **Step 5: Run the full suite and fix the assertions this moves**

Some existing tests assert a ticket body's exact text or the diagram's position.
Update them to the new order — again, do not weaken an assertion to make it
pass.

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t7.txt 2>&1; echo "exit=$?"; grep -E "^(FAILED|ERROR)" /tmp/t7.txt`
Expected: `exit=0`

- [ ] **Step 6: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/
git commit -m "feat(decision-map): a new ticket leads with its Question (ADR 0102)"
```

---

### Task 8: Wire the GitHub backend

**Files:**
- Modify: `plugins/decision-map/scripts/github_map_ops.py` (`Snapshot.__init__`/`ticket_json`/`map_json` ~583-619, `render_ticket_issue_body` ~636, `frontier` ~1331)
- Test: `plugins/decision-map/scripts/test_github_map_ops.py`

**Interfaces:**
- Consumes: Task 1's `milestone_index`, `milestone_progress`
- Produces: the same `milestones` / `milestone` fields as Task 6, on `map.json` and `frontier.json`; a ticket issue body whose Question precedes its graph region

- [ ] **Step 1: Write the failing tests**

Mirror Task 6's assertions against the fake API, following this file's existing
setup pattern (build a `FakeGitHub`, chart `INPUT` with a `milestones` entry and
`--real`, then call `gh.read_map` / `gh.frontier`):

```python
class GitHubMilestoneProjectionTest(unittest.TestCase):
    def test_read_carries_ordered_milestones_and_per_ticket_membership(self):
        ...   # same shape as LocalMilestoneProjectionTest, via gh.read_map
    def test_frontier_carries_progress_and_per_entry_membership(self):
        ...
    def test_an_unmilestoned_map_reports_an_empty_list(self):
        ...
    def test_a_new_ticket_issue_leads_with_its_question(self):
        body = gh.render_ticket_issue_body("k", "which one?")
        self.assertLess(body.index("## Question"), body.index(map_core.GRAPH_START))
        self.assertEqual(body.count(map_core.KEY_MARKER % "k"), 1)
        self.assertEqual(body.count(map_core.GIST_START), 1)
    def test_the_two_backends_report_the_same_milestone_fields(self):
        ...   # assert the key SET of one ticket dict matches the local one's,
              # minus the GitHub-only handles (dbId, repo)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_github_map_ops.py -k GitHubMilestone -q`
Expected: FAIL — `KeyError: 'milestones'` and the Question/diagram order

- [ ] **Step 3: Add the projection to `Snapshot`**

In `Snapshot.__init__`, after `self.map_key` is set, parse the map body once so
every projection shares one read:

```python
        # Parsed once here, not per ticket: the map body is already in hand and
        # both map_json and frontier read the same answer from it.
        self.milestones, self.milestone_of, self._bad_milestone_lines = \
            milestone_index(norm_eol(node.get("body")))
```

In `ticket_json`, add to the returned dict:

```python
            "milestone": self.milestone_of.get(key),
```

In `map_json`, add `"milestones": self.milestones,` between `"map"` and
`"tickets"`, so the document's key order matches the local backend's.

- [ ] **Step 4: Add the projection to `frontier`**

Add `"milestone": t["milestone"]` to the `base` dict each bucket entry is built
from, and after the loop:

```python
    out["milestones"] = milestone_progress(
        snap.milestones,
        {k: _state(snap.tickets[k].get("state")) for k in snap.keys})
```

- [ ] **Step 5: Reorder the ticket issue body**

```python
def render_ticket_issue_body(key, question):
    """The ticket issue body: key marker, the question, the position diagram,
    an empty gist region.

    The QUESTION comes first (ADR 0102) -- the card's identity is what it asks,
    and the diagram is context read second. Every region is still written at
    creation rather than inserted later, for the reason the local backend does
    the same: a writer that has to decide *where* a region goes is guessing at
    the boundary of content it did not write, which is the pattern that cost
    three review rounds. A fresh ticket has no blockers and unblocks nothing
    yet, so the diagram renders with empty parent/child lists; `chart`'s
    edge-wiring pass re-renders it once real edges exist.
    """
    return (f"{KEY_MARKER % key}\n\n## Question\n\n{scrub(question)}\n\n"
            f"{position_diagram_region(key, [], [])}\n"
            f"{GIST_START}\n{GIST_END}\n")
```

- [ ] **Step 6: Run the full suite and fix the assertions this moves**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t8.txt 2>&1; echo "exit=$?"; grep -E "^(FAILED|ERROR)" /tmp/t8.txt`
Expected: `exit=0`

- [ ] **Step 7: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/
git commit -m "feat(decision-map): GitHub backend carries milestones and the new card order (ADRs 0099, 0102)"
```

---

### Task 9: Update the data contract

The contract is the source of truth both backends answer to — it is not
documentation of the code, it is the specification a third backend implements.

**Files:**
- Modify: `plugins/decision-map/references/data-contracts.md`

**Interfaces:**
- Consumes: the shapes Tasks 1-8 actually implement — read them off the code, not off this plan
- Produces: no code; the contract's normative text

- [ ] **Step 1: Add the milestone concept and the two regions**

Add a section after "`chart` is additive", covering: what a milestone is
(ADR 0094/0095), that membership and order live in one region on the map
(ADR 0096), the exact line grammar with a worked example, exclusivity and the
legality of an unassigned ticket (ADR 0097), and what the additive merge applies
versus reports (ADR 0098). State the grammar precisely enough to implement from:
the anchored form, order-is-line-order, and that members cannot contain
brackets.

- [ ] **Step 2: Update `map_input.json`, `map.json` and `frontier.json`**

- `map_input.json`: `map.milestones` (optional, ordered, `{slug, label?, members}`), and `map.notes` now `str | list[str]`.
- `map.json`: the top-level `milestones` list and each ticket's `milestone`.
- `frontier.json`: the top-level `milestones` progress list and each entry's `milestone`. Say explicitly that the three buckets stay **key-ascending** (ADR 0062 is unchanged) and that milestone order is carried separately for the consumer to sort by.

- [ ] **Step 3: Update the `lint` rule table**

Add the four new rows, all **error** severity, with the harm each names. Then
fix the sentence that reads "**`gist-budget` is the only finding that carries
`ticket: null`**" — `milestone-line-unparsable` and `milestone-duplicate-slug`
do too, being map-level. Keep the surrounding warning that a consumer must not
assume `finding.ticket` is a key.

- [ ] **Step 4: Update the merge-detail vocabulary**

The `merge` `detail` strings now include `adds 1 milestone line`,
`adds 1 milestone member line` and `adds N notes lines`. Add them beside the
existing `adds 2 fog lines, 1 out-of-scope line` example, and keep the rule that
no `merge` entry may carry `detail: null`.

- [ ] **Step 5: Note the notes-region transition**

Record that a map whose Notes is still a paragraph keeps the scalar-divergence
behaviour, that the region is created only when a notes list is first declared,
and that `scalar_fields_for` is what keeps the two from double-reporting.

- [ ] **Step 6: Verify the doc against the code**

Re-read the doc against `map_core.py` and both backends. Every shape stated must
match what the tests assert. Grep for any count or "only" claim you introduced
and check it against the data — a generated-doc prose claim that contradicts its
own inputs is the failure mode this repo has hit twice.

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t9.txt 2>&1; echo "exit=$?"`
Expected: `exit=0` (the doc changes nothing, but prove the tree is still green)

- [ ] **Step 7: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/references/data-contracts.md
git commit -m "docs(decision-map): contract covers milestones, the notes region and four lint rules"
```

---

### Task 10: The two flow skills, the version bump, and the docs

**Files:**
- Modify: `plugins/decision-map/skills/chart-map/SKILL.md` (Step 2 ~149, Step 3 ~184)
- Modify: `plugins/decision-map/skills/work-map/SKILL.md` (Step 1 ~160-208, Step 2 ~210, Step 5 ~467)
- Modify: `plugins/decision-map/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`
- Modify: `plugins/decision-map/README.md`, `CONTEXT.md` if either states a shape this changed

**Interfaces:**
- Consumes: the JSON shapes from Tasks 6 and 8
- Produces: prose only — no code

- [ ] **Step 1: chart-map asks what ships first**

In Step 2, after the Ticket/Fog/Out-of-scope table, add the milestone question
(ADR 0100): once the tickets are named, ask which increment the user wants
first — in their own terms ("what do you want to be able to demo first?"), one
question, skippable, and say plainly that skipping it costs nothing and the
grouping can be declared later from `work-map`. Frame it the way this repo
requires: short sentences, at most two options, the recommendation first.

In Step 3, add `milestones` to the `map_input.json` template and its bullet
list:

```json
    "milestones": [
      { "slug": "mvp", "label": "demo the search page",
        "members": ["provider-choice"] }
    ],
```

with bullets stating: order is the list's order; a slug follows the same rule as
a ticket key (no `--`); a ticket belongs to at most one milestone; a ticket in
none is legal and means "not yet scheduled"; and that a later `chart` appends
milestones and unions members but reports a move, a reorder or a changed label
as a divergence rather than applying it.

- [ ] **Step 2: work-map presents the frontier grouped**

In Step 1's presentation list, replace the flat "frontier by ticket name" bullet
with the grouped form (ADR 0099): walk `frontier.json`'s `milestones` in order,
and under each show its progress and its takeable tickets by name, then the
unassigned tail. Keep the existing discipline — one line per item, around ten
lines total, group rather than itemize on a big map. Note that `read` carries
membership and `frontier` carries progress, and that the three buckets are still
key-ascending so milestone order comes from the `milestones` list.

Also update the paragraph that says the fog, out-of-scope and notes lists "live
only in the map document" — notes may now be a region, and the milestones region
is a fourth thing `read` does report (via `milestones`), so correct both halves.

- [ ] **Step 3: work-map's recommendation becomes two-level**

In Step 2, replace "recommend the first frontier ticket … usually that it
unblocks the most" with the two-level rule: the earliest **incomplete**
milestone first, then the existing "unblocks the most" heuristic inside it; an
unassigned ticket is recommended only when every milestone is complete or has
nothing takeable. Say the reason in one line — the ordering was decided once, on
the map, so a session does not re-derive it.

- [ ] **Step 4: work-map offers milestones once on a big unmilestoned map**

Add to Step 1, after the frontier presentation: when `frontier.json.milestones`
is empty and more than five tickets are open, offer **one line** — "this map has
no milestones; want to group what ships first before picking?" — once per
session, never repeated, and declining changes nothing. Say why the threshold
exists: a small map does not need an ordering layer, and milestones must never
become a toll on one.

- [ ] **Step 5: work-map Step 5 covers milestone graduation**

Note in Step 5 that a resolution may also sharpen the milestone list, that new
milestones and new members go in the same additive `chart` input (and appear in
the plan as `adds 1 milestone line` / `adds 1 milestone member line`), and that
a **move** between milestones is a hand edit of the region — the same shape as
deleting a graduated fog line, with `lint` as the check afterwards. Add the four
new lint rules to the Step 6 list of what `lint` catches.

- [ ] **Step 6: Bump both versions to 0.10.0**

Re-verify the global max first (a parallel session may have minted since this
plan was written):

```bash
cd "$(git rev-parse --show-toplevel)"
for r in $(git for-each-ref --format='%(refname:short)' refs/heads refs/remotes); do
  git show "$r:plugins/decision-map/.claude-plugin/plugin.json" 2>/dev/null |
    grep -o '"version": "[^"]*"' | head -1
done | sort -u
```

Then set the same new version in `plugins/decision-map/.claude-plugin/plugin.json`
and in the `decision-map` entry of `.claude-plugin/marketplace.json`. They must
match exactly.

- [ ] **Step 7: Validate the plugin and check for stale shapes**

```bash
cd "$(git rev-parse --show-toplevel)"
claude plugin validate plugins/decision-map
claude plugin validate .
grep -rn "## Notes" plugins/decision-map/ README.md CONTEXT.md
grep -rn "Decisions so far" plugins/decision-map/README.md
```

Fix any doc that describes the old map-body shape. Confirm `CONTEXT.md`'s
**Milestone** term still matches what shipped.

- [ ] **Step 8: Run the full suite one last time**

Run: `cd "plugins/decision-map/scripts" && python -m pytest test_local_map_ops.py test_github_map_ops.py -q > /tmp/t10.txt 2>&1; echo "exit=$?"; tail -2 /tmp/t10.txt`
Expected: `exit=0`

- [ ] **Step 9: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/ .claude-plugin/marketplace.json CONTEXT.md
git commit -m "feat(decision-map): 0.10.0 - the flow skills group by milestone and ask what ships first"
```

---

## Self-Review

**Spec coverage** — every ADR maps to at least one task:

| ADR | Where it lands |
|---|---|
| 0094 milestone grouping is the ordering dimension | Tasks 1, 6, 8 (the data), Task 10 (the surface) |
| 0095 first-class structure | Tasks 1, 3 (a real region, not a ticket) |
| 0096 membership + order on the map, one region | Tasks 1, 3 |
| 0097 at most one milestone per ticket | Task 2 (input), Task 4 (lint), Task 1 (`milestone_index` first-wins) |
| 0098 additive declaration, hand-edited moves | Task 3 (`merge_milestones` + divergences), Task 10 Step 5 |
| 0099 grouped frontier, two-level recommendation | Tasks 6, 8 (`milestones` + `milestone`), Task 10 Steps 2-3 |
| 0100 offered at chart time and once per session | Task 10 Steps 1 and 4 |
| 0101 notes as an append-only bullet region | Tasks 2, 3 (`notes_lines`, `scalar_fields_for`, the merge) |
| 0102 Question above the diagram | Task 7 (local + `set_graph_region`), Task 8 Step 5 (GitHub) |
| 0103 grouped decisions index | Task 5 |

**Type consistency** — the names used across tasks:
`milestone_line`, `milestone_lines_for`, `parse_milestones`, `milestone_index`,
`milestone_progress`, `notes_lines`, `scalar_fields_for`, `merge_milestones`,
`_validate_milestones`. A milestone dict is `{"slug", "label", "members"}`
everywhere; a progress dict is `{"slug", "label", "closed", "total",
"complete"}` everywhere. `decisions_region` takes four-tuples
`(key, title, link, gist)` from Task 5 on, and both callers change in that same
task. `local_map_ops.py` imports `map_core` names under a leading underscore
(`_milestone_index`, `_milestone_progress`, `_scalar_fields_for`) to match its
existing convention; `github_map_ops.py` imports them bare, to match its own.

**Two things to watch while implementing:**

1. **Task 3 is where the map body changes for both backends**, so its test-fixing
   step is the largest. Read each failure before editing: a failure asserting
   the old `## Notes` paragraph is expected, and one asserting a byte-identical
   no-op is a real bug in the merge.
2. **`assert_regions` counts every `<!-- decision-map:` occurrence** and requires
   each to belong to a declared region. Both new regions are added to
   `MAP_REGIONS` in Task 1 Step 3 — if that edit is missed, every map write
   fails with `MarkerIntegrityError` rather than silently misbehaving, which is
   the intended failure direction.
