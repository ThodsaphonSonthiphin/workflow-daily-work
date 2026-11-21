# The business note is one file per project, outside every repo

```mermaid
flowchart TD
    Q{"the note of what was asked must<br/>not go into git - where is it?"} -->|chosen| A["~/.claude/learn-the-business/&lt;project&gt;.md, where<br/>project is the folder name of the main git root,<br/>not of a worktree"]
    Q -->|rejected| B["inside the repo, hidden by .git/info/exclude - each<br/>worktree gets its own copy, so one worktree re-asks<br/>what another asked; deleting the clone deletes it;<br/>git add -f still commits it"]
    Q -->|rejected| C["one file for all projects, as the Mistake profile -<br/>English belongs to the person, but the business<br/>belongs to each client"]
    Q -->|rejected| D["the harness's per-project memory directory -<br/>one harness only, and its index loads into every session"]
```

Ruled 2026-11-21 by the user ("ไม่ต้องเอาเข้า git"). The pattern is ADR 0181's, changed in one
point: one file per project. The skill says the file's full path every time it writes. The
note does not travel to another machine, and it holds client business facts in the home
folder of a machine that already holds the client's repo.
