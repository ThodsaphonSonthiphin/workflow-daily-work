---
name: generating-test-cases
description: Use when you need to produce a test-case suite for a feature, change, PR, or fixed bug — manual or automated — for delivery to Excel/xlsx, Markdown, CSV, or a tracker. Triggers on "write test cases", "create a test plan", "QA cases", "turn this spec/diff/bug into tests", or after a feature is built / a bug is fixed and before filing or sign-off. Every case is grounded in real evidence (docs, code, git, or the LIVE system); the skill refuses to invent values. Do NOT use to verify one already-finished task (that is dual-verifier), or to file findings as work items (that is the backlog plugins — this hands off to them).
---

# Generating Test Cases

Turn a feature, change, or fixed bug into a structured, **evidence-grounded** test-case suite, then render it to whatever destination the user wants. Coverage is derived once from the sources of truth; the output format is a late, swappable step.

The whole skill rests on one discipline you must not skip:

> **🔒 Iron Law — No test case, no expected value, no test datum without a cited source.**
> Every row points to where it came from: a doc, source code (`file:line`), git, or the **live system**. If a value can't be found in a real source, you do **not** write it — you mark it `TBD (needs confirmation)` and ask. Guessing is a defect, not a shortcut.

**Violating the letter of this rule is violating its spirit.** A plausible-but-unsourced expected value is worse than a blank one: it looks verified and isn't.

## When to invoke

- "Write test cases / a test plan / QA cases for this feature/PR/change"
- After implementation finishes (hand-off from grill-then-plan → build) or a bug is fixed (hand-off from `post-mortem` → regression case)
- Before filing findings or release sign-off
- NOT for verifying one finished task → `dual-verifier`; NOT for filing tickets → `findings-to-ado-backlog` / `ado-create-work-items` (this skill *hands off* to them)

## Steps

**0. Scope + mode.** Testing a *change/PR* or a *whole feature/system*? Identify the live system that's involved (runnable app / DB / CRM / API).

**1. Gather sources of truth** — read-only; save evidence to disk.
- **docs** (spec, ADRs, README) · **code** (real defaults, behavior, field names)
- **git** — *easily skipped, do it explicitly:*
  - `git diff <base>..HEAD` → the real change surface (scope) — change/PR mode
  - `git log -- <touched paths>` → past fixes in this area → **regression cases**
  - `git blame` on risky lines → *why* it exists → ties a case to a reason
  - trailers / `#1234` / branch name → Evidence refs
  - deep "why does this exist?" → delegate to `ticket-trace`

**2. ▶ Pull REAL values from the LIVE system** — read-only, never mutate it.
Source code gives shape; the live system gives the values that exist nowhere else: actual device/monitor names, real option-set/enum values, true defaults, real schema, whether an error path actually reproduces. Run the app / query the DB·CRM·API and capture the output as Evidence. *git = history + intent + change-surface; live = the real values now.* This is the step agents skip by default — do not.

**3. Canonical schema** (format-independent — decide once, before any output choice):
`ID · Area · Title · Type(Auto/Manual) · Priority · Auto-test-link · Preconditions · Steps · Test Data · Expected Result · Evidence(required) · Status · Tester · Date · Notes`

**4. Derive cases — coverage dimensions + two-way traceability.**
Walk every dimension so none is missed: happy · config/validation · integration · **negative/failure/fallback/edge** · UI/DPI · packaging.
- Forward: every requirement / ADR / diff-hunk → ≥1 case. Backward: every case → real Evidence (blank Evidence = not done).
- Every fix-commit in the touched area → one regression case.
- Mark Auto/Manual, map automated cases to the real test method, assign Priority, flag **hard gates** (must-pass before sign-off).

**5. Make each case executable.** Numbered Steps; Expected = a **verifiable value from a real source** (`2026-06-18_14-03-22_screen.mp4`, `Total = 500,000 (NOT 0)`), never "works correctly". Can't source it → `TBD (needs confirmation)`, then ask.

**6. ▶ ASK the user the destination — before rendering.** Do not assume a format.
```
Output to?  1) Excel (.xlsx)  2) Markdown  3) CSV  4) Tracker (ADO / Jira / GitHub / Notion)
Also: priority scheme? · include Tester/Date columns? · map automated cases to tests?
```

**7. Render via a format adapter** (same canonical model → chosen target):
- **xlsx** → `scripts/render_xlsx.py` (Status dropdown, conditional color, freeze, auto-filter, Cases + Legend + Test Data + Summary sheets)
- **md** → grouped tables + summary · **csv** → flat rows
- **tracker** → **delegate** to `findings-to-ado-backlog` / `ado-create-work-items` (they own dry-run + safety gate + writeback). Do not re-implement ticket creation here.

**8. Self-review gates** (all must pass before delivery):
- Evidence present on **every** row; no `TBD` left unflagged; no "probably/assume/typically" in Steps/Expected/Test Data
- Coverage: every requirement/ADR/diff-hunk/risk has a case; negative cases present; every P1 has an unambiguous pass/fail
- Every fix-commit in the area has a regression case
- Encoding check **by codepoint**, not by console rendering (avoids false "mojibake")

**9. Deliver + chain.** Report counts (total / auto / manual / P1 / hard-gates) + path. Then: failed/`TBD` cases → `findings-to-ado-backlog` (FILE); summary → `management-talk` (REPORT).

## Rationalization table

| Excuse | Reality |
|---|---|
| "This value is probably ~X" | "Probably" = a guess. Read it / run it / query it. |
| "It's obvious from general behavior" | General ≠ this system. Cite this system's source. |
| "No time to run the live app — use a sample value" | A guessed sample = a test you can't trust. Pull the real value or mark TBD + ask. |
| "Docs are old, I'll infer from the function name" | Docs vs code → code/live wins. Read the real thing. |
| "The task said decide the format myself" | Decide *structure* yourself; the *destination* is the user's call — ask (Step 6). |
| "git is overkill for tests" | git diff scopes the change; git log finds the regressions you'd otherwise miss. |

## Red flags — STOP and go find the source

- "probably / expected / typically / normally / assume / should be" in Steps, Expected, or Test Data
- An Expected Result with no Evidence cell filled
- Picked a format without asking the user
- Wrote device names / defaults / enum values without running or querying the live system

## Common mistakes

- **Happy-path-only** → Step 4's dimensions + backward-trace from git regressions force the failure cases.
- **Vague "works correctly"** → Step 5 demands an exact verifiable value.
- **Assuming xlsx** → Step 6 asks first; the canonical model (Steps 1–5) is format-blind so re-rendering to a second format is free.
- **Re-implementing ADO/Jira creation** → delegate to the backlog plugins.
- **Skipping the live system** → the single most common gap; the real values live there.

## Chain position

Sits on the **WORK → FILE** hinge. In: `grill-then-plan`→build, `post-mortem`→regression case, alongside `dual-verifier`/`scrutinize`. Out: `findings-to-ado-backlog`/`ado-create-work-items` (FILE), `management-talk` (REPORT).
