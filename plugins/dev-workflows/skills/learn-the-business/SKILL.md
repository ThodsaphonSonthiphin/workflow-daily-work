---
name: learn-the-business
description: "Shows the business flow as it is now around the part of a program the user is touching - who does what and hands the work to whom, every line with its source - then asks ONE business question at a time that the picture gives the facts for but not the answer, and walks backward to the business origin. The part is a table, field, flow, rule, role, report or integration. After each answer it reveals the business reason first, then the technical choice it leads to, then the ADR text, then a named thinking trick, every line marked cited / told / general knowledge / assumed. Keeps a note of what was asked outside git. Use when the user says \"ถามเรื่อง business\", \"ถามธุรกิจของงานนี้\", \"ทำไมธุรกิจต้องการแบบนี้ ถามผมหน่อย\", \"learn the business\", \"ask me about the business behind this\", \"quiz me on why the business needs this\"; when someone can build a part but cannot say why the business needs it; when onboarding onto a program's domain. Not for the mechanism of an artifact (asking-to-understand), not for explaining on request (feynman-explain), not for tracing one value to its source with a verdict (why-this-logic)."
effort: max
---

# Learn The Business

A developer can build a part of a program and still not be able to say why the business
needs it. This skill first shows them the work as it runs today around the part they are
touching, then asks - one question per turn, walking backward - and after each answer shows
the business reason **first**, then the technical choice that follows from it, then the ADR
text, then the way of thinking that reaches such an answer.

**The failures this prevents:** a question about a flow the person has never seen, which
they can only guess at; an explanation that starts at the code ("this flow filters on this
field") and never reaches a person, money or a rule; and a tidy business reason no document
states, which the developer then repeats to the client.

Design decisions are ADRs 0368-0377 and 0389-0391 at the marketplace repo root. This file is
the procedure.

## Never do these

- **Never** ask a question before the ground search of step 1.
- **Never** ask the first question of a sitting before the Business flow is on the screen.
- **Never** ask two questions in one turn.
- **Never** write a guess without the mark *assumed* - on the card or on the Business flow.
- **Never** write a reason on the Business flow. It says what happens; the card says why.
- **Never** write to the project's repo, a tracker or a live system. The only file this
  skill writes is the Business note.
- **Never** refuse to run because the note is missing or unreadable. Start from nothing.

## The session

```
  ⓪ START     argument, or what the person is touching - say what you picked
  ① GROUND    search the sources + read the Business note   (no question before this)
  ② SHOW      the Business flow as it is now, the part marked "you are here"
  ③ ASK       one question the flow gives the facts for, then stop
  ④ RECEIVE   class of the answer picks the move; a system answer is pushed once
  ⑤ REVEAL    the card: business, technical, ADR, thinking trick - every line marked
  ⑥ NOTE      one row to the Business note, right away
  ⑦ BACK      one step backward, to ③ - until a Business origin or five questions
  ⑧ CLOSE     the fixed closing block
```

## What may be asked - the Business part

A **Business part** is one part of the program with a business decision behind it. Six
kinds, an open set - a part of a new kind is added, not forced into one:

| kind | examples | the business question behind it |
|---|---|---|
| data | table, field, choice value, relationship | what real thing does this stand for |
| process | flow, job, trigger, order of steps | how does the real work move, who hands to whom |
| rule | condition, threshold, validation, default | who set it, and what happens if it is wrong |
| people | role, permission, recipient | who may do what, and why not the others |
| output | report, email, document, screen | who reads it, and what do they do next |
| connection | external system, API, import, export | why must the program talk to that system |

A part the platform made - a created-on date, an id, an owner column - is **not** a Business
part. Do not ask about it. List the skipped parts on one line so the person sees they were
seen.

## ⓪ Start

An argument wins: a ticket URL, a part's name, a file, or "the whole program". With no
argument the start is what the person is touching, read in this order: the uncommitted
changes, the ticket named by the branch or the last commits, the session so far.

Say what you picked, as the first line:

```
เริ่มที่: <part> (<kind>) - จาก <where you read it>
```

A wrong pick then costs the person one line. "The whole program" is used only when the
person asks for it by name; then survey the parts first and start at the one with the most
parts depending on it.

## ① Ground - before the first question

For the part you will ask about, search in this order and stop at the first source that
states a **business** reason:

| order | where |
|---|---|
| 1 | ADRs |
| 2 | specs and documents in the repo |
| 3 | the ticket: description, acceptance criteria, every comment, every attached image (read an image through the `read-picture` skill, kind `requirement`, loaded through your harness's mechanism) |
| 4 | the project's glossary (`CONTEXT.md`) |
| 5 | commit messages |
| 6 | tests |

In the same search, collect the work **around** the part, for step 2: what starts it and who
does that, the one or two steps before it, the one or two steps after it, and the person who
gets the result. The code answers much of this - a trigger, a recipient, a writer of a row -
and a line read from the code is *cited* with its `path:line`.

Then read the Business note (below). A part whose row says `right` is not asked again.

## ② Show - the Business flow

The **Business flow** is the work as it runs today around the part: who does what, and whom
the work goes to next. Show it before the first question of a sitting. A person asked about
a flow they have never seen can only guess, and a guess teaches nothing.

```
flow ธุรกิจตอนนี้ - <the work this is, in one line>
   1. <who>  <does what>  → <whom the work goes to>            (<Source mark>)
   2. <who>  <does what>  → <whom the work goes to>            (<Source mark>)
 ▶ 3. <the step the part belongs to>                           (<Source mark>)   ← คุณอยู่ตรงนี้
   4. <who>  <does what>                                       (<Source mark>)
ข้ามไป: <the parts the platform made, on one line>
```

- **Three to seven lines.** One or two steps before the part, the part's own step, one or
  two after it, ending at the person who gets the result. A longer flow is cut at the ends
  with `...`; it is not a map of the whole program.
- **A line is a person, one action and a handoff.** The person is a role in the client's
  business; write `ระบบ` only where the program acts with nobody behind it. Use the
  business's words, with a gloss as in *Beginner level*. No table name, no expression, no
  field's logical name - a `path:line` appears only inside the mark.
- **Every line carries a Source mark** (the table in step 5). A step no source states is
  written with `?` and marked *assumed*, and it goes to the note's client questions. Never
  close a gap with a tidy step.
- **What happens, never why.** No reason, no cost, no "so that" on any line. Those are the
  card's, and the person must reach them by thinking.
- **Plain text lines**, as above - not a diagram language. The flow is read in the chat, and
  it must look the same in every harness.
- **Once per sitting.** A later question repeats only the one line it is about, with `▶`.
  When the Backward chain steps to a part that is not on the flow, add its line and show the
  flow again.
- Fewer than three lines have a source: show the lines there are, say
  `เอกสารบอก flow ได้แค่นี้`, and still ask.

## ③ Ask - one business question

```
<the Business flow - on the first question; after that, the one ▶ line>

**คำถาม: <one sentence about the business, not the mechanism>**
```

Then stop and wait.

**Every fact the question needs is on the flow. The answer is not.** The person reasons
from the picture to a consequence, a reason or a decision; they do not recall something they
were never shown. Name the step numbers in the question:

- "Step 4 stops for a month. Which step on the flow breaks first, and what does the person
  there lose?"
- "Step 3 waits 7 days. If it waited 30, who on the flow is hit, and how?"
- "Why does the report in step 4 go to the person in step 5 and not to the one in step 2?"

Two ways to get it wrong:

- **A reading test** - "who gets the report?" when step 5 names them. The answer is on the
  picture, so nothing is learned.
- **A guess** - the question needs a fact that is on no line, or on a `?` line. Put the fact
  on the flow first, or ask something else.

Never "what does this flow do" - that is a mechanism question and belongs to
`asking-to-understand`.

## ④ Receive - the class picks the move

| the answer | the move |
|---|---|
| reaches the business and is right | say so in one line, show the card in short, go on |
| half right | name the right half, add the missing half as fact |
| describes the system, not the business | push **once**: "นั่นคือสิ่งที่ระบบทำ - ใครคือคนที่เดือดร้อน?"; reveal after the second answer, whatever it is |
| wrong | reveal with the source; the verdict is on the answer, never on the person |
| does not know | reveal at once; do not ask that question again this sitting |

**System versus business is the move that pays.** "The flow cannot filter without it" is
true and stops at the program. One push moves the answer to a person. Push once only - with
no document behind the part, the person cannot know, and a second push is a trap.

When the card's business line is *assumed*, the answer gets **no verdict**: write the result
as `not judged`.

## ⑤ Reveal - the card

Fixed order. Headings in the person's language.

```
① ธุรกิจ    <the business reason, 1-3 short sentences>          (<Source mark>)
② เทคนิค    <the technical choice it leads to, with path:line>  (<Source mark>)
③ ADR       "<the sentence that decided it>" (ADR nnnn)   |  ไม่มี ADR พูดถึงส่วนนี้
④ วิธีคิด
   💡 ทริก: "<name>"
      1. <step, applied to this part>
      2. <step>
      3. <step>
   👉 <which step the person's answer reached>
   📌 ใช้อีกเมื่อ: <when to use it again>
📝 จดแล้ว: <part>  ->  <full path of the note>
```

### The Source mark - one on every line of ① and ②, and on every line of the Business flow

| mark | meaning | write |
|---|---|---|
| *cited* (อ้างอิง) | an ADR, file, ticket, commit or test says it | the place: `ADR 0123`, `path:line`, `#151 comment 3` |
| *told* (บอกมา) | a person said it | who, and the date |
| *general knowledge* (ความรู้ทั่วไป) | how the trade works in general - not a fact of this project | the words themselves |
| *assumed* (สันนิษฐาน) | your guess | the words themselves; and the line goes to the note's client questions |

- A guess is never written without *assumed*.
- The person's own answer to a part with no source is *told*, never *cited*.
- *general knowledge* never closes a question about this project's own rule - "why 7 days
  and not 5" stays *assumed* until a source or a person answers it.
- Line ③ quotes the ADR's own sentence. Do not paraphrase it. No ADR: say so, in the words
  of the template.

### The thinking trick - slot ④

Pick one trick from `references/thinking-tricks.md`. Give its three steps **applied to this
part**, say which step the person's answer reached, and say when to use it again. If the way
you reached the answer is not in the file, add it there as a new entry in the same run, in
the file's own shape.

### Beginner level

Short sentences. One idea per sentence. A business word gets a gloss of a few words in
brackets on first use - `liquidator (ผู้ชำระบัญชี - คนที่ปิดบริษัทและจ่ายเจ้าหนี้)`. No sentence
leans on a term the flow or the card has not glossed.

## ⑥ Note - the Business note

**Where:** `~/.claude/learn-the-business/<project>.md`. `<project>` is the folder name of
the **main** git root - the first entry of `git worktree list` - so every worktree of one
project shares one file. Outside a git repo, the working folder's name. The file is never
inside a repo. Write nothing to any harness memory index.

**Shape** - create the folder and the file on the first row:

```markdown
# Business note - <project>

## Asked
| date | part | kind | result | trick | answer (one line) | mark |
|---|---|---|---|---|---|---|

## Not yet asked
- <part> - reached from <part>, <date>

## Questions for the client or BA
- <part>: <the question> - assumed: <the guess>, <date>
```

`result` is one of `right`, `half`, `system`, `wrong`, `did not know`, `not judged`.

**Write the row right after the card**, not at the end of the sitting - a sitting the person
walks out of still leaves its rows. Say the file's full path every time you write.

A `?` line of the Business flow is written under *Questions for the client or BA* when the
flow is shown, not when a card reaches it.

**How a later run uses it:**

- `right` - not asked again.
- any other result - asked again when at least **3 days** have passed **and** the person is
  touching that part again.
- a row whose ADR or code changed after the row's date - mark it `may be old`; it may be
  asked again.
- *Not yet asked* - where "continue" and the next sitting pick up.
- a client question that later gets a source or an answer - move it to *Asked* with its new
  mark.

The person may edit the file, and their edit wins. On request, show the note or clear it.
No file, or a file you cannot read: start from nothing and still ask.

## ⑦ Back - the Backward chain

Each next question is one step backward: the part the last one reads, depends on, or exists
because of.

```
start   the report flow                      (the uncommitted change)
  ↑ 2   the field the flow filters on
  ↑ 3   the table that holds the field
  ↑ 4   who writes a row, and when
  ↑ 5   why the firm must do this at all     <- Business origin
```

Stop at the first of:

- a **Business origin** - the answer is a person, money, a law or a contract, and nothing in
  the program stands behind it;
- no source says more - write the point as a question for the client;
- **five questions** in this sitting. "ต่อ" / "continue" starts the next five from the same
  point.

Where the chain forks - a flow reads three fields - walk one branch and write the others
under *Not yet asked*.

The five and the 3 days rest on no evidence. Say which values you used when it matters.

## ⑧ Close

Emit exactly:

```
**ถามไปแล้ว** - the parts of this sitting, one line each, with the result
**ทางแยกที่ยังไม่ได้ถาม** - the branches written to the note
**ต้องถามลูกค้าหรือ BA** - the assumed lines, as questions
**โน้ต** - the full path
→ ต่อ / ทำ flashcard (learn-with-flashcard) / จบ
```

## Language

Mirror the language the person asked in, the flow and the questions included. Identifiers,
paths and the four Source mark words may stay in English.

## Worked example - one turn

> The person has an uncommitted change in an overdue-callback report flow. The values below
> are made up to show the shape.

```
เริ่มที่: flow รายงานสายค้าง (process) - จากไฟล์ที่แก้ค้างอยู่

flow ธุรกิจตอนนี้ - เจ้าหนี้ (คนที่บริษัทติดเงิน) โทรมาถามเรื่องคดี
   1. เจ้าหนี้  โทรเข้าสำนักงาน  → พนักงานรับสาย                       (cited: #151 description)
   2. พนักงานรับสาย  จดสายลงระบบ  → ผู้รับผิดชอบคดี                   (cited: flows/intake.json:8)
   3. ผู้รับผิดชอบคดี  โทรกลับ แล้วติ๊ก "โทรกลับแล้ว"                   (cited: #151 comment 2)
 ▶ 4. ระบบ  ส่งรายการสายที่ยังไม่โทรกลับเกิน 7 วัน ทุกเช้าวันทำงาน
            → ผู้รับผิดชอบคดี                                          (cited: flows/overduereport.json:3)   ← คุณอยู่ตรงนี้
   5. ผู้รับผิดชอบคดี  ? ทำอะไรกับรายการนี้                              (assumed)
ข้ามไป: วันที่สร้างแถว, เจ้าของแถว

**คำถาม: ถ้าขั้น 4 หยุดทำงานหนึ่งเดือน ขั้นไหนใน flow นี้พังก่อน และคนในขั้นนั้นเสียอะไร?**
```

Answer: *"รายงานจะไม่ถูกส่ง"* - class **describes the system** - push once:

```
นั่นคือสิ่งที่ระบบทำ - ใครคือคนที่เดือดร้อน?
```

Second answer: *"ผู้รับผิดชอบคดี เขาจะไม่รู้ว่ามีสายค้าง"* - class **half right** - reveal:

```
ถูกครึ่งหนึ่ง: คนที่เดือดร้อนคือผู้รับผิดชอบคดี ที่ขาดคือสิ่งที่เขาเสีย

① ธุรกิจ    เจ้าหนี้โทรมาถาม แล้วไม่มีใครโทรกลับ
            ผู้รับผิดชอบคดีต้องรู้ก่อนที่เจ้าหนี้จะร้องเรียน          (cited: #151 description)
② เทคนิค    flow จึงรันทุกเช้าวันทำงาน และส่งถึงผู้รับผิดชอบคดี ไม่ใช่ admin
            flows/overduereport.json:3                                 (cited: flows/overduereport.json:3)
            เลข 7 วัน: ไม่มีเอกสารบอกว่าใครกำหนด                       (assumed: ธรรมเนียมของสำนักงาน)
③ ADR       ไม่มี ADR พูดถึงส่วนนี้
④ วิธีคิด
   💡 ทริก: "หายไปหนึ่งเดือน"
      1. ลบขั้น 4 ออกจาก flow ในหัว
      2. ถามว่าใครรู้ตัวก่อน - คนที่รอรายการ คือผู้รับผิดชอบคดี
      3. ถามว่าเขาเสียอะไร - เจ้าหนี้ร้องเรียนก่อนที่เขาจะรู้
   👉 คำตอบของคุณถึงขั้น 2 ยังไม่ถึงขั้น 3 - ดูขั้น 1 ของ flow: คนที่รออยู่จริงคือเจ้าหนี้
   📌 ใช้อีกเมื่อ: เจอรายงานหรืออีเมลอัตโนมัติที่ไม่รู้ว่ามีไว้ให้ใคร
📝 จดแล้ว: flow รายงานสายค้าง  ->  C:\Users\<you>\.claude\learn-the-business\<project>.md
```

The `?` line of step 5 went into the note's *Questions for the client or BA* when the flow
was shown; the *assumed* line about 7 days goes there with the card.

## Red flags - stop and re-cut

- A question sent before the ground search
- A first question with no Business flow above it
- A flow line with a reason on it, with no mark, or with a table name in place of a person
- A flow of the whole program, or a diagram where plain lines were asked for
- A question the flow already answers, or one that needs a fact the flow does not show
- Two questions in one turn, or a second push on a system answer
- A card that opens with the code instead of a person, money or a rule
- A business line with no mark, or a guess marked *cited*
- A paraphrased ADR on line ③
- A row written only at the end of the sitting, or a note path inside a repo
- A question about a part the platform made

## Handoffs

| Situation | Go to |
|---|---|
| They want to be asked how it **works**, not why the business needs it | `asking-to-understand` |
| They want it explained, not to be asked | `feynman-explain` |
| "Is this value right, and where is it from" - one value, with a verdict | `why-this-logic` |
| One condition or branch, in five parts | `explain-condition` |
| Turn the note into review cards | `learn-with-flashcard` |
