# A learn-the-business question takes its facts from the Business flow and asks for what the flow does not say

```mermaid
flowchart TD
    Q{"what kind of question<br/>is asked?"} -->|chosen| A["every fact the question needs is on the Business<br/>flow, and the answer is not: the person reasons<br/>to a consequence, a reason or a decision,<br/>and the question names the step numbers"]
    Q -->|rejected| B["a recall question, as before - 'who is hurt?'<br/>with no flow shown asks for a fact the person<br/>was never given"]
    Q -->|rejected| C["a question the flow already answers - 'who gets<br/>the report?' when a line names them; a reading<br/>test, and nothing is learned"]
    Q -->|rejected| D["no question once the flow is shown - then it is<br/>feynman-explain, and ADR 0369 rejected that"]
```

Proposed by Claude and accepted by the user on 2026-11-23, with ADR 0389. Showing the flow
makes the old questions too easy or still impossible: the ones about who and when are now
written on the picture, and the ones about why are still nowhere. The rule keeps the
question between the two.

A question that needs a fact on no line, or on a `?` line, is not asked until the fact is on
the flow. ADR 0377's single push on a system answer is unchanged, and so is ADR 0369's order:
the person answers, then the card reveals.

The claim that a learner must hold the facts before a question about them teaches anything
is *general knowledge* here; no source was read for it in the session that made this ruling.
