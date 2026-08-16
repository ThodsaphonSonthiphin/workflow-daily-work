# Vendored-superpowers Resync Checker Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a report-only checker that mechanically guards the 21 vendored `superpowers` files, so a broken route or a silent upstream change is found by a command instead of by a reviewer who happens to look.

**Architecture:** One Python script in `plugins/dev-workflows/scripts/`, following the report/`--strict`/exit-0-1-2 convention `check_doc_provenance.py` already sets in that directory. All state it compares against lives in one JSON manifest under `references/`; the script holds the rules, the manifest holds the readings. Every byte comparison is CR-normalized first. A local mode (default, offline) answers "did our copies change?"; `--upstream-dir` answers "did upstream move?".

**Tech Stack:** Python 3.13, stdlib only (`argparse`, `hashlib`, `json`, `os`, `re`, `sys`). No PyYAML, no network, no third-party packages. Tests are plain functions runnable under pytest 9.0.3 **or** the file's own `__main__` runner.

**Spec:** [docs/superpowers/specs/2026-08-16-vendored-superpowers-resync-checker-design.md](../specs/2026-08-16-vendored-superpowers-resync-checker-design.md)

## Global Constraints

- **The program writes no file, under any flag.** `--emit-manifest` prints to **stdout**; the runner redirects. This preserves ADR 0075's "reports and changes nothing".
- **CR-normalize before every hash and every comparison** (ADR 0086). `data.replace(b"\r\n", b"\n")`, on both sides, always. Measured: 21 of 21 working-tree files are CRLF, 0 of 21 equal their own committed blob.
- **No count is hard-coded in the program.** Not 21, not 13, not 8, not 2, not 6. Every set and every number is read from the manifest or derived from it. Assert that a *set* matches, never that its size equals a literal.
- **Never glob `skills/sp-*` to find the copies.** That collects 24 files, because `sp-grill-with-doc` wears the `sp-` prefix and is **not** a vendored copy. The manifest's explicit file list is the only source.
- **Stdlib only.** `check_doc_provenance.py` needs PyYAML; this program must not.
- **Tests take `tmp_path=None` as a default argument** and use `tempfile.TemporaryDirectory()` inside, matching `test_check_doc_provenance.py`. A test that requires a pytest fixture breaks the `__main__` runner.
- **UTF-8 stdout.** `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` in `main`. Three permitted lines carry em-dashes; a Windows cp1252 console crashes while printing a finding without this.
- **Run scripts by type:** `.py` → `python`. Repo root is `c:\Repo2\workflow daily work`. Open each shell call with an absolute `cd` to the repo root.
- **Every command block in this plan is bash (Git Bash), not PowerShell.** `&&` is a parser error in PowerShell 5.1, and `$?` after a pipe reports the last command in the pipe, not the one that mattered. CLAUDE.md's "use PowerShell syntax" governs the repo's own scripts, not these steps.
- **Never redirect `--emit-manifest` onto the manifest it reads.** The shell truncates the target *before* the program starts, so every hand-written key reads as absent and is lost silently. Emit to a temp file, then move it into place.
- **Windows/PowerShell repo, CRLF working tree.** When creating a Markdown file, write CRLF to match its neighbours; verify with a byte count after writing, because an EOL flip is invisible in `git diff --stat`.

---

## File Structure

| file | responsibility |
|---|---|
| `plugins/dev-workflows/scripts/check_vendored_superpowers.py` | the whole program: manifest loading, the six local checks, the four upstream checks, `--emit-manifest`, reporting, exit codes |
| `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py` | the paired test — 19 synthetic cases plus one live regression against the real tree |
| `plugins/dev-workflows/references/vendored-superpowers.json` | the manifest: one upstream sha, 21 files with state + hash, the permit list, the qualified-ref census, routed/unrouted prompts, the frozen set, the trap config |
| `plugins/dev-workflows/references/resync-superpowers.md` | the human procedure: the six rewrite classes and the three traps, with **no line numbers** |
| `plugins/dev-workflows/.claude-plugin/plugin.json` | version `0.38.0` → `0.39.0` |
| `.claude-plugin/marketplace.json` | the same version, kept in sync |
| `CLAUDE.md` | one pointer line so the checker is discoverable |

One module, not several: the checks share the manifest, the CR-normalizing reader and the finding shape, and splitting them would spread that trio across files that always change together.

---

### Task 1: Module foundation — CR-normalizing reader, hashing, manifest loading, exit 2

**Files:**
- Create: `plugins/dev-workflows/scripts/check_vendored_superpowers.py`
- Test: `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`

**Interfaces:**
- Consumes: nothing (first task)
- Produces: `normalize(data: bytes) -> bytes`, `read_normalized(path: str) -> bytes`, `content_hash(data: bytes) -> str`, `finding(check: str, path: str, message: str, repair: str) -> dict`, `load_manifest(path: str) -> dict`, `copied_skill_dirs(manifest) -> list[str]`, `upstream_skill_names(manifest) -> list[str]`, `main(argv: list[str]) -> int`, and the module constants `HERE`, `PLUGIN_ROOT`, `DEFAULT_MANIFEST`, `DEFAULT_ROOT`, `REQUIRED_KEYS`

- [ ] **Step 1: Write the failing test**

Create `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`:

```python
#!/usr/bin/env python3
"""Tests for check_vendored_superpowers.py.
Run: python test_check_vendored_superpowers.py   (or: pytest)"""
import json
import os
import sys
import tempfile

from check_vendored_superpowers import (normalize, read_normalized,
                                        content_hash, load_manifest,
                                        copied_skill_dirs,
                                        upstream_skill_names, main)


def _write(path, text, eol="\n"):
    """Write text with an explicit line ending, creating parent dirs."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    body = text.replace("\r\n", "\n").replace("\n", eol)
    with open(path, "wb") as f:
        f.write(body.encode("utf-8"))


def test_normalize_collapses_crlf_only():
    assert normalize(b"a\r\nb\r\n") == b"a\nb\n"
    assert normalize(b"a\nb\n") == b"a\nb\n"
    assert normalize(b"a\rb") == b"a\rb"      # a lone CR is not an EOL here


def test_same_content_hashes_equal_across_eol(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        crlf = os.path.join(d, "crlf.md")
        lf = os.path.join(d, "lf.md")
        _write(crlf, "line one\nline two\n", eol="\r\n")
        _write(lf, "line one\nline two\n", eol="\n")
        assert open(crlf, "rb").read() != open(lf, "rb").read()
        assert content_hash(read_normalized(crlf)) == \
               content_hash(read_normalized(lf))


def test_copied_dirs_and_upstream_names_come_from_the_manifest():
    m = {"copy_set": {"files": [
        {"path": "sp-alpha/SKILL.md", "upstream_path": "alpha/SKILL.md"},
        {"path": "sp-alpha/extra.md", "upstream_path": "alpha/extra.md"},
        {"path": "sp-beta/SKILL.md", "upstream_path": "beta/SKILL.md"}]}}
    assert copied_skill_dirs(m) == ["sp-alpha", "sp-beta"]
    assert upstream_skill_names(m) == ["alpha", "beta"]


def test_missing_manifest_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        assert main(["--manifest", os.path.join(d, "nope.json"),
                     "--root", d]) == 2


def test_malformed_manifest_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.json")
        with open(p, "w", encoding="utf-8") as f:
            f.write("{not json")
        assert main(["--manifest", p, "--root", d]) == 2


def test_manifest_missing_a_required_key_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"upstream": {}}, f)
        assert main(["--manifest", p, "--root", d]) == 2


TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"{len(TESTS) - failed}/{len(TESTS)} passed")
    sys.exit(1 if failed else 0)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: FAIL — `ModuleNotFoundError: No module named 'check_vendored_superpowers'`

- [ ] **Step 3: Write minimal implementation**

Create `plugins/dev-workflows/scripts/check_vendored_superpowers.py`:

```python
#!/usr/bin/env python3
"""check_vendored_superpowers.py - the vendored-superpowers resync checker.

Reports drift in this marketplace's vendored copies of the upstream
`superpowers` skills. It CHANGES NOTHING: a person makes the repairs it names
and re-runs it until it exits 0 (ADR 0075).

Two modes:
  local (default)    Has anything changed OUR copies since they were vendored?
  --upstream-dir P   Has upstream moved, and which of the copied files changed?
                     P is the upstream PLUGIN ROOT (the directory holding
                     skills/), because one trap scans hooks/ and scripts/ too.

Every byte comparison is CR-normalized first (ADR 0086). git stores LF blobs
and Windows checks out CRLF, so raw bytes carry no information here: 0 of the
21 working-tree files equal their own committed blob.

Nothing is hard-coded about the copy set - not its size, not the skill names,
not the permitted lines. All of it is read from the manifest, so an intended
change is a manifest edit and never a code edit.

Usage:
  python check_vendored_superpowers.py [--strict]
  python check_vendored_superpowers.py --upstream-dir PATH [--strict]
  python check_vendored_superpowers.py --emit-manifest --upstream-dir PATH > new.json

Report mode (default): prints findings, exit 0. --strict makes any finding
exit 1. Exit 2 = cannot run.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
DEFAULT_MANIFEST = os.path.join(PLUGIN_ROOT, "references",
                                "vendored-superpowers.json")
DEFAULT_ROOT = os.path.join(PLUGIN_ROOT, "skills")

REQUIRED_KEYS = ("upstream", "copy_set", "permit_list", "qualified_refs",
                 "routing_marker", "routed_prompts", "unrouted_prompts",
                 "frozen", "upstream_traps")


def normalize(data):
    """CR-normalize a byte string (ADR 0086). CRLF -> LF, nothing else."""
    return data.replace(b"\r\n", b"\n")


def read_normalized(path):
    with open(path, "rb") as f:
        return normalize(f.read())


def read_text(path):
    return read_normalized(path).decode("utf-8", "replace")


def content_hash(data):
    return hashlib.sha256(data).hexdigest()


def finding(check, path, message, repair):
    """One reported problem. `repair` says what the runner should DO."""
    return {"check": check, "path": path, "message": message, "repair": repair}


def load_manifest(path):
    """Read the manifest. Raises ValueError if it cannot be trusted."""
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        raise ValueError("manifest not found: %s" % path)
    except json.JSONDecodeError as e:
        raise ValueError("manifest is not valid JSON: %s" % e)
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    missing = [k for k in REQUIRED_KEYS if k not in manifest]
    if missing:
        raise ValueError("manifest is missing required key(s): %s"
                         % ", ".join(missing))
    return manifest


def copied_skill_dirs(manifest):
    """The vendored directory names, FROM THE MANIFEST - never a glob.

    A glob of `sp-*` also collects sp-grill-with-doc, which carries the prefix
    but is not a vendored copy (ADR 0071)."""
    return sorted({f["path"].split("/")[0]
                   for f in manifest["copy_set"]["files"]})


def upstream_skill_names(manifest):
    """The upstream short names, derived from the 1:1 path mapping."""
    return sorted({f["upstream_path"].split("/")[0]
                   for f in manifest["copy_set"]["files"]})


def main(argv):
    ap = argparse.ArgumentParser(
        description="Report drift in the vendored superpowers copies.")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--root", default=DEFAULT_ROOT,
                    help="the skills/ directory holding the copies")
    ap.add_argument("--upstream-dir", default=None,
                    help="upstream plugin root (the directory holding skills/)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if there is any finding")
    ap.add_argument("--emit-manifest", action="store_true",
                    help="print a freshly computed manifest to stdout")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover
        pass

    try:
        manifest = load_manifest(args.manifest)
    except ValueError as e:
        print("ERROR: %s" % e)
        return 2

    findings = []
    print("OK: manifest loaded (%d files declared)."
          % len(manifest["copy_set"]["files"]))
    return 1 if (findings and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: PASS — `6/6 passed`

- [ ] **Step 5: Commit**

```bash
cd "c:/Repo2/workflow daily work" && git add plugins/dev-workflows/scripts/check_vendored_superpowers.py plugins/dev-workflows/scripts/test_check_vendored_superpowers.py && git commit -m "feat(dev-workflows): resync checker foundation - CR-normalized reads and manifest loading (ADR 0075, 0086)"
```

---

### Task 2: Checks 1, 2 and 6 — copy-set completeness, hashes, and the frozen set

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_vendored_superpowers.py`
- Test: `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`

**Interfaces:**
- Consumes: `read_normalized`, `content_hash`, `finding`, `copied_skill_dirs`, `load_manifest` (Task 1)
- Produces: `check_copy_set(root, manifest) -> list[dict]`, `check_hashes(root, manifest) -> list[dict]`, `check_frozen(root, manifest) -> list[dict]`

- [ ] **Step 1: Write the failing test**

Add to `test_check_vendored_superpowers.py`, above the `TESTS = [...]` line. Also extend the import at the top of the file to:

```python
from check_vendored_superpowers import (normalize, read_normalized,
                                        content_hash, load_manifest,
                                        copied_skill_dirs,
                                        upstream_skill_names, main,
                                        check_copy_set, check_hashes,
                                        check_frozen)
```

```python
def _tiny_tree(d):
    """A miniature copy set: two vendored skills, one non-copy that wears the
    sp- prefix, one frozen file. Returns (root, manifest)."""
    root = os.path.join(d, "skills")
    files = {
        "sp-alpha/SKILL.md": "---\nname: sp-alpha\n---\nbody\n",
        "sp-alpha/prompt.md": "Load the `scrutinize-dispatch` skill.\n",
        "sp-beta/SKILL.md": "second skill, no bare names\n",
        "sp-grill-with-doc/SKILL.md": "not a copy - must be ignored\n",
        "frozen/SKILL.md": "frozen body\n",
    }
    for rel, text in files.items():
        _write(os.path.join(root, rel), text, eol="\r\n")   # CRLF on purpose

    def h(rel):
        return content_hash(read_normalized(os.path.join(root, rel)))

    manifest = {
        "upstream": {"url": "https://example.invalid/x", "sha": "0" * 40},
        "copy_set": {"files": [
            {"path": "sp-alpha/SKILL.md", "upstream_path": "alpha/SKILL.md",
             "state": "edited", "sha256": h("sp-alpha/SKILL.md")},
            {"path": "sp-alpha/prompt.md", "upstream_path": "alpha/prompt.md",
             "state": "edited", "sha256": h("sp-alpha/prompt.md")},
            {"path": "sp-beta/SKILL.md", "upstream_path": "beta/SKILL.md",
             "state": "verbatim", "sha256": h("sp-beta/SKILL.md")}]},
        "permit_list": [],
        "qualified_refs": {},
        "routing_marker": "scrutinize-dispatch",
        "routed_prompts": ["sp-alpha/prompt.md"],
        "unrouted_prompts": [],
        "frozen": [{"path": "frozen/SKILL.md", "sha256": h("frozen/SKILL.md"),
                    "why": "owner constraint"}],
        "upstream_traps": {},
    }
    return root, manifest


def test_clean_tiny_tree_has_no_findings(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        assert check_copy_set(root, m) == []
        assert check_hashes(root, m) == []
        assert check_frozen(root, m) == []


def test_edited_copy_is_flagged_by_hash(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        _write(os.path.join(root, "sp-beta/SKILL.md"), "tampered\n", eol="\r\n")
        out = check_hashes(root, m)
        assert len(out) == 1
        assert out[0]["path"] == "sp-beta/SKILL.md"


def test_eol_flip_alone_is_not_a_finding(tmp_path=None):
    """ADR 0086: the same content rewritten LF instead of CRLF must be clean."""
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        _write(os.path.join(root, "sp-beta/SKILL.md"),
               "second skill, no bare names\n", eol="\n")
        assert check_hashes(root, m) == []


def test_missing_declared_file_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        os.remove(os.path.join(root, "sp-beta/SKILL.md"))
        out = check_copy_set(root, m)
        assert [f["path"] for f in out] == ["sp-beta/SKILL.md"]


def test_undeclared_file_under_a_vendored_dir_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        _write(os.path.join(root, "sp-alpha/sneaked.md"), "hi\n", eol="\r\n")
        out = check_copy_set(root, m)
        assert [f["path"] for f in out] == ["sp-alpha/sneaked.md"]


def test_sp_grill_with_doc_is_not_treated_as_a_copy(tmp_path=None):
    """The sp- prefix means 'belongs with superpowers', NOT 'is a copy'.
    A glob of sp-* collects 24 files in the real repo, not 21."""
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        _write(os.path.join(root, "sp-grill-with-doc/EXTRA.md"), "x\n",
               eol="\r\n")
        assert check_copy_set(root, m) == []


def test_undeclared_file_beside_a_frozen_file_is_flagged(tmp_path=None):
    """A frozen file is guarded by its hash; its NEIGHBOURS are guarded here."""
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        _write(os.path.join(root, "frozen/EXTRA.md"), "new\n", eol="\r\n")
        out = check_copy_set(root, m)
        assert [f["path"] for f in out] == ["frozen/EXTRA.md"]


def test_frozen_file_change_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        _write(os.path.join(root, "frozen/SKILL.md"), "edited\n", eol="\r\n")
        out = check_frozen(root, m)
        assert len(out) == 1
        assert "owner constraint" in out[0]["message"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: FAIL — `ImportError: cannot import name 'check_copy_set'`

- [ ] **Step 3: Write minimal implementation**

Insert these three functions into `check_vendored_superpowers.py`, after `upstream_skill_names` and before `main`:

```python
def check_copy_set(root, manifest):
    """Check 1 - every declared file exists, and no undeclared file sits
    inside a directory this manifest governs.

    Governed = the vendored skill dirs PLUS the top-level directory of every
    frozen file, so a file dropped beside a frozen one is seen too. A frozen
    file's own absence is reported by check_frozen, not here."""
    out = []
    declared = {f["path"] for f in manifest["copy_set"]["files"]}
    known = declared | {e["path"] for e in manifest.get("frozen", [])}
    for rel in sorted(declared):
        if not os.path.isfile(os.path.join(root, rel)):
            out.append(finding(
                "copy-set", rel, "declared file is missing from the tree",
                "restore it from upstream, or re-emit the manifest if the "
                "copy set genuinely shrank"))
    governed = set(copied_skill_dirs(manifest))
    governed |= {e["path"].split("/")[0]
                 for e in manifest.get("frozen", []) if "/" in e["path"]}
    for skill_dir in sorted(governed):
        base = os.path.join(root, skill_dir)
        for dirpath, _, names in os.walk(base):
            for name in names:
                rel = os.path.relpath(os.path.join(dirpath, name),
                                      root).replace("\\", "/")
                if rel not in known:
                    out.append(finding(
                        "copy-set", rel,
                        "file inside a directory this manifest governs is "
                        "not declared in it",
                        "if it came from upstream, copy it in properly and "
                        "add it; if it is ours, it does not belong beside a "
                        "vendored copy or a frozen file"))
    return sorted(out, key=lambda f: f["path"])


def check_hashes(root, manifest):
    """Check 2 - each copied file still hashes to its vendored value."""
    out = []
    for f in manifest["copy_set"]["files"]:
        path = os.path.join(root, f["path"])
        if not os.path.isfile(path):
            continue          # already reported by check_copy_set
        actual = content_hash(read_normalized(path))
        if actual != f["sha256"]:
            out.append(finding(
                "hash", f["path"],
                "content changed since vendoring (%s -> %s)"
                % (f["sha256"][:12], actual[:12]),
                "revert the edit, or re-vendor the set and re-emit the "
                "manifest. An edit inside a copy can break its route to "
                "scrutinize-dispatch with no error message"))
    return out


def check_frozen(root, manifest):
    """Check 6 - the frozen files are unchanged (ADR 0088)."""
    out = []
    for entry in manifest["frozen"]:
        path = os.path.join(root, entry["path"])
        if not os.path.isfile(path):
            out.append(finding(
                "frozen", entry["path"], "frozen file is missing",
                "restore it - %s" % entry["why"]))
            continue
        actual = content_hash(read_normalized(path))
        if actual != entry["sha256"]:
            out.append(finding(
                "frozen", entry["path"],
                "FROZEN file changed - %s" % entry["why"],
                "revert it. If the change is genuinely required it needs a "
                "decision first (ADR 0084's escape hatch), then a manifest "
                "update in the same commit"))
    return out
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: PASS — `14/14 passed`

- [ ] **Step 5: Commit**

```bash
cd "c:/Repo2/workflow daily work" && git add plugins/dev-workflows/scripts/ && git commit -m "feat(dev-workflows): checker asserts copy-set completeness, hashes and the frozen set (ADR 0088)"
```

---

### Task 3: Check 3 — the bare-name check, with NEW and STALE findings

This is the check ADR 0071 wrote down and nobody ran. It is the one that would have caught the Critical defect.

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_vendored_superpowers.py`
- Test: `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`

**Interfaces:**
- Consumes: `read_text`, `finding`, `upstream_skill_names` (Task 1)
- Produces: `bare_name_re(names) -> re.Pattern`, `check_bare_names(root, manifest) -> list[dict]`. Finding `check` values are exactly `"permit-list/NEW"`, `"permit-list/STALE"` and `"permit-list/UNREVIEWED"`.

- [ ] **Step 1: Write the failing test**

Extend the import to include `bare_name_re, check_bare_names`, then add:

```python
def test_bare_name_re_ignores_prefixed_forms():
    pat = bare_name_re(["brainstorming", "writing-plans"])
    assert pat.search("then use writing-plans next")           # bare - a hit
    assert not pat.search("see superpowers:writing-plans")     # qualified
    assert not pat.search("load sp-writing-plans now")         # our copy
    assert pat.search("digraph brainstorming {")               # bare - a hit


def _permit_tree(d):
    """A copy set holding one permitted bare name and nothing else.

    BOTH `brainstorming` and `writing-plans` must be in the copy set: the name
    set the checker searches for is DERIVED from it, so a name absent here can
    never be found anywhere."""
    root = os.path.join(d, "skills")
    permitted = "digraph brainstorming {"
    _write(os.path.join(root, "sp-brainstorming/SKILL.md"),
           "header\n%s\nsee sp-writing-plans and superpowers:using-git-worktrees\n"
           % permitted, eol="\r\n")
    _write(os.path.join(root, "sp-writing-plans/SKILL.md"),
           "a second copied skill, carrying no bare names\n", eol="\r\n")
    manifest = {
        "copy_set": {"files": [
            {"path": "sp-brainstorming/SKILL.md",
             "upstream_path": "brainstorming/SKILL.md",
             "state": "edited", "sha256": "x"},
            {"path": "sp-writing-plans/SKILL.md",
             "upstream_path": "writing-plans/SKILL.md",
             "state": "edited", "sha256": "x"}]},
        "permit_list": [{"file": "sp-brainstorming/SKILL.md",
                         "text": permitted,
                         "why": "DOT graph identifier, not a skill reference"}],
    }
    return root, manifest, permitted


def test_permitted_line_is_not_a_finding(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m, _ = _permit_tree(d)
        assert check_bare_names(root, m) == []


def test_new_bare_name_is_a_NEW_finding(tmp_path=None):
    """The Plan A Critical, reproduced: a bare short name that resolves to the
    UNVENDORED upstream skill, with no error message."""
    with tempfile.TemporaryDirectory() as d:
        root, m, permitted = _permit_tree(d)
        p = os.path.join(root, "sp-brainstorming/SKILL.md")
        _write(p, "header\n%s\nwriting-plans is the next step\n" % permitted,
               eol="\r\n")
        out = check_bare_names(root, m)
        assert [f["check"] for f in out] == ["permit-list/NEW"]
        assert "writing-plans is the next step" in out[0]["message"]


def test_reworded_permit_line_is_a_STALE_finding(tmp_path=None):
    """The reworded line still holds a bare name, so it is BOTH a STALE entry
    and a NEW unlisted line. The runner must see both."""
    with tempfile.TemporaryDirectory() as d:
        root, m, _ = _permit_tree(d)
        p = os.path.join(root, "sp-brainstorming/SKILL.md")
        _write(p, "header\ndigraph brainstorming {  // renamed\n", eol="\r\n")
        checks = sorted(f["check"] for f in check_bare_names(root, m))
        assert checks == ["permit-list/NEW", "permit-list/STALE"]


def test_two_permit_entries_need_two_occurrences(tmp_path=None):
    """Two entries claiming one line are not satisfied by a single occurrence."""
    with tempfile.TemporaryDirectory() as d:
        root, m, _ = _permit_tree(d)
        m["permit_list"].append(dict(m["permit_list"][0]))
        out = check_bare_names(root, m)
        assert [f["check"] for f in out] == ["permit-list/STALE"]


def test_permit_entry_awaiting_review_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m, _ = _permit_tree(d)
        m["permit_list"][0]["why"] = "REVIEW: state why this is inert"
        out = check_bare_names(root, m)
        assert [f["check"] for f in out] == ["permit-list/UNREVIEWED"]


def test_permitted_line_matches_anywhere_not_by_line_number(tmp_path=None):
    """ADR 0075: no line numbers - upstream may insert a paragraph above."""
    with tempfile.TemporaryDirectory() as d:
        root, m, permitted = _permit_tree(d)
        p = os.path.join(root, "sp-brainstorming/SKILL.md")
        _write(p, "a\nb\nc\nd\ne\n%s\n" % permitted, eol="\r\n")
        assert check_bare_names(root, m) == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: FAIL — `ImportError: cannot import name 'bare_name_re'`

- [ ] **Step 3: Write minimal implementation**

Insert after `check_frozen`:

```python
def bare_name_re(names):
    """Match an upstream short name that is NOT prefixed.

    The lookbehind rejects `superpowers:brainstorming` (preceded by ':') and
    `sp-brainstorming` (preceded by '-'), which is exactly ADR 0071's check:
    a search for any of the six upstream short names, unprefixed, must return
    nothing. Longest-first alternation so a longer name cannot be shadowed."""
    alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(r"(?<![\w:-])(" + alt + r")\b")


def check_bare_names(root, manifest):
    """Check 3 - ADR 0071's check, run against the files.

    NEW        a bare short name on a line the permit list does not hold.
    STALE      a permitted line that is no longer present in its file.
    UNREVIEWED a permit entry whose `why` is still a REVIEW: placeholder."""
    pattern = bare_name_re(upstream_skill_names(manifest))

    declared = Counter((e["file"], e["text"]) for e in manifest["permit_list"])
    why_of = {(e["file"], e["text"]): str(e.get("why", ""))
              for e in manifest["permit_list"]}

    out = []
    actual = Counter()
    for f in manifest["copy_set"]["files"]:
        rel = f["path"]
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue          # already reported by check_copy_set
        for line in read_text(path).split("\n"):
            if not pattern.search(line):
                continue
            if (rel, line) in declared:
                actual[(rel, line)] += 1
                continue
            out.append(finding(
                "permit-list/NEW", rel,
                "bare upstream skill name on an unlisted line: %s"
                % line.strip()[:160],
                "if it is a handoff, give it the sp- prefix - a bare name "
                "resolves to the UNVENDORED upstream skill with no error. If "
                "it is genuinely inert, add the line to permit_list with a why"))

    for (rel, text), want in sorted(declared.items()):
        got = actual[(rel, text)]
        if got < want:
            out.append(finding(
                "permit-list/STALE", rel,
                "permit list claims this line %d time(s), found %d: %s"
                % (want, got, text.strip()[:160]),
                "the line moved, was reworded or was deleted. Re-confirm it "
                "is still inert, then update permit_list"))
        elif why_of[(rel, text)].startswith("REVIEW:"):
            out.append(finding(
                "permit-list/UNREVIEWED", rel,
                "permit entry still carries a REVIEW: placeholder",
                "state why this bare name is inert, then replace the why. An "
                "unreviewed entry permits a line nobody has judged"))
    return out
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: PASS — `21/21 passed`

- [ ] **Step 5: Commit**

```bash
cd "c:/Repo2/workflow daily work" && git add plugins/dev-workflows/scripts/ && git commit -m "feat(dev-workflows): run ADR 0071's bare-name check - NEW/STALE permit list (ADR 0087)"
```

---

### Task 4: Checks 4 and 5 — the qualified-reference census and routing

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_vendored_superpowers.py`
- Test: `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`

**Interfaces:**
- Consumes: `read_text`, `finding`, `upstream_skill_names` (Task 1)
- Produces: `QUALIFIED` (a compiled `re.Pattern`), `check_qualified_refs(root, manifest) -> list[dict]`, `check_routing(root, manifest) -> list[dict]`

- [ ] **Step 1: Write the failing test**

Extend the import to include `check_qualified_refs, check_routing`, then add:

```python
def _ref_tree(d):
    root = os.path.join(d, "skills")
    _write(os.path.join(root, "sp-alpha/SKILL.md"),
           "see superpowers:using-git-worktrees for isolation\n", eol="\r\n")
    manifest = {
        "copy_set": {"files": [{"path": "sp-alpha/SKILL.md",
                                "upstream_path": "alpha/SKILL.md",
                                "state": "edited", "sha256": "x"}]},
        "qualified_refs": {"using-git-worktrees": 1},
    }
    return root, manifest


def test_reference_to_a_non_copied_skill_is_clean(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _ref_tree(d)
        assert check_qualified_refs(root, m) == []


def test_reference_to_a_copied_skill_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _ref_tree(d)
        _write(os.path.join(root, "sp-alpha/SKILL.md"),
               "hand off to superpowers:alpha now\n", eol="\r\n")
        out = check_qualified_refs(root, m)
        assert any(f["check"] == "qualified-ref" for f in out)


def test_census_change_is_flagged(tmp_path=None):
    """A NEW upstream name is legitimate but must be seen, not absorbed."""
    with tempfile.TemporaryDirectory() as d:
        root, m = _ref_tree(d)
        _write(os.path.join(root, "sp-alpha/SKILL.md"),
               "see superpowers:using-git-worktrees and "
               "superpowers:test-driven-development\n", eol="\r\n")
        out = check_qualified_refs(root, m)
        assert [f["check"] for f in out] == ["qualified-ref/census"]


def _route_tree(d):
    root = os.path.join(d, "skills")
    _write(os.path.join(root, "sp-x/code-reviewer.md"),
           "Load the `scrutinize-dispatch` skill.\n", eol="\r\n")
    _write(os.path.join(root, "sp-x/re-review-prompt.md"),
           "Verdict each finding ADDRESSED or NOT ADDRESSED.\n", eol="\r\n")
    manifest = {
        "routing_marker": "scrutinize-dispatch",
        "routed_prompts": ["sp-x/code-reviewer.md"],
        "unrouted_prompts": ["sp-x/re-review-prompt.md"],
    }
    return root, manifest


def test_routed_and_unrouted_prompts_are_clean(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _route_tree(d)
        assert check_routing(root, m) == []


def test_routed_prompt_losing_the_marker_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _route_tree(d)
        _write(os.path.join(root, "sp-x/code-reviewer.md"),
               "Review the diff yourself.\n", eol="\r\n")
        out = check_routing(root, m)
        assert [f["path"] for f in out] == ["sp-x/code-reviewer.md"]


def test_unrouted_prompt_gaining_the_marker_is_flagged(tmp_path=None):
    """ADR 0084's amendment: re-review is deliberately unrouted."""
    with tempfile.TemporaryDirectory() as d:
        root, m = _route_tree(d)
        _write(os.path.join(root, "sp-x/re-review-prompt.md"),
               "Load the `scrutinize-dispatch` skill.\n", eol="\r\n")
        out = check_routing(root, m)
        assert [f["path"] for f in out] == ["sp-x/re-review-prompt.md"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: FAIL — `ImportError: cannot import name 'check_qualified_refs'`

- [ ] **Step 3: Write minimal implementation**

Add `QUALIFIED` beside the other module constants, then insert the two functions after `check_bare_names`:

```python
QUALIFIED = re.compile(r"superpowers:([a-z][a-z0-9-]*)")


def check_qualified_refs(root, manifest):
    """Check 4 - no qualified reference names a skill that IS in the copy set,
    and the census of the rest is unchanged.

    ADR 0071 tabulates only two names with counts 5 and 3. A third,
    `using-superpowers`, is legitimately present (rewrite class 2), so an
    exact-match assertion on that table would fail on a correct tree. The
    rule is 'none of the copied names'; the census is reported separately."""
    copied = set(upstream_skill_names(manifest))
    census = {}
    out = []
    for f in manifest["copy_set"]["files"]:
        rel = f["path"]
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        for lineno, line in enumerate(read_text(path).split("\n"), 1):
            for match in QUALIFIED.finditer(line):
                name = match.group(1)
                census[name] = census.get(name, 0) + 1
                if name in copied:
                    out.append(finding(
                        "qualified-ref", rel,
                        "line %d names superpowers:%s, which IS in the copy "
                        "set" % (lineno, name),
                        "rewrite it to the short sp-%s name - left as is, the "
                        "arc re-enters the upstream original one handoff "
                        "later (ADR 0074 class 4)" % name))
    recorded = dict(manifest["qualified_refs"])
    if census != recorded:
        out.append(finding(
            "qualified-ref/census", "-",
            "qualified reference census changed: recorded %s, found %s"
            % (recorded, census),
            "confirm every new or changed reference names a skill that stays "
            "upstream, then update qualified_refs"))
    return out


def check_routing(root, manifest):
    """Check 5 - the routed reviewer prompts name the dispatch engine, and the
    deliberately unrouted one does not (ADR 0084 and its amendment).

    Only the prompt FILES are asserted. Two `description:` fields also mention
    the marker; asserting a raw repo-wide count would couple this check to
    description wording."""
    marker = manifest["routing_marker"]
    out = []
    for rel in manifest["routed_prompts"]:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            out.append(finding("routing", rel, "routed prompt is missing",
                               "restore it"))
            continue
        if marker not in read_text(path):
            out.append(finding(
                "routing", rel,
                "routed reviewer prompt no longer names `%s`" % marker,
                "restore the delegation line. Without it the dispatch falls "
                "back to the built-in reviewer, with no error and no warning "
                "- the exact failure this vendoring exists to remove"))
    for rel in manifest["unrouted_prompts"]:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            out.append(finding("routing", rel, "unrouted prompt is missing",
                               "restore it"))
            continue
        if marker in read_text(path):
            out.append(finding(
                "routing", rel,
                "deliberately unrouted prompt now names `%s`" % marker,
                "remove it. A re-review verdicts each prior finding ADDRESSED "
                "or NOT ADDRESSED, which that engine has no way to express "
                "(ADR 0084, amendment of 2026-08-16)"))
    return out
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: PASS — `27/27 passed`

- [ ] **Step 5: Commit**

```bash
cd "c:/Repo2/workflow daily work" && git add plugins/dev-workflows/scripts/ && git commit -m "feat(dev-workflows): checker asserts the qualified-ref census and both routing rules (ADR 0071, 0084)"
```

---

### Task 5: `--emit-manifest`, and the real committed manifest

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_vendored_superpowers.py`
- Create: `plugins/dev-workflows/references/vendored-superpowers.json`
- Test: `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`

**Interfaces:**
- Consumes: everything from Tasks 1-4
- Produces: `emit_manifest(root, upstream_root, previous) -> dict`. `previous` may be `None`; when given, each permit entry's `why` is carried over by exact text match.

- [ ] **Step 1: Write the failing test**

Extend the import to include `emit_manifest`, then add:

```python
def test_emit_manifest_round_trips_clean(tmp_path=None):
    """A manifest emitted from a tree must find that tree clean."""
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "skills")
        up = os.path.join(d, "upstream")
        _write(os.path.join(root, "sp-alpha/SKILL.md"), "body\n", eol="\r\n")
        _write(os.path.join(up, "skills/alpha/SKILL.md"), "body\n", eol="\n")
        m = emit_manifest(root, up, None)
        assert check_copy_set(root, m) == []
        assert check_hashes(root, m) == []
        # identical content, different EOL -> verbatim (ADR 0086)
        assert m["copy_set"]["files"][0]["state"] == "verbatim"


def test_emit_manifest_marks_an_edited_file(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "skills")
        up = os.path.join(d, "upstream")
        _write(os.path.join(root, "sp-alpha/SKILL.md"), "ours\n", eol="\r\n")
        _write(os.path.join(up, "skills/alpha/SKILL.md"), "theirs\n", eol="\n")
        m = emit_manifest(root, up, None)
        assert m["copy_set"]["files"][0]["state"] == "edited"


def test_emit_manifest_carries_over_a_reviewed_why(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "skills")
        up = os.path.join(d, "upstream")
        line = "digraph brainstorming {"
        _write(os.path.join(root, "sp-brainstorming/SKILL.md"),
               "%s\n" % line, eol="\r\n")
        _write(os.path.join(up, "skills/brainstorming/SKILL.md"),
               "%s\n" % line, eol="\n")
        previous = {"permit_list": [{"file": "sp-brainstorming/SKILL.md",
                                     "text": line, "why": "DOT identifier"}]}
        m = emit_manifest(root, up, previous)
        assert m["permit_list"][0]["why"] == "DOT identifier"
        m2 = emit_manifest(root, up, None)
        assert m2["permit_list"][0]["why"].startswith("REVIEW:")


def test_emit_refuses_when_the_manifest_was_truncated(tmp_path=None):
    """Redirecting --emit-manifest onto its own input truncates it first.
    Emitting from the empty file would drop every hand-written key in silence,
    so the program must refuse instead."""
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "skills")
        up = os.path.join(d, "upstream")
        _write(os.path.join(root, "sp-alpha/SKILL.md"), "body\n", eol="\r\n")
        _write(os.path.join(up, "skills/alpha/SKILL.md"), "body\n", eol="\n")
        p = os.path.join(d, "m.json")
        open(p, "w").close()                 # exactly what `>` leaves behind
        assert main(["--emit-manifest", "--root", root,
                     "--manifest", p, "--upstream-dir", up]) == 2


def test_emit_manifest_without_upstream_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        assert main(["--emit-manifest", "--root", d,
                     "--manifest", os.path.join(d, "absent.json")]) == 2
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: FAIL — `ImportError: cannot import name 'emit_manifest'`

- [ ] **Step 3: Write minimal implementation**

Insert after `check_routing`:

```python
def emit_manifest(root, upstream_root, previous):
    """Compute a complete manifest from the tree. Returns a dict; the caller
    prints it. NOTHING is written to disk (ADR 0075).

    Requires upstream, because `state` is verbatim-or-edited against it and a
    guessed state is worse than no state. `previous` supplies the human-written
    `why` strings, carried over by exact text match."""
    up_skills = os.path.join(upstream_root,
                             (previous or {}).get("upstream", {})
                             .get("skills_subdir", "skills"))
    prior_why = {}
    for entry in (previous or {}).get("permit_list", []):
        prior_why[(entry["file"], entry["text"])] = entry.get("why", "")

    files = []
    for skill_dir in sorted(os.listdir(root)):
        base = os.path.join(root, skill_dir)
        if not os.path.isdir(base) or not skill_dir.startswith("sp-"):
            continue
        upstream_name = skill_dir[len("sp-"):]
        if not os.path.isdir(os.path.join(up_skills, upstream_name)):
            continue          # not a vendored copy - e.g. sp-grill-with-doc
        for dirpath, _, names in sorted(os.walk(base)):
            for name in sorted(names):
                rel = os.path.relpath(os.path.join(dirpath, name),
                                      root).replace("\\", "/")
                up_rel = upstream_name + rel[len(skill_dir):]
                ours = read_normalized(os.path.join(root, rel))
                up_path = os.path.join(up_skills, up_rel)
                state = "edited"
                if os.path.isfile(up_path) and read_normalized(up_path) == ours:
                    state = "verbatim"
                files.append({"path": rel, "upstream_path": up_rel,
                              "state": state, "sha256": content_hash(ours)})

    manifest = dict(previous or {})
    manifest["copy_set"] = {"root": "plugins/dev-workflows/skills",
                            "files": files}

    scratch = {"copy_set": manifest["copy_set"]}
    pattern = bare_name_re(upstream_skill_names(scratch))
    permit, census = [], {}
    for f in files:
        rel = f["path"]
        for line in read_text(os.path.join(root, rel)).split("\n"):
            if pattern.search(line):
                permit.append({
                    "file": rel, "text": line,
                    "why": prior_why.get((rel, line))
                           or "REVIEW: state why this bare name is inert"})
            for match in QUALIFIED.finditer(line):
                census[match.group(1)] = census.get(match.group(1), 0) + 1
    manifest["permit_list"] = permit
    manifest["qualified_refs"] = census

    for key, default in (("upstream", {}), ("routing_marker",
                                            "scrutinize-dispatch"),
                         ("routed_prompts", []), ("unrouted_prompts", []),
                         ("frozen", []), ("upstream_traps", {})):
        manifest.setdefault(key, default)

    for entry in manifest["frozen"]:
        path = os.path.join(root, entry["path"])
        if os.path.isfile(path):
            entry["sha256"] = content_hash(read_normalized(path))
    return manifest
```

Then wire it into `main`, replacing the placeholder block that currently prints `OK: manifest loaded`:

```python
    if args.emit_manifest:
        if not args.upstream_dir:
            print("ERROR: --emit-manifest requires --upstream-dir: `state` is "
                  "verbatim-or-edited against upstream, and a guessed state "
                  "is worse than no state.")
            return 2
        if not os.path.isdir(args.upstream_dir):
            print("ERROR: --upstream-dir not found: %s" % args.upstream_dir)
            return 2
        previous = None
        if os.path.exists(args.manifest):
            if os.path.getsize(args.manifest) == 0:
                print("ERROR: %s exists but is empty. That is what a shell "
                      "redirect onto the manifest leaves behind - it truncates "
                      "the file before this program starts, so every "
                      "hand-written key would be read as absent and dropped. "
                      "Emit to a temp file, then move it into place."
                      % args.manifest)
                return 2
            try:
                previous = load_manifest(args.manifest)
            except ValueError as e:
                print("ERROR: refusing to emit from an unreadable manifest - "
                      "%s. Fix or delete it first; emitting now would silently "
                      "drop every hand-written key." % e)
                return 2
        out = emit_manifest(args.root, args.upstream_dir, previous)
        print(json.dumps(out, indent=2, ensure_ascii=False))
        return 0
```

Note the ordering: this block must run **before** `load_manifest` is required, so move the `--emit-manifest` handling above the `try: manifest = load_manifest(...)` block in `main`.

- [ ] **Step 4: Run test to verify it passes**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: PASS — `32/32 passed`

- [ ] **Step 5: Generate the real manifest**

```bash
cd "c:/Repo2/workflow daily work" && UP="$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/b36e0829c6d0" && python plugins/dev-workflows/scripts/check_vendored_superpowers.py --emit-manifest --upstream-dir "$UP" > /tmp/manifest.new.json && mv /tmp/manifest.new.json plugins/dev-workflows/references/vendored-superpowers.json && python -c "import json;m=json.load(open(r'plugins/dev-workflows/references/vendored-superpowers.json',encoding='utf-8'));print('files',len(m['copy_set']['files']));print('permit',len(m['permit_list']));print('census',m['qualified_refs']);print('verbatim',sum(1 for f in m['copy_set']['files'] if f['state']=='verbatim'))"
```

Expected: `files 21`, `permit 13`, `census {'finishing-a-development-branch': 5, 'using-git-worktrees': 3, 'using-superpowers': 1}`, `verbatim 13`.

**If any number differs, stop and report it — do not adjust the program to match.** These four figures were measured at `16de152`, and a difference means either the tree moved or the program is wrong.

- [ ] **Step 6: Fill in the hand-written sections of the manifest**

`--emit-manifest` cannot compute these. Edit `plugins/dev-workflows/references/vendored-superpowers.json` and set:

```json
  "upstream": {
    "url": "https://github.com/obra/superpowers",
    "sha": "b36e0829c6d0140e93cfef2ca599b1b07d4a7797",
    "license": "MIT (c) 2025 Jesse Vincent",
    "vendored_at": "2026-08-16",
    "skills_subdir": "skills"
  },
  "routing_marker": "scrutinize-dispatch",
  "routed_prompts": [
    "sp-requesting-code-review/code-reviewer.md",
    "sp-subagent-driven-development/task-reviewer-prompt.md"
  ],
  "unrouted_prompts": [
    "sp-subagent-driven-development/re-review-prompt.md"
  ],
  "frozen": [
    {"path": "scrutinize/SKILL.md", "sha256": "",
     "why": "owner constraint - the declared fork scrutinize-dispatch must not drift from something that moved underneath it (ADR 0084)"},
    {"path": "sp-subagent-driven-development/re-review-prompt.md", "sha256": "",
     "why": "deliberately unrouted and byte-identical to upstream (ADR 0084 amendment)"}
  ],
  "upstream_traps": {
    "no_qualified_ref_dir": "brainstorming",
    "hook_source": "using-superpowers/SKILL.md",
    "hook_named_skills": ["brainstorming", "systematic-debugging"],
    "dead_prompts": ["spec-document-reviewer-prompt", "plan-document-reviewer-prompt"],
    "dead_prompt_live_dirs": ["skills", "hooks", "scripts"]
  }
```

Then re-run `--emit-manifest` **through a temp file** so the two `frozen` hashes are filled in and the keys you just wrote survive:

```bash
cd "c:/Repo2/workflow daily work" && UP="$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/b36e0829c6d0" && python plugins/dev-workflows/scripts/check_vendored_superpowers.py --emit-manifest --upstream-dir "$UP" > /tmp/manifest.new.json && mv /tmp/manifest.new.json plugins/dev-workflows/references/vendored-superpowers.json && python -c "import json;m=json.load(open(r'plugins/dev-workflows/references/vendored-superpowers.json',encoding='utf-8'));print('upstream sha:',m['upstream'].get('sha','LOST'));print('frozen:',[(e['path'],e['sha256'][:12]) for e in m['frozen']]);print('routed:',m['routed_prompts'])"
```

Expected: the sha you typed, two frozen entries with real hashes, and both routed prompts. **If `upstream sha` prints `LOST`, the redirect truncated the manifest** - restore it from git and use the temp-file form.

Then replace the 13 `REVIEW:` placeholders with the real reasons:

| the line's shape | the `why` to write |
|---|---|
| `description: 'You MUST use this, and not the upstream superpowers <name> skill, …'` (6 entries) | `our own displacement description - names the upstream skill it replaces (ADR 0071 decision 3)` |
| `digraph brainstorming {` (1 entry) | `DOT graph identifier, not a skill reference` |
| the word used as an activity noun (4 entries) | `activity noun, not a skill reference` |
| `**Announce at start:** "I'm using the <name> skill…"` (2 entries) | `upstream's verbatim announce line - it tells the agent to SAY a name, not to LOAD one. Same textual shape as a handoff; inert only because of what it instructs` |

- [ ] **Step 7: Verify the checker now passes on the real tree**

```bash
cd "c:/Repo2/workflow daily work" && python plugins/dev-workflows/scripts/check_vendored_superpowers.py --strict; echo "exit=$?"
```

Expected: no findings, `exit=0`.

- [ ] **Step 8: Commit**

```bash
cd "c:/Repo2/workflow daily work" && git add plugins/dev-workflows/scripts/ plugins/dev-workflows/references/vendored-superpowers.json && git commit -m "feat(dev-workflows): --emit-manifest and the vendoring manifest (ADR 0075, 0085)"
```

---

### Task 6: Check 7 — the upstream per-file comparison and the 1:1 mapping

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_vendored_superpowers.py`
- Test: `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`

**Interfaces:**
- Consumes: `read_normalized`, `finding`, `upstream_skill_names` (Task 1)
- Produces: `upstream_skills_dir(upstream_root, manifest) -> str`, `check_upstream_files(root, upstream_root, manifest) -> list[dict]`

- [ ] **Step 1: Write the failing test**

Extend the import to include `check_upstream_files`, then add:

```python
def _upstream_pair(d, ours="body\n", theirs="body\n", state="verbatim"):
    root = os.path.join(d, "skills")
    up = os.path.join(d, "upstream")
    _write(os.path.join(root, "sp-alpha/SKILL.md"), ours, eol="\r\n")
    _write(os.path.join(up, "skills/alpha/SKILL.md"), theirs, eol="\n")
    manifest = {
        "upstream": {"skills_subdir": "skills"},
        "copy_set": {"files": [{"path": "sp-alpha/SKILL.md",
                                "upstream_path": "alpha/SKILL.md",
                                "state": state, "sha256": "x"}]},
    }
    return root, up, manifest


def test_verbatim_file_matching_upstream_is_clean(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, up, m = _upstream_pair(d)
        assert check_upstream_files(root, up, m) == []


def test_verbatim_file_that_upstream_moved_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, up, m = _upstream_pair(d, ours="body\n", theirs="body v2\n")
        out = check_upstream_files(root, up, m)
        assert [f["check"] for f in out] == ["upstream/moved"]


def test_edited_file_identical_to_upstream_is_flagged(tmp_path=None):
    """The rewrite pass was lost - the copy no longer differs from upstream."""
    with tempfile.TemporaryDirectory() as d:
        root, up, m = _upstream_pair(d, state="edited")
        out = check_upstream_files(root, up, m)
        assert [f["check"] for f in out] == ["upstream/moved"]


def test_upstream_deleting_a_copied_file_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, up, m = _upstream_pair(d)
        os.remove(os.path.join(up, "skills/alpha/SKILL.md"))
        out = check_upstream_files(root, up, m)
        assert [f["check"] for f in out] == ["upstream/mapping"]


def test_upstream_adding_a_file_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, up, m = _upstream_pair(d)
        _write(os.path.join(up, "skills/alpha/NEW.md"), "new\n", eol="\n")
        out = check_upstream_files(root, up, m)
        assert [f["check"] for f in out] == ["upstream/added"]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: FAIL — `ImportError: cannot import name 'check_upstream_files'`

- [ ] **Step 3: Write minimal implementation**

Insert after `emit_manifest`:

```python
def upstream_skills_dir(upstream_root, manifest):
    """--upstream-dir is the upstream PLUGIN ROOT; the skills live under it."""
    return os.path.join(upstream_root,
                        manifest["upstream"].get("skills_subdir", "skills"))


def check_upstream_files(root, upstream_root, manifest):
    """Check 7 - per-file comparison against upstream, plus the 1:1 mapping
    ADR 0074 depends on. All comparisons CR-normalized (ADR 0086)."""
    up_skills = upstream_skills_dir(upstream_root, manifest)
    declared_up = {f["upstream_path"] for f in manifest["copy_set"]["files"]}
    out = []

    for f in manifest["copy_set"]["files"]:
        our_path = os.path.join(root, f["path"])
        up_path = os.path.join(up_skills, f["upstream_path"])
        if not os.path.isfile(up_path):
            out.append(finding(
                "upstream/mapping", f["upstream_path"],
                "upstream no longer carries this file",
                "decide whether to drop the copy or keep it deliberately, "
                "then record which in the manifest"))
            continue
        if not os.path.isfile(our_path):
            continue          # already reported by check_copy_set
        ours = read_normalized(our_path)
        theirs = read_normalized(up_path)
        if f["state"] == "verbatim" and ours != theirs:
            out.append(finding(
                "upstream/moved", f["path"],
                "recorded verbatim, but it now differs from upstream",
                "re-copy the file, re-apply the rewrite pass if it needs one, "
                "then re-emit the manifest"))
        elif f["state"] == "edited" and ours == theirs:
            out.append(finding(
                "upstream/moved", f["path"],
                "recorded edited, but it is now identical to upstream - the "
                "rewrite pass looks lost",
                "re-apply the rewrite classes for this file, or correct its "
                "state if upstream adopted our wording"))

    for name in upstream_skill_names(manifest):
        base = os.path.join(up_skills, name)
        for dirpath, _, names in os.walk(base):
            for fn in names:
                rel = os.path.relpath(os.path.join(dirpath, fn),
                                      up_skills).replace("\\", "/")
                if rel not in declared_up:
                    out.append(finding(
                        "upstream/added", rel,
                        "upstream added a file to a vendored skill directory",
                        "copy it in and add it to the manifest, or record why "
                        "it is deliberately not copied. An uncopied new file "
                        "is a review touchpoint arriving unannounced"))
    return sorted(out, key=lambda f: (f["check"], f["path"]))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: PASS — `37/37 passed`

- [ ] **Step 5: Commit**

```bash
cd "c:/Repo2/workflow daily work" && git add plugins/dev-workflows/scripts/ && git commit -m "feat(dev-workflows): upstream mode compares the copy set and the 1:1 mapping (ADR 0074)"
```

---

### Task 7: Checks 8, 9 and 10 — the three upstream traps

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_vendored_superpowers.py`
- Test: `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`

**Interfaces:**
- Consumes: `read_text`, `finding`, `QUALIFIED`, `upstream_skills_dir` (Tasks 1, 4, 6)
- Produces: `check_upstream_traps(upstream_root, manifest) -> list[dict]`

- [ ] **Step 1: Write the failing test**

Extend the import to include `check_upstream_traps`, then add:

```python
def _trap_tree(d):
    up = os.path.join(d, "upstream")
    _write(os.path.join(up, "skills/brainstorming/SKILL.md"),
           "no qualified refs here\n", eol="\n")
    _write(os.path.join(up, "skills/using-superpowers/SKILL.md"),
           "use superpowers:brainstorming then "
           "superpowers:systematic-debugging\n", eol="\n")
    _write(os.path.join(up, "skills/brainstorming/"
                            "spec-document-reviewer-prompt.md"),
           "dead file\n", eol="\n")
    _write(os.path.join(up, "docs/history.md"),
           "we once used spec-document-reviewer-prompt\n", eol="\n")
    manifest = {
        "upstream": {"skills_subdir": "skills"},
        "upstream_traps": {
            "no_qualified_ref_dir": "brainstorming",
            "hook_source": "using-superpowers/SKILL.md",
            "hook_named_skills": ["brainstorming", "systematic-debugging"],
            "dead_prompts": ["spec-document-reviewer-prompt"],
            "dead_prompt_live_dirs": ["skills", "hooks", "scripts"]},
    }
    return up, manifest


def test_all_three_traps_hold(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        up, m = _trap_tree(d)
        assert check_upstream_traps(up, m) == []


def test_trap_1_qualified_ref_inside_brainstorming(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        up, m = _trap_tree(d)
        _write(os.path.join(up, "skills/brainstorming/SKILL.md"),
               "next use superpowers:writing-plans\n", eol="\n")
        out = check_upstream_traps(up, m)
        assert [f["check"] for f in out] == ["upstream/trap-1"]


def test_trap_2_a_third_hook_named_skill(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        up, m = _trap_tree(d)
        _write(os.path.join(up, "skills/using-superpowers/SKILL.md"),
               "superpowers:brainstorming superpowers:systematic-debugging "
               "superpowers:test-driven-development\n", eol="\n")
        out = check_upstream_traps(up, m)
        assert [f["check"] for f in out] == ["upstream/trap-2"]


def test_trap_3_a_dead_prompt_is_revived(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        up, m = _trap_tree(d)
        _write(os.path.join(up, "skills/brainstorming/SKILL.md"),
               "dispatch spec-document-reviewer-prompt now\n", eol="\n")
        out = check_upstream_traps(up, m)
        assert [f["check"] for f in out] == ["upstream/trap-3"]


def test_trap_3_ignores_docs_and_the_file_itself(tmp_path=None):
    """docs/ mentions are how upstream looks TODAY - only skills/, hooks/ and
    scripts/ count as a revival."""
    with tempfile.TemporaryDirectory() as d:
        up, m = _trap_tree(d)
        assert check_upstream_traps(up, m) == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: FAIL — `ImportError: cannot import name 'check_upstream_traps'`

- [ ] **Step 3: Write minimal implementation**

Insert after `check_upstream_files`:

```python
def check_upstream_traps(upstream_root, manifest):
    """Checks 8-10 - the three upstream changes that show up as no broken
    link and no failed build (ADR 0075).

    Trap 1  brainstorming still hands off by BARE name, so the host hook can
            keep winning that seam on specificity.
    Trap 2  the skills the host hook names still exist, and there are no more
            of them. Assert the set, never eyeball it.
    Trap 3  the two dead document-reviewer prompts stay unreferenced by live
            upstream code. Reviving either is two new review touchpoints
            arriving with no announcement."""
    traps = manifest["upstream_traps"]
    up_skills = upstream_skills_dir(upstream_root, manifest)
    out = []

    seam_dir = traps["no_qualified_ref_dir"]
    for dirpath, _, names in os.walk(os.path.join(up_skills, seam_dir)):
        for fn in sorted(names):
            path = os.path.join(dirpath, fn)
            rel = os.path.relpath(path, up_skills).replace("\\", "/")
            for match in QUALIFIED.finditer(read_text(path)):
                out.append(finding(
                    "upstream/trap-1", rel,
                    "upstream added a qualified reference (%s) inside %s/"
                    % (match.group(), seam_dir),
                    "the host hook wins that seam because the reference is "
                    "contestable prose. A qualified reference makes it forced, "
                    "and the hook stops winning. Re-decide the hook"))

    hook_path = os.path.join(up_skills, traps["hook_source"])
    if not os.path.isfile(hook_path):
        out.append(finding(
            "upstream/trap-2", traps["hook_source"],
            "the upstream file our host hook mirrors is gone",
            "re-derive the hook against upstream's new entry point"))
    else:
        found = sorted(set(QUALIFIED.findall(read_text(hook_path))))
        expected = sorted(traps["hook_named_skills"])
        if found != expected:
            out.append(finding(
                "upstream/trap-2", traps["hook_source"],
                "hook-named skills changed: expected %s, found %s"
                % (expected, found),
                "a rename makes our hook a silent no-op; a third name means "
                "the hook's coverage is incomplete from this version on"))

    for stem in traps["dead_prompts"]:
        for live_dir in traps["dead_prompt_live_dirs"]:
            base = os.path.join(upstream_root, live_dir)
            if not os.path.isdir(base):
                continue
            for dirpath, _, names in os.walk(base):
                for fn in sorted(names):
                    if fn == stem + ".md":
                        continue          # the dead file itself
                    path = os.path.join(dirpath, fn)
                    if stem in read_text(path):
                        rel = os.path.relpath(
                            path, upstream_root).replace("\\", "/")
                        out.append(finding(
                            "upstream/trap-3", rel,
                            "a live upstream file references the dead prompt "
                            "`%s`" % stem,
                            "upstream is reviving the document-review system: "
                            "two new review touchpoints, arriving unannounced. "
                            "Decide whether they must route too"))
    return sorted(out, key=lambda f: (f["check"], f["path"]))
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: PASS — `42/42 passed`

- [ ] **Step 5: Commit**

```bash
cd "c:/Repo2/workflow daily work" && git add plugins/dev-workflows/scripts/ && git commit -m "feat(dev-workflows): assert the three upstream traps ADR 0075 assigned to this checker"
```

---

### Task 8: Wire up `main`, the report, `--strict`, and the live regression test

**Files:**
- Modify: `plugins/dev-workflows/scripts/check_vendored_superpowers.py`
- Test: `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`

**Interfaces:**
- Consumes: every `check_*` function (Tasks 2, 3, 4, 6, 7)
- Produces: `run_checks(root, upstream_root, manifest) -> list[dict]`, `report(findings, summary) -> None`, and the finished `main`

- [ ] **Step 1: Write the failing test**

Extend the import to include `run_checks`, then add:

```python
def test_strict_exits_1_only_when_there_are_findings(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        m["upstream"]["skills_subdir"] = "skills"
        p = os.path.join(d, "m.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(m, f)
        assert main(["--manifest", p, "--root", root, "--strict"]) == 0
        _write(os.path.join(root, "sp-beta/SKILL.md"), "tampered\n",
               eol="\r\n")
        assert main(["--manifest", p, "--root", root]) == 0        # report
        assert main(["--manifest", p, "--root", root, "--strict"]) == 1


def test_missing_upstream_dir_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        p = os.path.join(d, "m.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(m, f)
        assert main(["--manifest", p, "--root", root,
                     "--upstream-dir", os.path.join(d, "absent")]) == 2


def test_the_real_repo_tree_is_clean(tmp_path=None):
    """THE REGRESSION GUARD. This is the test that would have caught the
    Critical: a bare short name inside a copy, resolving to the unvendored
    upstream skill with no error message.

    Skips only if the manifest has not been generated yet (Task 5)."""
    import check_vendored_superpowers as mod
    if not os.path.isfile(mod.DEFAULT_MANIFEST):
        print("SKIP  test_the_real_repo_tree_is_clean: no manifest yet")
        return
    assert main(["--strict"]) == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: FAIL — `ImportError: cannot import name 'run_checks'`

- [ ] **Step 3: Write minimal implementation**

Insert before `main`:

```python
def run_checks(root, upstream_root, manifest):
    """Every check, in report order. Upstream checks run only when an upstream
    tree was supplied."""
    findings = []
    findings += check_copy_set(root, manifest)
    findings += check_hashes(root, manifest)
    findings += check_bare_names(root, manifest)
    findings += check_qualified_refs(root, manifest)
    findings += check_routing(root, manifest)
    findings += check_frozen(root, manifest)
    if upstream_root:
        findings += check_upstream_files(root, upstream_root, manifest)
        findings += check_upstream_traps(upstream_root, manifest)
    return findings


def report(findings, summary):
    if not findings:
        print("OK: %s" % summary)
        return
    print("%d finding(s) - the copies do not match what the manifest records:"
          % len(findings))
    print("  a [hash] finding is the symptom; a [permit-list], "
          "[qualified-ref] or [routing] finding on the same file is the "
          "diagnosis. Repair the second and the first goes away.")
    grouped = {}
    for f in findings:
        grouped.setdefault(f["check"], []).append(f)
    for check in sorted(grouped):
        print("\n  [%s]" % check)
        for f in grouped[check]:
            print("    %s" % f["path"])
            print("      %s" % f["message"])
            print("      fix: %s" % f["repair"])
```

Then replace the placeholder tail of `main` (everything after the manifest loads) with:

```python
    if args.upstream_dir and not os.path.isdir(args.upstream_dir):
        print("ERROR: --upstream-dir not found: %s" % args.upstream_dir)
        return 2
    if not os.path.isdir(args.root):
        print("ERROR: skills root not found: %s" % args.root)
        return 2

    try:
        findings = run_checks(args.root, args.upstream_dir, manifest)
    except OSError as e:
        print("ERROR: cannot read a declared file: %s" % e)
        return 2

    summary = ("%d copied files (%d verbatim), %d permitted bare names, "
               "%d frozen files%s"
               % (len(manifest["copy_set"]["files"]),
                  sum(1 for f in manifest["copy_set"]["files"]
                      if f["state"] == "verbatim"),
                  len(manifest["permit_list"]),
                  len(manifest["frozen"]),
                  "" if not args.upstream_dir
                  else " - and upstream matches at %s"
                       % manifest["upstream"].get("sha", "?")[:12]))
    report(findings, summary)
    return 1 if (findings and args.strict) else 0
```

- [ ] **Step 4: Run test to verify it passes**

```bash
cd "c:/Repo2/workflow daily work/plugins/dev-workflows/scripts" && python test_check_vendored_superpowers.py
```

Expected: PASS — `45/45 passed`

Then confirm the full run against the real tree, including upstream mode:

```bash
cd "c:/Repo2/workflow daily work" && python plugins/dev-workflows/scripts/check_vendored_superpowers.py --upstream-dir "$HOME/.claude/plugins/cache/claude-plugins-official/superpowers/b36e0829c6d0" --strict; echo "exit=$?"
```

Expected: no findings, `exit=0`.

- [ ] **Step 5: Commit**

```bash
cd "c:/Repo2/workflow daily work" && git add plugins/dev-workflows/scripts/ && git commit -m "feat(dev-workflows): report format, --strict gate and the live regression guard"
```

---

### Task 9: The resync procedure document

**Files:**
- Create: `plugins/dev-workflows/references/resync-superpowers.md`

**Interfaces:**
- Consumes: the finished checker (Tasks 1-8)
- Produces: nothing code-facing

- [ ] **Step 1: Write the document**

Write `plugins/dev-workflows/references/resync-superpowers.md` with **CRLF** line endings. It opens with one overview Mermaid diagram per the repo's diagram convention, and it contains **no line numbers anywhere** — the program computes those (ADR 0075).

Required content, in this order:

1. **Overview diagram** — a `graph TD` of the resync loop: resolve the sha → re-copy all 21 → re-apply the rewrite classes → run the checker → repair → re-run until exit 0 → re-emit the manifest → commit.
2. **The one network step**, verbatim and copy-pasteable:
   ```bash
   git ls-remote https://github.com/obra/superpowers HEAD
   ```
   Compare against `upstream.sha` in the manifest. If unchanged, there is nothing to resync.
3. **Why all 21 files are re-copied, never a subset** — one sha governs the whole set; a partial resync spreads it across several shas and the checker can no longer tell "we edited it" from "upstream moved it" (ADR 0075).
4. **The six rewrite classes**, described by *what to look for*, never by file:line:
   - class 1 — `code-reviewer.md` and `task-reviewer-prompt.md` only: four sections each replaced by one `## Review method` block delegating to `scrutinize-dispatch`; `code-reviewer.md`'s `## Example Output` deleted outright; the `**Reviewer returns:**` line rewritten in both. `re-review-prompt.md` is **excluded** — it stays verbatim.
   - class 2 — cross-skill relative paths get the `sp-` prefix; `executing-plans`' path into `using-superpowers/references/` becomes a qualified `superpowers:` mention.
   - class 3 — `brainstorming`'s plugin-root-relative path to its visual companion becomes skill-relative.
   - class 4 — qualified handoffs naming one of the six become short `sp-` names. **Bare names count too** — that omission was the Critical defect.
   - class 5 — frontmatter `name` and `description`, each description naming the upstream skill it displaces.
   - class 6 — upstream's `Strengths:` clause substituted in two example transcripts, because the dispatch engine forbids a Strengths section.
5. **The three traps**, with what each one means if it fires (copy the `repair` strings from `check_upstream_traps`).
6. **Running the checker** — both invocations, and the exit codes.
7. **Re-emitting the manifest** — `--emit-manifest` writes nothing, so redirect it **to a temp file and then move it into place**. Never redirect onto the manifest itself: the shell truncates it before the program starts, the hand-written keys read as absent, and they are lost with no error. The program refuses with exit 2 when it sees the truncated file, but document the correct command, not the recovery:
   ```bash
   python plugins/dev-workflows/scripts/check_vendored_superpowers.py \
     --emit-manifest --upstream-dir "$UP" > /tmp/manifest.new.json && \
     mv /tmp/manifest.new.json plugins/dev-workflows/references/vendored-superpowers.json
   ```
   Any permit entry it marks `REVIEW:` must be judged by a person before commit.
8. **Two honest limits, stated plainly:**
   - The checker asserts that the routing *reference exists*, not that a dispatch obeys it. `task-reviewer-prompt.md` has never been driven live; only `code-reviewer.md` has.
   - Whether the harness accepts a **bare** skill literal is still unmeasured. Do not read a green run as settling it.

- [ ] **Step 2: Verify the file's line endings and diagram**

```bash
cd "c:/Repo2/workflow daily work" && python -c "
b=open(r'plugins/dev-workflows/references/resync-superpowers.md','rb').read()
c=b.count(b'\r\n'); l=b.count(b'\n')-c
t=b.decode('utf-8')
print('CRLF=%d LF=%d' % (c,l))
print('mermaid blocks:', t.count('\`\`\`mermaid'))
import re
print('line-number refs (must be 0):', len(re.findall(r'\.md:\d+', t)))
assert l==0 and t.count('\`\`\`mermaid')>=1 and not re.findall(r'\.md:\d+', t)
print('OK')
"
```

Expected: `LF=0`, at least one mermaid block, zero `file.md:NN` references, `OK`.

- [ ] **Step 3: Commit**

```bash
cd "c:/Repo2/workflow daily work" && git add plugins/dev-workflows/references/resync-superpowers.md && git commit -m "docs(dev-workflows): the resync procedure - six rewrite classes and three traps, no line numbers"
```

---

### Task 10: Version bump and discoverability

**Files:**
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`
- Modify: `CLAUDE.md`

**Interfaces:**
- Consumes: nothing
- Produces: nothing

- [ ] **Step 1: Re-mint the version from the global max**

```bash
cd "c:/Repo2/workflow daily work" && for r in $(git for-each-ref --format='%(refname)' refs/heads refs/remotes); do git show "$r:plugins/dev-workflows/.claude-plugin/plugin.json" 2>/dev/null | grep '"version"'; done | sort -u
```

Expected: `0.38.0` only. If anything higher appears, mint from **that** max instead of `0.39.0` — a parallel session bumped it and git will merge both without a conflict.

- [ ] **Step 2: Bump both files to 0.39.0**

Set `"version": "0.39.0"` in `plugins/dev-workflows/.claude-plugin/plugin.json`, and in the `dev-workflows` entry of `.claude-plugin/marketplace.json`. CLAUDE.md requires these two to match exactly.

- [ ] **Step 3: Add the pointer to CLAUDE.md**

In the **Key commands** section, after the existing `setup_check.ps1` block, add:

````markdown
# Check the vendored superpowers copies (report-only; --strict to gate)
python plugins/dev-workflows/scripts/check_vendored_superpowers.py --strict
````

And in the **Conventions** section, after the minted-counters bullet, add:

```markdown
- **The vendored `superpowers` copies are guarded by a checker, not by review.**
  `plugins/dev-workflows/scripts/check_vendored_superpowers.py` reports drift in the 21
  copies and the 2 frozen files against
  `plugins/dev-workflows/references/vendored-superpowers.json`. Run it with `--strict`
  before merging anything that touches `skills/sp-*` or `skills/scrutinize/`. Never glob
  `skills/sp-*` to find the copy set — `sp-grill-with-doc` wears the prefix and is not a
  copy. The procedure is `references/resync-superpowers.md` (ADRs 0075, 0085-0088).
```

- [ ] **Step 4: Verify version parity and that the checker still passes**

```bash
cd "c:/Repo2/workflow daily work" && grep -h '"version"' plugins/dev-workflows/.claude-plugin/plugin.json && grep -A3 '"name": "dev-workflows"' .claude-plugin/marketplace.json | grep version
cd "c:/Repo2/workflow daily work" && python plugins/dev-workflows/scripts/check_vendored_superpowers.py --strict; echo "checker exit=$?"
cd "c:/Repo2/workflow daily work" && claude plugin validate plugins/dev-workflows; echo "validate exit=$?"
```

Expected: both versions read `0.39.0`, checker `exit=0`, validation passes.

- [ ] **Step 5: Commit**

```bash
cd "c:/Repo2/workflow daily work" && git add plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json CLAUDE.md && git commit -m "chore(dev-workflows): 0.39.0 - ship the resync checker and point CLAUDE.md at it"
```

---

## Self-review notes

**Spec coverage.** Every numbered check in the spec maps to a task: checks 1, 2, 6 → Task 2; check 3 → Task 3; checks 4, 5 → Task 4; check 7 → Task 6; checks 8-10 → Task 7. The manifest schema → Task 5. Report format and exit codes → Task 8. The procedure document → Task 9. The version bump → Task 10. `--emit-manifest` → Task 5. Three further tests were added by review - a governed-directory case (T2), a duplicate-permit-entry case (T3) and the truncated-manifest guard (T5) - taking the suite to 45. All 19 spec test cases appear: 1-2 (T2), 3-4 (T3), 5 (T2), 6-7 (T4), 8-9 (T4), 10 (T2), 11-12 (T2), 13-14 (T1, T8), 15 (T6), 16-18 (T7), 19 (T6).

**Type consistency.** `finding()` returns a dict with keys `check`, `path`, `message`, `repair`, used identically by every `check_*` function and by `report()`. Every `check_*` takes `(root, manifest)` except the two upstream ones, which take `(root, upstream_root, manifest)` and `(upstream_root, manifest)` — matching how `run_checks` calls them. `read_normalized` returns `bytes`; `read_text` returns `str`; `content_hash` takes `bytes`. `emit_manifest(root, upstream_root, previous)` matches its three call sites.

**One deliberate ordering constraint.** In Task 5, the `--emit-manifest` block must sit **above** the `load_manifest` call in `main`, because bootstrapping runs before any manifest exists. Task 5 Step 3 says so explicitly.
