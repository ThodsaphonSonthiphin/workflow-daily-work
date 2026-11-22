# The walkthrough controls sit above the narration

```mermaid
flowchart TD
    Q{"The Previous, Next and Reset buttons are the last thing<br/>on the page. Where do they go?"}
    Q -->|chosen| A["Directly under the row of step dots, above the narration.<br/>Nothing above them changes height, so they never move"]
    Q -->|rejected| B["A bar fixed to the bottom of the window:<br/>a viewer that sizes the iframe to its content has no<br/>window edge to fix to, so the bar ends up last again,<br/>and it covers the bottom of the diagram"]
    Q -->|rejected| C["Leave them last and rely on the arrow keys:<br/>a reader on a touch screen, or one who has not clicked<br/>in the page yet, still scrolls to find them"]
```

The engine's §HTML put the controls after the mode content. On a tall mode content the
reader scrolls past it to reach them: the sequence diagram of the walkthrough published on 2026-11-20 is
664 units high. The controls also moved between steps, because the panels beside or under
the diagram differ in height, so a reader pressing Next again had to find the button first.

The order of the engine shell is now: title, step dots, controls with the keyboard hint
(ADR 0357), narration, mode content. Everything above the controls has a fixed height, so
the buttons stay where the pointer is. This changes the page for every mode, because the
controls are part of the engine (ADR 0020).
