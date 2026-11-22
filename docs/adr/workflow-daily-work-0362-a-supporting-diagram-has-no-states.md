# A supporting diagram has no states

```mermaid
flowchart TD
    Q{"Can a scene change a supporting diagram,<br/>for example light one attribute of a class box at step 7?"}
    Q -->|chosen| A["No. A supporting diagram is a fixed picture.<br/>A scene only shows or hides the panel that holds it.<br/>Emphasis (hot, bad, good) is written into the markup"]
    Q -->|rejected| B["Give the kit setters and a registry, like a mode pack:<br/>two things then change at one step, every mode's clear()<br/>has to reset the kit too, and the kit stops being<br/>independent of the mode"]
```

A step changes one thing, and that thing is on the main diagram. If a supporting diagram
also changed, the reader would have two places to watch. The kit therefore has no renderer,
no registry and no setters. A class box that must look different at a later step is a
second panel with a second picture.

This keeps the kit independent of the mode pack: every mode's `clear()` already hides every
`.wt-panel`, and that is all a supporting diagram needs.
