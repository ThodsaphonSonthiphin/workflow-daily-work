# Every skill installs standalone via `npx skills`, from a generated tree

```mermaid
flowchart TD
    Q{"29 of 55 skills point at plugin-level files<br/>outside their own directory.<br/>How do they install through skills.sh,<br/>which copies only the skill folder?"}
    Q -->|chosen| A["Generate a distribution tree<br/>with those paths resolved.<br/>Sources keep one canonical copy —<br/>the channel carries every skill."]
    Q -->|rejected| B["Declare a standalone-safe subset<br/>(~26 of 55) and document only those.<br/>Cheapest, but the headline command<br/>stays half-broken for the other 29."]
    Q -->|rejected| C["Inline the shared references and scripts<br/>into each skill directory at source.<br/>Contradicts ADR 0008 - one canonical<br/>diagram-convention.md - and drifts."]
```

`npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work` already works today
without any repo change: the skills.sh CLI reads `.claude-plugin/marketplace.json`, and a
probe on 2026-08-29 found 53 skills. What does **not** work is what the skills do once
copied. Measured in the same probe: the CLI copies the skill directory and nothing else,
so plugin-level `references/` and `scripts/` never arrive, and **29 of the 55 skills**
resolve a `${CLAUDE_PLUGIN_ROOT}/references/...` or `.../scripts/...` path that is not
there — `grill-then-plan`, `daily`, `sa-doc`, `debug-mantra`, both backlog pipelines and
both decision-map skills among them. Nothing errors; the skill simply reads an
instruction pointing at a file that does not exist.

The decision is that this channel is held to the same bar as the plugin: **every** skill
installs and works, not a subset that happens to be self-contained. The mechanism is a
generated distribution tree in which those paths are already resolved — the same shape
`plugins/dev-workflows/.antigravity/install-antigravity.py` already uses for the harness
with the same limitation, rather than a second idea invented for this one. Where that
tree lives, and what keeps it from drifting from its sources, are separate decisions.

Option B was rejected on the user's own framing: the ask is that the skills install
easily, not that some of them do. Option C was rejected because it moves the shared
files into ~20 skill directories, which is precisely the duplication ADR 0008 closed.
