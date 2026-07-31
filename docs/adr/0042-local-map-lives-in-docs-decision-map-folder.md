# ADR 0042 — the local-markdown map lives in `docs/decision-map/<slug>/`

- **Status:** Accepted
- **Date:** 2026-07-31

```mermaid
flowchart TD
    Q{"where does the tracker-less<br/>fallback map live?"} -->|chosen| DIR["docs/decision-map/&lt;slug&gt;/ —<br/>map.md + tickets/&lt;name&gt;.md;<br/>claim/close as frontmatter fields;<br/>committed via assisted git"]
    Q -->|rejected| ONE["single docs/decision-maps/&lt;slug&gt;.md —<br/>tickets lose their own identity and<br/>lifecycle; concurrent sessions collide<br/>editing one file; the map stops<br/>being an index"]
    Q -->|rejected| HID["hidden .decision-map/ state dir —<br/>a third state store, against the<br/>intent of ADR 0014's one-state-file<br/>boundary; invisible to the team"]
```

The fallback map sits on the **repo-docs side** of the ADR 0014 boundary: durable,
reviewable knowledge committed through assisted git — not a state file. One folder
per effort (`<slug>` = lowercase-kebab destination); `map.md` carries the map body
(Destination / Notes / Decisions so far / Not yet specified / Out of scope);
`tickets/<name>.md` gives each Decision ticket its own file, name, and lifecycle —
`status`, `assignee` (the claim), `blocks` as frontmatter, mutated only by the local
ops script (ADR 0037), so all three backends keep identical semantics.
