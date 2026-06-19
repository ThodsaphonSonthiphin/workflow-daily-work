# Design Spec — `/daily` cross-session work-state file (daily-state.md)

**Date:** 2026-06-19
**Status:** Draft — awaiting approval
**Topic:** Give `/daily` a persistent, resumable work-state file that both a human and another agent/session can read, so returning to `/daily` suggests the next concrete step
**ADRs:** 0014 (new — see below). Builds on [0004](../../adr/0004-daily-router-hybrid-interaction.md) (hybrid router).

---

## Goal

Today `/daily` is a **stateless router**: it asks ≤2 questions and hands off. When the
user leaves and comes back (new session, lost context), `/daily start` shows the ADO
board — which has no idea the user was *mid-debug on #6125, cause confirmed, next step
grill-then-plan*.

Ship a **single per-project state file** — markdown with a YAML frontmatter contract —
that captures the user's current position in the daily circle plus the explicit next
step, written when the user pauses or wraps, and read back when they return so `/daily`
narrates *"welcome back, here's where you were, here's what to do next."*

The file has **two readers by design**: a **human** (reads/edits the markdown body) and
**another AI/agent session** (parses the typed frontmatter deterministically to resume
or hand off context). The frontmatter is therefore a documented **data contract**, in
keeping with this repo's data-contract-first philosophy.

## Non-goals (explicitly cut — YAGNI)

These were considered during brainstorming and deliberately removed:

- **Multi-person / team board.** No per-person sections, no identity resolution, no
  shared standup board. The consumer is the user's own future session/agent, not
  teammates. (Can be revisited later — see Follow-ups.)
- **Auto-commit / auto-push.** The skill never commits on its own. Committing is
  *offered* (see Commit behavior) and often unnecessary, since the resuming session is
  usually the same working tree.
- **Stop-hook auto-capture.** No background hook writes the file. Writes happen only on
  explicit `/daily save` and `/daily wrap`. Predictable, user-controlled.
- **Replacing auto-memory.** The existing `.claude/.../memory/` files keep their role.
  This file is separate and complementary (see Relationship to auto-memory).
- **Multiple simultaneous in-flight tasks.** v1 tracks a single active focus. Juggling N
  tasks is a follow-up.
- **"Smart" next-step re-derivation.** The skill does not infer the next step from the
  conversation. It replays the `next` the user/agent captured while context was fresh —
  the correct pattern for hand-off.

---

## The contract — `daily-state.md`

One file per project. YAML frontmatter is the machine contract; the body is for humans.

```markdown
---
type: daily-state
schema_version: 1
updated: 2026-06-19T17:40:00+07:00   # ISO-8601, set on every write
station: work                         # start | work | file | report | wrap (circle position)
status: in-progress                   # in-progress | blocked | paused | done
focus:
  ticket: "6125"                      # optional
  topic: cargo-group status
next:
  action: grill-then-plan             # what the resuming agent/human should do next
  reason: fix has a design choice
chain:                                # optional — where in the work chain
  - debug-mantra: done (cause confirmed — POL null)
blockers: []                          # optional list of strings
---

# Daily state — <project>

## What I was doing
<human prose: files touched, decisions made, links to [[memory]] pages / ADO items>

## Next
<human elaboration of next.action>
```

### Field contract

| Field | Type | Required | Meaning |
|---|---|---|---|
| `type` | `"daily-state"` | yes | Identifies the contract to any consumer |
| `schema_version` | int | yes | Currently `1`; bump on breaking schema change |
| `updated` | ISO-8601 datetime | yes | Set to now on every write; a consumer uses it to judge staleness |
| `station` | enum | yes | Circle position: `start`/`work`/`file`/`report`/`wrap` |
| `status` | enum | yes | `in-progress`/`blocked`/`paused`/`done` |
| `focus.ticket` | string | no | Ticket/issue id, if any |
| `focus.topic` | string | yes | One-line description of the active work |
| `next.action` | string | yes | The next concrete step (skill name or free text) |
| `next.reason` | string | no | Why that's next |
| `chain` | list | no | Breadcrumbs of completed work-chain steps |
| `blockers` | list of strings | no | What's blocking, if `status: blocked` |

The canonical schema lives in `plugins/dev-workflows/references/daily-state-contract.md`
(new) — the single source of truth — so *any* agent or script can parse the file, not
just this skill.

## File location & discovery (generic, per-project)

- Resolved at **runtime**, never hardcoded: the file is `daily-state.md` at the **current
  git repository root** (`git rev-parse --show-toplevel`). Each project gets its own
  resume-point; the next agent working in that project finds it at a stable relative path.
- Override order: `--path <file>` flag → `DAILY_STATE_FILE` env var → git-root default.
- If the cwd is **not** inside a git repo, the skill asks the user where to put it (or
  uses cwd) rather than failing.
- Root-level (not a dotfolder) so the human reader sees it and Obsidian indexes it.

## Helper script — `scripts/daily-state.py`

Deterministic frontmatter read/write belongs in a script (a shared, machine-read contract
must not be corrupted by freehand edits), matching the repo's `read_source.py` /
`tracking.py` pattern. **Git stays in the skill** (gated, visible) — the script never runs
git. The script is the only thing that touches the YAML.

CLI (the script's interface contract):

| Command | Does |
|---|---|
| `show [--path P] [--json]` | Read current state. Default = human summary; `--json` = machine blob for an agent. If no file exists, prints `no state yet`. |
| `set [--station S] [--status S] [--ticket T] [--topic TXT] [--next-action A] [--next-reason R] [--blocker TXT ...] [--note TXT] [--path P]` | Upsert frontmatter (unset fields preserved), set `updated`=now, optionally append `--note` to the body. Creates the file (with header) if missing. |
| `resolve-path [--path P]` | Print the resolved file path (git-root discovery) — lets the skill show the user where it'll write. |

- Dependency: **PyYAML** for robust frontmatter parse/emit. Add to prerequisites and to
  `setup_check.ps1`'s checks.
- Timestamp: the script stamps `updated` itself (`datetime.now(timezone)`).

## `/daily` integration

The router gains a thin state layer at three touchpoints; it still hands off the actual
station work.

**Read — bare `/daily` and `/daily start`:**
Before the menu / before `ado-backlog:my-work`, call `daily-state.py show`. If state
exists, print a one-line **welcome-back**:
> *Last session (2h ago): 🔧 WORK on #6125 — cause confirmed. Suggested next → grill-then-plan.*
Then continue to the normal menu / START handoff. If no state exists, skip silently.

**Write — new `/daily save "<note>"` action** (synonyms `pause`, `checkpoint`):
Not a numbered station — a lightweight accelerator. Calls `daily-state.py set` to update
`station`/`focus`/`next`/`status` and append the note, then **offers** to commit.
Surfaced via a one-line footer under the menu: *"💾 Save state anytime: /daily save"* —
keeping the 5-station circle (ADR 0004) intact.

**Write — `/daily wrap`:**
After `invoice-generator` runs, prompt to write the end-of-day snapshot via
`daily-state.py set` (station, focus, next, status), then **offer** to commit.

**Argument parsing:** add `save`/`pause`/`checkpoint` to the station-word table. It routes
to the save flow, not a station. Unknown args still fall back to the menu (ADR 0004).

## Commit behavior (assisted, never automatic)

After any write, the skill writes the file then **explicitly offers**: *"Commit & push so
the next session/machine sees it? (y/n)"*. On yes, it stages **only** `daily-state.md`,
commits, and pushes. Rationale: a router silently committing is risky (this very workspace
has two sub-repos and a non-repo root, and the project rule forbids root-level commits).
For a same-machine resume, committing is usually unnecessary — the file is already on disk.

## Relationship to auto-memory (separate & complementary)

- **`daily-state.md`** = the immediate, in-repo, version-controllable **"resume HERE"**
  pointer for the *current project* — one active focus, optimized for "what do I do next."
- **Auto-memory** (`.claude/.../memory/`) = Claude's broader, longer-lived, harness-private
  facts and per-task history that outlive a single resume.
- They have different scopes and storage, so they don't compete. The `daily-state.md` body
  may `[[link]]` to relevant memory pages. `/daily` reads/writes only `daily-state.md`.

## Repo conventions to satisfy

1. **ADR 0014** — *"`/daily` gains a cross-session work-state file."* Records: the router
   stops being purely stateless; md+frontmatter contract; per-project runtime discovery;
   assisted (not auto) commit; helper script owns YAML, skill owns git; separate from
   auto-memory. Alternatives rejected: JSON-only (human-hostile), strict-schema-markdown
   (fragile machine contract), team board (no real team), auto-commit, Stop-hook capture.
2. **`plugins/dev-workflows/references/daily-state-contract.md`** — canonical schema doc.
3. **PLAYBOOK.md** — one row/note documenting `/daily save` and the resume behavior.
4. **`plugins/dev-workflows/skills/daily/SKILL.md`** — add the read/write touchpoints, the
   `save` action, the argument-table row, and the menu footer line.
5. **`setup_check.ps1`** — verify Python + PyYAML.
6. **Version bump in sync** — `plugins/dev-workflows/.claude-plugin/plugin.json` and the
   matching `.claude-plugin/marketplace.json` entry.

---

## Acceptance checks

1. `daily-state.py set --station work --topic "x" --next-action grill-then-plan` creates
   `daily-state.md` at the git root with valid frontmatter and the updated timestamp.
2. `daily-state.py show --json` emits a parseable blob with all required fields; `show`
   (no flag) prints a human summary; both print `no state yet` when the file is absent.
3. A second `set` updates only the passed fields and preserves the rest (read-modify-write).
4. Bare `/daily` and `/daily start` print the welcome-back line when state exists and skip
   silently when it doesn't.
5. `/daily save "note"` writes/updates the file and then *offers* commit (does not commit
   unprompted); declining leaves the file uncommitted on disk.
6. Outside a git repo, the skill asks for a location instead of erroring.
7. `references/daily-state-contract.md` documents every field in the example.
8. dev-workflows version is identical in plugin.json and marketplace.json.
9. PyYAML missing → `setup_check.ps1` reports it (WARN, matching the openpyxl
   convention — non-blocking, since the check lives in the ado-backlog plugin).

## Follow-ups (out of scope)

- **Multiple in-flight tasks** — a list of foci instead of one, with `/daily resume` to pick.
- **Station-hop auto-capture** — optionally update `station` on every `/daily <station>`
  jump (the "live board" trigger we rejected for v1's predictability).
- **Team sharing** — promote the file to a shared location with per-author entries if a
  real team materializes (the apparatus cut in Non-goals).
- **ADO/GitHub sync** — feed `focus.ticket` + `status` to/from the tracker.
