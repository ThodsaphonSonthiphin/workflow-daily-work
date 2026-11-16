# cut-vlog is one skill file, three references and three scripts

```mermaid
flowchart TD
    Q{how is the skill's content split across files?} -->|chosen| A["SKILL.md holds the run (phases 0-8);
    references/edits-tools.md, style-file.md and
    edit-record.md hold the detail; three scripts do
    the arithmetic"]
    Q -->|rejected| B["everything in SKILL.md - the tool-behaviour table
    and the two templates would bury the run the agent
    has to follow step by step"]
```

The run is what the agent must not lose its place in, so `SKILL.md` carries only the phases
and points to a reference at the phase that needs it. The Edits tool behaviours (spec §7)
change when the app changes, so they live in one file that can be corrected alone. The
style-file and edit-record templates are read once per run. The three scripts are the ones
ADR 0298 chose: `review_footage.py`, `plan_cuts.py`, `compare_timeline.py`. Decided in the
spec (§12-b) and approved by the user on 2026-11-07.
