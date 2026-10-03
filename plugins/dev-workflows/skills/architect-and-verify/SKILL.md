---
name: architect-and-verify
description: 'Write the architecture document for a new system that must work with an existing one, and prove it row by row - what the new system needs from the old one, the connections and the server prerequisites as tables, five UML views drawn in Mermaid, every change guided step by step, and every row tested until the document moves from to-be to as-built. Use this whenever a new application has to be brought up beside or on top of an old system: the user says bring up or go live with a new system, ขึ้นระบบใหม่, the new app must use data or logins from the old system, how will it plug into what we have, write the architecture document, draw the deployment or UML diagram, which ports or firewall rules do we need, test the connectivity, what must be installed on the server first (an SDK, a runtime, a driver). Use it even when the agent cannot reach the old system - the user then provides the facts and each one is marked measured or told. Do not use it for one hand-made change in a console with no architecture to write (that is guide-and-verify), for the software design document - use cases, classes, data model (that is sa-doc), or for studying an unfamiliar codebase (that is drive-to-legacy).'
---

# Architect and verify

A new system rarely stands alone. It needs data, a login or a function from a system that is
already running; it needs ports opened between the two; and it needs software on a server before
it can start. The deliverable here is **one architecture document, proven row by row**. It starts
as *to-be* — what the design says — and ends as *as-built* — what was measured.

The failure this skill prevents is the architecture drawn from what people believe. An old
diagram says a port is open. Someone remembers which SDK the server has. On go-live day one of
those beliefs is wrong, the new system does not start, and nobody can say which belief it was.
The cure is a mark on every fact, a test on every row, and each result written where its fact is.

## The boundary comes first

Before anything else, settle who acts. **You read and you test. You do not change either
system.** Every change — a firewall rule, an installation, an account — is made by a person: the
user, or a colleague in another team. Do not do "just the easy half", and do not quietly widen
your access to finish something. A boundary that you cross once stops being a boundary.

Say it out loud at the start, because it tells the person that waiting for you is not an option:

> I read and I test. I do not change either system. Every change below is yours or your
> colleagues'.

## Three rules that hold for the whole run

1. **Examination only reads.** Every command you run, or ask a person to run, while examining is
   read-only.
2. **Test only the connections in the connection table. Never scan.** A port outside the table
   is a port no need asked for, and a scan can raise the intrusion-detection alarm of whoever
   owns the network.
3. **Never write a secret.** The document, a step or a recorded result may name an account. It
   never holds a password, a key or a token — not even one the user pastes. Leave it out, and say
   that you left it out.

## The words this skill uses

| Word | Meaning |
|---|---|
| **Need** | one thing the new system must get from the old system — data, a login, a function |
| **Measured fact** | a fact that comes from the output of a command run against the live system, by you or by the user |
| **Told fact** | a fact that comes from someone's words or an old document; nobody ran a command for it |
| **Change** | one thing a person must do before a row can pass — install software, open a firewall rule, create an account |
| **Problem** | a test that fails when every change it needs is recorded as done |
| **To-be, as-built** | the status of the document; as-built only when no row is open |

## The run

Eight phases, 0 to 7, in order. Do not start a phase while the one before it has a question the
user has not answered.

### Phase 0 — Resume, when a document exists

When the user names an existing architecture document — or one already sits at the default path
for the system and environment they name — read it before you ask anything. Report its status,
the rows that are open, the changes not yet checked and the tests that are owed. Then continue
from the first open row. Do not ask the questions of Phase 1 again: the document holds the
answers. With no document, start at Phase 1.

### Phase 1 — Start

Say the boundary sentence. Then ask, in one round, only what the user has not already told you:

1. Which environment is this document for — UAT, production? One document covers one
   environment; a second environment is a second document.
2. Where do I save it? The default is `docs/architecture/<system>-<environment>.md`.
3. What is the new system, and who uses it?
4. What does it run on — the language or runtime, the database, and the server or service it
   will be installed on?
5. What must it get from the old system — data, a login, a function — and from which old system?

Questions 3 to 5 are the three questions about the new system. Their answers set the scope of
everything after: you examine only what they point at.

Then read `references/document-template.md` and create the document — the header, the three
answers, the empty tables. Create it now, not at the end. From here on, every fact goes into its
row when you take it, so a run interrupted at any point resumes from the file.

### Phase 2 — Needs

Turn the answer to question 5 into the needs table: one row per thing the new system must get. A
need is a thing, not a machine — *the staff data: name, email, department*, not *the HR database
server*. If the user says "reuse", read it as a need: what the new system must get from the old
one, not which old server is kept.

For each need, write where the thing lives in the old system — which system, which database or
service — with its mark.

### Phase 3 — Examine the old system

Examine only what the needs touch: the part that holds each needed thing, the zones and
firewalls on the path to it, and the server the new system runs on. Forty servers may exist; if
the needs touch two, you examine two.

Ask once which parts of the old system you may read yourself. Often the answer is none; that is
normal, and the user then provides the facts. For each fact:

- **You can read it** — run the read-only command. The fact is measured.
- **The user can run a command** — give them one exact read-only command and ask for the output.
  A pasted output is a measurement that travelled through a person. The fact is measured; record
  who ran it and when.
- **Nobody can run a command now** — take the user's words or an old document. The fact is told,
  and its row gets a test.

Write each fact into the parts table when you take it: the value, its mark, where it came from,
the time. A fact that contradicts what you were told first is the one most worth writing
immediately — it is the one nobody can reconstruct later.

### Phase 4 — A way for each need

Read `references/ways-to-meet-a-need.md`. For each need, propose the ways that can work, each
with one advantage and one cost, and say which facts rule a way out. **The user chooses.** You do
not pick the way: it is their architecture. Write the chosen way into the need's row.

Then take the rest of the new architecture — where each new part runs, in which zone — and add
those parts to the parts table as new.

### Phase 5 — Rows

From the needs and their ways, write:

- the **connection table** — one row per connection: from, to, port, the need it serves, and the
  state now with its mark;
- the **prerequisite table** — one row per piece of software or setting a server must have: what
  is necessary, where that requirement comes from, and what is installed now with its mark;
- the **changes** — one row per thing a person must do before a row can pass, with its owner.

Give every row its test and its expected result now, before anyone acts. A result with no
expected value written beforehand is a description, not a check. An expected output is itself a
claim: confirm what the command prints — from its documentation or a run — before it goes into a
row.

Every need is tested at two levels: each of its connections answers on its port, **and** one
real item of what it needs is read with the real account, from the new system's side. A port
that answers is not the test.

### Phase 6 — The document

Make the five views from the rows, as `references/document-template.md` describes: the context
view, the deployment view as-is, the deployment view to-be, the component view, and one sequence
diagram per need. Draw nothing that a row does not carry — every arrow in the deployment view
to-be is one connection row and shows its ID. The diagrams follow
`${CLAUDE_PLUGIN_ROOT}/references/diagram-convention.md`.

Save the document with the status to-be, and tell the user where it is.

### Phase 7 — Changes and tests

Read `references/change-steps.md` before the first change.

- **Guide each change** in the same eight steps, one change at a time. A change that belongs to
  another team gets the same steps, written so that team can follow them with only the document.
- **Test every row**, and write each result with its date into the row it tests. A told fact
  whose test passes becomes measured.
- **When a test does not pass**, it is owed, a finding or a problem — the next section says
  which.
- **When no row is open**, no change is unchecked and no test is owed, set the status to
  as-built, with the count of rows and the date.

## When a test does not pass

| What you see | What it is | What you do |
|---|---|---|
| The test cannot run yet: one end does not exist — the new system is not installed, so nothing listens on its port | **Owed** | Record the test as owed, with the reason. Do not open a temporary listener to prove the path early. The document stays to-be. |
| The test fails, and a change the row needs is not done — or a told fact turns out to be wrong | **A finding** | Write the measured value into the row. Add the change, or finish it. Carry on: an old document that is wrong is the normal case. |
| The test fails, and every change the row needs is recorded as done | **A problem** | Stop. Send the Freeze line, then hand off to `debug-mantra`, as `references/change-steps.md` says. Never tell the person to try again. |

## Measured or told

Every fact carries one of two marks.

- **measured** — the output of a command that was run against the live system, by you or by the
  user.
- **told** — anyone's words, an old document, a diagram.

A told fact always has a test in its row. When that test passes, the mark becomes measured, and
the result and its date stay in the row. Never write a told fact as if it were measured: an
unmeasured fact that looks measured is worse than a gap, because the document then certifies
something nobody confirmed.

A requirement — what the new system needs — is not a fact about the live system. It carries its
source (a vendor page, the user's word), not a mark.

## Say what you could not measure

Some part of the picture will be out of reach — a permission nobody in the session holds, a
firewall nobody can show you, a value that lives only in a console. Name it in the last section
of the document: what it is, why it could not be reached, and where a person can see it. Do not
let the gap hide inside a confident summary. If a fact came from something that refreshes on a
delay, say how old it is.

## When the run spans days

A firewall request takes days. A test of a connection into the new system is owed until that
system is installed. So a run is rarely one session, and the document is the memory: every
identifier in full, every result in its row, every owed test listed. The next session starts at
Phase 0 and needs nothing from this one.

## Write for the reader who was not there

The document is read by people who were never in the session — a network team opening a
firewall, an auditor three months later. Short sentences. Plain words. Their names for their own
systems; if their glossary separates two similar terms, keep them apart.
