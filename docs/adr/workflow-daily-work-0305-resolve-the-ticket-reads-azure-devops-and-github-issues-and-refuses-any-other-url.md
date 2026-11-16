# resolve-the-ticket reads Azure DevOps and GitHub Issues, and refuses any other URL

```mermaid
flowchart TD
    Q{"which ticket URLs does the first version<br/>understand?"} -->|chosen| A["Azure DevOps work items and GitHub issues. On GitHub
    the parent and children are the parent issue and the
    sub-issues, the AC are a task list or an 'Acceptance
    criteria' section, and the done State is closed. Any
    other URL: the skill says it cannot read that tracker
    and stops"]
    Q -->|rejected| B["Azure DevOps only - the user's daily tracker, but
    this marketplace ships a GitHub side and ticket-trace
    already reads both"]
    Q -->|rejected| C["Jira as well - there is no measured recipe for it in
    this repo, and an unmeasured adapter fails at run
    time (the rule of ADR 0118)"]
```

Ruled 2026-11-16 by the user (Pon), taking the recommended option. The parent / child read
is the one part `ticket-trace`'s reference does not yet carry; the skill's own reference file
gives the worked commands for both trackers, and each is measured against a real ticket
before it is written down.
