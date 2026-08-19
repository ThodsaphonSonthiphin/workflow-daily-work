# Map Notes become an append-only bullet region; the Destination stays one line

```mermaid
flowchart TD
    Q{the live map's Notes is ~450 words<br/>in ONE line — what shape fixes it?} -->|chosen| A["Notes becomes a tool-owned bullet
    list region (union like fog): one fact or
    amendment per line; Destination stays a
    single short line — amendments that used
    to bloat it land as Notes bullets"]
    Q -->|rejected| B["keep the paragraph, sharpen the
    authoring guidance — no code, but existing
    maps stay walls and every new amendment
    still splices into a run-on line"]
```

Measured on the live map `superpowers-review-to-scrutinize`: Notes is a single
~450-word line whose actual content is a *sequence of dated amendments*
("CORRECTED 2026-08-14: …", "NARROWED … (ADR 0077)", "CONSTRAINT ADDED …",
"ESCAPE HATCH TAKEN 2026-08-15 …") — a list forced to impersonate a paragraph.
So Notes gets the shape its content already has: a marker-region bullet list
under the same union rules as fog / out-of-scope (append, never remove or
reorder, byte-identical no-op). `map_input.json.map.notes` accepts a list of
lines (a bare string stays legal as a one-bullet list, so existing inputs keep
working); a legacy map whose Notes is still a paragraph under the plain heading
keeps reading and diverging exactly as today until someone hand-migrates it —
the region is only created when a notes list is first declared. The Destination
deliberately stays one line: it is the compass every choice is measured against,
and one breath is the budget. This decision rode the same session's scope call
to fix readability alongside milestones rather than defer it.
