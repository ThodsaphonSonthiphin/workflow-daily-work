---
name: daily
description: >-
  The single entry point into the daily-work arc — a hybrid menu/argument router.
  Trigger whenever the user invokes /dev-workflows:daily, types /daily, asks
  "what should I do now", "where was I", "start my day", "what's next today",
  "wrap up my day", "end my day", or seems unsure which skill fits their current
  daily-work moment. Bare invocation shows a 5-station menu (starting / working /
  filing findings / reporting / wrapping up); with an argument (start | work |
  file | report | wrap, synonyms accepted) it jumps straight to the station and
  hands off to the right skill: ado-backlog:my-work, the situational toolbox
  (grill-then-plan, debug-mantra, study-design-verify, naming-audit,
  fit-gap-analysis, problem-description, ticket-trace, scrutinize, dual-verifier,
  drive-to-legacy, crm-archaeology), findings-to-ado-backlog /
  findings-to-github-issues, management-talk, or invoice-generator.
---

# daily — the one command to remember

Route the user to the right skill for their moment in the day. You are a router:
ask at most two short questions, then hand off. Do not do the station's work
yourself — the destination skill owns it.

## Parse the argument first

`$ARGUMENTS` (if any) selects a station. Match case-insensitively against the
station words and synonyms:

| Station | Words |
|---|---|
| START | `start`, `morning`, `begin`, `plate` |
| WORK | `work`, `working`, `stuck`, `doing` |
| FILE | `file`, `filing`, `findings`, `tickets` |
| REPORT | `report`, `status`, `update` |
| WRAP | `wrap`, `done`, `end`, `finish`, `invoice` |

- **Match** → jump straight to that station (no menu).
- **No argument, or no match** → show the menu. An unrecognized word is NEVER an
  error; show the menu with a one-line note ("didn't recognize '<word>'").

## The menu (bare /daily)

Present exactly five options and wait:

```
Where are you in your day?

  1. ☀️  Starting my day      — what's on my plate
  2. 🔧  Working / stuck      — route me to the right tool
  3. 📋  Filing findings      — turn findings into tickets
  4. 📣  Reporting status     — reshape work for leadership
  5. 🌙  Wrapping up          — daily summary from my commits

(Next time: /daily start · work · file · report · wrap)
```

The last line teaches the shortcuts — that is how users graduate from menu to
argument.

## Stations

### 1. START

Invoke the **`my-work`** skill from the ado-backlog plugin (`ado-backlog:my-work`).
Mention the GitHub equivalent (`github-backlog`'s `github-my-work`) ONLY if the
user asks for GitHub.

### 2. WORK

Ask ONE question — "What's happening?" — with these options, then hand off:

| The user is… | Hand off to |
|---|---|
| designing something new | `grill-then-plan` |
| dealing with something broken | `debug-mantra` — then follow the debug chain below |
| advising how a system should work | `study-design-verify` |
| auditing names / labels / mappings | `naming-audit` (or `fit-gap-analysis` for as-is vs to-be) |
| explaining a complex problem | `problem-description` |
| asking why code/a ticket exists | `ticket-trace` |
| wanting a second opinion | `scrutinize` (plans/PRs) or `dual-verifier` (completed work) |
| facing an unfamiliar legacy codebase | `drive-to-legacy` |
| facing an unfamiliar Dynamics 365 / Dataverse org | `crm-archaeology` |

**Debug chain (ADR 0003):** after `debug-mantra` produces a diagnosis, ask:
*"Does the fix involve a design choice (multiple viable approaches with
trade-offs)?"*
- **No (mechanical fix)** → fix → `post-mortem` → offer `management-talk`.
- **Yes** → `grill-then-plan` to capture the decision FIRST → fix →
  `post-mortem` → offer `management-talk`.

### 3. FILE

Ask ONE question — "ADO or GitHub?" — then invoke `findings-to-ado-backlog`
(ado-backlog plugin) or `findings-to-github-issues` (github-backlog plugin).

### 4. REPORT

Invoke `management-talk`.

### 5. WRAP

Invoke `invoice-generator`. Run it every day — it builds the summary from git
commits, so a day without invoicing still yields a Tribletext-ready record.

## Graceful degradation

Stations 1 and 3 route to skills in OTHER plugins. If the target plugin is not
installed, say so explicitly and print the install command — never fail silently:

```
ado-backlog is not installed. Install it with:
/plugin install ado-backlog@workflow-daily-work
```

(Same pattern for `github-backlog@workflow-daily-work`.)

## Rules

- At most two questions before handoff (station + the one station question).
- Never do the destination skill's job inline.
- Unknown argument → menu, never an error.
- The full map lives in PLAYBOOK.md at the marketplace repo root — for humans;
  this skill is self-contained and never needs to read it.
