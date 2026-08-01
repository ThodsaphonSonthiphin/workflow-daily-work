# decision-map data contracts

Single source of truth for the shapes exchanged between the decision-map flow
skills and the three backend ops scripts (ADR 0037). Nothing else redefines them.
The tracker (or the local files) is the source of truth; these JSON files are
working files, never a store.

```mermaid
erDiagram
    MAP ||--o{ TICKET : "parent of"
    TICKET ||--o{ TICKET : "blockedBy"
```

## Subcommand contract (all three backends)

| Subcommand | Args | Effect |
|---|---|---|
| `chart` | `--input <map_input.json> --output <map.json>` | create map + tickets + parent links + blocking edges, **additively** (ADR 0054/0055) — see below. **Dry-run by default**; `--real` performs the writes; `--force` is a **destructive** full rewrite that discards recorded resolutions, claims and edges. |
| `read` | `--map <id\|slug> --output <map.json>` | fetch map + children at low resolution. |
| `frontier` | `--map <id\|slug> --output <frontier.json>` | open + unblocked + unclaimed children. |
| `claim` | `--ticket <id\|slug>` (`--user <upn>` ADO only) | assign the ticket to the caller. |
| `resolve` | `--ticket <id\|slug> --gist "<one line>" [--link <url>] [--body-file <md>]` | post resolution comment, close the ticket. |
| `comment` | `--ticket <id\|slug> --body-file <md>` | plain comment. |
| `block` | `--ticket <id\|slug> --blocked-by <id\|slug>` | dependency edge (ticket waits on blocked-by). |

Every subcommand also accepts `--dry-run` (print planned mutations, change
nothing) — for `chart` that is already the default.

### `chart` is additive (ADR 0054, refined by ADR 0055)

`chart` names **two acts**: the initial charting of a map, and the incremental
graduation of fog into fresh tickets mid-map. One create path serves both, so
do not read `chart` as create-only.

**Additive means union.** The guarantee is *never removes, never reorders,
never overwrites* — **not** "never touches". On a map that already exists,
`chart`:

- creates only the tickets whose `key` is absent;
- **unions** `notYetSpecified` / `outOfScope` lines into the map body: new
  lines are appended, existing ones are never removed or reordered, and an
  input that omits a line already on disk does not delete it;
- **unions** a new blocking edge into an existing ticket's `blockedBy`
  (ADR 0055). That ticket gains one entry and **nothing else** — every other
  byte of it, including status, assignee, gist and the resolution block, is
  unchanged. Dropping the edge instead was worse: `frontier()` then reported a
  ticket as actionable while a just-created ticket was meant to block it;
- does **not** apply a `title` / `destination` / `notes` that differs from
  what is on disk. The difference is reported in the result's `divergence`
  list and left unapplied — silently rewriting an evolved map from a stale
  input is precisely the destruction this design exists to prevent. Edit
  `map.md` by hand to change them.

**What additive does not guarantee:** that an existing ticket file is
byte-identical afterwards (it may gain one `blockedBy` entry), and that a
value in the input takes effect (a divergent scalar is reported, not applied).
It does guarantee that nothing recorded is ever removed, reordered or
overwritten, and that re-running identical input is a **no-op** — the same
bytes out, which also makes a partially-failed chart resumable.

An edge may name a ticket that already exists in the map **without re-listing
it in `tickets[]`** (ADR 0055). A `blocks` target must exist either in this
input or in the map on disk; naming a target that exists in neither is a
validation error.

`--force` is the explicit, dry-run-announced full rewrite. **It is
destructive: it discards every recorded resolution, claim and blocking edge
on the items it rewrites.** It is never required to add tickets or edges —
that is what additive `chart` is for. No message in any backend may recommend
`--force` without stating this cost.

**What `--force` does and does not discard, per action label.** `--force`
does not mean "reset the map"; it means "rewrite the items in this input".
Its reach is exactly the items the plan labels `OVERWRITE`:

| the item is… | label under `--force` | what happens to its recorded state |
|---|---|---|
| listed in `tickets[]` | `OVERWRITE` | **all discarded** — status back to `open`, assignee cleared, gist cleared, resolution removed, `blockedBy` reset and then re-wired from this input's `blocks` |
| the map itself | `OVERWRITE` | title / destination / notes / fog / out-of-scope rewritten from the input. Fog and out-of-scope lines that existed only on the map and are absent from the input **are lost** — this is the one place additive's union guarantee does not apply |
| named only in a `blocks` list, not in `tickets[]` | `merge` | **nothing discarded** — it gains the edge and keeps its status, assignee, gist and resolution, exactly as on the additive path |
| present on the map but in neither `tickets[]` nor any `blocks` | *absent from the plan* | **untouched** — `--force` never reaches an item this input does not name |

A backend must therefore not implement `--force` as "delete the map and
re-chart": that would destroy items the input does not mention, which neither
the plan nor this contract permits. Every destructive act must appear in the
dry-run plan as an `OVERWRITE` line before it happens.

One consequence worth knowing: the "Decisions so far" index is a projection
refreshed by `resolve`, so after a `--force` rewrite it reflects only the
tickets this input rewrote. A ticket left closed because the input did not
name it keeps its own closed state, but is no longer listed in the index until
something re-projects it.

#### Dry-run action vocabulary (required of every backend)

The dry run reports one action per item, on both the machine-readable stdout
plan and the human stderr rendering. All four labels are **required** — a
backend must be able to express each of them, because each names an outcome
additive `chart` genuinely produces:

| action | meaning |
|---|---|
| `create` | the item does not exist yet and will be created |
| `skip (exists)` | the item exists and will **not** be written at all |
| `merge` | the item exists and will be **modified in place, additively** — the map body gaining fog / out-of-scope lines, or a ticket gaining a `blockedBy` entry |
| `OVERWRITE` | `--force` only: the item exists and will be fully rewritten |

`skip (exists)` is a promise that nothing is written; anything modified must
be labelled `merge`, never `skip`. A `merge` entry carries a `detail` string
naming what it will add (e.g. `unions blockedBy: fog-graduate`), so the
ADR-0039 approval gate can show the reviewer every write before it happens.

## `map_input.json` (input to `chart`)

```json
{
  "target": { "org": "Cartagena365", "project": "GlassHull",
              "owner": "Cartagena365", "repo": "GlassHull",
              "slug": "example-effort" },
  "mapType": "Epic",
  "ticketType": "Issue",
  "map": {
    "title": "Decision map — <effort name>",
    "destination": "<one or two lines>",
    "notes": "<skills to consult; standing preferences>",
    "notYetSpecified": ["<fog line>", "..."],
    "outOfScope": ["<ruled-out line>", "..."]
  },
  "tickets": [
    { "key": "auth-model", "title": "Auth model — per-tenant or shared keys?",
      "type": "grilling", "question": "<the decision this resolves>",
      "blocks": ["rollout-order"] }
  ]
}
```

`target` carries only the fields the active backend needs (org/project for ADO,
owner/repo for GitHub, slug for local). `mapType`/`ticketType` are ADO work-item
types (defaults `Epic`/`Issue`; must be valid for the project's process — the
chart-map skill confirms them). `blocks` lists ticket keys this ticket blocks —
**downstream**, an authoring convenience the `chart` operation reads to wire
edges. This is deliberately different from `blockedBy` in `map.json` and
`frontier.json` below: that field reports the **upstream** relation (the
tickets that must close before this one is actionable), which is what every
consumer actually queries. Input authors `blocks`; output (and every reader)
sees `blockedBy` — do not confuse the two. `type` ∈ `research | prototype |
grilling | task`. Mode is derived: research=AFK, grilling/prototype=HITL,
task=either.

## `map.json` (output of `chart` and `read`)

```json
{
  "backend": "ado",
  "map": { "id": "1234", "name": "Decision map — <effort>", "url": "https://…",
           "destination": "<line>" },
  "tickets": [
    { "key": "auth-model", "id": "1235", "name": "Auth model — …",
      "url": "https://…", "type": "grilling", "mode": "HITL",
      "status": "open", "assignee": null, "blockedBy": ["rollout-order"],
      "gist": null }
  ]
}
```

`chart` (only — not `read`) adds `"divergence"`: a list of human-readable
strings naming anything the input asked for that an additive run deliberately
did not apply — a differing `title`/`destination`/`notes`, or list lines that
could not be merged into a `map.md` predating the list regions. Empty on an
initial chart and on `--force`. Blocking edges are **not** listed here: since
ADR 0055 they are applied, and appear in the dry-run plan as a `merge`.

`status` ∈ `open | closed`. `blockedBy` lists upstream blockers — the tickets
that must close before this one is actionable — the same relation `frontier.json`
reports for every blocked ticket; every backend computes this relation
naturally from its own native dependency mechanism (see the "blocking" row of
Backend mappings below for the exact field/label each backend uses). **Its
entries are `key`s, not native ids**, in every backend: a backend that stores
the edge natively (an ADO link, a GitHub "blocked by") must resolve each
linked item back to its key through the join above before emitting this field.
After `resolve`, `gist` holds the one-line answer. For the local backend, `id`
and `key` are both the ticket file's slug and `url` is the repo-relative file
path.

## `frontier.json` (output of `frontier`)

```json
{
  "frontier": [ { "id": "1235", "name": "Auth model — …", "url": "https://…", "type": "grilling" } ],
  "blocked":  [ { "id": "1236", "name": "Rollout order — …", "blockedBy": ["auth-model"] } ],
  "claimed":  [ { "id": "1237", "name": "…", "assignee": "thodsaphon.sonthipin@cartagena.no" } ]
}
```

Closed tickets appear in none of the three buckets — a closed ticket is done,
not actionable. `blockedBy` here carries `key`s, as it does in `map.json`.

**Bucket precedence — every backend must use the same order.** A ticket can
satisfy more than one condition at once (claimed *and* blocked is the common
case), and it appears in **exactly one** bucket:

1. `claimed` — the ticket has an assignee (whether or not it is also blocked);
2. `blocked` — otherwise, if it has at least one **open** blocker;
3. `frontier` — otherwise.

So a ticket that is both claimed and blocked appears under `claimed` only, and
its blockers are not listed there. That is deliberate: both answers mean "not
available to pick up", and the blocker list remains visible in `map.json`'s
`blockedBy` for the same ticket. A backend that ordered these the other way
would emit a different `frontier.json` from the same state. The local backend
pins this ordering in
`test_additive_chart_unions_a_new_edge_into_an_existing_ticket`, which asserts
a claimed-and-blocked ticket lands in `claimed` and not in `frontier`.

Only blockers that are still **open** count — a closed blocker does not hold a
ticket back, which is what makes `resolve` release the next decision.

## The `key` → tracker-item join

`key` is the stable, human-authored identity of a ticket (`auth-model`). It is
the **only** identifier that means the same thing in every backend, and every
ticket-to-ticket reference inside these JSON documents is a key — `blocks` in
`map_input.json` and `blockedBy` in `map.json` / `frontier.json`. `id` and
`url` are the backend's own native handles, for linking and for passing back
to `--ticket`; on the local backend `id` and `key` coincide, on ADO and GitHub
they do not.

Additive `chart` **cannot work without this join**: before it can label an item
`create`, `skip (exists)` or `merge`, it must answer *does a ticket with key X
already exist on this map?* A backend that cannot answer re-creates every
ticket on every run.

**The rule: the key is stored on the ticket itself, in a location returned when
the item is fetched, and the join is built by enumerating the map's children
once per run.** Never by a global search.

| Backend | Where the key lives | How the join is built |
|---|---|---|
| Local | the ticket filename stem, `tickets/<key>.md` | glob `tickets/*.md`; the stem *is* the key (stems that are not safe slugs are not decision-map tickets and are ignored) |
| ADO | marker line `<!-- decision-map:key:<key> -->` in `System.Description` | one WIQL/link query for the map work item's `System.LinkTypes.Hierarchy-Forward` children, then read each child's description |
| GitHub | marker line `<!-- decision-map:key:<key> -->` in the issue body | list the map issue's sub-issues (or parse the task list in the map body when sub-issues are unavailable), then read each issue's body |

Both trackers use the **same marker format as the local backend's regions**, so
one escaping rule covers all three: every user-supplied string written into a
tracker item is escaped on the way in, exactly as the local backend escapes
`<!-- decision-map:` to `&lt;!-- decision-map:`, so a `question` or `title`
can never forge a key. The marker is tool-owned — a human editing the body must
leave it alone.

Why not a tag or a label: it would mean one tag/label per ticket ever created,
and ADO tags are organisation-scoped while GitHub labels are repository-scoped,
so both namespaces would grow without bound. Why not the search API: the join
is correctness-critical, and code search is eventually consistent and rate
limited. Enumerating the map's own children is bounded, strongly consistent,
and needs one round trip per run regardless of ticket count.

Two rules a backend must enforce rather than guess:

- **Keys are unique within a map.** Finding two children with the same key is
  an error — fail, do not pick one.
- **A child with no key marker is not a decision-map ticket.** Ignore it (the
  local backend does the same for a filename that is not a safe slug), so a
  hand-created child issue cannot collide with the join.

## Backend mappings

| Concept | ADO | GitHub | Local |
|---|---|---|---|
| map | work item `mapType`, tag `decision-map:map` | issue, label `decision-map:map` | `docs/decision-map/<slug>/map.md` |
| ticket | child via `System.LinkTypes.Hierarchy-Reverse`, tag `decision-map:ticket`, body line `Decision-Map-Type: <type>` | sub-issue (native REST if available, else task-list in map body), labels `decision-map:ticket`, `decision-map:type:<type>` | `tickets/<slug>.md` with frontmatter |
| ticket `key` | `<!-- decision-map:key:<key> -->` in `System.Description` | `<!-- decision-map:key:<key> -->` in the issue body | the filename stem `tickets/<key>.md` |
| claim | `System.AssignedTo` | assignee | frontmatter `assignee:` |
| close | `System.State` → `Done` (fallback `Closed` on 400) | state closed | frontmatter `status: closed` |
| blocking | `System.LinkTypes.Dependency-Reverse` on the blocked item → predecessor | native "blocked by" if the plan supports it, else body line `blocked-by: #<n>` (weaker — the script labels it) | frontmatter `blocked_by: [slug]` |
| resolution | work-item comment | issue comment | `## Resolution` section inside the `decision-map:resolution` markers (see below) |

## Local map/ticket file formats

`map.md`:

```markdown
# Decision map — <effort name>

<one small overview mermaid diagram (diagram convention applies to local files)>

## Destination
<one or two lines>

## Notes
<domain; skills every session should consult; standing preferences>

## Decisions so far

<!-- decision-map:decisions:start -->
- [<ticket title>](tickets/<slug>.md) — <one-line gist>
<!-- decision-map:decisions:end -->

## Not yet specified

<!-- decision-map:fog:start -->
- <fog line>
<!-- decision-map:fog:end -->

## Out of scope

<!-- decision-map:scope:start -->
- <ruled-out line>
<!-- decision-map:scope:end -->
```

An empty list region holds the single line `- (none)`, which is tool-owned:
the merge drops it as soon as a real line arrives and restores it if the list
becomes empty again.

`tickets/<slug>.md`:

```markdown
---
title: <ticket title>
type: grilling
mode: HITL
status: open
assignee:
blocked_by: []
gist:
---

## Question

<the decision or investigation this ticket resolves>
```

`## Resolution` (written by `resolve` into the ticket file):

```markdown
<!-- decision-map:resolution:start -->
## Resolution

<gist — one or two lines>

Detail: <link to repo ADR / commit, when one exists (ADR 0036)>

<optional --body-file content, which may contain its own "## " sub-headings>
<!-- decision-map:resolution:end -->
```

### Generated regions in local files (local backend only)

Four spans of a local file are **generated regions**, each delimited by an HTML
comment pair: the resolution block in `tickets/<slug>.md`, and the
"Decisions so far" index, the "Not yet specified" list and the "Out of scope"
list in `map.md`. Everything else in those files is user content.

An additive `chart` rewrites only the two `map.md` list regions and leaves the
rest of that file byte-identical. It leaves a ticket file byte-identical too
**unless the ticket gains a blocking edge**, in which case exactly one line
changes — the frontmatter `blocked_by:` list gains one entry (ADR 0055) — and
every other byte, including the resolution region, is untouched. A ticket that
gains no edge is not opened for writing at all.

The rules, which any reader or writer of the local format must honour:

- **`resolve` owns strictly the span between its markers** and rewrites it
  wholesale; it never edits, and never needs to parse, anything outside it.
  The `map.md` index is likewise regenerated in full from the ticket
  frontmatter of every closed ticket — one physical line per ticket — so it is
  a projection, not accumulated state. **Its entries are ordered by ticket
  slug (ascending), not by when each decision was resolved**, so the index is
  a deterministic function of the ticket files and re-running the projection
  never reorders it. The local backend records no resolution timestamp, so
  resolution order is not recoverable from the files.
- **Only the tool writes markers.** Every user-supplied string — a ticket
  `question`, a `comment` body, `gist`, `link`, `--body-file` content, titles,
  `notes`, fog and out-of-scope lines — is escaped on the way in, so the
  literal text `<!-- decision-map:` in user content is written as
  `&lt;!-- decision-map:` (which still renders as typed, but is not a marker).
  A file must contain at most one well-formed region of each kind; a writer
  that finds otherwise should refuse to write rather than guess.
- **Do not emit an unmarked resolution block.** `resolve` treats an
  unmarked `## Resolution` as pre-existing user content and appends a fresh
  marked block below it, so an unmarked block written by another tool will
  be duplicated rather than updated.

These markers are specific to the local backend's Markdown files. ADO and
GitHub record the resolution as a native tracker comment and need no
equivalent.
