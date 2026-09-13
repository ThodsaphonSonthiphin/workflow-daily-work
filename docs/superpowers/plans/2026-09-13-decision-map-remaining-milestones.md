# decision-map — the map says which milestones remain: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make a Decision map say, in the map file itself, which milestones exist, which are done and which remain — from the moment it is charted until work-map declares it done.

**Architecture:** Three changes on one shared core. (1) `map_core.decisions_region` renders every declared milestone as a heading with `closed/total` (ADR 0211). (2) Both backends re-project that index whenever they write the map body — `resolve` as today, plus any `chart` that creates, merges or overwrites the map — folded into the write they already make, never an extra one. (3) The two flow skills change what they ask and what they refuse: chart-map asks "and after that?" until the user stops, writing an increment with no ticket yet as an empty milestone (ADR 0210); work-map treats an empty milestone as fog before it will call the map done (ADR 0212). Contract, README and versions follow.

**Tech Stack:** Python 3 stdlib (`python3` — macOS has no bare `python`), `unittest` suites run as scripts, Markdown skills, Mermaid diagrams.

**Spec:** `docs/superpowers/specs/2026-09-13-decision-map-remaining-milestones-design.md` (ADRs 0210–0212, banners on ADRs 0100 and 0103).

## Global Constraints

- **Versions in sync:** `plugins/decision-map/.claude-plugin/plugin.json` and the `decision-map` entry in `.claude-plugin/marketplace.json` both go `0.12.0 → 0.13.0`, in the same commit (Task 7).
- **The contract is the single source of truth:** `plugins/decision-map/references/data-contracts.md` defines every shape; the skills must not restate a rule the contract owns, only point at it.
- **Harness-neutral skills:** name actions, never one harness's tool. `${CLAUDE_PLUGIN_ROOT}` only in the shapes `/references/…`, `/scripts/…`, `/skills/…`. This plan adds no new reference of that kind.
- **The generated skills tree is committed:** after any edit under `plugins/*/skills/`, run `python3 scripts/generate_skills_tree.py` from the repo root and commit the resulting `skills/…` changes; `python3 scripts/check_skills_tree.py --repo .` must exit 0. Never hand-edit `skills/`.
- **`.agents/skills/` is out of scope.** It is the project-scope install snapshot of the skills CLI, tracked together with `skills-lock.json` (one `computedHash` per skill). It is refreshed by that CLI, not by hand and not by this plan; after merge the owner re-runs the install. Do not edit it.
- **JSON shapes do not change:** `map.json` and `frontier.json` are untouched. No new subcommand, no new lint rule.
- **Byte-identical no-op stays:** an identical re-chart writes nothing on either backend. The index is re-projected only inside a write that happens anyway (map `create` / `merge` with a body / `OVERWRITE`); a map labelled `skip (exists)` is never touched, even if its index is stale.
- **Rendering grammar (the one place it is defined is `decisions_region`; tests pin it):**
  - heading: `#### <slug>` + (` — <label>` if a label) + ` (<closed>/<total> closed)`; for `total == 0`: ` (0/0 closed — no tickets yet)`;
  - body: the closed entries key-ascending as today; `_nothing closed yet_` when `total > 0` and nothing closed; nothing when `total == 0`;
  - the `#### (unassigned)` tail as today; an unmilestoned map is unchanged (flat list; `START\nEND\n` when empty).
- **Tests:** run from `plugins/decision-map/scripts/`: `python3 test_local_map_ops.py` (baseline 219 OK) and `python3 test_github_map_ops.py` (baseline 134 OK). Single test: `python3 -m unittest test_local_map_ops.DecisionsIndexGroupingTest -v`.
- **Commits:** `feat(decision-map): …`, `test(decision-map): …`, `docs(decision-map): …`, `chore(skills): …`; every commit ends with the trailer `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` (pass it as a second `-m`).
- **ADR numbers are minted from the global max.** 0210–0212 were minted on 2026-09-13 against max 0209. Re-run the scan in the grilling skill's `ADR-FORMAT.md` (the `python3`-parsed variant in this repo's memory notes — the GNU-sed one prints an empty number on macOS) immediately before merging; if a parallel branch has taken a number, renumber the file and every citation of it (spec, plan, banners, CONTEXT.md).

---

### Task 0: Branch, commit the design records, repair the pre-existing skills-tree drift

**Files:**
- Commit (already in the working tree, uncommitted): `CONTEXT.md`, `docs/adr/workflow-daily-work-0210-*.md`, `docs/adr/workflow-daily-work-0211-*.md`, `docs/adr/workflow-daily-work-0212-*.md`, `docs/adr/workflow-daily-work-0100-*.md`, `docs/adr/workflow-daily-work-0103-*.md`, `docs/superpowers/plans/2026-08-19-decision-map-milestones-and-readability.md`, `docs/superpowers/specs/2026-09-13-decision-map-remaining-milestones-design.md`, `docs/superpowers/plans/2026-09-13-decision-map-remaining-milestones.md` (this file)
- Create (generated): `skills/practice-english-writing/**` — pre-existing drift on this branch, not part of this feature

**Interfaces:**
- Produces: the branch `decision-map-remaining-milestones` every later task commits to; a clean `check_skills_tree.py` baseline so Task 5/6 diffs contain only their own files.

- [ ] **Step 1: Branch from the current HEAD**

The working tree sits on `career-growth-paid-test-breadth` at `e3b99ba`. The design records are uncommitted there, so branch from HEAD (they come along); the owner decides the merge order later.

```bash
cd "$(git rev-parse --show-toplevel)"
git checkout -b decision-map-remaining-milestones
git status --short
```

Expected: `M CONTEXT.md`, the two `M docs/adr/…0100…` / `…0103…`, `M docs/superpowers/plans/2026-08-19-…`, and `??` for the three new ADRs, the spec and this plan. Nothing else.

- [ ] **Step 2: Commit the design records**

```bash
git add CONTEXT.md docs/adr docs/superpowers/specs/2026-09-13-decision-map-remaining-milestones-design.md \
        docs/superpowers/plans/2026-08-19-decision-map-milestones-and-readability.md \
        docs/superpowers/plans/2026-09-13-decision-map-remaining-milestones.md
git commit -m "docs(decision-map): design for the map saying which milestones remain (ADRs 0210-0212)" \
           -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 3: Confirm the pre-existing skills-tree drift, then repair it on its own commit**

```bash
python3 scripts/check_skills_tree.py --repo . ; echo "exit $?"
```

Expected (measured 2026-09-13, before this plan touched anything): two findings, both `missing from skills/: practice-english-writing/…`, exit 1. If any finding names another skill, stop and report — that is not the known drift.

```bash
python3 scripts/generate_skills_tree.py
git status --short skills/
```

Expected: only `?? skills/practice-english-writing/` (no `M` lines). If other files change, stop and report before committing.

```bash
git add skills/practice-english-writing
git commit -m "chore(skills): regenerate skills/ for practice-english-writing (pre-existing drift)" \
           -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
python3 scripts/check_skills_tree.py --repo . ; echo "exit $?"
```

Expected: `0 finding(s)` / exit 0.

- [ ] **Step 4: Baseline the two suites**

```bash
cd plugins/decision-map/scripts && python3 test_local_map_ops.py 2>&1 | tail -3 && python3 test_github_map_ops.py 2>&1 | tail -3
```

Expected: `Ran 219 tests … OK` and `Ran 134 tests … OK`.

---

### Task 1: `decisions_region` renders every declared milestone with its progress (ADR 0211)

**Files:**
- Modify: `plugins/decision-map/scripts/map_core.py:930-1002` (`decisions_region`, whole function)
- Test: `plugins/decision-map/scripts/test_local_map_ops.py:3258-3323` (`DecisionsIndexGroupingTest`)

**Interfaces:**
- Consumes: `map_core.milestone_progress(milestones, status_by_key) -> [{slug, label, closed, total, complete}]` (exists, `map_core.py:564`), `map_core.membership_of(milestones) -> {key: slug}` (exists, `:541`), `map_core.one_line(v)` (exists, `:285`).
- Produces: `map_core.decisions_region(entries, milestones=None) -> str` — **same signature**, new output. `entries` is `[(key, title, link, gist), …]` of the CLOSED tickets only (both backends already pass exactly that). Tasks 2 and 3 rely on the grammar in Global Constraints and on the fact that `milestones` may contain entries with `"members": []`.

- [ ] **Step 1: Rewrite the three affected tests and add four new ones**

In `test_local_map_ops.py`, inside `class DecisionsIndexGroupingTest` (line 3258), replace `test_grouped_by_milestone_in_map_order_with_an_unassigned_tail`, `test_a_milestone_with_no_closed_decision_is_not_rendered` and `test_empty_entries_with_milestones_supplied_is_still_unchanged` with the following, and add the three new tests (`…says_so_in_its_heading…`, `…equals_milestone_progress`, `…duplicated_slug…`). Leave every other test in the class untouched (`test_no_milestones_renders_todays_flat_list`, `test_entries_stay_key_ascending_inside_a_group`, `test_a_heading_label_is_flattened_and_escaped`, `test_the_region_markers_still_frame_it_exactly_once`, `test_empty_entries_and_no_milestones_is_byte_identical_to_before` keep passing unchanged).

```python
    def test_grouped_by_milestone_in_map_order_with_an_unassigned_tail(self):
        ms = [{"slug": "two", "label": "second", "members": ["b"]},
              {"slug": "one", "label": None, "members": ["a"]}]
        got = map_core.decisions_region(self.ENTRIES, ms)
        # Milestone order comes from the REGION, not from the keys.
        self.assertLess(got.index("#### two"), got.index("#### one"))
        self.assertIn("#### two — second (1/1 closed)\n", got)
        self.assertIn("#### one (1/1 closed)\n", got)
        self.assertLess(got.index("#### one"), got.index("(unassigned)"))
        # Unassigned decisions are a tail group, never dropped.
        self.assertIn("- [Z?](tickets/z.md) — maybe", got.split("(unassigned)")[1])

    def test_a_milestone_with_no_closed_decision_is_rendered_with_a_placeholder(self):
        # ADR 0211 withdraws ADR 0103's omission: a reader of map.md must see
        # that the increment exists and that nothing in it has closed yet.
        ms = [{"slug": "empty", "label": None, "members": ["nobody"]},
              {"slug": "one", "label": None, "members": ["a"]}]
        got = map_core.decisions_region(self.ENTRIES, ms)
        self.assertIn("#### empty (0/1 closed)\n\n_nothing closed yet_\n", got)
        self.assertLess(got.index("#### empty"), got.index("#### one"))

    def test_an_empty_milestone_says_so_in_its_heading_and_has_no_body(self):
        # The placeholder chart-map writes for an increment whose decisions are
        # still fog (ADR 0210): the heading is the whole information.
        ms = [{"slug": "later", "label": "retire the old provider", "members": []}]
        got = map_core.decisions_region(self.ENTRIES, ms)
        self.assertIn(
            "#### later — retire the old provider (0/0 closed — no tickets yet)\n", got)
        self.assertNotIn("_nothing closed yet_", got)
        # every entry is unassigned here, so the tail carries all three
        self.assertIn("#### (unassigned)", got)
        self.assertEqual(got.count("- ["), 3)

    def test_progress_in_the_heading_equals_milestone_progress(self):
        # The heading is computed by the same function frontier.json reports
        # through, so the file and the JSON cannot disagree -- including on a
        # repeated member, which is counted once, and an open member (q).
        ms = [{"slug": "one", "label": None, "members": ["a", "a", "b", "q"]}]
        got = map_core.decisions_region(self.ENTRIES, ms)
        row = map_core.milestone_progress(ms, {"a": "closed", "b": "closed"})[0]
        self.assertEqual((row["closed"], row["total"]), (2, 3))
        self.assertIn("#### one (2/3 closed)\n", got)

    def test_a_duplicated_slug_renders_once_with_its_first_declarations_count(self):
        # A lint error (milestone-duplicate-slug), but the region must still
        # render deterministically: once, under the first entry -- the same
        # first-wins rule frontier.json's rows and membership_of already use.
        ms = [{"slug": "one", "label": "first", "members": ["a"]},
              {"slug": "one", "label": "again", "members": ["b"]}]
        got = map_core.decisions_region(self.ENTRIES, ms)
        self.assertEqual(got.count("#### one"), 1)
        self.assertIn("#### one — first (1/1 closed)\n", got)

    def test_empty_entries_with_milestones_render_their_headings(self):
        # A milestoned map with nothing closed is no longer START/END: the
        # headings ARE the information -- "these increments exist, 0/N done".
        ms = [{"slug": "one", "label": None, "members": ["a"]}]
        self.assertEqual(
            map_core.decisions_region([], ms),
            f"{map_core.DECISIONS_START}\n#### one (0/1 closed)\n\n"
            f"_nothing closed yet_\n{map_core.DECISIONS_END}\n")
```

- [ ] **Step 2: Run the class to verify the new tests fail**

```bash
cd plugins/decision-map/scripts && python3 -m unittest test_local_map_ops.DecisionsIndexGroupingTest -v 2>&1 | tail -15
```

Expected: FAIL on the six tests above (assertions on `(1/1 closed)`, `(0/1 closed)`, `no tickets yet`, `(2/3 closed)`, and the exact `[]`-entries string); the five untouched tests pass.

- [ ] **Step 3: Replace `decisions_region` in `map_core.py`**

Replace the whole function (from `def decisions_region(entries, milestones=None):` through its `return`, currently lines 930–1002) with:

```python
def decisions_region(entries, milestones=None):
    """The "Decisions so far" index, regenerated in full inside its own region.

    The index is a projection of the tickets, not accumulated state, so it is
    rebuilt wholesale. There is no per-line pattern to match and nothing
    outside the region is read or touched -- which is what stops a
    user-authored, index-shaped line elsewhere in the map body from being
    substituted away, and stops a multi-line gist from splitting one entry into
    an orphanable pair.

    `entries` is [(key, title, link, gist), ...] -- the CLOSED tickets and
    only those; the key is carried so this can group by milestone. **Ordered
    by ticket key (ascending)** within each group, not by when each decision
    was resolved, so the index is a deterministic function of state; the
    caller sorts, this only formats.

    `milestones` is the map's parsed milestone list. Given one, the index is
    the map's STATUS BOARD (ADR 0103, ADR 0211): one `#### ` heading per
    DECLARED milestone in MAP order -- not key order, because the whole point
    of a milestone list is that its order is chosen -- each carrying
    `(<closed>/<total> closed)`, then an "(unassigned)" tail. A milestone with
    nothing closed yet is rendered, not omitted: its heading is the
    information ("this increment exists, 0/N done"), with a
    `_nothing closed yet_` line under it; an EMPTY milestone (no members)
    says `(0/0 closed — no tickets yet)` in the heading and has no body. The
    counts come from `milestone_progress`, the same function `frontier`
    reports through, with every entry here counted as closed -- so the file
    and frontier.json cannot disagree, including on a repeated member.
    Membership comes from `membership_of` -- the same first-occurrence-wins
    mapping `milestone_index` builds -- and a duplicated slug (a lint error)
    renders ONCE, under its first declaration, with that declaration's row.
    With no milestones at all the output is the flat list this function has
    always produced, so an unmilestoned map is unchanged.
    """
    lines = []

    def render(group):
        for _key, title, link, gist in group:
            lines.append(f"- [{title}]({link}) — {gist}".rstrip() + "\n")

    if not milestones:
        render(entries)
    else:
        by_key = membership_of(milestones)
        rows = milestone_progress(
            milestones, {key: "closed" for key, _t, _l, _g in entries})
        # Tracked by KEY rather than by removing tuples from a shrinking list:
        # the key is the identity these entries are joined on everywhere else.
        taken, seen = set(), set()
        for m, row in zip(milestones, rows):
            slug = m["slug"]
            if slug in seen:
                continue
            seen.add(slug)
            group = [e for e in entries
                     if e[0] not in taken and by_key.get(e[0]) == slug]
            taken.update(e[0] for e in group)
            heading = f"#### {slug}"
            if m.get("label"):
                # one_line even though this label was read back OUT of the map:
                # every user string written into a document goes through it, and
                # this is the one document -> document text path. Safe today only
                # because the write side escaped it and assert_regions refuses a
                # hand-forged marker -- defence in depth on the invariant, not a
                # second opinion about it. Idempotent, so a label that was
                # already escaped is unchanged.
                heading += f" — {one_line(m['label'])}"
            if row["total"] == 0:
                heading += " (0/0 closed — no tickets yet)"
            else:
                heading += f" ({row['closed']}/{row['total']} closed)"
            lines.append(heading + "\n\n")
            if group:
                render(group)
                lines.append("\n")
            elif row["total"]:
                lines.append("_nothing closed yet_\n\n")
        remaining = [e for e in entries if e[0] not in taken]
        if remaining:
            lines.append("#### (unassigned)\n\n")
            render(remaining)
    # An empty index -- no closed tickets on an UNMILESTONED map -- must render
    # as START\nEND\n, byte-identical to the pre-milestone format: a bare
    # "".join(lines) here would leave a blank line between the markers and turn
    # every empty map into a spurious diff against the byte-identical no-op
    # guarantee. A milestoned map is never empty here: its headings are the
    # information (ADR 0211).
    body = "".join(lines).rstrip("\n")
    return (f"{DECISIONS_START}\n{body}\n{DECISIONS_END}\n" if body
            else f"{DECISIONS_START}\n{DECISIONS_END}\n")
```

- [ ] **Step 4: Run the class, then both whole suites**

```bash
cd plugins/decision-map/scripts && python3 -m unittest test_local_map_ops.DecisionsIndexGroupingTest -v 2>&1 | tail -15
python3 test_local_map_ops.py 2>&1 | tail -3 && python3 test_github_map_ops.py 2>&1 | tail -3
```

Expected: the class passes (11 tests). Local suite `Ran 222 tests … OK` (219, with three tests replaced in place and three added). GitHub suite `Ran 134 tests … OK` — `GitHubGroupedIndexTest.test_resolving_writes_a_grouped_index` only checks the `#### mvp — demo it` prefix. The lint test at `test_local_map_ops.py:3152-3156` (`region.count("#### mvp") == 1`, `"#### mvp — first" in region`) also still passes.

- [ ] **Step 5: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/map_core.py plugins/decision-map/scripts/test_local_map_ops.py
git commit -m "feat(decision-map): the decisions index shows every declared milestone with its progress (ADR 0211)" \
           -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: The local backend re-projects the index whenever `chart` writes `map.md`

**Files:**
- Modify: `plugins/decision-map/scripts/local_map_ops.py:381-395` (`_chart_plan` docstring), `:501-575` (`chart`)
- Test: `plugins/decision-map/scripts/test_local_map_ops.py:3325-3354` (`LocalGroupedIndexTest`)

**Interfaces:**
- Consumes: `_reindex_decisions(root, slug)` (exists, `local_map_ops.py:737` — reads every ticket's frontmatter, renders `decisions_region(entries, milestones)` with the milestones parsed fresh from `map.md`, and writes `map.md` through `_write_map_md`); `_snapshot(base)` and `_DIAGRAM_BODY` (module-level helpers in the test file, lines 18 and 2167).
- Produces: the observable rule Task 4 documents — `chart --real` leaves the index current whenever the plan's `map.md` action was `create`, `merge` or `OVERWRITE`; a `skip (exists)` map is never written.

- [ ] **Step 1: Add a helper and four tests to `LocalGroupedIndexTest`**

Inside `class LocalGroupedIndexTest` (line 3325), after `tearDown`, add the helper and the tests:

```python
    def _decisions(self):
        text = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        return map_core.region_body(text, map_core.DECISIONS_START,
                                    map_core.DECISIONS_END)

    def test_charting_milestones_writes_their_headings_before_anything_closes(self):
        # ADR 0211: the index is the map's status board from day one, so a
        # freshly charted map already says which increments exist and 0/N.
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it",
             "members": ["auth-model", "rollout-order"]},
            {"slug": "later", "label": "retire the old provider", "members": []}]
        ops.chart(self.root, inp, real=True)
        body = self._decisions()
        self.assertIn("#### mvp — demo it (0/2 closed)\n\n_nothing closed yet_\n", body)
        self.assertIn(
            "#### later — retire the old provider (0/0 closed — no tickets yet)\n", body)

    def test_an_additive_chart_that_adds_a_milestone_writes_its_heading_in_the_same_run(self):
        ops.chart(self.root, copy.deepcopy(INPUT), real=True)
        self.assertNotIn("####", self._decisions(), "unmilestoned: flat and empty")
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it", "members": ["auth-model"]}]
        ops.chart(self.root, inp, real=True)
        self.assertIn("#### mvp — demo it (0/1 closed)", self._decisions())

    def test_an_identical_re_chart_never_rewrites_a_stale_index(self):
        # The trigger is "the map body is being written anyway", never "the
        # index is stale": a ticket closed by hand (no resolve) leaves the index
        # behind, and an identical re-chart must still be a byte-identical no-op.
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it", "members": ["auth-model"]}]
        ops.chart(self.root, inp, real=True)
        ticket = self.root / "example-effort" / "tickets" / "auth-model.md"
        ticket.write_text(ticket.read_text(encoding="utf-8")
                          .replace("status: open", "status: closed", 1),
                          encoding="utf-8")
        before = _snapshot(self.root / "example-effort")
        ops.chart(self.root, copy.deepcopy(inp), real=True)
        self.assertEqual(_snapshot(self.root / "example-effort"), before)
        self.assertIn("(0/1 closed)", self._decisions(), "stale, and left so")

    def test_force_leaves_the_index_fully_re_projected(self):
        # The contract used to say --force empties the index until the next
        # resolve. It now re-projects it from the state the rewrite leaves: a
        # still-closed ticket the input does not name stays listed, and a
        # rewritten (reopened) one drops out.
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it",
             "members": ["auth-model", "rollout-order"]}]
        ops.chart(self.root, inp, real=True)
        ops.resolve(self.root, "example-effort", "auth-model", "per-tenant keys",
                    "docs/adr/x.md", _DIAGRAM_BODY)
        ops.resolve(self.root, "example-effort", "rollout-order", "prod last",
                    "docs/adr/y.md", _DIAGRAM_BODY)
        narrow = copy.deepcopy(inp)
        narrow["tickets"] = [t for t in inp["tickets"] if t["key"] == "rollout-order"]
        ops.chart(self.root, narrow, real=True, force=True)
        body = self._decisions()
        self.assertIn("#### mvp — demo it (1/2 closed)", body)
        self.assertIn("per-tenant keys", body, "untouched and still closed: listed")
        self.assertNotIn("prod last", body, "rewritten, so open again: dropped")
```

- [ ] **Step 2: Run the class to verify the new tests fail**

```bash
cd plugins/decision-map/scripts && python3 -m unittest test_local_map_ops.LocalGroupedIndexTest -v 2>&1 | tail -12
```

Expected: `test_charting_milestones_writes_their_headings_before_anything_closes`, `…adds_a_milestone…`, and `test_force_leaves_the_index_fully_re_projected` FAIL (the region is empty after `chart`; `--force` empties it). `test_an_identical_re_chart_never_rewrites_a_stale_index` may already pass (the no-op holds today) — that is fine, it is the guard for Step 3. The two existing tests pass.

- [ ] **Step 3: Re-project in `chart()` after the passes, only when `map.md` was written**

In `local_map_ops.py`, inside `chart()` (line 501), after the pass-3 `for key in refresh:` loop and before `for d in div: print(f"chart: divergence: {d}", file=sys.stderr)`, add:

```python
    # ADR 0211: the map body was written above (create / merge / OVERWRITE), so
    # the decisions index it carries is re-projected in this same run -- every
    # declared milestone with its closed/total, the ones this run declared
    # included. Done after the passes so the tickets this run created (open)
    # and the ones --force reopened are what the projection sees. A map
    # labelled "skip (exists)" was not written and is not touched here either:
    # a stale index is never the reason an identical re-chart writes.
    if actions[base / "map.md"] != "skip (exists)":
        _reindex_decisions(root, slug)
```

Then, in `_chart_plan`'s docstring (line 388–390), change the `"merge"` line's description from

```
      - "merge"         the file exists and is modified in place, additively:
                        map.md gaining fog / out-of-scope lines, or a ticket
                        gaining a blockedBy entry (ADR 0058)
```

to

```
      - "merge"         the file exists and is modified in place, additively:
                        map.md gaining fog / out-of-scope / milestone lines
                        (and, whenever map.md is written at all, its decisions
                        index re-projected -- ADR 0211), or a ticket gaining a
                        blockedBy entry (ADR 0058)
```

- [ ] **Step 4: Run the class, then the whole local suite**

```bash
cd plugins/decision-map/scripts && python3 -m unittest test_local_map_ops.LocalGroupedIndexTest -v 2>&1 | tail -12
python3 test_local_map_ops.py 2>&1 | tail -3
```

Expected: the class passes (6 tests); `Ran 226 tests … OK`. In particular `test_rechart_identical_input_is_a_byte_identical_no_op` (line 980), `test_an_identical_re_chart_is_byte_identical` (line 2715) and `test_additive_chart_preserves_a_resolution_and_its_index_entry` (line 990) still pass — a skipped map is never reindexed.

- [ ] **Step 5: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/local_map_ops.py plugins/decision-map/scripts/test_local_map_ops.py
git commit -m "feat(decision-map): local chart re-projects the decisions index when it writes map.md (ADR 0211)" \
           -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: The GitHub backend folds the projection into the map write `chart` already makes

**Files:**
- Modify: `plugins/decision-map/scripts/github_map_ops.py:1480-1523` (`_reindex_decisions` — split into three functions), `:1130-1160` (`chart`, the map create / patch block)
- Test: `plugins/decision-map/scripts/test_github_map_ops.py:607-631` (`GitHubGroupedIndexTest`)

**Interfaces:**
- Consumes: `decisions_region` (Task 1), `milestone_index(text) -> (milestones, membership, bad_lines)` (imported at `github_map_ops.py:88`), `Snapshot.keys`, `Snapshot.tickets`, `Snapshot.gist_of(key)`, `Snapshot.milestones`, `_state(gql_state)`, `norm_eol`, `one_line`, `_DECISIONS_BLOCK_RE` (line 113), `_assert_map_body(text, what)`, `FakeGitHub.writes` (`(method, path, payload)` tuples), `FakeGitHub.reset_counters()`, `FakeGitHub.write_count`, `FakeGitHub.body_of(number)`.
- Produces: `_decisions_entries(snap, just_closed=None, just_gist=None, reopened=()) -> [(key, title, url, gist)]` and `_project_decisions(body, entries, milestones) -> str` (pure). `_reindex_decisions(ops, snap, just_closed, just_gist)` keeps its signature and its single PATCH.

- [ ] **Step 1: Add a helper and four tests to `GitHubGroupedIndexTest`**

Inside `class GitHubGroupedIndexTest(Base)` (line 607), add:

```python
    def _decisions(self):
        body = map_core.norm_eol(self.fake.body_of(self.map_number()))
        return map_core.region_body(body, map_core.DECISIONS_START,
                                    map_core.DECISIONS_END)

    def test_charting_milestones_writes_their_headings_in_the_create_call(self):
        # ADR 0211 on a tracker: the index rides in the POST that creates the
        # map -- never a second write, which would show in the issue timeline
        # and bump the call budget the contract writes down.
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it", "members": ["auth-model"]},
            {"slug": "later", "label": "retire the old provider", "members": []}]
        self.chart(inp)
        inner = self._decisions()
        self.assertIn("#### mvp — demo it (0/1 closed)\n\n_nothing closed yet_\n", inner)
        self.assertIn(
            "#### later — retire the old provider (0/0 closed — no tickets yet)\n", inner)
        n = self.map_number()
        map_patches = [w for w in self.fake.writes
                       if w[0] == "PATCH" and w[1].endswith(f"/issues/{n}")]
        self.assertEqual(map_patches, [], self.fake.writes)

    def test_an_additive_chart_that_adds_a_milestone_patches_the_map_once_with_its_heading(self):
        self.chart()
        self.fake.reset_counters()
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it", "members": ["auth-model"]}]
        self.chart(inp)
        patched = [w for w in self.fake.writes if w[0] == "PATCH"]
        self.assertEqual(len(patched), 1, f"only the map body: {self.fake.writes}")
        self.assertIn("#### mvp — demo it (0/1 closed)", patched[0][2]["body"])

    def test_an_identical_re_chart_of_a_milestoned_map_writes_nothing(self):
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it", "members": ["auth-model"]}]
        self.chart(inp)
        self.fake.reset_counters()
        self.chart(inp)
        self.assertEqual(self.fake.write_count, 0, self.fake.writes)

    def test_force_leaves_the_index_fully_re_projected(self):
        # Mirror of the local test: a still-closed ticket the input does not
        # name stays listed; the rewritten one is open again and drops out.
        inp = copy.deepcopy(INPUT)
        inp["map"]["milestones"] = [
            {"slug": "mvp", "label": "demo it",
             "members": ["auth-model", "rollout-order"]}]
        self.chart(inp)
        gh.resolve(self.ops, "billing", "auth-model", "shared keys", None, None)
        gh.resolve(self.ops, "billing", "rollout-order", "prod last", None, None)
        narrow = copy.deepcopy(inp)
        narrow["tickets"] = [t for t in inp["tickets"] if t["key"] == "rollout-order"]
        self.chart(narrow, force=True)
        inner = self._decisions()
        self.assertIn("#### mvp — demo it (1/2 closed)", inner)
        self.assertIn("shared keys", inner, "untouched and still closed: listed")
        self.assertNotIn("prod last", inner, "rewritten, so open again: dropped")
```

- [ ] **Step 2: Run the class to verify the new tests fail**

```bash
cd plugins/decision-map/scripts && python3 -m unittest test_github_map_ops.GitHubGroupedIndexTest -v 2>&1 | tail -12
```

Expected: the create-call, additive and `--force` tests FAIL (the region is empty after `chart`); `test_an_identical_re_chart_of_a_milestoned_map_writes_nothing` may already pass; the two existing tests pass.

- [ ] **Step 3: Split `_reindex_decisions` into entries + projection + write**

Replace the whole of `_reindex_decisions` (from `def _reindex_decisions(ops, snap, just_closed, just_gist):` through `ops.patch_issue(snap.map["number"], {"body": body})`, currently lines 1480–1522) with:

```python
def _decisions_entries(snap, just_closed=None, just_gist=None, reopened=()):
    """The closed tickets of `snap`, as the index's (key, title, link, gist) rows.

    `just_closed` folds in the ticket this process closed after the snapshot
    was taken (`resolve`) -- cheaper and more consistent than re-reading the
    whole map to observe a change this process just made. `reopened` drops the
    tickets this process is about to reset to open (a --force chart), so the
    projection describes the state the run LEAVES, not the one it found.
    """
    entries = []
    for key in snap.keys:
        if key in reopened:
            continue
        t = snap.tickets[key]
        if key == just_closed:
            closed, gist = True, just_gist
        else:
            closed, gist = _state(t.get("state")) == "closed", (snap.gist_of(key) or "")
        if not closed:
            continue
        # The ticket's FULL URL, not `#N`. Inside an issue body `[title](#2)` is
        # a same-page fragment link that goes nowhere -- every entry in the index
        # a human is meant to click was dead. (A bare `#2` would auto-link, but
        # the shared index format is `- [title](link) — gist`, so the link has to
        # be a real one.) The url also survives being copied out of the tracker.
        entries.append((key, one_line(t.get("title") or key),
                        t.get("url") or f"#{t['number']}", gist))
    return entries


def _project_decisions(body, entries, milestones):
    """`body` with its "Decisions so far" region regenerated from `entries`,
    grouped by `milestones` (ADR 0103, ADR 0211). Pure: no read, no write.

    A body charted before the region existed gets a fresh region inserted
    under the heading rather than a guess at where its old loose list ended --
    the same conservative choice as the local backend's legacy path.
    """
    region = decisions_region(entries, milestones)
    if _DECISIONS_BLOCK_RE.search(body):
        return _DECISIONS_BLOCK_RE.sub(lambda _m: region, body, count=1)
    heading = "## Decisions so far\n"
    if heading in body:
        return body.replace(heading, heading + "\n" + region, 1)
    return body.rstrip("\n") + f"\n\n## Decisions so far\n\n{region}"


def _reindex_decisions(ops, snap, just_closed, just_gist):
    """Rebuild the map body's "Decisions so far" index from the snapshot.

    A projection, not accumulated state, so it is regenerated wholesale inside
    its own region and ordered by ticket key. The milestones that group it
    come from `snap.milestones`, not a fresh parse: `resolve` never edits the
    milestones region, so the snapshot's copy cannot be stale for this purpose,
    and re-parsing the same body the snapshot already read would be the
    duplication `Snapshot.__init__` exists to avoid. (`chart` is the other
    caller of the projection, and it DOES re-parse -- from the merged body it
    is about to write, whose milestones the snapshot predates. ADR 0211.)
    """
    body = _project_decisions(norm_eol(snap.map.get("body")),
                              _decisions_entries(snap, just_closed, just_gist),
                              snap.milestones)
    _assert_map_body(body, f"the map issue body (#{snap.map['number']})")
    ops.patch_issue(snap.map["number"], {"body": body})
```

- [ ] **Step 4: Fold the projection into `chart()`'s map create and patch**

In `chart()` (line 1091), the block that currently reads

```python
    map_action = actions["<map>"]
    if map_action == "create":
        _assert_map_body(map_body, "the map issue body")
        created = ops.create_issue(inp["map"]["title"], map_body, {MAP_LABEL})
        map_number = created["number"]
        snap_tickets = {}
    else:
        map_number = snap.map["number"]
        snap_tickets = dict(snap.tickets)
        payload = {}
        if map_action in ("merge", "OVERWRITE"):
            if map_body is not None:
                _assert_map_body(map_body, f"the map issue body (#{map_number})")
                payload["body"] = map_body
```

becomes

```python
    map_action = actions["<map>"]
    if map_action == "create":
        # ADR 0211: the index rides in the body this run creates -- every
        # declared milestone at 0/N, parsed from the rendered body -- never in
        # a second write to the map.
        map_body = _project_decisions(map_body, [], milestone_index(map_body)[0])
        _assert_map_body(map_body, "the map issue body")
        created = ops.create_issue(inp["map"]["title"], map_body, {MAP_LABEL})
        map_number = created["number"]
        snap_tickets = {}
    else:
        map_number = snap.map["number"]
        snap_tickets = dict(snap.tickets)
        payload = {}
        if map_action in ("merge", "OVERWRITE"):
            if map_body is not None:
                # ADR 0211: the body is being written anyway, so the index it
                # carries is re-projected inside this same PATCH: milestones as
                # MERGED (parsed from the body about to be written, not from the
                # raw input and not from the snapshot, which predates the merge),
                # and every ticket the run leaves closed -- an OVERWRITE'd ticket
                # is reopened below, so it is dropped here. A relabel-only merge
                # has no body and is left alone: nothing writes the body, so
                # nothing re-projects it.
                reopened = {k for k, a in actions.items()
                            if a == "OVERWRITE" and k in snap_tickets}
                map_body = _project_decisions(
                    map_body, _decisions_entries(snap, reopened=reopened),
                    milestone_index(map_body)[0])
                _assert_map_body(map_body, f"the map issue body (#{map_number})")
                payload["body"] = map_body
```

Nothing else in `chart()` changes: the ticket passes, the edge pass, the closing snapshot, the strip pass and the pointer are untouched, and the map is still written exactly once.

- [ ] **Step 5: Run the class, then both whole suites**

```bash
cd plugins/decision-map/scripts && python3 -m unittest test_github_map_ops.GitHubGroupedIndexTest -v 2>&1 | tail -12
python3 test_github_map_ops.py 2>&1 | tail -3 && python3 test_local_map_ops.py 2>&1 | tail -3
```

Expected: the class passes (6 tests); GitHub `Ran 138 tests … OK`; local `Ran 226 tests … OK`. `test_skip_exists_writes_nothing_on_the_real_run_either` (line 178) and `test_an_identical_rechart_reports_no_divergence_at_all` (line 248) still pass — the skip decision in `_plan_map` compares the region-merged body without the projection, so a projected body that is already stored compares equal on the next run.

- [ ] **Step 6: Commit**

```bash
cd "$(git rev-parse --show-toplevel)"
git add plugins/decision-map/scripts/github_map_ops.py plugins/decision-map/scripts/test_github_map_ops.py
git commit -m "feat(decision-map): GitHub chart carries the re-projected decisions index in its own map write (ADR 0211)" \
           -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: The contract describes the new index, the new `--force` behaviour and the empty milestone

**Files:**
- Modify: `plugins/decision-map/references/data-contracts.md:70-72` (call budget note), `:240-247` (additive guarantees), `:288-297` (`--force` index paragraph), `:493-494` (end of the exclusivity paragraph — insertion point), `:1319-1321` (map.md skeleton), `:1462-1468` (generated-regions grouping rule)
- Modify: `docs/superpowers/plans/2026-07-31-decision-map.md:12-19` (banner — one more paragraph)

**Interfaces:**
- Consumes: the grammar in Global Constraints (Task 1's output) and the write rule (Tasks 2–3).
- Produces: the wording Tasks 5–6 point at instead of restating.

- [ ] **Step 1: Call budget — say the count is unchanged**

Find the paragraph ending `snapshot it already holds supplies each ticket's status and gist, so the\nprojection adds no reads.` (about line 70–72) and append one sentence, so it reads:

```
A slug passed to `--map` costs one extra listing call to resolve; an issue number
costs none. `resolve` re-projects the decisions index over every ticket, but the
snapshot it already holds supplies each ticket's status and gist, so the
projection adds no reads. `chart --real` re-projects the same index inside the
map create-or-patch it already makes (ADR 0211), so the table above does not
change.
```

- [ ] **Step 2: Additive guarantees — name the decisions region**

Replace the paragraph starting `**What additive does not guarantee:**` (lines 240–247) with:

```
**What additive does not guarantee:** that an existing ticket file is
byte-identical afterwards (it may gain one `blockedBy` entry and a
re-rendered `graph` region — its own, if it is the blocked ticket, or the
blocker's, since an edge is written at both ends); that the map document's
**decisions region** is byte-identical afterwards (whenever the map body is
written at all — `create`, `merge` with a body, or `OVERWRITE` — the
"Decisions so far" index is re-projected in that same write, ADR 0211; a map
labelled `skip (exists)` is never touched, so a stale index never turns an
identical re-chart into a write); and that a value in the input takes effect
(a divergent scalar is reported, not applied).
It does guarantee that nothing recorded is ever removed, reordered or
overwritten, and that re-running identical input is a **no-op** — the same
bytes out, which also makes a partially-failed chart resumable.
```

- [ ] **Step 3: `--force` — the index is re-projected, not emptied**

Replace the paragraph starting `One consequence worth knowing: the "Decisions so far" index is a projection` (lines 288–297) with:

```
One consequence worth knowing: the "Decisions so far" index is a projection,
and `--force` rewrites the map body **with the index fully re-projected in
that same write** (ADR 0211) — narrowed to the surviving decisions. Every
rewritten ticket is reset to `open`, so it drops out; a ticket that is still
closed (because the input named it only in a `blocks` list, or did not name it
at all) keeps its closed state and **stays listed**, under its milestone's
heading with the count that survives. (Before ADR 0211 the index came out
empty and self-healed on the next `resolve`; that is no longer the behaviour.)
A backend must still not implement a partial refresh here — the index is
either fully re-projected or left for the next `resolve` to rebuild, and on
every write of the map body it is the former.
```

- [ ] **Step 4: Milestones — the empty milestone**

After the paragraph that ends `is a lint **error** (`milestone-duplicate-member`), never resolved by picking\none.` (lines 493–494), insert a new paragraph:

```
**An empty milestone is a placeholder, and it holds the map open** (ADR 0210,
ADR 0212). `chart-map` writes one — `"members": []` — for an increment the
user named whose decisions are all still fog, so the map lists the whole plan
in order from day one. It is legal; `frontier` reports it `{closed: 0,
total: 0, complete: false}`; the decisions index renders it as `0/0 closed —
no tickets yet`; and `work-map` treats it as fog: when nothing is open and no
fog remains but a milestone has `total: 0`, the session asks whether that
increment still needs a decision (yes → one ticket is charted into it; no →
the line is removed by hand, ADR 0098). No lint rule names it — `frontier`
already carries the fact, and a warning that fired on every freshly charted
map would be noise.
```

- [ ] **Step 5: The map.md skeleton shows the milestoned shape of the index**

In the skeleton (lines 1319–1321), replace

```
<!-- decision-map:decisions:start -->
- [<ticket title>](tickets/<slug>.md) — <one-line gist>
<!-- decision-map:decisions:end -->
```

with

```
<!-- decision-map:decisions:start -->
#### <milestone slug> — <label> (<closed>/<total> closed)

- [<ticket title>](tickets/<slug>.md) — <one-line gist>
<!-- decision-map:decisions:end -->
```

(`grep -c "decision-map:decisions:start -->" plugins/decision-map/references/data-contracts.md` must print `1` before you edit — the skeleton is the only place the marker appears in this file.)

- [ ] **Step 6: The grouping rule under "Generated regions in local files"**

Replace the sentences from `**When the map carries milestones, the index is grouped to match**` through `flat list this always produced, unchanged.` (lines 1462–1468) with (the word `files.` that precedes the span stays where it is):

```
**When the map carries milestones, the index is the map's status
  board** (ADR 0103, ADR 0211; `decisions_region` in `map_core.py`): one
  `#### <slug>[ — <label>] (<closed>/<total> closed)` heading per **declared**
  milestone, in map order — not key order, because the milestone list's order
  is chosen — its closed entries key-ascending beneath, a `_nothing closed
  yet_` line when it has members but none closed, and `(0/0 closed — no
  tickets yet)` in the heading (no body) for an empty milestone; then an
  `#### (unassigned)` tail for any closed ticket not in a milestone. The
  counts are `milestone_progress`'s — distinct members, closed ones included —
  so the file and `frontier.json` agree. It is re-projected by `resolve` and by
  any `chart` that writes the map body. On a map with no milestones the index
  is the flat list this always produced, unchanged.
```

- [ ] **Step 7: One paragraph on the original plan's banner**

In `docs/superpowers/plans/2026-07-31-decision-map.md`, after the banner line `> user content in three different ways. Never copy that snippet.` (line 19), add:

```
>
> **2026-09-13 (ADRs 0210–0212):** the map-done rule at the end of Task 7 is
> narrower now — an **empty milestone** (declared, no tickets yet) also holds
> the map open, and work-map asks about it before handing off. See
> `docs/superpowers/specs/2026-09-13-decision-map-remaining-milestones-design.md`.
```

- [ ] **Step 8: Verify by reading, then commit**

```bash
cd "$(git rev-parse --show-toplevel)"
grep -c "ADR 0211" plugins/decision-map/references/data-contracts.md   # expected: 5 (steps 1, 2, 3 twice, 6)
grep -n "rather than rendered empty" plugins/decision-map/references/data-contracts.md   # expected: no output
grep -n "comes out empty" plugins/decision-map/references/data-contracts.md   # expected: only the "Before ADR 0211 the index came out empty" parenthetical
git add plugins/decision-map/references/data-contracts.md docs/superpowers/plans/2026-07-31-decision-map.md
git commit -m "docs(decision-map): contract — the index as status board, --force re-projects, the empty milestone (ADRs 0210-0212)" \
           -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: chart-map asks "and after that?" and records empty milestones (ADR 0210)

**Files:**
- Modify: `plugins/decision-map/skills/chart-map/SKILL.md:171-186` (section "Ask what ships first"), `:215-218` (Step 3 template `milestones`), `:232-236` (the `milestones` bullet)
- Regenerate: `skills/chart-map/SKILL.md` (generated; never hand-edit)

**Interfaces:**
- Consumes: the contract wording from Task 4 (the skill points at it, it does not restate the grammar).
- Produces: the `map_input.json` shape work-map's Step 5 reuses (unchanged shape — `milestones[].members` may be `[]`).

- [ ] **Step 1: Replace the closing-question section**

Replace the block from the heading `### Ask what ships first (ADR 0100)` (line 171) through the paragraph ending `to fill now.` (line 186) with:

```markdown
### Ask what ships first, then what ships next (ADR 0100, ADR 0210)

Once every ticket on this pass is named, ask one more question — in the
user's own terms, not the tool's: **"what do you want to be able to demo
first?"**, not "how do you want to group these tickets?". It is skippable —
say plainly that skipping it costs nothing, because the grouping can be
declared later from `work-map` once the map exists to group. Keep it short:
at most two options, and lead with your own recommendation before asking —
the framing every HITL question in these two skills should use, and the one
the HITL guard above already requires (a recommendation is offered, never
accepted on the human's behalf).

Then keep going — **"and after that?"** — one question at a time, in the same
shape, until the user says that is all or skips (ADR 0210). Each answer is one
more entry, in order, of the `milestones` list Step 3 writes: a slug, an
optional label in the user's own words, and the tickets named on this pass
that belong to it. A ticket goes in the **first** increment that needs it and
is never re-listed in a later one (ADR 0097).

**An increment with no named ticket is still recorded**, as a milestone with
`"members": []`. That is a placeholder — fog at increment level — and it is
what lets the map say, from day one, which increments exist and which remain.
Tell the user two things about it: it shows on the map as `0/0 closed — no
tickets yet`, and `work-map` will ask about it before the map can be called
done — either its first decision gets named then, or the user removes the
line by hand (ADR 0212). Do not invent a ticket now just to fill it.

Stopping early loses nothing: a declined question leaves the list as it
stands, and `work-map` can still grow it later (ADR 0098).
```

- [ ] **Step 2: The Step 3 template shows three milestones, one empty**

Replace (lines 215–218)

```json
    "milestones": [
      { "slug": "mvp", "label": "demo the search page",
        "members": ["provider-choice"] }
    ]
```

with

```json
    "milestones": [
      { "slug": "mvp", "label": "demo the search page",
        "members": ["provider-choice"] },
      { "slug": "tenant-ramp", "label": "per-tenant rollout",
        "members": ["cutover-order"] },
      { "slug": "billing-sunset", "label": "retire the old provider",
        "members": [] }
    ]
```

- [ ] **Step 3: The `milestones` bullet names the empty case**

The bullet currently ends `A ticket belongs to **at most one** milestone, and a\n  ticket in none is legal: it means "not yet scheduled", not an error.` (line 235–236). Append to it:

```
  A milestone with **no** members is legal too — the placeholder the loop
  above writes for an increment whose decisions are still fog (ADR 0210); the
  map lists it at `0/0`, and `work-map` keeps the map open until it gains a
  ticket or is removed by hand (ADR 0212).
```

- [ ] **Step 4: Regenerate the skills tree and check it**

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/generate_skills_tree.py
python3 scripts/check_skills_tree.py --repo . ; echo "exit $?"
git status --short
```

Expected: exit 0; changes only in `plugins/decision-map/skills/chart-map/SKILL.md` and `skills/chart-map/SKILL.md`.

- [ ] **Step 5: Read the section back against the sequence diagram in spec §4, then commit**

The section must: ask first, then loop on "and after that?", stop on "that is all" or a skip, write `members: []` for an increment with no ticket, and say what work-map will do with it. If any of the four is missing, fix before committing.

```bash
git add plugins/decision-map/skills/chart-map/SKILL.md skills/chart-map/SKILL.md
git commit -m "docs(decision-map): chart-map asks for the later milestones too, empty ones allowed (ADR 0210)" \
           -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: work-map treats an empty milestone as fog before declaring the map done (ADR 0212)

**Files:**
- Modify: `plugins/decision-map/skills/work-map/SKILL.md:41` (top diagram), `:208-211` (Step 1 surface), `:250-253` (Step 2 rule), `:508-509` (Step 5 checklist), `:750-770` (Step 6 "When the frontier came back empty")
- Regenerate: `skills/work-map/SKILL.md`

**Interfaces:**
- Consumes: `frontier.json`'s `milestones[]` rows (`total: 0` marks an empty milestone — unchanged shape); Step 5's `map_input.json` with `milestones[].members` (Task 5).
- Produces: nothing downstream; this is the end-of-map gate.

- [ ] **Step 1: The top diagram's step ② line**

Replace the single line

```
  │   nothing open, no fog? ■ the map is done
```

with the two lines (keep the leading two spaces and the `│` column exactly as the surrounding lines)

```
  │   nothing open, no fog, no empty
  │   milestone? ■ the map is done
```

- [ ] **Step 2: Step 1 — how an empty milestone reads on the surface**

In the "frontier, grouped by milestone" bullet, the text `for it to count against. `read` is what carries milestone *membership*` (about line 211) becomes:

```
  for it to count against. An **empty** milestone — `total: 0` in
  `milestones[]` — is one line, `<slug> — 0/0, no tickets named yet`, with
  nothing under it (ADR 0212). `read` is what carries milestone *membership*
```

- [ ] **Step 3: Step 2 — never recommend into an empty milestone**

Replace (lines 250–253)

```
incomplete milestone that has something takeable** — walk `frontier.json`'s
`milestones` list in order, skipping any milestone that is `complete` or
whose frontier tickets are none, and take the first one that has at least
one — then, inside it, apply the existing heuristic and recommend whichever
```

with

```
incomplete milestone that has something takeable** — walk `frontier.json`'s
`milestones` list in order, skipping any milestone that is `complete` or
whose frontier tickets are none (an empty milestone, `total: 0`, has none, so
it is skipped like any other — ADR 0212), and take the first one that has at
least one — then, inside it, apply the existing heuristic and recommend whichever
```

- [ ] **Step 4: Step 5 — a ticket that answers an empty milestone joins it**

The checklist bullet (lines 508–509)

```
- Did it sharpen the **milestone** plan — a group that should now exist, or a
  ticket that clearly belongs in one that already does?
```

becomes

```
- Did it sharpen the **milestone** plan — a group that should now exist, or a
  ticket that clearly belongs in one that already does? A ticket that answers
  an **empty** milestone's question is listed in that milestone's `members` in
  the same input (ADR 0212).
```

- [ ] **Step 5: Step 6 — the fourth empty-frontier case**

Under `### When the frontier came back empty` (line 750): change `Three different situations, and they need different answers:` to `Four different situations, and they need different answers:`; change the first bullet's lead `- **Nothing open and no fog left** — the map is done.` to `- **Nothing open, no fog left, and no empty milestone** — the map is done.`; and insert this bullet between the fog bullet (which ends `waiting on a decision that has not been made yet.`) and `- **Everything left is blocked or claimed**`:

```
- **Nothing open, no fog, but a milestone has no tickets** — `frontier.json`
  lists it with `total: 0`. That is fog at increment level, and it holds the
  map open exactly as fog does (ADR 0212). Take the first such milestone in
  map order and ask **one** HITL question: does this increment still need a
  decision? **Yes** — this session's work is graduation, the same as the fog
  case above: state that first decision as a question and run Step 5's gate
  with the new ticket listed in that milestone's `members`; then stop. **No**
  — the user removes the milestone line by hand (removal is a hand edit,
  ADR 0098), optionally adding a `notes` line saying why, and runs `lint`; if
  another empty milestone remains, ask about that one next, because no
  ticket was resolved. The map is done only when no milestone is empty.
```

- [ ] **Step 6: Regenerate the skills tree and check it**

```bash
cd "$(git rev-parse --show-toplevel)"
python3 scripts/generate_skills_tree.py
python3 scripts/check_skills_tree.py --repo . ; echo "exit $?"
git status --short
```

Expected: exit 0; changes only in `plugins/decision-map/skills/work-map/SKILL.md` and `skills/work-map/SKILL.md`. The two new diagram lines are 36 and 34 columns wide, inside the ≤ 50 the diagram convention sets for terminal diagrams.

- [ ] **Step 7: Read the flow back against spec §6.2, then commit**

Check the four branches read in this order: blocked/claimed → fog → empty milestone → done, and that "done" now requires no empty milestone in all three places (diagram, first bullet, new bullet).

```bash
git add plugins/decision-map/skills/work-map/SKILL.md skills/work-map/SKILL.md
git commit -m "docs(decision-map): work-map holds the map open over an empty milestone (ADR 0212)" \
           -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 7: README lifecycle and vocabulary, version bump, final verification

**Files:**
- Modify: `plugins/decision-map/README.md:43` (vocabulary row), `:93` (lifecycle diagram edge)
- Modify: `plugins/decision-map/.claude-plugin/plugin.json:4` (`"version": "0.12.0"`), `.claude-plugin/marketplace.json:154` (the `decision-map` entry's `"version": "0.12.0"`)

**Interfaces:**
- Consumes: everything above.
- Produces: `decision-map 0.13.0`.

- [ ] **Step 1: Vocabulary row**

After the table row `| Milestone | shippable increment, release slice |` (line 43) add:

```
| Empty milestone | a placeholder increment — a "TBD phase" that is still on the plan |
```

- [ ] **Step 2: Lifecycle diagram — the empty-milestone question and the narrower done edge**

Replace the single line (line 93)

```
    L -->|"empty and no fog left"| O["map done — hand off to<br/>sp-writing-plans → build"]
```

with

```
    L -->|"frontier empty, no fog,<br/>a milestone has no tickets"| P{"still needs a decision?<br/>(asked once, HITL)"}
    P -->|"yes"| R["name its first decision →<br/>a ticket in that milestone"]
    R --> E
    P -->|"no"| Q["the user removes the line<br/>by hand; lint"]
    Q --> L
    L -->|"empty, no fog, no empty milestone"| O["map done — hand off to<br/>sp-writing-plans → build"]
```

(`E` and `L` are existing nodes in that diagram: `E` is "work-map: one session, one ticket", `L` is the `map state` decision.)

- [ ] **Step 3: Bump both manifests**

```bash
cd "$(git rev-parse --show-toplevel)"
python3 - <<'EOF'
from pathlib import Path
p = Path("plugins/decision-map/.claude-plugin/plugin.json")
t = p.read_text(encoding="utf-8")
assert t.count('"version": "0.12.0"') == 1
p.write_text(t.replace('"version": "0.12.0"', '"version": "0.13.0"', 1), encoding="utf-8")

m = Path(".claude-plugin/marketplace.json")
t = m.read_text(encoding="utf-8")
i = t.index('"name": "decision-map"')
j = t.index('"version": "0.12.0"', i)
# the next "version" after the decision-map name must belong to that entry:
assert t.find('"name":', i + 1) > j, "another plugin entry sits between name and version"
m.write_text(t[:j] + '"version": "0.13.0"' + t[j + len('"version": "0.12.0"'):], encoding="utf-8")
print("bumped")
EOF
grep -n '"version"' plugins/decision-map/.claude-plugin/plugin.json
grep -n -B3 '"version": "0.13.0"' .claude-plugin/marketplace.json | grep -n "decision-map\|version"
```

Expected: plugin.json shows `0.13.0`; the marketplace grep shows `0.13.0` inside the `decision-map` block (its `"source": "./plugins/decision-map"` line appears within the three lines before it or the description line does).

- [ ] **Step 4: Full verification**

```bash
cd "$(git rev-parse --show-toplevel)"
python3 -c "import json;a=json.load(open('plugins/decision-map/.claude-plugin/plugin.json'))['version'];b=[p for p in json.load(open('.claude-plugin/marketplace.json'))['plugins'] if p['name']=='decision-map'][0]['version'];assert a==b=='0.13.0',(a,b);print('versions ok',a)"
(cd plugins/decision-map/scripts && python3 test_local_map_ops.py 2>&1 | tail -3 && python3 test_github_map_ops.py 2>&1 | tail -3)
python3 scripts/check_skills_tree.py --repo . ; echo "exit $?"
python3 plugins/dev-workflows/scripts/check_vendored_superpowers.py --strict ; echo "exit $?"
```

Expected: `versions ok 0.13.0`; `Ran 226 tests … OK`; `Ran 138 tests … OK`; skills tree exit 0; vendored check exit 0 (this plan touches nothing under `skills/sp-*` or `skills/scrutinize/`, so it must still be clean).

Then walk the spec's §9 acceptance list against a scratch map:

```bash
cd "$(git rev-parse --show-toplevel)"
S=$(mktemp -d)
cat > "$S/in.json" <<'EOF'
{"target":{"slug":"demo"},
 "map":{"title":"Decision map - demo","destination":"prove the index","notes":["none"],
        "notYetSpecified":[],"outOfScope":[],
        "milestones":[{"slug":"mvp","label":"demo it","members":["a","b"]},
                      {"slug":"ramp","label":"roll out","members":["c"]},
                      {"slug":"sunset","label":"retire","members":[]}]},
 "tickets":[{"key":"a","title":"A?","type":"grilling","question":"a?","blocks":[]},
            {"key":"b","title":"B?","type":"grilling","question":"b?","blocks":[]},
            {"key":"c","title":"C?","type":"task","question":"c?","blocks":[]}]}
EOF
python3 plugins/decision-map/scripts/local_map_ops.py chart --root "$S/maps" --input "$S/in.json" --output "$S/map.json" --real >/dev/null
sed -n '/decisions:start/,/decisions:end/p' "$S/maps/demo/map.md"
python3 plugins/decision-map/scripts/local_map_ops.py resolve --root "$S/maps" --map demo --ticket a --gist "yes" >/dev/null
sed -n '/decisions:start/,/decisions:end/p' "$S/maps/demo/map.md"
python3 plugins/decision-map/scripts/local_map_ops.py frontier --root "$S/maps" --map demo --output "$S/f.json" >/dev/null && python3 -c "import json;print(json.load(open('$S/f.json'))['milestones'])"
before=$(shasum "$S/maps/demo/map.md"); python3 plugins/decision-map/scripts/local_map_ops.py chart --root "$S/maps" --input "$S/in.json" --output "$S/map2.json" --real >/dev/null; [ "$before" = "$(shasum "$S/maps/demo/map.md")" ] && echo "re-chart: byte-identical"
```

Expected, in order: headings `mvp — demo it (0/2 closed)` + `_nothing closed yet_`, `ramp — roll out (0/1 closed)` + `_nothing closed yet_`, `sunset — retire (0/0 closed — no tickets yet)`; after the resolve `mvp — demo it (1/2 closed)` with the `[A?](tickets/a.md) — yes` entry; `frontier.json` reports `closed: 1, total: 2` for `mvp` and `total: 0` for `sunset`; `re-chart: byte-identical`. (If the CLI flag spelling differs from the above, `python3 plugins/decision-map/scripts/local_map_ops.py --help` is the authority — the contract's subcommand table is what this exercises.)

- [ ] **Step 5: Commit**

```bash
git add plugins/decision-map/README.md plugins/decision-map/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "feat(decision-map): the map says which milestones remain (0.12.0 -> 0.13.0)" \
           -m "Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

- [ ] **Step 6: Re-verify the ADR numbers before merging (Global Constraints, last bullet)**

Run the global-max scan; expected `next: workflow-daily-work-0213`. If it prints anything lower, another branch minted 0210–0212 in parallel: renumber this branch's three ADR files to the next free numbers and update every citation (`grep -rn "021[012]" CONTEXT.md docs/ plugins/decision-map/`), then amend or add a `docs(decision-map): renumber ADRs …` commit.

---

## What this plan deliberately leaves alone

- `.agents/skills/` (skills CLI install snapshot + `skills-lock.json`) — refreshed by the CLI after merge, not by hand (Global Constraints).
- Maps that predate the milestones region — not repaired (ADR 0098); the only such local map in this repo is finished.
- `smoke_github_live.py` — not run (destructive; needs a throwaway repo). Its `INPUT` has no milestones, so its byte-identical round-trip is unaffected; the fake covers the projection.
- `map.json` / `frontier.json`, the lint rules, the subcommand table, the dry-run plan vocabulary — unchanged by design (ADRs 0211, 0212).
