# The direct parent and children are read in full; other links by title and state

```mermaid
flowchart TD
    Q{"how far around the ticket does the skill read?"} -->|chosen| A["the ticket, its direct parent and every direct child
    in full - description, AC, comments, attached images.
    Predecessor, successor and related tickets: type,
    title and State only, shown as a list. An open linked
    Bug is pointed out in one line and does not change
    the verdict"]
    Q -->|rejected| B["every ancestor up to the Epic in full - an Epic is
    the whole programme; reading it at every run costs
    much and binds nothing the parent does not restate"]
    Q -->|rejected| C["parent and children only, other links unread - a
    related open Bug against the same flow is then
    invisible at the moment of resolving"]
```

Ruled 2026-11-16 by the user (Pon), taking the recommended option. Real case used: #151 with
parent #147 (Feature), child #297 (Task), predecessor #272, related #145 and #295 (Bug); the
Epic #141 is not read. Tickets are fetched the way `ticket-trace` Operation B steps 4-5 do
it, images through `read-picture` - loaded, not duplicated.
