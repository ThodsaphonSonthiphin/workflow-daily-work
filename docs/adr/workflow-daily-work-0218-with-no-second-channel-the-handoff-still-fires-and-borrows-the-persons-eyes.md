# With no second channel the handoff still fires, and step ① borrows the person's eyes

```mermaid
flowchart TD
    Q{the after-check was only 'reported by the operator'<br/>and it fails: does debug-mantra still open?} -->|chosen| A["yes — the freeze line goes out, and step ①
    is satisfied the way Phase 1 already does it:
    one read-only look the person pastes back (the
    pending state, the live value); every such run
    is labelled 'reported by the operator, not
    measured' and the label travels into every
    later claim"]
    Q -->|rejected| B["no handoff — say the result is unverified and
    let the person decide: abandons them at the one
    moment the skill exists for"]
    Q -->|rejected| C["hand off and treat the person's report as the
    repro, as if measured: a screenshot labelled as
    proof — loses the measured/reported distinction
    Phase 4 calls the whole value added"]
```

Phase 4 already names the systems with no second channel — consumer-grade admin pages,
routers, many SaaS settings screens — and rules that a check there is *"reported by the
operator, not independently measured"*, never *verified*. When such a check fails, there is no
measured repro for `debug-mantra` step ① to start from, only the person's words. Ruled
2026-09-14: the ADR 0214 handoff fires anyway; the ADR 0215 freeze goes out; and step ① is
met by the move Phase 1 already teaches when the agent cannot read the system — **borrow the
person's eyes**: one read-only look, pasted back, which becomes the run. The ledger entry for
that run carries the *reported by the operator* label, and so does every conclusion built on
it. The skill learns no new move; it applies an existing one at a second moment.
