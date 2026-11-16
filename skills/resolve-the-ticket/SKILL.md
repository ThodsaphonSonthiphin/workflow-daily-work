---
name: resolve-the-ticket
description: 'Read-only helper for one ticket at two moments. BRIEFING before the work starts - what the ticket asks, its parent and children, linked tickets, the runbook and the files to open. CHECK before a person sets it to Resolved - one row per Acceptance Criteria line, logic rule and child ticket, each with its test and result (pass cited / measured / told, no test, fail, stale, differs, open), then READY or NOT READY and, on READY, a closing comment to paste. Asks which moment and waits for the ticket URL (Azure DevOps or GitHub Issues). Use for "resolve the ticket", "is this ticket ready to resolve", "check before I resolve", "brief me on this ticket", "ticket นี้ resolve ได้ยัง", "เช็คก่อน resolve", "อ่าน ticket นี้ให้หน่อย". Never changes the ticket, builds nothing. Not work-map (Decision tickets), not dual-verifier (one diff).'
argument-hint: "[brief|check] <ticket URL - Azure DevOps or GitHub issue>"
effort: max
---

# Resolve the ticket

A ticket gets set to Resolved on "I think it is done". A week later it is reopened, because
one rule in its details had no passing test on that day. This skill stands at the two
moments where that is cheap to prevent: before the work starts, and before the State
changes.

**The failure this prevents:** a ticket resolved over a rule nobody tested, a pass that is
older than the last change, or a child task nobody did.

## What it never does

- It **builds nothing and fixes nothing.** The work between the two moments belongs to the
  other skills.
- It **never writes to the tracker** - no comment, no State change, no ticked box. The
  person does those.
- It **never writes a runbook.** A missing runbook is `guide-and-verify`'s to create.
- It **never starts the skill it names for a gap.** It names it and stops.

Its only write is one dated block appended to the ticket's runbook.

## The flow

```
 ┌──────────────────────────────────┐
 │ 0. Ask: briefing or check?       │
 │    Wait for the ticket URL       │
 └────────────────┬─────────────────┘
                  ▼
 ┌──────────────────────────────────┐
 │ 1. Read ticket, parent, children │
 │    (other links: title + State)  │
 └────────────────┬─────────────────┘
                  ▼
 ┌──────────────────────────────────┐
 │ 2. Find files by ticket number   │
 │    print the list, then read     │
 │    no runbook -> guide-and-verify│
 └───────┬──────────────────┬───────┘
         ▼                  ▼
 ┌───────────────┐  ┌───────────────────┐
 │ 3. BRIEFING   │  │ 4. CHECK          │
 │    chat only  │  │    rows + verdict │
 │    stop       │  │    append to the  │
 └───────────────┘  │    runbook        │
                    └───────────────────┘
```

## 0. Open - ask, and wait for the URL

Two things are needed: the **moment** (briefing or check) and the **ticket's URL**. Ask only
for what the invocation did not give, in one question:

> Briefing (before you start) or check (before you resolve)? And the ticket's URL, please.

Read nothing until you have the URL. A bare number is not enough - the URL names the
tracker, the organization and the project in one string, so the right number is never read
in the wrong project. Do not take the organization or project from an environment variable.

| URL | tracker |
|---|---|
| `dev.azure.com/<org>/<project>/_workitems/edit/<id>` | Azure DevOps |
| `github.com/<owner>/<repo>/issues/<n>` | GitHub Issues |
| anything else | say "I cannot read this tracker." and stop |

Then say one line: which moment this is, and for which ticket.

## 1. Read the ticket family

| who | how much |
|---|---|
| the ticket | in full |
| its direct parent | in full |
| every direct child | in full |
| predecessor, successor, related tickets | type, title and State only |
| the grandparent and above | not read |

**In full** means: type, title, State, revision, description (for an Azure DevOps Bug also
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
3. commit messages (`git log --grep`)
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

**No runbook found.** Say so in one line, then hand off to `guide-and-verify` (load it
through your harness's mechanism) to create the runbook, giving it what you have already
read - the ticket, its parent and children, the file list - as its head start. It writes
the file in its own shape and the project's own naming. Do not write a runbook yourself, do
not use the parent's runbook, and do not go on as if there were none. Continue when the
runbook exists.

## 3. Moment one - the briefing

Chat only, in this order, then stop:

1. **The ticket** - one line: type, id, title, State, revision, URL.
2. **The family** - a table: parent, children, linked tickets, each with type, title, State.
3. **What it asks** - every AC line and every logic rule, quoted **as written**, each with
   a locator (`#151 AC-2`, `#151 description`, `#151 image <name>`).
4. **The files** - the list from step 2, and which to open first (the runbook, when it has
   steps).
5. **Open points** - an AC line that names something no file mentions; a linked ticket that
   is still open; a place where the ticket and its parent disagree.

Show a rule with logic the way the project asks for it (some projects fix a flowchart
shape in their `CLAUDE.md` / `AGENTS.md` - follow it). Write no file. Print no check table
and no verdict.

## 4. Moment two - the check

### 4.1 The rows

One row per:

- **AC line** - each Acceptance Criteria statement, one per clause that binds behaviour (a
  value, a condition, a trigger, a recipient, an ordering). A sentence with "and" between
  two obligations is two rows; a heading, an example or a rationale is none. The full rules
  are `why-this-logic`'s:
  `skills/why-this-logic/references/splitting-rules.md`.
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
first. If the ticket's revision is the same, keep the rows; a row that was a pass is kept
only when its proof is still where the block says and it is not stale now - re-check every
other row. If the revision changed, split the rows again. An earlier block is never the
proof of a pass; the test result it points at is.

### 4.2 The result of one row

Ask these in order and stop at the first that decides:

```
 a test for this row?  ── none ───────────────▶ NO TEST
        │ yes
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
file in the repo, a case in a test-case suite, the register's *tested by* cell. Nothing
found: ask the user once, naming every such row - "Rows L-1 and AC-3 - no test found in the
runbook, the comments or the repo. Was either tested?"

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
snapshot, the ticket's revision date. A pass older than the change is **stale**: show both
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
approved decision** that covers the difference - a runbook decision, an ADR, a ticket
comment, with who approved it. Found: `pass - differs by decision <id>`, with its locator,
when the test passes. Not found: **differs** - a passing test of the wrong rule is not a
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

READY TO RESOLVE: NO
```

| result | counts for READY |
|---|---|
| pass (cited / measured / told) | yes |
| pass - differs by decision | yes |
| child done, or open on purpose (told) | yes |
| removed (child) | not counted - left out of the verdict |
| no test, fail, stale, differs, open | no |

READY needs every row to count. When told rows or undated passes exist, the verdict reads
`READY TO RESOLVE: YES (N rows rest on your word)`. A linked ticket that is an open Bug is
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

### 4.5 On NOT READY - name the next skill, and stop

Draft no comment. Print at most one line per kind of gap, naming every row of that kind:

| gap | the line names |
|---|---|
| no test | `generating-test-cases` |
| fail | `debug-mantra` |
| stale | the test step to run again (or: say the change does not touch the row) |
| differs, no decision | `grill-then-plan` - the decision gets written first |
| open child | `resolve-the-ticket` on that child |

> L-4 has no test - write its case (`generating-test-cases`)?
> #297 is still New - run `resolve-the-ticket` on it, or say it stays open on purpose?

Then stop. Do not start any of them.

### 4.6 Record the check in the runbook

Append to the runbook, after its last section. Never edit a line above your own block:

```
## Resolve check - <date> <time UTC> - READY | NOT READY

Ticket #<id> rev <n>. Checked by resolve-the-ticket (read-only).

<the table of 4.3, as a Markdown table>

Gaps: <the lines of 4.5, or "none">
```

One block per check, newest last. Say the runbook's path.

## Rules that keep it honest

- **Read-only on the board, always.** No comment, no State, no tick.
- **One mark on every pass.** A pass with no mark is a row nobody can trust later.
- **A person's word is shown as a person's word.** `told` is never written as `cited`.
- **Stale is not a warning.** A warning beside READY is read as READY.
- **Quote, do not paraphrase.** A row is the ticket's own words with a locator.
- **Say what you could not read.** A tracker you could not reach, an image that would not
  open, a change date not checked - name it in the output, never inside a confident summary.

## Not this skill

| not this | because |
|---|---|
| `work-map` | it resolves a **Decision ticket** on a Decision map - a different thing |
| `dual-verifier` | two agents verify one finished task from its diff; no ticket, no AC rows |
| `why-this-logic` | traces each rule to its source and teaches it; its splitting rules and marks are used here, its phases are not run |
| `ticket-trace` | answers why one line exists; its ticket fetch is loaded here |
| `guide-and-verify` | owns the runbook; this skill only appends its check block |
| `generating-test-cases` | writes the test cases a `no test` row needs |

## Language

Mirror the language the user asked in - Thai in, Thai out. Keep identifiers, file paths,
the result words (`pass`, `no test`, `fail`, `stale`, `differs`, `open`, `removed`), the three marks
and the verdict line in English.
