# A confirmed cause returns as a corrected step, recorded on the ticket — not a redo, not a post-mortem

```mermaid
flowchart TD
    Q{debug-mantra has confirmed why the step failed:<br/>what does the person get, and where is it written?} -->|chosen| A["a corrected step in the fixed Go to / Do / Do not /
    verify shape (the missing apply action as its own
    numbered line), the failed step's after-measurement
    as its new baseline; the cause and both timestamps
    go in the Phase 5 outcome line on the ticket. When
    the cause is the agent's — a wrong count, a wrong
    prediction — the corrected thing is the runbook"]
    Q -->|rejected| B["'try again' with the same step — the thing
    the whole handoff exists to stop; half-applied
    plus a redo is worse than half-applied"]
    Q -->|rejected| C["A plus a full post-mortem document under the
    ADR 0003 chain — that chain is for a fixed defect
    in code; a missed click is recorded where the next
    person looks, the ticket"]
```

Ruled 2026-09-14: when `debug-mantra` returns a confirmed cause, `guide-and-verify` resumes
at Phase 3 and writes a **corrected step** in the shape the person has been reading all
session — never "try again". The after-measurement of the failed step is the baseline the
corrected step is asserted against, so Phase 4 runs on it like any other step. The cause, the
time the step failed and the time the corrected step landed go into the Phase 5 outcome line
on the ticket, beside the measurement, because that is where the next person looks. When the
cause is on the agent's side — a Phase 1 count that was wrong, a Phase 2 prediction that was
wrong — the corrected thing is the runbook itself, and the person is told so. The ADR 0003
chain (fix → post-mortem → management-talk) is not entered for a missed click; it applies only
when the confirmed cause is a real defect in the system, and that is a hand-off *out of* the
runbook which the skill names as such.
