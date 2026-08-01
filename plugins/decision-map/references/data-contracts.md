# decision-map data contracts

Single source of truth for the shapes exchanged between the decision-map flow
skills and the backend ops scripts (ADR 0037). Nothing else redefines them.
The tracker (or the local files) is the source of truth; these JSON files are
working files, never a store.

```mermaid
erDiagram
    MAP ||--o{ TICKET : "parent of"
    TICKET ||--o{ TICKET : "blockedBy"
```

## What ships, and what is specification (ADR 0059)

**v1 ships exactly one backend: local markdown.** `scripts/local_map_ops.py` is
the only ops script that exists. Azure DevOps and GitHub Issues are **phase 2**,
gated on running the six-step probe below ("Before building the join") against a
live tracker. Read this document in two layers:

| Part | Status |
|---|---|
| the subcommand contract, `map_input.json` / `map.json` / `frontier.json`, the dry-run plan and its action vocabulary, the `key`-join rules, the local file formats and their generated regions | **shipping** — implemented and tested by the local backend |
| every tracker-specific part: the Backend-mappings table, the ADO / GitHub marker regions, "Where each field lives on a tracker", the ADO / GitHub `status` reading rules, the verification probe and its fallback ladder | **phase-2 specification** — nothing implements it yet |

Both layers are normative, and the phase-2 layer stays here unchanged: it is the
specification phase 2 implements, and the reasoning behind the `key` join is the
most valuable thing in this document. But nothing in it describes code you can
run today. Where a rule reads "every backend must …", it binds every backend
that ships — today that is one — and every backend phase 2 adds.

The flow skills are backend-neutral: the subcommands, flags and JSON shapes below
do not change when a tracker lands, only which ops script the skills call.

## Subcommand contract (identical on every backend)

| Subcommand | Args | Effect |
|---|---|---|
| `chart` | `--input <map_input.json> --output <map.json>` | create map + tickets + blocking edges, **additively** (ADR 0057/0058) — see below. **Parent links are tracker-only**: the local backend expresses containment by directory and creates none. **Dry-run by default**; `--real` performs the writes; `--force` is a **destructive** full rewrite that discards recorded resolutions, claims and edges. |
| `read` | `--map <id\|slug> --output <map.json>` | fetch map + children at low resolution. |
| `frontier` | `--map <id\|slug> --output <frontier.json>` | open + unblocked + unclaimed children. |
| `claim` | `--map <id\|slug> --ticket <id\|slug> [--user <upn>]` | assign the ticket to the caller. `--user` works on **every** backend (it sets the local `assignee:` frontmatter too); passing an empty value releases the claim. |
| `resolve` | `--map <id\|slug> --ticket <id\|slug> --gist "<one line>" [--link <url>] [--body-file <md>]` | post resolution comment, close the ticket. |
| `comment` | `--map <id\|slug> --ticket <id\|slug> --body-file <md>` | plain comment. |
| `block` | `--map <id\|slug> --ticket <id\|slug> --blocked-by <id\|slug>` | dependency edge (ticket waits on blocked-by). |

**`--map` is required on every ticket subcommand**, not only on `read` and
`frontier`: a ticket is identified by its map plus its key, and no backend
resolves a bare `--ticket` by global search (that is the same rejected
search-the-tracker shortcut as in the join below). Omitting it is a usage
error — the local backend exits `2` with `resolve needs --map`.

Every subcommand also accepts `--dry-run` (change nothing) — for `chart` that
is already the default. **Only `chart` renders a plan.** On `claim`, `resolve`,
`comment` and `block` the shipping backend prints a stub,
`{"dryRun": true, "wouldRun": <cmd>, "ticket": <ticket>}`, and does **not**
check that the map or ticket exists. A tracker backend must match that: a
dry-run that quietly performs lookups is not free, and one that renders a plan
where local renders a stub is not at parity.

### Exit codes and return shapes

Three exit codes, on every subcommand and every backend:

| Exit | Meaning | stdout | stderr |
|---|---|---|---|
| `0` | success | the subcommand's JSON document | empty, except `chart`'s plan rendering (dry-run) or its divergence lines (real run) |
| `2` | a **known** failure — bad usage, missing map or ticket, validation error | **empty** | exactly one line naming the problem |
| `1` | an unhandled crash | empty | a traceback |

Exit `2` with empty stdout is the contract the flow skills rely on; a backend
that prints a partial document alongside an error breaks them. Return shapes:

| Subcommand | stdout on success |
|---|---|
| `chart` (dry-run) | `{backend, dryRun: true, planned[], divergence[]}` |
| `chart --real` | the `map.json` document plus a `divergence` key |
| `read` | `map.json` |
| `frontier` | `frontier.json` |
| `claim` | `{"claimed": <ticket>, "assignee": <user>}` |
| `resolve` | `{"resolved": <ticket>, "gist": <gist **as stored**>}` — flattened and escaped, or `null` when the flattened value is empty. Never echo the raw input. |
| `comment` | `{"commented": <ticket>}` |
| `block` | `{"ticket": <t>, "blockedBy": [<the full list>]}` |

`block` **must not issue a write when the edge already exists** — it returns
the same document and touches nothing. On a tracker this matters more than on
local: a redundant link call bumps `System.Rev` and shows in the item history.

**`--user` has no default identity.** The shipping backend writes the literal
string `"me"` when `--user` is omitted. That is meaningless as an ADO
`System.AssignedTo` or a GitHub assignee, so a tracker backend must resolve the
caller's identity itself (`az account show` / `gh api user`) and must not write
`"me"`. Passing an empty value still releases the claim.

### `chart` is additive (ADR 0057, refined by ADR 0058)

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
  (ADR 0058). That ticket gains one entry and **nothing else** — every other
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
it in `tickets[]`** (ADR 0058). A `blocks` target must exist either in this
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
| listed in `tickets[]` **and already exists** | `OVERWRITE` | **all discarded** — status back to `open`, assignee cleared, gist cleared, resolution removed, `blockedBy` reset and then re-wired from this input's `blocks` |
| listed in `tickets[]` but **does not exist yet** | `create` | nothing to discard — `--force` does not change how a new ticket is created |
| the map itself | `OVERWRITE` | the **whole map document is regenerated** from the input. Fog and out-of-scope lines that existed only on the map and are absent from the input are lost — the one place additive's union guarantee does not apply — and so is any human prose added *outside* the generated regions. On a tracker that prose is the map item's description, where a team naturally adds context, and the plan shows one `OVERWRITE` line for all of it |
| named only in a `blocks` list, not in `tickets[]`, and **does not yet hold that edge** | `merge` | **nothing discarded** — it gains the edge and keeps its status, assignee, gist and resolution, exactly as on the additive path |
| named only in a `blocks` list and **already holds that edge** | *absent from the plan* | **untouched** — `block` and `chart` both no-op on an edge that exists, so there is nothing to announce |
| present on the map but in neither `tickets[]` nor any `blocks` | *absent from the plan* | **untouched** — `--force` never reaches an item this input does not name |

A backend must therefore not implement `--force` as "delete the map and
re-chart": that would destroy items the input does not mention, which neither
the plan nor this contract permits. Every destructive act must appear in the
dry-run plan as an `OVERWRITE` line before it happens.

One consequence worth knowing: the "Decisions so far" index is a projection
refreshed by `resolve`, and `--force` rewrites the map body without
re-projecting it, so **the index comes out empty** — not narrowed to the
surviving decisions. Every rewritten ticket is reset to `open` so could not
appear anyway, and a ticket that is still closed (because the input named it
only in a `blocks` list, or did not name it at all) keeps its own closed state
but drops out of the index too. It is **self-healing**: the next `resolve`
re-projects the index from every closed ticket and all of those entries come
back. A backend must therefore not implement a partial refresh here — the
index is either fully re-projected or left for the next `resolve` to rebuild.

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
naming what it will add — `unions blockedBy: fog-graduate` on a ticket,
`adds 2 fog lines, 1 out-of-scope line` on the map body — so the ADR-0039
approval gate can show the reviewer every write before it happens. **No
`merge` entry may carry `detail: null`**: the gate asks the user to approve
that line, and a blank one asks them to approve an undescribed write.

#### Dry-run plan schema

`chart` with `--dry-run` (the default) writes this to stdout and nothing else:

The worked example is the **shipping** backend, because this plan is exactly what
the ADR-0039 approval gate puts in front of the user:

```json
{
  "backend": "local",
  "dryRun": true,
  "planned": [
    { "path": "docs/decision-map/billing/map.md",                 "action": "merge",         "detail": "adds 1 fog line" },
    { "path": "docs/decision-map/billing/tickets/auth-model.md",  "action": "skip (exists)", "detail": null },
    { "path": "docs/decision-map/billing/tickets/rollout.md",     "action": "merge",         "detail": "unions blockedBy: auth-model" },
    { "path": "docs/decision-map/billing/tickets/new-thing.md",   "action": "create",        "detail": null }
  ],
  "divergence": ["<human-readable string>", "..."]
}
```

A phase-2 tracker backend emits the same document with `"backend": "ado"` /
`"github"` and the ticket `key` (or the literal `<map>`) in `path` — see the
`path` bullet below.

- `dryRun` is `true` only on a dry run; a real run returns `map.json` instead,
  with `divergence` added.
- **`planned` is ordered and complete**: the map first, then one entry for
  every item the run would touch — including an existing ticket that appears
  only as a `blocks` target and is therefore not in `tickets[]`. Nothing the
  run writes may be missing from it; that is the whole value of the gate.
- `path` identifies the item. The name is historical — it is the file path on
  the local backend, and on a tracker it is the ticket **`key`**, or the
  literal `<map>` for the map item. It is a display and correlation handle,
  not something to parse.
- `action` is one of the four labels above. `detail` is a one-line string on a
  `merge` entry saying what it will add, and `null` on every other action.
- `divergence` is always present (empty list when there is nothing to report),
  and holds the same strings the real run returns.

The same plan is rendered for humans on **stderr**; stdout carries JSON or
nothing, so `chart --input x | jq` works — a split every backend must keep.

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
    "destination": "<one or two sentences — stored as a single line>",
    "notes": "<skills to consult; standing preferences — stored as a single line>",
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
  "backend": "local",
  "map": { "id": "billing", "name": "Decision map — <effort>",
           "url": "docs/decision-map/billing/map.md", "destination": "<line>" },
  "tickets": [
    { "key": "auth-model", "id": "auth-model", "name": "Auth model — …",
      "url": "docs/decision-map/billing/tickets/auth-model.md",
      "type": "grilling", "mode": "HITL",
      "status": "open", "assignee": null, "blockedBy": [],
      "gist": null },
    { "key": "rollout-order", "id": "rollout-order", "name": "Rollout order — …",
      "url": "docs/decision-map/billing/tickets/rollout-order.md",
      "type": "grilling", "mode": "HITL",
      "status": "open", "assignee": null, "blockedBy": ["auth-model"],
      "gist": null }
  ]
}
```

Note the direction, because it inverts between the two documents and is the
one relation the whole graph is built from: the input above says `auth-model`
**blocks** `rollout-order`, so it is `rollout-order` that comes back
`"blockedBy": ["auth-model"]`. `auth-model` itself is blocked by nothing. The
`frontier.json` example below shows the same pair the same way round.

A phase-2 tracker backend emits the same fields with its own native handles —
`"backend": "ado"`, `"id": "1235"`, `"url": "https://…"` — and the same `key`s.

`chart` (only — not `read`) adds `"divergence"`: a list of human-readable
strings naming anything the input asked for that an additive run deliberately
did not apply — a differing `title`/`destination`/`notes`, or list lines that
could not be merged into a `map.md` predating the list regions. Empty on an
initial chart and on `--force`. Blocking edges are **not** listed here: since
ADR 0058 they are applied, and appear in the dry-run plan as a `merge`.

`status` ∈ `open | closed`. `blockedBy` lists upstream blockers — the tickets
that must close before this one is actionable; every backend computes it from
its own native dependency mechanism (see the "blocking" row of Backend
mappings below). **Its entries are `key`s, not native ids**, in every backend:
a backend that stores the edge natively (an ADO link, a GitHub "blocked by")
must resolve each linked item back to its key through the join above before
emitting this field.

**`map.json` and `frontier.json` filter `blockedBy` differently — this is
deliberate, and the two must not be made to agree:**

- **`map.json` lists *every* recorded blocker**, open or closed. It is the
  durable graph: an edge does not stop existing because the blocker was
  resolved, and a consumer redrawing the map needs all of them.
- **`frontier.json`'s `blocked[].blockedBy` lists only the *open* blockers.**
  It answers "why can I not pick this up right now", and a closed blocker is
  not a reason. This is also what makes `resolve` release the next decision.

A ticket with blockers that have all closed therefore appears on the
`frontier`, while still showing those blockers in `map.json`.

After `resolve`, `gist` holds the one-line answer. For the local backend, `id`
and `key` are both the ticket file's slug and `url` is the repo-relative file
path.

## `frontier.json` (output of `frontier`)

```json
{
  "frontier": [ { "id": "auth-model", "name": "Auth model — …",
                  "url": "docs/decision-map/billing/tickets/auth-model.md", "type": "grilling" } ],
  "blocked":  [ { "id": "rollout-order", "name": "Rollout order — …", "blockedBy": ["auth-model"] } ],
  "claimed":  [ { "id": "api-limits", "name": "…", "assignee": "thodsaphon.sonthipin@cartagena.no" } ]
}
```

Closed tickets appear in none of the three buckets — a closed ticket is done,
not actionable. `blockedBy` here carries `key`s, as it does in `map.json`, but
lists **only open blockers** — see the note under `map.json` above, which
lists every recorded blocker instead.

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
| Local | the ticket filename stem, `tickets/<key>.md` | glob `tickets/*.md`; the stem *is* the key (a stem that is not a safe slug is not a decision-map ticket: it is ignored, and a `warning:` line naming it is written to stderr so the skip is never silent) |
| ADO | marker line `<!-- decision-map:key:<key> -->` in `System.Description` | one WIQL/link query for the map work item's `System.LinkTypes.Hierarchy-Forward` children, then read each child's description |
| GitHub | marker line `<!-- decision-map:key:<key> -->` in the issue body | `GET /issues/{n}/sub_issues` — **one paginated pass**, no per-ticket fetch: the response carries full issue objects, bodies included |

Both trackers use the **same marker format as the local backend's regions**, so
one escaping rule covers all three: every user-supplied string written into a
tracker item is escaped on the way in, exactly as the local backend escapes
`<!-- decision-map:` to `&lt;!-- decision-map:`, so a `question` or `title`
can never forge a key. The marker is tool-owned — a human editing the body must
leave it alone.

Why not a tag or a label: it would mean one tag/label per ticket ever created,
and the namespace cost is real in both: ADO tags are **project**-scoped (an
unused tag is auto-deleted after about three days, so the pollution is
self-limiting but the live tag list still carries one entry per open ticket),
and GitHub labels are repository-scoped with no cleanup at all. The decisive
argument is not the pollution though — it is that **searchability buys nothing
once you enumerate the map's children**, so any namespace cost is paid for a
capability the design does not use.

Why not the search API: the join is correctness-critical, and code search is
eventually consistent and rate limited — a stale index means duplicate
tickets. Enumerating the map's own children is bounded and strongly
consistent. It is **not** one round trip: on ADO it is a WIQL query returning
ids, then `workitemsbatch` in pages of 200, so O(n/200)+1 calls; on GitHub it
is a paginated sub-issue listing. Bounded and predictable, not constant.

**Line endings are not normalised — normalise them yourself.** A tracker may
return a body with `\r\n`, `\n`, or a mix, decided by how that text was
submitted rather than by anything the tool controls. Verified live on GitHub:
`cli/cli#14021` comes back CRLF and `cli/cli#14031` LF, same repo, both with
HTML comments intact. **Every backend must normalise to `\n` on read, before
parsing regions or comparing anything, and write `\n`.** The key marker itself
is single-line and therefore safe either way, but region content is not: without
this, a human's web-UI edit can flip a whole region to CRLF and the next
`chart` sees every line as changed — breaking the byte-identical no-op
guarantee and emitting divergences for text nobody touched.

**GitHub specifics phase 2 must respect** (verified live 2026-08-01 unless
marked documented):

- **A map cannot exceed 100 tickets.** GitHub documents a hard ceiling of 100
  sub-issues per parent (and 8 nesting levels). `chart` must check the count
  before a real run and fail loudly rather than create tickets up to the cap
  and then start failing halfway.
- **Sub-issue mutations are keyed on the issue *database id*, not the issue
  number** — `sub_issue_id` and `issue_id` both take `.id`. The two are
  unrelated values. `map.json`'s `id` for GitHub must therefore carry the
  number (what humans and `--ticket` use) *and* the database id (what the
  mutations need), or every write costs an extra resolve call.
- **Dependencies cap at 50 issues per relationship type** (documented), a
  tighter limit than the 100 sub-issues and a separate one — a ticket cannot be
  blocked by more than 50 others.
- A sub-issue must share the parent's repository **owner** — which means it may
  legitimately live in a *different repository* of the same owner. The join must
  therefore key on parent identity, not on "same repo as the map".
- The remove-sub-issue path segment is **singular** (`DELETE
  /issues/{n}/sub_issue`) and takes `sub_issue_id` in the **request body**,
  which is unusual for a DELETE and easy to get wrong.
- **Secondary rate limit: 80 content-creating requests per minute.** A large
  additive `chart` must pace itself; the primary 5,000/hr limit is not the
  binding one.
- Native GitHub **issue types are organisation-scoped** and unavailable on a
  user-owned repo — which is why the type is carried by the
  `decision-map:type:<type>` label and not by the native field.
- `gh` gained first-class `--parent` / `--blocked-by` flags in **2.94.0**
  (2026-06-10). Either pin that as a prerequisite or drive the REST/GraphQL
  endpoints through `gh api`, which works on any version. GraphQL can fetch the
  map, its children, their bodies and their `blockedBy` edges in one round
  trip — worth considering over the REST list.

**Key format.** A key matches `[A-Za-z0-9][A-Za-z0-9_-]*` and **must not
contain `--`**. The HTML spec forbids `--` inside comment text, so
`<!-- decision-map:key:foo--bar -->` is a malformed comment that sanitizers
and rich-text editors rewrite or truncate — breaking the join silently and
re-creating every ticket. A double hyphen carries no meaning a single one does
not, so the key is constrained rather than the marker syntax; the alternatives
were encoding the key, which destroys the marker's greppability, or a
non-comment carrier, which is either visible to readers or strippable by
rich-text editors. The local backend rejects such a key at chart time, where
keys are minted.

#### Rules for a map a human has edited

The join must survive people editing the tracker by hand. These are errors,
not situations to work around:

- **Every child carrying the decision-map ticket tag/label must resolve to
  exactly one key, or the run fails.** In particular, a tagged child with
  **no** key marker is a **loud error** — never "ignore it and carry on".
  Ignoring it hides the ticket from the join, so `chart` labels it `create`,
  and a map whose markers were stripped (a bulk edit, an HTML sanitizer, a
  migration) is silently re-created in full and presented to the user as a
  page of ordinary, approvable `create` lines. That is the worst failure this
  contract can produce. Fail, and name the offending item.
- **Two key markers in one body is an error.** Do not take the first, the
  last, or the one that matches the input.
- **Keys are unique within a map.** Two children resolving to the same key is
  an error — fail, do not pick one.
- A child with **neither** the tag/label **nor** a key marker is simply not a
  decision-map ticket: ignore it, so an unrelated hand-created child cannot
  collide with the join. (The local backend does the same for a filename that
  is not a safe slug.)
- **A body that is absent is not an empty body.** GitHub returns `body: null`
  for an issue created with no description — verified on two live issues — so
  every read of a body must treat `null` as "no markers found" rather than
  letting a `contains`/regex throw. A *labelled* child with a null body is the
  loud error above, not a skip.
- **Parentage is authoritative.** A ticket re-parented out of this map stops
  being one of its tickets, and a later `chart` naming that key creates a
  fresh ticket rather than adopting the moved one. Re-parenting is not a
  supported way to move a decision between maps.

### Before building the join: verify it — phase 2's first step

The whole design rests on one bet — that a marker written into an item's body
survives round trips through the tracker. **Verify that before writing join
code**, because every fallback below is cheaper to adopt early than late.

> **GitHub half: PASSED, 2026-08-01.** Run against a throwaway private repo.
> The marker survives byte-for-byte through create → `GET`, through a
> close/reopen, and through a **human edit in the web UI** (the deciding test):
> a body of 122 chars came back byte-identical, and after a human typed a line
> *inside* a `decision-map:fog` region it came back as exactly the original
> plus what was typed — all three markers intact, no line-ending rewrite, no
> sanitiser. A key containing `--` also survives the API verbatim; the format
> rule stays because the local backend already rejects such keys at mint time
> and because ADO is the tracker with a rich-text editor. Sub-issue add/list
> and native `blocked_by` write+read were exercised end to end.
>
> **ADO half: NOT RUN — still the gate.** All the risk lives here:
> `System.Description` is HTML, and **Microsoft documents nothing about
> sanitisation of work-item HTML fields or whether HTML comments survive a
> `PATCH`→`GET` or a Boards rich-text edit.** This probe is therefore not
> diligence, it is the only evidence that will ever exist.

Steps 1–5 are ADO-shaped and **open**; step 6 is GitHub and is settled above.

1. `PATCH` a description containing the marker, `GET` it back, and
   **byte-compare the marker region** — not the whole body, which carries
   formatting the tracker may legitimately reshape.
2. Repeat with a key containing `--`, to confirm the format rule above is
   actually necessary on this tracker (and that a conforming key is safe).
3. **Edit that description in the Boards web UI, then re-`GET`.** This is the
   deciding test: the rich-text editor, not the API, is what rewrites HTML.
4. Close the item and reopen it, then re-`GET`.
5. Confirm the real call shape end to end: WIQL for ids (WIQL returns ids only
   whatever you `SELECT`, so the two-call shape is mandatory), then
   `workitemsbatch` in pages of 200 — **with `errorPolicy: "omit"`**, or one
   deleted child fails the whole batch. Send `fields` *and* `$expand:
   "relations"` in the same call and confirm both come back; the join needs the
   description and the links together. Capture a real `workItemRelations`
   payload for a map with 2+ children and pin the root-row shape in a fixture.
6. GitHub sub-issue API availability. **Settled: GA, no fallback needed.**

Two further ADO checks the documentation forces:

- **Enumerate `GET _apis/wit/workitemrelationtypes?api-version=7.1` rather than
  hard-coding dependency link names.** Microsoft's own WIQL page and the
  relation-types API disagree on the spelling
  (`Dependency-Predecessor/-Successor` vs `Dependency-Forward/-Reverse`); only
  `System.LinkTypes.Hierarchy-Forward` is agreed by both and safe to hard-code.
- **Use `op: "test"` on `/rev` in the JSON-Patch** when `chart` updates an
  existing item, so a concurrent human edit fails the call instead of being
  silently overwritten by a read-modify-write.

If the marker does not survive, take the first rung that does — **tags, labels
and the search API stay rejected at every rung**, for the reasons above:

1. **A key→id manifest in a marker region on the *map* item's body.** One
   marker in one place instead of n, so it is a single survival bet and costs
   zero extra calls (the map item is fetched anyway). The manifest must be
   rebuildable, since it is now a second source of truth.
2. **A tool-owned comment on the map item** holding the same manifest. Comments
   are not touched by the work-item rich-text editor, at the cost of one extra
   call per run.
3. **A key prefix in `System.Title`** (`[auth-model] Auth model — …`). Ugly and
   user-visible, and a human can rename it away, but titles survive everything.

### Parity gaps phase 2 must close

The local backend is the reference implementation, and an audit of it against
this document found places where the document is silent, where it describes
behaviour the code does not have, or where the two backends cannot both be
right. These are phase-2 work items, not descriptions of shipped behaviour.

**Decided here, because leaving them open is how the worst failure happens:**

- **The key marker is authoritative; the tag/label is decorative.** A child
  carrying a key marker **is** a decision-map ticket whether or not it still
  has the tag/label. Keying membership on the tag instead means one bulk tag
  edit hides every ticket from the join, `chart` labels them all `create`, and
  the map is silently re-created — the exact failure this contract names as the
  worst it can produce. The tag stays for human filtering and for the
  loud-error rule (a *tagged* child with no key marker still fails the run).
- **Normalise line endings to `\n` on read** before parsing regions or
  comparing anything, and write `\n` (see above).
- **A tracker must not write the literal `"me"`** as an assignee.

**Open — phase 2 must decide, and the probe can settle several:**

- **A human editing inside a generated region.** The contract says regions are
  tool-owned but never says what happens when someone types inside one. Local's
  behaviour is three-way and undocumented: markers deleted → the merge is
  skipped and a divergence reported; markers intact → the content between them
  is replaced, so the human's text is destroyed without warning. On a tracker
  the map item's description is exactly where a team adds context. Observed
  live during the GitHub probe: a human edit landed inside a `fog` region and
  the next `chart` would have overwritten it silently.
- **`read` / `frontier` on a map that does not exist.** Local `read` exits `2`;
  local `frontier` returns **exit 0 with three empty buckets**, which is
  indistinguishable from a finished map. `work-map` uses `read` as its
  existence check, so a tracker must not make `frontier` the check. Phase 2
  needs a read-failure table: missing, not-a-map, no permission, and deleted
  are four distinguishable cases on a tracker and one on local.
- **Ordering is unspecified** everywhere except the decisions index. Local
  emits `map.json.tickets[]` and the `frontier.json` buckets in key-ascending
  order, because it globs a directory. A tracker's natural order is creation or
  id order, so the two backends will disagree for the same logical state and
  nothing here says which is right. Pick one and write it down.
- **A blocker whose item no longer exists.** Local keeps the phantom key in
  `map.json.blockedBy` but `frontier` silently drops it, so deleting a blocker
  quietly unblocks its dependents. On a tracker this is the *common* case
  (items get deleted, moved, re-parented). The "Foreign edge targets" rule
  covers a link pointing out of the map, not a recorded key with no surviving
  item.
- **Tag/label provisioning is outside the dry-run plan**, which contradicts
  "nothing the run writes may be missing from it". A tracker `chart` must
  create `decision-map:map` / `decision-map:ticket` / `decision-map:type:*` if
  absent. Either extend the action vocabulary to cover it or declare it a
  preflight outside the gate — but say which.
- **`resolve` is the most expensive operation, not the cheapest.** It
  re-projects the decisions index by reading *every* ticket. On local that is n
  file reads; on a tracker it is a full enumerate-and-read pass plus a comment,
  a state change, a gist-region write and a map-body write. The cost analysis
  above only budgets the join. Write the per-subcommand call budget down before
  implementing, or phase 2 discovers this the slow way.
- **The escaping rule may not be portable.** Local flattens then scrubs
  `<!-- decision-map:` → `&lt;!-- decision-map:`, and *nothing may transform the
  string afterwards*. ADO stores `System.Description` as HTML, so a tracker
  backend must HTML-encode user text — a transformation applied after the
  escape, which this contract forbids. GitHub is settled (the escaped form
  round-tripped byte-identical through the API **and** through a web-UI edit);
  ADO is not. If ADO re-encodes `&lt;` to `&amp;lt;` the no-op guarantee
  breaks; if it decodes back to a live `<!--` a user string forges a marker.
- **The write-side region check covers 3 of the 5 markers.** `_assert_regions`
  validates `fog`, `scope` and `decisions`; `key` and `gist` are not paired
  regions and are not counted the same way. A tracker must decide whether to
  validate regions on **read** as well — a corrupted map is currently invisible
  to `read`, `frontier` and a no-op `chart`.

**Statements corrected in this document from that audit:** `chart` no longer
claims to create parent links on every backend (local creates none); `--dry-run`
no longer claims to print planned mutations for the four ticket subcommands; the
`merge` rows now say an item already holding the edge is *absent from the plan*
rather than labelled `merge`; and `--force` on the map is recorded as
regenerating the whole document, so human prose outside the generated regions is
lost too.

## Backend mappings

| Concept | ADO | GitHub | Local |
|---|---|---|---|
| map | work item `mapType`, tag `decision-map:map` | issue, label `decision-map:map` | `docs/decision-map/<slug>/map.md` |
| ticket | child via `System.LinkTypes.Hierarchy-Reverse`, tag `decision-map:ticket`, body line `Decision-Map-Type: <type>` | **sub-issue (native REST — GA since 2025-04-09, no fallback)**, labels `decision-map:ticket`, `decision-map:type:<type>` | `tickets/<slug>.md` with frontmatter |
| ticket `key` | `<!-- decision-map:key:<key> -->` in `System.Description` | `<!-- decision-map:key:<key> -->` in the issue body | the filename stem `tickets/<key>.md` |
| claim | `System.AssignedTo` | assignee | frontmatter `assignee:` |
| close | `System.State` → `Done` (fallback `Closed` on 400) | state closed | frontmatter `status: closed` |
| blocking | `System.LinkTypes.Dependency-Reverse` on the blocked item → predecessor | **native issue dependencies** — `POST /issues/{n}/dependencies/blocked_by` with `issue_id`; readable both directions (GA 2025-08-21, no fallback) | frontmatter `blocked_by: [slug]` |
| resolution | work-item comment | issue comment | `## Resolution` section inside the `decision-map:resolution` markers (see below) |
| ticket `key` | `<!-- decision-map:key:<key> -->` in `System.Description` | `<!-- decision-map:key:<key> -->` in the issue body | the filename stem `tickets/<key>.md` |
| ticket `gist` | `decision-map:gist` region in `System.Description` | same region in the issue body | frontmatter `gist:` |
| map `destination` / `notes` | prose in the map item's description | prose in the map issue body | `## Destination` / `## Notes` |
| map `notYetSpecified` / `outOfScope` | `decision-map:fog` / `decision-map:scope` regions in the map item's description | same regions in the map issue body | the same two regions in `map.md` |

### Where each field lives on a tracker

The local backend keeps everything in Markdown files. A tracker backend needs
an equivalent home for each field, and the same enumerate-and-read pass that
builds the key join should recover all of them without extra calls.

**`gist`.** `resolve` posts the human-facing resolution as a native tracker
comment, but the gist must also be **recoverable** for `map.json`, and walking
every ticket's comments costs one API call per ticket. So the gist is *also*
written into a `decision-map:gist` marker region on the ticket item itself and
read from there — one line, flattened and escaped exactly as the local backend
flattens it into frontmatter. The comment is the record a human reads; the
region is the field a machine reads. They are written in the same operation
and must not be allowed to diverge.

**The map body lists.** Additive `chart` unions `notYetSpecified` and
`outOfScope`, so a tracker needs the same delimited regions `map.md` uses:
read the map item's body, replace the content between the markers, write it
back. **Only the resolution markers are local-only** — a tracker records the
resolution as a native comment instead. The `key`, `gist`, `fog`, `scope` and
`decisions` markers are shared by every backend that stores text, and carry
the same escaping rule (user-supplied strings are escaped on the way in, so
nothing a user types can forge a marker).

**Foreign edge targets.** decision-map models dependencies **within one map**.
On write, an edge target must be in this input or already a child of this map;
anything else is a validation error, exactly as the local backend enforces. On
read, a native dependency link pointing at an item that is not a child of this
map has no key, cannot be expressed in `blockedBy`, and is **ignored** — it is
not part of the decision-map graph. A cross-map dependency added by hand in
the tracker UI is therefore invisible to the tool; express it as a fog line or
a note instead. A backend must not invent a synthetic key, and must not leak a
native id into `blockedBy`.

**Reading `status` back.** The "close" row above gives the write direction
only. Reading:

| Backend | `open` | `closed` |
|---|---|---|
| ADO | any other state category | `System.State` whose **state category** is `Completed` or `Removed` |
| GitHub | `state` is `open` | `state` is `closed` — read `state` **only** |
| Local | frontmatter `status: open`, or absent | frontmatter `status: closed` |

Match on ADO's **state category**, never on the literal state name: names
differ per process (Agile `Closed`, Scrum `Done`, Basic `Done`) and a project
may add its own, so a name-based check silently mis-reads a customised
process. `Removed` maps to `closed` because a removed item is not actionable;
like any closed ticket it then appears in no `frontier.json` bucket. The
category for a type is one call:
`GET {org}/{project}/_apis/wit/workitemtypes/{type}/states?api-version=7.1`
returns `{name, color, category}`. Note this rule contradicts the **close**
row's `Done` → fallback `Closed` on 400, which is name-based: `Done` is the
completed state in Basic and Scrum, `Closed` in Agile and CMMI, so the pair
covers the four stock processes and nothing else. Phase 2 should resolve the
target state through the states API rather than guessing and catching a 400.

**Never key on GitHub's `state_reason`.** A closed issue can carry
`state_reason: null`, and the enum has grown beyond `completed` /
`not_planned` (it now includes `duplicate` and `reopened`), so any check that
enumerates reasons mis-reads issues that are plainly closed. `state` alone is
the signal.

## Local map/ticket file formats

`map.md`:

```markdown
# Decision map — <effort name>

<one small overview mermaid diagram (diagram convention applies to local files)>

## Destination
<one or two sentences, always rendered as a single line>

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
changes — the frontmatter `blocked_by:` list gains one entry (ADR 0058) — and
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
- **Escape LAST: flatten first, then escape — never the other way round.**
  Any transformation applied to a string *after* it is escaped can put a
  marker back together. Flattening a value like
  `"<!--\ndecision-map:resolution:start -->"` to a single line finds no marker
  to escape if the escape has already run, and then reconstitutes a live one
  that nothing ever inspected. Whatever a backend does to user text —
  flattening to one line, trimming, collapsing whitespace, converting Markdown
  to HTML — must happen **before** the escape, and nothing may touch the
  string afterwards. Flatten using the same line-break definition the reader
  splits on, so writer and parser cannot drift apart (Python's
  `str.splitlines()` breaks on eight separators beyond CR/LF, including
  U+0085, U+2028 and U+2029). This rule cost four review rounds to get right
  and is invisible in the output when it is working; a backend that escapes
  first will pass every ordinary test and corrupt real files.
- **Do not emit an unmarked resolution block.** `resolve` treats an
  unmarked `## Resolution` as pre-existing user content and appends a fresh
  marked block below it, so an unmarked block written by another tool will
  be duplicated rather than updated.

Only the **resolution** markers are specific to the local backend's Markdown
files: ADO and GitHub record the resolution as a native tracker comment and
need no equivalent. The `key`, `gist`, `fog`, `scope` and `decisions` markers
are **shared by every backend that stores text** — see "Where each field lives
on a tracker" above — and carry the same escaping rule and the same
one-well-formed-region-per-kind rule stated here.
