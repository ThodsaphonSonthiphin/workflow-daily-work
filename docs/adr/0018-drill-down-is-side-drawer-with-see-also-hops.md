# Drill-down is a side drawer with see-also hops, not a tooltip

```mermaid
flowchart TD
    Q{"What UI container shows<br/>a drilled-into term?"}
    Q -->|chosen| A["Side drawer: opens with the short<br/>definition, see-also links hop to<br/>related terms (swap drawer content),<br/>each hop a clean static panel"]
    Q -->|rejected| B["Tooltip — one floating line,<br/>can't go deeper; fails the original<br/>'drill down ต่อไม่ได้' pain"]
    Q -->|rejected| C["Inline accordion — expands in the<br/>narration flow but supports no<br/>multi-hop and clutters the prose"]
```

The reader's original pain was *not being able to drill down further* on an unfamiliar
term, while also wanting a short answer first. A **side drawer** satisfies both: it
opens showing the short (CONTEXT.md-sourced, per ADR 0017) definition, then offers
**see-also** links that swap the drawer to a related term — multi-hop depth without the
authoring weight and idempotent-scene complexity of a nested sub-walkthrough. A tooltip
was rejected because it cannot go deeper (the core requirement); an inline accordion was
rejected because it supports no hop and clutters the narration. The drawer is a
**transient overlay independent of step/scene state** — opening or closing it never
mutates the walkthrough's scene state, and navigating steps (Next / Prev / Reset) closes
it — so the skill's idempotent-scene rule stays intact. It also reuses the existing
template's declared-upfront, toggle-visibility panel pattern.
