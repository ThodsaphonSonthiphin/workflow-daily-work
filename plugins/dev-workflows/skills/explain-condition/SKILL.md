---
name: explain-condition
description: >-
  Explain ONE condition, check or branch in a piece of logic - a flowchart node, an if, a
  filter, an expression term - in a fixed five-part answer: what it checks in one line, how
  it works step by step on the real expression, a table of examples from the real test data
  (pass and fail), the reasons behind each design choice with their source, and the file and
  line where it lives. Use when the user quotes a node, branch label or term and asks what
  it means - "X หมายความว่าไง", "X คือยังไงนะ", "เงื่อนไขนี้คืออะไร", "what does this check
  mean", "what does this branch do", "explain this condition". Not for a whole concept or
  system (feynman-explain), not for "is this value right / where does it come from" with a
  verdict per row (why-this-logic), and not for a clickable walkthrough (problem-description).
argument-hint: "<the condition, node label or expression term to explain>"
---

# Explain Condition

One condition, one answer, always in the same shape. The user learns where to look:
the meaning is first, the mechanism second, the proof third, the reasons fourth and the
source last. The shape is fixed because the user approved it - do not improve it.

## Before you write

1. **Find the real logic.** Open the expression, code or runbook step that implements the
   condition. A diagram label is a summary; the expression is the truth. If the label and
   the expression disagree, explain the expression and say in one line that the label is
   wrong.
2. **Find the real data.** Look for test rows, fixtures, seed files or run results that
   pass and fail this condition. Read the values; do not recall them.
3. **Find the reasons.** For each design choice inside the condition (why this field, why
   blank fails, why it runs before another check), find the decision, ticket, spec or
   person that set it. A reason with no source is written as "no source found", never
   made up.

## The output contract

Emit these five parts, in this order, and nothing else. Write in the user's language;
keep code names, field names and IDs in English in backticks.

| # | Part | ไทย | English | Cap |
|---|---|---|---|---|
| 1 | Meaning | (no heading) one or two sentences, the core meaning in **bold** | (no heading) | ≤ 2 sentences |
| 2 | Mechanism | `**ทำงานแบบนี้**` | `**How it works**` | numbered, ≤ 5 steps |
| 3 | Proof | `**ตัวอย่างจากข้อมูลทดสอบ**` | `**Examples from the test data**` | table, 2-4 rows |
| 4 | Reasons | `**ทำไม…**` (one bold question per reason) | `**Why…**` | 1-3 reasons, ≤ 3 sentences each |
| 5 | Source | (no heading) one line with `file:line` links | (no heading) | 1 line |

**Part 1 - Meaning.** Say what the condition checks in plain words, and when it runs
(which earlier branch leads here). Put the one idea the user must keep in bold. Do not
restate the question.

**Part 2 - Mechanism.** The steps in the order the logic runs. Name each real piece in
backticks with its plain meaning (`SameAcn` = the rows whose ACN equals the top row's).
The last step always says both exits: pass → where it goes next; fail → which result.

**Part 3 - Proof.** Columns: the input, the rows or values the logic sees, the result.
The result cell starts with the **bold result**, then a short reason. Include at least one
pass and one fail. A row that is not in the real data is marked `(สมมติ)` / `(made up)`;
use one only when the real data has no case for that path.

**Part 4 - Reasons.** Each heading is the question the user would ask next ("ทำไม ACN
ว่างต้องไม่ผ่าน"). Answer from the source found in "Before you write", and name it (the
decision number, the ticket, the person's question). If one check depends on another
("why this check runs before the date check"), that is a reason worth a heading.

**Part 5 - Source.** One line: where the logic lives, as clickable `file:line` links in the
harness's link format, and which part of the expression is which step.

No preamble, no "good question", no analogy, no summary paragraph, no offer of next steps.
Default budget about 300 words. Over budget means fewer reasons or fewer table rows, never
a new section.

## Follow-up questions

The user often asks about the next node of the same logic. Answer each one in the same five
parts. Do not reference "as above" - each answer stands alone, because the user may copy it
into a document or a chat.

## Worked example

> **User** (pointing at a flowchart node): `All hits have the same non-blank ACN?` หมายความว่าไง

````
คำถามนี้เช็กว่า **แถวที่เจอทั้งหมดเป็นบริษัทเดียวกันหรือเปล่า** flow ใช้ ACN เป็นตัวบอก เพราะ ACN คือเลขประจำบริษัท บริษัทหนึ่งมีเลขเดียว

**ทำงานแบบนี้**

1. flow ดู ACN ของแถวที่ 1 (`Top`) ก่อน ถ้า ACN ว่างก็ไม่ผ่านทันที
2. flow กรองหาแถวที่ ACN ตรงกับแถวที่ 1 (`SameAcn`)
3. ถ้าจำนวนแถวที่ตรง เท่ากับจำนวนแถวที่เจอทั้งหมด (`HitCount`) แปลว่าทุกแถวเป็นบริษัทเดียวกัน ผ่าน แล้วไปเช็กวันที่ต่อ
4. ถ้ามีแถวไหน ACN ไม่ตรง แปลว่าเป็นคนละบริษัท ได้ Ambiguous

**ตัวอย่างจากข้อมูลทดสอบ**

| ชื่อที่ค้น | แถวที่เจอ | ผล |
|---|---|---|
| TEST Harbour Bakery | 0002: ACN 222333444<br/>0004: ACN 222333444 | **ผ่าน** บริษัทเดียวกัน แล้วไปเช็กวันที่ ได้ Candidate 0004 |
| TEST Wattle Pty Ltd | 0005: TEST Wattle **Holdings** Pty Ltd, ACN 555666777<br/>0006: TEST Wattle Pty Ltd, ACN 666777888 | **ไม่ผ่าน** คนละบริษัท ได้ Ambiguous |
| (สมมติ) Bankrupt Estate 2 แถว | ทั้ง 2 แถว ACN ว่าง | **ไม่ผ่าน** ACN ว่าง ได้ Ambiguous |

**ทำไม Wattle เจอ 2 บริษัท**
decision 7 ตัดคำว่า `HOLDINGS` ออก ชื่อทั้ง 2 จึงกลายเป็น `TEST WATTLE` เหมือนกัน ถ้าดูแค่ชื่อจะแยกไม่ออก ACN ที่ต่างกันจึงบอกว่าเป็นคนละบริษัท

**ทำไม ACN ว่างต้องไม่ผ่าน**
ถ้าไม่มี ACN เราพิสูจน์ไม่ได้ว่าเป็นบริษัทเดียวกัน ตัวอย่างคือ Bankrupt Estate ของบุคคล ซึ่งไม่มี ACN (เช่น MG-TEST-0007) ถ้ามี 2 แถวที่ชื่อเหมือนกันแต่ไม่มี ACN อาจเป็นคนละคนที่ชื่อเหมือนกัน

**ทำไมต้องเช็กข้อนี้ก่อนเช็กวันที่**
วันที่ช่วยเลือกได้แค่ว่าการแต่งตั้งครั้งไหนของ**บริษัทเดียวกัน**เป็นครั้งปัจจุบัน ถ้าใช้วันที่เลือกระหว่าง 2 บริษัท ก็เท่ากับเดา และ agent อาจพูดชื่อบริษัทผิดให้ผู้โทรฟัง (decision 8: Pon ถามว่า "what if we send the wrong name?")

expression อยู่ที่ [runbook.md:573](documents/runbook.md#L573) (`SameAcn`) และ [บรรทัด 578](documents/runbook.md#L578) คือส่วนที่เป็น `not(empty(Top acn))` กับ `equals(length(SameAcn), HitCount)`
````

What makes it work: the bold line answers the question before any detail; the steps use
the real action names; the table shows a pass, a fail and the edge case; every "why" names
its decision; the last line lets the user check the expression themselves.

## Red flags - stop and re-cut

- A heading that is not in the contract, or a closing summary or offer
- Steps that describe the diagram label instead of the real expression
- A table with only passing rows, or a made-up row that is not marked
- A "why" with no source and no "no source found"
- Over about 300 words
