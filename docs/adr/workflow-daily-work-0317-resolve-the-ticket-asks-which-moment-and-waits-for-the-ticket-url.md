# resolve-the-ticket asks which moment and waits for the ticket URL

> **Amended 2026-11-18 by ADR 0337.** The skill still waits for the ticket's URL. It no longer asks "briefing or check": it reads the files, proposes the stage and asks for a yes.

```mermaid
flowchart TD
    Q{"the skill has two moments - the briefing and the<br/>check. How does a run know which one, and which<br/>ticket?"} -->|chosen| A["the skill asks: briefing or check, and the ticket's
    URL - then waits. It reads nothing until it has the
    URL. An invocation that already carries both asks
    nothing"]
    Q -->|rejected| B["the ticket's State decides (New = briefing, Active =
    check) - recommended; the user chose to be asked. A
    State is also a weak signal: a ticket can sit in New
    while the work is done"]
    Q -->|rejected| C["a word typed every time (brief / check) with a bare
    ticket number - a bare number needs the organization
    and project from somewhere else; the URL carries both"]
    Q -->|rejected| D["always both, in order - before the work the check is
    a table of 'no test yet' rows that says nothing"]
```

Ruled 2026-11-16 by the user (Pon): "ask me and wait for url". The ticket is named by its
URL, not by a bare number, because the URL names the tracker, the organization and the
project in one string (`dev.azure.com/<org>/<project>/_workitems/edit/<id>`), so the skill
needs no `AZDO_ORG` / `AZDO_PROJECT` and cannot read the right number in the wrong project.
Reading "ask me" as *ask which moment* is the agent's interpretation; the user confirmed
the URL wait in their own words.
