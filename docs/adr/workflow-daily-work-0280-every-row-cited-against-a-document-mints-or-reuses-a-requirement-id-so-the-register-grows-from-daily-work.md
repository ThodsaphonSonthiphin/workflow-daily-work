# Every row cited against a document mints or reuses a requirement ID, so the register grows from daily work

```mermaid
flowchart TD
    Q{a backward run closes a row as 'cited spec:145' -<br/>does that sentence enter the requirement register now,<br/>or only when someone runs a forward trace?} -->|chosen| A["now: the statement gets an R-ID if it has none, the
    row's Source line reads 'cited R-003 (spec:145)', and the
    register records R-003 ← this row; the matrix builds
    itself from every run, in either direction"]
    Q -->|rejected| B["only forward runs mint - five backward runs over two
    months leave an empty register, and 'which requirement
    has no test?' has no answer until someone does the
    matrix as separate work"]
```

> **Amended 2026-10-29 (Task 2 review):** a row closed against a document statement still runs search order 6, so that a test asserting its value lands in the register's *tested by*; without that, the backward run could never fill the column this ADR exists to fill.

Chosen 2026-10-29. The cost is one register line per cited row; the gain is that the
*tested by* column is visibly empty for every requirement the daily work has touched,
without a separate traceability exercise. A row cited against a commit, a test or a person
mints nothing - only a document statement is a requirement (ADR 0278); a test is a
coverer, a commit is an origin (ADR 0270), a person's word is *told* (ADR 0266).
