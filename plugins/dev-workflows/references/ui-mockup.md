# UI mockup-in-the-loop (a grilling aid)

A way to grill a UI decision by *showing* it, not describing it. Used from inside a
grilling session (grill-then-plan, grill-with-docs) — never a standalone step.

## When it applies

Only when a grilling question touches a UI surface the user pictures on a screen:
layout, where an element sits, what appears on screen at once, the flow between
states. Skip entirely for designs with no visual surface (data model, config, CLI,
backend pipeline). If a whole session raises no UI question, no mockup is ever made.

## Why show, not tell

Text agreement on UI is false agreement: you and the user both believe you
understand each other and picture different screens — because neither saw it. A
mockup is the disambiguation device. It makes "that's not what I meant" happen
*now*, while the decision is cheap to change, instead of after the feature is built.
A re-render is far cheaper than a mis-built feature, so never skip a render to save
cost.

## The rule — render when seeing would change the answer

Render or update the mockup when the open question can only be resolved by looking:

- where an element sits / the overall layout
- what appears on the screen at once
- the flow between screens or states

Do NOT render for what text already pins down — a label's exact words, a validation
rule, a copy tweak. The gate is "does seeing it change the answer?" — not a fixed
checkpoint, and not "render after every answer." Update the SAME artifact/file on
each later render; never spawn a new one per edit (hygiene, not a reason to render
less often).

## No design system? Establish one first — don't wireframe around it

A mockup is only as consistent as the design language behind it. If the project has
no design system, do NOT paper over the gap with ad-hoc or throwaway styling — every
mockup would drift, and so would the build. Surface it as a decision the user must
make: the project needs a design baseline before UI mockups mean anything.

Following grilling's own habit of always proposing a recommended answer, offer a
*minimal* starter — palette, type scale, spacing scale, a handful of base
components — so this never blocks the session; the user approves or edits it.
Persist the approved baseline as a file in the project (it is the consistency anchor
every later mockup reuses and the build inherits) and capture it as an ADR like any
other decision. Only once a baseline exists do you render.

## How to render

1. Gather the set of UI decisions resolved so far for this surface (not just the
   latest answer); the mockup reflects the whole accumulated set.
2. Use the project's design language so the mockup looks like the real app: existing
   CSS/theme, a component library, a Tailwind/token config, or a Figma design system
   (pull tokens via your harness's Figma mechanism if it has one). Found none → STOP
   and establish a baseline first (see above) — never fall back to ad-hoc styling.
3. Produce the artifact:
   - Harness can render artifacts (e.g. Claude Code) → create one.
   - It cannot → write a single self-contained `.html` (inline CSS/JS) to the
     working dir and give the user the path to open.
4. Ask it as a grilling question, with the mockup as your recommended answer: "Here's
   how I read the decisions so far as a screen — is this what you mean? Anything in
   the wrong place or missing?" If corrected → grill the point, update the same
   mockup, ask again. Loop until confirmed.

## Carry it to the spec

Reference the final mockup (artifact URL or `.html` path) in the design spec, so the
plan and the implementer see the same screen you confirmed — one source of truth, no
drift between words and picture.
