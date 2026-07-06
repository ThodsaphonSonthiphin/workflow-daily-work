# sa-doc core template

Section order and rules shared by both profiles. Every slot names the model
path that fills it — prose may connect and explain, never introduce facts that
are not in `sa-model.yaml`. The document language is `meta.language`.

## Document skeleton (in order)

1. **Title block** — `meta.project`, `meta.org`, `meta.authors`, `meta.date`.
2. **Overview diagram** (diagram convention Rule 1) — one Mermaid `flowchart TD`
   (≤ 15 nodes): actors → the system → major use-case groups → key entities.
3. **1. ที่มาและปัญหา / Background & problem** — `problem.current_problems`,
   `problem.objectives` (with the P→O links stated), scope table from `scope`
   (one row per actor: capability list + the use cases that implement it).
4. **2. Requirements** — FR table: one row per scope capability, id `FR-n`,
   column linking to its use cases. NFR table from `nfrs` (id, category,
   requirement, measurable metric).
5. **3. Use cases** — one `flowchart TD` overview (actors ↔ use cases), then
   per use case the 13-field description (below).
6. **4. Interactions** — one Mermaid `sequenceDiagram` per use case from
   `main_flow` (participants: the actors + the system + external actors).
7. **5. Activity** — one `flowchart TD` per use case that has branches
   (extensions render as decision diamonds); skip use cases with a linear flow.
8. **6. States** — one Mermaid `stateDiagram-v2` per `states` group; a table of
   transitions (from, to, trigger, use case).
9. **7. Data model** — one Mermaid `erDiagram` from `entities` (PK/FK marked,
   relationship per fk); then the data dictionary: one table per entity
   (field, type(size), description, key).
10. **8. Architecture** — `architecture.style` + components table +
    `graph TD` of the components; deployment paragraph.
11. **9. Screens** — table from `screens` (id, name, use cases served).
12. **10. Traceability matrix** — generated from ids only:
    P → O → UC → ENT/SCR. One row per problem chain. Zero manual upkeep.

## The 13-field use case description (semantics enforced)

| # | Field | Rule |
|---|---|---|
| 1 | Use case name | from `name` |
| 2 | Scope | the SYSTEM under design, not the use case name |
| 3 | Level | user goal / subfunction |
| 4 | Primary actor | from `actors` |
| 5 | Stakeholders & interests | derived from `scope` rows pointing here |
| 6 | Preconditions | from `preconditions` |
| 7 | Success guarantee | from `postconditions` — a guaranteed state, NEVER a button press |
| 8 | Main success scenario | numbered steps from `main_flow` — one goal per use case |
| 9 | Extensions | from `extensions`, each anchored `<step>a.` to a main-flow step; no generic "system crashed → restart" boilerplate |
| 10 | Special requirements | from `special_reqs`; empty = "—" |
| 11 | Technology & data variations | only real variations; empty = "—" |
| 12 | Frequency | an estimate with a number, or "—" |
| 13 | Open issues | genuinely unresolved questions only (decided rules go in the flow) |

## Diagram rules

Follow `${CLAUDE_PLUGIN_ROOT}/references/diagram-convention.md`: overview
diagram first (Rule 1), type-matched section diagrams (Rule 2 — including the
`stateDiagram-v2` row for entity lifecycles), every diagram introduced by at
least one sentence.
