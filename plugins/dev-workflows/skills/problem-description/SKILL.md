---
name: problem-description
description: Use when the user wants an interactive step-by-step HTML walkthrough explaining a complex technical problem (DB error, race condition, design issue, conceptual blocker) using concrete data and manual navigation. Triggers on phrases like "make me a walkthrough", "explain step by step with data", "interactive explanation", "make an animation", "walk me through with real examples", "อธิบายแบบ step by step", "ทำ animation/walkthrough/visualization", "ทำเป็น diagram", "วาด diagram". Do NOT use for one-line clarifications, conceptual Q&A answerable in a paragraph, or simple "what does X mean" questions — only when an interactive HTML artifact would clearly help.
---

# Problem Description — Interactive Step-by-Step Walkthroughs

## Overview

Generate a self-contained HTML page that explains a technical problem using:

- **Concrete data** — real names, real numbers, culturally appropriate context (e.g., Thai names for Thai users)
- **Manual step-through navigation** — `Next →`, `← Previous`, `↻ Reset` buttons. Reader controls pace.
- **Visual state changes** — at each step, the right thing highlights and the reader can point at it
- **Color-coded narration** — info / warn / error / success / magic boxes explaining what fires + WHY

**Core principle:** The reader should be able to point to any specific element at each step and say *"yes I understand why this is in this state right now."*

## Two Visualization Modes

This skill has **two modes**. Pick the right one for the problem.

### Mode A — DIAGRAM (default for most problems)

Boxes positioned spatially with arrows showing data flow between them. At each step, certain boxes light up and certain arrows fire, with "flying" labels showing the values being passed.

**Use this when** the problem is about:
- Architecture / data flow between components
- Process steps where a value moves A → B → C → D
- Concurrency, locking, message passing
- Workflow + sub-component interaction (the actual code path)
- Anything where "what's connected to what" matters more than "what row changed"

**Canonical reference:** `c:/Repo/glasshull repo/glasshull/docs/2026-05-28-polaris-booking-number-diagram.html` — 22-step explanation of Polaris's classic-workflow + CodeActivity + counter-entity architecture, including a 3-transaction concurrency demo.

**Template:** `skills/problem-description/template-diagram.html`

### Mode B — TABLES (for row-state problems)

Database tables rendered as styled HTML tables. At each step, specific rows highlight, badges (DELETE / SET NULL / CONFLICT) appear, fixed rows turn green, deleted rows go gray.

**Use this when** the problem is about:
- Rows in tables changing state due to FK rules, cascades, triggers
- Same table re-visited with different highlights to show conflicts
- Cardinality / relationship-driven scenarios

**Canonical reference:** `c:/Repo2/t/cascade-paths-explained.html` — 7-step SQL Server error 1785 walkthrough using "ครอบครัวสมศรี" budget data.

**Template:** `skills/problem-description/template.html`

### How to choose

> If you're explaining **"what happens to row X"** → Mode B (tables).
> If you're explaining **"what flows from A to B to C"** → Mode A (diagram).

When in doubt: **Mode A (diagram) is the better default** — most technical problems involve component interaction, and the diagram view scales to concurrency and message-passing scenarios that tables can't show cleanly.

## When to Use This Skill

- User wants an interactive walkthrough of a non-trivial technical problem
- Verbal/text explanation has failed and the user is still confused
- The problem involves multiple components or entities + a chain of cause-and-effect
- The "aha moment" hinges on seeing data move through the system
- Teaching a concept where the reader benefits from controlling pace

**Don't use when:**

- The answer fits in 1-3 sentences
- It's a "what does X mean?" definition question
- It's a simple bug fix where understanding is trivial
- The user wants to read code (use `drive-to-legacy` instead)
- The user wants a polished UI/component (use `frontend-design` instead)
- The user wants to *find* the bug, not *teach* it (use `superpowers:systematic-debugging` instead)

## The Process — 6 Phases

### Phase 0 — Confirm the artifact is wanted

Before generating ~500 lines of HTML, ask:

> "อยากได้ interactive step-by-step walkthrough (HTML page เปิดในเบราว์เซอร์), หรือคำตอบสั้นๆ พอ?"

**Skip Phase 0** if the user explicitly asked for "walkthrough", "animation", "visualization", "step by step", "ทำ animation", "diagram", "interactive", or similar artifact-shape language.

### Phase 1 — Identify the core misunderstanding AND pick the mode

Articulate three things in one sentence each:

1. **The ONE concept** the reader should grasp by the end (e.g., "the UPDATE-on-ctg_name trick is what acquires the row-level write lock")
2. **The misunderstanding** they have now (e.g., "they think the workflow and the counter entity are two unrelated things")
3. **The prerequisites** they already have (e.g., "they know Dataverse entities and that workflows trigger on Create")

Then pick the mode using the "How to choose" rule above. Tell the user which mode you're using in your first message.

If you can't articulate (1) and (2) in one sentence each, **ask the user before continuing**. Vague misunderstandings produce vague walkthroughs.

### Phase 2 — Choose concrete data

Replace abstract entities with realistic, culturally appropriate data.

**Data Quality Checklist:**

- [ ] ≤ 4 entities (boxes or tables) of any one kind — more is noise
- [ ] Names read aloud naturally ("BMW Group", "ครอบครัวสมศรี" not "Customer A", "Family A")
- [ ] Numbers small enough to mental-math (`5`, `42`, `80฿` — not `47,392.18฿`)
- [ ] **Identifiers must not look like sequence numbers** — if a sequence appears in the output (e.g., booking numbers 00001, 00002), avoid IDs like `cargo-1`/`cargo-2` that the reader will confuse for those. Prefer letter IDs (`cargo-A`, `cargo-B`) or source-tagged labels (`cargo (Portal)`).
- [ ] At least one element participates in EVERY problematic path — so when the conflict step lights up, it's visually obvious on one element
- [ ] Schema names match the user's actual codebase (`ctg_runningnumber`, `BudgetTransactions` — not `Counter`, `Table1`)
- [ ] Cultural fit — default to Thai narration for Thai users; technical terms (workflow, CodeActivity, EntityReference, transaction) stay in English

**Bad → Good examples:**

| Bad | Good |
|---|---|
| `Entity A` references `Entity B` | `BMW Group` owns `cargo-A` |
| `cargo-1, cargo-2, cargo-3` (collides with booking #1, #2, #3) | `cargo-A, cargo-B, cargo-C` or `cargo (Portal)`, `cargo (CIT)` |
| `Table1`, `Table2` | `ctg_runningnumber`, `ctg_cargodetail` (real schema names) |
| `value1=100` | `accountnumber="BMW"` |

### Phase 3 — Sequence the steps

Build a domino chain. Each step adds **one** new piece of state.

**Standard skeleton (diagram mode):**

| Step | Purpose |
|---|---|
| **0** | Overview — show all components + arrows in idle state. No action. Reader builds mental model. |
| **1** | Trigger — what initiates the flow? (Light up the triggering component.) |
| **2..N** | Single-actor flow — ONE component activates per step, ONE arrow fires per step, ONE value shown flying along it. State accumulates visibly. |
| **N+1** | **The key question** (REQUIRED) — pose a question the reader must answer in their head before the concurrent / failure scenario reveals the answer. |
| **N+2..M** | Concurrent / failure scenario — show 2-3 actors racing, blocking, or conflicting. |
| **M+1** | Counter-example — what would go wrong with the naive approach (e.g., "what if we used MAX()+1?"). |
| **M+2** | Summary / resolution — why the architecture works AND its trade-offs / side-effects. |

**Standard skeleton (tables mode):**

| Step | Purpose |
|---|---|
| **0** | Setup — show all tables + all rules. No action. |
| **1** | Trigger — user action starts the chain. |
| **2..N** | Domino effects — ONE rule fires per step, affecting specific named rows. |
| **N+1** | Key question. |
| **N+2** | Conflict / failure step. |
| **N+3** | Resolution with side-effects named. |

Each step has:

- **Scene title** — imperative, ≤ 12 words ("Step 8 — 🔒 AcquireWriteLock: UPDATE ctg_name forces row X-lock")
- **Narration** — 2-5 sentences answering WHY (not just WHAT). Why does this fire? Why is the value chosen? Why does this matter to the reader?
- **Visual change** — light up the active component/row, fire the active arrow, show the flying-value label, highlight the active rule

### Phase 4 — Generate the HTML

**Mode A (diagram):** Read `skills/problem-description/template-diagram.html`. The template ships with a 3-step demo (Client → Server → DB) so you can verify the scaffold works in a browser before adapting it.

Adapt these insertion zones:
1. **SVG component groups** — one `<g class="comp">` per component, positioned absolutely in the SVG coordinate space
2. **SVG arrows** — `<path class="arrow">` between component anchor points
3. **Flow labels** — `<g class="flow-label-group">` for data flying along arrows
4. **`COMPONENTS`, `ARROWS`, `LABELS` arrays** — every id used in scenes (drives `clearAllStates()`)
5. **Scenes JS array** — one function per step, fully describing DOM state
6. **Extra panels** — `questionPanel`, `racePanel`, `summaryPanel` (declared once, shown by scenes)

**Mode B (tables):** Read `skills/problem-description/template.html`. Adapt the table grid, rules panel, `ID_LIST`, scenes, and `keyQuestion` panel.

**Critical rule** (both modes): every scene must fully describe DOM state from scratch. Never `appendChild` from a scene. All optional panels (key-question, race demo, summary) declared upfront with `class="hidden"`, toggled per scene via `show()`/`hide()`.

### Phase 4.5 — Save and report

Default save path:

- **For a specific project:** `<workspace-root>/docs/YYYY-MM-DD-<topic>-walkthrough.html` (diagram mode) or `<workspace-root>/docs/<topic>-explained.html` (tables mode)
- **For ad-hoc explanations on this user's machine:** `c:/Repo2/t/<topic>-walkthrough.html`
- **If the user specified a path:** use it

Report back:
- The absolute path of the generated file
- Which mode (diagram or tables)
- How many steps
- "Open in your browser — `ถัดไป →` / `← ย้อนกลับ` / `↻ เริ่มใหม่` ปุ่มควบคุม pace"

### Phase 5 — Verify before declaring done

Run the self-test checklist:

- [ ] Every step's narration answers WHY, not just WHAT
- [ ] The "key question" step exists and forces reader thinking
- [ ] The resolution / summary step explicitly names side-effects and trade-offs
- [ ] `scenes.length - 1 === TOTAL` in JS (step 0 is included; TOTAL is the index of the last step)
- [ ] Every `getElementById(id)` call has a matching `id` attribute in the HTML
- [ ] `COMPONENTS` / `ARROWS` / `LABELS` (diagram mode) or `ID_LIST` (tables mode) contains every id used in scenes
- [ ] Going `← Previous` from any step returns clean state (idempotent scene rule)
- [ ] `↻ Reset` returns to step 0 with no residual highlights, badges, or visible panels
- [ ] No `appendChild` / `createElement` inside any scene function
- [ ] **No identifier collision:** sequence numbers in the output don't conflict with element IDs (e.g., don't use `cargo-1` when booking numbers `00001` will appear)

If any item fails — fix before reporting done.

## Diagram Mode — Design Decisions

The diagram template encodes proven choices:

**Color tokens** (don't change — proven for readability):

- `#5fb4ff` — info / accent / active (blue)
- `#ffd479` — firing / value-in-flight (amber)
- `#b070ff` — locked / magic / "this is the key step" (purple)
- `#ffaa00` — blocked / warn (orange)
- `#4ade80` — done / success (green)
- `#ff5757` — error / conflict (red)
- `#0a0e14` — background, `#1a2330` — panel background

**Component states** (set via `setComp(id, state)`):

- `''` — idle (default gray border, dim text)
- `active` — lit cyan, current focus
- `firing` — pulsing amber, just got triggered
- `locked` — purple with glow, holds an exclusive lock
- `blocked` — orange, dimmed, blinking — waiting on someone else
- `done` — green, completed
- `error` — red glow
- `dimmed` — 35% opacity, fades into background

**Arrow states** (set via `setArrow(id, state)`):

- `''` — idle gray
- `active` — bright cyan with dashed flow animation
- `magic` — purple, "the special arrow" (lock acquisition, etc.)
- `done` — green, traversed
- `error` — red

**Flow labels** (set via `setLabel(id, show, variant)`) — pre-positioned along each arrow's midpoint, toggled per scene. Variant `'magic'` or `'error'` recolors for those states.

## Tables Mode — Design Decisions

(Inherited from the original tables template — unchanged.)

**State classes** on row elements: `.target-delete`, `.target-setnull`, `.target-conflict`, `.fixed`, `.deleted`.

**Badge classes**: `.badge.delete`, `.badge.setnull`, `.badge.conflict`.

**Single source of truth for rows:**

```js
const ID_LIST = ['F1', 'C1', 'C2', 'A1', 'T1', 'T2', 'T3'];
```

`clearAllStates()` iterates this list to reset rows + badges.

## Idempotent Scenes — The One Rule (both modes)

**Every scene function must fully describe DOM state from scratch. Never build cumulatively.**

Why: if scene 4 calls `appendChild(panel)` and scene 5 doesn't remove it, then `← Previous` from scene 6 to scene 4 leaves the panel duplicated. Idempotent rendering eliminates this entire class of bugs.

How:

1. Declare every possible UI element in the initial HTML, hidden with `.hidden` class (or with default content for live-text fields)
2. Scenes call `show('panelId')` / `hide('panelId')` to toggle visibility
3. Scenes call `setComp(id, state)` / `setArrow(id, state)` / `setLabel(id, show)` / `setBadge(id, html)` — these REPLACE state, never append
4. Scenes call `setText(id, text)` to update live-text fields
5. The render loop calls `clearAllStates()` first, then runs ONLY the current scene function

**No scene function ever does:**

- `document.createElement(...)`
- `el.appendChild(...)`
- `el.classList.add(...)` (use the wrapper setters, which replace)
- `el.innerHTML += ...`

If you need to "add" a panel mid-walkthrough, declare it once in the initial HTML with `.hidden` and `show()` it from the scene.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Wrong mode picked — tables for a flow problem | Use the "How to choose" rule. Flow → diagram. Row state → tables. |
| Auto-playing animation that races past the reader | Manual `Next →` only. Reader controls pace. |
| Abstract names (`A`, `B`, `Table1`, `Customer1`) | Real, domain-flavored, culturally appropriate names. |
| IDs collide with output sequence numbers (`cargo-1` vs booking `00001`) | Use letter IDs (`cargo-A`) or source-tagged labels (`cargo (Portal)`). |
| Each step changes too many things at once | One component activates per step. One arrow fires. One value moves. |
| Narration says WHAT, not WHY | Every narration explains the rule's reason. |
| No "key question" step | The conflict/concurrency reveal needs a thinking-pause beforehand. |
| Fix without side-effects called out | Resolution always has trade-offs — name them. |
| Cumulative-replay rendering | Idempotent scenes only — no `appendChild` from scenes. |
| 300+ lines of HTML for a 2-step problem | This skill is for problems with 4+ chained effects. Smaller problems → just chat or use a single mermaid diagram. |
| `← Previous` leaves stale state | Scene functions must fully describe state, not deltas. |
| Same element never highlighted in the conflict step | Pick concrete data so at least one element is hit by every problematic path. |
| Flying-label rect too small / clipped text | Measure your label text length; widen the `<rect>` to fit comfortably. |

## Reference Examples

- **`c:/Repo/glasshull repo/glasshull/docs/2026-05-28-polaris-booking-number-diagram.html`** — DIAGRAM MODE canonical. 22 steps explaining how a classic workflow + CodeActivity + counter entity collaborate to assign sequential booking numbers, including a 3-transaction concurrency demo and a race-condition counter-example. Mixed Thai/English narration. Use this as the structural reference for any architecture/flow walkthrough.
- **`c:/Repo2/t/cascade-paths-explained.html`** — TABLES MODE canonical. 7 steps explaining SQL Server error 1785 (multiple cascade paths) using "ครอบครัวสมศรี" budget transactions. Use this for any row-state walkthrough.
