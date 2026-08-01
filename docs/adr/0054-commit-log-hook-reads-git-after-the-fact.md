# ADR 0054 — the commit-log hook reads git after the fact, not the command line

- **Status:** Accepted
- **Date:** 2026-08-01

```mermaid
flowchart TD
    Q{"where does the commit-log hook<br/>get the commit message?"} -->|chosen| POST["PostToolUse + read git —<br/>`git log -1` after the command ran;<br/>dedupe by short SHA so only commits<br/>that actually happened are logged"]
    Q -->|rejected| PRE["PreToolUse + parse the command line —<br/>shipped behaviour; cannot see shell<br/>substitution, cannot see a commit with<br/>no -m, and logs commits that then fail"]
    Q -->|rejected| PATCH["keep parsing, patch each symptom —<br/>fixes three known cases and leaves the<br/>class open (aliases, -F file, --template,<br/>any future message form)"]
```

## Context

`commit-log.py` echoed every commit into the repo's `daily-state.md ## Log`. It ran
as a **PreToolUse** hook and reconstructed the message by parsing `-m` values out
of the Bash command string. That produced four classes of wrong entry, all
reproduced from real log data in this repo (damage dating to 2026-06-26):

- **Mojibake.** `json.load(sys.stdin)` decodes a pipe with the Windows ANSI
  codepage, so every non-ASCII character in a subject was mangled — an em dash
  logged as `â€”`, Thai text as `à¸žà¸±...`. The tell was that the hook's *own*
  hardcoded separator survived while characters from the payload did not.
- **Shell substitution logged raw.** `-m "$(cat <<'EOF' … EOF)"` is a literal
  token to `shlex`, so the log got the shell source instead of the message —
  and, being multi-line, it broke the `## Log` list structure. 14 such entries.
- **Content-free placeholders.** A commit with no `-m` (`--amend --no-edit`,
  editor form) fell back to the string `(commit)`. 7 such entries.
- **Phantom entries.** The guard `"git" in tokens and "commit" in tokens` fires on
  any command merely mentioning the word — `git log … # show last commit` logged
  an entry. And because PreToolUse runs *before* the command, a commit that then
  failed was logged as if it had succeeded.

Parsing the command line is the common cause: it infers the outcome from the
request instead of observing it.

## Decision

The hook moves to **PostToolUse** and reads the commit from **git itself** —
`git log -1 --format=%h%x00%s` — after the command has run. Entries are
**deduplicated by short SHA**, which is recorded in the log line.

Consequences of that shape, rather than rules bolted on:

- A failed commit never moves HEAD, so nothing is logged. No outcome inference.
- Any message form works — `-m`, `-F`, `--template`, editor, alias, heredoc — because
  the message is never parsed out of the command.
- A commit message **rewritten by another git hook** is logged as rewritten, which is
  the truth of the record (this repo has a documented case of an AI hook silently
  replacing commit messages).
- Re-firing on the same commit is a no-op, so the hook is idempotent.
- Non-ASCII is read as UTF-8 from `sys.stdin.buffer`, never through the locale codec.

The **hard contract is unchanged**: best-effort only, always exit 0, never write to
stdout, swallow every failure. A missing log line is acceptable; a blocked command is
not. `plugins/dev-workflows/scripts/test_commit_log.py` covers all four classes plus
the contract under malformed payloads.

## Consequences

- ➕ The log becomes a record of what git did, not of what an agent typed.
- ➕ The whole class is closed, not three instances of it.
- ➖ Two `git` subprocesses per Bash command whose text mentions a commit-creating
  verb (a substring pre-filter keeps every other call at zero).
- ➖ A commit created by a command that mentions none of those verbs is not logged;
  the next matching command backfills it, since dedupe is by SHA rather than by run.
- ➖ Log lines now carry a short SHA, so entries written before this change have a
  different shape. Existing corrupted entries are **not** rewritten by this ADR —
  repairing them is a separate, reviewable data migration.
