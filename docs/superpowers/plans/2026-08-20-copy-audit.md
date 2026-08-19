# copy-audit Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a report-only checker that finds every copy of a plugin or skill on any machine and grades each against the source by CR-normalized hash.

**Architecture:** One stdlib-only Python module, `check_plugin_copies.py`, built as small pure functions that each take their inputs as parameters — never reading a hard-coded home directory — so tests point them at synthetic trees. A skill file wraps the script with the procedure and the traps. The script reports and exits; it never writes to any copy.

**Tech Stack:** Python 3 standard library only (`argparse`, `hashlib`, `json`, `os`, `subprocess`, `sys`). Tests are plain `assert` functions run by pytest or directly. No new dependencies.

**Spec:** [docs/superpowers/specs/2026-08-20-copy-audit-design.md](../specs/2026-08-20-copy-audit-design.md)

## Global Constraints

- **No machine-specific path may appear in the script.** No user name, drive, repo name or marketplace name. Every location is derived at run time from the registry or passed as a parameter. A test that only passes on the authoring machine is a failed test.
- **CR-normalize before every comparison** (ADR 0086). git stores LF, Windows checks out CRLF; raw byte equality carries no information.
- **Never write into the plugin cache tree** (ADR 0104). The script writes nothing anywhere, and a `cache` row never carries a write repair.
- **A name match alone never earns `STALE`** (ADR 0107). Provenance is confirmed from content or the verdict is `UNRELATED`.
- **Exit codes:** `0` clean, `1` findings exist *and* `--strict` was passed, `2` cannot run (which includes the source-health refusal).
- **Every home directory is an injectable parameter** (`claude_home`, `agents_home`), defaulting to the real one only in `main`.
- **Skill frontmatter `description:` is single-quoted on one line.** An unquoted colon-space silently drops the whole frontmatter and the skill disappears.
- **Skill text stays harness-neutral.** Name actions, not one harness's tool. `${CLAUDE_PLUGIN_ROOT}` only in the `/scripts/…` and `/references/…` shapes.
- **Python file style matches `check_vendored_superpowers.py`:** module-level functions, a module docstring naming the usage, no classes unless a real exception type is needed.

---

## File Structure

| File | Responsibility |
|---|---|
| `plugins/dev-workflows/scripts/check_plugin_copies.py` | the whole engine: resolve, gate, scan, classify, report |
| `plugins/dev-workflows/scripts/test_check_plugin_copies.py` | tests over synthetic trees, machine-independent |
| `plugins/dev-workflows/skills/copy-audit/SKILL.md` | the procedure and the traps |
| `PLAYBOOK.md` | one row for the new skill |
| `plugins/dev-workflows/.claude-plugin/plugin.json` | version bump |
| `.claude-plugin/marketplace.json` | matching version bump |

The engine is one file because its functions share the normalize/hash primitives and are each small; splitting it would scatter six ten-line functions across four files. It is expected to land near 300 lines, well inside what stays readable.

---

### Task 1: Primitives, registry loading, source resolution

**Files:**
- Create: `plugins/dev-workflows/scripts/check_plugin_copies.py`
- Test: `plugins/dev-workflows/scripts/test_check_plugin_copies.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: `normalize(data) -> bytes`, `content_hash(data) -> str`, `read_normalized(path) -> bytes`, `load_registry(claude_home) -> dict`, `marketplace_root(registry, marketplace) -> str`, `plugin_root(mkt_root, plugin) -> str`, `source_skills(plugin_root) -> dict[str, str]`. `load_registry`, `marketplace_root` and `plugin_root` call `sys.exit(2)` on any failure they cannot resolve.

- [ ] **Step 1: Write the failing tests**

```python
#!/usr/bin/env python3
"""Tests for check_plugin_copies.py.
Run: python test_check_plugin_copies.py   (or: pytest)"""
import json
import os
import sys
import tempfile

import pytest

from check_plugin_copies import (normalize, content_hash, read_normalized,
                                 load_registry, marketplace_root,
                                 plugin_root, source_skills)


def _write(path, text, eol="\n"):
    """Write text with an explicit line ending, creating parent dirs."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = text.replace("\r\n", "\n").replace("\n", eol)
    with open(path, "wb") as f:
        f.write(body.encode("utf-8"))


def _registry(claude_home, entries):
    path = os.path.join(claude_home, "plugins", "known_marketplaces.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entries, f)


def _marketplace(root, plugin, source):
    path = os.path.join(root, ".claude-plugin", "marketplace.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"name": "mkt", "plugins": [
            {"name": plugin, "source": source, "version": "1.0.0"}]}, f)


def test_normalize_collapses_crlf_only():
    assert normalize(b"a\r\nb\r\n") == b"a\nb\n"
    assert normalize(b"a\nb\n") == b"a\nb\n"
    assert normalize(b"a\rb") == b"a\rb"


def test_eol_flip_alone_does_not_change_the_hash():
    with tempfile.TemporaryDirectory() as d:
        crlf = os.path.join(d, "a", "SKILL.md")
        lf = os.path.join(d, "b", "SKILL.md")
        _write(crlf, "one\ntwo\n", eol="\r\n")
        _write(lf, "one\ntwo\n", eol="\n")
        assert open(crlf, "rb").read() != open(lf, "rb").read()
        assert content_hash(read_normalized(crlf)) == \
               content_hash(read_normalized(lf))


def test_missing_registry_exits_2():
    with tempfile.TemporaryDirectory() as d:
        with pytest.raises(SystemExit) as exc:
            load_registry(d)
        assert exc.value.code == 2


def test_malformed_registry_exits_2():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "plugins", "known_marketplaces.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("{not json")
        with pytest.raises(SystemExit) as exc:
            load_registry(d)
        assert exc.value.code == 2


def test_directory_source_resolves_to_the_repo_tree():
    with tempfile.TemporaryDirectory() as d:
        repo = os.path.join(d, "somerepo")
        os.makedirs(repo)
        reg = {"mkt": {"source": {"source": "directory", "path": repo},
                       "installLocation": repo}}
        assert marketplace_root(reg, "mkt") == repo


def test_github_source_resolves_to_the_marketplace_clone():
    clone = os.path.join("anywhere", "marketplaces", "mkt")
    reg = {"mkt": {"source": {"source": "github", "repo": "o/r"},
                   "installLocation": clone}}
    assert marketplace_root(reg, "mkt") == clone


def test_unknown_marketplace_exits_2():
    with pytest.raises(SystemExit) as exc:
        marketplace_root({}, "nope")
    assert exc.value.code == 2


def test_plugin_root_follows_the_marketplace_manifest():
    with tempfile.TemporaryDirectory() as d:
        _marketplace(d, "myplug", "./plugins/myplug")
        got = plugin_root(d, "myplug")
        assert got == os.path.normpath(os.path.join(d, "plugins", "myplug"))


def test_plugin_absent_from_the_manifest_exits_2():
    with tempfile.TemporaryDirectory() as d:
        _marketplace(d, "myplug", "./plugins/myplug")
        with pytest.raises(SystemExit) as exc:
            plugin_root(d, "other")
        assert exc.value.code == 2


def test_source_skills_finds_only_dirs_holding_a_skill_file():
    with tempfile.TemporaryDirectory() as d:
        _write(os.path.join(d, "skills", "alpha", "SKILL.md"), "a\n")
        _write(os.path.join(d, "skills", "beta", "SKILL.md"), "b\n")
        os.makedirs(os.path.join(d, "skills", "gamma"))
        _write(os.path.join(d, "skills", "delta", "notes.md"), "d\n")
        assert sorted(source_skills(d)) == ["alpha", "beta"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q > /tmp-out.txt 2>&1; echo "EXIT=$?"; cat /tmp-out.txt`

Redirect and check the bare command's code — a pipe would report the last command's status and make a red run read as green.

Expected: collection error, `ModuleNotFoundError: No module named 'check_plugin_copies'`.

- [ ] **Step 3: Write the minimal implementation**

```python
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


def load_registry(claude_home):
    """The marketplace registry. This is the only discovery root that is
    assumed to exist at a fixed place."""
    path = os.path.join(claude_home, "plugins", "known_marketplaces.json")
    if not os.path.isfile(path):
        _die("no marketplace registry at %s" % path)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except ValueError as exc:
        _die("the marketplace registry is not valid JSON (%s)" % exc)


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
    try:
        with open(manifest, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as exc:
        _die("the marketplace manifest is not valid JSON (%s)" % exc)
    for entry in data.get("plugins") or []:
        if entry.get("name") == plugin:
            return os.path.normpath(os.path.join(mkt_root, entry["source"]))
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q > out.txt 2>&1; echo "EXIT=$?"; tail -3 out.txt; rm out.txt`

Expected: 11 passed, EXIT=0.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/scripts/check_plugin_copies.py \
        plugins/dev-workflows/scripts/test_check_plugin_copies.py
git commit -m "feat(dev-workflows): copy-audit primitives and source resolution"
```

---

### Task 2: The source-health gate

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_plugin_copies.py`
- Test: `plugins/dev-workflows/scripts/test_check_plugin_copies.py`

**Interfaces:**
- Consumes: nothing from Task 1 beyond the module existing
- Produces: `git_output(repo, *args) -> str | None` (None when git fails or is absent), `source_blockers(plugin_root) -> list[str]`. An empty list means the source is trustworthy; a non-empty list is the refusal text, one blocker per line.

- [ ] **Step 1: Write the failing tests**

Append to `test_check_plugin_copies.py`, and add `source_blockers` and `git_output` to the import list at the top:

```python
import subprocess


def _git(repo, *args):
    subprocess.run(["git", "-C", repo] + list(args),
                   check=True, capture_output=True)


def _repo_with_plugin(d):
    """A real git repo holding plugins/myplug/skills/alpha/SKILL.md."""
    _git_init = ["git", "init", "-q", "-b", "main", d]
    subprocess.run(_git_init, check=True, capture_output=True)
    _git(d, "config", "user.email", "t@example.invalid")
    _git(d, "config", "user.name", "Test")
    _git(d, "config", "commit.gpgsign", "false")
    plug = os.path.join(d, "plugins", "myplug")
    _write(os.path.join(plug, "skills", "alpha", "SKILL.md"), "alpha v1\n")
    _git(d, "add", "-A")
    _git(d, "commit", "-q", "-m", "initial")
    return plug


def test_a_clean_source_has_no_blockers():
    with tempfile.TemporaryDirectory() as d:
        plug = _repo_with_plugin(d)
        assert source_blockers(plug) == []


def test_a_non_git_source_has_no_blockers():
    with tempfile.TemporaryDirectory() as d:
        plug = os.path.join(d, "plugins", "myplug")
        _write(os.path.join(plug, "skills", "alpha", "SKILL.md"), "a\n")
        assert source_blockers(plug) == []


def test_uncommitted_change_under_the_plugin_is_a_blocker():
    with tempfile.TemporaryDirectory() as d:
        plug = _repo_with_plugin(d)
        _write(os.path.join(plug, "skills", "alpha", "SKILL.md"), "alpha v2\n")
        blockers = source_blockers(plug)
        assert len(blockers) == 1
        assert "uncommitted" in blockers[0]


def test_an_uncommitted_change_elsewhere_is_not_a_blocker():
    with tempfile.TemporaryDirectory() as d:
        plug = _repo_with_plugin(d)
        _write(os.path.join(d, "README.md"), "unrelated\n")
        assert source_blockers(plug) == []


def test_a_branch_ahead_under_the_plugin_is_a_blocker():
    with tempfile.TemporaryDirectory() as d:
        plug = _repo_with_plugin(d)
        _git(d, "checkout", "-q", "-b", "feature")
        _write(os.path.join(plug, "skills", "alpha", "SKILL.md"), "alpha v2\n")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "ahead")
        _git(d, "checkout", "-q", "main")
        blockers = source_blockers(plug)
        assert len(blockers) == 1
        assert "feature" in blockers[0]
        assert "1 commit" in blockers[0]


def test_a_branch_ahead_only_outside_the_plugin_is_not_a_blocker():
    with tempfile.TemporaryDirectory() as d:
        plug = _repo_with_plugin(d)
        _git(d, "checkout", "-q", "-b", "docs-only")
        _write(os.path.join(d, "README.md"), "unrelated\n")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "docs")
        _git(d, "checkout", "-q", "main")
        assert source_blockers(plug) == []
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q -k "blocker or non_git" > out.txt 2>&1; echo "EXIT=$?"; tail -5 out.txt; rm out.txt`

Expected: ImportError on `source_blockers`.

- [ ] **Step 3: Write the minimal implementation**

```python
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


def source_blockers(root):
    """Reasons the source cannot be trusted as a baseline (ADR 0106).

    Empty list = trustworthy. Anything else and every downstream verdict
    would be graded against the wrong source, so the caller must refuse.
    """
    top = git_output(root, "rev-parse", "--show-toplevel")
    if not top:
        return []                      # not a git checkout: nothing to gate
    rel = os.path.relpath(root, top).replace(os.sep, "/")
    blockers = []

    dirty = git_output(top, "status", "--porcelain", "--", rel)
    if dirty:
        blockers.append(
            "uncommitted changes under %s (%d path(s)) - commit them first"
            % (rel, len(dirty.splitlines())))

    head = git_output(top, "rev-parse", "--abbrev-ref", "HEAD") or ""
    refs = git_output(top, "for-each-ref", "--format=%(refname:short)",
                      "refs/heads") or ""
    for ref in refs.splitlines():
        if ref == head:
            continue
        ahead = git_output(top, "rev-list", "--count",
                           "HEAD..%s" % ref, "--", rel)
        if ahead and ahead != "0":
            blockers.append(
                "branch %s is %s commit(s) ahead under %s - merge it first"
                % (ref, ahead, rel))
    return blockers
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q > out.txt 2>&1; echo "EXIT=$?"; tail -3 out.txt; rm out.txt`

Expected: 17 passed, EXIT=0.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/scripts/check_plugin_copies.py \
        plugins/dev-workflows/scripts/test_check_plugin_copies.py
git commit -m "feat(dev-workflows): copy-audit refuses to run against a stale source"
```

---

### Task 3: Derived scan roots and the scan

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_plugin_copies.py`
- Test: `plugins/dev-workflows/scripts/test_check_plugin_copies.py`

**Interfaces:**
- Consumes: `load_registry`'s dict shape from Task 1
- Produces: `PRUNE` (frozenset of directory names), `derive_roots(registry, claude_home, agents_home) -> list[str]`, `scan_for_skill_dirs(roots, names) -> list[str]` returning absolute directory paths sorted, each holding a `SKILL.md` and named after one of `names`.

- [ ] **Step 1: Write the failing tests**

Add `PRUNE`, `derive_roots` and `scan_for_skill_dirs` to the imports, then append:

```python
def test_derive_roots_takes_the_parent_of_a_directory_source():
    with tempfile.TemporaryDirectory() as d:
        parent = os.path.join(d, "code")
        repo = os.path.join(parent, "somerepo")
        claude = os.path.join(d, "claude")
        agents = os.path.join(d, "agents")
        for p in (repo, claude, agents):
            os.makedirs(p)
        reg = {"mkt": {"source": {"source": "directory", "path": repo},
                       "installLocation": repo}}
        roots = derive_roots(reg, claude, agents)
        assert os.path.abspath(parent) in roots
        assert os.path.abspath(claude) in roots
        assert os.path.abspath(agents) in roots


def test_derive_roots_ignores_a_github_source():
    with tempfile.TemporaryDirectory() as d:
        claude = os.path.join(d, "claude")
        agents = os.path.join(d, "agents")
        for p in (claude, agents):
            os.makedirs(p)
        reg = {"mkt": {"source": {"source": "github", "repo": "o/r"},
                       "installLocation": os.path.join(d, "clone")}}
        roots = derive_roots(reg, claude, agents)
        assert roots == [os.path.abspath(claude), os.path.abspath(agents)]


def test_derive_roots_drops_duplicates_and_missing_dirs():
    with tempfile.TemporaryDirectory() as d:
        parent = os.path.join(d, "code")
        os.makedirs(os.path.join(parent, "a"))
        os.makedirs(os.path.join(parent, "b"))
        reg = {"m1": {"source": {"source": "directory",
                                 "path": os.path.join(parent, "a")}},
               "m2": {"source": {"source": "directory",
                                 "path": os.path.join(parent, "b")}}}
        roots = derive_roots(reg, os.path.join(d, "gone"),
                             os.path.join(d, "also-gone"))
        assert roots == [os.path.abspath(parent)]


def test_scan_finds_matching_dirs_holding_a_skill_file():
    with tempfile.TemporaryDirectory() as d:
        _write(os.path.join(d, "x", "alpha", "SKILL.md"), "a\n")
        _write(os.path.join(d, "y", "deep", "alpha", "SKILL.md"), "a\n")
        _write(os.path.join(d, "z", "beta", "SKILL.md"), "b\n")
        os.makedirs(os.path.join(d, "w", "alpha"))          # no SKILL.md
        hits = scan_for_skill_dirs([d], ["alpha"])
        assert len(hits) == 2
        assert all(h.endswith("alpha") for h in hits)


def test_scan_honours_the_prune_list():
    with tempfile.TemporaryDirectory() as d:
        _write(os.path.join(d, "keep", "alpha", "SKILL.md"), "a\n")
        for pruned in sorted(PRUNE):
            _write(os.path.join(d, pruned, "alpha", "SKILL.md"), "a\n")
        hits = scan_for_skill_dirs([d], ["alpha"])
        assert len(hits) == 1
        assert "keep" in hits[0]


def test_scan_deduplicates_overlapping_roots():
    with tempfile.TemporaryDirectory() as d:
        _write(os.path.join(d, "x", "alpha", "SKILL.md"), "a\n")
        hits = scan_for_skill_dirs([d, os.path.join(d, "x")], ["alpha"])
        assert len(hits) == 1
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q -k "derive or scan" > out.txt 2>&1; echo "EXIT=$?"; tail -5 out.txt; rm out.txt`

Expected: ImportError on `derive_roots`.

- [ ] **Step 3: Write the minimal implementation**

```python
PRUNE = frozenset(["node_modules", ".git", "obj", "bin", "__pycache__",
                   ".venv"])


def _key(path):
    """Case-insensitive absolute key. Windows paths differ in drive-letter
    case between callers, so raw string comparison double-counts."""
    return os.path.normcase(os.path.abspath(path))


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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q > out.txt 2>&1; echo "EXIT=$?"; tail -3 out.txt; rm out.txt`

Expected: 23 passed, EXIT=0.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/scripts/check_plugin_copies.py \
        plugins/dev-workflows/scripts/test_check_plugin_copies.py
git commit -m "feat(dev-workflows): copy-audit derives its scan roots from the registry"
```

---

### Task 4: Classification by content provenance

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_plugin_copies.py`
- Test: `plugins/dev-workflows/scripts/test_check_plugin_copies.py`

**Interfaces:**
- Consumes: `normalize`, `content_hash`, `git_output` from Tasks 1-2
- Produces: `PROVENANCE_MIN` (float), `line_overlap(a_text, b_text) -> float`, `historical_hashes(path, limit=50) -> set[str]`, `classify(src_bytes, copy_bytes, historical=()) -> (verdict, overlap)` where verdict is one of `"IN SYNC"`, `"STALE"`, `"UNRELATED"`.

- [ ] **Step 1: Write the failing tests**

Add `PROVENANCE_MIN`, `line_overlap`, `historical_hashes`, `classify` to the imports, then append:

```python
def test_identical_content_is_in_sync():
    verdict, overlap = classify(b"one\ntwo\n", b"one\ntwo\n")
    assert verdict == "IN SYNC"
    assert overlap == 1.0


def test_crlf_only_difference_is_in_sync():
    verdict, _ = classify(b"one\ntwo\n", b"one\r\ntwo\r\n")
    assert verdict == "IN SYNC"


def test_one_missing_line_is_stale_not_unrelated():
    src = b"---\nname: alpha\ndescription: x\neffort: max\n---\nbody\n"
    copy = b"---\nname: alpha\ndescription: x\n---\nbody\n"
    verdict, overlap = classify(src, copy)
    assert verdict == "STALE"
    assert overlap == 1.0


def test_a_same_named_file_sharing_no_lineage_is_unrelated():
    src = b"---\nname: alpha\n---\nour body\n"
    copy = b"---\nname: alpha\n---\nsomebody else entirely\ndifferent\nlines\n"
    verdict, overlap = classify(src, copy)
    assert verdict == "UNRELATED"
    assert overlap < PROVENANCE_MIN


def test_matching_a_historical_hash_is_stale_even_with_low_overlap():
    src = b"completely\nrewritten\ncontent\n"
    copy = b"the\nold\nversion\n"
    old = content_hash(normalize(copy))
    verdict, _ = classify(src, copy, historical={old})
    assert verdict == "STALE"


def test_line_overlap_ignores_blank_lines():
    assert line_overlap("a\n\n\nb\n", "a\nb\n") == 1.0


def test_line_overlap_of_empty_input_is_zero():
    assert line_overlap("", "a\n") == 0.0
    assert line_overlap("a\n", "   \n") == 0.0


def test_historical_hashes_finds_a_previous_committed_version():
    with tempfile.TemporaryDirectory() as d:
        plug = _repo_with_plugin(d)
        target = os.path.join(plug, "skills", "alpha", "SKILL.md")
        first = content_hash(read_normalized(target))
        _write(target, "alpha v2\n")
        _git(d, "add", "-A")
        _git(d, "commit", "-q", "-m", "second")
        hashes = historical_hashes(target)
        assert first in hashes
        assert content_hash(normalize(b"alpha v2\n")) in hashes


def test_historical_hashes_of_a_non_git_path_is_empty():
    with tempfile.TemporaryDirectory() as d:
        target = os.path.join(d, "alpha", "SKILL.md")
        _write(target, "a\n")
        assert historical_hashes(target) == set()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q -k "classify or overlap or historical or stale or unrelated or in_sync" > out.txt 2>&1; echo "EXIT=$?"; tail -5 out.txt; rm out.txt`

Expected: ImportError on `classify`.

- [ ] **Step 3: Write the minimal implementation**

```python
PROVENANCE_MIN = 0.60


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
    """
    directory = os.path.dirname(path)
    top = git_output(directory, "rev-parse", "--show-toplevel")
    if not top:
        return set()
    rel = os.path.relpath(path, top).replace(os.sep, "/")
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q > out.txt 2>&1; echo "EXIT=$?"; tail -3 out.txt; rm out.txt`

Expected: 32 passed, EXIT=0.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/scripts/check_plugin_copies.py \
        plugins/dev-workflows/scripts/test_check_plugin_copies.py
git commit -m "feat(dev-workflows): copy-audit grades copies by content provenance"
```

---

### Task 5: Roles, repairs, claimed version, agent-list warning

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_plugin_copies.py`
- Test: `plugins/dev-workflows/scripts/test_check_plugin_copies.py`

**Interfaces:**
- Consumes: `_key` from Task 3
- Produces: `role_of(path, claude_home, agents_home, source_root) -> str` returning one of `"source"`, `"cache"`, `"worktree"`, `"agent-store"`, `"vendored"`; `repair_for(role, copy_path, source_root) -> str`; `claimed_install(claude_home, marketplace, plugin) -> dict | None` with keys `version`, `install_path`, `dir_exists`; `agent_list_warning(agents_home) -> str | None`.

- [ ] **Step 1: Write the failing tests**

Add `role_of`, `repair_for`, `claimed_install`, `agent_list_warning` to the imports, then append:

```python
def test_role_of_identifies_each_distribution_point():
    claude = os.path.join("C:", os.sep, "home", ".claude")
    agents = os.path.join("C:", os.sep, "home", ".agents")
    source = os.path.join("C:", os.sep, "repo", "plugins", "myplug")
    cache = os.path.join(claude, "plugins", "cache", "mkt", "myplug", "1.0.0",
                         "skills", "alpha")
    worktree = os.path.join("C:", os.sep, "repo", ".claude", "worktrees", "wt",
                            "plugins", "myplug", "skills", "alpha")
    store = os.path.join(agents, "skills", "alpha")
    inside = os.path.join(source, "skills", "alpha")
    other = os.path.join("C:", os.sep, "other", "repo", "skills", "alpha")
    assert role_of(cache, claude, agents, source) == "cache"
    assert role_of(worktree, claude, agents, source) == "worktree"
    assert role_of(store, claude, agents, source) == "agent-store"
    assert role_of(inside, claude, agents, source) == "source"
    assert role_of(other, claude, agents, source) == "vendored"


def test_a_cache_row_never_gets_a_write_repair():
    repair = repair_for("cache", "any/path", "any/source")
    assert "never hand-patch" in repair.lower()
    for forbidden in ("copy ", "cp ", "write "):
        assert forbidden not in repair.lower()


def test_a_vendored_repair_says_commit_in_that_repo():
    repair = repair_for("vendored", "other/repo/skills/alpha", "src")
    assert "commit" in repair.lower()


def test_an_agent_store_repair_warns_that_update_will_not_fix_it():
    repair = repair_for("agent-store", "store/alpha", "src")
    assert "update" in repair.lower()


def test_claimed_install_reports_a_missing_directory_as_a_claim():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "plugins", "installed_plugins.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"version": 2, "plugins": {"myplug@mkt": [
                {"scope": "user", "version": "9.9.9",
                 "installPath": os.path.join(d, "nope")}]}}, f)
        claim = claimed_install(d, "mkt", "myplug")
        assert claim["version"] == "9.9.9"
        assert claim["dir_exists"] is False


def test_claimed_install_is_none_when_the_manifest_is_absent():
    with tempfile.TemporaryDirectory() as d:
        assert claimed_install(d, "mkt", "myplug") is None


def test_agent_list_warning_fires_when_claude_code_is_missing():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, ".skill-lock.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"lastSelectedAgents": ["cursor", "codex"]}, f)
        warning = agent_list_warning(d)
        assert warning is not None
        assert "claude-code" in warning


def test_agent_list_warning_is_silent_when_claude_code_is_present():
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, ".skill-lock.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"lastSelectedAgents": ["cursor", "claude-code"]}, f)
        assert agent_list_warning(d) is None


def test_agent_list_warning_is_silent_without_a_lock_file():
    with tempfile.TemporaryDirectory() as d:
        assert agent_list_warning(d) is None
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q -k "role or repair or claimed or agent_list" > out.txt 2>&1; echo "EXIT=$?"; tail -5 out.txt; rm out.txt`

Expected: ImportError on `role_of`.

- [ ] **Step 3: Write the minimal implementation**

```python
WORKTREE_MARK = os.path.join(".claude", "worktrees")


def _under(path, parent):
    key, root = _key(path), _key(parent)
    return key == root or key.startswith(root + os.sep)


def role_of(path, claude_home, agents_home, source_root):
    """What kind of distribution point this copy is. The role decides the
    repair, and whether a repair may be offered at all."""
    if _under(path, os.path.join(claude_home, "plugins", "cache")):
        return "cache"
    if os.path.normcase(WORKTREE_MARK) in os.path.normcase(os.path.abspath(path)):
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
    return ("edit %s in its own repo and commit it there - the copy is "
            "git-tracked by that project, so copying a file in would leave "
            "their tree dirty." % copy_path)


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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q > out.txt 2>&1; echo "EXIT=$?"; tail -3 out.txt; rm out.txt`

Expected: 41 passed, EXIT=0.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/scripts/check_plugin_copies.py \
        plugins/dev-workflows/scripts/test_check_plugin_copies.py
git commit -m "feat(dev-workflows): copy-audit roles, repairs and manifest claims"
```

---

### Task 6: Audit assembly, report and exit codes

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_plugin_copies.py`
- Test: `plugins/dev-workflows/scripts/test_check_plugin_copies.py`

**Interfaces:**
- Consumes: every function from Tasks 1-5
- Produces: `audit(plugin, marketplace, claude_home, agents_home, extra_roots=()) -> dict` with keys `rows`, `source_root`, `skills`, `claim`, `warning`; `report(result) -> None`; `main(argv) -> int`. Each row is a dict with `path`, `skill`, `role`, `verdict`, `overlap`, `repair`.

- [ ] **Step 1: Write the failing tests**

Add `audit`, `report`, `main` to the imports, then append:

```python
def _machine(d):
    """A synthetic machine: a claude home, an agents home, and a repo holding
    a marketplace with one plugin and one skill."""
    claude = os.path.join(d, "home", ".claude")
    agents = os.path.join(d, "home", ".agents")
    code = os.path.join(d, "code")
    repo = os.path.join(code, "srcrepo")
    os.makedirs(claude)
    os.makedirs(agents)
    os.makedirs(repo)
    _marketplace(repo, "myplug", "./plugins/myplug")
    _write(os.path.join(repo, "plugins", "myplug", "skills", "alpha",
                        "SKILL.md"), "alpha v2\nshared\nlines\n")
    _registry(claude, {"mkt": {"source": {"source": "directory",
                                          "path": repo},
                               "installLocation": repo}})
    return claude, agents, code, repo


def test_audit_grades_a_matching_and_a_drifted_copy():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        _write(os.path.join(code, "consumer", "vendored", "alpha",
                            "SKILL.md"), "alpha v2\nshared\nlines\n")
        _write(os.path.join(agents, "skills", "alpha", "SKILL.md"),
               "alpha v1\nshared\nlines\n")
        result = audit("myplug", "mkt", claude, agents)
        by_role = dict((r["role"], r["verdict"]) for r in result["rows"])
        assert by_role["vendored"] == "IN SYNC"
        assert by_role["agent-store"] == "STALE"


def test_audit_never_grades_the_source_itself_as_stale():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        result = audit("myplug", "mkt", claude, agents)
        for row in result["rows"]:
            if row["role"] == "source":
                assert row["verdict"] == "IN SYNC"


def test_audit_reports_an_unrelated_same_named_skill():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        _write(os.path.join(code, "stranger", "alpha", "SKILL.md"),
               "nothing\nin\ncommon\nat\nall\n")
        result = audit("myplug", "mkt", claude, agents)
        strangers = [r for r in result["rows"] if "stranger" in r["path"]]
        assert len(strangers) == 1
        assert strangers[0]["verdict"] == "UNRELATED"


def test_audit_carries_the_agent_list_warning():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        with open(os.path.join(agents, ".skill-lock.json"), "w",
                  encoding="utf-8") as f:
            json.dump({"lastSelectedAgents": ["cursor"]}, f)
        result = audit("myplug", "mkt", claude, agents)
        assert "claude-code" in result["warning"]


def test_extra_roots_are_additive_not_a_replacement():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        elsewhere = os.path.join(d, "far", "away")
        _write(os.path.join(elsewhere, "alpha", "SKILL.md"),
               "alpha v2\nshared\nlines\n")
        _write(os.path.join(agents, "skills", "alpha", "SKILL.md"),
               "alpha v2\nshared\nlines\n")
        result = audit("myplug", "mkt", claude, agents,
                       extra_roots=[elsewhere])
        paths = " ".join(r["path"] for r in result["rows"])
        assert "far" in paths           # the extra root was searched
        assert ".agents" in paths       # and the derived roots still were


def test_main_exits_2_when_the_source_is_dirty():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        subprocess.run(["git", "init", "-q", "-b", "main", repo],
                       check=True, capture_output=True)
        _git(repo, "config", "user.email", "t@example.invalid")
        _git(repo, "config", "user.name", "Test")
        _git(repo, "config", "commit.gpgsign", "false")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "initial")
        _write(os.path.join(repo, "plugins", "myplug", "skills", "alpha",
                            "SKILL.md"), "edited\n")
        code_out = main(["--plugin", "myplug", "--marketplace", "mkt",
                         "--claude-home", claude, "--agents-home", agents])
        assert code_out == 2


def test_allow_dirty_source_continues_past_the_gate():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        subprocess.run(["git", "init", "-q", "-b", "main", repo],
                       check=True, capture_output=True)
        _git(repo, "config", "user.email", "t@example.invalid")
        _git(repo, "config", "user.name", "Test")
        _git(repo, "config", "commit.gpgsign", "false")
        _git(repo, "add", "-A")
        _git(repo, "commit", "-q", "-m", "initial")
        _write(os.path.join(repo, "plugins", "myplug", "skills", "alpha",
                            "SKILL.md"), "edited\n")
        code_out = main(["--plugin", "myplug", "--marketplace", "mkt",
                         "--claude-home", claude, "--agents-home", agents,
                         "--allow-dirty-source"])
        assert code_out == 0


def test_strict_turns_a_stale_copy_into_exit_1():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        _write(os.path.join(agents, "skills", "alpha", "SKILL.md"),
               "alpha v1\nshared\nlines\n")
        argv = ["--plugin", "myplug", "--marketplace", "mkt",
                "--claude-home", claude, "--agents-home", agents]
        assert main(argv) == 0
        assert main(argv + ["--strict"]) == 1


def test_a_clean_machine_exits_0_under_strict():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        argv = ["--plugin", "myplug", "--marketplace", "mkt",
                "--claude-home", claude, "--agents-home", agents, "--strict"]
        assert main(argv) == 0
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q -k "audit or main or strict or allow_dirty or extra_roots" > out.txt 2>&1; echo "EXIT=$?"; tail -5 out.txt; rm out.txt`

Expected: ImportError on `audit`.

- [ ] **Step 3: Write the minimal implementation**

```python
def audit(plugin, marketplace, claude_home, agents_home, extra_roots=()):
    """Measure every copy. Reports; changes nothing."""
    registry = load_registry(claude_home)
    mkt_root = marketplace_root(registry, marketplace)
    source_root = plugin_root(mkt_root, plugin)
    skills = source_skills(source_root)
    if not skills:
        _die("plugin %r at %s has no skills/<name>/SKILL.md to compare"
             % (plugin, source_root))

    roots = derive_roots(registry, claude_home, agents_home)
    for extra in extra_roots:          # additive, never a replacement
        if os.path.isdir(extra) and _key(extra) not in set(_key(r)
                                                           for r in roots):
            roots.append(os.path.abspath(extra))

    history = dict((name, historical_hashes(path))
                   for name, path in skills.items())

    rows = []
    for directory in scan_for_skill_dirs(roots, list(skills)):
        name = os.path.basename(directory)
        copy_file = os.path.join(directory, "SKILL.md")
        role = role_of(directory, claude_home, agents_home, source_root)
        verdict, overlap = classify(read_normalized(skills[name]),
                                    read_normalized(copy_file),
                                    history.get(name, set()))
        rows.append({"path": directory, "skill": name, "role": role,
                     "verdict": verdict, "overlap": overlap,
                     "repair": "" if verdict != "STALE"
                               else repair_for(role, directory, source_root)})

    for name, path in sorted(skills.items()):
        for directory in set(os.path.dirname(r["path"]) for r in rows):
            sibling = os.path.join(directory, name, "SKILL.md")
            present = any(r["skill"] == name and
                          _key(os.path.dirname(r["path"])) == _key(directory)
                          for r in rows)
            if not present and os.path.isdir(directory) and \
                    not os.path.exists(sibling):
                rows.append({"path": os.path.join(directory, name),
                             "skill": name,
                             "role": role_of(directory, claude_home,
                                             agents_home, source_root),
                             "verdict": "MISSING", "overlap": 0.0,
                             "repair": repair_for(
                                 role_of(directory, claude_home, agents_home,
                                         source_root),
                                 os.path.join(directory, name), source_root)})

    return {"rows": sorted(rows, key=lambda r: (r["role"], r["path"])),
            "source_root": source_root,
            "skills": sorted(skills),
            "claim": claimed_install(claude_home, marketplace, plugin),
            "warning": agent_list_warning(agents_home)}


def report(result):
    print("source: %s" % result["source_root"])
    print("skills: %d (%s)" % (len(result["skills"]),
                               ", ".join(result["skills"])))
    claim = result["claim"]
    if claim:
        print("install manifest CLAIMS version %s at %s (directory %s) "
              "- a claim, not evidence"
              % (claim["version"], claim["install_path"],
                 "exists" if claim["dir_exists"] else "MISSING"))
    print("")
    grouped = {}
    for row in result["rows"]:
        grouped.setdefault(row["role"], []).append(row)
    for role in sorted(grouped):
        print("  [%s]" % role)
        for row in grouped[role]:
            print("    %-9s %-24s overlap %3.0f%%  %s"
                  % (row["verdict"], row["skill"], row["overlap"] * 100,
                     row["path"]))
            if row["repair"]:
                print("      fix: %s" % row["repair"])
        print("")
    stale = [r for r in result["rows"] if r["verdict"] in ("STALE", "MISSING")]
    unrelated = [r for r in result["rows"] if r["verdict"] == "UNRELATED"]
    print("%d stale, %d unrelated (same name, different lineage - not ours), "
          "%d in sync"
          % (len(stale), len(unrelated),
             sum(1 for r in result["rows"] if r["verdict"] == "IN SYNC")))
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
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py -q > out.txt 2>&1; echo "EXIT=$?"; tail -3 out.txt; rm out.txt`

Expected: 50 passed, EXIT=0.

- [ ] **Step 5: Run it for real against this marketplace**

Run: `cd "plugins/dev-workflows/scripts" && python check_plugin_copies.py --plugin dev-workflows > real.txt 2>&1; echo "EXIT=$?"; cat real.txt`

Expected: a report naming the source as the repo working tree, cache rows for each cached version, and no crash. Read the output and confirm no row proposes writing into the cache. Then `rm real.txt`.

- [ ] **Step 6: Commit**

```bash
git add plugins/dev-workflows/scripts/check_plugin_copies.py \
        plugins/dev-workflows/scripts/test_check_plugin_copies.py
git commit -m "feat(dev-workflows): copy-audit report, exit codes and CLI"
```

---

### Task 7: The skill, the playbook row, the version bump

**Files:**
- Create: `plugins/dev-workflows/skills/copy-audit/SKILL.md`
- Modify: `PLAYBOOK.md`
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

**Interfaces:**
- Consumes: `check_plugin_copies.py`'s CLI from Task 6
- Produces: the user-facing skill. No code depends on it.

- [ ] **Step 1: Mint the version from the global max**

Run this before editing either manifest. A ref-only scan is not enough: an uncommitted bump in a working tree is invisible to it and mints a colliding number.

```bash
cd "<repo root>"
{
  git for-each-ref --format='%(refname)' refs/heads | while read r; do
    git show "$r:plugins/dev-workflows/.claude-plugin/plugin.json" 2>/dev/null
  done
  cat plugins/dev-workflows/.claude-plugin/plugin.json
  for w in .claude/worktrees/*/; do
    cat "$w/plugins/dev-workflows/.claude-plugin/plugin.json" 2>/dev/null
  done
} | grep -o '"version": *"[0-9.]*"' | grep -o '[0-9][0-9.]*' | sort -V | tail -1
```

Take the value printed, increment the minor, and use that in both manifests. Do not assume `0.46.0`.

- [ ] **Step 2: Write the skill**

Create `plugins/dev-workflows/skills/copy-audit/SKILL.md`. The `description` is single-quoted on one line — an unquoted colon-space silently drops the whole frontmatter and the skill vanishes from the list.

```markdown
---
name: copy-audit
description: 'Find every copy of a plugin or skill on this machine and prove which ones are stale. Use when the user asks to update every place / everywhere on this PC, check the plugin cache, confirm an edit actually went live, verify a skill is deployed, find drifted or vendored copies, or asks why a skill still behaves like the old version. Also use before shipping a plugin change that other repos vendor. It reports and never writes.'
effort: max
---

<what-to-do>

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

- `IN SYNC` - the bytes match. Nothing to do.
- `STALE` - a real copy of ours, behind. Repair it.
- `UNRELATED` - the same name from a different lineage. Not ours. Leave it
  alone and do not report it as drift.
- `MISSING` - a copy carrying a skill's siblings but not that skill.

Each verdict shows the line overlap it was decided on, so a borderline call is
visible rather than hidden inside a number.

## Step 4 - repair, per role

Every `STALE` row carries its own repair. The role decides it:

- **cache** - never hand-patch it. The runtime maintains this snapshot. Edit
  the source and let the next session refresh it. A patched cache reports
  success while the real source stays old, which is the single most expensive
  mistake in this area.
- **vendored** - the copy is git-tracked by another project. Edit it in that
  repo and commit there; copying a file in leaves their tree dirty.
- **agent-store** - reinstall for the agents that read the store. A skills
  `update` short-circuits on the source hash without checking the copy, so an
  update alone never repairs a drifted copy.
- **worktree** - another branch's checkout. Merge or rebase that branch;
  do not edit its files to match.

## Step 5 - prove it landed

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

</what-to-do>
```

- [ ] **Step 3: Validate the plugin loads**

Run: `cd "<repo root>" && claude plugin validate plugins/dev-workflows > out.txt 2>&1; echo "EXIT=$?"; cat out.txt; rm out.txt`

Expected: EXIT=0. A non-zero exit here usually means the frontmatter failed to parse — check the `description` is single-quoted on one line.

- [ ] **Step 4: Add the PLAYBOOK row**

Open `PLAYBOOK.md`, find the table the other dev-workflows skills sit in, and add one row in the same column order the neighbouring rows use. Read two adjacent rows first and match their shape exactly rather than assuming the columns. The row's content: the skill is `copy-audit`, it belongs to the wrap/verify part of the arc, and its one-line purpose is "find every copy of a plugin or skill on this machine and prove which are stale".

- [ ] **Step 5: Bump both manifests to the minted version**

Edit `plugins/dev-workflows/.claude-plugin/plugin.json` and the `dev-workflows` entry in `.claude-plugin/marketplace.json` to the version from Step 1. They must match — a mismatch is a repo-convention violation.

Verify both, and confirm the diff is only the version lines:

```bash
cd "<repo root>"
python -c "import json;print(json.load(open('plugins/dev-workflows/.claude-plugin/plugin.json',encoding='utf-8'))['version'])"
python -c "import json;d=json.load(open('.claude-plugin/marketplace.json',encoding='utf-8'));print([p['version'] for p in d['plugins'] if p['name']=='dev-workflows'])"
git diff --stat -w
```

Expected: the same version from both, and a diff touching only the two manifest lines plus the new files. A large diff on a manifest means the writer re-indented the file — revert and edit the single line instead.

- [ ] **Step 6: Run the whole suite**

Run: `cd "plugins/dev-workflows/scripts" && python -m pytest test_check_plugin_copies.py test_check_vendored_superpowers.py -q > out.txt 2>&1; echo "EXIT=$?"; tail -3 out.txt; rm out.txt`

Expected: EXIT=0, with the vendored-superpowers tests still passing — this task adds a skill directory under `skills/`, and that checker asserts things about that directory's contents.

- [ ] **Step 7: Re-verify the version is still free, then commit**

Another session can mint the same version while this one works. Re-run the Step 1 scan; if the max has moved, take the new max + 1 and redo Step 5.

```bash
git add plugins/dev-workflows/skills/copy-audit/SKILL.md \
        PLAYBOOK.md \
        plugins/dev-workflows/.claude-plugin/plugin.json \
        .claude-plugin/marketplace.json
git commit -m "feat(dev-workflows): copy-audit skill"
```

---

## Self-Review

**Spec coverage.** Source resolution → Task 1. Source-health gate → Task 2. Discovery and derived roots → Task 3. Classification and CR-normalization → Task 4. Report roles and repairs, the manifest-is-a-claim rule, the agent-list trap → Task 5. Report format, exit codes, `--strict`, `--allow-dirty-source` → Task 6. The skill, the playbook row, the version bump → Task 7. Every spec test-plan case appears as a named test.

**Two spec items deliberately not built as code.** The version-minting trap and the pipe/exit-code trap are process rules, not behaviours of this script, so they live in the skill text and in the plan's own run commands rather than in a function. The `install-antigravity.py` asymmetry is documented in the spec's Risks section and is not addressed here — it is a separate plugin's concern, and inventing coverage for it would widen this change without a decision behind it.

**Placeholders.** None. Every code step carries the actual code; Task 7 Step 4 describes a row rather than quoting one because the PLAYBOOK table's columns must be read from the file at the time — quoting a guessed column order would be worse than instructing the implementer to match its neighbours.

**Type consistency.** `classify` returns `(verdict, overlap)` everywhere it is used. `role_of` returns exactly the five strings `repair_for` branches on. `audit` returns the dict `report` reads, with row keys `path`/`skill`/`role`/`verdict`/`overlap`/`repair` used identically in Tasks 6's tests and implementation. `git_output` returns `str | None` and every caller treats `None` as "no information".

**One known rough edge.** The `MISSING` detection in Task 6 is the weakest part of the design: it infers a copy's "directory of skills" from the parent of discovered hits, which cannot see a consumer that vendors none of the plugin's skills. It is correct for the cases it can observe and silent otherwise. If Task 6's implementer finds it awkward, a simpler rule — report `MISSING` only for parents that already contributed at least one hit — is what the tests actually pin, and is acceptable.
