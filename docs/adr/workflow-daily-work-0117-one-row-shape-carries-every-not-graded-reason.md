# One row shape carries every not-graded reason

```mermaid
flowchart TD
    Q{how does a row say<br/>"this was not measured"?} -->|chosen| A["every row has graded: bool and, when
    false, not_graded_reason: str - built by
    one row-builder, summarised by one loop
    that counts per reason"]
    Q -->|rejected| B["the three shipped mechanisms: a pre-role
    path test, a post-role version test, and
    a cache_note string that silently disabled
    the second one wholesale"]
```

The checker grew three suppression mechanisms with three different shapes: a path test
before role classification that wrote a `SUPERSEDED` row, a version test after it that
wrote a near-identical `SUPERSEDED` row, and a `cache_note` string that turned the second
one off entirely for the whole run. Each carried its own hand-written explanation, and
each explanation was printed from a different place than the branch that produced it.

That is how the false line in
[ADR 0116](workflow-daily-work-0116-an-unusable-install-claim-grades-the-version-present-and-is-itself-a-finding.md)
survived: the summary said "older than the claimed version" for rows suppressed by a
branch that had no claimed version to be older than. The wording was not sloppy, it was
*structurally unable* to be right - one string described two branches.

With one representation the reason travels with the row that earned it. The summary loop
groups by reason and prints a count per reason, so it can only ever print reasons that
some row actually carries, and a new suppression cannot be added without a reason to show
for it. `SUPERSEDED` as a pseudo-verdict is gone: the three verdicts stay exactly
`IN SYNC` / `STALE` / `UNRELATED` (the spec's supersession banner), and a row that was not
measured says `NOT GRADED` plus why.

Cost: the module did not shrink. The collapse itself is roughly line-neutral, and the
fixes landed inside it (grading the version present, the provenance floor, scan-error
reporting, robust marketplace detection) added ~60 code lines of new measurement. The
duplication is gone even though the file is longer.
