# Three tested Python scripts do the repeatable work

```mermaid
flowchart TD
    Q{who does the work that is the same on every<br/>run - footage review, cut-point arithmetic,<br/>comparing the timeline with the plan?} -->|chosen| A["three Python scripts bundled with the plugin,
    each with tests: review the footage, compute the
    planned cuts, compare the timeline with the plan"]
    Q -->|rejected| B["the agent writes the commands fresh each run from
    the SKILL.md prose - on the first run the hand-written
    review sampled frames unevenly and ran past a
    ten-minute timeout before it was rewritten"]
```

The three jobs are deterministic and the same every time. **Review** runs ffmpeg over a
folder of clips: eight evenly spaced frames per clip as one row, a loudness trace, and the
clips grouped into parts of the day by the gaps between their capture times. **Plan**
turns the song's BPM, the drop and each shot's length in beats into frame-exact cut times
and the trim values for each clip; those numbers are the planned values that the
second-channel check (ADR 0296) compares against. **Compare** reads the timeline the
agent saved from Edits and the plan, and names every shot that does not match. The scripts
never call the Edits MCP server: the agent calls the tools and passes their JSON to the
scripts, so the scripts can be tested without the app. Decided by the user on 2026-11-07.
