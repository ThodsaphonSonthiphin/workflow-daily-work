# problem-description Mode Framework + state-machine (Phase 2) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or executing-plans. Steps use `- [ ]`. (Author note: the artifacts workflow hit a session limit; the controller is executing this plan directly, committing per task so progress is durable and the repo stays coherent at every commit.)

**Goal:** Turn the two hard-coded visualization modes into a plug-in mode framework — one inlined-at-generation engine reference + per-mode renderer packs — migrate diagram + tables onto it, and ship the first new mode, **state-machine**.

**Architecture:** `references/walkthrough-engine.html` owns the step loop, nav, `:root` palette, narration contract, `RENDER_HOOKS=[]`, `modeRenderers={}`, `MODE`. Each mode is a `references/mode-<name>.html` pack registering one renderer `{registry, clear(reg), <setters>, assertRegistryComplete()}`. Generation splices engine § + one pack § + drawer § + authored scenes/GLOSSARY → one self-contained file, sets `MODE`, aliases renderer methods to flat names. Drawer self-registers `RENDER_HOOKS.push(closeDrawer)`. A post-assembly self-test is the no-build safety net.

**Tech Stack:** Plain HTML/CSS/vanilla JS, self-contained, no build. Verify: extend the Phase-1 `check_drilldown.py` + browser via local HTTP server (Playwright blocks `file://`).

## Global Constraints (verbatim)

- Generated walkthrough = ONE self-contained .html; no build; no external assets.
- DRY: the engine exists once (`references/walkthrough-engine.html`); never duplicated into a pack. A pack is browser-verified by **assembling** engine+pack+demo into a scratch file and opening that.
- No NEW color tokens: core palette hoisted to `:root`; reuse existing hexes only; SVG marker fills use the engine's fixed 5 markerheads (`arrowhead`/`-active`/`-magic`/`-done`/`-error`) or `var(--token)`. Tables `.target-conflict` gradient `#3a1818`→`#3a2810` and diagram per-variant `.step-title` recolors lifted verbatim.
- Idempotent scenes: engine runs `RENDER_HOOKS` → `R.clear(R.registry)` → `scenes[step]()`. Scenes never `createElement`/`appendChild`, never reference `openTerm`/`closeDrawer`/`GLOSSARY`.
- Narration contract = diagram's NESTED shape; 3-arg `setNarration(cls,title,bodyHTML)` + `setSceneTitle`; tables migrates; `--bg=#0a0e14`.
- Hybrid scene API: renderer object is the engine contract; generation aliases methods to flat names.
- Registration-push: engine declares empty `RENDER_HOOKS`/`modeRenderers`/`MODE`; drawer & mode `§JS` push/register; only ordering rule = engine `§JS` precedes drawer/mode `§JS`.
- Harness-neutral, skill-relative paths (`references/x.html`). SKILL doc follows the diagram convention. No PLAYBOOK row.
- Post-assembly self-test asserts: (1) `modeRenderers[MODE]` resolves to `{registry,clear,setters}`; (2) `RENDER_HOOKS` includes `closeDrawer` and runs before paint; (3) `assertRegistryComplete()` throws on any scene id missing from the registry; (4) engine `§JS` precedes drawer/mode `§JS`.

Spec: `docs/superpowers/specs/2026-06-27-problem-description-mode-framework-design.md`. ADRs 0020–0024.

## :root token set (core palette, enumerated from the two templates)

```
--bg:#0a0e14; --panel:#1a2330; --surface:#0f1722; --surface-2:#0f1419;
--border:#2a3441; --border-dim:#3d4a5f; --surface-active:#233040;
--text:#e0e6ed; --text-dim:#b8c4cf; --muted:#6b7785; --muted-2:#8a96a3;
--accent:#5fb4ff; --accent-bright:#7ed4ff;
--amber:#ffd479; --warn:#ffaa00; --warn-text:#ffaa44;
--magic:#b070ff; --magic-text:#d4a4ff; --magic-bg:#2a1a3a;
--success:#4ade80; --success-text:#a3e8b9;
--error:#ff5757; --error-text:#ff8888; --conflict:#ff3030;
```
Mode-specific state-background shades (e.g. diagram `#1a3a5f`/`#2a2818`, tables `#3a1818`/`#3a2810`/`#2a4a5f`/`#1a3320`) stay as their existing hexes in the mode pack CSS — reused, not new.

## Tasks (each ends in a browser-verified, committed, repo-coherent state)

### Task 1 — `references/walkthrough-engine.html` (the shared engine)
- Create the engine reference: `§CSS` (`:root` block; chrome: body/container/h1/h2/code/controls/buttons/step-progress/step-dot; the nested `#narration` box with the full variant set incl `.magic`; `.wt-panel`; `.hidden`), `§HTML` (container shell with `#stepProgress`, nested `#narration` [`#stepBadge`,`#sceneTitle`,`#narrationBody`], `#controls`, the 5 `<marker>` defs in a hidden `<svg>`), `§JS` (`let currentStep,TOTAL; const RENDER_HOOKS=[],modeRenderers={}; let MODE; show/hide null-guarded; setNarration(cls,title,bodyHTML); setSceneTitle; buildProgressDots; render(step){RENDER_HOOKS.forEach(h=>h()); const R=modeRenderers[MODE]; if(R&&R.clear)R.clear(R.registry); scenes[step]&&scenes[step](); dots/#stepBadge/nav}; nav handlers; bootstrap render(0)`).
- Built-in DEMO mode: register `modeRenderers['_demo']` + a 2-scene demo + `MODE='_demo'` in a DEMO-ONLY block so the engine opens standalone.
- Verify: serve dir, browser → engine loads, demo steps, no console errors (favicon ok). Commit.

### Task 2 — `references/mode-state-machine.html` (first new mode)
- Pack registers `modeRenderers['state-machine'] = { registry:{NODE_LIST,EDGE_LIST}, clear(reg), setNode(id,state), setEdge(id,state), assertRegistryComplete() }`.
- `§HTML`: `<svg>` with `<g class="sm-node" id="...">` states + `<path class="sm-edge" id="...">` transitions using engine markerheads. `§CSS`: `.sm-node`/`.sm-edge` state classes on palette tokens (current=accent, passed=success, illegal/stuck=error, key=magic, idle=dimmed) — 0 new tokens, 0 new markers. `§JS`: renderer + a 3-scene DEMO (BookingItemStatus: Planning→Confirmed→Allocated→Loaded→Discharged; conflict = illegal re-activate edge lit error).
- Verify: assemble `<SCRATCH>/sm-sample.html` = engine §CSS/§HTML/§JS + pack §CSS/§HTML/§JS + `MODE='state-machine'` + alias + demo scenes; browser → states/edges paint, illegal edge red, stepping works, self-test asserts pass. Commit pack.

### Task 3 — `references/mode-diagram.html` (migrate diagram)
- Extract from `template-diagram.html`: keep the SVG component/arrow/label CSS + content + DOM helpers as `modeRenderers['diagram']={registry:{COMPONENTS,ARROWS,LABELS}, clear, setComp,setArrow,setLabel,setText, assertRegistryComplete}`; delete its embedded engine (now from the engine ref); narration already nested.
- Verify: assemble + browser; visual unchanged vs Phase-1 diagram demo (regression). Commit.

### Task 4 — `references/mode-tables.html` (migrate tables + narration migration)
- Extract from `template.html`: `modeRenderers['tables']={registry:{ID_LIST}, clear, setRowClass,setBadge,setCell,setRule, assertRegistryComplete}`; **migrate narration to nested 3-arg shape** (drop outer `.scene` card / header-above; fold `setSceneTitle`); `--bg`; lift `.target-conflict` gradient verbatim.
- Verify: assemble + browser; cascade demo works; narration nested; regression. Commit.

### Task 5 — assembly procedure + checker
- Add `references/_assembly.md` (or a SKILL section) documenting the splice + alias + self-test. Extend the checker (`scripts/check-walkthrough.py` in skill, or scratch) for the 4 asserts + drawer integrity + scenes-clean across an assembled file.
- Verify: run checker on the Task-2/3/4 assembled samples → pass. Commit.

### Task 6 — SKILL.md rewrite + retire old templates
- Rewrite to the engine+pack model + flat selection table (diagram/tables/state-machine rows + 2 disambiguators) + assembly + self-test; per-mode detail points to pack files. **Atomically** remove `template.html`/`template-diagram.html` (replaced by engine + packs) in this same commit so the repo never references missing files.
- Verify: SKILL.md links resolve; no dangling refs. Commit.

### Task 7 — timeline + tree dry-sketch
- Add `docs/superpowers/plans/_artifacts/phase2-timeline-tree-drysketch.md`: registries/setters/clear/§HTML for each + verdict on zero-engine-edit additivity (or the one minimal layout hook). Commit.

### Task 8 — end-to-end proof + finish
- Browser-verify an assembled state-machine walkthrough with a drillable term (drawer composes; Next closes drawer + advances). Run checker on all assembled samples. Version bump `plugin.json`+`marketplace.json` if warranted. Final review. Merge.

## Acceptance criteria
- [ ] Engine runs standalone; each pack assembles+runs; state-machine paints with 0 new tokens/markers.
- [ ] diagram + tables visually unchanged (tables narration nested is the one intended change).
- [ ] Drawer composes in an assembled walkthrough; Next closes it; checker passes 4 asserts + drawer integrity + scenes-clean.
- [ ] SKILL.md selection table has the 2 disambiguators; no dangling template refs; old templates removed.
- [ ] timeline/tree dry-sketch records the additivity verdict.
