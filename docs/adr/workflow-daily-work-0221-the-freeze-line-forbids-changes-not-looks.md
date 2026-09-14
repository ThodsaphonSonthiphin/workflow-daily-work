# The Freeze line forbids changes in the console, not looks — a read-only look is not a redo

```mermaid
flowchart TD
    Q{the Freeze line says 'do not touch the console', then step ①<br/>asks the person to look in that console: which gives?} -->|chosen| A["narrow the prohibition to what its reason covers:
    'do not redo the step or change anything in the
    console'; item 3 says out loud that a read-only look
    is not a redo — the person obeys literally AND can
    still paste back the pending state"]
    Q -->|rejected| B["keep 'touch the console' and rely on the person
    to infer the exception — a prohibition wider than
    its reason gets ignored the moment it is inconvenient
    (Phase 3's own rule), and the next prohibition is
    then read as approximate too"]
    Q -->|rejected| C["drop the borrowed look and stop at 'no repro' when
    there is no second channel — abandons the person at
    the moment the skill exists for (ADR 0218 rejected B)"]
```

Found at the whole-branch review, 2026-09-14: the ADR 0215 Freeze line forbade touching the
console, and two paragraphs later the ADR 0218 path asked the person to look in it — the
pending-state read that disproves hypothesis #1 (ADR 0217) is, in a portal, a read only they can
perform. Ruled by the controller as ADR 0092 requires of a mid-run ruling: the prohibition is
narrowed to *change anything in the console*, which is exactly what its reason covers — a redo
destroys the half-applied state, a look does not — and item 3 states the exception explicitly
so the person never has to infer that this agent's prohibitions are approximate. ADR 0215's
decision stands; only the quoted line's verb changes, and 0215 carries the refinement note.
