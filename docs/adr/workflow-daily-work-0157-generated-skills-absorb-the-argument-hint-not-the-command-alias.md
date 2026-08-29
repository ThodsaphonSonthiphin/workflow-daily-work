# Generated skills absorb the command's `argument-hint`, not its alias

```mermaid
flowchart TD
    Q{"skills.sh installs skills only,<br/>never the 16 command wrappers.<br/>What happens to those entry points?"}
    Q -->|chosen| A["The generator folds each command's<br/>argument-hint into its skill's<br/>frontmatter. Users type the skill's<br/>own name, and a table in the doc<br/>maps the short aliases."]
    Q -->|rejected| B["Do nothing.<br/>Autocomplete stops hinting<br/>what arguments a skill takes."]
    Q -->|rejected| C["Generate 16 alias skills so /feynman<br/>works too. Installing an alias alone<br/>yields a pointer to a skill<br/>the machine does not have."]
```

Claude Code merged custom commands into skills: a skill at `.claude/skills/<name>/` is
invocable as `/<name>`, and `disable-model-invocation: true` blocks only automatic
invocation, not the user typing it. So the npx channel does not lose the ability to
invoke anything — `wait-what` and `document-what-shipped` stay reachable. What it loses
is the *short alias* (`/ask` for `asking-to-understand`, `/feynman` for
`feynman-explain`, `/chart` for `chart-map`, `/run` for `findings-to-ado-backlog`) and
the `argument-hint` that made autocomplete useful.

The hint is worth carrying and costs one frontmatter key; the alias is not worth a
generated skill whose whole body is a pointer, because `--skill <alias>` installs that
pointer on its own and the target is absent. Aliases stay a plugin-channel feature, and
the user-facing document carries the name-mapping table.
