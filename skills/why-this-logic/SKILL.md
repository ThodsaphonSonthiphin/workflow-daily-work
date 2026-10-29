---
name: why-this-logic
description: 'Find where a condition or a value comes from and whether it is right - one row per decision point (every if, every term of an and/or, every literal, every default), each with its own source, one proof mark (cited / told / measured) and one verdict (matches / contradicts / no source / cannot check from the document) - then explain each row in plain words and ask one question until the user can state the rule themselves. The thing may be code, an Azure DevOps / GitHub / JIRA ticket, a document, or pasted text; the user may name a source folder or document. Use whenever the user asks "is this logic right", "why is this value 30 / 0.15 / 914120001", "where does this condition come from", "what is the reference for this", "ทำไมต้องมี if นี้", "ค่านี้มาจากไหน", "logic นี้ถูกไหม", "แหล่งอ้างอิงคืออะไร", or doubts a filter, a mapping, a threshold or a default they did not write. Searches git, the ticket and its images, the named folder, specs, generating scripts and tests before asking; never opens a live system without asking first, and never writes to one. Writes docs/why/<thing>.md and starts from its open rows next time. Not ticket-trace (one line -> one ticket, no verdict, no teaching), not asking-to-understand (questions about a whole artifact the user owns), not study-design-verify (how it SHOULD work - this skill asks why it IS the way it is).'
argument-hint: "<function, ticket URL, file:line, or pasted text> [source folder or document]"
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

## The run - eight phases

Say this one line before anything else, every run:

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

### 2. Search first - before asking anyone

In this order, per row, stopping when the row closes. **Write each hit on its row as it is
found, not in a batch at the end** - a crash or a compaction loses an unwritten search, and
the hit that contradicts the document is the one nobody can reconstruct.

| order | where | how |
|---|---|---|
| 1 | git | `git log -S "<the literal>" -- <file>`, `git blame -w -L <n>,<n> <file>`, the commit message; a ticket number in the message is followed exactly as `ticket-trace` Operation B follows it - load that skill through your harness's mechanism |
| 2 | the ticket | description, acceptance criteria, every comment, and **every attached image** through `read-picture` (kind `requirement`) - a requirement is often only an annotated screenshot |
| 3 | the folder or document the user named | every file in it, PDFs and images included |
| 4 | specs, ADRs, wikis in the project | the field's definition, the flow's description |
| 5 | generating scripts and templates | anything that could have *produced* the text - a backlog-population script, a scaffold, a template |
| 6 | tests | an assertion on the value is a source, and it names the intent |

A row closed here is **cited**: `file:line`, a commit hash, or `ticket #n (comment / image
name)`.

### 3. Close the rest - told, or measured after a yes

Two kinds of row survive the search:

**no source** - nothing found. Ask the user, *for these rows only*: "Do you have a
document or a person for row N?" A person's answer closes the row as **told: who, date**.
"I do not know" leaves it open.

**cannot check from the document** - the source and the logic use different handles: a
label where the logic has a number, a name where the config has an id, and only the live
system maps them. Write the **exact read-only query** that would close it on the row
(`dataverse:dv-metadata` for an option set, a `SELECT`, a `GET`), then ask **once per
run**, in this shape:

> Row N cannot be checked from the documents. This read-only query would close it:
> `<the query>`
> Run it? On no, the query stays on the row for you to run later.

Yes: run exactly that query, read-only, and close the row as **measured: the query**.
No, or no answer: the row stays open with the query on it. The ask is per run, never a
standing permission. **Never write to a live system, and never widen a yes to a second
query** - a second row needs its own ask.

### 4. Verdict - one of four, on every row

| verdict | meaning | row is |
|---|---|---|
| **matches** | a source exists and the logic agrees with it | closed |
| **contradicts** | a source exists and the logic disagrees - the number maps to a different label than the spec intends, the threshold differs from the ticket, the test asserts another value | closed |
| **no source** | nothing found, and no one asked could say | open |
| **cannot check from the document** | different handles; the query that would close it is on the row | open |

A verdict is written once the row is closed or declared open - never left blank.

### 5. Table, then explain - before any question

Print the table in monospace (a live terminal does not render Mermaid - see
`references/diagram-convention.md`, *two render targets*):

```
row  decision point                       source                      mark      verdict
0    origin of the text                   scripts/populate_x.py:388   cited     matches
1    and mgw_loggingstatus … (the term)   —                           none      no source
2    914120001 / 914120003 (the numbers)  query on the row            none      cannot check from the document
```

Then explain **every row** in plain words - what the row is, where it comes from, what
the verdict means, and for *contradicts* what the source says instead. The register is
`wait-what`'s: a little context, ASD-STE100 Simplified Technical English, the project's
`CONTEXT.md` words. Short sentences. One idea per sentence. Present tense. Two or three
sentences per row. End the block with exactly this line:

> Not clear? Type /wait-what on the sentence.

Never invoke `wait-what` yourself - it runs only when the user types it.

### 6. One question, until the user states the rule

Pick the row that matters most: a *contradicts* row first, then *no source*, then
*cannot check*. Ask **one** question, in the manner of `asking-to-understand`:

> In your own words - why is row N here?

Classify the answer and move:

| the answer | the move |
|---|---|
| states the rule - names the source (or that there is none) and what the verdict means | close; go to phase 7 |
| repeats the code ("because the status is 1 or 3") | re-explain that one row (phase 5, that row only), ask again |
| names a source the search did not find | say what was searched and not found; ask whether they can point at it - a pointer re-enters phase 2 for that row |
| "I don't know" | re-explain that one row with the evidence on screen; ask once more; a second "I don't know" closes the run with the row open and the question written into the Why file |

Never more than one question per turn. Never a list of questions.

### 7. Write the Why file

Write `docs/why/<thing>.md` in the project being traced, from
`references/why-file-template.md` - one Mermaid overview, then one fixed-shape block per
row. Say the path. The *In plain words* line of each block is the same text the user was
shown in phase 5.

If any row's verdict is *contradicts*, end with exactly one line and stop:

> Row N contradicts its source - file it as a finding (`findings-to-ado-backlog`), or take
> it to `grill-then-plan` if the fix is a design choice?

The skill files nothing and fixes nothing.

### 8. A later run on the same thing

If `docs/why/<thing>.md` exists, open it **first**. Rows whose verdict is *matches* or
*contradicts* are not re-traced. Start at phase 3 for the rows still *no source* or
*cannot check*, with their queries already written - the per-run ask applies again. If
row 0's origin hash differs from the thing's current hash, say so and re-split.

## Rules that keep it honest

- **Read-only, always.** A `SELECT`, a `GET`, a metadata read. Never a write, never a
  "harmless" update.
- **Ask per run, per row.** A yes on row 2 is not a yes on row 5.
- **One mark or `none`.** A row with a source and no mark is a row nobody can trust later.
- **A person's word is a source, and is marked as one.** `told: Khun A, 2026-10-29` closes
  the row; it is never written as `cited`.
- **Record as found.** Every hit goes on its row before the next search.
- **Explain before you ask.** A question before the explanation tests memory, not
  understanding.

## Not this skill

| not this | because | hand-off |
|---|---|---|
| `ticket-trace` | answers *why* for one line via git -> ticket -> image, with no split, no verdict, no teaching; this skill **uses** its chain in phase 2 | loaded, not duplicated |
| `asking-to-understand` | questions a whole artifact the user owns; only its close is borrowed here - one grounded question per turn, ends when the rule is stated | borrowed, not invoked |
| `feynman-explain` | a stand-alone explanation card; here the explanation sits beside a row | - |
| `wait-what` | the user's own repair for one sentence; cannot be invoked by a skill | pointed at, every explaining block |
| `study-design-verify` | how it *should* work; this skill asks why it *is* this way | named in the phase-7 line when the fix is a design choice |
| `debug-mantra` | nothing is broken; a *contradicts* row is a finding, not a failure | - |
| `guide-and-verify`, `architect-and-verify` | their row block and their marks are copied; neither is loaded | - |

## Language

Mirror the language the user asked in - Thai in, Thai out, including the explanations and
the one question. Keep identifiers, file paths and the four verdict words in English.
