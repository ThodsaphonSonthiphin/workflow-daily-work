# The `cloud` destination commits and pushes the handoff into the repo; every other destination stays in temp

```mermaid
flowchart TD
    Q{a Claude Code cloud session clones the branch<br/>from GitHub and sees nothing on this machine —<br/>where does the handoff document go?} -->|chosen| A["docs/superpowers/handoffs/<date>-<slug>.md
    on the working branch, committed and pushed;
    the document names the branch, the plan path,
    the launch (web and CLI), how the result comes
    back, and says the local plugins are absent on
    cloud; temp stays the default for every other
    destination; the file is left in place after
    the work lands"]
    Q -->|rejected| B["temp, as upstream — the file does not
    exist on the cloud machine"]
    Q -->|rejected| C["paste the summary as the cloud session's
    prompt — upstream's own warning: backticks and
    $(...) are mangled on interpolation and the
    failure is silent truncation"]
    Q -->|rejected| D["delete the file in the merge PR — a dated
    record of the crossing costs nothing and
    explains a claude/… branch's origin"]
```

Upstream `handoff` writes to the OS temp directory on purpose: a handoff is a
transit document, not an artifact. That holds for every destination except one.
A Claude Code cloud session is created from a GitHub branch; it has no access to
this machine, its temp directory, its marketplaces or its user-scope plugins.
The only channel into it is the branch itself, so for the `cloud` destination
the document is written into the repo under `docs/superpowers/handoffs/`,
committed, and pushed on the working branch — never on `main` — after anything
it points at (spec, plan, ADRs) has been committed too. Because the plugins are
absent there, the document must stand on its own and say so: it names the plan
path, states that the plan is self-contained, and does not promise a review loop
that depends on a skill the cloud session cannot load. The launch is given both
ways (the web *Create session* route and `claude --cloud "Read <path> and
continue from it."`), pointing at the file rather than pasting it, and the return
path is named (`claude --teleport`, or fetch and check out the `claude/…`
branch) together with what must be re-verified locally before merge. The file
stays after the work lands.
