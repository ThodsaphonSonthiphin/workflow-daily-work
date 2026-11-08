# The playbook gets an "outside the daily arc" section

```mermaid
flowchart TD
    Q{where does cut-vlog's playbook row go?} -->|chosen| A["a new section, Outside the daily arc, after the
    WORKING router - for skills that are not part of
    a working day"]
    Q -->|rejected| B["a row in the WORKING router - cutting a family video
    is not something that happens while working"]
    Q -->|rejected| C["no row - the repo's rule is that a skill missing from
    the playbook is invisible (ADR 0001)"]
```

Every new skill adds a playbook row in the same commit (ADR 0001). cut-vlog is the first
skill that has no place in the daily circle, so it gets its own section rather than
stretching the WORKING router. Agreed by the user in the recap on 2026-11-07.
