#!/usr/bin/env python3
"""check_plugin_copies.py - find every copy of a plugin or skill, and grade it.

Reports where a plugin or bare skill exists on THIS machine and whether each
copy matches the source. It CHANGES NOTHING: a person reads the report and
makes the repair it names (ADR 0104).

Nothing about any particular machine is hard-coded. Every location is derived
at run time from the marketplace registry, so the same code runs unchanged on
a machine it has never seen (ADR 0108).

Usage:
  python check_plugin_copies.py --plugin NAME [--marketplace NAME] [--strict]
  python check_plugin_copies.py --plugin NAME --root PATH [--root PATH ...]

Exit codes: 0 clean, 1 findings under --strict, 2 cannot run.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys


def normalize(data):
    """CR-normalize a byte string (ADR 0086). CRLF -> LF, nothing else."""
    return data.replace(b"\r\n", b"\n")


def content_hash(data):
    return hashlib.sha256(data).hexdigest()


def read_normalized(path):
    with open(path, "rb") as f:
        return normalize(f.read())


def _die(message):
    sys.stderr.write("cannot run: %s\n" % message)
    sys.exit(2)


def _load_json_or_die(path, what):
    """Load a JSON file or die with exit code 2. Catches both JSON and OS errors."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError) as exc:
        _die("%s is not valid JSON or is unreadable (%s)" % (what, exc))


def load_registry(claude_home):
    """The marketplace registry. This is the only discovery root that is
    assumed to exist at a fixed place."""
    path = os.path.join(claude_home, "plugins", "known_marketplaces.json")
    if not os.path.isfile(path):
        _die("no marketplace registry at %s" % path)
    return _load_json_or_die(path, "the marketplace registry")


def marketplace_root(registry, marketplace):
    """Where the marketplace's own tree lives.

    A `directory` source means the repo working tree IS the load path -
    editing that tree is the deploy, and the cache is only a snapshot.
    """
    entry = registry.get(marketplace)
    if entry is None:
        _die("no marketplace named %r in the registry (known: %s)"
             % (marketplace, ", ".join(sorted(registry)) or "none"))
    source = entry.get("source") or {}
    if source.get("source") == "directory" and source.get("path"):
        return source["path"]
    location = entry.get("installLocation")
    if not location:
        _die("marketplace %r records neither a directory source nor an "
             "installLocation" % marketplace)
    return location


def plugin_root(mkt_root, plugin):
    """The plugin's directory, read from the marketplace manifest rather than
    assumed to be plugins/<name>."""
    manifest = os.path.join(mkt_root, ".claude-plugin", "marketplace.json")
    if not os.path.isfile(manifest):
        _die("no marketplace manifest at %s" % manifest)
    data = _load_json_or_die(manifest, "the marketplace manifest")
    plugins = data.get("plugins") or []
    if not isinstance(plugins, list):
        _die("marketplace manifest %s: plugins must be a list, not %s"
             % (manifest, type(plugins).__name__))
    for entry in plugins:
        if entry.get("name") == plugin:
            source = entry.get("source")
            if not source:
                _die("marketplace manifest %s lists plugin %r with no source key"
                     % (manifest, plugin))
            return os.path.normpath(os.path.join(mkt_root, source))
    _die("marketplace manifest %s lists no plugin named %r" % (manifest, plugin))


def source_skills(root):
    """{skill name: path to its SKILL.md} for one plugin tree."""
    skills_dir = os.path.join(root, "skills")
    found = {}
    if not os.path.isdir(skills_dir):
        return found
    for name in sorted(os.listdir(skills_dir)):
        candidate = os.path.join(skills_dir, name, "SKILL.md")
        if os.path.isfile(candidate):
            found[name] = candidate
    return found


def _git_dir_above(path):
    """Check if a .git entry exists anywhere from path up to filesystem root.

    Returns True if found; False otherwise. Checks for existence, not
    directory-ness, because in a git worktree .git is a plain file, not a dir.
    """
    path = os.path.abspath(path)
    while True:
        git_candidate = os.path.join(path, ".git")
        if os.path.exists(git_candidate):
            return True
        parent = os.path.dirname(path)
        if parent == path:  # reached filesystem root
            return False
        path = parent


def git_output(repo, *args):
    """stdout of a git command, or None if git is absent or the command
    failed. A None return always means 'no information', never 'no'."""
    try:
        result = subprocess.run(["git", "-C", repo] + list(args),
                                capture_output=True, text=True)
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


PRUNE = frozenset(["node_modules", ".git", "obj", "bin", "__pycache__",
                   ".venv"])


def _key(path):
    """Case-insensitive absolute key for deduplication. Windows paths differ
    in drive-letter case and in the 8.3 short form (e.g., THODSA~1.SON)
    versus the long form (e.g., thodsaphon.sonthipin). This function uses
    realpath instead of abspath to collapse both forms to one canonical name.

    This choice is deliberate and load-bearing: without realpath, a --root
    given in short form would overlap a derived root in long form without
    dedup, and in Task 5, role classification would misclassify a cache path
    arriving in a different form as a vendored copy — which incorrectly
    carries a write repair forbidden for the cache. Do not simplify this back
    to abspath.
    """
    return os.path.normcase(os.path.realpath(path))


def derive_roots(registry, claude_home, agents_home):
    """Where to look, computed rather than configured (ADR 0108).

    A repo that vendors a plugin is overwhelmingly a sibling of the repo that
    publishes it, so the parent of each directory-sourced marketplace is the
    rule that finds vendored copies with no machine-specific input.
    """
    candidates = []
    for entry in registry.values():
        source = (entry or {}).get("source") or {}
        if source.get("source") == "directory" and source.get("path"):
            parent = os.path.dirname(os.path.normpath(source["path"]))
            if parent:
                candidates.append(parent)
    candidates.append(claude_home)
    candidates.append(agents_home)

    seen, roots = set(), []
    for candidate in candidates:
        if not os.path.isdir(candidate):
            continue
        key = _key(candidate)
        if key in seen:
            continue
        seen.add(key)
        roots.append(os.path.abspath(candidate))
    return roots


def scan_for_skill_dirs(roots, names):
    """Every directory named after one of `names` that holds a SKILL.md.

    Finds copies nobody registered - the reason a scan was chosen over a
    declared manifest (ADR 0105). Whether a hit is OURS is a separate
    question, answered from content by classify().
    """
    wanted = set(names)
    seen, hits = set(), []
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in PRUNE]
            if os.path.basename(dirpath) in wanted and "SKILL.md" in filenames:
                key = _key(dirpath)
                if key not in seen:
                    seen.add(key)
                    hits.append(os.path.abspath(dirpath))
    return sorted(hits)


def source_blockers(root):
    """Reasons the source cannot be trusted as a baseline (ADR 0106).

    Empty list = trustworthy. Anything else and every downstream verdict
    would be graded against the wrong source, so the caller must refuse.
    """
    top = git_output(root, "rev-parse", "--show-toplevel")
    if not top:
        # None means no information, so distinguish:
        # - genuinely not a git repo: return [] (nothing to gate)
        # - git present but refused to answer: return blocker (cannot verify)
        if _git_dir_above(root):
            return [
                "git could not determine the repository root at %s - "
                "refusing rather than reporting an unverified baseline" % root]
        return []                      # not a git checkout: nothing to gate
    # Normalize both paths to canonical form for relpath calculation.
    # Windows hands out 8.3 short names (e.g. THODSA~1.SON) for temp paths
    # while git returns the long form. Without realpath, os.path.relpath
    # would calculate a .. path that matches nothing, and every later
    # git command scoped to --<rel> would check a nonexistent path while
    # appearing to pass. This line is load-bearing.
    top_normalized = os.path.normpath(os.path.realpath(top))
    root_normalized = os.path.normpath(os.path.realpath(root))
    rel = os.path.relpath(root_normalized, top_normalized).replace(os.sep, "/")
    blockers = []

    dirty = git_output(top, "status", "--porcelain", "--", rel)
    if dirty is None:
        blockers.append(
            "git status could not run at %s - refusing rather than reporting "
            "an unverified baseline" % top)
    elif dirty:
        blockers.append(
            "uncommitted changes under %s (%d path(s)) - commit them first"
            % (rel, len(dirty.splitlines())))

    head = git_output(top, "rev-parse", "--abbrev-ref", "HEAD")
    if head is None:
        blockers.append(
            "git rev-parse could not run at %s - refusing rather than reporting "
            "an unverified baseline" % top)
    else:
        refs = git_output(top, "for-each-ref", "--format=%(refname:short)",
                          "refs/heads")
        if refs is None:
            blockers.append(
                "git for-each-ref could not run at %s - refusing rather than reporting "
                "an unverified baseline" % top)
        else:
            for ref in refs.splitlines():
                if ref == head:
                    continue
                ahead = git_output(top, "rev-list", "--count",
                                   "HEAD..%s" % ref, "--", rel)
                if ahead is None:
                    blockers.append(
                        "git rev-list could not run at %s - refusing rather than reporting "
                        "an unverified baseline" % top)
                    break
                elif ahead != "0":
                    blockers.append(
                        "branch %s is %s commit(s) ahead under %s - merge it first"
                        % (ref, ahead, rel))
    return blockers
