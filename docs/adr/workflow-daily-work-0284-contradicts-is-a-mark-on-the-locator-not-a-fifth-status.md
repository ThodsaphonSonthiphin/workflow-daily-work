# `contradicts` is a mark on the locator, not a fifth status

```mermaid
flowchart TD
    Q{a backward row implements R-003 and its verdict is<br/>contradicts - what does the register show?} -->|chosen| A["the locator in 'implemented at' (and a test locator in
    'tested by' whose assertion disagrees) carries
    '(contradicts)' after it; the status words keep saying
    whether code and a test EXIST - implemented / untested /
    not found / source changed - and the mark keeps the
    disagreement visible on the same line"]
    Q -->|rejected| B["a fifth status 'contradicted' - it would hide whether
    a test exists, which is the column the matrix is read
    for, and two rows of one requirement could disagree"]
```

Ruled 2026-10-29 at the Task 1 review (Minor 3a), promoted to an ADR by the whole-plan
review on 2026-10-30, which added the test-locator half: a test that asserts a value the
requirement does not say is coverage of the wrong value, and is marked too.
