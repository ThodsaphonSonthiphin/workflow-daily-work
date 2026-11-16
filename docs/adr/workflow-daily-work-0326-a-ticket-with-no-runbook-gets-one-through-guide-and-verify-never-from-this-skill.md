# A ticket with no runbook gets one through guide-and-verify, never from this skill

```mermaid
flowchart TD
    Q{"the check is written into the ticket's runbook,<br/>and the ticket has none. What then?"} -->|chosen| A["the skill says no runbook was found and hands off to
    guide-and-verify, which creates the runbook file in
    its own shape and the project's own naming. This
    skill then appends its section to that file. It never
    authors a runbook itself"]
    Q -->|rejected| B["briefing in chat, and the check asks once for a file
    or stays in chat - recommended; the user chose that a
    runbook always exists, made by the skill that owns
    its shape"]
    Q -->|rejected| C["this skill creates a small runbook file itself - a
    second author of runbooks with a second shape"]
    Q -->|rejected| D["the parent ticket's runbook - a child's check then
    sits in a document about another ticket"]
```

Ruled 2026-11-16 by the user (Pon): "use guid and verify to create runbook file". The
hand-off is by loading `guide-and-verify` through the harness's mechanism, with what this
skill has already read (the ticket, its parent and children, the file list) passed as the
head start, so nothing is fetched twice. Applying the hand-off at both moments - at the
briefing, where the runbook is about to be needed, and at the check - is the agent's reading;
the user's words name the skill and the file, not the moment.
