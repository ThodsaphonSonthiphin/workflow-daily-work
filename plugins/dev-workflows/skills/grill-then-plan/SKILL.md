---
name: grill-then-plan
description: Like grill-with-docs (domain-aware grilling, glossary sharpening, inline CONTEXT.md/ADR capture) BUT continues into the superpowers planning pipeline by handing off to superpowers:writing-plans at the end. Use ONLY when the user wants both the grilling AND a written implementation plan produced afterward; if they want grilling/docs alone, use grill-with-docs instead. Requires the superpowers plugin.
---

<what-to-do>

Run a domain-aware design session, then hand off to the superpowers planning
pipeline. Do NOT write code, scaffold, or invoke any implementation skill until
the design spec is approved and you have invoked `superpowers:writing-plans`.

</what-to-do>

## Step 0 — Preflight: ensure superpowers is installed

This skill delegates its final step to `superpowers:writing-plans`. Check that
dependency FIRST, so the user never spends a whole session only to hit a wall at
handoff.

1. **Detect** superpowers. Read `~/.claude/plugins/installed_plugins.json` and
   look for the key `superpowers@claude-plugins-official`. As a fallback, check
   for a directory matching
   `~/.claude/plugins/cache/claude-plugins-official/superpowers/*/`.
2. **If present** → continue to Step 1.
3. **If missing** → tell the user superpowers is required, then offer to install
   it:
   - Confirm the marketplace is registered: run `/plugin marketplace list` and
     look for `claude-plugins-official`. If it is absent, add it with
     `/plugin marketplace add anthropics/claude-plugins-official`.
   - `/plugin install superpowers@claude-plugins-official`
4. **Wait for the user to confirm the install completed**, then re-verify using
   the detection in (1). Plugin installation runs through the interactive
   `/plugin` UI and is not instantaneous — do NOT re-verify in the same turn you
   issued the install, or you will read stale state and wrongly conclude it
   failed. Ask the user to confirm (or to re-run this skill) first.
5. **If now present** → continue to Step 1.
6. **If still missing or the install could not complete** → STOP. Do not start
   grilling. Tell the user explicitly:

   > superpowers could not be installed; the grill-then-plan handoff to
   > `superpowers:writing-plans` can't run without it. Please install it manually
   > with `/plugin install superpowers@claude-plugins-official`, then re-run.

   Never fail silently and never start a session you cannot finish.

## Step 1 — Explore context

Read the codebase, recent commits, and existing docs: `CONTEXT.md` /
`CONTEXT-MAP.md` at the repo root, and `docs/adr/`. If a `CONTEXT-MAP.md` exists,
the repo has multiple contexts — infer which one the topic relates to (ask if
unclear).

## Step 2 — Grill relentlessly, one question at a time

Interview the user about every aspect of the plan until you reach shared
understanding. Walk down each branch of the design tree, resolving dependencies
between decisions one-by-one. For each question, provide your recommended answer.
Ask one question at a time and wait for feedback before continuing. If a question
can be answered by exploring the codebase, explore the codebase instead of asking.

## Step 3 — Stay domain-aware while grilling

- **Challenge against the glossary.** If a term conflicts with `CONTEXT.md`, call
  it out: "Your glossary defines X as A, but you seem to mean B — which is it?"
- **Sharpen fuzzy language.** Propose a precise canonical term for vague or
  overloaded words: "You're saying 'account' — Customer or User?"
- **Discuss concrete scenarios.** Invent edge-case scenarios that force precision
  about boundaries between concepts.
- **Cross-reference with code.** When the user states how something works, check
  the code agrees; surface any contradiction.

## Step 4 — Capture inline as decisions crystallize

- **Update CONTEXT.md inline** the moment a term resolves — don't batch. Keep it
  a glossary only; no implementation detail. Create it lazily on the first
  resolved term if it doesn't exist. Use the format in
  [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).
- **Always create an ADR for every design decision** — one ADR per decision, the
  moment the decision is made. Do not batch or defer. Create `docs/adr/` lazily
  on the first ADR. Use the format in [ADR-FORMAT.md](./ADR-FORMAT.md). Every
  ADR opens with a small Mermaid decision diagram (chosen vs rejected paths) —
  see `${CLAUDE_PLUGIN_ROOT}/references/diagram-convention.md`. A
  decision qualifies if the user chose one option over another — architectural
  shape, technology choice, naming, scope boundary, safety mechanism. When in
  doubt, write the ADR. A short ADR is better than a missing one.

## Step 5 — Write the design spec

Once understanding is shared, write the design to
`docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md` (`<topic>` is a
lowercase-kebab slug). The spec is a Markdown document — follow the diagram
convention in `${CLAUDE_PLUGIN_ROOT}/references/diagram-convention.md` (one
overview Mermaid diagram at the top; type-matched diagrams per section).
Run a self-review for placeholders, internal consistency,
scope, and ambiguity; fix inline. Ask the user to review the spec and approve
before proceeding. If they do NOT approve, return to Step 2 and grill on the
disputed points, then revise the spec — do not proceed to handoff until approved.

## Step 6 — Hand off

After the user approves the spec, invoke `superpowers:writing-plans` to produce
the implementation plan. This is the terminal state — do NOT invoke any other
implementation skill.
