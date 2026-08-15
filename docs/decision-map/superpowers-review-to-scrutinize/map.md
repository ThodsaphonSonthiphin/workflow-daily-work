# Decision map - route every superpowers review step to scrutinize

```mermaid
graph TD
    MAP["map (this file)"] --> T["tickets/*.md — one decision each"]
    T --> D["Decisions so far (index below)"]
```

## Destination
The superpowers skills that carry a review step are copied into this repo, with all seven review touchpoints routed to the existing scrutinize skill, running in both Claude Code and Antigravity, and with a documented path to resync the copies from upstream.

## Notes
Constraints fixed at chart time: scrutinize is FROZEN - the copies adapt to it as-is, its behaviour and output format do not change. Upstream is obra/superpowers, MIT (c) 2025 Jesse Vincent, vendored from sha b36e0829c6d0 (byte-identical to the 6.3.0 cache dir); the live plugin is a url-source clone, so editing the plugin cache is never the mechanism. Closure is 21 files - 2407 Markdown lines plus 1559 non-Markdown - copied verbatim over six skill dirs, then one rewrite pass (ADR 0074). CORRECTED 2026-08-14: only FOUR reviewer dispatches exist, driven by THREE prompt files inside requesting-code-review and subagent-driven-development; touchpoints #1 and #2 name files nothing references (the live step is an inline self-review checklist), #6 dispatches nothing, and #7 has the agent review the plan itself. The other four skills are copied for their qualified handoffs, not for a review step of their own. Distribution scope is this repo plus Antigravity only. Repo conventions apply to whatever ships: one PLAYBOOK.md row per skill, the diagram convention, versions and ADR numbers minted from the global max. NARROWED 2026-08-14 (ADR 0077): the diagram convention does NOT reach the six vendored copies or the documents they generate - it still binds this repo's own skills, ADRs and ticket resolutions; the three WIRING conventions (plugin-root path, frontmatter, harness-neutral wording) do bind, at zero new resync cost, and each copy gets a PLAYBOOK row in one new grouped section. Grilling tickets: load sp-grill-with-doc. The seven charted touchpoints, with what each was measured to be (ADR 0074): 1 brainstorming/spec-document-reviewer-prompt.md (DEAD FILE), 2 writing-plans/plan-document-reviewer-prompt.md (DEAD FILE), 3 requesting-code-review (SKILL.md + code-reviewer.md), 4 subagent-driven-development/task-reviewer-prompt.md, 5 subagent-driven-development/re-review-prompt.md, 6 receiving-code-review/SKILL.md, 7 executing-plans/SKILL.md. CONSTRAINT ADDED 2026-08-14 by the owner: scrutinize is NEVER edited - if a change to it is genuinely required, the change goes into a NEW Skill that is a copy of it, and taking that option changes the destination line rather than resolving a ticket under it (ADR 0076).

## Decisions so far

<!-- decision-map:decisions:start -->
- [Ripple - which existing daily-arc handoffs get repointed at the copies?](tickets/arc-rewiring.md) — All 11 refs - one skill, 4 files - become short-form sp-writing-plans; grill-then-plan Step 0 retargets to it; PLAYBOOK and the daily router need no change, they never named superpowers.
- [Attribution - how is the MIT notice carried on vendored files?](tickets/attribution.md) — Upstream MIT ships verbatim in dev-workflows/LICENSE-superpowers with the sha and a MODIFIED marker, never per-file; the repo also gained the top-level LICENSE it never had.
- [Mechanism - with per-skill disable impossible, does the plugin go fully off or stay fully on?](tickets/coexistence-mechanism.md) — Plugin stays FULLY on; this marketplace ships its OWN SessionStart hook that re-points the one skill the upstream hook names - measured 3/3 against a 2/2 control, not assumed.
- [Coexistence - does the superpowers plugin stay enabled alongside the copies?](tickets/coexistence.md) — Plugin stays enabled; the six review-carrying originals go off via skillOverrides - the other eight skills stay live and the copies' outbound refs keep resolving.
- [Conventions - how far must vendored copies obey this repo's skill conventions?](tickets/convention-compliance.md) — Three wiring conventions bind at zero new cost - already ADR 0074 edits, or already satisfied; the Mermaid rule does not reach the copies' output; PLAYBOOK gains six rows.
- [Granularity - whole skill directories, or just the reviewer prompt files with shims?](tickets/copy-granularity.md) — All 21 files copied verbatim plus one rewrite pass; shims are impossible - a reviewer prompt is a RELATIVE link inside the SKILL.md, so only a copied SKILL.md can redirect a dispatch.
- [Harness behaviour - how does Claude Code resolve two skills with the same name from different plugins?](tickets/harness-skill-shadowing.md) — Both load - no collision, since plugin skills are namespaced plugin:skill; skillOverrides switches off one skill without disabling its plugin.
- [Host plugin - do the copies live in dev-workflows or a new plugin of their own?](tickets/host-plugin.md) — The six copies live in plugins/dev-workflows - no sixth plugin: the destination needs Antigravity and its only installer is plugin-local, and ADR 0070's hook must ship beside them.
- [receiving-code-review - it dispatches nothing, so what does the copy actually change?](tickets/receiving-code-review-role.md) — Copied verbatim - the set stays six, justified by set completeness and the 1:1 upstream mapping, not a review step; ADR 0076 leaves nothing to retune, class 4 absorbs the unmeasured ref fact.
- [Resync - what is the documented procedure for pulling upstream changes into the copies?](tickets/resync-path.md) — Resync is a checker script that reports and changes nothing, driven by ONE recorded sha plus a 21-file manifest; a person applies the 9 files edits and the exit code says done.
- [Acceptance check - what observable signal proves a dispatched review actually ran scrutinize?](tickets/review-acceptance-check.md) — The proof is the subagent's own Skill tool_use naming dev-workflows:scrutinize - harness-written so unfakeable; toolStats cannot see it and it never persists, so the check is a run not a gate.
- [Invocation - how does a dispatched reviewer subagent run a frozen, human-facing scrutinize?](tickets/reviewer-invocation.md) — The prompt file stays the HARNESS - context in, output contract out - and delegates only the review method to the frozen scrutinize, translating blocker/major/nit to Critical/Important/Minor.
- [Live check - does a bare sp- reference actually resolve to the plugin skill, on both harnesses?](tickets/short-ref-resolution.md) — Short form DOES resolve - the model self-qualifies to dev-workflows:sp-*; but with the copy ABSENT it silently launches the upstream twin instead of failing. Subagents DO inherit effort: max.
- [Naming - what are the copied skills called, and what do their descriptions trigger on?](tickets/skill-naming.md) — The six copies take the sp- prefix, reference each other by short name (the eight non-copied stay superpowers:*), and each description names the upstream skill it displaces.
- [Live check - does a plugin-qualified skillOverrides key work, and what does the hook do when its skill is off?](tickets/skilloverrides-live-check.md) — Observed on CC 2.1.232: skillOverrides cannot reach a PLUGIN skill by EITHER key form - only whole-plugin disable works, and the hook injects a file so no override touches it.
<!-- decision-map:decisions:end -->

## Not yet specified

<!-- decision-map:fog:start -->
- Whether subagent-driven-development/scripts/review-package needs to change, and what it assumes about the reviewer it packages for.
- Whether Claude Code's /skills picker will show an override on a plugin skill as applied while enforcement ignores it - the listing UI computes the override without the plugin exemption the enforcement resolver applies, which would make any future per-skill claim about a plugin untrustworthy unless it is checked live.
- Whether the commit-log PostToolUse hook (ADR 0054) is being retired - the working tree has emptied plugins/dev-workflows/hooks/hooks.json, which is the same file ADR 0073 puts ADR 0070's SessionStart hook in.
- Nothing notices that upstream moved - ADR 0075 makes resync on-demand with no trigger, and this repo has no CI to hold one, so a new superpowers version can sit unpulled indefinitely.
- Nothing notices a routing failure during ordinary use - ADR 0079 measured that the dispatched subagent's Skill record never reaches the session log, so a review that quietly ran the built-in reviewer leaves no trace anyone can find afterwards, and the only proof is a probe arranged in advance.
- Whether a routed review's Critical finding actually fires the controller's fix loop at subagent-driven-development/SKILL.md:356 - ADR 0075's checker asserts the three translation rows are PRESENT in the prompt files, and ADR 0079's probe stops at the reviewer loading scrutinize; neither watches the gate itself fire.
<!-- decision-map:fog:end -->

## Out of scope

<!-- decision-map:scope:start -->
- Syncing the vendored skill copies tracked under menunest's .agents/ directory.
- The dev-playbook distribution at ~/Downloads/custom-skill - the active PAT cannot push to it.
- The separate superpowers copies under .gemini/extensions and .codex/plugins.
- Changing scrutinize's own behaviour, stance or output format - it is frozen by decision.
- Contributing any of this back upstream to obra/superpowers.
- Copying or replacing the eight superpowers skills that carry no review step - the coexistence decision keeps them live from the upstream plugin, and two of them (using-git-worktrees, finishing-a-development-branch) are load-bearing for the copies.
- Repointing references to superpowers skills that carry NO review touchpoint - problem-description's systematic-debugging pointer is an editorial call about this repo's own debug-mantra, not part of the review-to-scrutinize swap (ADR 0072).
- Retuning sp-receiving-code-review's content for scrutinize-shaped findings - ADR 0076's translation emits upstream's Critical/Important/Minor, so the copy has nothing to adapt to (ADR 0078).
<!-- decision-map:scope:end -->
