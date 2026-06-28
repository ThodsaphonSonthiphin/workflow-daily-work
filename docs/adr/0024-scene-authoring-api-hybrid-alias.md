# Scene-authoring API: hybrid — engine keeps the renderer object, generation aliases methods to flat names

```mermaid
flowchart TD
    Q{"How do authored scene bodies call a mode's setters,<br/>given the engine dispatches through modeRenderers[MODE]?"}
    Q -->|chosen| A["Hybrid: the renderer object is the engine's contract surface<br/>(registry + clear() + dispatch); at GENERATION its methods are<br/>aliased to flat top-level names — const {setNode,setEdge}=<br/>modeRenderers[MODE] — so scene bodies read flat like today's<br/>setComp(...)"]
    Q -->|rejected| B["Full dispatch: scenes call R.setNode(...) via const R=<br/>modeRenderers[MODE] — collision-proof and mode-blind, but<br/>verbose in the part authored most"]
    Q -->|rejected| C["Flat-only, drop the registry — simplest scene reads, but the<br/>engine loses its generic clear()/dispatch; each mode wires<br/>its own"]
```

The renderer-registry (ADR 0020) gives the engine a clean, mode-blind contract via
`modeRenderers[MODE]`, but the indirection layer is its one real authoring-ergonomics
cost: scene bodies — the part an author writes most — would read `R.setNode(...)` instead
of today's flat `setComp(...)`. We take the **hybrid**: the renderer object stays the
engine's contract surface (it owns the id-registry, the replace-only setters, and the
`clear()` body the engine calls generically), but at **generation time** its methods are
aliased to flat top-level names (`const { setNode, setEdge } = modeRenderers[MODE]`) so
the authored scenes stay exactly as readable as today's. This keeps the structural wins
the judges valued — `R`-namespaced collision-proofing, a mode-blind engine, only the
chosen renderer inlined — while removing the ergonomic tax on scene authoring. Full
dispatch was rejected for verbose scene bodies; flat-only was rejected for losing the
engine's generic `clear()`/dispatch.
