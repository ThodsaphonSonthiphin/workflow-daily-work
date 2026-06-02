# grill-then-plan Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a `grill-then-plan` skill that runs a domain-aware, one-question-at-a-time grilling session (updating CONTEXT.md + ADRs inline), then hands off to `superpowers:writing-plans` — after a preflight check that superpowers is installed.

**Architecture:** A single owned `SKILL.md` describes the pipeline (preflight → explore → grill → capture inline → spec → handoff). Two format files are vendored (copied verbatim) from the existing `grill-with-docs` skill so they are frozen. superpowers is delegated by name, never copied.

**Tech Stack:** Claude Code skill format (Markdown + YAML frontmatter). No build, no test runner. "Tests" are concrete verification commands (file existence, content greps, diffs against source). No git in the target dir, so commit steps are replaced by verification checkpoints.

---

## File Structure

All files live in the user's own skills directory so they survive plugin updates:

- Create: `~/.claude/skills/grill-then-plan/SKILL.md` — owned; the pipeline instructions (preflight, grilling, inline docs, handoff).
- Create: `~/.claude/skills/grill-then-plan/ADR-FORMAT.md` — vendored verbatim copy from `grill-with-docs`.
- Create: `~/.claude/skills/grill-then-plan/CONTEXT-FORMAT.md` — vendored verbatim copy from `grill-with-docs`.

Source files for the vendored copies (absolute, Windows):
- `C:\Users\thodsaphon.sonthipin\.claude\skills\grill-with-docs\ADR-FORMAT.md`
- `C:\Users\thodsaphon.sonthipin\.claude\skills\grill-with-docs\CONTEXT-FORMAT.md`

Target dir (absolute, Windows): `C:\Users\thodsaphon.sonthipin\.claude\skills\grill-then-plan\`

---

## Task 1: Create the skill directory

**Files:**
- Create: `~/.claude/skills/grill-then-plan/` (directory)

- [ ] **Step 1: Verify the target directory does not already exist**

Run (PowerShell):
```powershell
Test-Path "$env:USERPROFILE\.claude\skills\grill-then-plan"
```
Expected: `False` (if `True`, stop and confirm with the user before overwriting).

- [ ] **Step 2: Create the directory**

Run (PowerShell):
```powershell
New-Item -ItemType Directory -Force "$env:USERPROFILE\.claude\skills\grill-then-plan" | Out-Null
```

- [ ] **Step 3: Verify it exists**

Run (PowerShell):
```powershell
Test-Path "$env:USERPROFILE\.claude\skills\grill-then-plan"
```
Expected: `True`

---

## Task 2: Vendor ADR-FORMAT.md

**Files:**
- Create: `~/.claude/skills/grill-then-plan/ADR-FORMAT.md` (copied verbatim from grill-with-docs)

- [ ] **Step 1: Verify the source file exists**

Run (PowerShell):
```powershell
Test-Path "$env:USERPROFILE\.claude\skills\grill-with-docs\ADR-FORMAT.md"
```
Expected: `True` (if `False`, stop — the source skill is required for vendoring).

- [ ] **Step 2: Copy the file verbatim**

Run (PowerShell):
```powershell
Copy-Item "$env:USERPROFILE\.claude\skills\grill-with-docs\ADR-FORMAT.md" `
          "$env:USERPROFILE\.claude\skills\grill-then-plan\ADR-FORMAT.md" -Force
```

- [ ] **Step 3: Verify the copy is byte-identical to the source**

Run (PowerShell):
```powershell
$a = Get-FileHash "$env:USERPROFILE\.claude\skills\grill-with-docs\ADR-FORMAT.md"
$b = Get-FileHash "$env:USERPROFILE\.claude\skills\grill-then-plan\ADR-FORMAT.md"
$a.Hash -eq $b.Hash
```
Expected: `True`

---

## Task 3: Vendor CONTEXT-FORMAT.md

**Files:**
- Create: `~/.claude/skills/grill-then-plan/CONTEXT-FORMAT.md` (copied verbatim from grill-with-docs)

- [ ] **Step 1: Verify the source file exists**

Run (PowerShell):
```powershell
Test-Path "$env:USERPROFILE\.claude\skills\grill-with-docs\CONTEXT-FORMAT.md"
```
Expected: `True`

- [ ] **Step 2: Copy the file verbatim**

Run (PowerShell):
```powershell
Copy-Item "$env:USERPROFILE\.claude\skills\grill-with-docs\CONTEXT-FORMAT.md" `
          "$env:USERPROFILE\.claude\skills\grill-then-plan\CONTEXT-FORMAT.md" -Force
```

- [ ] **Step 3: Verify the copy is byte-identical to the source**

Run (PowerShell):
```powershell
$a = Get-FileHash "$env:USERPROFILE\.claude\skills\grill-with-docs\CONTEXT-FORMAT.md"
$b = Get-FileHash "$env:USERPROFILE\.claude\skills\grill-then-plan\CONTEXT-FORMAT.md"
$a.Hash -eq $b.Hash
```
Expected: `True`

---

## Task 4: Write SKILL.md

**Files:**
- Create: `~/.claude/skills/grill-then-plan/SKILL.md`

- [ ] **Step 1: Write the SKILL.md file with this exact content**

Write the following to `~/.claude/skills/grill-then-plan/SKILL.md`:

````markdown
---
name: grill-then-plan
description: Domain-aware grilling session that interrogates a plan one question at a time, sharpens terminology against the project glossary, cross-references claims against code, captures CONTEXT.md and ADRs inline, then hands off to superpowers:writing-plans. Use when the user wants to stress-test and design a feature against their project's language AND continue into the superpowers planning pipeline. Requires the superpowers plugin.
---

<what-to-do>

Run a domain-aware design session, then hand off to the superpowers planning
pipeline. Do NOT write code, scaffold, or invoke any implementation skill until
the design spec is approved and you have invoked `superpowers:writing-plans`.

</what-to-do>

## Step 0 — Preflight: ensure superpowers is installed

This skill delegates its final step to `superpowers:writing-plans`. Check that
dependency FIRST, so the user never spends a whole session only to hit a wall at
handoff.

1. **Detect** superpowers. Read `~/.claude/plugins/installed_plugins.json` and
   look for the key `superpowers@claude-plugins-official`. As a fallback, check
   for a directory matching
   `~/.claude/plugins/cache/claude-plugins-official/superpowers/*/`.
2. **If present** → continue to Step 1.
3. **If missing** → tell the user superpowers is required, then offer to install
   it:
   - If the marketplace is not already known:
     `/plugin marketplace add anthropics/claude-plugins-official`
   - `/plugin install superpowers@claude-plugins-official`
4. **Re-verify** using the detection in (1).
5. **If now present** → continue to Step 1.
6. **If still missing or the install could not complete** → STOP. Do not start
   grilling. Tell the user explicitly:

   > superpowers could not be installed; the grill-then-plan handoff to
   > `superpowers:writing-plans` can't run without it. Please install it manually
   > with `/plugin install superpowers@claude-plugins-official`, then re-run.

   Never fail silently and never start a session you cannot finish.

   Note: plugin installation may require the user to confirm in the interactive
   `/plugin` UI, so a fully silent auto-install is not guaranteed. Detect,
   attempt/guide, re-verify — and fail loudly if it does not work.

## Step 1 — Explore context

Read the codebase, recent commits, and existing docs: `CONTEXT.md` /
`CONTEXT-MAP.md` at the repo root, and `docs/adr/`. If a `CONTEXT-MAP.md` exists,
the repo has multiple contexts — infer which one the topic relates to (ask if
unclear).

## Step 2 — Grill relentlessly, one question at a time

Interview the user about every aspect of the plan until you reach shared
understanding. Walk down each branch of the design tree, resolving dependencies
between decisions one-by-one. For each question, provide your recommended answer.
Ask one question at a time and wait for feedback before continuing. If a question
can be answered by exploring the codebase, explore the codebase instead of asking.

## Step 3 — Stay domain-aware while grilling

- **Challenge against the glossary.** If a term conflicts with `CONTEXT.md`, call
  it out: "Your glossary defines X as A, but you seem to mean B — which is it?"
- **Sharpen fuzzy language.** Propose a precise canonical term for vague or
  overloaded words: "You're saying 'account' — Customer or User?"
- **Discuss concrete scenarios.** Invent edge-case scenarios that force precision
  about boundaries between concepts.
- **Cross-reference with code.** When the user states how something works, check
  the code agrees; surface any contradiction.

## Step 4 — Capture inline as decisions crystallize

- **Update CONTEXT.md inline** the moment a term resolves — don't batch. Keep it
  a glossary only; no implementation detail. Create it lazily on the first
  resolved term if it doesn't exist. Use the format in
  [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).
- **Offer ADRs sparingly** — only when all three are true: (1) hard to reverse,
  (2) surprising without context, (3) the result of a real trade-off. Create
  `docs/adr/` lazily on the first ADR. Use the format in
  [ADR-FORMAT.md](./ADR-FORMAT.md).

## Step 5 — Write the design spec

Once understanding is shared, write the design to
`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`. Run a self-review for
placeholders, internal consistency, scope, and ambiguity; fix inline. Ask the
user to review the spec and approve before proceeding.

## Step 6 — Hand off

After the user approves the spec, invoke `superpowers:writing-plans` to produce
the implementation plan. This is the terminal state — do NOT invoke any other
implementation skill.
````

- [ ] **Step 2: Verify the file exists and has the right frontmatter name**

Run (PowerShell):
```powershell
Test-Path "$env:USERPROFILE\.claude\skills\grill-then-plan\SKILL.md"
Select-String -Path "$env:USERPROFILE\.claude\skills\grill-then-plan\SKILL.md" -Pattern "^name: grill-then-plan$"
```
Expected: `True`, and one match for the `name:` line.

- [ ] **Step 3: Verify all six pipeline steps and the dependency name are present**

Run (PowerShell):
```powershell
$f = "$env:USERPROFILE\.claude\skills\grill-then-plan\SKILL.md"
@('Step 0','Step 1','Step 2','Step 3','Step 4','Step 5','Step 6',
  'superpowers:writing-plans','superpowers@claude-plugins-official',
  'CONTEXT-FORMAT.md','ADR-FORMAT.md') |
  ForEach-Object { "{0}: {1}" -f $_, [bool](Select-String -Path $f -Pattern ([regex]::Escape($_)) -Quiet) }
```
Expected: every line ends in `True`.

---

## Task 5: End-to-end verification

**Files:** (none — verification only)

- [ ] **Step 1: Confirm all three files are present**

Run (PowerShell):
```powershell
Get-ChildItem "$env:USERPROFILE\.claude\skills\grill-then-plan\" -Name
```
Expected: `ADR-FORMAT.md`, `CONTEXT-FORMAT.md`, `SKILL.md`

- [ ] **Step 2: Confirm vendored files still match source (no accidental edits)**

Run (PowerShell):
```powershell
foreach ($n in 'ADR-FORMAT.md','CONTEXT-FORMAT.md') {
  $src = Get-FileHash "$env:USERPROFILE\.claude\skills\grill-with-docs\$n"
  $dst = Get-FileHash "$env:USERPROFILE\.claude\skills\grill-then-plan\$n"
  "{0}: {1}" -f $n, ($src.Hash -eq $dst.Hash)
}
```
Expected: both lines end in `True`.

- [ ] **Step 3: Confirm the skill is discoverable by Claude Code**

Start a new Claude Code session (or reload) and confirm `grill-then-plan` appears
in the available skills list. Then invoke it on a trivial feature idea and confirm
Step 0 (preflight) runs first.
Expected: the skill is listed; invoking it begins with the superpowers preflight
check, not with grilling.

---

## Self-Review

- **Spec coverage:** Preflight dependency check (Task 4 Step 0) ✓; explore context
  ✓; one-at-a-time domain-aware grilling ✓; inline CONTEXT.md + ADRs via vendored
  formats (Tasks 2, 3) ✓; design spec ✓; handoff to `superpowers:writing-plans` ✓;
  hybrid coupling — superpowers delegated by name, formats vendored ✓; location
  `~/.claude/skills/` ✓.
- **Placeholder scan:** No TBD/TODO; SKILL.md content is given in full; copy steps
  reference exact source paths.
- **Type/name consistency:** `grill-then-plan` (dir + frontmatter `name`),
  `superpowers:writing-plans` (handoff), `superpowers@claude-plugins-official`
  (detection key), `ADR-FORMAT.md` / `CONTEXT-FORMAT.md` (vendored, referenced by
  relative path in SKILL.md) — consistent across all tasks.
