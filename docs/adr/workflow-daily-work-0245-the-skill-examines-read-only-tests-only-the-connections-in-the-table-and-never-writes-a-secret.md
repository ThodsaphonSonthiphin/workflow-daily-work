# The skill examines read-only, tests only the connections in the table, and never writes a secret

```mermaid
flowchart TD
    Q{the skill examines an old system that other people<br/>depend on: what may it do?} -->|chosen| A["three rules, no exception — examination commands
    only read; only the connections in the connection
    table are tested, the network is never scanned; the
    document may name an account but never holds a
    password, a key or a token"]
    Q -->|rejected| B["the same, but a scan is allowed once the user
    confirms permission — a scan of all 65,535 ports of
    a server can raise the intrusion-detection alarm,
    and the needs table already says which ports matter"]
```

Asked 2026-10-03 with an example: the skill wants to know which ports server DB02 has
open. Under the three rules it tests port 1433 only, because row `C-01` names it. With
the exception it would scan every port of the server, the company's intrusion detection
may alert, and the security team comes asking. The owner chose the three rules with no
exception.

The second rule costs nothing the skill needs. Every connection it has a reason to test
is a row that serves a need (ADR 0239), so a port outside the table is a port no need
asked for. The third rule holds for everything the skill writes — the document, a step,
a recorded result: an account is named, its secret is not.
