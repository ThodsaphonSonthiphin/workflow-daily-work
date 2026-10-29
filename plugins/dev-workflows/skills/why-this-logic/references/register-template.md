# The register - `docs/why/requirements.md`

One file per project, beside the Why files. One line per requirement ID. Read column-wise it
is the traceability matrix: an empty *tested by* cell is `generating-test-cases`' work, an
empty *implemented at* cell is a gap (ADR 0281).

## Rules

- **One line per ID.** The source's own ID when it is unique across the project (`FR-12`), qualified by its ticket or document when it is not (`#151/AC-2`);
  else `R-001`, `R-002` … where a new `R-nnn` is one above the highest across every branch
  and worktree - never this checkout's copy alone; an ID is never reused for another
  statement and never renumbered once merged (ADR 0278).
- **A statement is the registered one when its text matches** - at the registered locator, or
  at a new locator in the same section (add it to *source*, joined by ` · `). A matching
  locator whose text differs is *source changed*: `<new text> (was: <old text>)` in the
  statement cell, nothing minted, said before anything cites it. The same text in another
  section is a new statement unless the user says it restates the first; a restatement adds
  its locator and mints nothing (ADR 0282).
- **statement** is quoted as written in the source; **source** is its locator
  (`spec:145`, `#151 AC-2`, `spec:121 (MG_ReminderAgeDays (7))`).
- **implemented at** and **tested by** hold one or more locators separated by ` · `:
  `file:line`, `<Why file> row N`, `<suite> case <id>`; a cell with nothing carries `—`.
- **status** is one of four words: `implemented`, `untested`, `not found`, `source changed`.
- **A fact only the live system could confirm** is written `told <who, date>` in
  *implemented at* when the user states it - the backward run's marks apply (ADR 0266, 0272).
- **source changed** keeps both texts in the *statement* cell: `<new text> (was: <old text>)`,
  until the user confirms the new wording.
- **Still to answer** is filled only when a forward run's one question stayed open (F6);
  otherwise `—`.
- **Sources** lists every spec, ticket and folder a statement in the table came from.
- The header's counts and *Last run* are refreshed by every run that cited or minted an
  ID, in either direction; a run that cited no document statement leaves the file alone.
- A locator in *implemented at* whose row's verdict is *contradicts* carries `(contradicts)`
  after it - the status says whether code and a test exist, the mark keeps the disagreement
  visible. A test locator in *tested by* whose assertion disagrees with the statement carries it too (ADR 0284).
- The overview is Mermaid; one lead-in sentence follows it; no double quotes inside labels.
  It shows one node per *not found* and *untested* statement plus one node with the count
  of *implemented* ones - never one node per ID, which outgrows a thumbnail.

## Template

````markdown
# Requirements - <project>

- **Register of:** <repo or system name>  ·  **Last run:** <YYYY-MM-DD>  ·  **Statements:** <n> · implemented <a> · untested <b> · not found <c> · source changed <d>
- **Sources:** <spec path(s)> · <ticket(s)> · <folder>
- **Still to answer:** <R-nnn — the question, or —>

```mermaid
flowchart LR
    S["<source>"] --> R1["R-001<br/>untested"]
    S --> I["implemented: 1"]
    S --> R8["R-008<br/>not found"]
```

<One sentence: which statements are not found or untested.>

| ID | statement (as written) | source | implemented at | tested by | status |
|---|---|---|---|---|---|
| R-001 | <statement> | <locator> | <file:line · Why file row N · —> | <file:line · suite case id · —> | <status> |
````

## Worked lines - `Elevate`, spec §4 Workflow 3

| ID | statement (as written) | source | implemented at | tested by | status |
|---|---|---|---|---|---|
| R-001 | Runs Mon-Fri 08:00 AEST | spec:144 | `flows/mgw_flow_overduereport.json:3` | — | untested |
| R-003 | callDateTime < Now - 7 days | spec:145 · spec:121 (`MG_ReminderAgeDays (7)`) | `flows/mgw_flow_overduereport.json:12` | `tests/flows/overdue.test.ts:14-15` | implemented |
| R-008 | emails to `MG_AdminEmail` / Liquidators | spec:147 | — | — | not found |
