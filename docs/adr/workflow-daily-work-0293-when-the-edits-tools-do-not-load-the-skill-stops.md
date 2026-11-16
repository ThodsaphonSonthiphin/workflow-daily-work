# When the Edits tools do not load, the skill stops

```mermaid
flowchart TD
    Q{Edits is open, but the agent cannot load<br/>the tools of its MCP server: what does the<br/>skill do?} -->|chosen| A["say what failed and how to fix it - update Edits,
    update the agent, restart - and stop; nothing is
    reviewed or planned until the tools load"]
    Q -->|rejected| B["call the server over HTTP with curl, the token read
    from the agent's config - every edit becomes a long
    shell command, it reads a secret out of a config file,
    and it works in one harness only"]
    Q -->|rejected| C["review the footage with ffmpeg and draft the shot plan
    while the user fixes it - the user chose one clear stop
    over a run that is half done and half waiting"]
```

On the first run (2026-11-07) Claude Code connected to the server but rejected its tool
list (`tools/list`: `ttlMs` expected a number, `cacheScope` not `public`/`private`). The
agent worked around it with `curl` until the tools loaded. The skill does not repeat that:
a pre-flight loads the tools before any other step, and when it fails the skill names the
error and the fixes, then stops. Decided by the user on 2026-11-07.
