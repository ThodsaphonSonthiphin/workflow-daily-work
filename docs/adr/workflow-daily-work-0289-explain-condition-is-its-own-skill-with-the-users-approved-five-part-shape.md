# explain-condition is its own skill, with the user's approved five-part shape

```mermaid
flowchart TD
    Q{the user asked twice "what does this flowchart node mean"<br/>and said the answers were very good - make it reusable,<br/>and keep the same format} -->|chosen| A["new dev-workflows skill explain-condition: one
    condition per answer in five fixed parts - meaning in
    bold, how it works on the real expression, a table of
    real test rows (pass and fail), the reasons with their
    source, the file:line - copied from the approved answers"]
    Q -->|rejected| B["a mode of feynman-explain - its card has fuzzy-parts,
    gaps and 30-second slots the user did not get and did
    not ask for; a mode would change the shape that was
    approved"]
    Q -->|rejected| C["a mode of why-this-logic - it gives every decision
    point a proof mark and a verdict and writes docs/why/;
    the user asked what a check means, not whether it is
    right"]
    Q -->|rejected| D["a feedback memory in one project - the format would
    not travel to other repos or harnesses"]
```

Ruled 2026-11-04 by the user (Pon), in the MG-AI-Creditor-Enquiry-Agent session that
explained the ADO #148 match flowchart: "อธิบายคำถามดีมาก สร้างสกิลไว้ ใช้ซ้ำหน่อย", then
"อธิบายต้องอยู่ใน format เดิม". The name `explain-condition` was chosen by the user over
`condition-explain`, `what-does-this-check` and `explain-branch`. The skill's worked
example is the second approved answer, verbatim. The format is a contract: the skill says
not to improve it.
