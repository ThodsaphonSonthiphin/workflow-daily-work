---
name: chart-map
description: >-
  Chart a Decision map for an effort too big for one agent session — name the
  destination, grill breadth-first to separate real decision tickets from fog,
  create the map and its tickets behind a dry-run gate, fire the research
  subagents, then STOP. Use when the user has a loose, foggy, multi-session
  idea — "this is huge, where do we even start", "plan this migration", "chart
  this", "make a decision map", "map out this initiative", "too big for one
  session" — and the route to the goal is not visible yet. Do NOT use for a
  well-scoped single-session design (that is grill-then-plan / grill-with-docs),
  and do NOT use to continue a map that already exists (that is work-map). If
  the opening grill surfaces no fog, this skill stops and says a map is not
  needed.
---

# chart-map

Chart the way; don't charge at the goal. The output is a **Decision map** — one
item indexing the whole effort — plus child **Decision tickets**: questions whose
resolution is a *decision*, each sized to one session.

**Plan, don't do.** Charting creates the map and hand-resolves nothing (ADR
0041). One charting run is one session, and it ends at Step 5.

Emit this diagram once, at the start, so the user can see the whole run:

```
CHART A DECISION MAP — one session, then stop
─────────────────────────────────────────────

  ① PREFLIGHT
  │   backend = local markdown (v1 only)
  │   maps land in docs/decision-map/<slug>/
  │   name it BEFORE any charting
  ▼
  ② DESTINATION
  │   what does arriving look like?
  │   one or two lines, written down first
  ▼
  ③ FRONTIER — breadth-first, never deep
  │   can you STATE the question now?
  │     yes → ticket · no → fog
  │     past the destination → out of scope
  │
  │   no fog anywhere? ■ STOP — no map
  │      needed; hand to grill-then-plan
  ▼
  ④ GATE — dry run first, always
  │   create · skip (exists) · merge
  │   show every label → get a yes → --real
  ▼
  ⑤ RESEARCH subagents, in parallel
  │   findings posted back with `resolve`
  ▼
  ■ STOP — charting hand-resolves nothing
```

## Step 0 — Preflight: name the backend before you chart

**v1 has exactly one backend: local markdown** (ADR 0056). Say so in one line
before anything else happens, even if the user never mentioned a tracker:

> This map will live in this repo as Markdown, under
> `docs/decision-map/<slug>/`, and is shared the way the repo is shared — by
> committing it. Azure DevOps and GitHub Issues are planned (phase 2) but are
> not available yet, so nothing will appear on a board.

Someone who expected their map on a shared board needs to learn that **here**,
not after spending a session charting. If a board is a hard requirement for
them, stop and say decision-map cannot do that yet. Do **not** offer to install
`ado-backlog` or `github-backlog` — neither plugin can drive a decision map, so
offering them would be a false promise.

Everything from Step 1 down is backend-neutral: when phase 2 lands, only the
script named in this step changes, not the flow, the subcommands, or the JSON.

**Ops script** (run it with `python`, from the repo root, so the map lands at
its ADR-0042 default location):

```
${CLAUDE_PLUGIN_ROOT}/scripts/local_map_ops.py
```

**Contract** — every subcommand, flag and JSON shape used below is fixed by
`${CLAUDE_PLUGIN_ROOT}/references/data-contracts.md`. Where this skill and the
contract disagree, the contract wins.

The map is repo docs, so it is committed through **assisted git** — offer the
commit, never make it automatically.

## Step 1 — Name the destination

Run a short grilling exchange (load `grill-with-docs` the way your harness loads
skills, if it is available; otherwise ask directly, one question at a time):
**what does reaching the end look like?** A written spec, a locked decision, a
change made in place?

One or two lines. The destination is what every ticket is measured against, and
what makes "out of scope" decidable. Write it down before any ticket exists.

## Step 2 — Map the frontier, breadth-first

Grill again, this time breadth-first: fan out across the whole space, never deep
on one thread. Depth is what the individual sessions are for.

For each area, apply one test — **can you *state* the question precisely, right
now?** Not answer it. State it.

| Verdict | When | What you record |
|---|---|---|
| **Ticket** | you can state the question precisely now, even if it is blocked | a typed ticket (below) |
| **Fog** | you cannot phrase it sharply yet | one line under "Not yet specified" |
| **Out of scope** | it lies past the destination | one line under "Out of scope" |

Do not pre-slice fog into ticket-sized pieces. Fog that is left as fog graduates
into real tickets later, once an earlier decision has sharpened it.

Type every ticket — the type picks its resolver and its mode (ADR 0038):

| Type | Mode | Resolved by |
|---|---|---|
| `research` | AFK | a research subagent, fired at chart time (Step 4) |
| `prototype` | HITL | a cheap artifact the user reacts to |
| `grilling` | HITL | a live grilling exchange — the default |
| `task` | either | doing the thing that unblocks a decision |

**If this step surfaces no fog at all, stop.** The way is already clear and the
whole journey fits one session, so a map would be overhead. Say that plainly and
point the user at `grill-then-plan` instead.

## Step 3 — Create the map (gated)

Build a `map_input.json` in a scratch working directory. These JSON files are
working files, never a store — the map itself is the source of truth.

```json
{
  "target": { "slug": "billing-migration" },
  "map": {
    "title": "Decision map - migrate billing to the new provider",
    "destination": "<the one or two lines from Step 1>",
    "notes": "<skills every session should consult; standing preferences>",
    "notYetSpecified": ["<fog line>"],
    "outOfScope": ["<ruled-out line>"]
  },
  "tickets": [
    { "key": "provider-choice", "title": "Provider - which one do we commit to?",
      "type": "grilling", "question": "<the decision this resolves>",
      "blocks": ["cutover-order"] }
  ]
}
```

- `slug` and every ticket `key` are lowercase-kebab, must match
  `[A-Za-z0-9][A-Za-z0-9_-]*`, and **must not contain `--`**.
- `blocks` is **downstream** — the tickets this one holds up. Readers see the
  upstream `blockedBy` instead; do not confuse the two.
- `mapType` / `ticketType` in the contract are Azure DevOps work-item types.
  They have no effect on the local backend — leave them out.

### The create-class gate (never skip it)

**1. Dry run.** `chart` is dry-run by default; `--real` is what writes.

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/local_map_ops.py" chart --input <workdir>/map_input.json
```

The plan lands twice: as JSON on **stdout** (machine-readable) and as a human
rendering on **stderr**. Show the user the stderr rendering.

**2. Read the labels — they are what the user is approving.** Every item the run
would touch appears exactly once, with one of four actions:

| Action | What it means for that item |
|---|---|
| `create` | it does not exist yet and will be created |
| `skip (exists)` | it exists and **nothing** will be written to it |
| `merge` | it exists and will be modified **in place, additively** — the `detail` names exactly what it gains |
| `OVERWRITE` | `--force` only: it exists and will be fully rewritten, discarding its recorded state |

On a first chart every line is `create`. On a later chart most lines are
`skip (exists)` — that is the design, not a failure: **`chart` is additive** (ADR
0054/0055). It adds what is absent and never removes, reorders or overwrites
what is there, so re-running the identical input is a byte-identical no-op, and
a partially-failed chart is resumable by simply re-running it. If you see an
`OVERWRITE` line and did not deliberately pass `--force`, stop and investigate.

**3. Ask for explicit approval. Never create without it.** The approval is for
the plan you just showed — if the input changes at all, re-run the dry run and
show the new plan.

**4. On approval, re-run with `--real`:**

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/local_map_ops.py" chart --input <workdir>/map_input.json --output <workdir>/map.json --real
```

Keep the returned `map.json` as this session's working file. Show the user the
map's name and its path, and the tickets by name — never a wall of bare keys.
The script wires the parent links and the blocking edges itself.

**5. Check `divergence` in the result.** A non-empty list means the input asked
for something an additive run deliberately did **not** apply — most often a
changed `title` / `destination` / `notes` on a map that already exists. Report
every line. The fix is to edit `map.md` by hand, never to reach for `--force`.

**On failure:** a known, actionable failure exits `2` with one line on stderr
and **empty stdout**. That line names the field to fix. Correct
`map_input.json`, re-run the dry run, and re-approve.

### `--force` is an escape hatch, never a remedy

`--force` is **destructive**: on every item the plan labels `OVERWRITE` it
discards the recorded resolution, the claim and the blocking edges. Its exact
blast radius — which items it reaches, and what survives on each — is tabulated
in `${CLAUDE_PLUGIN_ROOT}/references/data-contracts.md`. Read it there and quote
it; do not paraphrase it loosely.

Do **not** suggest `--force` because a re-chart printed `skip (exists)`, because
the map looks stale, or because a run half-failed. Additive `chart` already
covers all three, and `--force` is never required to add a ticket or an edge.
Offer it only when the user explicitly asks for an existing map to be rewritten
from a new input — and only after showing the `--force` dry run's `OVERWRITE`
lines and naming, per line, what will be destroyed.

## Step 4 — Fire the research subagents

Every `research` ticket is AFK, and they are the one exception to
one-ticket-per-session. For each one just created:

1. Dispatch a research subagent — all of them in parallel, the way your harness
   runs subagents. Give it that ticket's Question verbatim plus the destination
   line for context, and ask for raw markdown findings, not a polished summary.
2. Write each set of findings to a scratch file and post it onto its ticket:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/local_map_ops.py" resolve --map <slug> --ticket <key> --gist "<one-line answer>" --body-file <workdir>/findings-<key>.md
```

`resolve` records the resolution, closes the ticket, and re-projects the map's
"Decisions so far" index.

**Escalation (ADR 0038).** If a research question can only be answered from a
live system — a real schema, a real org's data, the actual code — do not answer
it from outside knowledge. Leave the ticket **open** and note on it that it
should be resolved via `study-design-verify` in its own session:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/local_map_ops.py" comment --map <slug> --ticket <key> --body-file <workdir>/note-<key>.md
```

## Step 5 — Stop

Report, in this order:

- the map's name and path;
- the tickets **by name**, split into frontier (open and unblocked) and blocked;
- what the research subagents resolved, one gist each;
- the fog lines still unspecified;
- what was ruled out of scope.

Offer to commit the new `docs/decision-map/<slug>/` folder (assisted git —
offer, never automatic).

Then suggest `/decision-map:work` for the next session, and **stop**. Do not
claim a ticket, do not resolve one, do not start the first decision. Charting is
one session's work, and the map — not this conversation — carries the state from
here on.

Fog graduates into new tickets later through this same Step 3 gate, driven from
`work-map`: `chart` is one operation serving both acts (ADR 0054).
