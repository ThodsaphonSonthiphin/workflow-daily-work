# Route superpowers reviews to scrutinize-dispatch — Plan A, the routing core

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every dispatched superpowers reviewer run this repo's `scrutinize-dispatch` instead of the built-in reviewer, and prove it with a live probe.

**Architecture:** Six upstream skill directories are copied verbatim into `plugins/dev-workflows/skills/` under an `sp-` prefix (21 files), then edited by one enumerated rewrite pass over five classes of reference. The three live reviewer prompts point at a new `scrutinize-dispatch` skill — a copy of the frozen `scrutinize` retuned for a dispatched caller. A host `SessionStart` hook re-points the one skill the upstream hook names. `scrutinize` itself is never edited and never on the dispatch path.

**Tech Stack:** Markdown skills with YAML frontmatter, Claude Code plugin manifests, a `SessionStart` hook in `hooks.json`, Git Bash for the copy and assertion steps, Python 3 for assertion scripts.

**Spec:** `docs/decision-map/superpowers-review-to-scrutinize/map.md` plus ADRs [0069–0084](../../adr/) in `docs/adr/`. The load-bearing ones are 0070 (hook), 0071 (naming/descriptions), 0073 (host plugin), 0074 (the 21 files and the five rewrite classes), 0079 (the acceptance probe), 0084 (scrutinize-dispatch).

## Global Constraints

- **Upstream sha is `b36e0829c6d0`** — one sha for the whole copy set, never per-file (ADR 0075).
- **Vendoring source on this machine:** `C:/Users/thodsaphon.sonthipin/.claude/plugins/cache/claude-plugins-official/superpowers/b36e0829c6d0`. This path is machine-local. The portable equivalent is `git clone https://github.com/obra/superpowers && git checkout b36e0829c6d0`. Verify either source has exactly 21 files across the six directories before copying.
- **`scrutinize` is FROZEN.** `plugins/dev-workflows/skills/scrutinize/SKILL.md` must be byte-identical at the end of this plan. Any task that modifies it is a failed task.
- **The copy set is exactly six:** `sp-brainstorming`, `sp-writing-plans`, `sp-executing-plans`, `sp-subagent-driven-development`, `sp-requesting-code-review`, `sp-receiving-code-review` (ADR 0071).
- **Two provably dead files ship anyway** — `sp-brainstorming/spec-document-reviewer-prompt.md` and `sp-writing-plans/plan-document-reviewer-prompt.md`. They are the detector for upstream reviving them. Do not "clean them up" (ADR 0074).
- **The Mermaid diagram convention does NOT bind the six vendored copies or the documents they generate** (ADR 0077). It DOES bind `scrutinize-dispatch`, which is this repo's own skill.
- **Three wiring conventions DO bind the copies** (ADR 0077): skill-relative paths for a skill's own files, frontmatter `name` + trigger-rich `description`, harness-neutral wording.
- **Versions move together.** `plugins/dev-workflows/.claude-plugin/plugin.json` and the `dev-workflows` entry in `.claude-plugin/marketplace.json` must report the same version. Mint from the global max, never `current + 1`.
- **Every new skill adds one PLAYBOOK.md row**, in the same commit that adds the skill.
- Shell steps assume **Git Bash**. Run from the repo root.

---

### Task 1: The `scrutinize-dispatch` skill

Build this first: all four reviewer dispatches route to it, and it is the only artifact in this plan with no upstream source to copy from. It is testable in isolation, before any vendoring exists.

**Files:**
- Create: `plugins/dev-workflows/skills/scrutinize-dispatch/SKILL.md`
- Create: `scripts/assert_scrutinize_dispatch.py` (temporary test harness; deleted in Task 7)
- Read only, never modify: `plugins/dev-workflows/skills/scrutinize/SKILL.md`

**Interfaces:**
- Consumes: nothing.
- Produces: a skill loadable as `dev-workflows:scrutinize-dispatch`. Tasks 4 and 7 reference that exact string. Its report emits the literal headings `#### Critical (Must Fix)`, `#### Important (Should Fix)`, `#### Minor (Nice to Have)` and the literal token `⚠️ Cannot verify from diff:` — Task 4's prompt edits and Task 7's probe both depend on these exact strings.

- [ ] **Step 1: Write the failing assertion script**

```python
# scripts/assert_scrutinize_dispatch.py
"""Assert scrutinize-dispatch carries its four deltas from scrutinize (ADR 0084)."""
import io, sys, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SKILL = pathlib.Path("plugins/dev-workflows/skills/scrutinize-dispatch/SKILL.md")
FROZEN = pathlib.Path("plugins/dev-workflows/skills/scrutinize/SKILL.md")

if not SKILL.is_file():
    sys.exit("FAIL: %s does not exist" % SKILL)

text = SKILL.read_text(encoding="utf-8")
failures = []

# frontmatter
for needle in ("name: scrutinize-dispatch", "effort: max"):
    if needle not in text:
        failures.append("frontmatter missing %r" % needle)

# delta 2 - native severity vocabulary
for needle in ("#### Critical (Must Fix)",
               "#### Important (Should Fix)",
               "#### Minor (Nice to Have)"):
    if needle not in text:
        failures.append("severity heading missing %r" % needle)

# delta 3 - the cannot-verify channel
if "⚠️ Cannot verify from diff:" not in text:
    failures.append("missing the cannot-verify channel token")

# delta 1 - blast-radius scope, and NOT scrutinize's end-to-end stance
if "blast radius" not in text:
    failures.append("missing the blast-radius scope rule")
if "The diff is the entry point, not the scope" in text:
    failures.append("carries scrutinize's end-to-end scope stance - delta 1 not applied")

# delta 4 - upstream verdicts
for needle in ("Ready to merge", "Task quality"):
    if needle not in text:
        failures.append("verdict vocabulary missing %r" % needle)

# carried over from scrutinize
for needle in ("simpler", "Cite or it didn't happen", "No flattery"):
    if needle not in text:
        failures.append("dropped a carried-over rule: %r" % needle)

# the freeze
if not FROZEN.is_file():
    failures.append("frozen scrutinize is missing")
elif "scrutinize-dispatch" in FROZEN.read_text(encoding="utf-8"):
    failures.append("FROZEN scrutinize was modified - it must not mention the copy")

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)
print("PASS: scrutinize-dispatch carries all four deltas; scrutinize untouched")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python scripts/assert_scrutinize_dispatch.py`
Expected: FAIL with `FAIL: plugins/dev-workflows/skills/scrutinize-dispatch/SKILL.md does not exist`

- [ ] **Step 3: Record the frozen skill's hash, so a later step can prove it never moved**

```bash
git hash-object plugins/dev-workflows/skills/scrutinize/SKILL.md > /tmp/scrutinize.sha
cat /tmp/scrutinize.sha
```

- [ ] **Step 4: Write the skill**

Create `plugins/dev-workflows/skills/scrutinize-dispatch/SKILL.md` with exactly this content:

````markdown
---
name: scrutinize-dispatch
description: The review engine for a DISPATCHED reviewer subagent - the scoped counterpart to scrutinize. Use only when a reviewer prompt (code-reviewer.md, task-reviewer-prompt.md, re-review-prompt.md) dispatched you to review a task diff and a controller will parse your report. Emits Critical/Important/Minor and a spec-compliance verdict. For a human-facing review in a live session, use scrutinize instead.
effort: max
---

# Scrutinize (dispatch)

Stand outside the change and ask whether it should exist at all, then verify it
actually does what it claims — within the blast radius of the task you were given.

This is `scrutinize` retuned for one caller: a reviewer subagent that was dispatched,
cannot ask the author questions, and whose report a controller parses for exact words.
It differs from `scrutinize` in four places and nowhere else — scope, severity
vocabulary, the cannot-verify channel, and the verdicts (ADR 0084).

## Operating stance

- **Outsider.** Forget who wrote it and why they think it's right. Read the diff cold.
- **Scoped to the blast radius, not the whole call graph.** The diff and its context
  lines are your view of the change. Do not crawl the broader codebase. Inspect code
  outside the diff only to evaluate a concrete risk you can *name* — one focused check
  per named risk, and name both the risk and what you checked in your report.
  Cross-cutting changes are legitimate named risks: if the diff changes lock ordering, a
  function or API contract, or shared mutable state, checking the call sites is the
  right method.
- **Actionable, concise, with rationale.** Every finding states *what to change*, *why*,
  and *what evidence* led you there. No filler, no restating the diff back.

## Workflow

### 1. Intent — what is this actually trying to do?

- State the goal in one sentence, in your own words. If you cannot, say so — that is
  itself a finding about the brief.
- Ask: **is there a simpler, smaller, or more elegant way to achieve the same goal?**
  Consider using something that already exists instead of adding new surface, and a
  smaller change that solves 90% of the goal with 10% of the risk.
- If a better alternative exists, name it. Report it as `Important` when the change
  works but a materially simpler one was available; as `Minor` when it is taste.
  A stated rationale never downgrades a finding's severity.

### 2. Trace — walk the path the diff actually creates

- For each behavior the change claims, trace it through the diff and its context lines:
  entry point → call sites → branches taken → state mutated → exit or side effect.
- Read the seams. The context lines around a hunk are unchanged code, and they are in
  scope — bugs hide where new code meets old.
- Note every place the trace surprises you. Surprises are signal.

### 3. Verify — does it do what it claims?

- **Spec compliance first.** Check the diff against the brief's requirements, one by
  one. Every listed file must have its corresponding hunk; a listed file the diff never
  touches is a Missing finding no matter how clean the rest looks.
- **If a requirement cannot be verified from this diff alone** — it lives in unchanged
  code, or spans tasks — report it as a `⚠️` item. Do not broaden your search to settle
  it. The controller holds the cross-task context you lack and will resolve it.
- **What inputs or states would break it?** Edge cases, error paths, partial failures,
  retries, empty/null/unicode/huge inputs, ordering assumptions.
- **What does it silently change?** Performance, error semantics, observability, the
  contract for other callers, on-disk or on-wire format.
- **How is it tested?** Do the tests exercise the traced path, or pass while skipping it
  — mocks that hide the bug, asserts on intermediate state, happy path only?
- **Does every site that must honor a stated invariant honor it?** When the change
  declares a rule about itself, check every site *within the diff* that the rule covers,
  not just the ones the author aimed at. A site outside the diff is a `⚠️` item.

## Output format

Emit exactly these sections, in this order.

```
## Spec Compliance

✅ Spec compliant | ❌ Issues found: [what's missing, extra, or misunderstood]
⚠️ Cannot verify from diff: [requirements you could not verify from the diff alone,
one per line, each naming the requirement and why the diff cannot settle it]

## Issues

#### Critical (Must Fix)
#### Important (Should Fix)
#### Minor (Nice to Have)

## Recommendations

## Assessment

Ready to merge: Yes | With fixes | No
Task quality: Approved | Needs fixes
```

Under each severity heading, one entry per finding:

- **Finding** — one sentence, specific. Cite `file:line`.
- **Why it matters** — the consequence, not the principle.
- **Evidence** — the trace step or input that exposes it.
- **Suggested change** — concrete, minimal.

Omit a severity heading only when it has no findings. If every heading is empty, say
what you traced and what you checked, so the controller can judge the coverage.

## Severity calibration

Not everything is Critical.

- **Critical** — the change is wrong or unsafe: incorrect behavior, data loss, a
  security hole, a broken contract for an existing caller.
- **Important** — the task cannot be trusted until it is fixed: an unmet requirement,
  a missing test for the behavior just added, an error path that swallows failure, a
  materially simpler approach that was available.
- **Minor** — style, naming, and polish. Ledger-only; these never block.

Both `Critical` and `Important` trigger the controller's fix loop. `Minor` never does.
Mis-labelling a nitpick as Critical burns a fix round; mis-labelling a real defect as
Minor ships it.

## Operating rules

- **No rubber-stamps.** "LGTM" is not an output.
- **Cite or it didn't happen.** Every claim about the code references a specific path,
  file, or line. No vague "this might break under load."
- **Distinguish claim from verification.** "The brief says X" and "I traced X and
  confirmed it" are different — keep them separate.
- **One simpler-alternative pass is mandatory**, even on a small diff.
- **Do not dispatch subagents.** You are the reviewer; there is no one below you.
- **Do not trust the implementer's report.** Read the diff. A report claiming a test
  passes is not evidence the test exists.
- **Read-only.** Never edit the checkout, never run git commands that write.
- **No flattery, no hedging.** State the finding. There is no Strengths section.
````

- [ ] **Step 5: Run the assertion to verify it passes**

Run: `python scripts/assert_scrutinize_dispatch.py`
Expected: `PASS: scrutinize-dispatch carries all four deltas; scrutinize untouched`

- [ ] **Step 6: Verify the frozen skill did not move**

```bash
test "$(git hash-object plugins/dev-workflows/skills/scrutinize/SKILL.md)" = "$(cat /tmp/scrutinize.sha)" \
  && echo "FROZEN OK" || echo "FAIL: scrutinize was modified"
```
Expected: `FROZEN OK`

- [ ] **Step 7: Validate the plugin manifest still parses**

Run: `claude plugin validate plugins/dev-workflows`
Expected: exit 0. A colon-space inside an unquoted `description:` silently drops the whole frontmatter and the skill vanishes from the skill list — this command is what catches it.

- [ ] **Step 8: Commit**

```bash
git add plugins/dev-workflows/skills/scrutinize-dispatch/SKILL.md scripts/assert_scrutinize_dispatch.py
git commit -m "feat(dev-workflows): add scrutinize-dispatch, the dispatch-tuned review engine (ADR 0084)"
```

---

### Task 2: Vendor the 21 files verbatim, with the upstream licence

**Files:**
- Create: `plugins/dev-workflows/skills/sp-brainstorming/` (8 files)
- Create: `plugins/dev-workflows/skills/sp-writing-plans/` (2 files)
- Create: `plugins/dev-workflows/skills/sp-executing-plans/` (1 file)
- Create: `plugins/dev-workflows/skills/sp-requesting-code-review/` (2 files)
- Create: `plugins/dev-workflows/skills/sp-receiving-code-review/` (1 file)
- Create: `plugins/dev-workflows/skills/sp-subagent-driven-development/` (7 files)
- Create: `plugins/dev-workflows/LICENSE-superpowers`
- Create: `scripts/assert_vendored_closure.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: the six directories at the exact paths above. Tasks 3 and 4 edit files inside them by these names.

- [ ] **Step 1: Write the closure assertion script**

```python
# scripts/assert_vendored_closure.py
"""Assert the vendored copy set is exactly 21 files in six sp- directories."""
import io, sys, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = pathlib.Path("plugins/dev-workflows/skills")
EXPECTED = {
    "sp-brainstorming": 8,
    "sp-writing-plans": 2,
    "sp-executing-plans": 1,
    "sp-requesting-code-review": 2,
    "sp-receiving-code-review": 1,
    "sp-subagent-driven-development": 7,
}
DEAD = [
    "sp-brainstorming/spec-document-reviewer-prompt.md",
    "sp-writing-plans/plan-document-reviewer-prompt.md",
]

failures, total = [], 0
for name, count in EXPECTED.items():
    d = ROOT / name
    if not d.is_dir():
        failures.append("missing directory %s" % name)
        continue
    n = sum(1 for p in d.rglob("*") if p.is_file())
    total += n
    if n != count:
        failures.append("%s has %d files, expected %d" % (name, n, count))
    if not (d / "SKILL.md").is_file():
        failures.append("%s has no SKILL.md - the Antigravity installer skips it" % name)

if total != 21:
    failures.append("total is %d files, expected 21" % total)

for rel in DEAD:
    if not (ROOT / rel).is_file():
        failures.append("dead-file detector missing: %s (ADR 0074 keeps it on purpose)" % rel)

lic = pathlib.Path("plugins/dev-workflows/LICENSE-superpowers")
if not lic.is_file():
    failures.append("LICENSE-superpowers is missing")
else:
    t = lic.read_text(encoding="utf-8")
    for needle in ("MIT", "Jesse Vincent", "b36e0829c6d0", "MODIFIED"):
        if needle not in t:
            failures.append("LICENSE-superpowers missing %r" % needle)

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)
print("PASS: 21 files across six sp- directories, licence present")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python scripts/assert_vendored_closure.py`
Expected: FAIL, six `missing directory` lines plus the licence line.

- [ ] **Step 3: Verify the source before copying**

```bash
SRC="C:/Users/thodsaphon.sonthipin/.claude/plugins/cache/claude-plugins-official/superpowers/b36e0829c6d0/skills"
find "$SRC/brainstorming" "$SRC/writing-plans" "$SRC/executing-plans" \
     "$SRC/requesting-code-review" "$SRC/receiving-code-review" \
     "$SRC/subagent-driven-development" -type f | wc -l
```
Expected: `21`. If the path does not exist, clone instead: `git clone https://github.com/obra/superpowers /tmp/sp && git -C /tmp/sp checkout b36e0829c6d0` and set `SRC=/tmp/sp/skills`.

- [ ] **Step 4: Copy the six directories verbatim**

```bash
SRC="C:/Users/thodsaphon.sonthipin/.claude/plugins/cache/claude-plugins-official/superpowers/b36e0829c6d0/skills"
DST="plugins/dev-workflows/skills"
for d in brainstorming writing-plans executing-plans requesting-code-review \
         receiving-code-review subagent-driven-development; do
  cp -r "$SRC/$d" "$DST/sp-$d"
done
find "$DST"/sp-* -type f | wc -l
```
Expected: `21`

- [ ] **Step 5: Copy the upstream licence and mark it modified**

```bash
SRC="C:/Users/thodsaphon.sonthipin/.claude/plugins/cache/claude-plugins-official/superpowers/b36e0829c6d0"
cp "$SRC/LICENSE" plugins/dev-workflows/LICENSE-superpowers
```

Then prepend this header to `plugins/dev-workflows/LICENSE-superpowers`, above the copied MIT text:

```text
The six skill directories named sp-* under plugins/dev-workflows/skills/ are
vendored from obra/superpowers (https://github.com/obra/superpowers) at commit
b36e0829c6d0, and are MODIFIED: one rewrite pass over five enumerated classes of
reference retargets their reviewer dispatches to this repo's scrutinize-dispatch
skill. See docs/adr/0074 and docs/adr/0084.

The upstream MIT licence follows, verbatim. It covers the vendored files only.
No per-file provenance header is injected into any copied file (ADR 0075).

---
```

- [ ] **Step 6: Run the closure assertion to verify it passes**

Run: `python scripts/assert_vendored_closure.py`
Expected: `PASS: 21 files across six sp- directories, licence present`

- [ ] **Step 7: Prove the copies are byte-identical to the source**

```bash
SRC="C:/Users/thodsaphon.sonthipin/.claude/plugins/cache/claude-plugins-official/superpowers/b36e0829c6d0/skills"
DST="plugins/dev-workflows/skills"
rc=0
for d in brainstorming writing-plans executing-plans requesting-code-review \
         receiving-code-review subagent-driven-development; do
  diff -r "$SRC/$d" "$DST/sp-$d" || rc=1
done
[ $rc -eq 0 ] && echo "VERBATIM OK" || echo "FAIL: copies differ from source"
```
Expected: `VERBATIM OK`. This must pass *before* Task 3 edits anything — it is the only moment the copies are provably verbatim.

- [ ] **Step 8: Commit**

```bash
git add plugins/dev-workflows/skills/sp-* plugins/dev-workflows/LICENSE-superpowers scripts/assert_vendored_closure.py
git commit -m "feat(dev-workflows): vendor six superpowers review skills verbatim at b36e0829c6d0 (ADR 0074)"
```

---

### Task 3: Rewrite class 5 — frontmatter on the six SKILL.md files

Split from Task 4 because this is what makes the copies *load*; Task 4 is what makes them *route*. A reviewer can accept one and reject the other.

**Files:**
- Modify: `plugins/dev-workflows/skills/sp-brainstorming/SKILL.md` (frontmatter only)
- Modify: `plugins/dev-workflows/skills/sp-writing-plans/SKILL.md` (frontmatter only)
- Modify: `plugins/dev-workflows/skills/sp-executing-plans/SKILL.md` (frontmatter only)
- Modify: `plugins/dev-workflows/skills/sp-requesting-code-review/SKILL.md` (frontmatter only)
- Modify: `plugins/dev-workflows/skills/sp-receiving-code-review/SKILL.md` (frontmatter only)
- Modify: `plugins/dev-workflows/skills/sp-subagent-driven-development/SKILL.md` (frontmatter only)

**Interfaces:**
- Consumes: the six directories from Task 2.
- Produces: six skills loadable as `dev-workflows:sp-<name>`. Task 4's short-form references and Task 5's hook text both name these exact skill names.

- [ ] **Step 1: Write the failing frontmatter assertion**

Append to `scripts/assert_vendored_closure.py`, before the `if failures:` block:

```python
# --- frontmatter (ADR 0071) ---
import re
NAMES = ["sp-brainstorming", "sp-writing-plans", "sp-executing-plans",
         "sp-requesting-code-review", "sp-receiving-code-review",
         "sp-subagent-driven-development"]
for name in NAMES:
    p = ROOT / name / "SKILL.md"
    if not p.is_file():
        continue
    head = p.read_text(encoding="utf-8").split("---")
    if len(head) < 3:
        failures.append("%s: no YAML frontmatter" % name)
        continue
    fm = head[1]
    if ("name: %s" % name) not in fm:
        failures.append("%s: frontmatter name is not %r" % (name, name))
    if "description:" not in fm:
        failures.append("%s: no description" % name)
    else:
        desc = fm.split("description:", 1)[1].split("\n")[0]
        if "superpowers" not in desc:
            failures.append("%s: description does not name the skill it displaces" % name)
        if ": " in desc and not desc.strip().startswith(("'", '"')):
            failures.append("%s: unquoted description contains ': ' - strict YAML "
                            "parsers reject it and npx skills silently skips the skill" % name)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python scripts/assert_vendored_closure.py`
Expected: FAIL with six `frontmatter name is not` lines — the copies still carry upstream's names.

- [ ] **Step 3: Rewrite the six frontmatter blocks**

Replace only the `name:` and `description:` lines in each SKILL.md. Leave the body untouched — that is Task 4. Each description keeps upstream's situation, then names the displacement (ADR 0071). Single-quote each value on one line, because every one contains `: `.

`sp-brainstorming`:
```yaml
name: sp-brainstorming
description: 'You MUST use this, and not the upstream superpowers brainstorming skill, before any creative work - creating features, building components, adding functionality, or modifying behavior. Explores user intent, requirements and design before implementation. The spec review goes to the scrutinize-dispatch skill.'
```

`sp-writing-plans`:
```yaml
name: sp-writing-plans
description: 'You MUST use this, and not the upstream superpowers writing-plans skill, when you have a spec or requirements for a multi-step task, before touching code. The plan review goes to the scrutinize-dispatch skill.'
```

`sp-executing-plans`:
```yaml
name: sp-executing-plans
description: 'You MUST use this, and not the upstream superpowers executing-plans skill, when you have a written implementation plan to execute in a separate session with review checkpoints. Reviews go to the scrutinize-dispatch skill.'
```

`sp-requesting-code-review`:
```yaml
name: sp-requesting-code-review
description: 'You MUST use this, and not the upstream superpowers requesting-code-review skill, when completing tasks, implementing major features, or before merging to verify work meets requirements. The review itself runs the scrutinize-dispatch skill.'
```

`sp-receiving-code-review`:
```yaml
name: sp-receiving-code-review
description: 'You MUST use this, and not the upstream superpowers receiving-code-review skill, when receiving code review feedback, before implementing suggestions, especially if feedback seems unclear or technically questionable - requires technical rigor and verification, not performative agreement or blind implementation.'
```

`sp-subagent-driven-development`:
```yaml
name: sp-subagent-driven-development
description: 'You MUST use this, and not the upstream superpowers subagent-driven-development skill, when executing implementation plans with independent tasks in the current session. Every dispatched review runs the scrutinize-dispatch skill.'
```

- [ ] **Step 4: Run the assertion to verify it passes**

Run: `python scripts/assert_vendored_closure.py`
Expected: `PASS: 21 files across six sp- directories, licence present`

- [ ] **Step 5: Validate and confirm the six skills load**

```bash
claude plugin validate plugins/dev-workflows
```
Expected: exit 0.

- [ ] **Step 6: Commit**

```bash
git add plugins/dev-workflows/skills/sp-*/SKILL.md scripts/assert_vendored_closure.py
git commit -m "feat(dev-workflows): rename vendored skills to sp-* and name the displacement (ADR 0071)"
```

---

### Task 4: Rewrite classes 1–4 — route the dispatches and fix the paths

**Files:**
- Modify: `plugins/dev-workflows/skills/sp-requesting-code-review/code-reviewer.md` (class 1)
- Modify: `plugins/dev-workflows/skills/sp-subagent-driven-development/task-reviewer-prompt.md` (class 1)
- Modify: `plugins/dev-workflows/skills/sp-subagent-driven-development/re-review-prompt.md` (class 1)
- Modify: `plugins/dev-workflows/skills/sp-subagent-driven-development/SKILL.md:88,117,118,454` (class 2)
- Modify: `plugins/dev-workflows/skills/sp-executing-plans/SKILL.md:14` (class 2)
- Modify: `plugins/dev-workflows/skills/sp-brainstorming/SKILL.md:250` (class 3)
- Modify: `plugins/dev-workflows/skills/sp-writing-plans/SKILL.md` (class 4)
- Create: `scripts/assert_rewrite_pass.py`

**Interfaces:**
- Consumes: `dev-workflows:scrutinize-dispatch` from Task 1; the six directories from Tasks 2–3.
- Produces: three prompt files whose review method is `scrutinize-dispatch`. Task 7's probe asserts the dispatched subagent loads that exact skill.

**Note on class 2's count:** ADR 0074's body says the cross-skill path appears "at three places"; its own amendment corrects this to **four** — lines 88, 117, 118 and 454. Three of them sit inside DOT node labels rather than markdown links, which is how a link-shaped read undercounted them. Use the amendment.

**Note on `executing-plans:14`:** it references `../using-superpowers/references/`, a skill that stays upstream and is never staged into Antigravity's flat skills directory. ADR 0074 leaves the choice between a qualified mention and a deletion open. **This plan chooses the qualified mention** — it preserves upstream's guidance, and a `superpowers:` string is inert rather than dangling when the plugin is absent.

- [ ] **Step 1: Write the failing rewrite assertion**

```python
# scripts/assert_rewrite_pass.py
"""Assert the ADR 0074 rewrite pass, classes 1-4, is fully applied."""
import io, sys, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = pathlib.Path("plugins/dev-workflows/skills")
failures = []

# class 1 - the three live reviewer prompts route to scrutinize-dispatch
PROMPTS = [
    "sp-requesting-code-review/code-reviewer.md",
    "sp-subagent-driven-development/task-reviewer-prompt.md",
    "sp-subagent-driven-development/re-review-prompt.md",
]
for rel in PROMPTS:
    p = ROOT / rel
    if not p.is_file():
        failures.append("missing prompt file %s" % rel)
        continue
    t = p.read_text(encoding="utf-8")
    if "scrutinize-dispatch" not in t:
        failures.append("%s does not route to scrutinize-dispatch" % rel)
    if "dev-workflows:scrutinize-dispatch" not in t:
        failures.append("%s uses a bare name - a missing copy would silently "
                        "launch the upstream twin; qualify it" % rel)

# class 2 - no cross-skill path may point at a non-sp- sibling
for rel in ["sp-subagent-driven-development/SKILL.md", "sp-executing-plans/SKILL.md"]:
    p = ROOT / rel
    if not p.is_file():
        continue
    t = p.read_text(encoding="utf-8")
    if "../requesting-code-review/" in t:
        failures.append("%s still points at ../requesting-code-review/ (needs sp-)" % rel)
    if "../using-superpowers/" in t:
        failures.append("%s still points at ../using-superpowers/ - that skill is "
                        "never staged; qualify it as superpowers:using-superpowers" % rel)

# class 3 - plugin-root-relative path becomes skill-relative
p = ROOT / "sp-brainstorming/SKILL.md"
if p.is_file() and "skills/brainstorming/visual-companion.md" in p.read_text(encoding="utf-8"):
    failures.append("sp-brainstorming/SKILL.md still uses a plugin-root path for its own file")

# class 4 - qualified handoffs among the six become short sp- names
p = ROOT / "sp-writing-plans/SKILL.md"
if p.is_file():
    t = p.read_text(encoding="utf-8")
    for bad in ("superpowers:executing-plans", "superpowers:subagent-driven-development"):
        if bad in t:
            failures.append("sp-writing-plans still hands off to %s" % bad)

# no copy may reference the frozen human-facing skill
for p in ROOT.glob("sp-*/**/*.md"):
    t = p.read_text(encoding="utf-8")
    if "scrutinize" in t and "scrutinize-dispatch" not in t:
        failures.append("%s references scrutinize but not scrutinize-dispatch" % p)

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)
print("PASS: rewrite pass classes 1-4 applied")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python scripts/assert_rewrite_pass.py`
Expected: FAIL, three `does not route to scrutinize-dispatch` lines plus the class 2/3/4 lines.

- [ ] **Step 3: Class 1 — replace the review method in the three prompts**

In each of the three prompt files, find the section that states the reviewer's own stance and checklist, and replace it with a delegation. Keep everything else: the placeholders, the operational rules, the output format, and the scoping rules. Insert this block in place of the stance section:

```markdown
    ## Review method

    Load the `dev-workflows:scrutinize-dispatch` skill through your harness's skill
    mechanism, and run its workflow against the diff above. That skill owns the
    review stance, the trace discipline, the severity calibration and the output
    format — do not duplicate or dilute it here, and do not substitute your own
    checklist for it.

    Everything in this prompt outside this section still applies: the context above,
    the operational rules below, and the report file you write to.
```

- [ ] **Step 4: Class 2 — repoint the four cross-skill paths in `sp-subagent-driven-development/SKILL.md`**

```bash
f="plugins/dev-workflows/skills/sp-subagent-driven-development/SKILL.md"
python - "$f" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
n = t.count("../requesting-code-review/")
assert n == 4, "expected 4 sites, found %d" % n
p.write_text(t.replace("../requesting-code-review/", "../sp-requesting-code-review/"),
             encoding="utf-8")
print("rewrote %d cross-skill paths" % n)
PY
```
Expected: `rewrote 4 cross-skill paths`

- [ ] **Step 5: Class 2 — qualify the `using-superpowers` reference at `sp-executing-plans/SKILL.md:14`**

Replace this substring:
```text
see the per-platform tool refs in `../using-superpowers/references/`
```
with:
```text
see the per-platform tool refs in the upstream `superpowers:using-superpowers` skill, which this marketplace does not vendor
```

Then in the same line replace `use superpowers:subagent-driven-development instead of this skill` with `use sp-subagent-driven-development instead of this skill`.

- [ ] **Step 6: Class 3 — make `sp-brainstorming`'s own-file path skill-relative**

At `sp-brainstorming/SKILL.md:250`, replace `skills/brainstorming/visual-companion.md` with `visual-companion.md`.

- [ ] **Step 7: Class 4 — short-form the handoffs among the six**

```bash
cd plugins/dev-workflows/skills
python - <<'PY'
import pathlib
pairs = [("superpowers:brainstorming", "sp-brainstorming"),
         ("superpowers:writing-plans", "sp-writing-plans"),
         ("superpowers:executing-plans", "sp-executing-plans"),
         ("superpowers:subagent-driven-development", "sp-subagent-driven-development"),
         ("superpowers:requesting-code-review", "sp-requesting-code-review"),
         ("superpowers:receiving-code-review", "sp-receiving-code-review")]
total = 0
for p in pathlib.Path(".").glob("sp-*/**/*.md"):
    t = old = p.read_text(encoding="utf-8")
    for a, b in pairs:
        t = t.replace(a, b)
    if t != old:
        p.write_text(t, encoding="utf-8")
        total += 1
print("rewrote handoffs in %d file(s)" % total)
PY
cd ../../..
```

The eight non-copied skills keep their `superpowers:` qualification — this replaces only the six names in the copy set.

- [ ] **Step 8: Run the assertion to verify it passes**

Run: `python scripts/assert_rewrite_pass.py`
Expected: `PASS: rewrite pass classes 1-4 applied`

- [ ] **Step 9: Confirm the eight non-copied handoffs still resolve upstream**

```bash
grep -rho "superpowers:[a-z-]*" plugins/dev-workflows/skills/sp-* | sort -u
```
Expected: only `superpowers:finishing-a-development-branch`, `superpowers:using-git-worktrees` and `superpowers:using-superpowers`. Eleven references total, unchanged in count. Any `superpowers:` name from the copy set appearing here is a missed class-4 site.

- [ ] **Step 10: Commit**

```bash
git add plugins/dev-workflows/skills/sp-* scripts/assert_rewrite_pass.py
git commit -m "feat(dev-workflows): route the four reviewer dispatches to scrutinize-dispatch (ADRs 0074, 0084)"
```

---

### Task 5: The host SessionStart hook

**Files:**
- Modify: `plugins/dev-workflows/hooks/hooks.json`
- Create: `plugins/dev-workflows/hooks/session-start.py`

**Interfaces:**
- Consumes: the six skill names from Task 3.
- Produces: a `SessionStart` hook whose injected text names `sp-brainstorming`. Task 7's probe measures its effect.

**Why this exists:** the upstream plugin stays fully enabled, and its own `SessionStart` hook injects `using-superpowers/SKILL.md` verbatim, which names `superpowers:brainstorming`. Without a counter-hook, entry into the arc goes upstream and touchpoint #1 is lost with no error. ADR 0070 measured this: control runs answered `superpowers:brainstorming` twice; with a host hook, three runs of three answered the host's skill instead — **even though the host text landed first in the merged attachment**. Specificity wins, position does not. Word it to name the conflict outright; do not rely on ordering.

`hooks.json` is currently `{"hooks": {}}` — the `PostToolUse` commit-log hook was removed in `e7839a8` and ADR 0054 is bannered Retired. This task adds the `SessionStart` entry to that empty object.

- [ ] **Step 1: Write the failing hook assertion**

```python
# append to scripts/assert_rewrite_pass.py, before `if failures:`
import json
hj = pathlib.Path("plugins/dev-workflows/hooks/hooks.json")
if not hj.is_file():
    failures.append("hooks.json is missing")
else:
    cfg = json.loads(hj.read_text(encoding="utf-8"))
    ss = cfg.get("hooks", {}).get("SessionStart")
    if not ss:
        failures.append("no SessionStart hook registered")
    else:
        blob = json.dumps(ss)
        if "session-start.py" not in blob:
            failures.append("SessionStart does not call session-start.py")
        if "${CLAUDE_PLUGIN_ROOT}" not in blob:
            failures.append("hook command must use ${CLAUDE_PLUGIN_ROOT}, not a hard-coded path")
hp = pathlib.Path("plugins/dev-workflows/hooks/session-start.py")
if not hp.is_file():
    failures.append("session-start.py is missing")
else:
    t = hp.read_text(encoding="utf-8")
    if "sp-brainstorming" not in t:
        failures.append("hook text does not name sp-brainstorming")
    if "instead of" not in t:
        failures.append("hook text does not name the conflict outright (ADR 0070)")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python scripts/assert_rewrite_pass.py`
Expected: FAIL with `no SessionStart hook registered` and `session-start.py is missing`.

- [ ] **Step 3: Write the hook script**

```python
# plugins/dev-workflows/hooks/session-start.py
"""SessionStart hook: re-point the one skill the upstream superpowers hook names.

The upstream plugin injects skills/using-superpowers/SKILL.md verbatim at session
start, and that text names superpowers:brainstorming as the entry into the arc.
This marketplace vendors six of those skills under an sp- prefix so their reviewer
dispatches reach scrutinize-dispatch. Both texts arrive in one merged attachment,
so this text must win on specificity, not on position (ADR 0070).

Emits nothing when the dev-workflows copies are not present, so a partial install
degrades to silence rather than to a wrong instruction.
"""
import io, json, os, sys, pathlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

root = pathlib.Path(os.environ.get("CLAUDE_PLUGIN_ROOT", ""))
if not (root / "skills" / "sp-brainstorming" / "SKILL.md").is_file():
    sys.exit(0)

TEXT = (
    "IMPORTANT - this marketplace vendors the superpowers review skills. "
    "When you would invoke superpowers:brainstorming, superpowers:writing-plans, "
    "superpowers:executing-plans, superpowers:subagent-driven-development, "
    "superpowers:requesting-code-review or superpowers:receiving-code-review, "
    "you MUST invoke dev-workflows:sp-brainstorming, dev-workflows:sp-writing-plans, "
    "dev-workflows:sp-executing-plans, dev-workflows:sp-subagent-driven-development, "
    "dev-workflows:sp-requesting-code-review or dev-workflows:sp-receiving-code-review "
    "INSTEAD OF the upstream skill of the same name. This is not a preference: the "
    "upstream copies send every code review to the built-in reviewer, and the sp- "
    "copies send it to dev-workflows:scrutinize-dispatch, which is the whole reason "
    "they exist. Every other superpowers skill is unchanged - use it as normal."
)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": TEXT,
    }
}))
```

- [ ] **Step 4: Register it in `hooks.json`**

Replace the whole file with:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python \"${CLAUDE_PLUGIN_ROOT}/hooks/session-start.py\"",
            "async": false
          }
        ]
      }
    ]
  }
}
```

- [ ] **Step 5: Run the assertion to verify it passes**

Run: `python scripts/assert_rewrite_pass.py`
Expected: `PASS: rewrite pass classes 1-4 applied`

- [ ] **Step 6: Verify the hook emits valid JSON and is silent when the copies are absent**

```bash
CLAUDE_PLUGIN_ROOT="plugins/dev-workflows" python plugins/dev-workflows/hooks/session-start.py | python -c "import json,sys; d=json.load(sys.stdin); print('OK:', d['hookSpecificOutput']['hookEventName'])"
CLAUDE_PLUGIN_ROOT="/nonexistent" python plugins/dev-workflows/hooks/session-start.py && echo "SILENT OK"
```
Expected: `OK: SessionStart`, then `SILENT OK` with no JSON printed.

- [ ] **Step 7: Commit**

```bash
git add plugins/dev-workflows/hooks/hooks.json plugins/dev-workflows/hooks/session-start.py scripts/assert_rewrite_pass.py
git commit -m "feat(dev-workflows): host SessionStart hook re-points the skills the upstream hook names (ADR 0070)"
```

---

### Task 6: Repo conventions — PLAYBOOK rows, versions, glossary

**Files:**
- Modify: `PLAYBOOK.md` (one new grouped section, seven rows)
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json` (version)
- Modify: `.claude-plugin/marketplace.json` (the `dev-workflows` entry's version)
- Modify: `CONTEXT.md` (two glossary terms)

**Interfaces:**
- Consumes: the seven skill names from Tasks 1 and 3.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Write the failing conventions assertion**

```python
# scripts/assert_conventions.py
import io, sys, json, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
failures = []

SKILLS = ["scrutinize-dispatch", "sp-brainstorming", "sp-writing-plans",
          "sp-executing-plans", "sp-requesting-code-review",
          "sp-receiving-code-review", "sp-subagent-driven-development"]
pb = pathlib.Path("PLAYBOOK.md").read_text(encoding="utf-8")
for s in SKILLS:
    if s not in pb:
        failures.append("PLAYBOOK.md has no row for %s" % s)

pj = json.loads(pathlib.Path("plugins/dev-workflows/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
mk = json.loads(pathlib.Path(".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
entry = next((p for p in mk["plugins"] if p["name"] == "dev-workflows"), None)
if entry is None:
    failures.append("dev-workflows missing from marketplace.json")
elif entry["version"] != pj["version"]:
    failures.append("version mismatch: plugin.json %s vs marketplace.json %s"
                    % (pj["version"], entry["version"]))

ctx = pathlib.Path("CONTEXT.md").read_text(encoding="utf-8")
for term in ("Vendored Skill", "Reviewer prompt"):
    if term not in ctx:
        failures.append("CONTEXT.md missing glossary term %r" % term)

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)
print("PASS: PLAYBOOK rows, version parity, glossary terms")
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python scripts/assert_conventions.py`
Expected: FAIL with seven `PLAYBOOK.md has no row` lines and two glossary lines.

- [ ] **Step 3: Add the PLAYBOOK section**

Insert after the "WORKING — the situational router" table, before "### The debug chain":

```markdown
### Vendored superpowers skills (ADRs 0071, 0074, 0084)

Six upstream `superpowers` skills are vendored here under an `sp-` prefix so their
reviewer dispatches reach this repo's reviewer instead of the built-in one. Prefer the
`sp-` copy over the upstream skill of the same name; every *other* superpowers skill is
unchanged and used as normal.

| When… | Reach for |
|---|---|
| a dispatched reviewer subagent needs to run a review | `scrutinize-dispatch` — the scoped counterpart to `scrutinize`; emits `Critical/Important/Minor` and a spec-compliance verdict. Not for human-facing review — that is `scrutinize` |
| brainstorming a feature before implementation | `sp-brainstorming` — displaces `superpowers:brainstorming` |
| writing an implementation plan from a spec | `sp-writing-plans` — displaces `superpowers:writing-plans` |
| executing a written plan in a separate session | `sp-executing-plans` — displaces `superpowers:executing-plans` |
| executing a plan task-by-task with dispatched subagents | `sp-subagent-driven-development` — displaces `superpowers:subagent-driven-development`; all four reviewer dispatches route to `scrutinize-dispatch` |
| requesting a code review before merge | `sp-requesting-code-review` — displaces `superpowers:requesting-code-review` |
| receiving and triaging review feedback | `sp-receiving-code-review` — displaces `superpowers:receiving-code-review` |
```

- [ ] **Step 4: Add the two glossary terms to `CONTEXT.md`**

```markdown
- **Vendored Skill** — one of the six `sp-`-prefixed skills under
  `plugins/dev-workflows/skills/`, copied verbatim from `obra/superpowers` at
  `b36e0829c6d0` and then edited by one enumerated rewrite pass. A Vendored Skill is
  not a fork to be improved locally: every edit is re-applied on each upstream pull, so
  the edited set is deliberately small (ADR 0074).
- **Reviewer prompt** — the harness half of a dispatched review: the file that supplies
  the per-touchpoint context, the operational rules and the output contract, and that
  delegates the review method to `scrutinize-dispatch`. There are three:
  `code-reviewer.md`, `task-reviewer-prompt.md`, `re-review-prompt.md` (ADRs 0076, 0084).
```

- [ ] **Step 5: Mint the version from the global max and set both files**

```bash
cd "$(git rev-parse --show-toplevel)"
{ git for-each-ref --format='%(refname:short)' refs/heads refs/remotes refs/stash |
    while IFS= read -r r; do git show "$r:plugins/dev-workflows/.claude-plugin/plugin.json" 2>/dev/null; done
  git worktree list --porcelain | sed -n 's|^worktree ||p' |
    while IFS= read -r p; do cat "$p/plugins/dev-workflows/.claude-plugin/plugin.json" 2>/dev/null; done
} | grep -o '"version": "[0-9.]*"' | grep -o '[0-9.]*' | sort -V | tail -1
```
Take that value, bump the **minor** component (this adds seven skills), and write the same string into both `plugins/dev-workflows/.claude-plugin/plugin.json` and the `dev-workflows` entry in `.claude-plugin/marketplace.json`. At the time of writing the max is `0.37.0`, so the expected new value is `0.38.0` — re-run the scan rather than trusting that number.

- [ ] **Step 6: Run the assertion to verify it passes**

Run: `python scripts/assert_conventions.py`
Expected: `PASS: PLAYBOOK rows, version parity, glossary terms`

- [ ] **Step 7: Commit**

```bash
git add PLAYBOOK.md CONTEXT.md plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json scripts/assert_conventions.py
git commit -m "docs: PLAYBOOK rows and glossary for the vendored skills, version parity"
```

---

### Task 7: The acceptance probe — prove a dispatched review actually ran `scrutinize-dispatch`

This is the only evidence the whole effort works, and it **cannot be reconstructed after the fact**. ADR 0079 measured that the dispatched subagent's `Skill` record never reaches the persisted session log: the proof exists only in the live dispatch stream, so the probe must be arranged in advance and run deliberately. Treat a skipped probe as a failed plan, not a deferred nicety.

**Files:**
- Create: `docs/superpowers/plans/2026-08-16-acceptance-probe-result.md`
- Delete: `scripts/assert_scrutinize_dispatch.py`, `scripts/assert_vendored_closure.py`, `scripts/assert_rewrite_pass.py`, `scripts/assert_conventions.py`

**Interfaces:**
- Consumes: everything from Tasks 1–6.
- Produces: a recorded result. Plan B's resync checker generalizes the four assertion scripts, which is why they are deleted here rather than kept.

- [ ] **Step 1: Run every assertion once more, together**

```bash
for s in scrutinize_dispatch vendored_closure rewrite_pass conventions; do
  python "scripts/assert_$s.py" || echo "^^ FAILED: $s"
done
```
Expected: four `PASS:` lines, no `FAILED` lines.

- [ ] **Step 2: Restart Claude Code so the plugin and hook reload**

The marketplace is a directory source, so editing the repo *is* the deploy — but a `SessionStart` hook and new skills only register on a fresh session. Start a new session in this repo before Step 3.

- [ ] **Step 3: Run the control**

In a fresh session, with the `superpowers` plugin enabled and this marketplace **not** yet reloaded (or in a directory outside this repo), ask:

> build a new feature — name the ONE skill you would invoke first

Expected: `superpowers:brainstorming`. This confirms the upstream hook really does steer, which is the premise the whole design rests on. Record the answer.

- [ ] **Step 4: Run the test — the hook**

In a fresh session in this repo, ask the same question.

Expected: `sp-brainstorming` (or `dev-workflows:sp-brainstorming`). Record the answer. If it still answers `superpowers:brainstorming`, the hook text lost — re-word it to be more specific, not to land later, and re-run.

- [ ] **Step 5: Run the test — the dispatch**

In this repo, invoke `sp-subagent-driven-development` on any small two-task plan, and let it reach its first task review. Watch the dispatched reviewer subagent's tool stream.

Expected: a `Skill` tool_use in the **subagent's own stream** naming `dev-workflows:scrutinize-dispatch`. That record is written by the harness, so it cannot be faked by the subagent claiming it. Confirm the returned report carries `## Spec Compliance` and at least one of the three severity headings.

- [ ] **Step 6: Record the result**

Write `docs/superpowers/plans/2026-08-16-acceptance-probe-result.md` with: the date, the Claude Code version (`claude --version`), the control answer, the hook answer, whether the `Skill` record named `scrutinize-dispatch`, and the report's section headings. State plainly if any step did not reproduce. A probe that half-worked is a finding, not a rounding error.

- [ ] **Step 7: Delete the temporary assertion scripts**

```bash
git rm scripts/assert_scrutinize_dispatch.py scripts/assert_vendored_closure.py \
       scripts/assert_rewrite_pass.py scripts/assert_conventions.py
```

- [ ] **Step 8: Confirm `scrutinize` is still byte-identical to where it started**

```bash
git log --oneline -- plugins/dev-workflows/skills/scrutinize/SKILL.md | head -3
```
Expected: no commit from this plan touches it. `scrutinize` is frozen by decision and this is the last chance to catch a violation.

- [ ] **Step 9: Commit**

```bash
git add docs/superpowers/plans/2026-08-16-acceptance-probe-result.md
git commit -m "test: record the routing acceptance probe - a dispatched review runs scrutinize-dispatch (ADR 0079)"
```

---

## Self-review

**Spec coverage.** ADR 0084 → Task 1. ADR 0074 (21 files, five rewrite classes) → Tasks 2–4. ADR 0071 (names, descriptions) → Task 3. ADR 0070/0073 (host hook, in `dev-workflows`) → Task 5. Attribution ADR (`LICENSE-superpowers`, sha, MODIFIED marker, no per-file headers) → Task 2. ADR 0077 (three wiring conventions bind; Mermaid rule does not) → Tasks 3, 4, 6. ADR 0079 (probe) → Task 7. **Deferred to Plan B, by the scope decision:** ADR 0075 (resync checker + manifest), ADR 0082 (setup-check), ADR 0081 (three commands), ADR 0072/0080 (arc rewiring and the Step 0 warning), and the Antigravity install run.

**Gaps I am naming rather than papering over.**

1. **Class 1 is the one step in this plan that is not mechanical.** Steps 3 of Task 4 says *"find the section that states the reviewer's own stance and checklist"* — its exact line range differs across the three prompt files, so the plan cannot give one span. The implementer must read each file. The assertion in Step 1 catches a missed file, but it cannot catch a *sloppy* excision that removes an operational rule along with the stance. Re-read the three files against upstream after the edit.
2. **Task 7 Step 3's control is awkward on a machine where this marketplace is already installed.** The honest control needs a session where the host hook does not fire. If that cannot be arranged, record the control as not-run rather than inventing it — ADR 0070 already has a clean control from its own measurement.
3. **The Antigravity half is untested by this plan.** `install-antigravity.py` rewrites and leak-checks markdown only, and the copies bring eight non-markdown files. At `b36e0829c6d0` this is benign — verified: the only plugin-root dependency outside markdown is `server.cjs:209`, which degrades to reporting version `unknown`. Running the installer belongs to Plan B.

**Placeholder scan.** No `TBD`, no "add error handling", no "similar to Task N". Every code step carries runnable content. The one prose-only instruction is Task 4 Step 3, named in gap 1 above.

**Type consistency.** The skill name `scrutinize-dispatch` is used identically in Task 1 (frontmatter), Task 3 (descriptions), Task 4 (prompts and assertions), Task 6 (PLAYBOOK) and Task 7 (probe). The qualified form `dev-workflows:scrutinize-dispatch` is what Task 4's assertion requires and what Task 7 looks for in the stream. The six `sp-` directory names are spelled identically in Tasks 2, 3, 4, 5 and 6.
