# Sequence is a fourth mode pack, and the diagram pack stays as it is

```mermaid
flowchart TD
    Q{"A published walkthrough drew a UML sequence diagram by<br/>editing a copy of the diagram pack and adding its own CSS.<br/>How does the skill get a sequence diagram of its own?"}
    Q -->|chosen| A["A new pack, references/mode-sequence.html, registers<br/>modeRenderers['sequence']: lifelines, messages, fragments,<br/>a legend and a two-column layout. No engine edit.<br/>mode-diagram.html does not change"]
    Q -->|rejected| B["A recipe in SKILL.md for editing a copy of the diagram pack:<br/>the sequence CSS is rewritten in every session, so two<br/>walkthroughs look different and the checker cannot test it"]
    Q -->|rejected| C["Turn the diagram pack into a sequence diagram:<br/>loses the boxes-and-wires picture, which is the better one<br/>when one wire fires many times or a value builds up in a box"]
```

The walkthrough published on 2026-11-20 is the evidence that a sequence diagram
explains a flow well: five lifelines, eleven numbered messages, an `opt` frame around the
proposed part, one message lit per step. None of it is in the skill. That session wrote
about sixty lines of `.seq-*` and `.uml-*` CSS on top of a copy of `mode-diagram.html`, so
the next session cannot reproduce it and `check-walkthrough.py` knows nothing about it.

The sequence diagram becomes a mode pack of its own, the fourth. Adding it is the case
ADR 0020 was built for: one file that registers one renderer, and zero engine edits. ADR
0023 asked whether a time-ordered mode would need a layout hook in the engine. It does not:
the published walkthrough ran on the unmodified engine, because every lifeline and message
position is authored markup and every state is a class on an element declared up front.

The diagram pack is not changed and not renamed. It remains the mode for a flow where the
wiring is the story.
