# Frame Line Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Every message the plan stage sends the person opens with one fixed Frame line (`#196 AC-2 · 196-match-key · question 1 of 2 · plan (2/4)`), and `work-map` lists the calling ticket's Decision tickets first.

**Architecture:** Three skill texts change and nothing else runs differently: `work-map` defines the Frame line once and uses it in its frontier, its questions and its close report; `chart-map` gets the same rule in one paragraph; `resolve-the-ticket` hands both map skills the facts the line needs (ticket number, AC rows, point letters, stage count) on the yes. The facts for a cold session come from the "Touches" sentence every Decision ticket's Question already ends with. No script, no data contract, no existing ticket changes.

**Tech Stack:** Markdown skill files (`SKILL.md`), JSON eval files, Python 3.12 (`scripts/generate_skills_tree.py`, `scripts/check_skills_tree.py`), git on Windows (CRLF checkout, `core.autocrlf=true`).

**Spec:** `docs/superpowers/specs/2026-11-24-frame-line-design.md` (ADRs `workflow-daily-work-0392` to `0397`; ADR `0338` amended; CONTEXT.md term **Frame line** already written on 2026-11-24).

## Global Constraints

- Repo: `C:\Repo\workflow-daily-work`, branch `main`. Commit on it, as the repo's own history does. **No `Co-Authored-By: Claude …` line in any commit message** (Pon's rule, overrides the harness reminder).
- Only these skills are edited: `plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md`, `plugins/decision-map/skills/work-map/SKILL.md`, `plugins/decision-map/skills/chart-map/SKILL.md`. `sp-grill-with-doc`, `guide-and-verify`, `sp-writing-plans`, the map scripts and `references/data-contracts.md` are not touched (ADRs 0338, 0395).
- Skills stay harness-neutral: say "load the skill the way your harness loads skills", never "call the Skill tool". No new `${CLAUDE_PLUGIN_ROOT}` shapes.
- The Frame line grammar, verbatim from the spec, parts joined by ` · ` in this order: tracker ticket + AC line → Decision ticket key (chart-map: `briefing point <letter>`) → map (chart-map only: `chart map <slug>`) → `question N of M` (`question N` when M is unknown; on a question only) → stage (`plan (2/4)` when loaded by resolve-the-ticket; `work-map` / `chart-map` on a direct call).
- Versions: dev-workflows `0.69.0` → `0.70.0`; decision-map `0.14.0` → `0.15.0`; each plugin's `.claude-plugin/plugin.json` and its entry in `.claude-plugin/marketplace.json` report the same number.
- The generated `skills/` tree is never hand-edited: regenerate with `python scripts/generate_skills_tree.py --repo .` and prove with `python scripts/check_skills_tree.py --repo .` (exit 0). The checkout is CRLF, so the generator marks every skill modified; `git diff --ignore-cr-at-eol --stat -- skills/` must list only the three skills, and `git checkout -- skills/` restores the rest.
- Read `/usr/bin/sort` as unavailable in the Bash tool on this PC (Defender ASR); use Python for sorting or hashing.
- Eval files follow the shape in `plugins/dev-workflows/skills/resolve-the-ticket/evals/evals.json`: `{"skill_name": …, "evals": [{"id", "name", "prompt", "expected_output", "files": [], "assertions": [...]}]}`. An eval is the test of a skill-text change: write it before the text, then check every assertion against the new text by reading it.

---

### Task 1: work-map - the Frame line section, the per-ticket frontier group, the question rule, the close report

**Files:**
- Modify: `plugins/decision-map/skills/work-map/SKILL.md` (the opening diagram at lines 28-63; a new section before `## Step 0` at line 65; Step 1 after the "If the frontier is empty" paragraph at lines 234-236; Step 3's "Frame every question" paragraph at lines 345-352; Step 6's "Report, in this order:" at line 728)
- Create: `plugins/decision-map/skills/work-map/evals/evals.json`

**Interfaces:**
- Consumes: the "Touches" sentence of a Decision ticket's `## Question` (free text, ADR 0346), e.g. `Touches #196 AC-4.`; the tracker ticket number, the row list and the stage count that `resolve-the-ticket` hands over on the yes (Task 3 writes that hand-off; the wording this task expects is: `for #196`, `rows: AC-1 "…", AC-2 "…"`, `stage: plan (2/4)`).
- Produces: the section heading `## The Frame line` (Task 2 and Task 3 refer to it by that name) and the message shapes the evals assert.

- [ ] **Step 1: Write the failing eval**

Create `plugins/decision-map/skills/work-map/evals/evals.json`:

```json
{
  "skill_name": "work-map",
  "evals": [
    {
      "id": 0,
      "name": "called-for-one-tracker-ticket-every-message-opens-with-the-frame-line",
      "prompt": "work the decision map docs/decision-map/ado-193-ips-api-feed/ for #196, stage plan (2/4). Rows of #196: AC-1 \"Initial full seed populates all active and pre-appointment IPS cases\", AC-2 \"Daily delta sync updates modified cases idempotently by mgw_casecode\", AC-3 \"Every synced case record includes resolved emails and the appointment status\", AC-4 \"Transient network or API errors are logged with structured retry handling\". The map is local. Its open tickets and the Touches sentence of each Question: 196-match-key (grilling) 'Touches #144, #196 AC-2.'; 196-retry-shape (grilling) 'Touches #196 AC-4.'; 196-staff-source (task) 'Touches #196.'; 195-ip-loss-recovery (task) 'Touches #195 AC-1 and #196.'; 197-counts-and-owner (task) 'Touches #197 AC.'. Milestones: decide-now [195-ip-loss-recovery], sync-ready [196-match-key, 196-retry-shape, 196-staff-source], timesheet-ready [197-counts-and-owner]. Nothing is claimed or blocked. I pick 196-match-key; it has two questions. After both answers, close it.",
      "expected_output": "Every message to the person opens with the Frame line. The frontier lists the tickets for #196 first under a heading with their count, then one line for the rest of the map, and recommends inside the #196 group. Each grilling question opens '#196 AC-2 · 196-match-key · question N of 2 · plan (2/4)'. The close report opens '#196 AC-2 · 196-match-key closed · plan (2/4): #196 has 3 open'.",
      "files": [],
      "assertions": [
        "The first line of the frontier message is '#196 · map ado-193-ips-api-feed · plan (2/4)' and nothing comes before it",
        "The frontier shows a heading 'Tickets for #196' with the count '4 of 4 open' (196-match-key, 196-retry-shape, 196-staff-source and 195-ip-loss-recovery, which touches #196 too), each with its type and the AC line its Touches sentence names",
        "After the group, one line says 'Other tickets on this map: 1 for #197' and names 197-counts-and-owner",
        "The recommendation is a ticket inside the #196 group, not 197-counts-and-owner, and it does not say the two-level milestone rule chose it from the whole map",
        "The first question opens with the line '#196 AC-2 · 196-match-key · question 1 of 2 · plan (2/4)' before any context or question text",
        "The second question opens with '#196 AC-2 · 196-match-key · question 2 of 2 · plan (2/4)'",
        "The close report opens with '#196 AC-2 · 196-match-key closed · plan (2/4): #196 has 3 open'",
        "No message to the person in the run opens with a heading, a table or prose before the Frame line",
        "The Touches sentence of the ticket is read from the ticket file, not from read or frontier output"
      ]
    },
    {
      "id": 1,
      "name": "a-direct-call-still-opens-every-question-with-the-frame-line",
      "prompt": "continue the map docs/decision-map/ado-193-ips-api-feed/ (local). No tracker ticket was named. Open tickets: 196-retry-shape (grilling) whose Question ends 'Touches #196 AC-4.'; 197-counts-and-owner (task) whose Question ends 'Touches #197 AC.'. Milestones: sync-ready [196-retry-shape], timesheet-ready [197-counts-and-owner]. I pick 196-retry-shape. It needs one question; I do not know how many more.",
      "expected_output": "The frontier is shown by milestone as before (no tracker group, because none was named). The question opens '#196 AC-4 · 196-retry-shape · question 1 · work-map'.",
      "files": [],
      "assertions": [
        "The frontier is grouped by milestone and has no 'Tickets for #' heading",
        "The first question opens with '#196 AC-4 · 196-retry-shape · question 1 · work-map' - the tracker part comes from the ticket's Touches sentence, there is no 'of M' and the stage part is 'work-map'",
        "The frontier message's first line is 'map ado-193-ips-api-feed · work-map'"
      ]
    }
  ]
}
```

- [ ] **Step 2: Check the eval fails against the current text**

Run: `grep -c "Frame line" plugins/decision-map/skills/work-map/SKILL.md`
Expected: `0` (the current text has no Frame line; assertions 1, 5, 6, 7 cannot hold).

- [ ] **Step 3: Add the Frame line to the opening diagram**

In `plugins/decision-map/skills/work-map/SKILL.md`, replace the diagram lines

```
  ② FRONTIER
  │   read the map, then list the frontier
  │   BY NAME — never a wall of bare ids
```

with

```
  ② FRONTIER
  │   read the map, then list the frontier
  │   BY NAME — never a wall of bare ids
  │   called for one tracker ticket? its
  │   tickets first (ADR 0394)
```

and replace

```
  ④ RESOLVE by type
  │   grilling · prototype · research · task
```

with

```
  ④ RESOLVE by type
  │   grilling · prototype · research · task
  │   every message opens with the FRAME LINE
  │   #196 AC-2 · 196-match-key · question 1 of 2
```

- [ ] **Step 4: Add the Frame line section before Step 0**

Insert this section immediately before the line `## Step 0 — Preflight: name the backend before you work` (keep one blank line on each side):

````markdown
## The Frame line — the first line of every message to the person (ADRs 0392, 0393, 0396)

A person answering a question could not tell which tracker ticket, which acceptance
criterion and which Decision ticket it served (measured 2026-11-24: three `/wait-what`
calls in one hour, every re-pitch that landed opened with the line the question lacked).
So **every message this skill sends the person — the frontier, the dry-run gate, each
question, the close report — opens with one fixed line, before any heading, table or
prose.** Its parts, joined by ` · `, in this order; leave out a part you do not have:

| part | value | present |
|---|---|---|
| tracker ticket + AC line | `#196 AC-2` — from the sentence of the ticket's `## Question` that starts `Touches` (`Touches #195 AC-2 and #196.` becomes `#195 AC-2, #196`); when the sentence names no AC line, the ticket alone; when there is no sentence, the tracker ticket the caller named; when neither, nothing | when known |
| Decision ticket | the key — `196-match-key`; `196-match-key closed` on the close report; `196-retry-shape (new)` on a gate that creates it | always |
| question number | `question 1 of 2`; `question 1` when you do not know how many there will be | on a question only |
| stage | what the caller named — `plan (2/4)` from resolve-the-ticket; `work-map` on a direct call | always |

```
frontier     #196 · map ado-193-ips-api-feed · plan (2/4)
dry-run gate #196 AC-4 · 196-retry-shape (new) · plan (2/4)
question     #196 AC-2 · 196-match-key · question 1 of 2 · plan (2/4)
close report #196 AC-2 · 196-match-key closed · plan (2/4): #196 has 7 open
direct call  #196 AC-4 · 196-retry-shape · question 1 · work-map
```

The frontier message has no one ticket yet, so its line is the tracker ticket (when
named), `map <slug>` and the stage. The `Touches` sentence is **not** in `read` or
`frontier` output — open the ticket document (`docs/decision-map/<slug>/tickets/<key>.md`
on local, the issue body on GitHub) and read it, as Step 1 already opens the map document
for the fog region. An AC line the sentence names that is not in the caller's row list is
written as the sentence has it, followed by `(not in the row list)`, so a mismatch is seen.
Identifiers stay in English whatever language the rest of the message is in. The line is
written by this skill on every message, including the questions a loaded grilling skill
asks: hand the grilling skill the line and ask it to open every question with it, counting
the question number.
````

- [ ] **Step 5: Add the per-ticket group to Step 1**

Immediately after the paragraph that ends `and Step 6 tells them apart.` (and before `### Offer milestones once, only on a big unmilestoned map (ADR 0100)`), insert:

````markdown
### Called for one tracker ticket: its tickets first (ADR 0394)

When the caller named a tracker ticket — `resolve-the-ticket` does on its yes: "for #196",
with the row list and the stage — a map shared by a Feature's children (ADR 0346) is shown
from that ticket's side, before the milestone view above:

```
#196 · map ado-193-ips-api-feed · plan (2/4)

Tickets for #196 - 8 of 10 open:
  196-status-rule (grilling, AC-3) · 196-match-key (grilling, AC-2) · 196-retry-shape (grilling, AC-4)
  196-staff-source (task) · 196-portal-login-source (task) · 196-alert-recipients (task)
  196-vnet-path (task) · 196-schema-in-staging (task, Brad answers)
Other tickets on this map: 1 for #195 (195-ip-loss-recovery), 1 for #197.
```

A ticket is in the group when the `Touches` sentence of its Question names the tracker
ticket; a ticket that touches several tracker tickets is in each group — accepted. The
count is open tickets of the group over all tickets of the group. Blocked and claimed
tickets of the group are collapsed to one line each, as the milestone view does. The rest
of the map is one line, counted per tracker ticket. **Step 2's recommendation picks inside
the group**, by the existing heuristic (the ticket that unblocks the most); the two-level
milestone rule is applied inside the group only. With no tracker ticket named (a direct
call) there is no group, and the milestone view above is the whole presentation.
````

- [ ] **Step 6: Replace the "restate" sentence in Step 3 with the rule**

Replace the paragraph

```
**Frame every question in the user's terms, whatever the ticket's `type`** — name the
screen, what they press, what they would observe. Restate where the session has got to
*immediately before* asking: a frame set at session open goes stale across a long
technical middle. And when a plan, ADR or standing rule already names a route, say so
and justify any deviation rather than offering a neutral menu. This is not grilling-only
— a `task` ticket's blocking question (which branch, which environment) fails the same
way. An answer that comes back as a question is a framing failure: re-pose it, do not
explain it at greater length.
```

with

```
**Open every question with the Frame line, then frame it in the user's terms, whatever
the ticket's `type`** — the line first (`#196 AC-2 · 196-match-key · question 1 of 2 ·
plan (2/4)`, see *The Frame line* above), then the screen, what they press, what they
would observe. A restatement of where the session has got to, set once at session open,
goes stale across a long technical middle; the line is that restatement, on every
message. And when a plan, ADR or standing rule already names a route, say so and justify
any deviation rather than offering a neutral menu. This is not grilling-only — a `task`
ticket's blocking question (which branch, which environment) fails the same way. An
answer that comes back as a question is a framing failure: re-pose it, do not explain it
at greater length.
```

- [ ] **Step 7: Open the close report with the line**

Replace

```
Report, in this order:

- **any `lint` finding**, errors first — and say explicitly when it came back
  clean, so the user knows the check ran;
```

with

```
Report, opening with the Frame line in its closed form — `#196 AC-2 · 196-match-key
closed · plan (2/4): #196 has 7 open`, the count being the tracker ticket's open tickets
when the caller named one, else the map's — then in this order:

- **any `lint` finding**, errors first — and say explicitly when it came back
  clean, so the user knows the check ran;
```

- [ ] **Step 8: Check every assertion against the new text**

Run:

```bash
cd /c/Repo/workflow-daily-work && f=plugins/decision-map/skills/work-map/SKILL.md
grep -n "^## The Frame line" "$f"
grep -n "Tickets for #196 - 8 of 10 open" "$f"
grep -n "Open every question with the Frame line" "$f"
grep -n "opening with the Frame line in its closed form" "$f"
grep -n "not in the row list" "$f"
grep -n "question 1 · work-map" "$f"
python -I -c "import json; d=json.load(open('plugins/decision-map/skills/work-map/evals/evals.json',encoding='utf-8')); print(d['skill_name'], len(d['evals']))"
```

Expected: one line number for each `grep`; `work-map 2`. Then read the four edited places once and check each assertion of eval 0 and eval 1 is satisfiable by the text (the group heading, the count, the "Other tickets" line, the question line with and without `of M`, the close line, the ticket-file read).

- [ ] **Step 9: Commit**

```bash
cd /c/Repo/workflow-daily-work
git add plugins/decision-map/skills/work-map/SKILL.md plugins/decision-map/skills/work-map/evals/evals.json
git commit -m "feat(work-map): every message opens with the Frame line; a tracker ticket's Decision tickets first (ADRs 0392-0396)"
```

---

### Task 2: chart-map - the Frame line under the HITL guard

**Files:**
- Modify: `plugins/decision-map/skills/chart-map/SKILL.md` (after the HITL guard's last paragraph, `If the human is not available to answer, stop and say so rather than charting alone.`, lines 176-177; the opening diagram lines 28-74)
- Modify: `plugins/decision-map/skills/chart-map/evals/evals.json` (append one eval)

**Interfaces:**
- Consumes: the points `resolve-the-ticket` hands over on the yes, each as `<letter> · <locator> · <question> · <who must answer>` — e.g. `C · #196 AC-4 · Retries - how does the sync handle a transient error? · not named` (Task 3 writes that hand-off); the stage count `plan (2/4)`.
- Produces: the paragraph `**The Frame line** (ADRs 0392, 0397)` the eval asserts; the `Touches` sentence on every ticket it creates stays as ADR 0346 has it.

- [ ] **Step 1: Write the failing eval**

Append to the `evals` array of `plugins/decision-map/skills/chart-map/evals/evals.json` (keep eval 0 as it is; the new one is `id: 1`):

```json
{
  "id": 1,
  "name": "charted-from-a-briefing-every-question-opens-with-the-frame-line",
  "prompt": "chart a map for ADO Feature #193 (children #194-#197), stage plan (2/4), local markdown, folder ado-193-ips-api-feed. The briefing's open points, each with its letter and locator: A · #195 AC-1 · NAT gateway shape - SKU, IP, subnets and names? · not named; B · #195 AC-2 · IPS password - by which safe route does it reach Key Vault? · Scott van der Kreek; C · #196 AC-4 · Retries - how does the sync handle a transient network or API error? · not named. Group 1: B. Group 2: A, C. B blocks C. Destination to confirm with me: every question that blocks building #195 and #196 has a recorded answer.",
  "expected_output": "A charting run whose every message to the person opens with the Frame line: the destination question '#193 · briefing · chart map ado-193-ips-api-feed · question 1 of 4 · plan (2/4)', then one question per point opening with that point's letter and locator, then the sweep question, then the gate.",
  "files": [],
  "assertions": [
    "The first message to the person opens with '#193 · briefing · chart map ado-193-ips-api-feed · question 1 of 4 · plan (2/4)' and asks the destination",
    "The question about point C opens with '#196 AC-4 · briefing point C · chart map ado-193-ips-api-feed · question 4 of 4 · plan (2/4)' or the same line with its own position in the count",
    "The sweep's one batched question opens with '#193 · sweep · chart map ado-193-ips-api-feed · question 5 of 5 · plan (2/4)' (the count grows by one for the sweep)",
    "The dry-run gate message opens with '#193 · chart map ado-193-ips-api-feed · gate · plan (2/4)'",
    "Every created ticket's Question still ends with a sentence that starts 'Touches' and names the point's locator, e.g. 'Touches #196 AC-4.'",
    "No message to the person opens with a heading, a table or prose before the Frame line"
  ]
}
```

- [ ] **Step 2: Check the eval fails against the current text**

Run: `grep -c "Frame line" plugins/decision-map/skills/chart-map/SKILL.md`
Expected: `0`.

- [ ] **Step 3: Add the line to the opening diagram**

Replace

```
  ② DESTINATION  (HITL — the human answers)
  │   what does arriving look like?
  │   one or two sentences, one line, first
```

with

```
  ② DESTINATION  (HITL — the human answers)
  │   what does arriving look like?
  │   one or two sentences, one line, first
  │   every message opens with the FRAME LINE
  │   #196 AC-4 · briefing point C · question 3 of 4
```

- [ ] **Step 4: Add the paragraph under the HITL guard**

Immediately after the paragraph `If the human is not available to answer, stop and say so rather than charting\nalone.` (and before `## Step 2 — Map the frontier, breadth-first`), insert:

````markdown
**The Frame line** (ADRs 0392, 0397). Every message this skill sends the person — the
destination question, each frontier question, the sweep's batched question, the gate, the
report — opens with one fixed line, before any heading, table or prose. Its parts, joined
by ` · `, in this order; leave out a part you do not have:

| part | value |
|---|---|
| tracker ticket + AC line | the locator the caller gave the point (`#196 AC-4`); on the destination, the sweep and the gate, the Feature or ticket the map is for (`#193`) |
| point | `briefing point C` — the letter the caller gave; `briefing` on the destination question, `sweep` on the sweep, `gate` on the dry run |
| map | `chart map <slug>` |
| question number | `question 3 of 4` — M is the points handed in plus one for the destination, plus one more when the sweep is asked; `question N` when the count is not known |
| stage | what the caller named (`plan (2/4)` from `resolve-the-ticket`); `chart-map` on a direct call |

```
destination  #193 · briefing · chart map ado-193-ips-api-feed · question 1 of 4 · plan (2/4)
a point      #196 AC-4 · briefing point C · chart map ado-193-ips-api-feed · question 4 of 4 · plan (2/4)
sweep        #193 · sweep · chart map ado-193-ips-api-feed · question 5 of 5 · plan (2/4)
gate         #193 · chart map ado-193-ips-api-feed · gate · plan (2/4)
direct call  chart map billing-migration · briefing · question 1 · chart-map
```

A direct call with no briefing behind it has no letters and no locators: the line is the
map, the step and the question number. The locator a point carries is also what the
ticket's Question names in its closing `Touches` sentence (ADR 0346) — write both from the
same value, so `work-map` later reads the same `#196 AC-4` back from the ticket.
````

- [ ] **Step 5: Check every assertion against the new text**

Run:

```bash
cd /c/Repo/workflow-daily-work && f=plugins/decision-map/skills/chart-map/SKILL.md
grep -n "^\*\*The Frame line\*\* (ADRs 0392, 0397)" "$f"
grep -n "briefing point C · chart map ado-193-ips-api-feed · question 4 of 4" "$f"
grep -n "gate         #193" "$f"
grep -n "FRAME LINE" "$f"
python -I -c "import json; d=json.load(open('plugins/decision-map/skills/chart-map/evals/evals.json',encoding='utf-8')); print(d['skill_name'], [e['id'] for e in d['evals']])"
```

Expected: a line number for each `grep`; `chart-map [0, 1]`. Read the paragraph once against the six assertions.

- [ ] **Step 6: Commit**

```bash
cd /c/Repo/workflow-daily-work
git add plugins/decision-map/skills/chart-map/SKILL.md plugins/decision-map/skills/chart-map/evals/evals.json
git commit -m "feat(chart-map): every message opens with the Frame line, naming the briefing point (ADR 0397)"
```

---

### Task 3: resolve-the-ticket - hand the map skills the facts for the line

**Files:**
- Modify: `plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md` (Stage 2: the offer table at lines 293-298, the end-of-run line at lines 299-302, the `What to hand chart-map` table at lines 304-313; the flow diagram at lines 29-50 is unchanged)
- Modify: `plugins/dev-workflows/skills/resolve-the-ticket/evals/evals.json` (append one eval)

**Interfaces:**
- Consumes: the section name `## The Frame line` in `work-map` (Task 1) and the paragraph `**The Frame line**` in `chart-map` (Task 2).
- Produces: the hand-off wording both map skills expect — to `work-map`: `for #196`, `rows: AC-1 "…", …`, `stage: plan (2/4)`; to `chart-map`: each point as `<letter> · <locator> · <question> · <who>` and `stage: plan (2/4)`.

- [ ] **Step 1: Write the failing eval**

Append to the `evals` array of `plugins/dev-workflows/skills/resolve-the-ticket/evals/evals.json`, with `id` = the highest `id` in the file + 1 (read it: `python -I -c "import json; print(max(e['id'] for e in json.load(open('plugins/dev-workflows/skills/resolve-the-ticket/evals/evals.json',encoding='utf-8'))['evals']))"`):

```json
{
  "id": <max id + 1>,
  "name": "the-plan-stage-hands-work-map-the-ticket-number-the-rows-and-the-stage",
  "prompt": "resolve the ticket https://dev.azure.com/Contoso/Ops/_workitems/edit/196 . You cannot reach the board from here, so here is what it holds. #196 User Story, Active, rev 8, parent #193 Feature (Active), children #394 Task (New) and #395 Task (Closed). Acceptance Criteria: 'Initial full seed populates all active cases.' and 'Transient network or API errors are logged with structured retry handling.' No description logic. docs/decision-map/ado-193-ips-api-feed/ exists; its tickets 196-match-key and 196-retry-shape are open and 195-sync-host is closed. The runbook documents/runbook-ado-193-ips-api-feed.md has a '## Stage - 2026-11-19 03:29 UTC - briefing done' block. I say yes to the stage you propose.",
  "expected_output": "The proposal is the plan stage with work-map, with the count of open Decision tickets as evidence. On the yes, the hand-off to work-map names the ticket (for #196), the row list (AC-1 and AC-2 quoted as written), the stage count plan (2/4), and asks work-map to open every message with the Frame line and to list the tickets for #196 first. The skill writes no Frame line of its own for work-map's messages.",
  "files": [],
  "assertions": [
    "Proposes the plan stage and names work-map, with '2 open Decision tickets' (or the same count in other words) as the evidence line",
    "On the yes, the hand-off says 'for #196' (the tracker ticket the map session is for)",
    "The hand-off carries the row list: AC-1 'Initial full seed populates all active cases.' and AC-2 'Transient network or API errors are logged with structured retry handling.', quoted as written",
    "The hand-off carries the stage count 'plan (2/4)'",
    "The hand-off asks work-map to open every message with the Frame line and to show the tickets for #196 first",
    "Does not load work-map before the yes, and does not resolve a Decision ticket itself",
    "The end-of-run line, when work-map stops, names the tracker ticket: '#196: N Decision tickets still open on docs/decision-map/ado-193-ips-api-feed/. Call resolve-the-ticket again for the next one.'"
  ]
}
```

- [ ] **Step 2: Check the eval fails against the current text**

Run: `grep -c "Frame line" plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md`
Expected: `0`.

- [ ] **Step 3: Add the hand-off to the offer table and the end-of-run line**

Replace

```
| has open Decision tickets | offer `work-map` for that map; on a yes load it; when it stops, end |
| has no open Decision ticket | the plan is over - propose do and verify |

Say in the offer that the run ends when that skill stops. End the run with one line: what
is left, and that the next call carries on - "3 Decision
tickets are still open on `docs/decision-map/ado-193-creditor-sync/`. Call
resolve-the-ticket again for the next one."
```

with

```
| has open Decision tickets | offer `work-map` for that map; on a yes load it; when it stops, end |
| has no open Decision ticket | the plan is over - propose do and verify |

Say in the offer that the run ends when that skill stops. End the run with one line: what
is left, and that the next call carries on - "#196: 3 Decision
tickets are still open on `docs/decision-map/ado-193-creditor-sync/`. Call
resolve-the-ticket again for the next one."

**What to hand `work-map`** on the yes, in the same request that loads it (ADRs 0392-0394,
0396). `work-map` opens every message to the person with its **Frame line** -
`#196 AC-2 · 196-match-key · question 1 of 2 · plan (2/4)` - and lists the tracker ticket's
own Decision tickets first; it can do neither without these:

| thing | value |
|---|---|
| the tracker ticket | `for #196` - the ticket this call is for; on a Feature call during the family walk, the child the walk is on |
| the row list | the rows of 4.1, quoted as written: `rows: AC-1 "…", AC-2 "…", L-1 "…"` - so the AC line in the Frame line means the same thing as in the check |
| the stage | `stage: plan (2/4)` |
| the ask | "open every message with the Frame line, and show the tickets for #196 first" |

The line itself is `work-map`'s to write on its own messages; this skill writes none for
it. A new point handed over as a ticket to add (the row above, ADR 0355) carries its letter
and its locator the way the `chart-map` table below has them, so the ticket's Question gets
its `Touches` sentence.
```

- [ ] **Step 4: Add the letter and the locator to the chart-map table**

Replace

```
| a group 1 point | a ticket of type `task`: the question, who must answer (or `not named`) |
| a group 2 point | a ticket of type `grilling` |
| a ticket's key | `<child id>-<short name>` - `195-shared-table`. A point that touches several children takes the first child's id, and its question names every ticket it touches |
| blocking edges | read from the briefing's "what depends on what" map |
```

with

```
| a group 1 point | a ticket of type `task`: the question, who must answer (or `not named`) |
| a group 2 point | a ticket of type `grilling` |
| every point | its letter and its locator, as one line: `C · #196 AC-4 · <the question> · <who must answer>`. `chart-map` opens each question with its **Frame line** from these (`#196 AC-4 · briefing point C · chart map ado-193-… · question 3 of 4 · plan (2/4)`, ADR 0397) and writes the locator into the ticket's `Touches` sentence |
| a ticket's key | `<child id>-<short name>` - `195-shared-table`. A point that touches several children takes the first child's id, and its question names every ticket it touches - the `Touches` sentence, last in the Question: `Touches #195 AC-2 and #196.` (ADRs 0346, 0395) |
| the stage | `stage: plan (2/4)` |
| blocking edges | read from the briefing's "what depends on what" map |
```

- [ ] **Step 5: Check every assertion against the new text**

Run:

```bash
cd /c/Repo/workflow-daily-work && f=plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md
grep -n "^\*\*What to hand \`work-map\`\*\*" "$f"
grep -n '"#196: 3 Decision' "$f"
grep -n "C · #196 AC-4 · <the question>" "$f"
grep -n "| the stage | \`stage: plan (2/4)\` |" "$f"
grep -c "Frame line" "$f"
python -I -c "import json; d=json.load(open('plugins/dev-workflows/skills/resolve-the-ticket/evals/evals.json',encoding='utf-8')); ids=[e['id'] for e in d['evals']]; print(len(ids), len(set(ids))==len(ids))"
```

Expected: a line number for the first three `grep`s, `2` for the fourth (one in each table), a count of at least 3 for the fifth; `18 True`.

- [ ] **Step 6: Commit**

```bash
cd /c/Repo/workflow-daily-work
git add plugins/dev-workflows/skills/resolve-the-ticket/SKILL.md plugins/dev-workflows/skills/resolve-the-ticket/evals/evals.json
git commit -m "feat(resolve-the-ticket): the plan stage hands the map skills the ticket, the rows, the point letters and the stage for the Frame line (ADRs 0392-0397)"
```

---

### Task 4: versions, the generated skills tree, the check

**Files:**
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json:4` (`"version": "0.69.0"` → `"0.70.0"`)
- Modify: `plugins/decision-map/.claude-plugin/plugin.json:4` (`"version": "0.14.0"` → `"0.15.0"`)
- Modify: `.claude-plugin/marketplace.json:36` (`"version": "0.69.0"` → `"0.70.0"`, the dev-workflows entry) and `.claude-plugin/marketplace.json:158` (`"version": "0.14.0"` → `"0.15.0"`, the decision-map entry)
- Modify (generated): `skills/resolve-the-ticket/`, `skills/work-map/`, `skills/chart-map/`

**Interfaces:**
- Consumes: the three committed skill texts of Tasks 1-3.
- Produces: a `skills/` tree that `check_skills_tree.py` accepts; the versions Task 5's install note quotes.

- [ ] **Step 1: Bump the four version strings**

Edit the four lines named above. Then run:

```bash
cd /c/Repo/workflow-daily-work && python -I - <<'EOF'
import json
m=json.load(open('.claude-plugin/marketplace.json',encoding='utf-8'))
mv={p['name']:p['version'] for p in m['plugins']}
for p in ['dev-workflows','decision-map']:
    pv=json.load(open(f'plugins/{p}/.claude-plugin/plugin.json',encoding='utf-8'))['version']
    print(p, pv, mv[p], 'OK' if pv==mv[p] else 'MISMATCH')
EOF
```

Expected: `dev-workflows 0.70.0 0.70.0 OK` and `decision-map 0.15.0 0.15.0 OK`.

- [ ] **Step 2: Regenerate the skills tree and restore the CRLF-only changes**

```bash
cd /c/Repo/workflow-daily-work
python scripts/generate_skills_tree.py --repo .
git diff --ignore-cr-at-eol --stat -- skills/
```

Expected: the stat lists only files under `skills/resolve-the-ticket/`, `skills/work-map/` and `skills/chart-map/`. Then restore every other skill's line endings:

```bash
cd /c/Repo/workflow-daily-work && python -I - <<'EOF'
import subprocess
changed=subprocess.run(['git','diff','--ignore-cr-at-eol','--name-only','--','skills/'],capture_output=True,text=True).stdout.split()
keep={p for p in changed if p.split('/')[1] in ('resolve-the-ticket','work-map','chart-map')}
allmod=subprocess.run(['git','diff','--name-only','--','skills/'],capture_output=True,text=True).stdout.split()
restore=[p for p in allmod if p not in keep]
if restore: subprocess.run(['git','checkout','--',*restore],check=True)
print('kept',sorted(keep)); print('restored',len(restore))
EOF
git status --short -- skills/
```

Expected: `kept` names only the three skills' files; `git status` shows only those (plus `skills/work-map/evals/evals.json` as new, if the generator copies evals).

- [ ] **Step 3: Run the check**

Run: `python scripts/check_skills_tree.py --repo .`
Expected: exit code 0 and no findings. If it reports findings, run the generator again and repeat Step 2; never edit `skills/` by hand.

- [ ] **Step 4: Commit**

```bash
cd /c/Repo/workflow-daily-work
git add .claude-plugin/marketplace.json plugins/dev-workflows/.claude-plugin/plugin.json plugins/decision-map/.claude-plugin/plugin.json skills/resolve-the-ticket skills/work-map skills/chart-map
git commit -m "chore(dev-workflows, decision-map): manifests 0.70.0 and 0.15.0, and the skills tree for the Frame line"
```

---

### Task 5: design records, the live copies, and the first real run

**Files:**
- Commit (already written on 2026-11-24, uncommitted): `CONTEXT.md`, `docs/adr/workflow-daily-work-0338-…md` (amendment), `docs/adr/workflow-daily-work-0392-…md` to `0397-…md`, `docs/superpowers/specs/2026-11-24-frame-line-design.md`, `docs/superpowers/plans/2026-11-24-frame-line.md`
- Overwrite (outside git): `~/.claude/skills/resolve-the-ticket/`, `~/.claude/skills/work-map/`, `~/.claude/skills/chart-map/`

**Interfaces:**
- Consumes: the generated tree of Task 4.
- Produces: live skill copies equal to the generated tree except the one known path rewrite (measured 2026-11-24: the installed `resolve-the-ticket` differs from `skills/resolve-the-ticket/SKILL.md` only in `skills/why-this-logic/references/splitting-rules.md` → `~/.claude/skills/why-this-logic/references/splitting-rules.md`).

- [ ] **Step 1: Commit the design records**

Only the files of this design; leave the pre-existing untracked ADRs `0290` and `0291` and `daily-state.md` alone:

```bash
cd /c/Repo/workflow-daily-work
git add CONTEXT.md docs/adr/workflow-daily-work-0338-the-one-entry-is-built-by-changing-resolve-the-ticket-only.md docs/adr/workflow-daily-work-0392-*.md docs/adr/workflow-daily-work-0393-*.md docs/adr/workflow-daily-work-0394-*.md docs/adr/workflow-daily-work-0395-*.md docs/adr/workflow-daily-work-0396-*.md docs/adr/workflow-daily-work-0397-*.md docs/superpowers/specs/2026-11-24-frame-line-design.md docs/superpowers/plans/2026-11-24-frame-line.md
git commit -m "docs(frame-line): design session - ADRs 0392-0397, ADR 0338 amended, the Frame line glossary term, spec and plan"
```

- [ ] **Step 2: Copy the three generated skills to the live folder, with the path rewrite**

```bash
cd /c/Repo/workflow-daily-work && python -I - <<'EOF'
import os, shutil, hashlib
home=os.path.expanduser('~'); live=os.path.join(home,'.claude','skills')
def h(p): return hashlib.sha256(open(p,'rb').read().replace(b'\r\n',b'\n')).hexdigest()[:10]
for sk in ['resolve-the-ticket','work-map','chart-map']:
    src=os.path.join('skills',sk); dst=os.path.join(live,sk)
    for root,dirs,files in os.walk(src):
        dirs[:]=[d for d in dirs if d!='__pycache__']
        rel=os.path.relpath(root,src); os.makedirs(os.path.join(dst,rel),exist_ok=True)
        for fn in files:
            s=os.path.join(root,fn); d=os.path.join(dst,rel,fn)
            if fn.endswith('.md'):
                t=open(s,encoding='utf-8').read().replace('`skills/why-this-logic/references/splitting-rules.md`','`~/.claude/skills/why-this-logic/references/splitting-rules.md`')
                open(d,'w',encoding='utf-8',newline='').write(t)
            else: shutil.copyfile(s,d)
    print(sk,'SKILL.md generated',h(os.path.join(src,'SKILL.md')),'live',h(os.path.join(dst,'SKILL.md')))
EOF
```

Expected: three lines; `work-map` and `chart-map` hashes equal; `resolve-the-ticket` differs only by the rewrite (confirm with a unified diff of the two files: exactly one changed line, the `splitting-rules.md` path).

- [ ] **Step 3: Verify the live copies carry the change**

```bash
grep -c "Frame line" ~/.claude/skills/work-map/SKILL.md ~/.claude/skills/chart-map/SKILL.md ~/.claude/skills/resolve-the-ticket/SKILL.md
ls ~/.claude/skills/work-map/evals/evals.json
```

Expected: every count ≥ 1; the evals file exists.

- [ ] **Step 4: The first real run (Pon, in `C:\Repo\MG-AI-Creditor-Enquiry-Agent`)**

This is the measured test of the spec's last Tests row; it needs Pon at the keyboard and is not run by the executor. Hand Pon this note:

> In a new session in `C:\Repo\MG-AI-Creditor-Enquiry-Agent`, run `/resolve-the-ticket` with `https://dev.azure.com/MackayGoodwin/Elevate/_workitems/edit/196` and say yes to the plan stage. Expected: the first line of work-map's first message is `#196 · map ado-193-ips-api-feed · plan (2/4)`, the frontier opens with `Tickets for #196 - 7 of 10 open` (the count on the day), and the first grilling question opens `#196 AC-<n> · <key> · question 1 of … · plan (2/4)`. If any message opens with something else, that is a defect of Task 1 or Task 3: note the message and the missing part.

---

## Self-review

**Spec coverage.** The Frame line grammar and six examples → Task 1 Step 4, Task 2 Step 4. Where the facts come from (ticket file, not `read`) → Task 1 Step 4. resolve-the-ticket's four hand-off rows → Task 3 Steps 3-4. work-map Step 1 group, Step 3 rule, Step 6 report → Task 1 Steps 5-7. chart-map paragraph → Task 2 Step 4. Edge cases: direct call (Task 1 eval 1, Task 2 "direct call" row), no Touches sentence (Task 1 Step 4 table), several tracker tickets (Task 1 Step 5), AC not in the row list (Task 1 Step 4), GitHub body (Task 1 Step 4), family walk (Task 3 Step 3), M unknown (Task 1 eval 1). Tests: three evals (Tasks 1-3), the generated tree and check (Task 4), the live copies (Task 5 Steps 2-3), the real run (Task 5 Step 4). Files and versions → Task 4. Design records → Task 5 Step 1.

**Placeholders.** The one `<max id + 1>` in Task 3 Step 1 is computed by the command given beside it. No "TBD", no "similar to".

**Consistency.** The hand-off words `for #196`, `rows: AC-1 "…"`, `stage: plan (2/4)` are the same in Task 1 (consumed), Task 3 (produced) and both evals. The section names `## The Frame line` (work-map) and `**The Frame line**` (chart-map) are what Task 3's text refers to. The point line `C · #196 AC-4 · <the question> · <who must answer>` is the same in Task 2 (consumed) and Task 3 (produced).
