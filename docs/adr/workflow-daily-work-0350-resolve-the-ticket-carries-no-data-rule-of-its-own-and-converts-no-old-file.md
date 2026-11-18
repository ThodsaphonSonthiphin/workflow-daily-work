# resolve-the-ticket carries no data rule of its own, and converts no old file

```mermaid
flowchart TD
    Q{"runbooks and maps hold ticket text and snapshots<br/>of a live system. What must resolve-the-ticket keep<br/>out of the repo files it writes or hands on - and do<br/>old runbooks and maps have to be converted?"} -->|chosen| A["the skill carries no data rule of its own: what may
    be written is the project's rule (its CLAUDE.md /
    AGENTS.md). Old runbooks and maps are not converted;
    old and new shapes are read side by side"]
    Q -->|rejected| B["the skill never writes a secret or a customer's
    personal data, and replaces each with a description -
    recommended; the user chose to leave it to the project"]
    Q -->|rejected| C["the skill forbids secrets only"]
```

Ruled 2026-11-18 by the user (Pon), on Decision ticket `repo-data-rules` of the map
`docs/decision-map/one-entry-for-a-ticket/`: "C. ไม่มีกฎในสกิล", from three options the agent
laid out. The agent recommended the first rejected branch. The user gave no reason.

What still holds, from elsewhere:

- The skill follows the project's `CLAUDE.md` / `AGENTS.md`, as it already does for a
  comment format or a flowchart shape.
- What a loaded skill writes - a snapshot taken by `guide-and-verify`, a ticket created by
  `chart-map` - is that skill's own matter; none of them may be edited (ADR 0338).

No conversion (the agent's reading of earlier answers, stated to the user before the
question): a runbook with a D1..Dn table is still accepted (ADR 0347); a runbook with no
stage trace line is still read by its steps and results (ADR 0337, ADR 0343).

Nothing changes in `resolve-the-ticket/SKILL.md` for this decision.
