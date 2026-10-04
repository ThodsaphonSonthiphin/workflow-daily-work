# architect-and-verify is one SKILL.md and three reference files

```mermaid
flowchart TD
    Q{the skill carries the run, the document layout, the<br/>change method copied from guide-and-verify, and the<br/>ways to meet a need: one file or several?} -->|chosen| A["SKILL.md holds the run and the rules that hold
    all run long; three reference files are read at
    the moment each is needed — document-template.md,
    change-steps.md, ways-to-meet-a-need.md"]
    Q -->|rejected| B["one SKILL.md, as guide-and-verify is — the
    copied change method is most of that skill's 289
    lines; with the run, the layout and the ways on
    top, the file is far more than is read at one
    moment"]
```

First stated in the design spec of 2026-10-03 (§3) and approved with it by the owner the
same day. `SKILL.md` names the moment each reference is read: the document template
before the document is created, the ways when the first need needs one, the change steps
before the first change is guided or the first test fails.

The references are the skill's own files, named by skill-relative path. `change-steps.md`
is where the copy from `guide-and-verify` lives (ADR 0231), with one provenance line at
its top and nothing that tells a reader to load the original.
