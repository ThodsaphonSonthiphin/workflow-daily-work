# A connection into the new system stays owed until the system is installed — no temporary listener

```mermaid
flowchart TD
    Q{a connection runs INTO the new system, and the new<br/>system is not installed yet - nothing listens on its<br/>port: how is that row tested?} -->|chosen| A["it is not, yet — the row's test is recorded as
    owed, the document stays to-be, and the test runs
    once the new system is installed"]
    Q -->|rejected| B["open a temporary listener on the port to prove
    the path early — a listener is itself a change on a
    server, it proves the path and not the application,
    and a forgotten one is an open port nobody owns"]
```

Confirmed by the owner in the recap of 2026-10-03, as the second of five defaults.
Before the new system is installed, a test of a connection into it cannot pass, for a
reason that is not a fault: nothing listens. That is not a problem in the sense of
ADR 0244 either — the row still needs something that is not done.

So the row carries its test as owed, with the reason. The document cannot become
as-built (ADR 0242) until that test has run and passed.
