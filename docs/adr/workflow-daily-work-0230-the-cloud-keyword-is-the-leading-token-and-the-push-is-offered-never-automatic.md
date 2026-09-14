# The `cloud` keyword is the leading token, and the push is offered, never automatic

```mermaid
flowchart TD
    Q{where in the argument does `cloud` select the<br/>cloud destination, and does the skill commit<br/>and push it on its own?} -->|chosen| A["leading token only —
    /dev-workflows:handoff cloud <what next>;
    commit AND push are OFFERED (assisted git),
    never automatic; on main the skill STOPS and
    says 'branch first' until a branch exists"]
    Q -->|rejected| B["keyword anywhere in the argument, as spec
    §3 first said — 'cloud' is an ordinary word
    here, so an ordinary subject line pushes by
    accident"]
    Q -->|rejected| C["a separate /dev-workflows:handoff-cloud
    command — removes the ambiguity but splits
    one skill into two entry points for one act"]
    Q -->|rejected| D["push automatically once the commit was
    offered — a push leaves the machine, and the
    repo's assisted-git rule (ADR 0014) offers
    every write that does"]
```

This ruling came out of the final whole-branch review of the `handoff` branch
(2026-09-14). The drafted skill and its spec (§3 item 1) said the word `cloud`
"anywhere in the arguments" selects the cloud destination. In this repo `cloud`
is an ordinary word — "cloud portal", "cloud flows" — and the cloud path
commits and pushes, so an ordinary subject line containing it would silently
select a push. The fix scopes the trigger to the argument's first token, the
same shape as any other flag-like leading word, so `/dev-workflows:handoff
cloud <what next>` selects it and `/dev-workflows:handoff fix the cloud flows
config` does not.

The same review found the drafted §4 steps 1–2 treated the commit as offered
but the push as automatic once a branch existed. ADR 0014 already settled that
a git write in this repo is offered, never run silently; a push is a git write
that leaves the machine, so it gets no exception. The skill now stops outright
when the current branch is `main` — "branch first" — rather than proceeding to
an offer that would only be refused, and once past that, the commit and the
push are each their own yes/no, never chained automatically off one approval.
This ADR amends the spec and ADR 0228's step-by-step description accordingly;
it does not reopen ADR 0228's choice of destination or ADR 0227's choice to
vendor the skill.
