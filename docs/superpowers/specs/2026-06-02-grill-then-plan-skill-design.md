# grill-then-plan — Design

## Purpose

A domain-aware front-end to the superpowers pipeline. It grills the user one
question at a time (the grill-with-docs interrogation style), keeps the glossary
and decisions honest against the actual code, captures `CONTEXT.md` + ADRs inline
as decisions crystallize, writes a short design spec, then hands off to
`superpowers:writing-plans`.

It combines two things the user already likes:

- **superpowers** — the gated pipeline (`brainstorming → writing-plans →
  executing-plans`) with a hard gate that blocks implementation before an
  approved design.
- **grill-with-docs** — relentless, domain-aware, one-question-at-a-time grilling
  that challenges wording against a glossary, cross-references claims against
  code, and records hard decisions as ADRs inline.

The combined skill bolts grill-with-docs' interrogation + docs behavior onto the
front of the superpowers spine, preserving the hard gate.

## Location

`~/.claude/skills/grill-then-plan/` — the user's own skills directory, so it
survives plugin updates.

## Files

| File | Origin | Notes |
|---|---|---|
| `SKILL.md` | New (owned) | ~40-50 lines describing the pipeline below |
| `ADR-FORMAT.md` | **Vendored copy** from grill-with-docs | Frozen; can't be changed by upstream edits |
| `CONTEXT-FORMAT.md` | **Vendored copy** from grill-with-docs | Frozen; can't be changed by upstream edits |

## Coupling model (the hybrid)

- **Delegate superpowers by name.** The back half (`→ superpowers:writing-plans`)
  is a plain skill invocation. Any superpowers version bump is picked up
  automatically; never copy superpowers content. Zero maintenance from
  superpowers updates.
- **Vendor the grill behavior.** The grilling instructions and the two format
  files are copied in. This is the behavior the user wants frozen, so
  grill-with-docs can evolve independently without surprising this skill.

Net effect:
- superpowers updates → this skill transparently benefits, nothing to do.
- grill-with-docs updates → this skill is unaffected (own copy); re-sync only by
  explicit choice.
- The only maintained surface is the owned `SKILL.md`.

## Pipeline

The terminal state is invoking `superpowers:writing-plans`. No implementation,
code, or scaffolding happens before the design spec is approved (hard gate
inherited from superpowers brainstorming discipline).

### Step 0 — Preflight dependency check (before any grilling)

superpowers is a hard dependency because the skill delegates to
`superpowers:writing-plans` at the end. Checking up front means the user does not
spend a whole grilling session only to hit a wall at the handoff. Fail fast, fail
loud.

1. **Detect superpowers** — check `installed_plugins.json` for
   `superpowers@claude-plugins-official`, and/or the cache dir
   `.../plugins/cache/claude-plugins-official/superpowers/<version>/`.
2. **If present** → proceed to Step 1.
3. **If missing** → tell the user superpowers is required, then offer to install:
   - `/plugin marketplace add anthropics/claude-plugins-official` (only if the
     marketplace is not already known)
   - `/plugin install superpowers@claude-plugins-official`
4. **Re-verify** after the attempt.
5. **If it succeeded** → continue to Step 1.
6. **If it failed or could not be done automatically** → **STOP the pipeline**
   and tell the user explicitly:

   > "superpowers could not be installed; the grill-then-plan handoff to
   > `superpowers:writing-plans` can't run without it. Please install it manually
   > with the command above, then re-run."

   No silent failure, no half-finished pipeline.

**Honesty constraint:** a skill is instructions Claude follows. Plugin
installation normally goes through the interactive `/plugin` flow and may require
the user to confirm in the UI, so a fully silent auto-install cannot be
guaranteed. The skill detects, attempts/guides, and re-verifies — and the
non-negotiable requirement is that it never fails silently.

### Step 1 — Explore context

Codebase, recent commits, and existing docs: `CONTEXT.md` / `CONTEXT-MAP.md`,
`docs/adr/`.

### Step 2 — Grill relentlessly, one question at a time

Walk the design tree, resolving dependencies between decisions one-by-one. Give a
recommended answer for each question. If a question is answerable from the code,
read the code instead of asking. Wait for feedback on each question before
continuing.

### Step 3 — Stay domain-aware while grilling

- Challenge terms that conflict with the glossary in `CONTEXT.md`.
- Sharpen fuzzy/overloaded words to a precise canonical term.
- Stress-test domain relationships with concrete scenarios that probe edge cases.
- Cross-reference stated behavior against the code; surface contradictions.

### Step 4 — Capture inline as decisions crystallize

- Update `CONTEXT.md` the moment a term resolves (glossary only — no
  implementation detail), per the vendored `CONTEXT-FORMAT.md`.
- Offer an ADR only when all three hold: hard to reverse · surprising without
  context · the result of a real trade-off. Use the vendored `ADR-FORMAT.md`.
- Single- vs multi-context repos are handled per `CONTEXT-FORMAT.md`
  (`CONTEXT-MAP.md` at root → multi-context).

### Step 5 — Write the design spec

Once understanding is shared, write
`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`, run the spec self-review
(placeholders, internal consistency, scope, ambiguity), and get the user's
approval.

### Step 6 — Hand off

Invoke `superpowers:writing-plans` (delegated by name → always the current
version) to produce the implementation plan.

## Artifacts produced

- `CONTEXT.md` (and/or `CONTEXT-MAP.md`) — durable glossary, updated inline.
- ADRs under `docs/adr/` — created sparingly, inline.
- A design spec under `docs/superpowers/specs/` — feeds `writing-plans`.

## Out of scope (YAGNI)

- Auto-running implementation skills other than `superpowers:writing-plans`.
- Modifying or forking superpowers content.
- Guaranteeing a fully silent plugin install (not reliably possible; detect +
  attempt + loud failure instead).
