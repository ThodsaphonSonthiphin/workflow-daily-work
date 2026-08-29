# The front page shows the whole-set command first, then the single-skill form

```mermaid
flowchart TD
    Q{"Which npx command does a stranger<br/>see on opening the repo?"}
    Q -->|chosen| A["Both, whole-set first:<br/>--all, then --skill NAME.<br/>Matches how the plugin channel<br/>reads on the same page."]
    Q -->|rejected| B["Only --skill NAME.<br/>Someone who wants the toolkit<br/>would have to install 55 skills<br/>one command at a time."]
    Q -->|rejected| C["Only --all.<br/>Drops the single-skill install,<br/>which is the reason this channel<br/>was wanted."]
```

Requested by the owner: there must be a way to install everything in one command.
Measured the same day — `npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work
--all` installs the whole set (53 today, 55 after ADR 0156's rename) in one run.

`--all` is not decoration. Without it the CLI opens an interactive picker for a human at a
terminal; `--all` is what makes "install everything" a command someone can paste. The
single-skill form keeps its place beside it, because taking one skill into an unrelated
project is what started this work. Both lines sit in the README's existing Install block
per ADR 0160; neither names a skill, so ADR 0090 still holds.
