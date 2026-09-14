# `handoff` is vendored from mattpocock/skills as a MODIFIED copy, not verbatim like `wait-what`

```mermaid
flowchart TD
    Q{the owner wants mattpocock's handoff skill<br/>as this marketplace's own, usable any time —<br/>verbatim, or adapted?} -->|chosen| A["a MODIFIED copy under
    LICENSE-mattpocock-skills, pinned to the
    upstream sha the installed plugin records:
    harness-neutral wording, an opening diagram,
    a cloud destination (ADR 0228), the 'working
    if' list from upstream's own docs; manual
    invocation kept (disable-model-invocation)"]
    Q -->|rejected| B["verbatim, the way wait-what was —
    upstream says 'call the Skill tool', which
    this repo's harness-neutral rule forbids, and
    upstream has no cloud destination at all, which
    is the reason the owner asked"]
    Q -->|rejected| C["keep using mattpocock-skills:handoff
    from the official marketplace — not installed on
    every machine or harness this marketplace
    targets, and cannot carry the cloud destination"]
    Q -->|rejected| D["write our own from scratch — upstream's
    trigger table, no-duplication and redaction
    rules are exactly right; re-deriving them
    buys nothing"]
```

The owner asked for mattpocock's `handoff` as a skill of this marketplace, to use
at any phase boundary and specifically to hand a written plan to a Claude Code
cloud session. Upstream's copy is small and right about the core — portability
not compression, suggested skills, reference-don't-copy, redact — but it names
one harness's tool and knows nothing about cloud sessions, so a verbatim copy
would break this repo's harness-neutral rule and miss the requested case. It is
therefore vendored as a **modified** copy: the licence file lists the changes and
the upstream sha (`6654f6b60cd9…`, the commit the installed 1.2.3 plugin pins),
`generate_skills_tree.py` carries the licence into the generated tree the way
it does for `wait-what` (ADR 0158), and `disable-model-invocation: true` is kept
— a handoff is something the user asks for, never something the agent decides.
