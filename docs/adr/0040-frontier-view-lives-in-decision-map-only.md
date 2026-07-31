# ADR 0040 — the frontier view lives in decision-map; my-work stays untouched

- **Status:** Accepted
- **Date:** 2026-07-31

```mermaid
flowchart TD
    Q{"where does the frontier<br/>(open + unblocked + unclaimed<br/>tickets) surface?"} -->|chosen| DM["inside decision-map's work-the-map<br/>skill — it loads the map and shows the<br/>frontier at session start; claimed tickets<br/>surface in my-work naturally because<br/>they're assigned"]
    Q -->|rejected| DS["/daily start appends the frontier —<br/>couples dev-workflows to decision-map<br/>and slows every morning, map or not"]
    Q -->|rejected| MW["my-work grows a maps section —<br/>couples the backlog plugins back onto<br/>decision-map and mutates my-work's<br/>identity (my assigned work, not<br/>anyone-can-take work)"]
```

decision-map enters the daily arc as a **WORK-router branch** ("work too big for
one session") with PLAYBOOK rows in the same commit (ADR 0001) — never a sixth
station (ADR 0004). The frontier is decision-map's own view, rendered by the
work-the-map skill from the ops scripts' frontier query (ADR 0037). The backlog
plugins keep their one-directional role: decision-map depends on them, never the
reverse. A claimed ticket appears in `my-work` with no integration at all —
claiming assigns it to you, and my-work lists assigned items.
