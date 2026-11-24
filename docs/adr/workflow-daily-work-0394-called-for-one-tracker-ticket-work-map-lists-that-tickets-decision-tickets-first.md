# Called for one tracker ticket, work-map lists that ticket's Decision tickets first

```mermaid
flowchart TD
    Q{"a Feature's map holds the Decision tickets of every<br/>child (ADR 0346). resolve-the-ticket, called with one<br/>child (#196), loads work-map. What frontier does the<br/>person see?"} -->|chosen| A["the tickets that touch #196 first, under a heading
    with their count ('tickets for #196 - 8 of 10 open'),
    then one line for the rest of the map ('other tickets
    on this map: 1 for #195, 1 for #197'). The
    recommendation picks inside the #196 group. A direct
    /work-map call shows the whole map as before"]
    Q -->|rejected| B["the whole map as today, grouped by milestone - the
    key prefix is the only hint, and a prefix of 195- does
    not mean 'not #196': a ticket that touches several
    children takes the first child's id (ADR 0346); and the
    two-level rule recommends by milestone, so it offered
    195-ip-loss-recovery to a person who asked about #196"]
    Q -->|rejected| C["only the #196 tickets, the rest hidden - a #195
    ticket that still blocks #196 work would be invisible"]
```

Ruled 2026-11-24 by the user (Pon): "a", from three options the agent laid out, in the same
grill-then-plan session as ADRs 0392 and 0393. The agent recommended A.

Measured on the session of 2026-11-24 10:00: `resolve-the-ticket` was called with #196 and
`work-map` listed four milestones with tickets of #195, #196 and #197 together; three
minutes later the person ran `/wait-what`. A ticket belongs to the #196 group when its
Question's "Touches …" sentence names #196 (ADR 0395), so a ticket that touches several
tracker tickets appears in each one's group - accepted. resolve-the-ticket hands the tracker
ticket's number to work-map on the yes; without it (a direct call) work-map has no group to
form and shows the map as before.
