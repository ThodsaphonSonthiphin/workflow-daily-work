# Engine narration contract = diagram's nested shape; tables migrates onto it

```mermaid
flowchart TD
    Q{"Which narration DOM becomes the shared engine's<br/>single canonical contract? (the two modes disagree today)"}
    Q -->|chosen| A["Diagram's NESTED shape: badge + title + body inside one<br/>#narration box; 3-arg setNarration(cls,title,bodyHTML).<br/>tables migrates onto it (drops its outer .scene card +<br/>scene-title-above-narration chrome)"]
    Q -->|rejected| B["Tables' CARD shape: outer .scene card with a .scene-title<br/>header above a bare #narration — diagram's per-variant<br/>title-recolor logic would have to move; tables is the<br/>heavier chrome to keep"]
    Q -->|rejected| C["A neutral third contract, migrate BOTH — most work,<br/>both shipped files churn for little gain"]
```

The shared engine (ADR 0020) needs one canonical narration contract, but the two shipped
templates differ: diagram nests badge + title + body inside a single `#narration` box
with a 3-arg `setNarration(cls, title, bodyHTML)`, while tables wraps an outer `.scene`
card whose `.scene-title` header (badge + title) sits *above* a separate bare `#narration`
body, with a 2-arg `setNarration` plus a separate `setSceneTitle`. We adopt **diagram's
nested shape** as the engine contract because diagram is the stated default mode and its
narration already carries the per-variant title recoloring and the full
`warn/error/success/magic` variant set; **tables migrates onto it** (its outer card /
header-above chrome is replaced by the nested box). This is a real, user-visible change to
a shipped template — hence its own ADR — and it is the gating prerequisite: the engine
cannot be extracted until the narration contract is settled. The background token shift
that rides along with the `:root` hoist is reconciled to diagram's `#0a0e14` (the darker,
higher-contrast default).
