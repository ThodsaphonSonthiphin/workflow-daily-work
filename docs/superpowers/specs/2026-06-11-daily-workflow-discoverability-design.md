# Design Spec — Daily workflow discoverability (PLAYBOOK.md + /daily router + skill consolidation)

**Date:** 2026-06-11
**Status:** Draft — awaiting approval
**Topic:** Make the owner's 24+ skills discoverable and routable as a daily workflow
**ADRs:** [0001](../../adr/0001-playbook-plus-daily-router.md), [0002](../../adr/0002-repo-as-single-source-of-skills.md), [0003](../../adr/0003-conditional-debug-chain.md), [0004](../../adr/0004-daily-router-hybrid-interaction.md)

---

## Goal

The owner can no longer recall what skills exist or when to trigger them. Ship three
things: (1) **PLAYBOOK.md** — the one-page map of the daily arc and situational
triggers; (2) **`/daily`** — a hybrid menu/argument router that is the single thing
to memorize; (3) **consolidation** — copy the 5 missing daily-arc skills into the
repo so it is the single source of truth.

## Non-goals

- Copying `power-bi-*` (13), `seed-dataverse-data`, `react-structure`,
  `grill-with-docs`, `brainstorm-reviewer` into the repo (explicitly excluded, ADR 0002)
- Deleting the personal copies in `~/.claude/skills` (follow-up after the repo
  versions are verified via plugin install — not this change)
- Time-based automation (no cron; `/daily` is always user-invoked)
- A new plugin (everything lands in `dev-workflows`)

---

## The daily arc (canonical)

```
1. START      /daily start   → ado-backlog:my-work   (ADO task hub; GitHub only on request)
2. WORKING    /daily work    → situational toolbox (table below)
3. FILING     /daily file    → findings-to-ado-backlog OR findings-to-github-issues
4. REPORTING  /daily report  → management-talk
5. WRAP-UP    /daily wrap    → invoice-generator (every day; builds from git commits)
```

### WORKING — situational routing table

| When… | Reach for |
|---|---|
| designing something new | `grill-then-plan` |
| something broke | `debug-mantra` → *(fix is mechanical?)* fix → `post-mortem` → `management-talk` |
| | → *(fix involves a design choice?)* `grill-then-plan` first, then fix → `post-mortem` → `management-talk` (ADR 0003) |
| advising on how a system should work | `study-design-verify` |
| auditing names / mappings | `naming-audit` / `fit-gap-analysis` |
| explaining a complex problem | `problem-description` |
| "why does this code/ticket exist?" | `ticket-trace` |
| second opinion on plan/PR/change | `scrutinize` / `dual-verifier` |
| unfamiliar legacy codebase | `drive-to-legacy` |

---

## Deliverable 1 — Skill consolidation (5 copies)

Copy verbatim from `~/.claude/skills/<name>/SKILL.md` to
`plugins/dev-workflows/skills/<name>/SKILL.md`:

1. `debug-mantra`
2. `post-mortem`
3. `scrutinize`
4. `dual-verifier`
5. `drive-to-legacy`

Per copy: verify YAML frontmatter has `name` + trigger-rich `description`; verify no
absolute personal paths are referenced inside (adjust to `${CLAUDE_PLUGIN_ROOT}` if
any bundled files exist — expected: none, all five are single-file skills).

After this, every skill named in the arc lives in the repo.

## Deliverable 2 — PLAYBOOK.md (repo root)

One page, structured as:

1. **The daily circle (Mermaid diagram 1)** — the 5 stations as a cycle
   (START → WORKING → FILING → REPORTING → WRAP-UP → next day), with `/daily` shown
   as the entry point into every station via dotted edges.
2. **Situational table** — the WORKING routing table above, one row per trigger.
3. **The WORKING router (Mermaid diagram 2)** — the 8 situational branches, with
   the conditional debug chain drawn in full:
   `debug-mantra → {design choice?} → [no: fix | yes: grill-then-plan → fix] →
   post-mortem → management-talk` (ADR 0003).
4. **The one command** — `/daily` usage: bare → menu; `/daily <station>` → jump.
   Station words: `start`, `work`, `file`, `report`, `wrap`.
5. **Maintenance rule** — pointer to the CLAUDE.md convention: every new skill adds
   a row here.

Both diagrams are Mermaid blocks (render on GitHub and in VS Code). The chat
versions presented during design are the canonical drafts to embed.

Plain English, no implementation detail. The audience is the owner six months from
now, and any colleague who installs the marketplace.

## Deliverable 3 — `/daily` router

**Command** `plugins/dev-workflows/commands/daily.md` — thin wrapper, frontmatter
`description` + `argument-hint: "[start|work|file|report|wrap]"`, hands `$ARGUMENTS`
to the skill.

**Skill** `plugins/dev-workflows/skills/daily/SKILL.md`:

- **With argument** (`start|work|file|report|wrap`, accept close synonyms like
  `morning`, `stuck`, `done`): jump to that station.
- **Bare / unrecognized argument**: show the 5-station menu, never an error
  (ADR 0004).
- **Station behavior:**
  - `start` → invoke `ado-backlog:my-work`. Mention GitHub my-work exists only if
    the user asks for GitHub.
  - `work` → ask the one situational question (the 8 rows), route to the matched
    skill; for "something broke" follow the ADR 0003 conditional chain.
  - `file` → ask "ADO or GitHub?" → `findings-to-ado-backlog` or
    `findings-to-github-issues`.
  - `report` → invoke `management-talk`.
  - `wrap` → invoke `invoice-generator`.
- **Graceful degradation:** if a routed plugin is not installed (e.g. ado-backlog),
  say so and print the install command
  (`/plugin install ado-backlog@workflow-daily-work`) — never fail silently.

## Deliverable 4 — documentation sync

- **CLAUDE.md** — add convention: *"Every new skill must add one row to
  PLAYBOOK.md"*, placed beside the version-sync rule.
- **Root README.md** — fix staleness: now lists 3 plugins (ado-backlog,
  github-backlog, dev-workflows), links PLAYBOOK.md as "how to actually use this
  daily".
- **dev-workflows README + plugin.json description** — list the 6 new skills
  (5 copies + daily).
- **Version bumps:** `plugins/dev-workflows/.claude-plugin/plugin.json` 0.8.0 → 0.9.0
  and the matching entry in `.claude-plugin/marketplace.json` (must stay in sync).

---

## Acceptance checks

1. `/daily` with no argument prints the 5-station menu; every station routes to an
   existing skill in this repo.
2. `/daily wrap` (and each station word) jumps without showing the menu.
3. An unrecognized argument (`/daily banana`) falls back to the menu.
4. All 8 situational rows in PLAYBOOK.md name skills that exist under
   `plugins/*/skills/`.
5. The 5 copied skills load (frontmatter valid) and their personal originals remain
   untouched.
6. dev-workflows version is identical in plugin.json and marketplace.json.
7. Root README no longer claims the marketplace ships one plugin.

## Follow-ups (out of scope)

- Prune duplicate personal copies in `~/.claude/skills` after verifying the repo
  versions trigger correctly via plugin install.
- Decide the fate of the external `dev-playbook` plugin (its 5 skills are now
  redundant with this repo).
