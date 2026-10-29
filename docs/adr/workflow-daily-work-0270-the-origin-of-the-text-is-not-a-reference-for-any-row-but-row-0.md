# The origin of the text is not a reference for any row but row 0

```mermaid
flowchart TD
    Q{phase 2 searches git first and stops when a row closes -<br/>the commit or script that WROTE the value is found first;<br/>does it close the row?} -->|chosen| A["no: a commit that introduced the text, or a script or
    template that generated it, is the ORIGIN - row 0's
    source; on rows 1 and on it is written as
    'origin: <commit / file:line>' and the search goes on;
    only a ticket, a spec, an ADR, a test, a person or a
    measurement closes a row; a ticket number in the
    commit message is a pointer to follow"]
    Q -->|rejected| B["any file:line or commit closes a row as cited - on
    Elevate #151 rows 1 and 2 close against the script
    that generated them, cited · matches, and the
    headline case 'changed later in a commit with no
    ticket' comes out as cited instead of no source"]
```

Ruled 2026-10-29 at the final whole-branch review. `SKILL.md` phase 2 said "stopping when the
row closes" and "a row closed here is cited: file:line, a commit hash". Traced on the spec's
own example, rows 1 and 2 closed against `populate_teams_agent_backlog.py:388` - a copy of
themselves - and eval case 1 closed `> 30` on commit `a1b2c3d` before the tests at search
order 6 were ever read. A value agrees with the commit that wrote it by construction; that is
provenance of the text, not a reason for the value.

So the origin hit is recorded on the row as `origin: …` and never closes it. Row 0 is where
the origin is the answer. ADR 0264's search order is unchanged; what changes is what counts
as closing.
