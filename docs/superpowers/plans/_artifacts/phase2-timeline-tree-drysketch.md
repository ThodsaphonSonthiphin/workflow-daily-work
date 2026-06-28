# Additivity dry-sketch — timeline & tree against the mode-pack contract

Per [ADR 0023](../../../adr/0023-additivity-proof-dry-sketch-timeline-tree.md): sketch the
two layout-stressing future modes against the renderer contract **without building them**,
to confirm the framework boundary holds (adding a mode = **zero engine edits**). The
contract a pack implements (from `references/walkthrough-engine.html`):

```js
modeRenderers['<name>'] = { registry, clear(reg), <replace-only setters>, assertRegistryComplete() };
// engine render(): RENDER_HOOKS → R.clear(R.registry) → scenes[step]()
```

The engine positions nothing — every mode's geometry is authored in its `§HTML` (diagram
component coords, state-machine node coords are all in markup). The question for timeline
and tree: can their geometry also live in authored markup, expressed at runtime purely as
class toggles over pre-declared ids — or does either force an engine layout hook?

## timeline (events on a continuous time axis)

- **registry:** `EVENT_LIST: ['evCreated','evConfirmed','evTimeout', …]` (one id per event marker).
- **§HTML:** an `<svg>` with a static horizontal axis (`<line>` + tick `<text>`), and one
  `<g class="tl-event" id="evX" transform="translate(<x>,<y>)">` per event. **x is computed
  at authoring time** from the event's timestamp (`x = left + (t - t0)/span * width`), exactly
  as diagram/state-machine compute node coords at authoring time. SVG edges select the
  engine's markerheads.
- **setters:** `setEvent(id, state)` — replace class (`pending`/`fired`/`late`/`conflict`);
  optional `setSpan(id, state)` for duration bars.
- **clear(reg):** reset every `EVENT_LIST` id to idle; hide `.wt-panel`.
- **VERDICT: ✅ zero engine edits.** Geometry is authored markup; runtime is class toggles
  over pre-declared ids — the existing render slot fits. **Caveat:** if a future author wanted
  the engine to auto-lay-out events from raw timestamps *at runtime*, that would be a layout
  hook — avoided by the authoring-computes-x model (consistent with every existing mode).

## tree / hierarchy (containment indentation)

- **registry:** `NODE_LIST: ['tnRoot','tnChildA','tnChildB', …]` (+ optional `EDGE_LIST` for connectors).
- **§HTML:** nested `<div class="tree-node" id="tnX" style="margin-left:<depth*24>px">` (or an
  `<svg>` with authored coords). **Indentation/positions authored in markup**, by depth, at
  authoring time.
- **setters:** `setTreeNode(id, state)` — replace class (`active`/`visited`/`pruned`/`conflict`);
  optional `setBranch(id, state)`.
- **clear(reg):** reset every `NODE_LIST` id to idle; hide `.wt-panel`.
- **VERDICT: ✅ zero engine edits** for a **step-driven** tree (scenes reveal/highlight
  pre-declared nodes). **Caveat (important):** *reader-driven expand/collapse* is a NEW reader
  affordance that collides with both the idempotent-scene rule and the reader-driven drawer
  (two competing reader interactions) — it would need engine work and a collision design.
  So build tree **step-driven only**; keep expand/collapse out of the registry model. This is
  why tree is sequenced LAST in Phase 3 (per the spec's risk list).

## Conclusion

Both modes express as replace-setters over pre-declared, authoring-positioned ids with **no
engine layout hook** — the renderer-registry boundary is calibrated correctly. The only
things that would force an engine change (runtime auto-layout; reader-driven expand/collapse)
are explicitly out of the authoring model. No engine layout hook is added in Phase 2.
