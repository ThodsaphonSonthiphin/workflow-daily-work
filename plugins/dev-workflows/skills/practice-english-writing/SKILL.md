---
name: practice-english-writing
description: Fix and teach the user's written English, on demand. Turns Thai or broken English into natural everyday English, shows the smallest correction with every change labelled by error class and explained in Thai, then the natural version. Use when the user invokes /practice-english-writing, or asks to check / fix / correct their English, "แก้อังกฤษให้หน่อย", "ประโยคนี้ถูกไหม", "เขียนอังกฤษยังไงดี", "is my English right", "make this sound natural", "help me write this in English" — or hands over a message, commit message, PR description or chat reply they are about to send. Writing only; for English the user is trying to UNDERSTAND, use feynman-explain instead.
---

# Practice English Writing

Fix the message **and** teach from it. The user is a Thai speaker writing English to an
AI, to a tracker and to people. The correction is worth little on its own; the gap between
what they wrote and what a fluent writer would write is the lesson.

Design decisions are ADRs 0175–0196 at the marketplace repo root. This file is the
procedure; the ADRs are the reasoning. The nine error classes and their Thai explanations
are canonical in `${CLAUDE_PLUGIN_ROOT}/references/english-error-explanations.md` and are
never restated here or anywhere else.

## Never do these

- **Never** change anything inside a **protected span** (below).
- **Never** silently change the user's meaning. Where the text cannot carry it, guess and
  flag — or ask, if the guess would change the scope of an instruction.
- **Never** refuse a correction because the profile is missing or malformed. Degrade.
- **Never** report an error the register does not have. A subjectless, article-less
  imperative is *correct* in a commit subject.

## Step 1 — Read the register

Work out what kind of text this is, and **name it on the card**. The user reads that line;
a wrong read then costs them one sentence to fix rather than a wrong lesson to unlearn.

| register | what it looks like | what changes |
|---|---|---|
| `commit subject` | one short line, imperative, often no subject and no full stop | imperative kept; no subject expected; articles often correctly absent |
| `prompt to an AI` | an instruction or question aimed at a tool | direct and unambiguous; brevity is fine |
| `chat to a person` | conversational, addressed to someone | natural, contractions welcome |
| `PR description` / long form | multi-line, structured, headings or bullets | structured; fuller sentences |

**Natural everyday English is the default**, not the only setting — use it when the text
does not clearly belong to one of the above.

## Step 2 — Hold out the protected spans

Copy these through **byte for byte**:

- **Absolute, no judgement**: anything inside backticks, fenced code blocks, or quotes.
- **Best-effort, and say so**: bare tokens that look like identifiers — camelCase,
  snake_case, dotted paths, file extensions, flags, version strings, numbers.

When you protect a bare token, **flag it**: `⛊ I left getUserById alone — it looks like an
identifier. Tell me if it is not.` A wrong guess then costs one line; an unflagged wrong
guess corrupts the message.

## Step 3 — Produce both levels

Always both. The gap between them is the teaching.

1. **Minimal fix** — the smallest correction that makes it right. Every changed token is
   highlighted, and every change carries **one** error class from the reference file (a
   second class may be added where a span genuinely belongs to two). The user's frame,
   vocabulary and length survive.
2. **Natural version** — how a fluent writer would put the same message, in the register
   from Step 1. It may reorder, shorten or reframe freely.

**Highlight every changed token, including capitalisation** — and mark a capitalisation
change distinctly (underline it, or say so), because unlike `return` → `returns` the word
looks unchanged at a glance.

Where the meaning is not recoverable from the text — Thai leaves noun number unmarked, so
this is common — **guess the likely reading and flag it**: `⚑ GUESSED: plural`. Render a
guess flag **differently from an error label**: a guess says *I decided something you did
not say*; an error label says *you got this wrong*. **Ask instead of guessing** when the
guess would change the **scope of an instruction** — how many things get deleted, which
records are touched.

## Step 4 — Choose the card's form

Predict the card's length: roughly `3N + C + 2F + 5`, where `N` is lines of the user's
text, `C` is the number of changes, and `F` is the number of **distinct** error classes
currently in full form. Every change costs a line; the Thai explanation is printed **once
per class, not once per change**. **Over about 40 lines, use the compact form.**

**Full card** — register · the user's original · minimal fix · every change on its own line
with its class and Thai explanation · guess and protected flags · natural version · the gap
between the two levels, in Thai.

**Compact card** — same order, three cuts: **drop the echo** of the original (it is one
scroll up), show the minimal fix as its **changed lines only**, and replace per-instance
labels with **per-class counts** (`article ×9 · sv-agreement ×7`). The **natural version
stays whole** — it is what the user sends.

Both forms are fixed formats, and both keep the lesson first and the answer last.

## Step 5 — Explain, unless it is time to stop

Take each class's two-line Thai explanation from
`${CLAUDE_PLUGIN_ROOT}/references/english-error-explanations.md`. Never write your own; if
a class has no entry there, the class does not exist yet — use `other` and add a free-text
note.

A class is shown in **full** for its first **10 distinct days** of exposure, then in
**short form** — the fix and the class label, no explanation. Two things bring the full
text back:

- **Relapse** — the class fires again after **14 quiet days**. Say how long it was gone.
- **The user asks.** Expand for that message only; asking is not relapse, so it does not
  reset the collapse.

A `Caveat` in the reference file is the precise version of an explanation. Show it only on
request. Its absence means the two lines are accurate as written.

Those three numbers — 10 days, 14 days, ~40 lines — **rest on no evidence**. State which
values you used when it matters, so a wrong guess is visible and cheap to change.

## Step 6 — Record it

The **mistake profile** is one Markdown file at
`~/.claude/practice-english-writing/profile.md`. It is shared by every project — Claude's
own memory directory is per-project, and four partial histories measure nothing. **Write
nothing to any `MEMORY.md`.**

Per error class, keep: a **count**, a **lastSeen** date, the number of **distinct days** it
has fired (at most one per calendar day), a breakdown **by register**, and a **capped**
FIFO sample of a few real before/after pairs. It is an aggregate, never a log. Carry a
**label-set version** so a future slug rename can migrate the history.

Rewrite the file rather than appending, so hand edits are absorbed. The user may edit it
and their edits win — there is nowhere else it is written. Samples are the user's own
sentences on disk; if they ask to clear them, clear them.

**Degrade, never fail.** No profile means every count is zero and every explanation is in
full form. A class you cannot parse is treated as absent. Neither is a reason to refuse a
correction.

## Step 7 — Accept a correction

The user may say, in plain words and in either language, that the register was wrong —
*"that was a commit message"*, `อันนี้ commit message`. No command word, ever.

Read it as a correction when it **names a register and follows a card**; otherwise it is an
ordinary message to correct. If that is genuinely unclear, guess and flag it.

Then **re-run the whole correction** from the original text under the stated register. Do
not merely relabel: the register decides which classes apply, so a relabel leaves false
error labels under a corrected header. The user's stated register beats the detector.

**Replace what the first run wrote in the profile.** Counts that were never errors under
the right register are **deleted**, not moved to another bucket. This works only while that
write is still in the conversation; afterwards, tell the user the profile is theirs to edit.
