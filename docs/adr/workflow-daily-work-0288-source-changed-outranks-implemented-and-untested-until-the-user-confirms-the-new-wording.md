# `source changed` outranks `implemented` and `untested` until the user confirms the new wording

```mermaid
flowchart TD
    Q{"a backward run finds the text at a registered locator changed (ADR 0282) and also finds a row and a test - phase 5 sets implemented; eval case 6 expects source changed; which wins?"} -->|chosen| A["source changed wins: the line keeps that status, and its
    implemented-at / tested-by cells still fill, until the user
    confirms the new wording in phase 6 or F6 - then the status
    is re-derived from the cells; the row's own verdict against
    the NEW text is still given in the same run, because 'the
    spec moved and the code did not' is exactly the finding
    worth surfacing"]
    Q -->|rejected| B["implemented wins, as the cells say - the changed
    requirement disappears behind a green status, and the
    one thing the forward trace exists to show (the spec is
    ahead of the code) is hidden"]
    Q -->|rejected| C["derive nothing until the user confirms - the backward
    run then cannot give the row a verdict, and the user is
    asked to confirm a wording before seeing why it matters"]
```

Ruled 2026-10-30 at the fix-wave re-review (new breakage NB-1), which traced eval case 6
through the amended phase 2 and found phase 5's refresh ("`implemented` when a test is in
*tested by*, else `untested`") had no third outcome. The status table's "re-derive nothing
until the user confirms" meant the *status*, not the row's verdict; this ADR says so. Text
in `SKILL.md` phase 5, the status table and `register-template.md` follows in the next change.
