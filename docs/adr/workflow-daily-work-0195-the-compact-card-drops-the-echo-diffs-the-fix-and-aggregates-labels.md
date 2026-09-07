# The compact card drops the echo, diffs the fix, and aggregates the labels

```mermaid
flowchart TD
    Q{"Past the threshold, the card must get much<br/>shorter without losing what ADR 0175 requires<br/>- both levels - or what #18 requires - a<br/>copy target. The full card grows in THREE<br/>places at once. Which give way?"}
    Q -->|chosen| A["All three, each in its own way. Stop echoing<br/>the original. Show the minimal fix as its<br/>CHANGED LINES only. Replace per-instance<br/>labels with per-class counts. Both levels<br/>survive; the natural version stays whole."]
    Q -->|rejected| B["Aggregate the labels only. Smallest change to<br/>the card's shape, but on a long input the<br/>labels were never the biggest term - three<br/>copies of the text were. 116 lines becomes<br/>51, of which 42 are duplication."]
    Q -->|rejected| C["One card per paragraph. Loses nothing and<br/>gains nothing: the same total, now in four<br/>blocks, and the text to send is split across<br/>them - which breaks the copy target #18<br/>required."]
    Q -->|rejected| D["Refuse, and ask the user to split the input.<br/>Pushes the work back onto the person who<br/>reached for the skill BECAUSE the writing<br/>was hard."]
```

Each of the three terms is cut by the thing that makes it redundant rather than by a blanket
truncation:

- **The echo goes.** The user's original is one scroll away in their own message. It is the
  only part of the card that carries no new information at all.
- **The minimal fix becomes a diff of its changed lines**, not a full reprint. Its job is to
  show what was wrong; the whole corrected text is already visible in the natural version
  below it.
- **Per-instance labels become per-class counts** — `article ×9 · sv-agreement ×7 ·
  verb-tense ×4 · capitalisation ×3`. This is the shape the **Mistake profile** already
  stores, so the summary is native rather than invented.

The natural version stays **whole**, because it is the text the user actually sends, and
#18 made the copy target a requirement.

On the worked example — a PR description, N=14, C=23 — this takes the card from **116 lines
to about 28**.

**The order is unchanged, and that matters.**
[ADR 0179](workflow-daily-work-0179-the-correction-card-is-lesson-first-and-explains-every-change.md)
chose lesson-first so the eye passes through the correction on its way to the answer. The
compact card keeps that: what was wrong comes first, the natural version last. Only the
redundancy is removed, never the ordering that carries the pedagogy.

**Amends ADR 0179**, which called the card a fixed format. It has two forms — full and
compact — selected by
[ADR 0194](workflow-daily-work-0194-the-compact-card-triggers-on-predicted-length-not-input-size.md)'s
predicted-length rule. Both are fixed; neither is free prose.
