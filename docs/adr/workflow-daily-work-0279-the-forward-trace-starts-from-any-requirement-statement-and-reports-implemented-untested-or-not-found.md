# The forward trace starts from any requirement statement, and reports implemented, untested, not found or source changed

```mermaid
flowchart TD
    Q{the user wants 'where is this requirement implemented,<br/>and is it tested?' - what may they point at?} -->|chosen| A["any requirement text: a spec section, a ticket's
    acceptance criteria, a typed sentence, or an ID already
    in the register; the skill splits it into statements,
    mints IDs for the new ones, searches the code for the
    decision points that implement each (the value, the
    field, the flow name) and the tests that assert it,
    and gives every statement one status: implemented
    (which rows) · untested (code, no test) · not found
    (no code - a gap the backward trace can never see) ·
    source changed (on a later run the text at the locator no
    longer reads as registered; nothing is re-derived until
    the user confirms the new wording)"]
    Q -->|rejected| B["only an ID already minted by an earlier backward run
    - a requirement nobody has traced backward from yet
    cannot be asked about, which is exactly the gap case"]
    Q -->|rejected| C["a second skill or command for the forward direction -
    two entry points for one register, and the user must know
    which to type; direction by what is pointed at needs no
    choice"]
```

> **Amended 2026-10-30 (whole-plan review):** when the thing pointed at could go either way, the question decides - *why / where does it come from / is it right* runs backward, *where is it implemented / is it tested / coverage* runs forward, neither → the one direction question; the four status words stay in English beside the verdict words; a *source changed* line keeps `<new text> (was: <old text>)` in its statement cell.

Chosen 2026-10-29. The backward run (ADR 0261–0277) can only start from code that exists;
a requirement with no code behind it - spec §4 Workflow 3's "emails the PDF digest to
`MG_AdminEmail`" on `Elevate` #151, say - has nothing to point at. The forward run is the
direction that finds it. The same skill carries both: what the user points at decides the
direction - a decision point or a thing with logic in it runs backward; a requirement
statement or an `R-` ID runs forward.
