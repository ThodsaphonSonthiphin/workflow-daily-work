# Cross-Project Gotchas (reflect Route F) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cross-project "gotcha" capability to the dev-workflows `reflect` skill — a new Route F that files reusable tooling/environment traps into `~/.claude/GOTCHAS.md`, auto-loaded in every project via an `@` import in the global `~/.claude/CLAUDE.md`.

**Architecture:** Pure documentation/config change. Edit one SKILL.md (add Route F to the routing table, ownership guardrail, Stage-4 apply block, Stage-5 record note, and the frontmatter description) and bump the owning plugin's version in its two manifests. No runtime code, no `~/.claude` files are created by this plan — those are provisioned by reflect at runtime when a real Route-F finding occurs. Decisions are frozen in ADRs 0028–0031; source of truth for the design is `docs/superpowers/specs/2026-07-12-reflect-cross-project-gotchas-design.md`.

**Tech Stack:** Markdown (SKILL.md), JSON (plugin.json / marketplace.json), PowerShell/Bash for edits, git.

## Global Constraints

- **Write/Edit tools are BLOCKED in this repo** by the mobile-app write-guard hook. Apply every repo edit with PowerShell (read `-Raw` → `.Replace(old,new)` → write back UTF-8) or Bash. Try the Edit tool first; on a hook block, fall back to shell.
- **Version lockstep:** dev-workflows goes **0.24.0 → 0.25.0** in BOTH `plugins/dev-workflows/.claude-plugin/plugin.json` AND its entry in `.claude-plugin/marketplace.json` — the two MUST stay identical (CLAUDE.md convention).
- **GOTCHAS.md is diagram-exempt** (ADR 0030): the Stage-4 instructions must tell reflect to keep it terse, one line per gotcha, NO Mermaid diagram (unlike normal document-skill output).
- **The `@` import line must be written PLAIN** — never inside backticks / a code fence — or Claude Code treats it as literal and never imports it (verified against Claude Code docs).
- **F-vs-D boundary test, verbatim:** *"if I did this in another project, would this same thing bite me?"* — keep this wording identical everywhere it appears.
- **reflect is an existing skill** → no new PLAYBOOK.md row (the maintenance rule fires for new skills only).
- **After merge, the change loads only after a cache resync + Claude Code restart** (skills-deploy-mechanism memory).

---

### Task 1: Add Route F to `reflect/SKILL.md`

**Files:**
- Modify: `plugins/dev-workflows/skills/reflect/SKILL.md`

**Interfaces:**
- Consumes: nothing.
- Produces: the Route F contract used by Tasks 2–3 — Route letter `F`, destination `~/.claude/GOTCHAS.md`, the `@~/.claude/GOTCHAS.md` import line, and the `[Route F · GOTCHAS.md] <title>` reflections tag.

All five edits below are literal find/replace on unique anchor strings (each anchor occurs exactly once in the file). Keep surrounding text byte-identical.

- [ ] **Step 1: Edit the frontmatter description** — extend the route list so the skill's own trigger blurb stays accurate.

Find (anchor):
~~~
where it will fire again: an owned skill, a project CLAUDE.md, or memory.
~~~
Replace with:
~~~
where it will fire again: an owned skill, a project CLAUDE.md, a cross-project
GOTCHAS.md file, or memory.
~~~

- [ ] **Step 2: Sharpen Route C and D "When" cells** (Stage 2 routing table) so the boundary against F is clean.

Find `| C | Project CLAUDE.md | Project-specific convention or gotcha. |` → replace with:
~~~
| C | Project CLAUDE.md | This project's own convention or architecture (this repo only). |
~~~
Find `| D | Auto-memory | Preference or single-project fact. |` → replace with:
~~~
| D | Auto-memory | Personal preference or a single-project fact. |
~~~

- [ ] **Step 3: Add the Route F row + the boundary test** to the Stage 2 table.

Find (anchor): `| E | Discard | One-off noise. |`
Replace with (the E row unchanged, then the F row, then the boundary paragraph):
~~~
| E | Discard | One-off noise. |
| F | Global gotcha (`~/.claude/GOTCHAS.md`) | A cross-project tooling / environment / harness trap. |

**F vs C vs D — one-line test.** Ask *"if I did this in another project, would
this same thing bite me?"* **Yes → F** — it fires everywhere via the
`@`-imported `~/.claude/GOTCHAS.md`. **No, it's this repo's own rule → C.** **A
preference or one-project fact → D.** Route F explicitly reclaims the
cross-project tooling/environment lessons that used to default to D (D's store
is keyed by project directory, so they never surfaced in other projects).
~~~

- [ ] **Step 4: Add the Route F ownership note** after the ownership guardrail.

Find (anchor): `memory or a Route C CLAUDE.md override instead.`
Replace with:
~~~
memory or a Route C CLAUDE.md override instead.

**Route F writes global config.** Route F targets the user's global Claude
config — `~/.claude/GOTCHAS.md` plus one `@~/.claude/GOTCHAS.md` import line in
`~/.claude/CLAUDE.md`. The user owns these, so writing is allowed, but the edit
to the personal `CLAUDE.md` is **announced before it happens** (see Stage 4) —
the same transparency Route D memory writes get.
~~~

- [ ] **Step 5: Add the Route F apply block** in Stage 4.

Find (anchor): `- **Route E:** nothing.`
Replace with the E line unchanged, then the Route F block:
~~~
- **Route E:** nothing.
- **Route F (global gotcha -> `~/.claude/GOTCHAS.md`):** the destination is a
  standalone, cross-project file that Claude Code auto-loads in every session
  via an `@` import in the global `~/.claude/CLAUDE.md`. Provision it lazily and
  idempotently:
    1. **Ensure the file.** If `~/.claude/GOTCHAS.md` is missing, create it with
       a short header (title + one line: auto-loaded everywhere via `@` in
       ~/.claude/CLAUDE.md, one gotcha = one line, grouped by area, update in
       place). If it exists, never clobber it.
    2. **Append or update — one line per gotcha.** Under the matching `##` area
       heading (create one lazily if none fits), write
       `- **<short title>** — <fix / workaround>. (YYYY-MM-DD)`. Before adding,
       search for the bold `<short title>`; if present, UPDATE that line in
       place (refine + re-date) instead of duplicating. Never auto-delete; the
       date supports manual review. Keep it terse — this file loads on every
       turn, so **no Mermaid diagram** (convention-exempt like MEMORY.md, ADR
       0030). Any literal `@path` written INTO this file must be backticked, or
       it would itself be re-imported.
    3. **Ensure the import (first time only, announced).** If `~/.claude/CLAUDE.md`
       has no bare `@~/.claude/GOTCHAS.md` line, first TELL the user: "adding one
       `@import` line to your global CLAUDE.md so gotchas auto-load in every
       project — Claude Code will ask you to approve the import on next start,
       please approve it." Then append the line at end of file, written **plain**
       (never inside backticks / a code fence, or it will not import).
~~~

- [ ] **Step 6: Note the Route F tag in Stage 5.**

Find (anchor): `project, findings (one line each), applied vs skipped, cited sources.`
Replace with:
~~~
project, findings (one line each — tag the route, e.g.
`[Route F · GOTCHAS.md] <title>` for a global gotcha), applied vs skipped, cited
sources.
~~~

- [ ] **Step 7: Verify all edits landed and no anchor was missed.**

Run:
```
powershell -Command "$p='plugins/dev-workflows/skills/reflect/SKILL.md'; @('cross-project.*GOTCHAS','Route F','one-line test','Route F writes global config','Route F \(global gotcha','\[Route F . GOTCHAS.md\]') | %% { $h=Select-String -Path $p -Pattern $_ -Quiet; \"$_ => $h\" }"
```
Expected: every pattern prints `=> True`. Also open the file and eyeball the Stage 2 table (6 rows A–F) and the Stage 4 list (A–F present, Note paragraph intact below F).

- [ ] **Step 8: Commit.**

```
git add "plugins/dev-workflows/skills/reflect/SKILL.md"
git commit -m "feat(reflect): add Route F — cross-project gotchas in ~/.claude/GOTCHAS.md (ADR 0028-0031)"
```

---

### Task 2: Bump dev-workflows to 0.25.0 and refresh the description blurbs

**Files:**
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: the Route F contract from Task 1 (only referenced in prose).
- Produces: version 0.25.0 reported identically in both manifests.

- [ ] **Step 1: Bump the version in plugin.json.**

In `plugins/dev-workflows/.claude-plugin/plugin.json`, replace `"version": "0.24.0"` with `"version": "0.25.0"` (this string occurs once in that file).

- [ ] **Step 2: Bump the dev-workflows version in marketplace.json.**

In `.claude-plugin/marketplace.json`, replace `"version": "0.24.0"` with `"version": "0.25.0"` (0.24.0 is unique to the dev-workflows entry; do NOT touch the marketplace top-level `0.3.0` or ado-backlog `0.2.0`).

- [ ] **Step 3: Refresh the Reflection clause in BOTH manifests** so the description advertises the gotcha route. The identical clause appears in each file's dev-workflows description.

Find (anchor, both files): `an owned skill, a CLAUDE.md, or memory — closing the daily arc`
Replace with:
~~~
an owned skill, a CLAUDE.md, a cross-project GOTCHAS.md, or memory — closing the daily arc
~~~

- [ ] **Step 4: Verify both manifests are valid JSON and report 0.25.0.**

Run:
```
powershell -Command "$a=(Get-Content 'plugins/dev-workflows/.claude-plugin/plugin.json' -Raw|ConvertFrom-Json).version; $m=((Get-Content '.claude-plugin/marketplace.json' -Raw|ConvertFrom-Json).plugins|?{$_.name -eq 'dev-workflows'}).version; \"plugin.json=$a marketplace=$m match=$($a -eq $m -and $a -eq '0.25.0')\""
```
Expected: `plugin.json=0.25.0 marketplace=0.25.0 match=True`. (ConvertFrom-Json throwing = invalid JSON; fix the edit.)

- [ ] **Step 5: Commit.**

```
git add "plugins/dev-workflows/.claude-plugin/plugin.json" ".claude-plugin/marketplace.json"
git commit -m "chore(dev-workflows): 0.24.0 -> 0.25.0 (Route F cross-project gotchas)"
```

---

### Task 3: Deploy — resync the plugin cache and restart

**Files:** none (operates on the installed plugin cache under `~/.claude/plugins/`).

**Interfaces:**
- Consumes: the committed edits from Tasks 1–2.
- Produces: the running Claude Code loading reflect 0.25.0.

Per the `skills-deploy-mechanism` memory, dev-workflows runs from a versioned cache, not `~/.claude/skills`. Two options — pick one:

- [ ] **Step 1 (recommended, immediate): hot-patch the current cache.** Copy the edited files over the live cache dir so the change takes effect on next restart without a full reinstall.

```
powershell -Command "$d=Get-ChildItem '~/.claude/plugins/cache/workflow-daily-work/dev-workflows' -Directory | Sort-Object Name -Descending | Select-Object -First 1; Write-Host $d.FullName; Copy-Item 'plugins/dev-workflows/skills/reflect/SKILL.md' (Join-Path $d.FullName 'skills/reflect/SKILL.md') -Force; Copy-Item 'plugins/dev-workflows/.claude-plugin/plugin.json' (Join-Path $d.FullName '.claude-plugin/plugin.json') -Force"
```
Expected: prints the cache dir path and copies without error. (If the path differs on this machine, discover it with `Get-ChildItem ~/.claude/plugins/cache -Recurse -Filter plugin.json | Select-String dev-workflows`.)

- [ ] **Step 1 (alternative, clean): reinstall via the plugin manager.** Because the version changed, run `/plugin update` (or reinstall dev-workflows) in an interactive Claude Code session to pull 0.25.0 cleanly.

- [ ] **Step 2: Restart Claude Code.** The edit does not load in the current session. TELL the user to restart (the agent cannot restart the session). After restart, `/reflect` reflects the new Route F.

- [ ] **Step 3 (smoke check, after restart):** run `/reflect` on a trivial session and confirm the routing table now lists Route F. No file is written unless a real cross-project gotcha is found and approved.

---

## Notes / Out of scope

- **No `~/.claude/GOTCHAS.md` is created by this plan.** It is provisioned by reflect at runtime (Stage 4) on the first approved Route-F finding.
- **Migrating existing Route-D memories** that are really cross-project gotchas is out of scope — reflect routes future ones to F; a manual promotion sweep can follow.
- **ADRs 0028–0031 and the design spec already exist** (written during the grill-then-plan session); no task recreates them.
- **Marketplace top-level version (`0.3.0`)** is intentionally left unchanged — the convention ties plugin.json to its marketplace entry, not the marketplace root.

## Self-review

- **Spec coverage:** §1 destination/mechanism → Task 1 Steps 4–5 + Global Constraints; §2 Route F + test → Task 1 Steps 2–3; §3 format/diagram-exempt → Task 1 Step 5.2 + Constraints; §4 provisioning/transparency/plain-@ → Task 1 Step 5.3 + Constraints; §5 growth (update-beats-create/no-delete) → Task 1 Step 5.2; §6 reflections coexistence → Task 1 Step 6; versioning/deploy → Tasks 2–3; out-of-scope → Notes. No gaps.
- **Placeholder scan:** `<short title>` / `<title>` / `YYYY-MM-DD` are deliberate templates inside skill instructions, not plan placeholders. No "TBD/handle edge cases/etc.".
- **Consistency:** Route letter `F`, path `~/.claude/GOTCHAS.md`, import line `@~/.claude/GOTCHAS.md`, tag `[Route F · GOTCHAS.md] <title>`, and the boundary test wording are identical across all tasks and match the spec/ADRs.
