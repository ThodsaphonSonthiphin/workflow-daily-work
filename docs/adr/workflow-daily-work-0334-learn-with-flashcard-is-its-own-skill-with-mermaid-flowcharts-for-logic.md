# learn-with-flashcard is its own skill, with Mermaid flowcharts for logic

```mermaid
flowchart TD
    Q{"the user asked for a flashcard page to turn the<br/>session's answers into long-term memory, then said<br/>make it a skill named learn with flashcard"} -->|chosen| A["new dev-workflows skill learn-with-flashcard:
    programmer-level cards (name, inputs with keys,
    outputs, tables, choice values, logic), every logic
    answer a Mermaid flowchart + a real example + its
    source, built from one HTML template and checked by
    a script before it is published"]
    Q -->|rejected| B["a mode of problem-description - that is a linear,
    step-by-step walkthrough of one problem; flashcards
    are many atomic cards graded and revisited"]
    Q -->|rejected| C["logic answered as bullet lists - the first deck did
    this and the user rejected it: logic must be a
    flowchart"]
    Q -->|rejected| D["ASCII flowcharts - the second deck did this and the
    user rejected it: the flowchart must be Mermaid"]
    Q -->|rejected| E["the host's built-in Mermaid rendering - it renders
    static blocks at page load, and cards are drawn at
    run time; the template loads Mermaid from cdnjs and
    calls mermaid.render per card instead"]
    Q -->|rejected| F["a feedback memory in one project - the format
    would not travel to other repos or harnesses"]
```

Ruled 2026-11-07 by the user (Pon), in the MG-AI-Creditor-Enquiry-Agent session about the
phone-log flows (ADO #148-#150). The first deck answered logic with lists; the user said
"แก้ใหม่ logic ต้องเป็น flowchart" and asked for programmer questions ("flow แรก ชื่ออะไร
รับค่าอะไร return ค่าอะไร และ logic เป็นไง"). The second deck drew ASCII flowcharts; the user
said "flow chart ต้องเป็น mermaid diagram". Then: "create the skill from this ... the name
skill is learn with flashcard". The skill's worked example is that third deck, verbatim
(`assets/example-phone-log-flashcards.html`); the template is the same page with sample cards.
