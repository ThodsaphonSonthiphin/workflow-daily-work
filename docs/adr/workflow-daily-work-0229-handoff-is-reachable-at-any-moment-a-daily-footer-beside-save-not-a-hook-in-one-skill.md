# `handoff` is reachable at any moment — a `/daily` footer beside Save, not a hook inside one skill

```mermaid
flowchart TD
    Q{where does a user find handoff — it must work<br/>at every step of any conversation, not one<br/>moment of one skill} -->|chosen| A["a standalone command usable any time, plus
    a second /daily menu footer line beside Save —
    '🚀 Hand off anytime: /dev-workflows:handoff
    [cloud]' — plus its PLAYBOOK row and a
    glossary pair (Save = your resume-point here;
    Handoff = the work travels); no skill is
    edited to call it"]
    Q -->|rejected| B["a third option in sp-writing-plans'
    execution question — visible at one moment of
    one skill, and it edits a vendored copy the
    resync checker must then guard"]
    Q -->|rejected| C["a sentence in grill-then-plan Step 6 —
    the same one-skill coupling, and invisible at
    the moment the choice is made"]
    Q -->|rejected| D["PLAYBOOK row only — nothing reminds the
    user in the flow, and save proved a footer
    is what gets an accelerator used"]
```

The first draft of this decision wired `handoff` into the plan's execution
question (the moment it was missing on 2026-09-14). The owner rejected that
shape: a handoff has to be possible at every step of a conversation with the
agent — mid-debug, mid-grill, mid-review — not at one moment of one skill. The
repo already has an accelerator with exactly that property: `/daily save`, a
footer line on the station menu that is not a station (ADR 0004) and captures
the user's own resume-point in this repo. `handoff` is its twin for the case
where the *work* travels — to another harness, machine, colleague or a Claude
Code cloud session — so it takes the same shape: a standalone command
(`/dev-workflows:handoff [cloud] <what the next session is for>`) invocable at
any time, a second footer line on the `/daily` menu beside Save, one PLAYBOOK
row, and a glossary entry that states the Save / Handoff distinction so nobody
reaches for the wrong one. No skill is edited to call it, and `sp-writing-plans`
stays as upstream shipped it; the circle stays five stations — two footers are
still footers.
