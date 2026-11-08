# The plugin is media-workflows, the skill is cut-vlog

```mermaid
flowchart TD
    Q{what are the plugin, the skill and the<br/>user's folder called?} -->|chosen| A["plugin media-workflows, skill cut-vlog, command
    /media-workflows:cut-vlog, folder ~/.claude/cut-vlog/
    holding style.md and one edit record per project"]
    Q -->|rejected| B["video-workflows - names one medium; a future photo
    or album skill would not fit"]
    Q -->|rejected| C["family-media - says whose footage it is, which a
    public plugin name has no reason to say"]
    Q -->|rejected| D["edits-vlog / cut-to-the-beat for the skill - the first
    ties the name to one app's brand, the second is long
    to type and names one technique, not the job"]
```

The user folder follows practice-english-writing's `~/.claude/<skill>/` shape. The skill
also triggers on what the user would say ("ตัดต่อคลิป", "ตัดต่อ vlog", "cut my video"),
not only on the command. Decided by the user on 2026-11-07.
