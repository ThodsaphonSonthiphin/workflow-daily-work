# The front page carries the command; INSTALL.md carries what churns

```mermaid
flowchart TD
    Q{"The owner wants the install visible<br/>on opening the repo. ADR 0090 bars<br/>churning facts from the front page."}
    Q -->|chosen| A["README's existing Install block gains<br/>the npx line - a command, which<br/>ADR 0090 calls a stable entry point.<br/>INSTALL.md holds the rest."]
    Q -->|rejected| B["The whole guide on the README:<br/>skill names and per-skill gotchas are<br/>exactly the facts that rotted<br/>through 122 commits."]
    Q -->|rejected| C["Everything in INSTALL.md, README<br/>only points. The owner asked to see it<br/>on opening the repo, and a pointer<br/>is not seeing it."]
```

ADR 0090 is not in tension with showing the command. It sets the front page's audience as
a stranger, puts install "four lines just below" the opening, and bars *skill names,
counts, versions and roadmap status* — the facts measured to have rotted. An install
command is the opposite of that: it names a plugin or a repo, and it changes when the
install mechanism changes, which is the moment someone is editing this anyway.

So the split follows what rots:

- **README** — both channels as copy-pasteable commands, in the Install block that already
  exists on the first screen. No skill names.
- **INSTALL.md** (new, repo root) — choosing between the channels, the `--skill=<name>`
  trap that silently installs everything, the short-alias mapping table, what the npx
  channel does not carry (hooks, aliases, auto-update), the renames from ADR 0156, and the
  per-plugin machine setup.

One consequence worth naming: ADR 0090 refused a CI badge because "a green badge with
nothing behind it is worse than none". ADR 0159 puts something behind it, so the badge
becomes available — and it is a claim about the repo, not a fact that churns.
