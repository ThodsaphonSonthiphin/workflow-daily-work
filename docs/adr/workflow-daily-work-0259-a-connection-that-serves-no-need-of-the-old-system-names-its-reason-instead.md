# A connection that serves no need of the old system names its reason instead

```mermaid
flowchart TD
    Q{every connection row names the need it serves: what<br/>about a connection that serves none - users reaching<br/>the new system?} -->|chosen| A["its Need column holds a dash and the reason in
    a few words - 'users open the portal'; it is still
    a row, with its ID, its arrow and its test"]
    Q -->|rejected| B["invent a need for it - a need is something the
    new system gets from the old one, and the users'
    path to the new system is not that"]
    Q -->|rejected| C["leave it out of the table because it serves no
    need - its firewall rule still has to be asked for
    and tested, and an arrow with no row breaks the
    rule that the row is the source"]
```

Ruled at planning, 2026-10-03, while the worked example of the document was written;
reported to the owner with the plan. ADR 0239 says every connection row names the need
it serves. The example needed a third connection — from the staff's PCs to the new
portal — and no need stands behind it: nothing is taken from the old system.

The sample the owner chose from for ADR 0237 already carried such a row ("users open the
web application"), so the row stays. Its Need column holds `—` and the reason in a few
words, and everything else about it is as for any other connection: an ID, one arrow in
the deployment view to-be, one test.
