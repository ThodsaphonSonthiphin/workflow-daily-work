# The ER diagram skill draws from a model file through a bundled script, not by hand

```mermaid
flowchart TD
    Q{"How does the new ER diagram skill turn a system into the tiered ER page?"} -->|chosen| A["A: the agent writes one model file<br/>(tiers, tables, columns, descriptions, relationships);<br/>a script in the skill lays out, draws and checks the page"]
    Q -->|rejected| B["B: the agent writes every coordinate by hand each time:<br/>every change moves boxes and lines by hand;<br/>labels overlapped twice in one session"]
    Q -->|rejected| C["C: Mermaid erDiagram:<br/>no tiers, no tooltip per column or line,<br/>Mermaid decides the layout"]
```

Status: accepted (Pon, 2026-11-26, "a").

The skill is made from a tiered data model page drawn for a client project (kept off this public
repo, ADR 0409), whose SVG was drawn by a hand-written Python file with fixed x/y for every box
and line. When one table changed its key, the rows moved and every line into that table had to be
re-placed by hand; label overlaps happened twice in that session. So the agent writes only the
content (it reads the source, writes descriptions and multiplicities) into one model file, and a
script in the skill computes the positions, draws the page and checks it: every table has its row
meaning and purpose, every relationship has a label, a tooltip and both multiplicities, and no
label or line overlaps another. The cost: the layout follows the script's rules, so it is less
free than drawing by hand.
