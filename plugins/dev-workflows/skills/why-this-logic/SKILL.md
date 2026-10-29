---
name: why-this-logic
description: 'Find where a condition or a value comes from and whether it is right - one row per decision point (every if, every term of an and/or, every literal, every default), each with its own source, one proof mark (cited / told / measured) and one verdict (matches / contradicts / no source / cannot check from the document) - then explain each row in plain words and ask one question until the user can state the rule themselves. The thing may be code, an Azure DevOps / GitHub / JIRA ticket, a document, or pasted text; the user may name a source folder or document. Use whenever the user asks "is this logic right", "why is this value 30 / 0.15 / 914120001", "where does this condition come from", "what is the reference for this", "ทำไมต้องมี if นี้", "ค่านี้มาจากไหน", "logic นี้ถูกไหม", "แหล่งอ้างอิงคืออะไร", or doubts a filter, a mapping, a threshold or a default they did not write. Searches git, the ticket and its images, the named folder, specs, generating scripts and tests before asking; never opens a live system without asking first, and never writes to one. Writes docs/why/<thing>.md and starts from its open rows next time. Pointed at a requirement instead - a spec section, the acceptance criteria of a ticket, a sentence, or an R-ID - it runs forward: splits it into statements, gives each an ID, finds the decision points that implement it and the tests that assert it, and writes docs/why/requirements.md, the register that is the traceability matrix; every backward run feeds the same register. Use it too when the user asks "where is this requirement implemented", "is this requirement tested", "traceability", "requirement coverage", "which requirements have no code", "requirement นี้อยู่ตรงไหน", "มี test ไหม", "ทำ traceability matrix". Not ticket-trace (one line -> one ticket, one intentional/bug/unknown verdict for the whole line, no rows, no teaching), not asking-to-understand (questions about a whole artifact the user owns), not study-design-verify (how it SHOULD work - this skill asks why it IS the way it is).'
effort: max
---

# Why this logic

A developer looks at `if (days > 30)`, at `rate = 0.15`, at
`mgw_loggingstatus eq 914120001 or mgw_loggingstatus eq 914120003`, and cannot say whether
it is right - because they cannot say where it came from. Three things are tangled: *why
does this branch exist*, *where does this value come from*, and *which document, ticket or
person is the reference*. This skill untangles them one row at a time, and does not stop
at the table: it explains every row in plain words and asks one question until the user
can say the rule themselves.

**The failure this prevents:** one answer per function - "this comes from ticket #151" -
when the `30` came from that ticket, the `0.15` was changed later in a commit with no
ticket, and the status numbers map to labels that no document states. A per-function
answer hides that the rows have different origins, and that some have none.

## Three ideas the whole skill rests on

1. **The unit is one decision point, not one function.** Every comparison, every term of
   an `and`/`or`, every literal, every default is its own row with its own source and its
   own verdict (`references/splitting-rules.md`). Row 0 is always the origin of the text
   itself - a ticket body is often a copy of a script.
2. **Every closed row carries one proof mark.** *cited* (a file and line, or a commit),
   *told* (a person and a date), or *measured* (a read-only query against the live system,
   run only after the user said yes this run). A row with no mark is not closed.
3. **The session ends when the user states the rule, not when the table is written.** The
   explanation always comes before the question; the question is one, on the row that
   matters most; a wrong answer re-explains that one row and asks again.

## Two directions, one skill

What the user points at picks the direction (ADR 0279). Say which you chose in one line,
right after that direction's opening line (the quoted line that opens each run below); in
the ambiguous case the one question comes before either line:

| pointed at | direction |
|---|---|
| a `file:line`, a function, a filter inside a ticket, pasted logic, a decision point | **backward** - the phases 0 to 8 below: row -> source -> verdict |
| a spec section, a ticket's acceptance criteria, a document paragraph, a typed requirement sentence, an `R-` ID or the source's own ID | **forward** - the phases F0 to F6 further down: statement -> rows in code -> tests -> status |
| ambiguous - a whole ticket with both a description and logic | ask one question: "Trace the logic backward to its sources, or trace the requirements forward into the code?" |

Both directions write the same register, `docs/why/requirements.md` (ADR 0281); read
column-wise it is the traceability matrix.

## The backward run - phases 0 to 8

Say this one line before anything else, every backward run:

> I will break this into rows. For each row I find where it comes from, explain it, then
> ask you one question.

### 0. Open - ask only what the invocation did not give

Two things are needed: **what** to check (a function, a `file:line`, a ticket URL, a
document, pasted text) and, **if the user has one at hand**, a source (a folder, a
document, a ticket). Ask only for what is missing, in one question. An invocation that
carries both asks nothing and goes on. A source given here is a head start, not the whole
search - phase 2 still runs in full.

### 1. Split - one row per decision point

Apply `references/splitting-rules.md`. Write the row list before searching anything:

```
row  decision point (quoted as written)
0    origin of the text itself
1    <first term>
2    <second term>
...
```

More than about twelve rows: say so, and ask which part to trace first.

Phase 2 may split a row whose parts turn out to have different sources; it never merges rows.

**Write the Why file's skeleton now** - `docs/why/<thing>.md` (never `requirements.md`,
which is the register; a thing so named gets `why-requirements.md`) from
`references/why-file-template.md`, one block per row, every line carrying `—` - so every
hit found from here on has a durable place (ADR 0274).

### 2. Search first - before asking anyone

In this order, per row, stopping when the row closes - except that a row closed against a
document statement still runs order 6, so that a test asserting its value reaches the
register's *tested by* (ADR 0280) - and the origin of the text never closes a row but row 0
(below). **Write each hit into its block in the Why file as it is
found, not in a batch at the end** - a crash or a compaction loses an unwritten search, and
the hit that contradicts the document is the one nobody can reconstruct.

| order | where | how |
|---|---|---|
| 1 | git | `git log -S "<the literal>" -- <file>`, `git blame -w -C -L <n>,<n> <file>` (`--follow` when the file moved), the commit message; a ticket number in the message is followed with `ticket-trace` Operation B steps 3-5 (ticket reference -> tracker -> attachments) - load that skill through your harness's mechanism; do not give its step-6 answer, the row's verdict is one of this skill's four |
| 2 | the ticket | description, acceptance criteria, every comment, and **every attached image** through `read-picture` (kind `requirement`) - a requirement is often only an annotated screenshot |
| 3 | the folder or document the user named | every file in it, PDFs and images included |
| 4 | specs, ADRs, wikis in the project | the field's definition, the flow's description |
| 5 | generating scripts and templates | anything that could have *produced* the text - a backlog-population script, a scaffold, a template (row 0's source; on other rows, origin only) |
| 6 | tests | an assertion on the value is a source, and it names the intent |

A row closed here is **cited**: `file:line`, a commit hash, or `ticket #n (comment / image
name)`.

**A document statement gets an ID (ADR 0280).** When the source is a document - a spec, an
ADR, a wiki page, a ticket's description, one of its acceptance criteria, a comment or an
attached image that states a requirement (locator `#151 comment 3`, `#151 image <name>`);
not a commit, not a test, not a person - find or mint the statement's ID in `docs/why/requirements.md`
(`references/register-template.md`; create the file if absent): the source's own ID if the
statement carries one (`FR-12`, `AC-2`), else a new `R-nnn` one above the highest across every branch and worktree (ADR 0278). A statement
already registered - same locator, or same text - reuses its ID; never two IDs for one
sentence. The row's Source line then reads `cited R-003 (spec:145)`, and the register's
*implemented at* cell for R-003 gains `<Why file> row N`. Row 0 never mints - an origin is
not a requirement. A test found at order 6 that asserts the row's value goes into the
register's *tested by* cell of every requirement the row implements.

**The origin is not a reference.** The commit that introduced the text, and a script or
template that generated it, say where the text came from - that is row 0's source. On rows 1
and on, write such a hit on the row as `origin: <commit / file:line>` and keep searching.
Only a ticket, a spec, an ADR, a test, a person or a measurement closes a row. A ticket
number in the commit message is a pointer: follow it (ADR 0270).

### 3. Close the rest - told, or measured after a yes

Two kinds of row survive the search:

**no source** - nothing found. Ask **one** question naming every such row, each quoted,
with what was searched: "Rows 1 and 4 - nothing in git, the ticket, <folder>, specs,
scripts, tests. A document or a person for either?" A person's answer closes a row as
**told: who, date**. "I do not know" leaves it open. Phase 6's one-question rule is
separate from this ask (ADR 0277).

**cannot check from the document** - the source and the logic use different handles: a
label where the logic has a number, a name where the config has an id, and only the live
system maps them. Write the **exact read-only query** that would close it on the row
(for a Dataverse option set, the metadata GET `GET <org>/api/data/v9.2/EntityDefinitions(LogicalName='<table>')/Attributes(LogicalName='<column>')/Microsoft.Dynamics.CRM.PicklistAttributeMetadata?$expand=OptionSet($select=Options)`; a `SELECT`; a REST `GET`), then ask **once per
query**, in this shape:

> Row N cannot be checked from the documents. This read-only query would close it:
> `<the query>`
> Run it? On no, the query stays on the row for you to run later.

Yes: run exactly that query, read-only, and close the row as **measured: the query**.
The user runs the query themselves later and pastes its output: **measured: the query (run by <who>, <date>)** - the output travelled through them; a value stated without the output is **told** (ADR 0272).
No, or no answer: the row stays open with the query on it. The ask is per query and per run - a yes is never carried to another row or another run, and is never a standing permission (ADR 0275). **Never write to a live system, and never widen a yes to a second
query** - a second row needs its own ask.

### 4. Verdict - one of four, on every row

| verdict | meaning | row is |
|---|---|---|
| **matches** | a source exists and the logic agrees with it | closed |
| **contradicts** | a source exists and the logic disagrees - the number maps to a different label than the spec intends, the threshold differs from the ticket, the test asserts another value | closed |
| **no source** | nothing found, and no one asked could say | open |
| **cannot check from the document** | different handles; the query that would close it is on the row | open |

A verdict is written once the row is closed or declared open - never left blank.

A source that covers the whole thing and says nothing about this point - a spec query with
two terms, where the logic has three - is **no source** for the extra point, not
**contradicts**. **contradicts** needs the source to say something different about the same
point (ADR 0271).

### 5. Table, then explain - before any question

Print the table in monospace (a live terminal does not render Mermaid - see
`${CLAUDE_PLUGIN_ROOT}/references/diagram-convention.md`, *two render targets*):

```
row  decision point                       source                      mark      verdict
0    origin of the text                   scripts/populate_x.py:388   cited     matches
1    and mgw_loggingstatus … (the term)   —                           none      no source
2    914120001 / 914120003 (the numbers)  query on the row            none      cannot check from the document
```

Then explain **every row** in plain words - what the row is, where it comes from, what
the verdict means, and for *contradicts* what the source says instead. The style is
`wait-what`'s: a little context, ASD-STE100 Simplified Technical English, the project's
`CONTEXT.md` words. Short sentences. One idea per sentence. Present tense. Two or three
sentences per row. End the block with exactly this line:

> Not clear? Type /wait-what on the sentence.

Never invoke `wait-what` yourself - it runs only when the user types it.

Then **complete the Why file**: the plain-words text just shown goes into each block's
*In plain words* line, every Source and Verdict line is filled, and the overview's one-sentence
lead-in names the open rows. From here the file is whole; phases 6 and 7 update it. A run the
user walks out of still leaves the file (ADR 0274). **Refresh the register** at the same
moment - when this run cited or minted any ID: every such ID has its *implemented at*,
*tested by* and *status* cells current (`implemented` when a test is in *tested by*, else
`untested`), a locator whose row's verdict is *contradicts* carries `(contradicts)` after it,
the header's counts and *Last run* date are updated, and the overview's status nodes and
lead-in sentence are refreshed. A run that cited no document statement does not touch the
register and never creates it.

### 6. One question, until the user states the rule

Pick the row that matters most: a *contradicts* row first, then *no source*, then
*cannot check*. Ask **one** question. The manner is `asking-to-understand`'s - one grounded question per turn, stop when the rule is stated - but its answer table is replaced by the one below, where a re-ask always follows a re-explanation, and its closing block is not emitted: the Why file is the close.

> In your own words - why is row N here?

Classify the answer and move:

| the answer | the move |
|---|---|
| states the rule - names the source (or that there is none) and what the verdict means | close; go to phase 7 |
| repeats the code ("because the status is 1 or 3") | re-explain that one row (phase 5, that row only), ask again; a second repeat is handled like a second "I don't know" |
| names a source the search did not find | say what was searched and not found; ask whether they can point at it - a pointer re-enters phase 2 for that row |
| "I don't know" | re-explain that one row with the evidence on screen; ask once more; a second "I don't know" closes the run with the row open and the question written on the Why file's *Still to answer* header line (ADR 0276) |

Never more than one question per turn. Never a list of questions.

### 7. Close the Why file

Update `docs/why/<thing>.md` (its skeleton was written in phase 1 and completed in phase 5): the *Still to answer* header line if a question stayed open, any row the close changed, and the offer line below. Say the path - and the register's path when this run touched it.

If any row's verdict is *contradicts*, end with exactly one line and stop:

> Row N contradicts its source - file it as a finding (`findings-to-ado-backlog`), or take
> it to `grill-then-plan` if the fix is a design choice?

The skill files nothing and fixes nothing.

### 8. A later run on the same thing

Look in `docs/why/` for the file whose **Thing:** line names the same thing; if it exists, open it **first**. Rows whose verdict is *matches* or
*contradicts* are not re-traced. Start at phase 3 for the rows still *no source* or
*cannot check*, with their queries already written - the per-run ask applies again. If the thing has changed since - row 0's origin hash for code; the ticket's revision (`System.Rev`, `updated_at`) or the document's modified date otherwise - say so and re-split.

## The forward run - phases F0 to F6

Say this one line before anything else, every forward run:

> I will split this into requirement statements. For each one I find where it is
> implemented and which test proves it, explain it, then ask you one question.

### F0. Open

Open `docs/why/requirements.md` if it exists; it is created in F2, by the first ID minted
(`references/register-template.md`). Ask only for what the invocation did not give: the requirement text (or its
locator - a spec section, a ticket, an ID) and, if the user has it, the code area it is
expected to live in. The area is a head start, not a limit - F3 searches the whole project.

### F1. Split the text into statements

Apply the *Splitting a requirement text* section of `references/splitting-rules.md`: one
statement per clause that binds behaviour - a value, a condition, a trigger, a recipient, an
ordering. A sentence with "and" between two obligations is two statements; an example, a
rationale or a heading is none. Quote each statement **as written**, with its locator
(`spec:145`, `#151 AC-2`). Write the list before searching anything:

```
id      statement (as written)                          locator
R-001   Runs Mon-Fri 08:00 AEST                         spec:144
R-002   hasthecallbeenactioned eq false                 spec:145
R-003   callDateTime < Now - 7 days                     spec:145
R-004   Sends reminder emails to case staff             spec:146
R-005   increments ReminderCount                        spec:146
R-006   Compiles consolidated table                     spec:147
R-007   converts to PDF                                 spec:147
R-008   emails to MG_AdminEmail / Liquidators            spec:147
```

### F2. Find or mint IDs

The source's own ID when the statement carries one; else the next `R-nnn` of this register.
A statement already registered - same locator, or same text - reuses its ID. A new
`R-nnn` is one above the highest across every branch and worktree; an ID is never reused
for another statement and never renumbered once merged (ADR 0278). Write every new line into the register now, cells `—` - creating the file from
`references/register-template.md` on the first ID - so the file
exists before the search.

### F3. Search the code for each statement

In this order, recording every hit into the register as it is found:

| order | look for | how |
|---|---|---|
| 1 | the literal value | `7`, `08:00`, `MG_AdminEmail` - grep the project, read each hit as a decision point |
| 2 | the field or variable name | `mgw_hasthecallbeenactioned`, `reminder_age_days` |
| 3 | the flow, function or job name | `mgw_flow_overduereport`, `markOverdue` |
| 4 | an existing Why file | a row whose Source line cites this ID |

Each real hit is a decision point: write it in *implemented at* as `file:line` or
`<Why file> row N`. A hit that only mentions the value in a comment, a log string or a
test is not an implementation. No hit: *implemented at* stays `—`.

### F4. Search the tests for each statement

A code test that asserts the value or the condition (`expect(isOverdue(31)).toBe(true)`), or
a case in a `generating-test-cases` suite whose Evidence or ID column cites the statement's
ID. Write it in *tested by* as `file:line` or `<suite> case <id>`. No hit: `—`.

### Status - one of four, on every statement

| status | meaning |
|---|---|
| **implemented** | at least one decision point in *implemented at* and at least one test in *tested by* |
| **untested** | a decision point, no test - `generating-test-cases`' work |
| **not found** | no decision point - a gap only the forward trace can see |
| **source changed** | on a later run, the text at the locator no longer reads as the register records; keep the old text beside the new, re-derive nothing until the user confirms the new wording |

The forward run never opens a live system. A fact only the live system could confirm (a
schedule inside a flow definition, say) is written *implemented at: told <who, date>* when
the user states it - the same marks as the backward run (ADR 0266, 0272).

### F5. Matrix, then explain - before any question

Print the register's lines for these statements in monospace:

```
id      statement                               implemented at                     tested by               status
R-001   Runs Mon-Fri 08:00 AEST                 mgw_flow_overduereport trigger     —                       untested
R-002   hasthecallbeenactioned eq false         …/elevate-151-overdue-filter.md row 1 —                    untested
R-003   callDateTime < Now - 7 days             …filter.md row 2 · overdue.ts:14   overdue.test.ts:14-15   implemented
…       (R-004..R-007 omitted here)
R-008   emails to MG_AdminEmail / Liquidators   —                                  —                       not found
```

Then explain **every statement** in plain words - where it lives, what proves it, or that
nothing does - in `wait-what`'s plain style: short sentences, two or three per statement,
the project's `CONTEXT.md` words. End the block with exactly this line:

> Not clear? Type /wait-what on the sentence.

Then refresh the register: cells, statuses (a locator whose row's verdict is *contradicts*
carries `(contradicts)` after it), the header's counts and *Last run*, and the overview's
one-sentence lead-in naming the *not found* and *untested* statements.

### F6. One question, then close

Pick the statement that matters most: *not found* first, then *untested*, then *source
changed*. Ask **one** question - phase 6's manner, phase 6's answer table, a re-ask always
after a re-explanation:

> In your own words - why has R-008 no code?

Read phase 6's table with two substitutions: "go to phase 7" means this close, and "the Why
file's *Still to answer* header line" means the register's. When the user states the rule,
update the register; when a question stayed open, write it on the register's *Still to
answer* header line. End with at most two one-line offers and stop:

> R-001 has code and no test - generate its case (`generating-test-cases`)?
> R-008 has no code - design it (`grill-then-plan`), or file it as a finding (`findings-to-ado-backlog`)?

The skill writes no test and no code. Say the register's path.

### A later forward run

Open the register first. Re-read each statement's locator: text unchanged -> keep the line
and re-run F3/F4 only for statements still *untested* or *not found*; text changed -> status
*source changed*, old text kept beside the new, and one question before anything else is
re-derived.

## Rules that keep it honest

- **Read-only, always.** A `SELECT`, a `GET`, a metadata read. Never a write, never a
  "harmless" update.
- **Ask per query.** A yes on row 2 is not a yes on row 5, and not a yes next run.
- **One mark or `none`.** A row with a source and no mark is a row nobody can trust later.
- **A person's word is a source, and is marked as one.** `told: Khun A, 2026-10-29` closes
  the row; it is never written as `cited`.
- **Record as found.** Every hit goes into its block in the Why file - or its line in the
  register, on a forward run - before the next search.
- **The origin never closes a row but row 0.** A commit or script that wrote the value is where the text came from, not why.
- **One ID per statement, for ever.** A new `R-nnn` is one above the highest across every
  branch and worktree - never this checkout's copy alone; an ID is never reused for another
  statement and never renumbered once merged; a statement already registered reuses its ID
  (ADR 0278). This binds both directions.
- **The register is written, never the source.** IDs go into `docs/why/requirements.md`; a
  spec, a ticket or a tracker is never edited (ADR 0281).
- **Explain before you ask.** A question before the explanation tests memory, not
  understanding.

## Not this skill

| not this | because | hand-off |
|---|---|---|
| `ticket-trace` | answers *why* for one line via git -> ticket -> image, with no split, one intentional/bug/unknown verdict for the whole line, no teaching; this skill **uses** its chain in phase 2 | loaded, not duplicated |
| `asking-to-understand` | questions a whole artifact the user owns; only its close is borrowed here - one grounded question per turn, ends when the rule is stated | borrowed: one question per turn, stop at the rule; its closing block is not emitted |
| `feynman-explain` | a stand-alone explanation card; here the explanation sits beside a row | - |
| `wait-what` | the user's own repair for one sentence; cannot be invoked by a skill | pointed at, every explaining block |
| `study-design-verify` | how it *should* work; this skill asks why it *is* this way | — (a contradicts row that needs a design goes to `grill-then-plan`, named in the phase-7 line) |
| `generating-test-cases` | writes the test cases; this skill only shows which requirement has none | the F6 offer line |
| `fit-gap-analysis` | compares a target against a whole system; this skill traces one requirement text into code | - |
| `debug-mantra` | nothing is broken; a *contradicts* row is a finding, not a failure | - |
| `guide-and-verify`, `architect-and-verify` | their row block and their marks are copied; neither is loaded | - |

## Language

Mirror the language the user asked in - Thai in, Thai out, including the explanations and
the one question. Keep identifiers, file paths, the four verdict words and the four status
words in English.
