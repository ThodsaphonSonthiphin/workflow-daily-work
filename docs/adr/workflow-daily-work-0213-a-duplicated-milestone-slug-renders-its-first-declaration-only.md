# A duplicated milestone slug renders its first declaration only — its own count and its own members

```mermaid
flowchart TD
    Q{two milestone lines share a slug (a lint error):<br/>what does the decisions index render?} -->|chosen| A["one heading, from the FIRST declaration,
    carrying that declaration's milestone_progress
    row and ONLY its own members; a closed ticket
    listed only by a later duplicate falls to the
    (unassigned) tail — heading and list agree,
    and the heading matches frontier.json's first row"]
    Q -->|rejected| B["one heading, every same-slug member beneath it
    (membership_of maps them all to the slug) —
    the count comes from the first row alone, so a
    map read '1/1 closed' over two bullets: the file
    contradicted itself (found in review, 2026-09-13)"]
    Q -->|rejected| C["merge the duplicates' counts into one heading —
    a second counting rule beside milestone_progress,
    and a heading that no frontier.json row reports"]
```

Under ADR 0211 every declared milestone renders as a heading with `<closed>/<total>`
taken from `milestone_progress`, which reports one row per *declaration*; under a
duplicated slug the first implementation swept every member `membership_of` maps
to that slug under the first declaration's heading, so the heading's count and the
bullets beneath it disagreed. Ruled during execution (SDD ledger, Ruling 5): the
group under a heading is scoped to that declaration's own members as well as to
the slug, a closed ticket listed only by a later duplicate lands in the
`(unassigned)` tail, and the heading therefore always matches both its list and
`frontier.json`'s first row for that slug. `lint`'s `milestone-duplicate-slug`
message and the contract's rule table say the same; the later declarations lose
only their labels. The state is a lint error either way — this decides only what
the file shows while it stands.
