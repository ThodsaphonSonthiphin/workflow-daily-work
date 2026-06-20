# Installing dev-workflows on Google Antigravity

The dev-workflows skills run on **both Claude Code and Antigravity** from one
source tree. The two harnesses install differently:

| | Claude Code | Antigravity |
|---|---|---|
| Install | the marketplace (`/plugin install dev-workflows@workflow-daily-work`) | the installer in this folder |
| Skill discovery | plugin manifest | folder scan + semantic match on `description` |
| Bundled-file paths | `${CLAUDE_PLUGIN_ROOT}` expanded by the harness | **relative to the skill dir, no variable expansion** |

Because Antigravity does not expand `${CLAUDE_PLUGIN_ROOT}`, this installer stages
a working copy: it places each skill in Antigravity's skills directory, copies the
plugin-level `references/` and `scripts/` into a shared support folder beside them,
and rewrites every `${CLAUDE_PLUGIN_ROOT}/...` reference to a real absolute path.
**The source tree is never modified — your Claude Code install keeps working.**

## Prerequisites

- Google Antigravity (IDE or CLI) installed.
- Python 3.9+ on PATH (the same Python the plugin's `daily-state.py` uses).
- A local checkout of this repo.

## Install

From this folder (`plugins/dev-workflows/.antigravity/`):

```bash
# Antigravity IDE — global scope (~/.gemini/config/skills)   [default]
python install-antigravity.py

# Antigravity CLI — global scope (~/.gemini/antigravity-cli/skills)
python install-antigravity.py --scope cli

# Project scope — installs into <repo>/.agents/skills
python install-antigravity.py --scope project --project /path/to/your/repo

# Preview only, write nothing
python install-antigravity.py --dry-run
```

On Windows, use the same command (`python install-antigravity.py`) from PowerShell
or Git Bash.

After it finishes, **reload Antigravity** (restart the IDE, or start a new CLI
session) so it rediscovers the skills.

### What gets installed

Into the target skills directory:

```
<skills-dir>/
  grill-then-plan/SKILL.md ... + each of the 16 skills
  daily/ ...
  .dev-workflows-shared/
    references/   (diagram-convention.md, daily-state-contract.md)
    scripts/      (daily-state.py, ...)
```

`.dev-workflows-shared/` is dot-prefixed and has no `SKILL.md`, so Antigravity does
not treat it as a skill — it is just the resolved home for files the skills point at.

## Verify it works

1. Start a fresh Antigravity session in any project.
2. Ask: **"What skills do you have for daily dev work?"** — it should list
   dev-workflows skills (semantic discovery surfaces them by `description`).
3. Trigger one by intent, e.g. **"grill my plan then write an implementation
   plan"** → it should load `grill-then-plan` and begin the Step 0 preflight.
   (grill-then-plan also needs a superpowers skills port installed on Antigravity;
   if absent, Step 0 will tell you and stop — that is the correct behavior.)

If a skill that runs a bundled script (e.g. `daily`) reports it cannot find the
script, re-run the installer and confirm it ended with `rewrote N
${CLAUDE_PLUGIN_ROOT} reference(s)` and no warning.

## Update

Re-run the same command. Existing skill folders and `.dev-workflows-shared/` are
replaced cleanly each time.

## Uninstall

Delete the installed skill folders and `.dev-workflows-shared/` from the target
skills directory. Claude Code is unaffected (it never used this copy).

## How this maps to the source

The installer rewrites three reference shapes (the only ones the skills use):

| Source reference | Installed path |
|---|---|
| `${CLAUDE_PLUGIN_ROOT}/references/…` | `<skills-dir>/.dev-workflows-shared/references/…` |
| `${CLAUDE_PLUGIN_ROOT}/scripts/…` | `<skills-dir>/.dev-workflows-shared/scripts/…` |
| `${CLAUDE_PLUGIN_ROOT}/skills/…` | `<skills-dir>/…` (skills are staged flat) |

If a future skill introduces a new `${CLAUDE_PLUGIN_ROOT}/<something>/` shape, the
installer exits non-zero and names the file with the unresolved reference — add the
mapping to `rewrite_plugin_root()` in `install-antigravity.py`.
