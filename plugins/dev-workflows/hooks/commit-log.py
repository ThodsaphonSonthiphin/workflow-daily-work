#!/usr/bin/env python
"""
commit-log.py — dev-workflows PreToolUse hook (commit -> daily-state ## Log).

Fires on every Bash tool call (matcher "Bash" in hooks.json). When the command
is a `git commit`, it echoes the commit message into that repo's daily-state.md
## Log via `daily-state.py log`, so every commit lands a worklog line at the
repo root — independent of git history, readable by humans and any agent.

HARD CONTRACT: this hook MUST NEVER block or slow a commit in a way that fails.
It does best-effort logging and ALWAYS exits 0 with no stdout. Every failure
mode (not a commit, not a git repo, git/python/PyYAML missing, daily-state.py
error) is swallowed silently. A missing log line is acceptable; a blocked
commit is not.

Input: the PreToolUse JSON payload on stdin —
    {"tool_name": "Bash", "tool_input": {"command": "..."}, "cwd": "..."}
"""

import json
import os
import re
import sys


def _read_payload():
    try:
        return json.load(sys.stdin)
    except Exception:
        return {}


def _extract_messages(tokens):
    """Pull every -m / --message value out of a tokenized git-commit command.

    Handles: `-m X`, `--message X`, `--message=X`, `-mX`, and combined short
    clusters ending in m (e.g. `-am X`). A commit with title+body (two -m) is
    joined into one log line.
    """
    msgs = []
    i, n = 0, len(tokens)
    while i < n:
        t = tokens[i]
        if t in ("-m", "--message") and i + 1 < n:
            msgs.append(tokens[i + 1]); i += 2; continue
        if t.startswith("--message="):
            msgs.append(t[len("--message="):]); i += 1; continue
        if t.startswith("-m") and len(t) > 2 and not t.startswith("--"):
            msgs.append(t[2:]); i += 1; continue
        if re.match(r"^-[a-zA-Z]*m$", t) and i + 1 < n:  # e.g. -am, -sm
            msgs.append(tokens[i + 1]); i += 2; continue
        i += 1
    return msgs


def _repo_path(tokens, base_cwd):
    """Resolve which repo the commit targets: a `-C <path>` if present, else cwd."""
    for i, t in enumerate(tokens):
        if t == "-C" and i + 1 < len(tokens):
            p = tokens[i + 1]
            return p if os.path.isabs(p) else os.path.join(base_cwd, p)
    return base_cwd


def main():
    payload = _read_payload()
    if payload.get("tool_name") != "Bash":
        return
    command = (payload.get("tool_input") or {}).get("command", "") or ""
    # Cheap pre-filter: skip the vast majority of Bash calls without parsing.
    if "commit" not in command:
        return

    import shlex
    import subprocess

    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()
    # Token-level check (handles quoted paths with spaces, compound commands).
    if "git" not in tokens or "commit" not in tokens:
        return

    base_cwd = payload.get("cwd") or os.getcwd()
    repo = _repo_path(tokens, base_cwd)
    message = " — ".join(m for m in _extract_messages(tokens) if m).strip() or "(commit)"

    # Resolve the repo's git root → daily-state.md (pass --path so daily-state.py
    # doesn't depend on this process's cwd).
    try:
        root = subprocess.run(
            ["git", "-C", repo, "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return
    if root.returncode != 0 or not root.stdout.strip():
        return
    target = os.path.join(root.stdout.strip(), "daily-state.md")

    script = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "scripts", "daily-state.py",
    )
    try:
        subprocess.run(
            [sys.executable, script, "log", message, "--path", target],
            capture_output=True, text=True, timeout=10,
        )
    except Exception:
        return


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)  # ALWAYS allow the commit — never block.
