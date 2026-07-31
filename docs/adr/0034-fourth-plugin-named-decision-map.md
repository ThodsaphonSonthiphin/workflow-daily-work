# ADR 0034 — the fourth plugin is named `decision-map`

- **Status:** Accepted
- **Date:** 2026-07-31

```mermaid
flowchart TD
    Q{"what is the wayfinder-style<br/>plugin called?"} -->|chosen| DM["decision-map — names the unit<br/>(decision ticket) and the artifact<br/>(the map); /decision-map:* commands;<br/>decision-map:map tracker tag"]
    Q -->|rejected| WF["wayfinder — collides with<br/>mattpocock's 194K-install original;<br/>imports expectations our ADO-first<br/>adaptation won't match"]
    Q -->|rejected| CW["chart-work — 'chart' reads as<br/>graphs; hides that the unit<br/>is a decision"]
    Q -->|rejected| PF["pathfinder — metaphor only;<br/>says nothing about<br/>decision tickets"]
```

Descriptive over homage: the upstream skill itself just renamed its unit to
"decision ticket" because people mis-read tickets as implementation slices — our
name bakes that lesson in from the start. The plugin dir, command prefix
(`/decision-map:<skill>`), tracker tag/label prefix (`decision-map:map`), and
glossary terms all derive from this name.
