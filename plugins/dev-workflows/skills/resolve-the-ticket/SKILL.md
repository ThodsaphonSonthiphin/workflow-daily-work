---
name: resolve-the-ticket
description: 'The one entry for working a ticket (Azure DevOps or GitHub Issues). Give it the ticket URL: it reads the ticket, its parent and children and the files in the repo, says which of four stages comes next - BRIEFING, PLAN, DO AND VERIFY, CHECK - and asks once. It does no work itself: at each stage it offers the skill that does (chart-map / work-map, guide-and-verify, sp-writing-plans) and loads it on a yes. CHECK: one row per Acceptance Criteria line, logic rule and child ticket, each with its test and result, then READY or NOT READY and, on READY, a closing comment to paste. Use for "resolve the ticket", "work on this ticket", "start this ticket", "what is next on this ticket", "is this ticket ready to resolve", "check before I resolve", "brief me on this ticket", "ticket นี้ resolve ได้ยัง", "เช็คก่อน resolve", "อ่าน ticket นี้ให้หน่อย", "ทำ ticket นี้ต่อ". Never writes to the tracker. Not dual-verifier (one diff).'
effort: max
---

# Resolve the ticket

A ticket gets set to Resolved on "I think it is done". A week later it is reopened, because
one rule in its details had no passing test on that day. This skill is the one door for a
ticket: call it with the ticket's URL at any time, and it says where the ticket is and what
comes next.

**The failure this prevents:** a ticket resolved over a rule nobody tested, a pass that is
older than the last change, a child task nobody did - and a person who has to remember
which skill comes when.

## What it never does

- It **does no work itself.** It builds nothing and fixes nothing. The work happens inside
  the skill it loads, under that skill's own rules (ADR 0339).
- It **never loads a skill that does work without a yes.** It names the skill, says why,
  and waits. `ticket-trace` and `read-picture` are read helpers: they are loaded to read
  the ticket and need no yes.
- It **never writes to the tracker** - no comment, no State change, no ticked box. The
  person does those. A skill it loads follows its own rules: `guide-and-verify` records its
  readings on the ticket as it goes.
- It **never writes a runbook.** `guide-and-verify` creates it.

Its only writes are two kinds of dated block appended to the ticket's runbook: one stage
block after a briefing (only when the runbook exists), and one block per check.

## The flow

```
 ┌──────────────────────────────────┐
 │ 0. Wait for the ticket URL       │
 └────────────────┬─────────────────┘
                  ▼
 ┌──────────────────────────────────┐
 │ 1. Read ticket, parent, children │
 │ 2. Find files by ticket number   │
 └────────────────┬─────────────────┘
                  ▼
 ┌──────────────────────────────────┐
 │ 3. Say which stage comes next,   │
 │    with one line of evidence.    │
 │    Ask once. The person may name │
 │    another stage.                │
 └──┬─────────┬──────────┬────────┬─┘
    ▼         ▼          ▼        ▼
 Stage 1   Stage 2    Stage 3   Stage 4
 BRIEFING  PLAN       DO AND    CHECK
 chat      chart-map  VERIFY    rows +
           work-map   guide-    verdict
                      and-verify
                      or sp-
                      writing-plans
```

## 0. Open - wait for the URL

One thing is needed: the **ticket's URL**. If the invocation did not give it, ask:

> The ticket's URL, please.

Do not ask which stage. Read nothing until you have the URL. A bare number is not enough -
the URL names the tracker, the organization and the project in one string, so the right
number is never read in the wrong project. Do not take the organization or project from an
environment variable.

| URL | tracker |
|---|---|
| `dev.azure.com/<org>/<project>/_workitems/edit/<id>` | Azure DevOps |
| `github.com/<owner>/<repo>/issues/<n>` | GitHub Issues |
| anything else | say "I cannot read this tracker." and stop |

If the person named a stage in the call ("brief me", "check", "start the work"), that is
the stage: steps 1 and 2 still run, step 3 says one line and does not ask.

## 1. Read the ticket family

| who | how much |
|---|---|
| the ticket | in full |
| its direct parent | in full |
| every direct child | in full |
| predecessor, successor, related tickets | type, title and State only |
| the grandparent and above | not read |

**In full** means: type, title, State, revision (on GitHub: `updatedAt`), description (for an Azure DevOps Bug also
the repro steps), Acceptance Criteria, every comment, and **every attached image**. Fetch
one ticket the way `ticket-trace` does it - load that skill through your harness's
mechanism and follow its Operation B steps 4 and 5; images go through `read-picture`
(kind `requirement`). An image is often the whole requirement: never report "the
description is empty" without opening it.

The parent, the children, the other links and which States count as done are in
`references/ticket-family.md` - use its commands as written.

If you cannot reach the tracker, say so and ask the user to paste the ticket's fields. What
they paste is the ticket for this run; say in the output that it came through them.

## 2. Find the files, list them, read them

Search the project you run in for the ticket's number and each child's number:

1. file and folder names (`runbook-ado-151-…`, `151-…`, `ado-151-…`)
2. file contents (`#151`, `AB#151`, `ado-151`)
3. commit messages (`git log --all --grep`)
4. every file the ticket or the runbook names

Match the number whole: `151` does not match `1510`, a date or a GUID. Drop a hit that only
shares the digits.

Print the list before reading, grouped by kind:

```
Files for #151 (and child #297):
 runbook   documents/runbook-ado-151-overduereport-flow.md
 why       docs/why/151-loggingstatus-filter.md
 register  docs/why/requirements.md  (R-001)
 snapshot  documents/snapshots/ado-151-before/  (4 files)
 commits   7 with "151" in the message
```

Then read the documents. A snapshot folder is listed with its file count, not read file by
file.

**No runbook found.** Say so in one line. What happens next depends on the stage that step 3 proposes or the call names:

- **briefing or plan** - go on without one. A briefing with no runbook is chat only.
- **do and verify** - for click work `guide-and-verify` creates it (Stage 3). Code work
  gets none there; its check takes the route below.
- **check** - the work was done with no runbook. Hand off to `guide-and-verify` (load it
  through your harness's mechanism, on the person's yes) and ask it for the runbook
  **file** only - in its own shape and the project's own naming, holding the title, the
  ticket link, the file list and the boundary line - with no baseline measurement and
  nothing written to the ticket: a baseline cannot be measured after the change. Give it
  what you have already read as its head start; your block is then appended to the file it
  creates (4.6). Do not write a runbook yourself, do not use the parent's runbook, and do
  not go on as if there were none. Continue when the runbook exists.

## 3. Say which stage comes next

A ticket has four stages. Each ends on something a file shows:

| stage | what happens | ends when |
|---|---|---|
| 1. briefing | the ticket, its family and its files are read; the open points are shown | the person has read it and says go on |
| 2. plan | the open points of groups 1 and 2 are decided on a Decision map | the map has no open Decision ticket (no such points: skipped) |
| 3. do and verify | the work is done step by step, each step measured | every step has a recorded result |
| 4. check | one row per AC line, logic rule and child; READY or NOT READY | READY, and the person resolves the ticket |

Read the table below from the top. The first row that fits is the proposal:

| what the files show | propose | the evidence line names |
|---|---|---|
| the last `## Resolve check` block says READY and nothing that can make it stale changed after it - no commit to its files, no edit to the ticket's requirement text (a comment or a State change is not one, ADR 0331) | nothing - say it was READY on that date and the person resolves it on the board; offer a new check | the block's date |
| the last `## Resolve check` block says NOT READY and no work is recorded after it | the gap's skill (4.5), else the check again | the block's gap lines |
| the work record is complete - click work: the runbook has steps and every one has an outcome line; code work: every task of the plan has a `Task <N>: complete` line in the executing skill's ledger (no ledger left after a run: ask the person once whether the run finished). Work of both kinds: both records | check | the count of steps |
| the work record is started and not complete | do and verify, at the first step with no result (code work: the first task with no complete line) | which steps have a result and which is first without one |
| the Decision map for this ticket has open Decision tickets | plan | the count of open tickets |
| the briefing is known to be done - a `## Stage` block in the runbook, or a Decision map with no open ticket | plan when that block counts open points in group 1 or 2 and no map exists; else say "Plan: skipped, nothing to decide" and propose do and verify | the block's date or the map's path |
| none of the above | briefing | "no runbook and no map found" |

**The work record** is what the loaded skill writes, never a file of this skill
(ADR 0343): for click work the runbook's steps and outcome lines; for code work the plan
file under `docs/superpowers/plans/`, the executing skill's ledger and `git log --all` (the work may sit on a branch that is not merged yet).

**The Decision map for a ticket** is found like the runbook - by number, matched whole: a
folder under `docs/decision-map/` whose name carries the Feature's number
(`ado-193-…`, `gh-12-…`), or the ticket's own number when no Feature is above it.

Say the proposal in this shape, then wait:

```
Next for #195: do and verify, at step 3 - click work, with guide-and-verify.
Steps 1-2 have a result; step 3 has none - it may have partly landed, so it is measured first.
Go on? Or name another stage.
```

One question, once. A yes starts the stage. Another stage's name starts that stage. Never
start a stage on silence.

## Stage 1 - the briefing

Chat, in this order:

1. **The ticket** - one line: type, id, title, State, revision, URL. On GitHub the revision
   is `updated <timestamp>`, from `updatedAt`.
2. **The family** - a table: parent, children, linked tickets, each with type, title, State.
3. **What it asks** - every AC line and every logic rule, quoted **as written**, each with
   a locator (`#151 AC-2`, `#151 description`, `#151 image <name>`).
4. **The files** - the list from step 2, and which to open first (the runbook, when it has
   steps).
5. **Open points** - an AC line that names something no file mentions; a linked ticket that
   is still open; a place where the ticket and its parent disagree; a count, a name or a
   rule in the ticket that its own attachments or an approved decision contradict. Print
   them in the shape below, never as one flat list.

#### The open points - sorted by what they do to the work (ADR 0336)

A flat list makes the person work out for themselves which point stops which task. Sort
every point into exactly one of four groups, in this order, and give each point a letter
(`A`, `B` …) so the map and the order can name it:

| group | a point goes here when | columns |
|---|---|---|
| **1. Fix before the work starts** | a task or an AC cannot be done until someone answers | point · touches (ticket / AC) · who must answer · if it is not fixed |
| **2. Decide while designing** | the work can start, but a design choice is open | point · touches · what must be decided |
| **3. Rules to keep** | it is a thing not to do, not a thing to resolve | the rule and its reason, one line each |
| **4. Touches no task** | it blocks no build - it matters at the check, or it is housekeeping | the point, and "touches no task" or "matters at the check before resolve" in words |

Rules for the table:

- **Touches** names the tickets and AC lines the point affects - of the ticket itself, its
  children and its linked tickets. A point that touches nothing says so in group 4; it is
  never dropped.
- **Who must answer** is a name or a role the ticket, the runbook or the project's files
  give. None found: write `not named`. Never guess a person.
- **If it is not fixed** is one concrete consequence ("AC-1 cannot pass as written"), not
  "may cause problems".
- A point the person can settle alone, under a written decision, goes in group 2 and says
  so ("no one to wait for - follow decision D6").
- An empty group is printed with `none`.

Then **what depends on what** - one small monospace map, points and tickets as nodes, an
arrow meaning "must be done before". Only arrows a file supports, or that follow from the
table (a point that touches a ticket comes before it); mark a dependency you inferred from
a ticket's wording with `(inferred)`:

```
 A sandbox or production ─┐
 B fixed outbound IP ─────┼─▶ #195 ─┐
 C password ──────────────┘         ├─▶ #196
 D shared table ────────────────────┘
 D + E ticket counts ───────────────▶ #197
```

Then **a suggested order** - a short numbered list read off the map: first send every
question of group 1 in one round (name who gets which letters), then the task nothing
waits on, then each task as its points close, last the task that waits on the most. It is a
suggestion: say so in one line, and build nothing.

Show a rule with logic the way the project asks for it (some projects fix a flowchart
shape in their `CLAUDE.md` / `AGENTS.md` - follow it). Print no check table and no verdict.

**After the briefing.** When the ticket has a runbook, append one block to it, after its
last section, and never edit a line above it:

```
## Stage - <date> <time UTC> - briefing done

Ticket #<id> rev <n> (GitHub: updated <timestamp>). Open points: group 1: <count>, group 2: <count>.
```

When the ticket has no runbook, write no file: the next call proposes the briefing again,
which costs nothing (ADR 0341).

Then propose the next stage in the same turn and wait for the yes: plan when group 1 or 2
has a point; else say "Plan: skipped, nothing to decide" and propose do and verify.

## Stage 2 - the plan

The open points of **group 1** and **group 2** of the briefing are decided on a Decision
map (ADR 0345). Groups 3 and 4 never become Decision tickets. When both groups are empty,
say so in one line - "Plan: skipped, nothing to decide" - and propose do and verify.

Offering `chart-map` needs the briefing's open points - their letters, what each touches,
and the "what depends on what" map. If they are not in this conversation, work them out
again from the ticket and the files and print them before the offer; the `## Stage` block
holds only the counts. A call that offers `work-map` does not print them again.

**The map skills must be there.** The stage needs `chart-map` and `work-map`, which ship in
another plugin. If either skill is not available in this session, say so, print this, and
end the run (ADR 0349). Do not decide the points another way, and do not skip the stage:

```
The plan stage needs the chart-map and work-map skills, and they are not installed.
- Claude Code:  /plugin install decision-map@workflow-daily-work
- npx skills:   npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill chart-map
                npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill work-map
- Antigravity:  the decision-map plugin has no installer. Copy the folders skills/chart-map
                and skills/work-map from the workflow-daily-work repo into your skills directory.
Install them and call resolve-the-ticket again - or name another stage.
```

**One call does one of three things, then the run ends** (ADR 0348). `chart-map` ends its
session after charting and `work-map` stops after one decision; this skill ends there too.

| the ticket's Decision map | this call |
|---|---|
| does not exist | offer `chart-map`; on a yes load it through your harness's mechanism; when it stops, end |
| has open Decision tickets | offer `work-map` for that map; on a yes load it; when it stops, end |
| exists, and a child's briefing has a group 1 or 2 point that is not on it | offer `work-map` for that map and hand it the new points as tickets to add through its own gate; when it stops, end (ADR 0355) |
| has no open Decision ticket | the plan is over - propose do and verify |

Say in the offer that the run ends when that skill stops. End the run with one line: what
is left, and that the next call carries on - "3 Decision
tickets are still open on `docs/decision-map/ado-193-creditor-sync/`. Call
resolve-the-ticket again for the next one."

**What to hand `chart-map`.** One map per Feature, shared by all its children; a ticket
with no Feature above it gets its own (ADR 0346):

| thing | value |
|---|---|
| the map's folder | `<tracker>-<Feature id>-<short name>` - `ado-193-creditor-sync`, `gh-12-export` |
| a group 1 point | a ticket of type `task`: the question, who must answer (or `not named`) |
| a group 2 point | a ticket of type `grilling` |
| a ticket's key | `<child id>-<short name>` - `195-shared-table`. A point that touches several children takes the first child's id, and its question names every ticket it touches |
| blocking edges | read from the briefing's "what depends on what" map |

`chart-map` asks for the destination and runs its own gate; do not answer its questions
for the person. On a map that already exists `chart-map` runs only its own sweep; new points go through `work-map` (the table above). On a small ticket `chart-map` may say no map is needed and name `grill-then-plan` - say
that to the person as it is, and end the run with one line: "chart-map found nothing to
chart. The next call proposes the plan again - name do and verify then to go on."
Nothing records that stop, so the person carries it (ADR 0354).

A **closed** Decision ticket is the record of the decision (ADR 0347). The check reads it
(4.2).

## Stage 3 - do and verify

This skill does not do the work. It says what kind of work the ticket is, offers the skill
for it, and loads that skill on a yes (ADR 0339).

| the ticket's work | the skill to load | the proof it leaves for the check |
|---|---|---|
| a person must click in a console, a portal, a settings page | `guide-and-verify` | runbook steps and outcome lines |
| code the agent can write | `sp-writing-plans`, which hands off to its own executing skill | tests in the repo |
| both | each part goes to its own skill, the click part first unless the briefing's order says otherwise | both |

Say the kind with the proposal, in the same question: "#195 is click work (a flow in the
portal) - load `guide-and-verify`?" The person may correct the kind.

**Before loading, write the row list** - the rows of 4.1 (`AC-1`, `L-1` …), quoted as
written. Then hand the loaded skill three things:

1. what you have already read - the ticket, its parent and children, the file list;
2. the row list, with this request: "name on each step (or task, or test) the rows it
   proves, for example `Step 3 - set the schedule (AC-2)`";
3. for a call after a break, the evidence line of section 3: which steps have a result and which
   is the first without one - "measure it first; do not do it again blind" (ADR 0343).

Ask the loaded skill, in the same request, to say before the first step which rows no
step (or task, or test) names - "L-4 has no step that proves it" - so the gap is seen
before the work, not at NOT READY.

**`guide-and-verify`** runs in full: it measures the baseline before the first
instruction and creates the runbook when the ticket has none (ADR 0341). Do not ask it for
a file only here. Its own fields are what the check reads (ADR 0340):

| the check needs | `guide-and-verify` writes |
|---|---|
| Given | the baseline |
| When | the step's **Do** lines |
| Then | the assertion declared before the person acts |
| result and date | the outcome line with its measurement and time |

**`sp-writing-plans`** takes the ticket's AC lines and logic rules as its requirements.
No before / after measurement is asked of code work: a test written first, failing before
and passing after, is its measurement (ADR 0342).

**After a break in code work** the plan file already exists: offer the executing skill
that was running it (`sp-subagent-driven-development` or `sp-executing-plans`) on that
plan, not `sp-writing-plans`, with the evidence line of section 3 (ADR 0343).

When the loaded skill is done, propose the other part's skill when the work is of both
kinds, else the check - and wait for the yes. When it stops
part-way, say what is left in one line and end the run.

## Stage 4 - the check

### 4.1 The rows

One row per:

- **AC line** - each Acceptance Criteria statement, one per clause that binds behaviour (a
  value, a condition, a trigger, a recipient, an ordering). A sentence with "and" between
  two obligations is two rows; a heading, an example or a rationale is none. The full rules
  are `why-this-logic`'s:
  `${CLAUDE_PLUGIN_ROOT}/skills/why-this-logic/references/splitting-rules.md`.
  Use its *Split* and *Do not split* tables for logic rules and its *Splitting a requirement
  text* section for AC lines. Its row 0 (the origin of the text) and its twelve-row cap
  belong to why-this-logic's own run and do not apply here.
- **logic rule** - each decision point in the ticket's details: a filter, a threshold, a
  mapping, a default. Same splitting rules: a filter `f eq A or f eq B` is two rows - the
  term (why filter on `f` at all) and the codes `A` / `B` together.
- **child** - each direct child ticket, with its State.

Quote each row as written, with its locator. Name them `AC-1`, `AC-2` … and `L-1`, `L-2` …
in the order the ticket has them; a child row is named by its id. When the project has
`docs/why/requirements.md` and the statement is registered there, put its ID beside the row.
Write the row list before you look for any test.

**A later check on the same ticket:** read the last `## Resolve check` block in the runbook
first. If the ticket's revision is the same (on GitHub: `updated <timestamp>` from
`updatedAt` is the same), keep the rows; a row that was a pass is kept only when its proof
is still where the block says and it is not stale now - re-check every other row. A
**told** row is asked again: its only proof was the earlier block. If the revision changed,
split the rows again. An earlier block is never the proof of a pass; the test result it
points at is.

### 4.2 The result of one row

Ask these in order and stop at the first that decides:

```
 a test for this row?  ── none ───────────────▶ NO TEST
        │ yes
 does it prove the row?
 (Given / When / Then) ── a part differs ─────▶ NO TEST (names the part)
        │ all three match
 its result?           ── fail ───────────────▶ FAIL
        │ pass
 older than the last
 change to the thing?  ── yes ────────────────▶ STALE
        │ no
 built as the ticket   ── yes ────────────────▶ PASS + mark
 says?                 ── no, written decision ▶ PASS - differs by decision
                       ── no, no decision ────▶ DIFFERS
```

**Where a test is found.** The runbook's steps and Outcome log, a ticket comment, a test
file in the repo, a case in a test-case suite, the register's *tested by* cell. A step,
task or test that names the row (`Step 3 - set the schedule (AC-2)`) is the first place to
look - and it is still compared part by part below; a tag never replaces that comparison
(ADR 0340). Nothing found: ask the user once, naming every such row - "Rows L-1 and AC-3 -
no test found in the runbook, the comments or the repo. Was either tested?"

**Does the test prove the row? Given / When / Then (ADR 0335).** A test that is only
*about* the same thing proves nothing. Break the row into three parts, break the test into
the same three, and compare part by part:

| part | the question | example row: "a caller who does not agree is disconnected" |
|---|---|---|
| **Given** | the state before | the caller was asked for consent |
| **When** | the event | the caller says "I don't agree" |
| **Then** | the result that must be seen | the call ends |

All three match: the test proves the row - go on to its result. One part differs: the row
is **no test**, and the row says which part - `no test - When differs: test says "no", row
says "I don't agree"`. A part the test does not state is a part that differs. Do not stretch
a test to fit: "close enough" is how a rule with no test gets resolved. A **told** row gets
the same three questions - ask the user what state, what event and what result they tested.

When what was built differs from the ticket under a written decision (**Differs**, below),
compare the test with the row as the decision states it; when all three parts match and
the test passes, the row is `pass - differs by decision <id>` (ADR 0324).

Write one reasoning line per AC and logic row under the table (4.3), so the person can see
why each test was paired with its row.

**Boundary values - a note, never a verdict.** When a row holds a threshold or a range
("older than 7 days"), look at which values the test used. If no value sits on the edge (6,
7, 8 days), add one line under the verdict: `AC-2: tested at 30 days only - the edge (7) is
not tested`. It does not change the result of the row.

**The mark on a pass - exactly one:**

| mark | proof |
|---|---|
| **cited** | a result written in the runbook, a ticket comment or a test file - give the locator and the date |
| **measured** | a test you ran in this session - give the command and its result line |
| **told** | the user says it was tested - write `told: <who>, <date>` |

A told pass counts. It is never shown as anything else.

A test run in this session is **measured**, even when the test lives in a file; **cited** is
for a result someone wrote down earlier.

**Stale.** Compare the pass's date with the last change you can see: a git commit on the
file (`git log -1 --format=%cI -- <file>`), a modified date written in the runbook or a
snapshot, the last edit to the ticket's requirement text - its description, acceptance
criteria or repro steps (see `references/ticket-family.md`); a comment, a tag or an
assignment is not a change. A pass older than the change is **stale**: show both
dates (`passed 2026-11-10; changed 2026-11-12`). It stops being stale when the test is run
again, or when the user says the change does not touch this row (then `told`). A pass with
no date cannot be compared: show `pass (no date)`. A change date that only the live system
holds needs one read-only query - write the exact query and ask once per query, per run:

> The last change to `<thing>` is only in the live system. This read-only query shows it:
> `<the query>`
> Run it? On no, the row shows "change date not checked".

Never write to a live system. A yes is for that one query.

**Differs.** Compare what the ticket says with what was built (the code, the flow
definition, a snapshot, the runbook's design). Something built that the ticket does not state - an extra
recipient, an extra condition - is a difference too. When they differ, look for a **written,
approved decision** that covers the difference - a **closed** Decision ticket on the
ticket's Decision map (the record, ADR 0347), an ADR, a runbook decision, a ticket
comment, with who approved it. Found: `pass - differs by decision <id>`, with its locator
(for a Decision ticket: its key and path), when the test passes. An open or claimed
Decision ticket is not a decision. Not found: **differs** - a passing test of the wrong rule is not a
pass. The user approving it now, in this session, closes the row as `told`.

**Child rows.** A child whose State is a done State (see `references/ticket-family.md`) is
`done`. A child in State `Removed` is shown `removed` and left out of the verdict - it is
neither done nor open (`references/ticket-family.md`, ADR 0330). Any other State is **open**, unless the user says it stays open on purpose - then
`open on purpose - told: <who>, <date>`. Do not check the child's own AC here.

### 4.3 The table and the verdict

Print in monospace:

```
row    what the ticket says        test   result
AC-1   runs Mon-Fri 08:00          S3c    pass   cited (runbook:255, 2026-11-09)
L-2    cut-off = UTC day - 7       S3c    pass   differs by decision D2 (runbook:70)
AC-3   PDF digest to admin         S6c    STALE  passed 2026-11-10; changed 2026-11-12
L-4    status Created or Partial   -      NO TEST
#297   child Task                  -      OPEN   State = New

Why each test proves its row:
AC-1  Given the flow is on / When it is Monday 08:00 / Then it runs
      S3c: flow on / pinned Monday 08:00 / run recorded - all three match
L-4   Given a row with status Partial / When the flow lists rows / Then it is selected
      S4c: only status Created rows - Given differs -> no test

READY TO RESOLVE: NO
```

The *Why* block has one entry per AC and logic row: the row's Given / When / Then, then the
test's, then which parts match. Child rows need none.

| result | counts for READY |
|---|---|
| pass (cited / measured / told) | yes |
| pass - differs by decision | yes |
| pass (no date) | yes - counted with the told rows |
| change date not checked | yes - counted with the told rows |
| child done, or open on purpose (told) | yes |
| removed (child) | not counted - left out of the verdict |
| no test, fail, stale, differs, open | no |

READY needs every row that is not `removed` to count. When told rows, `pass (no date)` rows
or `change date not checked` rows exist, the verdict reads
`READY TO RESOLVE: YES (N rows rest on your word)`, N counting all three. A linked ticket that is an open Bug is
pointed out in one line under the verdict; it does not change it.

### 4.4 On READY - draft the closing comment

Give the comment as raw Markdown in **one code block**, ready to paste. If the project's
`CLAUDE.md` / `AGENTS.md` fixes a comment format, use it. Otherwise:

```
## Ready to resolve - <date>, <time> UTC
Checked against the runbook and the repo (read-only).

| Item | Result |
|---|---|
| AC-1 <statement> | pass - cited (<locator>, <date>) |
| L-2 <statement> | pass - differs by decision <id> |
| AC-3 <statement> | pass - told (<who>, <date>) |

### Built differently from the ticket, by decision
- L-2: <what was built>, decision <id> (<locator>)

### Left open on purpose
- #<child>: <reason as the user gave it>

Details in the runbook: <path>
```

Leave out a `###` section that has no line. Then say:

> Paste this on the ticket, tick the acceptance criteria, and set the State yourself (on
> GitHub: close the issue). I have changed nothing on the board.

Then record the check (4.6).

### 4.5 On NOT READY - record, then offer the next skill

Draft no comment. Work out the gap lines - at most one per kind of gap, naming every row
of that kind - then record the check with them (4.6), then print them all:

| gap | the line offers |
|---|---|
| no test | `generating-test-cases` |
| fail | `debug-mantra` |
| stale | the test step to run again (or: say the change does not touch the row) |
| differs, no decision | `work-map` when the ticket's Decision map holds an open Decision ticket for it (ADR 0355); else `grill-then-plan` - the decision gets written first |
| open child | `resolve-the-ticket` on that child |

> L-4 has no test - load `generating-test-cases` for its case?
> #297 is still New - go on to #297, or say it stays open on purpose?

Then ask about them one at a time, in the order of the table. On a yes: load the named
skill through your harness's mechanism and hand it the row and what you read; for a stale
row, name the test step to run again - the person or the skill that owns that step runs
it; for an open child, go on with that child as if this skill were called with its URL.
On a no, ask about the next gap; when a loaded skill is done, ask about the next gap;
after the last one, or on no answer, stop. Never load one without a yes (ADR 0339).

### 4.6 Record the check in the runbook

Append to the runbook, after its last section. Never edit a line above your own block:

```
## Resolve check - <date> <time UTC> - READY | NOT READY

Ticket #<id> rev <n> (GitHub: updated <timestamp>). Checked by resolve-the-ticket (read-only).

<the table of 4.3, as a Markdown table>

Gaps: <the lines of 4.5, or "none">
```

One block per check, newest last. Say the runbook's path.

## A Feature and its children

When the URL is an Azure DevOps **Feature** or **Epic** with children, the URL is the one
address for the whole family (ADR 0351). On GitHub, an issue with sub-issues is asked about inside the stage question - "#12 has 4
sub-issues - walk them one at a time, or treat #12 as one ticket?" - on each call: the
answer is kept nowhere.
A User Story or Bug with child Tasks is one ticket: its Tasks stay rows of its own check.

| stage | for the family |
|---|---|
| briefing | once, for the Feature and every child |
| plan | once, on the Feature's map |
| do and verify | per child, one at a time, in the order of the briefing's "what depends on what" map |
| check | per child; when no child is left, the Feature's own check (a row per child, by State) |

On every call, run step 3 for each child from its own runbook and work record. While the
family is still at the briefing or the plan, propose that stage for the family. After
that, propose **one** child. A child whose last check is READY, or whose State is done or
`Removed`, is skipped; when every child is skipped, propose the Feature's own check.

```
Next for Feature #193: #195 - do and verify, from the start.
#194 is READY (checked 2026-11-17). #196 and #197 wait on #195.
Go on? Or name another child or stage.
```

The person may also call the skill with a child's URL. Read the parent as always. When the
parent's map exists and has no open Decision ticket, the family's briefing and plan are
done - propose that child's own next stage; while it has open ones, propose the plan.

## Rules that keep it honest

- **It leads; it does not act.** Every act of the work happens in a skill it loaded on a
  yes.
- **This skill is read-only on the board, always.** No comment, no State, no tick. A skill
  it loaded keeps its own rules.
- **One mark on every pass.** A pass with no mark is a row nobody can trust later.
- **A test about the same thing is not a test of the row.** Given, When and Then all match,
  or the row has no test.
- **A person's word is shown as a person's word.** `told` is never written as `cited`.
- **Stale is not a warning.** A warning beside READY is read as READY.
- **Quote, do not paraphrase.** A row is the ticket's own words with a locator.
- **Say what you could not read.** A tracker you could not reach, an image that would not
  open, a change date not checked - name it in the output, never inside a confident summary.

## Not this skill

| not this | because |
|---|---|
| `work-map` | it resolves a **Decision ticket** on a Decision map; this skill loads it in the plan stage |
| `dual-verifier` | two agents verify one finished task from its diff; no ticket, no AC rows |
| `why-this-logic` | traces each rule to its source and teaches it; its splitting rules and marks are used here, its phases are not run |
| `ticket-trace` | answers why one line exists; its ticket fetch is loaded here |
| `guide-and-verify` | owns the runbook and the click work; loaded in do and verify |
| `sp-writing-plans` | owns the plan for code work; loaded in do and verify |
| `generating-test-cases` | writes the test cases a `no test` row needs; offered after NOT READY |

## Language

Mirror the language the user asked in - Thai in, Thai out. Keep identifiers, file paths,
the result words (`pass`, `no test`, `fail`, `stale`, `differs`, `open`, `removed`), the three marks
and the verdict line in English.
