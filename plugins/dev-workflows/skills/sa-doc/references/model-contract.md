# sa-model.yaml — the sa-doc model contract

The single source of truth for a generated SA&D document. Every section of the
document is derived from this file; prose may explain but never introduce
actors, use cases, entities, fields, or states that are not in the model.
This file is the only place the schema is defined.

## Conventions

- Every object carries a stable `id`. Prefixes: `P`/`O`/`B` (problem/objective/
  benefit), `ACT`, `UC`, `ENT`, `SCR`, `NFR`, `SEC` — e.g. `UC-ORDER`, `ENT-PRODUCT`.
- Cross-references use ids only, never names.
- `TBD` (case-insensitive) is a legal value for any leaf. TBDs are inventoried
  by the validator and surfaced in the final summary — never silently invented.
- Language of `name`/`text` values follows the document language.

## Schema

```yaml
meta:
  project: string            # short slug used in file names
  org: string
  language: th | en          # document language
  profile: academic | professional
  authors: [string]
  date: YYYY-MM-DD

problem:
  current_problems: [ {id: P1, text} ]
  objectives:       [ {id: O1, text, problems: [P1]} ]     # which problems it answers
  benefits:         [ {id: B1, text, objectives: [O1]} ]

actors: [ {id: ACT-X, name, desc} ]

scope:                       # every capability MUST point at >= 1 use case (E2)
  - {actor: ACT-X, capability: string, use_cases: [UC-X]}

use_cases:
  - id: UC-X
    name: string
    actors: [ACT-X]                       # must exist (E1)
    objectives: [O1]                      # optional; W1 checks coverage
    preconditions: [string]
    postconditions: [string]              # guaranteed state AFTER success —
                                          # never a trigger like "user clicks save" (W4)
    main_flow:
      - {step: 1, actor: ACT-X, action: string, system_response: string,
         fields: [ENT-X.field]}           # optional machine-checkable refs (E4)
    extensions:
      - {at_step: 3, condition: string, flow: string, fields: []}
    special_reqs: [string]                # only real ones; empty list is fine
    entities: [ENT-X]                     # entities this use case touches
    screens: [SCR-X]

entities:
  - id: ENT-X
    name: string
    fields:
      - {name: string, type: string, size: int, desc: string,
         pk: true,                        # optional
         fk: ENT-Y.field,                 # optional; target must exist (E3)
         sample: string}                  # optional; W6 checks sample vs size

states:                                   # one group per stateful entity field
  - entity: ENT-X
    field: status                         # must exist on the entity (E5)
    states: [string]                      # field type must be able to hold them (E5)
    transitions: [ {from, to, trigger, uc: UC-X} ]

nfrs: [ {id: NFR-X, category, requirement, metric} ]

security: [ {id: SEC-X, concern, control} ]   # REQUIRED non-empty when profile=professional (E8)

architecture:
  style: string                           # e.g. web client-server
  components: [ {name, responsibility} ]
  deployment: string

screens: [ {id: SCR-X, name, use_cases: [UC-X]} ]

# academic profile extras
plan:
  phases: [ {name, from: YYYY-MM, to: YYYY-MM} ]   # contiguous + ordered (E7)
budget: [ {item, category, amount} ]
literature: [ {topic, source, relevance} ]
```

## Validation

`${CLAUDE_PLUGIN_ROOT}/scripts/validate_model.py <path>` — exit 0 clean,
exit 1 on errors. Errors block generation; warnings must be fixed or
explicitly accepted by the user; TBDs are reported, never invented away.
