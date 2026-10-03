# One architecture document per environment, saved where the user says at the start

```mermaid
flowchart TD
    Q{where does the architecture document live, and what<br/>does one document cover?} -->|chosen| A["one document per environment, named in its
    header; a default path under docs/architecture,
    built from the system name and the environment
    name; the skill asks for the location once, when
    the work starts"]
    Q -->|rejected| B["one document for every environment, a column
    per environment in each table — the rows multiply,
    and a result measured in UAT reads as a result
    for production"]
```

Confirmed by the owner in the recap of 2026-10-03, as the third of five defaults. Facts
differ by environment — the servers, the addresses, the firewall rules — and so do
results: a port that answers in UAT says nothing about production.

So one document describes one environment and says which in its header, beside the
status (ADR 0242). A second environment is a second document. The default path is
`docs/architecture/<system>-<environment>.md` in the project the skill is run in; the
skill asks once, at the start, and writes where the user says.
