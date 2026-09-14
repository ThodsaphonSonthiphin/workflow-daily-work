# guide-and-verify failed-check handoff — Implementation Plan
> **Refined by ADR 0221 (2026-09-14, whole-branch review):** the Freeze line reads *"change anything in the console"*, not *"touch the console"*; Task 1's check literal and block were updated to match at the fix wave.

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** When a `guide-and-verify` after-check fails, the skill hands off to `debug-mantra` behind a one-line freeze and returns with a corrected step — never "try again".

**Architecture:** Prose-only change to one skill file plus its discoverability surfaces (PLAYBOOK row + diagram, plugin description, one eval case), a minor version bump in both manifests, and the regenerated `skills/` tree. `debug-mantra` is not touched (owner ruling, ADR 0216). Tests are shell/JSON assertions run before (fail) and after (pass) each edit, plus the repo's own `check_skills_tree.py` gate.

**Tech Stack:** Markdown skill files, JSON manifests, Python 3 (`python3` — macOS has no bare `python`), git.

**Spec:** `docs/superpowers/specs/2026-09-14-guide-and-verify-failed-check-handoff-design.md` — read it first; every task cites the ADR it implements.

## Global Constraints

- **Do not edit anything under `plugins/dev-workflows/skills/debug-mantra/`** (ADR 0216, owner ruling 2026-09-14).
- **Harness-neutral wording only:** say "load `debug-mantra` through your harness's mechanism", never "call the Skill tool" (CLAUDE.md).
- **Versions in sync:** `plugins/dev-workflows/.claude-plugin/plugin.json` and the `dev-workflows` entry in `.claude-plugin/marketplace.json` both go `0.54.0 → 0.55.0`.
- **Never hand-edit `skills/`** — regenerate with `python3 scripts/generate_skills_tree.py`, gate with `python3 scripts/check_skills_tree.py`.
- **ADR citations inside this repo are bare numbers** (ADR 0093): `ADR 0214`, not the filename prefix.
- **Use the CONTEXT.md terms** **Freeze line** and **Corrected step** (already defined there this session) — not "warning", "retry", "redo".
- **Every commit ends with the trailer, verbatim:** `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>`
- **Branch:** all work on `guide-and-verify-failed-check-handoff`, branched from `main` at `c781c68`. The merge into `main` is the owner's, after Task 6.
- Run commands from the repo root: `/Users/liusp/Documents/repo/workflow-daily-work`.

---

### Task 1: Branch, commit the design docs, add the Phase 4 handoff subsection

**Files:**
- Modify: `plugins/dev-workflows/skills/guide-and-verify/SKILL.md` — insert after line 178 (the paragraph ending `makes it worse.`), before `### 5. Teach the self-check, and record the result`
- Commit (already written, uncommitted): `CONTEXT.md`, `docs/adr/workflow-daily-work-0214-*.md` … `0220-*.md`, `docs/superpowers/specs/2026-09-14-guide-and-verify-failed-check-handoff-design.md`, and this plan

**Interfaces:**
- Consumes: nothing.
- Produces: the heading `#### When the check fails: hand off to debug-mantra` in `guide-and-verify/SKILL.md` — Task 5's generator copies this file verbatim into `skills/guide-and-verify/SKILL.md`.

- [ ] **Step 1: Create the branch and commit the design documents**

```bash
git checkout -b guide-and-verify-failed-check-handoff
git add CONTEXT.md docs/adr/workflow-daily-work-021[4-9]-*.md docs/adr/workflow-daily-work-0220-*.md \
        docs/superpowers/specs/2026-09-14-guide-and-verify-failed-check-handoff-design.md \
        docs/superpowers/plans/2026-09-14-guide-and-verify-failed-check-handoff.md
git commit -m "docs: ADRs 0214-0220, spec and plan — guide-and-verify hands a failed after-check to debug-mantra

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

Expected: one commit, 10 files (CONTEXT.md, 7 ADRs, spec, plan). `git status --short` prints nothing.

- [ ] **Step 2: Write the failing check**

Save as `/private/tmp/claude-501/-Users-liusp-Documents-repo-workflow-daily-work/37b74f25-11fe-4007-bb66-a304132f2b90/scratchpad/check_task1.sh` (scratchpad, not the repo):

```bash
#!/bin/sh
# Task 1 assertions on guide-and-verify/SKILL.md — exit 0 only when every line holds.
f=plugins/dev-workflows/skills/guide-and-verify/SKILL.md
fail=0
chk() { if ! grep -qF -- "$1" "$f"; then echo "MISSING: $1"; fail=1; fi; }
chk '#### When the check fails: hand off to debug-mantra'
chk 'Check failed: expected `<assertion>`, got `<measured>`'
chk 'Do not redo the step or change anything in the console'
chk 'through your harness'
chk 'hypothesis #1 is always the saved-is-not-applied trap'
chk 'reported by the operator, not independently measured'
chk 'The runbook session is one debug session'
chk 'Corrected step'
chk 'ADR 0214'; chk 'ADR 0215'; chk 'ADR 0216'; chk 'ADR 0217'; chk 'ADR 0218'; chk 'ADR 0219'; chk 'ADR 0220'
# ordering: the new heading sits between Phase 4's last paragraph and Phase 5's heading
a=$(grep -n 'makes it worse\.' "$f" | cut -d: -f1)
h=$(grep -n '#### When the check fails' "$f" | cut -d: -f1)
p5=$(grep -n '### 5\. Teach the self-check' "$f" | cut -d: -f1)
if [ -z "$h" ] || [ "$a" -ge "$h" ] || [ "$h" -ge "$p5" ]; then echo "ORDER: heading not between Phase 4 tail ($a) and Phase 5 ($p5): $h"; fail=1; fi
# the new section must not say the forbidden thing outside its one quoted mention
sec=$(sed -n "${h:-0},${p5:-0}p" "$f")
n=$(printf '%s\n' "$sec" | grep -c 'try again')
if [ "$n" -ne 1 ]; then echo "'try again' must appear exactly once in the new section (as the prohibition); got $n"; fail=1; fi
if grep -qi 'Skill tool' "$f"; then echo "harness-specific wording found"; fail=1; fi
exit $fail
```

- [ ] **Step 3: Run it to verify it fails**

Run: `sh "$SCRATCH/check_task1.sh"` (with `SCRATCH=/private/tmp/claude-501/-Users-liusp-Documents-repo-workflow-daily-work/37b74f25-11fe-4007-bb66-a304132f2b90/scratchpad`)
Expected: prints `MISSING: #### When the check fails: hand off to debug-mantra` (and the other MISSING lines), exit 1.

- [ ] **Step 4: Insert the subsection**

Insert the following block **verbatim** after line 178 of `plugins/dev-workflows/skills/guide-and-verify/SKILL.md` — i.e. after the paragraph that ends `…on a step that partly landed makes it worse.` and before the blank line preceding `### 5. Teach the self-check, and record the result`. Keep one blank line above and below the block.

````markdown
#### When the check fails: hand off to debug-mantra

A failed after-check — the success condition or the blast radius — is the one moment in this
skill where something misbehaved and the person is about to act on a guess. Do not diagnose by
improvising, and never propose a redo on an unverified cause (ADR 0214, the mirror of
ADR 0011). Hand off to `debug-mantra`, in this order.

**1. The Freeze line goes out first** (ADR 0215). Before the mantra, before any question, the
person reads one line in the runbook's own shape, with the numbers:

> Check failed: expected `<assertion>`, got `<measured>`.
> Do not redo the step or change anything in the console — a redo destroys the state that tells not-saved
> from not-applied from wrong-object. I am finding out why first.

Then load `debug-mantra` through your harness's mechanism and follow it as written. The recital
stays verbatim and complete; only the Freeze line precedes it (ADR 0216). What changes is what
you already hold when it opens.

**2. What you already hold, per step** (ADR 0217) — do not ask the person for any of it:

| debug-mantra step | you already have |
|---|---|
| ① reproduce | the baseline and the after-measurement — the repro is the diff. The environment is the one the runbook names; there is no "local or deployed?" to ask |
| ② fail path | the step's own numbered lines — the question is which line did not land |
| ③ falsify | **hypothesis #1 is always the saved-is-not-applied trap.** Read the pending state first; the table under *The trap that catches nearly every system* says where it lives for each kind of system; rank the rest yourself |
| ④ breadcrumbs | the per-check measurements you wrote on the ticket in Phase 1 — a half-applied step shows as a contradiction between two of them |

**3. No second channel** (ADR 0218). The handoff fires anyway. Step ① is met the way Phase 1
meets it when you cannot read the system: borrow the person's eyes — one read-only look, pasted
back. A read-only look is not a redo — the Freeze line forbids changes, not looks (ADR 0221). That
run, and every claim built on it, carries the label
*reported by the operator, not independently measured*.

**4. A second failure in the same runbook** (ADR 0219). The runbook session is one debug
session. Send the Freeze line again and re-enter at step ①; do not recite the mantra a second
time, and keep the ledger — the earlier runs are still evidence, because the system, the person
and the console are the same.

**5. When the cause is confirmed** (ADR 0220). Return to Phase 3 and write a **Corrected step**
in the fixed shape — the missing apply or publish as its own numbered line — asserted against
the failed step's after-measurement as its baseline. Never "try again". If the cause was yours —
a Phase 1 count, a Phase 2 prediction — say so, and the corrected thing is the runbook. Write
the cause and both timestamps into the Phase 5 outcome line on the ticket: *"Step 2 failed
09:14Z — cause: saved, not published; corrected step landed 09:31Z, 1 → 0"*. If the cause is a
real defect in the system rather than a missed click, that is a hand-off out of the runbook to
the debug chain (ADR 0003: fix → post-mortem → management-talk) — name it as such and stop the
runbook there.
````

- [ ] **Step 5: Run the check to verify it passes**

Run: `sh "$SCRATCH/check_task1.sh"`
Expected: no output, exit 0.

- [ ] **Step 6: Read the result in context**

Run: `sed -n 170,232p plugins/dev-workflows/skills/guide-and-verify/SKILL.md`
Expected: the Phase 4 paragraph, one blank line, the `####` heading, the block, one blank line, `### 5. Teach the self-check…`. No duplicated blank lines, no stray backtick fences.

- [ ] **Step 7: Commit**

```bash
git add plugins/dev-workflows/skills/guide-and-verify/SKILL.md
git commit -m "feat(guide-and-verify): a failed after-check hands off to debug-mantra behind a Freeze line (ADRs 0214-0220)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 2: PLAYBOOK row and WORK diagram

**Files:**
- Modify: `PLAYBOOK.md:68` (the `DM` node line in the WORK mermaid block) and `PLAYBOOK.md:103` (the `guide-and-verify` row)

**Interfaces:**
- Consumes: nothing from Task 1 (independent surfaces).
- Produces: mermaid node id `GAV` in the WORK diagram — nothing later depends on it.

- [ ] **Step 1: Write the failing check**

Save as `$SCRATCH/check_task2.sh`:

```bash
#!/bin/sh
f=PLAYBOOK.md; fail=0
chk() { if ! grep -qF -- "$1" "$f"; then echo "MISSING: $1"; fail=1; fi; }
chk 'WORK -- hand-work in a console I cannot write to --> GAV["guide-and-verify"]'
chk 'GAV -. after-check fails .-> DM'
chk 'and when an after-check fails, it hands off to `debug-mantra`'
chk '(ADRs 0214–0220)'
# both new diagram lines must sit inside the WORK mermaid block (opens at the 2nd ```mermaid)
open=$(grep -n '^```mermaid' "$f" | sed -n 2p | cut -d: -f1)
close=$(awk -v o="$open" 'NR>o && /^```$/ {print NR; exit}' "$f")
for pat in 'GAV\["guide-and-verify"\]' 'GAV -\. after-check fails \.-> DM'; do
  ln=$(grep -n "$pat" "$f" | head -1 | cut -d: -f1)
  if [ -z "$ln" ] || [ "$ln" -le "$open" ] || [ "$ln" -ge "$close" ]; then echo "OUTSIDE WORK BLOCK ($open..$close): $pat at $ln"; fail=1; fi
done
# GAV must be defined once
n=$(grep -c 'GAV\["guide-and-verify"\]' "$f"); [ "$n" -eq 1 ] || { echo "GAV defined $n times"; fail=1; }
exit $fail
```

- [ ] **Step 2: Run it to verify it fails**

Run: `sh "$SCRATCH/check_task2.sh"`
Expected: four `MISSING:` lines, exit 1.

- [ ] **Step 3: Edit the WORK diagram**

In `PLAYBOOK.md`, the line

```
    WORK -- 💥 something broke --> DM["debug-mantra<br/>(diagnose)"]
```

becomes these three lines (the original line unchanged, two added directly beneath it):

```
    WORK -- 💥 something broke --> DM["debug-mantra<br/>(diagnose)"]
    WORK -- hand-work in a console I cannot write to --> GAV["guide-and-verify"]
    GAV -. after-check fails .-> DM
```

- [ ] **Step 4: Edit the row**

In `PLAYBOOK.md` line 103, the row currently ends:

```
…then prove it landed read-only in a channel other than the one they edited in |
```

Replace that ending with:

```
…then prove it landed read-only in a channel other than the one they edited in — and when an after-check fails, it hands off to `debug-mantra` (Freeze line first, saved-is-not-applied as hypothesis #1) and returns with a Corrected step, never "try again" (ADRs 0214–0220) |
```

The full row after the edit is one line:

```
| a change only a human can make by hand, in a console you cannot write to (CRM, cloud portal, DNS, SaaS admin, CI settings, a database GUI) | `guide-and-verify` — measure the live baseline first, hand over Go to / Do / Do not / verify-yourself steps one at a time, then prove it landed read-only in a channel other than the one they edited in — and when an after-check fails, it hands off to `debug-mantra` (Freeze line first, saved-is-not-applied as hypothesis #1) and returns with a Corrected step, never "try again" (ADRs 0214–0220) |
```

- [ ] **Step 5: Run the check to verify it passes**

Run: `sh "$SCRATCH/check_task2.sh"`
Expected: no output, exit 0.

- [ ] **Step 6: Eyeball the diagram block**

Run: `sed -n 42,80p PLAYBOOK.md`
Expected: `GAV` lines sit directly under the `DM` line, same 4-space indent, inside the fence.

- [ ] **Step 7: Commit**

```bash
git add PLAYBOOK.md
git commit -m "docs(playbook): guide-and-verify hands a failed after-check to debug-mantra — row clause and WORK edge (ADRs 0214-0220)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 3: Plugin description clause and version bump in both manifests

**Files:**
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json` — `"version"` and the `"description"` string
- Modify: `.claude-plugin/marketplace.json` — the `dev-workflows` entry's `"version"` (line 36) and its `"description"` string (line 35)

**Interfaces:**
- Consumes: nothing.
- Produces: version `0.55.0` — Task 5's generated tree may embed nothing version-related, but Task 6 asserts both manifests agree.

- [ ] **Step 1: Write the failing check**

Save as `$SCRATCH/check_task3.py`:

```python
import json, sys
P = "plugins/dev-workflows/.claude-plugin/plugin.json"
M = ".claude-plugin/marketplace.json"
clause = "a failed after-check hands off to debug-mantra behind a one-line freeze and returns with a corrected step, never 'try again'"
p = json.load(open(P, encoding="utf-8"))
m = next(x for x in json.load(open(M, encoding="utf-8"))["plugins"] if x["name"] == "dev-workflows")
errs = []
if p["version"] != "0.55.0": errs.append(f"plugin.json version {p['version']} != 0.55.0")
if m["version"] != "0.55.0": errs.append(f"marketplace.json version {m['version']} != 0.55.0")
for name, d in (("plugin.json", p["description"]), ("marketplace.json", m["description"])):
    if clause not in d: errs.append(f"{name}: clause missing")
    if "or you cannot read the system at all; " + clause not in d:
        errs.append(f"{name}: clause not attached to the guide-and-verify sentence")
print("\n".join(errs)); sys.exit(1 if errs else 0)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 "$SCRATCH/check_task3.py"`
Expected: four lines (two version mismatches, two clause-missing), exit 1.

- [ ] **Step 3: Edit both descriptions**

In **both** files, inside the guide-and-verify sentence, the text

```
or you cannot read the system at all)
```

becomes

```
or you cannot read the system at all; a failed after-check hands off to debug-mantra behind a one-line freeze and returns with a corrected step, never 'try again')
```

(Single quotes around `try again` — the description is a JSON string and the rest of it uses no double quotes inside.)

- [ ] **Step 4: Bump both versions**

In `plugins/dev-workflows/.claude-plugin/plugin.json`: `"version": "0.54.0"` → `"version": "0.55.0"`.
In `.claude-plugin/marketplace.json`, the `dev-workflows` entry only (line 36): `"version": "0.54.0"` → `"version": "0.55.0"`. Do not touch the other plugins' versions.

- [ ] **Step 5: Run the check to verify it passes**

Run: `python3 "$SCRATCH/check_task3.py"`
Expected: empty line, exit 0.

- [ ] **Step 6: Confirm both files still parse and nothing else moved**

Run: `python3 -c "import json;json.load(open('.claude-plugin/marketplace.json'));json.load(open('plugins/dev-workflows/.claude-plugin/plugin.json'));print('ok')" && git diff --stat`
Expected: `ok`; diff stat shows exactly the two files, 2 lines changed in each.

- [ ] **Step 7: Commit**

```bash
git add plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(dev-workflows): 0.54.0 -> 0.55.0 — guide-and-verify failed-check handoff in the description

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 4: Eval case for the failed after-check

**Files:**
- Modify: `plugins/dev-workflows/skills/guide-and-verify/evals/evals.json` — append one object to `"evals"`

**Interfaces:**
- Consumes: nothing.
- Produces: eval `id: 3`, `name: "failed-after-check-hands-off"`; Task 5's generator copies the file.

- [ ] **Step 1: Write the failing check**

Save as `$SCRATCH/check_task4.py`:

```python
import json, sys
E = "plugins/dev-workflows/skills/guide-and-verify/evals/evals.json"
d = json.load(open(E, encoding="utf-8"))
errs = []
ids = [e["id"] for e in d["evals"]]
if ids != [0, 1, 2, 3]: errs.append(f"ids {ids} != [0,1,2,3]")
c = next((e for e in d["evals"] if e.get("name") == "failed-after-check-hands-off"), None)
if c is None: errs.append("case failed-after-check-hands-off missing")
else:
    for k in ("prompt", "expected_output", "files", "assertions"):
        if k not in c: errs.append(f"case lacks {k}")
    if len(c.get("assertions", [])) != 7: errs.append(f"{len(c.get('assertions', []))} assertions != 7")
    joined = " ".join(c.get("assertions", []))
    for must in ("try again", "saved", "reported by the operator", "own numbered", "repro"):
        if must not in joined: errs.append(f"assertions never mention: {must}")
print("\n".join(errs)); sys.exit(1 if errs else 0)
```

- [ ] **Step 2: Run it to verify it fails**

Run: `python3 "$SCRATCH/check_task4.py"`
Expected: `ids [0, 1, 2] != [0,1,2,3]` and `case failed-after-check-hands-off missing`, exit 1.

- [ ] **Step 3: Append the case**

In `evals.json`, after the closing `}` of the `id: 2` object (currently line 53), add a comma and this object, so the array becomes four entries:

```json
    {
      "id": 3,
      "name": "failed-after-check-hands-off",
      "prompt": "ok i did step 2 in the RDS console - changed log_min_duration_statement to 500 in the parameter group and hit save. you said to tell you and you'd measure it. here's what your check gives me now:\n\nSELECT setting FROM pg_settings WHERE name='log_min_duration_statement';\n setting\n---------\n -1\n(1 row)\n\nso it's still -1. what do i do, just do it again?",
      "expected_output": "Does NOT say try again. Opens with a Freeze line carrying the numbers (expected 500, got -1) and the do-not-redo prohibition with its reason, then enters debug-mantra with the before/after readings as the repro, names the saved-but-not-applied gap (parameter group pending-reboot / apply) as the first hypothesis to disprove by reading the pending state, and - once the cause is confirmed - returns a corrected step in the fixed shape with the apply/reboot as its own numbered line, asserted against -1 as the new baseline, and records the cause and timestamps for the ticket.",
      "files": [],
      "assertions": [
        "The first thing the user reads states expected 500 vs measured -1 AND tells them not to redo the step or change anything in the console, giving the reason (a redo destroys the state that distinguishes not-saved from not-applied from wrong-object)",
        "Nowhere tells the user to try again or repeat the unchanged step",
        "Names the saved-but-not-applied gap (RDS parameter group pending-reboot / apply status) as the FIRST hypothesis to check, before any other cause such as wrong parameter group or wrong instance",
        "Does not ask the user for a reproduction or for what environment they are in; treats the earlier baseline and this -1 reading as the repro",
        "When it gives the corrected step, the apply/reboot action is its own numbered line, not a clause inside another line, and the step names -1 as the baseline it is asserted against",
        "Records, or says it will record, the cause and both timestamps (when the step failed, when the corrected step landed) on the ticket rather than only saying done",
        "If it cannot read the database itself and relies on the user's pasted output, it labels that reading as reported by the operator, not independently measured, rather than calling it verified"
      ]
    }
```

- [ ] **Step 4: Run the check to verify it passes**

Run: `python3 "$SCRATCH/check_task4.py"`
Expected: empty line, exit 0.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/skills/guide-and-verify/evals/evals.json
git commit -m "test(guide-and-verify): eval case — a failed after-check hands off, never 'try again' (ADRs 0214-0220)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 5: Regenerate the `skills/` tree

**Files:**
- Regenerate: `skills/guide-and-verify/SKILL.md`, `skills/guide-and-verify/evals/evals.json` (and whatever else the generator touches — never by hand)

**Interfaces:**
- Consumes: Task 1's SKILL.md and Task 4's evals.json.
- Produces: a `skills/` tree that `check_skills_tree.py` accepts (exit 0).

- [ ] **Step 1: Run the gate to verify it fails**

Run: `python3 scripts/check_skills_tree.py; echo "exit=$?"`
Expected: findings naming `skills/guide-and-verify/…` as differing from the plugin source; `exit=1`.

- [ ] **Step 2: Regenerate**

Run: `python3 scripts/generate_skills_tree.py`
Expected: the generator reports the skills it wrote; no traceback.

- [ ] **Step 3: Run the gate to verify it passes**

Run: `python3 scripts/check_skills_tree.py; echo "exit=$?"`
Expected: `exit=0`.

- [ ] **Step 4: Confirm the change set is only what Tasks 1 and 4 produced**

Run: `git status --short skills/ && git diff --stat skills/`
Expected: only files under `skills/guide-and-verify/` changed; the SKILL.md diff is the Task 1 block, the evals diff is the Task 4 case. If any other skill directory changed, stop and report — that means the generator was stale before this branch, and it must be committed separately with its own message.

- [ ] **Step 5: Commit**

```bash
git add skills/
git commit -m "chore(skills): regenerate skills/ after the guide-and-verify failed-check handoff

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>"
```

---

### Task 6: Pre-merge verification (no edits)

**Files:** none modified.

**Interfaces:**
- Consumes: everything above.
- Produces: a go/no-go report for the owner's merge.

- [ ] **Step 1: Re-verify the ADR numbers against the global max (CLAUDE.md / ADR 0056)**

Run the bash scan from `plugins/dev-workflows/skills/grill-then-plan/ADR-FORMAT.md` § Numbering (the one starting `cd "$(git rev-parse --show-toplevel)" && d=docs/adr`). Do **not** use any sed-based helper script — it is GNU-only and prints an empty number on macOS.
Expected: `next: workflow-daily-work-0221`. If it prints anything lower than 0221, a parallel branch minted a colliding number: stop and report which of 0214–0220 collides.

- [ ] **Step 2: Every task's check still passes**

Run:
```bash
sh "$SCRATCH/check_task1.sh" && sh "$SCRATCH/check_task2.sh" && python3 "$SCRATCH/check_task3.py" && python3 "$SCRATCH/check_task4.py" && python3 scripts/check_skills_tree.py && echo ALL-GREEN
```
Expected: `ALL-GREEN`.

- [ ] **Step 3: debug-mantra untouched, vendored set untouched**

Run: `git diff --stat main..HEAD -- plugins/dev-workflows/skills/debug-mantra skills/debug-mantra skills/sp-* skills/scrutinize; echo "exit=$?"`
Expected: no output before `exit=0`.

- [ ] **Step 4: Branch summary for the owner**

Run: `git log --oneline main..HEAD`
Expected: six commits, in this order (newest first): regenerate skills/, eval case, version bump, playbook, feat(guide-and-verify), docs ADRs+spec+plan.

Report to the owner: the branch name, the six commits, the `next: …0221` line from Step 1, and that the merge into `main` is theirs (`finishing-a-development-branch` is not installed).
