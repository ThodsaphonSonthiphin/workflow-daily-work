# Drill-down primitive lives in one reference file, inlined at generation

```mermaid
flowchart TD
    Q{"The drawer code must appear in every<br/>self-contained walkthrough. How do we<br/>avoid maintaining two copies (one per template)?"}
    Q -->|chosen| A["One source: references/term-drilldown.html<br/>(runnable demo + copyable CSS/HTML/JS).<br/>Templates carry markers; the skill inlines<br/>the reference at generation time"]
    Q -->|rejected| B["Byte-identical copy in BOTH templates<br/>— two hand-maintained copies drift;<br/>review rubric flags it as DRY defect"]
    Q -->|rejected| C["Sync script keeps template copies in step<br/>with one source — templates stay runnable<br/>but adds markers + a generator/checker to<br/>maintain; heavier machinery for ~70 lines"]
```

A generated walkthrough must be a **single self-contained file** (ADR 0017 / SKILL.md
output contract), so the drawer's CSS + HTML + JS physically appears in every output —
"DRY" cannot mean a runtime import. It can only mean **one source of truth at authoring
time**. We keep the primitive in a single new file,
`plugins/dev-workflows/skills/problem-description/references/term-drilldown.html`, which
is **both** the canonical copy (clearly-delimited CSS / HTML / JS-framework sections to
inline) **and** a standalone runnable demo of the drawer (open it in a browser to see it
work). The two templates no longer carry the drawer code — they carry a short marker at
each insertion point — and the skill inlines the reference sections into the walkthrough
it generates. This refines the *implementation* of [ADR 0018](0018-drill-down-is-side-drawer-with-see-also-hops.md)
(the drawer-vs-tooltip container choice is unchanged); it supersedes the earlier
"add the block to both templates" approach in the design spec. Trade-off accepted: the
raw templates no longer demo the drawer standalone — that demo now lives in the reference
file, which doubles as the single source. End-to-end integration is proven during
verification by assembling a sample walkthrough from a template + the reference.
