# Video editing ships as its own opt-in plugin

```mermaid
flowchart TD
    Q{where does the skill that cuts a day's footage<br/>into a vlog in the Edits app live?} -->|chosen| A["a new plugin in this marketplace, installed
    only on the machine that edits video"]
    Q -->|rejected| B["inside dev-workflows - every dev-workflows install,
    a colleague's too, would list a family-vlog skill that
    can trigger on 'ตัดต่อ' on a machine with no Edits app"]
```

The skill drives Meta's Edits app on a Mac through the app's own MCP server, and it
cuts family footage. Neither has anything to do with the daily dev-work arc that
`dev-workflows` carries. It follows the `react-workflows` precedent: a separate plugin
that you install only where it applies, so it does not trigger anywhere else. Decided by
the user on 2026-11-07, in the grilling session that designed the skill.
