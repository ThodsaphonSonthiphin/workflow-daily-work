# decision-map

Plan an effort **too big for one agent session** as a **Decision map**: one item
indexing the effort — in v1 a `map.md` committed to your repo — with child
**Decision tickets**, questions whose resolution is a *decision*, not a slice of
a build, resolved **one per session** until nothing is left to decide. Then hand
off to the normal build flow.

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

**v1 ships exactly one backend: local markdown** (ADR 0056). Your map is repo
docs — it lives under `docs/decision-map/<slug>/` and is shared the way the repo
is shared, by committing it. Nothing appears on a board.

| Backend | Status | Needs | Ops script |
|---|---|---|---|
| Local markdown | **ships in v1** | nothing | `decision-map/scripts/local_map_ops.py` → `docs/decision-map/<slug>/` |
| Azure DevOps | planned (phase 2) | `ado-backlog` plugin, `az login`, `AZDO_ORG`/`AZDO_PROJECT` | not built yet |
| GitHub Issues | planned (phase 2) | `github-backlog` plugin, `gh auth login`, `GH_OWNER`/`GH_REPO` | not built yet |

Installing `ado-backlog` or `github-backlog` does **not** give decision-map a
tracker backend today — neither plugin can drive a map.

### What phase 2 looks like, and why it is not here

The tracker design is written down in full, not hand-waved: a map is one work
item / issue carrying the same five marker regions the local files use
(`key`, `gist`, `fog`, `scope`, `decisions`), its Decision tickets are its
children, and the `key` → item join is built by enumerating those children once
per run — never by search. All of it is specified in
[`references/data-contracts.md`](references/data-contracts.md), which keeps its
tracker mappings precisely because they are the phase-2 spec.

What is missing is evidence. The whole scheme rests on one bet — that
`<!-- decision-map:key:<key> -->` survives a round trip through the tracker,
including **an edit in the Boards web UI**, where the rich-text editor (not the
API) rewrites HTML. That bet has never been tested against a live API. If it
loses, the per-item marker collapses to a manifest on the map item — a
*different shape*, so both backends get rewritten rather than patched — and the
failure is silent in the worst way: a map whose markers were stripped re-charts
in full and is presented as a page of ordinary, approvable `create` lines.

So phase 2 starts with the contract's six-step verification probe ("Before
building the join") against a live tracker, and no join code is written until it
passes; the contract already records the fallback ladder for each way it can
fail. Everything above the ops script is backend-neutral — the skills, the
subcommands and the JSON shapes do not change when a tracker lands, only which
script the skills call.

## Safety

Creating items (charting, fog graduation) always dry-runs first and waits for your
explicit approval. Claim/comment/close ride the conversation's own confirmations.
