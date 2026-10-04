# A fact the user provides carries a mark — measured or told — and every told fact gets a test row

```mermaid
flowchart TD
    Q{the agent cannot access the old system, so the user<br/>provides the information: what may the user give,<br/>and what does the document write?} -->|chosen| A["anything — a command output, the user's own
    words, an old document — and every fact carries a
    mark: 'measured' for the output of a command that
    was run, 'told' for words or an old document; each
    'told' fact gets a row in the test list"]
    Q -->|rejected| B["only the output of a command the user ran —
    the document stops at the first fact that exists
    only in a document or in someone's memory"]
    Q -->|rejected| C["anything, with no mark — every fact looks the
    same, so nobody can tell which ones were never
    measured until one of them fails on go-live day"]
```

Ruled by the owner 2026-10-03: when the agent cannot access the old system, the user
must provide the information. Asked what form that takes, the owner chose the marked
form. The example that carried it: an old network diagram says port 1433 is open from
the application server to the database server. Written with no mark, the document says
"open", the connection fails on go-live day, and nobody can say whether the diagram was
wrong or the firewall changed. Marked `told`, the same fact puts a row for port 1433 in
the test list, so it is tested before that day.

This is the new skill's own copy (ADR 0231) of the two honest options `guide-and-verify`
gives for a system the agent cannot read — borrow the person's eyes, or declare the
baseline unverified — turned from a label on the baseline into a mark on each fact.
