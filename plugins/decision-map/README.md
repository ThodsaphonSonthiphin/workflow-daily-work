# decision-map

Plan an effort **too big for one agent session** as a **Decision map**: one tracker
item indexing the effort, with child **Decision tickets** — questions whose
resolution is a *decision*, not a slice of a build — resolved **one per session**
until nothing is left to decide. Then hand off to the normal build flow.

Adapted from the [wayfinder](https://github.com/mattpocock/skills) skill by Matt
Pocock, re-grounded on this marketplace's plugins, trackers, and safety gates
(design: `docs/superpowers/specs/2026-07-31-decision-map-design.md`, ADRs 0033–0042
at the marketplace root).

## Skills

| Skill | Command | What it does |
|---|---|---|
| chart-map | `/decision-map:chart` | Name the destination, grill breadth-first, create map + tickets (dry-run gated), fire research subagents, stop. |
| work-map | `/decision-map:work` | Load the map, show the frontier, claim ONE ticket, resolve it via the matching arc skill, record + graduate fog, stop. |

## Backends

| Backend | Needs | Ops script |
|---|---|---|
| Azure DevOps | `ado-backlog` plugin, `az login`, `AZDO_ORG`/`AZDO_PROJECT` | `ado-backlog/scripts/decision-map-ops.cs` |
| GitHub Issues | `github-backlog` plugin, `gh auth login`, `GH_OWNER`/`GH_REPO` | `github-backlog/scripts/decision_map_ops.py` |
| Local markdown | nothing (fallback) | `decision-map/scripts/local_map_ops.py` → `docs/decision-map/<slug>/` |

## Safety

Creating items (charting, fog graduation) always dry-runs first and waits for your
explicit approval. Claim/comment/close ride the conversation's own confirmations.
