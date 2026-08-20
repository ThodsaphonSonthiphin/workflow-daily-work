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


PROVENANCE_MIN = 0.70


def line_overlap(a_text, b_text):
    """Share of the smaller file's non-blank lines present in the other.

    Measured against the SMALLER side so that a copy which is a strict subset
    of the source - the common drift, a line dropped - scores 1.0 rather than
    being penalised for the source having grown.
    """
    a = set(line for line in a_text.splitlines() if line.strip())
    b = set(line for line in b_text.splitlines() if line.strip())
    if not a or not b:
        return 0.0
    return len(a & b) / float(min(len(a), len(b)))


def historical_hashes(path, limit=50):
    """Normalized hashes of this file's previous committed versions.

    A copy matching one of these is certainly ours, however far it has since
    fallen behind - the case line overlap alone would misjudge.

    IMPORTANT: An empty set means "no evidence found", not "confirmed no history".
    When git cannot answer (failed rev-parse or log), this function returns an
    empty set indistinguishably from "this file has no history". A copy that
    would have matched a historical version then gets graded by line overlap
    alone, and at PROVENANCE_MIN=0.70 can return UNRELATED — meaning the tool
    says nothing about a copy that is genuinely stale.

    Mitigation: The source-health gate (source_blockers) runs first and refuses
    the whole run when git cannot answer for this repository, blocking the tool
    before classify() is called. Holes: --allow-dirty-source bypasses the gate,
    and calling audit() directly (as tests do) has no gate at all.
    """
    directory = os.path.dirname(path)
    top = git_output(directory, "rev-parse", "--show-toplevel")
    if not top:
        return set()
    # Normalize both paths to resolve short forms and slashes consistently
    top = os.path.normpath(os.path.realpath(top))
    path_normalized = os.path.normpath(os.path.realpath(path))
    rel = os.path.relpath(path_normalized, top).replace(os.sep, "/")
    revs = git_output(top, "log", "--format=%H", "-n", str(limit), "--", rel)
    hashes = set()
    for rev in (revs or "").splitlines():
        try:
            blob = subprocess.run(
                ["git", "-C", top, "show", "%s:%s" % (rev, rel)],
                capture_output=True)
        except OSError:
            return hashes
        if blob.returncode == 0:
            hashes.add(content_hash(normalize(blob.stdout)))
    return hashes


def classify(src_bytes, copy_bytes, historical=()):
    """Grade one copy against the source. Returns (verdict, overlap).

    A name match alone never earns STALE (ADR 0107): provenance is confirmed
    from content, or the copy is somebody else's and we say nothing about it.
    """
    src = normalize(src_bytes)
    copy = normalize(copy_bytes)
    if content_hash(src) == content_hash(copy):
        return "IN SYNC", 1.0
    if content_hash(copy) in set(historical):
        return "STALE", 1.0
    overlap = line_overlap(src.decode("utf-8", "replace"),
                           copy.decode("utf-8", "replace"))
    if overlap >= PROVENANCE_MIN:
        return "STALE", overlap
    return "UNRELATED", overlap


WORKTREE_MARK = os.path.join(".claude", "worktrees")


def _under(path, parent):
    """Check if path is under parent, using the same canonicalization as _key."""
    key, root = _key(path), _key(parent)
    return key == root or key.startswith(root + os.sep)


def role_of(path, claude_home, agents_home, source_root):
    """What kind of distribution point this copy is. The role decides the
    repair, and whether a repair may be offered at all."""
    if _under(path, os.path.join(claude_home, "plugins", "cache")):
        return "cache"
    if os.path.normcase(WORKTREE_MARK) in _key(path):
        return "worktree"
    if _under(path, agents_home):
        return "agent-store"
    if _under(path, source_root):
        return "source"
    return "vendored"


def repair_for(role, copy_path, source_root):
    """What the runner should DO about this copy. Never a write into the
    cache (ADR 0104)."""
    if role == "cache":
        return ("none - the runtime maintains this snapshot. Edit the source "
                "at %s and let the next session refresh it. Never hand-patch "
                "the cache: a patched cache reports success while the real "
                "source stays old." % source_root)
    if role == "worktree":
        return ("none - this is another branch's checkout. Merge or rebase "
                "that branch; do not edit its files to match.")
    if role == "agent-store":
        return ("reinstall this skill for the agents that read the store, "
                "then re-run. Note that a skills `update` short-circuits on "
                "the source hash without checking this copy, so an update "
                "alone will not repair it.")
    if role == "source":
        return ("this is the source - no repair needed.")
    if role == "vendored":
        return ("edit %s in its own repo and commit it there - the copy is "
                "git-tracked by that project, so copying a file in would leave "
                "their tree dirty." % copy_path)
    raise ValueError("unknown role: %r" % role)


def claimed_install(claude_home, marketplace, plugin):
    """What the install manifest CLAIMS. Never evidence: the directory it
    names can be absent while every field says it exists."""
    path = os.path.join(claude_home, "plugins", "installed_plugins.json")
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError:
        return None
    entries = (data.get("plugins") or {}).get("%s@%s" % (plugin, marketplace))
    for entry in entries or []:
        install_path = entry.get("installPath") or ""
        return {"version": entry.get("version"),
                "install_path": install_path,
                "dir_exists": os.path.isdir(install_path)}
    return None


def agent_list_warning(agents_home):
    """The trap where a skills install succeeds for every agent except this
    one. It re-arms on the next install, so the check is unconditional."""
    lock = os.path.join(agents_home, ".skill-lock.json")
    if not os.path.isfile(lock):
        return None
    try:
        with open(lock, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError:
        return "the skills lock at %s is not valid JSON" % lock
    agents = data.get("lastSelectedAgents") or []
    if "claude-code" not in agents:
        return ("`claude-code` is missing from lastSelectedAgents in %s - a "
                "skills install will succeed for every other agent and report "
                "success while nothing lands for Claude Code." % lock)
    return None


def _cache_version(path, claude_home, marketplace, plugin):
    """The version segment of a cache-role path, when that path sits under
    THIS plugin's own cache tree
    (claude_home/plugins/cache/<marketplace>/<plugin>/<version>/...).

    Returns None when the path is a cache hit for something else entirely
    (a different marketplace or plugin that happens to share a skill name) -
    that case is graded the old way, unaffected by version comparison; it is
    not what "a superseded cache version" means.
    """
    base = os.path.join(claude_home, "plugins", "cache", marketplace, plugin)
    if not _under(path, base):
        return None
    rel = os.path.relpath(os.path.realpath(path), os.path.realpath(base))
    parts = rel.split(os.sep)
    return parts[0] if parts and parts[0] not in ("", os.curdir) else None


def audit(plugin, marketplace, claude_home, agents_home, extra_roots=()):
    """Measure every copy of `plugin` on this machine against its source.
    Reports; changes nothing."""
    registry = load_registry(claude_home)
    mkt_root = marketplace_root(registry, marketplace)
    source_root = plugin_root(mkt_root, plugin)
    skills = source_skills(source_root)
    if not skills:
        _die("plugin %r at %s has no skills/<name>/SKILL.md to compare"
             % (plugin, source_root))

    roots = derive_roots(registry, claude_home, agents_home)
    known = set(_key(r) for r in roots)
    for extra in extra_roots:          # additive, never a replacement
        if os.path.isdir(extra) and _key(extra) not in known:
            roots.append(os.path.abspath(extra))
            known.add(_key(extra))

    history = dict((name, historical_hashes(path))
                   for name, path in skills.items())

    # Only the cache directory matching the install manifest's CLAIMED
    # version is graded. Every other cached version is a historical
    # snapshot - being behind is its correct state, not drift - and grading
    # it would flag every skill added after that version shipped as a false
    # "STALE". If there is no usable claim (none recorded, or its directory
    # is absent), no cache directory can be graded, because there is no
    # reliable version to grade against.
    claim = claimed_install(claude_home, marketplace, plugin)
    claimed_version = claim["version"] if claim and claim["dir_exists"] else None
    cache_note = None
    if claimed_version is None:
        cache_note = ("cache directories are NOT graded: the install "
                      "manifest names no usable version (no claim, or its "
                      "claimed directory is absent).")

    rows = []
    superseded = 0
    for directory in scan_for_skill_dirs(roots, list(skills)):
        name = os.path.basename(directory)
        role = role_of(directory, claude_home, agents_home, source_root)
        if role == "cache":
            version = _cache_version(directory, claude_home, marketplace,
                                     plugin)
            if version is not None and version != claimed_version:
                superseded += 1
                rows.append({"path": directory, "skill": name, "role": role,
                             "verdict": "SUPERSEDED", "overlap": None,
                             "repair": ""})
                continue
        copy_file = os.path.join(directory, "SKILL.md")
        verdict, overlap = classify(read_normalized(skills[name]),
                                    read_normalized(copy_file),
                                    history.get(name, set()))
        rows.append({"path": directory, "skill": name, "role": role,
                     "verdict": verdict, "overlap": overlap,
                     "repair": "" if verdict != "STALE"
                               else repair_for(role, directory, source_root)})

    return {"rows": sorted(rows, key=lambda r: (r["role"], r["path"])),
            "source_root": source_root,
            "skills": sorted(skills),
            "claim": claim,
            "cache_note": cache_note,
            "superseded": superseded,
            "warning": agent_list_warning(agents_home)}


def report(result):
    """Print the human-readable audit report. Returns the count of
    actionable findings (STALE only), which main() uses for --strict."""
    print("source: %s" % result["source_root"])
    print("skills: %d (%s)" % (len(result["skills"]),
                               ", ".join(result["skills"])))
    claim = result["claim"]
    if claim:
        print("install manifest CLAIMS version %s at %s (directory %s) "
              "- a claim, not evidence"
              % (claim["version"], claim["install_path"],
                 "exists" if claim["dir_exists"] else "ABSENT"))
    if result.get("cache_note"):
        print(result["cache_note"])
    print("")
    grouped = {}
    for row in result["rows"]:
        grouped.setdefault(row["role"], []).append(row)
    for role in sorted(grouped):
        print("  [%s]" % role)
        for row in grouped[role]:
            overlap_text = ("  n/a" if row["overlap"] is None
                            else "%3.0f%%" % (row["overlap"] * 100))
            print("    %-9s %-24s overlap %s  %s"
                  % (row["verdict"], row["skill"], overlap_text, row["path"]))
            if row["repair"]:
                print("      fix: %s" % row["repair"])
        print("")
    stale = [r for r in result["rows"] if r["verdict"] == "STALE"]
    unrelated = [r for r in result["rows"] if r["verdict"] == "UNRELATED"]
    print("%d stale, %d unrelated (same name, different lineage - not ours), "
          "%d in sync"
          % (len(stale), len(unrelated),
             sum(1 for r in result["rows"] if r["verdict"] == "IN SYNC")))
    if result.get("superseded"):
        print("%d superseded cache director%s excluded (older than the "
              "claimed version, not graded)"
              % (result["superseded"], "y" if result["superseded"] == 1
                                       else "ies"))
    print("provenance threshold: %.0f%% line overlap. A verdict's overlap "
          "shows which side of it the call came from." % (PROVENANCE_MIN * 100))
    if result["warning"]:
        print("\nwarning: %s" % result["warning"])
    return len(stale)


def main(argv):
    parser = argparse.ArgumentParser(
        description="Find every copy of a plugin or skill and grade it.")
    parser.add_argument("--plugin", required=True)
    parser.add_argument("--marketplace", default=None,
                        help="defaults to the only marketplace listing the "
                             "plugin, if exactly one does")
    parser.add_argument("--claude-home",
                        default=os.path.expanduser("~/.claude"))
    parser.add_argument("--agents-home",
                        default=os.path.expanduser("~/.agents"))
    parser.add_argument("--root", action="append", default=[],
                        help="an extra scan root; additive, never a "
                             "replacement for the derived roots")
    parser.add_argument("--strict", action="store_true",
                        help="exit 1 when any copy is stale")
    parser.add_argument("--allow-dirty-source", action="store_true",
                        help="report against a source that is not clean; the "
                             "report is stamped ungraded")
    args = parser.parse_args(argv)

    marketplace = args.marketplace
    if marketplace is None:
        registry = load_registry(args.claude_home)
        owners = []
        for name in sorted(registry):
            root = marketplace_root(registry, name)
            manifest = os.path.join(root, ".claude-plugin",
                                    "marketplace.json")
            if not os.path.isfile(manifest):
                continue
            try:
                with open(manifest, encoding="utf-8") as f:
                    data = json.load(f)
            except ValueError:
                continue
            if any(p.get("name") == args.plugin
                   for p in data.get("plugins") or []):
                owners.append(name)
        if len(owners) != 1:
            _die("pass --marketplace: %d marketplaces list plugin %r (%s)"
                 % (len(owners), args.plugin, ", ".join(owners) or "none"))
        marketplace = owners[0]

    # The source-health gate runs BEFORE audit(), and this order is
    # load-bearing: historical_hashes() silently degrades to "no evidence
    # found" when git cannot answer for this repo, which would under-report
    # real drift if audit() ran against an untrustworthy source first.
    registry = load_registry(args.claude_home)
    source_root = plugin_root(marketplace_root(registry, marketplace),
                              args.plugin)
    blockers = source_blockers(source_root)
    if blockers:
        if not args.allow_dirty_source:
            sys.stderr.write(
                "cannot run: the source is not a trustworthy baseline, so "
                "every verdict would be graded against the wrong source.\n")
            for blocker in blockers:
                sys.stderr.write("  - %s\n" % blocker)
            sys.stderr.write("  re-run with --allow-dirty-source to report "
                             "anyway (the report is then ungraded).\n")
            return 2
        print("UNGRADED REPORT - the source is not clean:")
        for blocker in blockers:
            print("  - %s" % blocker)
        print("")

    result = audit(args.plugin, marketplace, args.claude_home,
                   args.agents_home, args.root)
    stale = report(result)
    return 1 if (stale and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
