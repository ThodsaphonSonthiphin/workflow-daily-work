---
name: copy-audit
description: 'Find every copy of a plugin or skill on this machine and prove which ones are stale. Use when the user asks to update every place / everywhere on this PC, check the plugin cache, confirm an edit actually went live, verify a skill is deployed, find drifted or vendored copies, or asks why a skill still behaves like the old version. Also use before shipping a plugin change that other repos vendor. It reports and never writes.'
effort: max
---

# Copy Audit

A plugin exists in more places than anyone tracks: the repo that publishes it,
the runtime cache, copies vendored into other repos, and per-agent skill
stores. They drift silently, and every signal that looks like proof is not one.

Run the audit, read it, and repair what it names. Never repair by guessing.

## Step 1 - run the audit

Run the checker with the plugin's name. Redirect to a file and check the bare
command's exit code; a pipe reports the last command's status, which turns a
failed run into an apparent success.

    python ${CLAUDE_PLUGIN_ROOT}/scripts/check_plugin_copies.py --plugin NAME > audit.txt 2>&1
    echo "EXIT=$?"

Exit 2 means it refused to run. That is a result, not a failure: read the
blocker it names, clear it, and run again.

## Step 2 - if it refuses, clear the blocker first

The audit refuses when the source is not a trustworthy baseline - uncommitted
changes under the plugin, or a branch holding commits the checked-out branch
lacks. Grading copies against a stale source reports them current when they
merely match an obsolete source, which is worse than no report.

Commit or merge what it names, then re-run. Use `--allow-dirty-source` only
when you have already accepted the baseline; the report is then stamped
ungraded and must not be quoted as proof of anything.

## Step 3 - read the verdicts

There are exactly three:

- `IN SYNC` - the CR-normalized bytes match. Nothing to do.
- `STALE` - a real copy of ours (provenance confirmed by content, not just by
  name), and behind. Repair it.
- `UNRELATED` - the same name, but a different lineage - provenance was never
  confirmed. Not ours. Leave it alone and do not report it as drift.

Each row shows the line overlap the call was decided on, so a borderline
verdict is visible rather than hidden inside a number.

## Step 4 - two exclusions that are not missing rows

The audit removes two categories from grading entirely, before either verdict
above can apply, and prints a labelled count for each instead of a row:

- **Superseded cache version directories** - only the one cache directory
  matching the version the install manifest currently claims is graded. Older
  version directories under the same plugin's cache tree are historical
  snapshots; being behind is their correct state, not drift.
- **Backup snapshots** - anything under the Claude home's `backups` directory
  is excluded. A dated backup is supposed to be behind; grading it would tell
  you to "edit and commit" a directory that usually is not even a repo.

If a report says "N superseded cache directories excluded" or "N backup
snapshots excluded," those copies were deliberately left out, not missed.

## Step 5 - repair, per role

Every `STALE` row carries its own repair. The role decides it:

- **cache** - never hand-patch it. The runtime maintains this snapshot. Edit
  the source and let the next session refresh it. A patched cache reports
  success while the real source stays old, which is the single most expensive
  mistake in this area.
- **vendored** - what to do depends on whether a `.git` exists above the copy:
  - if one does, the copy is git-tracked by that project: edit it in that
    repo and commit there. Copying a file in would leave their tree dirty.
  - if none does, there is no repo behind it to keep in sync with: edit it
    in place.
- **agent-store** - reinstall for the agents that read the store. A skills
  `update` short-circuits on the source hash without checking the copy, so an
  update alone never repairs a drifted copy.
- **worktree** - another branch's checkout. Merge or rebase that branch;
  do not edit its files to match.

## Step 6 - prove it landed

Re-run the audit. Do not accept any of these as proof instead:

- the install manifest naming the new version - it can name a version, an
  install path and a commit while the directory was never created
- "I restarted" - that says nothing about a directory outside the load path
- two version numbers matching - that proves the numbers match, not the bytes

The only proof is the hash, which is what re-running takes.

## What this skill will not do

It does not write to any copy. The correct action differs per role and two of
the roles must never be written to at all, so the audit reports and a person
repairs.
