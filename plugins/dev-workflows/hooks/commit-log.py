#!/usr/bin/env python
"""
commit-log.py — dev-workflows PostToolUse hook (commit -> daily-state ## Log).

Fires after every Bash tool call (matcher "Bash" in hooks.json). When the repo's
HEAD has moved to a commit that is not yet in the log, it echoes that commit's
real subject into the repo's daily-state.md ## Log via `daily-state.py log`, so
every commit lands a worklog line at the repo root — readable by humans and any
agent.

WHY IT READS GIT INSTEAD OF THE COMMAND LINE. An earlier version parsed `-m`
values out of the command string, which produced three classes of wrong entry:
a `-m "$(cat <<'EOF' ...)"` message logged the raw shell substitution instead of
the text; a commit with no `-m` (`--amend --no-edit`, editor form) logged a
content-free "(commit)"; and any command merely *mentioning* the word commit
(`git log ... # show last commit`) logged a phantom entry. Reading `git log -1`
after the fact fixes all three, only records commits that actually happened, and
captures the final message even when a git hook rewrote it.

Entries are deduplicated by short SHA, so this stays idempotent: a failed commit
never moves HEAD and therefore logs nothing, and re-running a Bash call cannot
double-log.

HARD CONTRACT: this hook MUST NEVER block or slow a commit in a way that fails.
It does best-effort logging and ALWAYS exits 0 with no stdout. Every failure mode
(not a commit, not a git repo, git/python/PyYAML missing, daily-state.py error)
is swallowed silently. A missing log line is acceptable; a blocked commit is not.

Input: the PostToolUse JSON payload on stdin —
    {"tool_name": "Bash", "tool_input": {"command": "..."}, "cwd": "..."}
"""

import json
import os
import re
import subprocess
import sys

# Cheap pre-filter: substrings of commands that can move HEAD. Keeps the common
# case (every non-git Bash call) at zero subprocesses.
COMMIT_VERBS = ("commit", "merge", "rebase", "cherry-pick", "revert", "git am")

MAX_SUBJECT = 200


def _read_payload():
    """Parse the payload as UTF-8.

    Reads the raw buffer rather than `json.load(sys.stdin)`: on Windows sys.stdin
    decodes a pipe with the ANSI codepage (cp1252), which turned every non-ASCII
    character in a commit subject into mojibake (an em dash logged as three
    characters). json.loads on bytes always decodes UTF-8.
    """
    try:
        return json.loads(sys.stdin.buffer.read() or b"{}")
    except Exception:
        return {}


def _git(repo, *args):
    """Run a read-only git command; return stripped stdout, or None on any failure."""
    try:
        p = subprocess.run(
            ["git", "-C", repo] + list(args),
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=10,
        )
    except Exception:
        return None
    if p.returncode != 0:
        return None
    out = (p.stdout or "").strip()
    return out or None


def _repo_path(command, base_cwd):
    """Resolve which repo the command targeted.

    Order: an explicit `git -C <path>`, then a leading `cd <path> &&` (how an
    agent enters a worktree), else the payload's cwd. Only used for path
    resolution — never for reading the commit message.
    """
    try:
        import shlex
        tokens = shlex.split(command, posix=True)
    except Exception:
        tokens = command.split()

    for i, t in enumerate(tokens):
        if t == "-C" and i + 1 < len(tokens):
            p = tokens[i + 1]
            return p if os.path.isabs(p) else os.path.join(base_cwd, p)

    m = re.match(r"""\s*cd\s+(?:"([^"]+)"|'([^']+)'|(\S+))""", command)
    if m:
        p = m.group(1) or m.group(2) or m.group(3)
        return p if os.path.isabs(p) else os.path.join(base_cwd, p)

    return base_cwd


def _already_logged(target, short_sha):
    """True when this commit already has a line in the ## Log section."""
    try:
        with open(target, encoding="utf-8-sig") as f:
            return ("(%s)" % short_sha) in f.read()
    except Exception:
        return False  # unreadable/absent -> let the append attempt decide


def main():
    payload = _read_payload()
    if payload.get("tool_name") != "Bash":
        return
    command = (payload.get("tool_input") or {}).get("command", "") or ""
    if not any(v in command for v in COMMIT_VERBS):
        return

    base_cwd = payload.get("cwd") or os.getcwd()
    repo = _repo_path(command, base_cwd)

    root = _git(repo, "rev-parse", "--show-toplevel")
    if not root:
        return
    target = os.path.join(root, "daily-state.md")

    # The commit as git actually recorded it — including a message a git hook
    # rewrote after the command was issued.
    head = _git(repo, "log", "-1", "--format=%h%x00%s")
    if not head or "\x00" not in head:
        return
    short_sha, subject = head.split("\x00", 1)
    subject = " ".join(subject.split())  # collapse to one line, defensively
    if not short_sha or not subject:
        return
    if len(subject) > MAX_SUBJECT:
        subject = subject[:MAX_SUBJECT - 1].rstrip() + "…"

    if _already_logged(target, short_sha):
        return

    script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "scripts", "daily-state.py",
    )
    try:
        subprocess.run(
            [sys.executable, script, "log", "%s (%s)" % (subject, short_sha),
             "--path", target],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=10,
        )
    except Exception:
        return


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)  # ALWAYS allow the command — never block.
