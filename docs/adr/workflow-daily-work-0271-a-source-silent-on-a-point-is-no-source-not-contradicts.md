# A source silent on a point is `no source`, not `contradicts`

```mermaid
flowchart TD
    Q{the spec gives Workflow 3's whole query with two terms;<br/>the story's filter has three - is the third term<br/>'contradicts' or 'no source'?} -->|chosen| A["no source: a source that covers the whole thing and says
    nothing about THIS point is silent on it; contradicts
    needs the source to say something different about the
    same point (a different threshold, a different label,
    a test asserting another value)"]
    Q -->|rejected| B["contradicts: 'a source exists and the logic disagrees'
    read literally - phase 6 then aims the one question at
    the wrong row and phase 7 offers to file a finding
    about a term nobody ever ruled on"]
```

Ruled 2026-10-29 at the final whole-branch review. Spec §1 gives row 1 of `Elevate` #151 the
verdict *no source* ("the spec lists two filter terms and never names this field"), and
`SKILL.md`'s verdict table let an agent read the same facts as *contradicts*. The distinction
matters downstream: *contradicts* outranks *no source* in phase 6 and triggers the phase-7
offer line (ADR 0267, 0268). The rule is now one sentence under the verdict table.
