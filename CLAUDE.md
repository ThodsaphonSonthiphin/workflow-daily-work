# CLAUDE.md — workflow-daily-work

Orientation for an AI agent or new contributor working *in* this repo. For end-user
install/use, see [README.md](README.md). For deeper internals, see
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md). For term definitions, see
[CONTEXT.md](CONTEXT.md).

## What this is

A Claude Code **plugin marketplace** (`workflow-daily-work`). It ships five
**plugins**: `ado-backlog` (findings → Azure DevOps backlog, plus the assigned-work
view), `github-backlog` (the same pipeline against GitHub Issues), `dev-workflows`
(the daily-work arc: the `/daily` router plus design, debugging, review, study, and
communication skills), `react-workflows` (opt-in React conventions), and
`decision-map` (multi-session decision-ticket planning). [PLAYBOOK.md](PLAYBOOK.md)
maps the whole arc — when to reach for what.

## Repo layout

```
.claude-plugin/marketplace.json   the marketplace (lists the plugins)
CONTEXT.md                        glossary — domain + architecture terms
PLAYBOOK.md                       the daily-arc map — when to reach for what
README.md                         end-user overview + install
docs/
  ARCHITECTURE.md                 how it's built + how to extend
  superpowers/specs/              design specs
  superpowers/plans/              implementation plans
  adr/                            marketplace-level ADRs (daily arc, playbook, router)
plugins/ado-backlog/
  .claude-plugin/plugin.json      the plugin manifest
  skills/<name>/SKILL.md          one capability per pipeline step
  commands/<name>.md              thin /ado-backlog:<name> entry points
  scripts/                        executables the skills call (.cs/.py/.ps1)
  references/data-contracts.md    canonical JSON schemas (single source of truth)
  docs/adr/                       accepted design decisions (ADRs)
  examples/                       sample fixtures for testing
  README.md, QUICKSTART.md        user docs
plugins/github-backlog/           same pipeline, GitHub Issues backend
plugins/dev-workflows/            daily-work arc skills + the /daily router
  references/diagram-convention.md   canonical diagram convention (ADRs 0005-0009)
plugins/decision-map/             multi-session planning: chart-map + work-map skills
  scripts/map_core.py               rules both backends share — the marker invariant,
                                    region merge, input validation, the key join
  scripts/local_map_ops.py          local-markdown backend (default)
  scripts/github_map_ops.py         GitHub Issues backend (sub-issues + dependencies)
  scripts/fake_github.py            in-memory GitHub API, for the tests
  scripts/smoke_github_live.py      one live run — the byte-identical no-op check
  references/data-contracts.md      the ops contract both backends answer to
```

## Mental model

The plugin is a pipeline; each step is a skill; state flows through three JSON **data
contracts** joined by a stable `key`:

```
extract → triage (in-memory) → classify → create (dry-run gated) → write-back
  findings.json               → backlog_input.json → backlog_result.json
```

The orchestrator skill `findings-to-ado-backlog` sequences these steps and enforces the
safety gates; `ado-auth` is the optional pre-flight (Step 0) it delegates to before
extract. `my-work` (list assigned items) is a standalone query skill outside the
pipeline. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the step-by-step detail
and an add-a-skill recipe.

## Conventions (do not violate)

- **Skills** live in `plugins/<plugin>/skills/<name>/SKILL.md` with YAML frontmatter
  (`name` + a trigger-rich `description`). Reference bundled files via
  `${CLAUDE_PLUGIN_ROOT}` — never hard-code paths. For a skill's **own** files use a
  skill-relative path (`references/x.md`), not `${CLAUDE_PLUGIN_ROOT}/skills/<name>/…`.
- **Skills must stay harness-neutral (Claude Code + Antigravity).** Name *actions*,
  not one harness's tool/command (say "load the skill via your harness's mechanism",
  not "call the Skill tool"; give install commands for both harnesses). Use
  `${CLAUDE_PLUGIN_ROOT}` only in the three shapes the Antigravity installer rewrites —
  `/references/…`, `/scripts/…`, `/skills/…` (see
  `plugins/dev-workflows/.antigravity/`). A new shape means updating
  `install-antigravity.py`'s `rewrite_plugin_root()`.
- **Commands** are thin wrappers in `plugins/<plugin>/commands/<name>.md`
  (`description` + `argument-hint` frontmatter) that hand off to a skill via
  `$ARGUMENTS` and are invocable as `/<plugin>:<name>`. Logic lives in the skill, not the command.
- **Data-contract schemas are defined only** in
  `plugins/ado-backlog/references/data-contracts.md`. Never redefine them elsewhere.
- **Keep versions in sync:** each plugin's `.claude-plugin/plugin.json` and its entry
  in `.claude-plugin/marketplace.json` must always report the same version.
- **Every new skill adds one row to [PLAYBOOK.md](PLAYBOOK.md)** — the playbook is the
  discoverability map for the daily arc; a skill missing from it is invisible. Add the
  row in the same commit that adds the skill.
- **Document skills follow the diagram convention** — every skill-generated Markdown
  document opens with one overview Mermaid diagram; ADRs carry a small decision diagram.
  Canonical wording lives only in
  `plugins/dev-workflows/references/diagram-convention.md` (ADRs 0005–0009).
- **Minted counters come from the global max, never from your checkout** — ADR numbers
  *and* plugin/marketplace versions. Take the highest value across every ref and every
  worktree, then +1; `current + 1` from the tree you happen to be sitting in is how two
  parallel sessions mint the same value, and git merges both without conflict because
  only the number collides, not the filename ([ADR 0056](docs/adr/0056-adr-numbers-minted-from-global-max-across-branches-and-worktrees.md)).
  The runnable scan is the **Numbering** section of the grilling skills' `ADR-FORMAT.md`.
  In this repo all new ADRs go in the repo-root `docs/adr/`; the per-plugin `docs/adr/`
  directories are separate, older sequences. **A new ADR filename carries its
  sequence's short-name prefix** — `workflow-daily-work-` at the root, otherwise
  `ado-backlog-` / `dev-workflows-` / `github-backlog-` — and that prefix *is* the
  cross-repo citation (`ado-backlog-0002`); a bare `ADR 0092` is correct only inside
  this repo ([ADR 0093](docs/adr/workflow-daily-work-0093-adr-filenames-carry-the-owning-sequences-short-name.md)).
  Existing ADRs are **not** renamed, so every sequence is permanently mixed and the
  minting scan must stay prefix- and width-tolerant. Re-verify the number immediately
  before merging, not only when you create the file.
- **Every design decision gets its own ADR**, written as it lands, with one `|rejected|`
  branch per alternative that was genuinely on the table — there is no
  hard-to-reverse/surprising/trade-off gate to pass first
  ([ADR 0092](docs/adr/workflow-daily-work-0092-every-design-decision-gets-an-adr.md)).

- **A controller ruling during execution is a design decision and gets an ADR**, not
  just a ledger line. Rulings taken mid-run — dropping a verdict, changing a threshold,
  adding an exclusion — are exactly what ADR 0092 covers. Recording them only in the SDD
  ledger loses them when the workspace is deleted at finish, and leaves supersession
  banners with nothing to cite (2026-08-20: five such rulings became ADRs 0110–0114 only
  because an implementer noticed its banners could cite nothing).

- **The vendored `superpowers` copies are guarded by a checker, not by review.**
  `plugins/dev-workflows/scripts/check_vendored_superpowers.py` reports drift in the
  vendored copies and the frozen files against
  `plugins/dev-workflows/references/vendored-superpowers.json` — which is the authority on
  what those sets contain; the two overlap, so their sizes do not add. Run it with `--strict`
  before merging anything that touches `skills/sp-*` or `skills/scrutinize/`. Never glob
  `skills/sp-*` to find the copy set — `sp-grill-with-doc` wears the prefix and is not a
  copy. The procedure is `references/resync-superpowers.md` (ADRs 0075, 0085-0089).

- **A superseded design doc gets its banner in the same change that supersedes it.**
  Implementation routinely invalidates the spec or plan that seeded it — and the SDD
  flow generates each implementer's requirements *from the plan file*, so a stale plan
  ships wrong requirements silently. When a decision changes what a spec, plan or ADR
  describes, add a supersession banner at the top of that document (what it says vs
  what is now true, and the ADR that changed it) in the same commit. Worked examples:
  `docs/superpowers/specs/2026-07-31-decision-map-design.md`, ADRs 0033/0035/0037.

- **The SDD pre-flight scan must evaluate the plan's arithmetic, not just read it.** A
  scan that checks cross-task interfaces and per-task self-agreement as prose cannot see
  that a constant contradicts a fixture the same plan asserts on. Compute what each
  fixture actually produces and compare it against the assertion beside it — a plan can
  be perfectly consistent in wording and still be unimplementable (2026-08-20:
  `PROVENANCE_MIN = 0.60` against a fixture measuring 0.6667 that the plan required to
  grade `UNRELATED`; the scan passed it, and an implementer found it mid-transcription).

## Key commands

Run these from a shell at the repo root (repo-relative paths). Inside a skill's
SKILL.md, reference scripts via `${CLAUDE_PLUGIN_ROOT}/scripts/<name>` instead.

```powershell
# Verify prerequisites (az login, .NET >= 10, Python + openpyxl, org/project)
powershell -ExecutionPolicy Bypass -File "plugins/ado-backlog/scripts/setup_check.ps1"

# Dry run — validates against ADO, creates nothing (this is the DEFAULT)
dotnet run "plugins/ado-backlog/scripts/create-backlog.cs" -- "<workdir>/backlog_input.json"

# Real run — only after explicit user approval of the dry-run result
$env:AZDO_DRY_RUN = "false"
dotnet run "plugins/ado-backlog/scripts/create-backlog.cs" -- "<workdir>/backlog_input.json"
```

```bash
# Check the vendored superpowers copies (report-only; --strict to gate)
python plugins/dev-workflows/scripts/check_vendored_superpowers.py --strict
```

Run scripts by type: `.cs` → `dotnet run` (file-based app, .NET 10), `.py` → `python`,
`.ps1` → `powershell -ExecutionPolicy Bypass -File`.

## Environment & gotchas

- **Windows + PowerShell.** Use PowerShell syntax (`$env:VAR`, not `$VAR`).
- **cp1252 console trap:** don't open spreadsheets blind — dump them to UTF-8 first with
  `read_source.py`, then read the dump.
- **ADO auth** defaults to an Entra token
  (`az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798`); an
  `AZDO_PAT` env var is the fallback. See the `ado-auth` skill.
- **`AZDO_ORG` / `AZDO_PROJECT` are bare names** (e.g. `Cartagena365`, `GlassHull`), not
  URLs and not the Azure subscription/tenant. See [CONTEXT.md](CONTEXT.md).

## Safety gates (non-negotiable)

1. **Never create in ADO before a passing dry-run.**
2. **Never create without explicit user approval** of the validated list.
3. **Back up the source spreadsheet before write-back** (it edits the file in place).

The `findings-to-ado-backlog` orchestrator owns the canonical wording of these gates.

## Pointers

- [CONTEXT.md](CONTEXT.md) — glossary (Organization, Project, Skill, Orchestrator, …)
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — internals + add-a-skill recipe
- [docs/adr/](docs/adr/) — marketplace-level design decisions (daily-arc/playbook/router ADRs 0001–0004, 0011)
- [plugins/ado-backlog/docs/adr/](plugins/ado-backlog/docs/adr/) — accepted design decisions (ADRs)
- [plugins/ado-backlog/README.md](plugins/ado-backlog/README.md) /
  [QUICKSTART.md](plugins/ado-backlog/QUICKSTART.md) — user docs
