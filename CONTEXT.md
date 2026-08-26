# workflow-daily-work

The glossary for this Claude Code plugin **marketplace** — the words its plugins, skills
and documents use, and what each one means *here*. Marketplace-wide terms come first;
per-plugin sections follow.

## Language

**Organization**:
An Azure DevOps organization, referenced everywhere by its **bare name** (e.g.
`Cartagena365`) — the single segment after `dev.azure.com/`. It is **not** a URL, and
**not** the Azure subscription or Entra tenant the account signs into (`az account show`
returns the latter, which is a different thing). Carried as `AZDO_ORG`.
_Avoid_: org URL, Azure subscription, tenant, account.

**Project**:
A project inside an Organization (e.g. `GlassHull`), referenced by name (exact casing).
A work item type is only valid relative to the project's **process** (Agile, Scrum,
Basic, CMMI). Carried as `AZDO_PROJECT`.
_Avoid_: team project, board, repo.

## Repo architecture terms

**Marketplace**:
The repo as a whole — a Claude Code plugin marketplace declared in
`.claude-plugin/marketplace.json`. It _lists_ plugins; it is not a plugin itself.
_Avoid_: repo (ambiguous), package.

**Front page**:
`README.md` at the marketplace root — the entry document for someone who has not used this
repo before. An **index**, not a catalogue: it names plugins, their entry commands and
their prerequisites and then links onward, and it never names or counts individual skills,
because those churn and this is the page nobody remembers to update (ADR 0090).
_Avoid_: landing page, overview, docs.

**Playbook**:
`PLAYBOOK.md` at the marketplace root — the map of the daily arc, one row per skill,
answering *what do I reach for now*. The maintained skill index, which is why the **Front
page** points here rather than restating it.
_Avoid_: README, index, guide.

**Plugin**:
A self-contained unit a colleague installs (e.g. `ado-backlog`), defined by its own
`.claude-plugin/plugin.json`. Bundles skills, commands, scripts, and references.

**Skill**:
A single reusable capability under `skills/<name>/SKILL.md`, model-invoked by its
`description` triggers. One pipeline step = one skill.
_Avoid_: command (a command is a thin user-typed entry point, not the capability).

**Command**:
A user-typed `/ado-backlog:<name>` entry point under `commands/<name>.md`; a thin
wrapper that hands off to a skill. Not where logic lives.

**Orchestrator**:
The one skill (`findings-to-ado-backlog`) that sequences the other skills end-to-end
and enforces the safety gates. A skill, but the conductor — not a peer step.

**Data contract**:
One of the three JSON files (`findings.json`, `backlog_input.json`,
`backlog_result.json`) that carry state between steps, joined by a stable `key`.
Canonical shapes live in `references/data-contracts.md` — that file is the source of
truth; nothing else redefines them.

**Safety gate**:
A deliberate stop before an irreversible action: dry-run before real create, explicit
user approval before any write, back up the source before write-back.

**Document skill**:
A skill whose output is a durable Markdown artifact (ARCHITECTURE.md, post-mortem,
design spec, audit, trace). Always includes Mermaid diagrams (ADR 0005/0006).
_Avoid_: study skill (narrower), doc generator.

**Channel output**:
Skill output shaped for a delivery channel (Slack, JIRA comment, email, standup line,
Tribletext) rather than a repo document. Exempt from the diagram convention; a document
skill posting to a channel asks before stripping diagrams (ADR 0006).
_Avoid_: chat output, message.

**Diagram convention**:
The rule that every skill-generated Markdown document opens with one overview Mermaid
diagram, adds type-matched diagrams per section (sequence = flow, er = data,
flowchart = decision, graph = hierarchy), and that ADRs carry a small decision diagram
(ADRs 0005–0009). Governs **Markdown-document** output only; an interactive skill whose
output is a live terminal session follows the sibling **Terminal diagram** rule instead
(ADR 0010). Canonical wording: `plugins/dev-workflows/references/diagram-convention.md`.
_Avoid_: UML rule (it's the Mermaid family, not strict UML class diagrams).

**Terminal diagram**:
A text / box-drawing diagram authored to read in a monospace **terminal** session, used by
an **interactive skill** whose output is a live chat session rather than a `.md` document
(e.g. debug-mantra's four-step process diagram). Unicode box-drawing, vertical layout,
emitted inside a fenced code block. The terminal sibling of the **Diagram convention** —
introduced because Mermaid fences don't render in a terminal (ADR 0010). Canonical wording
lives alongside the Mermaid rules in
`plugins/dev-workflows/references/diagram-convention.md`.
_Avoid_: ASCII art (too generic), UML diagram (not class-diagram UML), Mermaid diagram.

**Term drill-down**:
A mechanism in a `problem-description` walkthrough by which the reader clicks an
unfamiliar term in the narration to open a **side drawer** showing a short definition —
sourced from this repo's `CONTEXT.md` glossary and inlined into the self-contained HTML
at authoring time (ADR 0017) — with **see-also** links that hop to related terms,
swapping the drawer per hop. Cross-cutting: it applies to every walkthrough mode, not a
mode of its own (ADRs 0016, 0018). The drawer code is kept DRY in one reference file
(`references/term-drilldown.html`) and inlined at generation (ADR 0019). Makes a
walkthrough *glossary-aware*.
_Avoid_: tooltip (narrower — can't hop), glossary popup, nested sub-walkthrough.

## Decision-map terms (decision-map plugin)

**Decision map**:
The fourth plugin (ADR 0033/0034) and its canonical artifact: one map item that
indexes a multi-session planning effort — the destination, decisions so far, open
fog, and out-of-scope list. In v1 that item is `docs/decision-map/<slug>/map.md`
in the repo; the tracker form (a work item / issue tagged or labelled
`decision-map:map`) is specified but deferred to phase 2 (ADR 0059). An **index,
not a store**: each decision's detail lives in its Decision ticket; the map only
gists and links.
_Avoid_: wayfinder (the upstream skill it adapts), roadmap, epic.

**Decision ticket**:
A child item of a Decision map (in v1 a file under its `tickets/` folder, in phase
2 a child work item / sub-issue) whose resolution is a **decision** — a question
to settle, sized to one agent session — not a slice of a build to execute. Closed
with the answer recorded on the ticket; the map gets a one-line gist + link. When a
repo ADR exists for the decision, the ticket only gists and links it — the ADR stays
canonical (ADR 0036). Typed `research`, `prototype`, `grilling`, or `task`
(ADR 0038).
_Avoid_: implementation ticket, task (an ADO/GitHub work item type, not this),
user story.

**Milestone**:
A named, **ordered**, shippable increment on the way to a Decision map's
destination — the group of Decision tickets that must all close before building
that increment can begin. The ordering intent is declared once (at chart time or
when it becomes clear) and stored on the map, so no session re-derives "what
ships first" (ADR 0094). First-class map structure, not a ticket (ADR 0095).
Distinct from GitHub's native milestone object and from an ADO iteration — those
are backend furniture, not this term.
_Avoid_: sprint, iteration, phase, epic, release.

**HITL / AFK ticket**:
Every Decision ticket is one or the other. **HITL** (human-in-the-loop) resolves
only through live exchange with the human — the agent never answers its own
questions (grilling, prototype). **AFK** is agent-driven without the human
(research, some tasks). The mode determines who speaks, not who types.
_Avoid_: manual/automated (it's about who decides, not who executes).

## Career-growth terms (dev-workflows plugin)

**Moat**:
A skill combination that passes **all four tests**: (1) *rare* — few people in the
same target market hold it; (2) *evidenced* — backed by tangible public proof
(shipped repo, certificate, delivered work); (3) *paid* — demand verified by real
market signals; (4) *durable* — expected to survive ≥3 years against AI/automation
absorption (ADR 0044). Every recommendation the career-growth skill emits must state
how it passes each test.
_Avoid_: strength, unique selling point (marketing term), specialty (implies depth
only — a moat is a combination).

**Job family**:
A named, hireable role with its own career ladder inside a market ring — e.g.
*Solution Architect*, *AI Platform Engineer* — the unit MARKET's pass 2a counts
(workflow-daily-work-0148). Distinct from a skill keyword (*Dataverse*, *MCP*):
round 1 counted keywords and missed the families; a family is what a person is
actually hired as, and it carries the gates (language, certs, domain) a plan
must clear.
_Avoid_: job title (one posting's string, not the ladder), role keyword.

**Declared destination**:
A career target the user declares themselves — role + ring + stack, e.g.
*Solution Architect, Bangkok, Microsoft Business Applications* — entering the
pipeline as an optional preflight input that Station 3 must argue against the
four tests as a mandatory candidate (workflow-daily-work-0151). It is an input
to validate, never a shortcut past the Station 4 gate, and never silently
swapped. Unrelated to the publishing **Destination** below (where a page lands).
_Avoid_: goal (unvalidated wish), moat (a declared destination has not passed
the four tests yet), bare destination (taken by the publishing term).

**Family gate**:
A measurable entry requirement a **Job family** states in its posting text,
read during MARKET's pass 2b in six fields — language level, named
certificates, domain experience, lead delivery, location / eligibility,
seniority signal. The first four are **plannable gates**: each one of the
chosen moat or declared destination becomes a milestone lane in
`growth-plan.md` (workflow-daily-work-0152). The last two are **scope facts**
— recorded, and they decide which ring is reachable and which rung is in play,
but they never become a lane and their absence is not a planning hole.
Distinct from the Station 4 approval gate (a pipeline stop, not a market fact).
_Avoid_: requirement (too generic), bare gate (ambiguous with the approval gate).

## GitHub terms (github-backlog plugin)

**GitHub Owner**:
The org or user name segment of a GitHub repo URL (e.g. `Cartagena365`). Carried as
`GH_OWNER`. It is **not** a URL. Mirrors `AZDO_ORG` from the ADO side.
_Avoid_: org URL, full repo path.

**GitHub Repo**:
The repository name (e.g. `GlassHull`). Carried as `GH_REPO`. Mirrors `AZDO_PROJECT`.
_Avoid_: repo URL, full path.

**Tracking Issue**:
A GitHub Issue whose body contains a task list (`- [ ] #N title`) linking all issues
created in a batch. GitHub renders it as a progress bar. The GitHub equivalent of an
ADO Feature/Epic parent item.
_Avoid_: epic issue (ambiguous), parent issue (not a GitHub term).

**Size label**:
A `size:XS` / `size:S` / `size:M` / `size:L` / `size:XL` label on a GitHub Issue
encoding the effort estimate for that item. Maps from raw hours during classification.
_Avoid_: story points (different concept), estimate label.

## Vendored-skill terms (superpowers copies)

**Vendored Skill**:
A copy of an upstream `superpowers` **Skill** inside this **Marketplace**, taken so that
**where a review step dispatches, it routes to** `scrutinize-dispatch` - a dispatch-tuned
copy of the frozen `scrutinize` - instead of to the built-in reviewer (ADR 0084). Two of
the six dispatch: `sp-requesting-code-review` and `sp-subagent-driven-development`. The
other four are copied for **chain integrity**, not for a review step of their own -
`sp-brainstorming` and `sp-writing-plans` review inline (their document-reviewer prompts
are dead files, ADR 0074), `sp-receiving-code-review` teaches how to *take* feedback
(ADR 0078), and `sp-executing-plans` reviews the plan itself. Leave any of the four
upstream and the arc re-enters the originals one handoff later. Six exist by decision
(ADR 0071) - the review-carrying half of upstream's 14. A Vendored Skill takes the
**`sp-` prefix** and references its siblings by short name; the upstream original stays
live and is never edited (ADR 0070).
_Avoid_: fork (nothing goes back upstream - that is out of scope), shim, override
(`skillOverrides` was measured inert against plugin skills).

**`sp-` prefix**:
The marker on every Skill in this Marketplace that belongs with `superpowers` - both a
**Vendored Skill** (`sp-writing-plans`) and this Marketplace's own superpowers-based
Skills (`sp-grill-with-doc`, which is *not* a copy). It means "belongs with
superpowers", not "is a copy of superpowers", so a search for `sp-` is not by itself a
list of Vendored Skills. No upstream Skill name begins with `sp-`, which is what makes a
short reference unambiguous in both harnesses (ADR 0071).
_Avoid_: namespace (the Plugin prefix is the namespace), superpowers prefix.

**Reviewer prompt**:
One of **three** files in a **Vendored Skill** that dispatch a reviewer subagent -
`code-reviewer.md`, `task-reviewer-prompt.md`, `re-review-prompt.md` - but only the first
two are routed. `re-review-prompt.md` is deliberately left unrouted: a re-review verdicts
prior findings as ADDRESSED / NOT ADDRESSED, a concept `scrutinize-dispatch` has no notion
of (ADR 0074, amendment of 2026-08-16). For the two that are routed, the file is the
*harness*: it supplies the per-touchpoint context (base/head sha, brief file, findings)
and states the operating rules a dispatched agent needs. It does **not** carry the output
contract - both `## Output Format` sections were deleted from the routed prompts, and the
contract now lives only in `scrutinize-dispatch/SKILL.md:79-115`. The review *method* and
the report shape are both delegated to `scrutinize-dispatch`, the *engine*, which emits
`Critical`/`Important`/`Minor` natively, with no translation at the boundary (ADR 0084,
superseding ADR 0076).
_Avoid_: reviewer skill (it is a file, not a Skill), review template (the three differ by
touchpoint, they are not one template).

**Resync checker**:
The program `plugins/dev-workflows/scripts/check_vendored_superpowers.py`. It reads the
**Vendoring manifest**, reports, and changes nothing - a person makes the repairs it names
and re-runs it until it exits `0` (ADR 0075). It has two modes: **local** (default, no
network) asks whether *our* copies changed since they were vendored; **`--upstream-dir`**
asks which of the 21 files upstream changed, by comparing against an upstream tree the
runner supplies. Every hash and every comparison is CR-normalized first (ADR 0086).
_Avoid_: resync script (it re-applies nothing - a rewriter was rejected in ADR 0075),
linter, validator (`validate_model.py` is a different thing), CI check (there is no CI).

**Vendoring manifest**:
The JSON file `plugins/dev-workflows/references/vendored-superpowers.json`, read only by
the **Resync checker**. It holds one upstream sha for the whole copy set - never per-file -
the 21 copied files each marked `verbatim` or `edited` with a CR-normalized hash, the
**Permit list**, and the frozen set (ADR 0075, ADR 0085, ADR 0088). It carries *data*; the
rules that read it live in the checker.
_Avoid_: lockfile (nothing resolves or installs from it), inventory, provenance header
(per-file headers were rejected in ADR 0075 - they would destroy the per-file diff).

**Permit list**:
The entry in the **Vendoring manifest** naming every line that may legitimately hold a bare
upstream Skill name. Each entry stores the line's **exact text**, matched
anywhere in its file, with no line number, so upstream may move it (ADR 0087). It exists
because ADR 0071's check - *a search for any of the six upstream short names, unprefixed,
must return nothing* - has true exceptions. How many is a property of the manifest, which
grows whenever a rewrite adds a permitted line; read it there rather than from this page.
A bare name on an unlisted line is a **NEW**
finding; a listed line that has moved or been reworded is a **STALE** finding.
_Avoid_: allowlist/whitelist (this repo says permit list), exclusions, ignore list (an
ignored line is never re-read; a permitted one is re-confirmed at every resync).

**Frozen file**:
A file that must not be edited, for a reason that no compile step or test can see. Two
exist: `skills/scrutinize/SKILL.md`, frozen by the owner's constraint so the declared fork
`scrutinize-dispatch` cannot drift from something that moved underneath it (ADR 0084); and
`skills/sp-subagent-driven-development/re-review-prompt.md`, deliberately unrouted and
byte-identical to upstream (ADR 0084 amendment). The **Resync checker** reports a change to
either (ADR 0088). Reporting is all it does - it does not judge whether the change was
good.
_Avoid_: read-only (nothing on disk enforces it), immutable, locked, deprecated.

## document-what-shipped terms (dev-workflows plugin)

**Destination**:
The place a published page lands. Two families, keyed on how a page is written: an
**API page store** (one HTTP call per page, version token = an `ETag`) and a **git file
store** (write the file, commit, push; version token = the commit). A plain local folder
is the git family with the push left out. Every destination carries its own Mermaid fence
— Azure DevOps wiki uses `::: mermaid`, GitHub a triple-backtick fence — so the fence
belongs to the destination, not to the writer (ADR 0119).
_Avoid_: target, wiki (one destination among several), channel (a **Channel output** is a
message, not a page).

**Destination adapter**:
The measured recipe for one destination: how a page is addressed, read, written with a
version token, listed, given attachments, linked to, and renamed. An adapter is
**measured or it does not exist** — a recipe written from vendor documentation is a guess
that fails at publish time, after the draft is finished (ADR 0118).
_Avoid_: connector, driver, provider, integration.

**Shot list**:
The numbered list of pictures a page intends to show, one row per step, saying what each
picture must contain. Handed to the owner **before** the draft, not after. It opens the
**visual gate** only on an explicit answer — files, or a plain "no images" / "the diagram
is enough"; silence leaves the gate closed (ADRs 0121, 0122).
_Avoid_: screenshot request, attachment map (that is the later mapping of source file to
uploaded attachment name).

**Fact ledger**:
One row for every fact on the page: the fact, the places that answered it — authored
code, the platform's own automation, a live observation — and the date. It is the artifact
that proves the fact gate ran, and it is what makes a page auditable without re-reading
the system (ADR 0127).
_Avoid_: evidence list, citation table, sources.

**Provenance line**:
The one status sentence the reader sees, naming which environment the page describes, since
when, and whether it is proven on a real record. The ref, the build number and the queries
stay in the record, because a branch name tells a management reader nothing and goes stale
one deploy later (ADR 0126).
_Avoid_: version banner, build stamp, footer.

**Before-snapshot**:
The live page's content plus its version token, fetched immediately before a write. It is
both the generator's input and the one artifact that makes a bad publish a one-command
restore (ADR 0129).
_Avoid_: backup (suggests a separate copy nobody reads), cache, previous version.

**Publish record**:
The file written after a publish: version token before and after, the size change, the
probes checked, and the link-check result. It also names the page's **origin** — a
generator script, or a person — which decides how the next edit is made (ADRs 0129, 0130).
_Avoid_: changelog, publish log, release note (that is one of the five document types).

**Spine**:
The section list of one document type, chosen by the reader's question — "how do I do
this?" for a user manual, "what happens, in what order?" for a process page. Five spines
exist; three have never been through a real publish and are marked unproven (ADRs 0124,
0125).
_Avoid_: template (a template is filled in; a spine is chosen), skeleton, outline.

## read-picture terms (dev-workflows plugin)

**Picture record**:
One file per project, at the **git root of the repo you run in**, holding what has already
been read out of pictures — never in this marketplace repo, which ships to other people's
machines (ADR 0142). Its path resolves at runtime the same way `daily-state.md` does. Each
row is keyed by the image's **content hash** *and* the **Question kind** it answers, and
carries the source it was read from plus a flag when it could not be re-checked against
current bytes (ADRs 0136, 0139). It records only what its question asked, which is what
makes it safe to commit (ADR 0137).
_Avoid_: image ledger (one word from **Fact ledger**, and the two share no content —
the collision `naming-audit` exists to catch, ADR 0141), screenshot cache, image metadata.

**Question kind**:
The named half of a **Picture record** row's key — a small enumerated set (`on-screen-text`,
`requirement`, and siblings) that a caller picks from, adding its own detail underneath the
name. Free text was rejected because two skills needing the same answer phrase it
differently, so the second never gets a hit and nothing reports the miss (ADR 0138). `other`
is allowed and obliges the run to write the new kind back into the reference file, the way
`document-what-shipped` writes back a **Spine** its five did not cover.
_Avoid_: prompt, brief, query (all suggest free text — the point is that it is a set).

**read-picture**:
The Skill that opens a picture, extracts only the answer to the **Question kind** it was
handed, appends the row to the **Picture record**, and returns rows to its caller — a
*reader*, not a record format (ADR 0135). Dispatchable as a subagent, so the calling
conversation never holds the images. Unlike `document-what-shipped` it must stay
**model-invocable**: `disable-model-invocation: true` would make it slash-only and
therefore unloadable by another Skill (ADR 0141).
_Avoid_: image reader (too generic), OCR step (it answers a question, it does not
transcribe), vision tool.
