# learn-the-business Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the `learn-the-business` skill to the `dev-workflows` plugin: it asks one business question at a time about the part of a program the person is touching, walks backward to the business origin, reveals business -> technical -> ADR -> thinking trick, and keeps a note outside git.

**Architecture:** A prose skill, no script. One `SKILL.md`, one skill-relative reference file of thinking tricks, one thin command. Registration follows the footprint of `learn-with-flashcard`: both manifests, `PLAYBOOK.md`, and the Generated tree under `skills/`, which is produced by `scripts/generate_skills_tree.py` and never hand-edited.

**Tech Stack:** Markdown with YAML frontmatter; JSON manifests; Python 3.10+ for the two tree scripts.

**Spec:** `docs/superpowers/specs/2026-11-21-learn-the-business-design.md` - read it before any task. Decisions: ADRs 0368-0377 in `docs/adr/`.

## Global Constraints

- Work only inside the worktree you were given. Never touch another checkout of this repo - another session is working in the main checkout.
- Windows. Run commands with PowerShell. Edit files with your file-edit tool, never with `Set-Content` / `Out-File` - the manifests hold non-ASCII characters and the console code page corrupts them.
- Skills stay harness-neutral: name actions ("load the skill through your harness's mechanism"), never one harness's tool. Do not write `${CLAUDE_PLUGIN_ROOT}` anywhere in the new skill; its own reference is the skill-relative path `references/thinking-tricks.md`.
- Never hand-edit anything under the repo-root `skills/` folder. It is generated.
- `plugins/dev-workflows/.claude-plugin/plugin.json` and the `dev-workflows` entry of `.claude-plugin/marketplace.json` must report the same version: `0.67.0`.
- Do not edit `plugins/dev-workflows/skills/scrutinize/SKILL.md` or any `sp-*` skill.
- The note path is exactly `~/.claude/learn-the-business/<project>.md`. The four Source mark words are exactly *cited*, *told*, *general knowledge*, *assumed*. The six kinds are exactly data, process, rule, people, output, connection. The result words are exactly `right`, `half`, `system`, `wrong`, `did not know`, `not judged`.
- Commit messages end with the line `Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>`.

---

### Task 1: The skill, its reference file and its command

**Files:**
- Create: `plugins/dev-workflows/skills/learn-the-business/SKILL.md`
- Create: `plugins/dev-workflows/skills/learn-the-business/references/thinking-tricks.md`
- Create: `plugins/dev-workflows/commands/learn-the-business.md`

**Interfaces:**
- Consumes: nothing.
- Produces: a skill whose frontmatter `name` is `learn-the-business`; a command file named `learn-the-business.md`. Task 2 registers both by these exact names.

- [ ] **Step 1: Run the tree check and see it pass before the change**

Run: `python scripts/check_skills_tree.py`
Expected: exit code 0. (This is the baseline. After Step 4 the same check must FAIL, because the new skill is not in the Generated tree yet - Task 2 repairs that.)

- [ ] **Step 2: Create `plugins/dev-workflows/skills/learn-the-business/SKILL.md` with exactly this content**

`````markdown
---
name: learn-the-business
description: "Asks the user ONE business question at a time about the part of a program they are touching - a table, field, flow, rule, role, report or integration - then walks backward to the business origin. After each answer it reveals the business reason first, then the technical choice it leads to, then the ADR text, then a named thinking trick, every line marked cited / told / general knowledge / assumed. Keeps a note of what was asked outside git. Use when the user says \"ถามเรื่อง business\", \"ถามธุรกิจของงานนี้\", \"ทำไมธุรกิจต้องการแบบนี้ ถามผมหน่อย\", \"learn the business\", \"ask me about the business behind this\", \"quiz me on why the business needs this\"; when someone can build a part but cannot say why the business needs it; when onboarding onto a program's domain. Not for the mechanism of an artifact (asking-to-understand), not for explaining on request (feynman-explain), not for tracing one value to its source with a verdict (why-this-logic)."
effort: max
---

# Learn The Business

A developer can build a part of a program and still not be able to say why the business
needs it. This skill asks them - one question per turn, starting at the part they are
touching and walking backward - and after each answer shows the business reason **first**,
then the technical choice that follows from it, then the ADR text, then the way of thinking
that reaches such an answer.

**The failure this prevents:** an explanation that starts at the code ("this flow filters on
this field") and never reaches a person, money or a rule - or one that invents a tidy
business reason no document states, which the developer then repeats to the client.

Design decisions are ADRs 0368-0377 at the marketplace repo root. This file is the procedure.

## Never do these

- **Never** ask a question before the ground search of step 1.
- **Never** ask two questions in one turn.
- **Never** write a guess without the mark *assumed*.
- **Never** write to the project's repo, a tracker or a live system. The only file this
  skill writes is the Business note.
- **Never** refuse to run because the note is missing or unreadable. Start from nothing.

## The session

```
  ⓪ START     argument, or what the person is touching - say what you picked
  ① GROUND    search the sources + read the Business note   (no question before this)
  ② ASK       one business question about one Business part, then stop
  ③ RECEIVE   class of the answer picks the move; a system answer is pushed once
  ④ REVEAL    the card: business, technical, ADR, thinking trick - every line marked
  ⑤ NOTE      one row to the Business note, right away
  ⑥ BACK      one step backward, to ② - until a Business origin or five questions
  ⑦ CLOSE     the fixed closing block
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

Then read the Business note (below). A part whose row says `right` is not asked again.

## ② Ask - one business question

```
<the part, its kind, and where it lives: path:line>          (at most three lines of evidence)

**คำถาม: <one sentence about the business, not the mechanism>**
```

Then stop and wait. The question is about a person, money, a rule or a consequence:

- "If this field were gone for a month, who could not do their work?"
- "Who decided this is 7 days, and what happens to them if it becomes 30?"
- "Who reads this report, and what do they do the next morning?"

Never "what does this flow do" - that is a mechanism question and belongs to
`asking-to-understand`.

## ③ Receive - the class picks the move

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

## ④ Reveal - the card

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

### The Source mark - one on every line of ① and ②

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
leans on a term the card has not glossed.

## ⑤ Note - the Business note

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

## ⑥ Back - the Backward chain

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

## ⑦ Close

Emit exactly:

```
**ถามไปแล้ว** - the parts of this sitting, one line each, with the result
**ทางแยกที่ยังไม่ได้ถาม** - the branches written to the note
**ต้องถามลูกค้าหรือ BA** - the assumed lines, as questions
**โน้ต** - the full path
→ ต่อ / ทำ flashcard (learn-with-flashcard) / จบ
```

## Language

Mirror the language the person asked in, the questions included. Identifiers, paths and the
four Source mark words may stay in English.

## Worked example - one turn

> The person has an uncommitted change in an overdue-callback report flow. The values below
> are made up to show the shape.

```
เริ่มที่: flow รายงานสายค้าง (process) - จากไฟล์ที่แก้ค้างอยู่

flows/overduereport.json:12 กรองแถวด้วย field "โทรกลับแล้วหรือยัง" และอายุเกิน 7 วัน

**คำถาม: ถ้า flow นี้หยุดทำงานหนึ่งเดือน ใครในบริษัทลูกค้ารู้ตัวก่อน และเขาเสียอะไร?**
```

Answer: *"รายงานจะไม่ถูกส่ง"* - class **describes the system** - push once:

```
นั่นคือสิ่งที่ระบบทำ - ใครคือคนที่เดือดร้อน?
```

Second answer: *"น่าจะ admin"* - reveal:

```
① ธุรกิจ    เจ้าหนี้ (คนที่บริษัทติดเงิน) โทรมาถาม แล้วไม่มีใครโทรกลับ
            ผู้รับผิดชอบคดีต้องรู้ก่อนที่เจ้าหนี้จะร้องเรียน          (cited: #151 description)
② เทคนิค    flow จึงรันทุกเช้าวันทำงาน และส่งถึงผู้รับผิดชอบคดี ไม่ใช่ admin
            flows/overduereport.json:3                                 (cited: flows/overduereport.json:3)
            เลข 7 วัน: ไม่มีเอกสารบอกว่าใครกำหนด                       (assumed: ธรรมเนียมของสำนักงาน)
③ ADR       ไม่มี ADR พูดถึงส่วนนี้
④ วิธีคิด
   💡 ทริก: "หายไปหนึ่งเดือน"
      1. ลบ flow นี้ออกในหัว
      2. ถามว่าใครรู้ตัวก่อน - คนที่รอรายงาน คือผู้รับผิดชอบคดี
      3. ถามว่าเขาเสียอะไร - เจ้าหนี้ร้องเรียนก่อนที่เขาจะรู้
   👉 คำตอบของคุณถึงขั้น 2 แต่ชี้ไปที่ admin - ดูผู้รับในไฟล์ จะเห็นว่าเป็นผู้รับผิดชอบคดี
   📌 ใช้อีกเมื่อ: เจอรายงานหรืออีเมลอัตโนมัติที่ไม่รู้ว่ามีไว้ให้ใคร
📝 จดแล้ว: flow รายงานสายค้าง  ->  C:\Users\<you>\.claude\learn-the-business\<project>.md
```

The *assumed* line about 7 days also goes into the note's *Questions for the client or BA*.

## Red flags - stop and re-cut

- A question sent before the ground search
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
`````

- [ ] **Step 3: Create `plugins/dev-workflows/skills/learn-the-business/references/thinking-tricks.md` with exactly this content**

````markdown
# Thinking tricks

The open list `learn-the-business` draws slot ④ of its card from. Each entry is one way of
getting from a part of a program to the business reason behind it. An entry has a name,
three steps, and one "use it again when" line - no more.

When a card needs a way of thinking that is not here, add it below in the same shape, in
the same run.

## who reads this value

1. Find who writes the value and who reads it.
2. The reader is the one who needs it.
3. Ask what the reader decides with it - that decision is the business reason.

Use it again when: a field or a flag has no clear purpose.

## gone for a month

1. Remove the part in your head.
2. Name who notices first.
3. Name what it costs them - that cost is why the part exists.

Use it again when: a report, an email or a job runs and you cannot say for whom.

## before the system

1. Ask how the work was done by hand.
2. Find what hurt in that - lost paper, a late answer, a wrong number.
3. The part answers that hurt.

Use it again when: a process has steps that look pointless from the code.

## who set this number

1. A number comes from a law, a contract, capacity or habit.
2. Find which one, in the documents.
3. If it is habit, or nothing says, it is a question for the client.

Use it again when: a threshold, a limit or a default has no comment beside it.

## follow the money

1. Ask who pays and who is paid.
2. Ask what a delay or a mistake costs.
3. The part protects one of them.

Use it again when: a rule is stricter than the code seems to need.
````

- [ ] **Step 4: Create `plugins/dev-workflows/commands/learn-the-business.md` with exactly this content**

```markdown
---
description: Be asked about the business behind the part of a program you are touching - one question per turn, walking backward to the business origin; each answer is followed by the business reason, the technical choice, the ADR text and a thinking trick. Keeps a note outside git.
argument-hint: "[a ticket URL, a part's name, a file, or 'the whole program' - default: what you are touching now]"
---

Use the **`learn-the-business`** skill. Search the sources first, then ask ONE question.

Argument: $ARGUMENTS
```

- [ ] **Step 5: Verify the three files**

Run:
```powershell
python -c "import io,sys; t=io.open('plugins/dev-workflows/skills/learn-the-business/SKILL.md',encoding='utf-8').read().replace('\r',''); assert t.startswith('---\nname: learn-the-business\n'), 'frontmatter'; assert 'CLAUDE_PLUGIN_ROOT' not in t, 'plugin root token'; assert 'references/thinking-tricks.md' in t; [sys.exit('missing: '+w) for w in ['cited','told','general knowledge','assumed','did not know','not judged','~/.claude/learn-the-business/<project>.md'] if w not in t]; print('SKILL ok')"
python -c "import io; t=io.open('plugins/dev-workflows/skills/learn-the-business/references/thinking-tricks.md',encoding='utf-8').read(); assert t.count('\n## ')==5, t.count('\n## '); assert t.count('Use it again when:')==5; print('tricks ok')"
python -c "import io; t=io.open('plugins/dev-workflows/commands/learn-the-business.md',encoding='utf-8').read().replace('\r',''); assert t.startswith('---\ndescription: ') and 'Argument: ' in t and 'ARGUMENTS' in t; print('command ok')"
python scripts/check_skills_tree.py
```
Expected: `SKILL ok`, `tricks ok`, `command ok`, then `check_skills_tree.py` exits **non-zero** and names `learn-the-business` as missing from the tree. That failure is expected here; Task 2 repairs it.

- [ ] **Step 6: Commit**

```powershell
git add plugins/dev-workflows/skills/learn-the-business plugins/dev-workflows/commands/learn-the-business.md
git commit -m "feat(dev-workflows): learn-the-business - one business question per turn, walking backward (ADRs 0368-0377)" -m "Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>"
```

---

### Task 2: Register the skill - neighbours, playbook, manifests, the Generated tree

**Files:**
- Modify: `plugins/dev-workflows/skills/asking-to-understand/SKILL.md` (frontmatter description; the Handoffs table at the end)
- Modify: `plugins/dev-workflows/skills/feynman-explain/SKILL.md` (the Modes list)
- Modify: `PLAYBOOK.md` (the router diagram; the router table)
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json` (version, description, keywords)
- Modify: `.claude-plugin/marketplace.json` (the `dev-workflows` entry: version, description, keywords)
- Regenerate: `skills/` (by script only)

**Interfaces:**
- Consumes: the skill `learn-the-business` and the command `learn-the-business.md` from Task 1.
- Produces: nothing a later task uses.

- [ ] **Step 1: See the failing check**

Run: `python scripts/check_skills_tree.py`
Expected: non-zero exit, naming `learn-the-business`.

- [ ] **Step 2: `asking-to-understand` - description and hand-off row**

In `plugins/dev-workflows/skills/asking-to-understand/SKILL.md`, in the frontmatter `description`, replace the ending

```
Not for explaining on request (feynman-explain) and not for challenging a plan before building it (grill-then-plan)."
```

with

```
Not for explaining on request (feynman-explain), not for challenging a plan before building it (grill-then-plan), and not for the business reason behind a program (learn-the-business)."
```

In the same file's `## Handoffs` table, add this row directly under the `feynman-explain` row:

```
| They want to be asked why the **business** needs it, with the answer revealed | `learn-the-business` |
```

- [ ] **Step 3: `feynman-explain` - one hand-off line**

In `plugins/dev-workflows/skills/feynman-explain/SKILL.md`, in the `## Modes` list, add this bullet directly after the bullet that ends with `` hand off to `study-design-verify`. ``:

```
- The user wants to be **asked** about the business behind a part of a program, not told →
  hand off to `learn-the-business`.
```

- [ ] **Step 4: `PLAYBOOK.md` - one router edge and one table row**

In the Mermaid block under `## WORKING — the situational router`, add this line directly after the line that starts with `    WORK -- I own this but do not understand it --> ATU[`:

```
    WORK -- I can build it but cannot say why the business needs it --> LTB["learn-the-business"]
    LTB -. make review cards from the note .-> LWF
```

In the table below it, add this row directly after the row that starts with `| work you OWN but do not understand`:

```
| you can build a part but cannot say why the business needs it - "ถามเรื่อง business", "ถามธุรกิจของงานนี้", "ask me about the business behind this" | `learn-the-business` (`/dev-workflows:learn-the-business`) - one business question per turn about the part you are touching (a table, field, flow, rule, role, report or integration), then one step backward at a time until a business origin - a person, money, a law or a contract - or five questions. You answer first; the card then gives the business reason, the technical choice it leads to, the ADR's own sentence and a named thinking trick with the step your answer stopped at. Every line is marked cited / told / general knowledge / assumed, and an assumed line becomes a question for the client. The note of what was asked lives at `~/.claude/learn-the-business/<project>.md`, never in git. Not `asking-to-understand` (the mechanism, no reveal) or `why-this-logic` (one value, with a verdict) (ADRs 0368-0377) |
```

- [ ] **Step 5: Both manifests - version, description, keywords**

In `plugins/dev-workflows/.claude-plugin/plugin.json`:

1. Change `"version": "0.66.0"` to `"version": "0.67.0"`.
2. In `description`, insert the following text immediately before the words `Reflection: reflect (` (keep the space that follows it):

```
Business understanding: learn-the-business (/dev-workflows:learn-the-business - asks ONE business question per turn about the part of a program the user is touching, then walks backward to the business origin; the user answers first, then the card gives the business reason, the technical choice it leads to, the ADR's own sentence and a named thinking trick; every line marked cited / told / general knowledge / assumed, an assumed line becoming a question for the client; the note of what was asked is kept at ~/.claude/learn-the-business/<project>.md, outside git. ADRs 0368-0377). 
```

3. In `keywords`, add after `"feature-walk"` (put a comma after `"feature-walk"`):

```
    "learn-the-business",
    "business-understanding",
    "business-first",
    "thinking-tricks"
```

In `.claude-plugin/marketplace.json`, in the entry whose `"name"` is `"dev-workflows"` only:

1. Change `"version": "0.66.0"` to `"version": "0.67.0"`.
2. In `description`, insert the same text as above immediately before `Reflection: reflect (`.
3. In `keywords`, add the same four keywords after `"saved-vs-applied"` (comma after it).

- [ ] **Step 6: Regenerate the tree and run every check**

Run:
```powershell
python scripts/generate_skills_tree.py
python scripts/check_skills_tree.py
python -c "import json,io; p=json.load(io.open('plugins/dev-workflows/.claude-plugin/plugin.json',encoding='utf-8')); m=[x for x in json.load(io.open('.claude-plugin/marketplace.json',encoding='utf-8'))['plugins'] if x['name']=='dev-workflows'][0]; assert p['version']==m['version']=='0.67.0', (p['version'],m['version']); assert 'learn-the-business' in p['description'] and 'learn-the-business' in m['description']; assert 'learn-the-business' in p['keywords'] and 'learn-the-business' in m['keywords']; print('manifests ok')"
python plugins/dev-workflows/scripts/check_vendored_superpowers.py --strict
python -m pytest scripts -q
git status --short
```
Expected: `check_skills_tree.py` exits 0; `manifests ok`; the vendored check exits 0; pytest passes; `git status --short` lists, under `skills/`, only `skills/learn-the-business/…`, `skills/asking-to-understand/SKILL.md` and `skills/feynman-explain/SKILL.md` (plus the files this task edited by hand). If the generator changed any other file under `skills/`, do not commit it - report which file and stop.

- [ ] **Step 7: Commit**

```powershell
git add plugins/dev-workflows/skills/asking-to-understand/SKILL.md plugins/dev-workflows/skills/feynman-explain/SKILL.md PLAYBOOK.md plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json skills
git commit -m "chore(dev-workflows): learn-the-business in the playbook, both manifests 0.67.0, the neighbours' hand-offs and the skills tree" -m "Co-Authored-By: Claude Fable 5.2 <noreply@anthropic.com>"
```

---

## Self-review (run by the plan's author)

- **Spec coverage:** section 2 -> SKILL "What may be asked"; 3 -> "Start" and "Back"; 4 -> "Ground", "Ask", "Receive"; 5 -> "Reveal", the reference file; 6 -> "Note"; 7 -> "Close"; 8 -> "Handoffs", "Language", Task 2 steps 2-3; 9 -> Tasks 1 and 2; 10 -> the checks in Task 1 step 5 and Task 2 step 6 (the live sitting of spec section 10 is run by the controller after the merge, not by an implementer - it needs a real project and a person).
- **Names:** `learn-the-business`, `references/thinking-tricks.md`, `0.67.0`, the four marks, the six kinds and the six result words read the same in the constraints, the skill text and the checks.
- **No placeholders:** every file's content is given in full; every edit names its anchor text.
