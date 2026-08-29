# npx Install Channel Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make every skill in this marketplace installable on its own with `npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill <name>`, and the whole set with `--all`, by generating a self-contained `skills/` tree that CI keeps in sync.

**Architecture:** A generator reads the 55 authored skills under `plugins/*/skills/` and writes a resolved copy of each into `skills/<name>/` at the repo root. "Resolved" means every `${CLAUDE_PLUGIN_ROOT}/…` reference has been rewritten and the file it names has been copied into the skill directory, together with anything that file imports. A checker regenerates into a temp directory and fails if the committed tree differs. GitHub Actions runs the checker on every push.

**Tech Stack:** Python 3.9+ standard library only (no PyYAML, no pytest — the repo's test harness is a `__main__` block that runs `test_*` functions and exits 1 on failure, matching `plugins/dev-workflows/scripts/test_check_plugin_copies.py`). GitHub Actions for CI.

**Spec:** [docs/superpowers/specs/2026-08-29-npx-skills-install-channel-design.md](../specs/2026-08-29-npx-skills-install-channel-design.md)

## Global Constraints

- **Stdlib only.** The generator, the checker and their tests import nothing outside the Python standard library. CI installs no packages.
- **The tree is generated, never hand-edited.** Nothing in this plan writes `skills/` by hand except through `generate_skills_tree.py`.
- **All 55 skill directories are generated** (ADR 0161) — no conditional membership.
- **Rewrite rule** (ADR 0164): a `.md` target becomes a path relative to the skill directory; every other target becomes `${CLAUDE_SKILL_DIR}/<path>`. A target the rule cannot classify falls back to `${CLAUDE_SKILL_DIR}`, which is always correct in Claude Code.
- **No `${CLAUDE_PLUGIN_ROOT}` token may survive** anywhere under `skills/`.
- **Directory name equals frontmatter `name`** for every generated skill (ADR 0162).
- **Excluded from copying:** files whose basename starts with `test_`, and anything under a `fixtures/` directory — *unless* a `SKILL.md` names the file directly (ADR 0155; `sa-doc` relies on the override for `scripts/fixtures/sa-model-bookstore.yaml`).
- **`${CLAUDE_PLUGIN_ROOT}/...`** (literal three dots) in `ado-create-work-items` is prose about quoting, not a reference. It must never be treated as a path.
- **Licence files** (ADR 0158): `LICENSE-superpowers` into each of `sp-brainstorming`, `sp-executing-plans`, `sp-grill-with-doc` is **not** included — only the six vendored copies: `sp-brainstorming`, `sp-executing-plans`, `sp-receiving-code-review`, `sp-requesting-code-review`, `sp-subagent-driven-development`, `sp-writing-plans`. `LICENSE-mattpocock-skills` into `wait-what`.
- **Commit style:** `<type>(<scope>): <subject>`, one commit per task, matching the repo's history.

---

## File Structure

| Path | Responsibility |
|---|---|
| `scripts/generate_skills_tree.py` | Discovery, reference scanning, dependency resolution, rewriting, emission. Importable; `main()` is the CLI. |
| `scripts/check_skills_tree.py` | Imports the generator, regenerates into a temp dir, diffs against `skills/`, asserts the invariants. Reports and exits non-zero; never writes to `skills/`. |
| `scripts/test_generate_skills_tree.py` | Tests for the generator, against synthetic fixture repos. |
| `scripts/test_check_skills_tree.py` | Tests for the checker. |
| `.github/workflows/skills-tree.yml` | Runs both test suites and the checker on push and pull request. |
| `skills/**` | The generated tree. 55 directories. Never hand-edited. |
| `INSTALL.md` | The channel guide — everything that churns (ADR 0160). |
| `README.md` | Install block gains two npx lines (ADRs 0160, 0163). |

---

### Task 1: Rename the two colliding github-backlog skills

The generator's uniqueness invariant depends on 55 distinct frontmatter names, so this lands first. The CLI keys on frontmatter `name`, not the directory (ADR 0162), so both must change.

**Files:**
- Rename: `plugins/github-backlog/skills/extract-findings/` → `plugins/github-backlog/skills/github-extract-findings/`
- Rename: `plugins/github-backlog/skills/triage-findings/` → `plugins/github-backlog/skills/github-triage-findings/`
- Modify: the `name:` line in each renamed `SKILL.md`
- Modify: `plugins/github-backlog/skills/findings-to-github-issues/SKILL.md`
- Modify: `plugins/github-backlog/skills/github-writeback-tracking/SKILL.md`
- Modify: `plugins/github-backlog/skills/classify-github-issues/SKILL.md`
- Modify: `plugins/github-backlog/references/data-contracts.md`
- Modify: `plugins/github-backlog/README.md`
- Modify: `docs/ARCHITECTURE.md`
- Modify: `plugins/github-backlog/.claude-plugin/plugin.json` (version bump)

**Interfaces:**
- Consumes: nothing.
- Produces: 55 distinct skill names across the marketplace. Every later task assumes `github-extract-findings` and `github-triage-findings` exist.

- [ ] **Step 1: Prove the collision exists before changing anything**

```bash
cd "$(git rev-parse --show-toplevel)"
for d in plugins/*/skills/*/; do basename "$d"; done | sort | uniq -d
```

Expected output — exactly these two lines:

```text
extract-findings
triage-findings
```

- [ ] **Step 2: Rename both directories with git**

```bash
git mv plugins/github-backlog/skills/extract-findings \
       plugins/github-backlog/skills/github-extract-findings
git mv plugins/github-backlog/skills/triage-findings \
       plugins/github-backlog/skills/github-triage-findings
```

- [ ] **Step 3: Change the frontmatter name in each renamed skill**

```bash
sed -i '' 's/^name: extract-findings$/name: github-extract-findings/' \
  plugins/github-backlog/skills/github-extract-findings/SKILL.md
sed -i '' 's/^name: triage-findings$/name: github-triage-findings/' \
  plugins/github-backlog/skills/github-triage-findings/SKILL.md
```

On Linux (and in CI) use `sed -i` with no `''` argument. Verify:

```bash
grep -h '^name:' plugins/github-backlog/skills/github-*-findings/SKILL.md
```

Expected:

```text
name: github-extract-findings
name: github-triage-findings
```

- [ ] **Step 4: Update every live reference in the github-backlog plugin**

Only files inside `plugins/github-backlog/` and `docs/ARCHITECTURE.md` are rewritten. Do **not** touch `docs/superpowers/plans/` or `docs/superpowers/specs/` — those are historical records (spec §6).

```bash
for f in plugins/github-backlog/skills/findings-to-github-issues/SKILL.md \
         plugins/github-backlog/skills/github-writeback-tracking/SKILL.md \
         plugins/github-backlog/skills/classify-github-issues/SKILL.md \
         plugins/github-backlog/references/data-contracts.md \
         plugins/github-backlog/README.md; do
  python3 - "$f" <<'PY'
import io, re, sys
p = sys.argv[1]
s = io.open(p, encoding='utf-8').read()
s = re.sub(r'(?<![\w-])extract-findings(?![\w-])', 'github-extract-findings', s)
s = re.sub(r'(?<![\w-])triage-findings(?![\w-])', 'github-triage-findings', s)
s = s.replace('github-github-', 'github-')
io.open(p, 'w', encoding='utf-8').write(s)
print('rewrote', p)
PY
done
```

The `github-github-` collapse is load-bearing: the negative lookbehind stops at a hyphen, so a string already reading `github-extract-findings` would otherwise become `github-github-extract-findings` on a second run. This makes the edit idempotent.

- [ ] **Step 5: Update `docs/ARCHITECTURE.md` by hand**

That file names both plugins' pipelines, so a blind substitution would rename ADO's skills too. Open it, find the four mentions, and change **only** the ones in the GitHub Issues pipeline section. Verify afterwards that ADO's are untouched:

```bash
grep -n 'extract-findings\|triage-findings' docs/ARCHITECTURE.md
```

Every remaining bare `extract-findings` / `triage-findings` must be in an ADO context; every GitHub one must now read `github-…`.

- [ ] **Step 6: Verify no live reference to the old names survives**

```bash
grep -rn '\(^\|[^-]\)\(extract\|triage\)-findings' \
  plugins/github-backlog/ | grep -v 'github-extract\|github-triage'
```

Expected: no output.

- [ ] **Step 7: Verify the collision is gone**

```bash
for d in plugins/*/skills/*/; do basename "$d"; done | sort | uniq -d
```

Expected: no output. And the count is still 55:

```bash
ls -d plugins/*/skills/*/ | wc -l
```

Expected: `55`.

- [ ] **Step 8: Bump the plugin version**

Edit `plugins/github-backlog/.claude-plugin/plugin.json` and the matching `version` in `.claude-plugin/marketplace.json`'s `github-backlog` entry from `0.1.0` to `0.2.0`. Both must match — the marketplace carries a copy.

```bash
grep -n '"version"' plugins/github-backlog/.claude-plugin/plugin.json
python3 -c "import json;d=json.load(open('.claude-plugin/marketplace.json'));print([p['version'] for p in d['plugins'] if p['name']=='github-backlog'])"
```

Both must print `0.2.0`.

- [ ] **Step 9: Commit**

```bash
git add -A plugins/github-backlog docs/ARCHITECTURE.md .claude-plugin/marketplace.json
git commit -m "refactor(github-backlog): prefix the two skills that collided with ado-backlog (ADR 0156)"
```

---

### Task 2: Skill discovery and reference scanning

**Files:**
- Create: `scripts/generate_skills_tree.py`
- Create: `scripts/test_generate_skills_tree.py`

**Interfaces:**
- Consumes: the 55 renamed skill directories from Task 1.
- Produces:
  - `discover_skills(repo) -> list[Skill]` where `Skill` is a `namedtuple('Skill', 'plugin name src_dir')` — `plugin` is the plugin directory name, `name` is the frontmatter `name`, `src_dir` is the absolute source directory.
  - `frontmatter_name(text) -> str | None`
  - `plugin_root_refs(text) -> list[str]` — the relative paths named after `${CLAUDE_PLUGIN_ROOT}/`, de-duplicated, order preserved, prose ellipses excluded.

- [ ] **Step 1: Write the failing test**

Create `scripts/test_generate_skills_tree.py`:

```python
#!/usr/bin/env python3
"""Tests for generate_skills_tree.py.
Run: python3 scripts/test_generate_skills_tree.py   (from the repo root)"""
import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate_skills_tree as g


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _skill(repo, plugin, dirname, name, body=""):
    """Create one source skill and return its directory."""
    d = os.path.join(repo, "plugins", plugin, "skills", dirname)
    _write(os.path.join(d, "SKILL.md"),
           "---\nname: %s\ndescription: d\n---\n\n%s" % (name, body))
    return d


def _repo():
    return tempfile.mkdtemp(prefix="skilltree-")


def test_discover_finds_skills_across_plugins():
    repo = _repo()
    try:
        _skill(repo, "alpha", "one", "one")
        _skill(repo, "beta", "two", "two")
        found = g.discover_skills(repo)
        assert [s.name for s in found] == ["one", "two"], found
        assert [s.plugin for s in found] == ["alpha", "beta"], found
    finally:
        shutil.rmtree(repo)


def test_discover_reads_the_frontmatter_name_not_the_directory():
    repo = _repo()
    try:
        _skill(repo, "alpha", "gamma", "delta")
        found = g.discover_skills(repo)
        assert [s.name for s in found] == ["delta"], found
        assert found[0].src_dir.endswith(os.path.join("skills", "gamma"))
    finally:
        shutil.rmtree(repo)


def test_frontmatter_name_requires_the_opening_marker_on_line_one():
    assert g.frontmatter_name("---\nname: a\n---\n") == "a"
    assert g.frontmatter_name("\n---\nname: a\n---\n") is None
    assert g.frontmatter_name("no frontmatter") is None


def test_refs_collects_paths_in_order_without_duplicates():
    text = ('see `${CLAUDE_PLUGIN_ROOT}/references/x.md`\n'
            'python "${CLAUDE_PLUGIN_ROOT}/scripts/y.py" --flag\n'
            'again `${CLAUDE_PLUGIN_ROOT}/references/x.md`\n')
    assert g.plugin_root_refs(text) == ["references/x.md", "scripts/y.py"]


def test_refs_ignores_the_prose_ellipsis():
    text = 'always wrap `"${CLAUDE_PLUGIN_ROOT}/..."` when it has spaces'
    assert g.plugin_root_refs(text) == []


def test_refs_stops_at_the_closing_quote_or_backtick():
    text = 'dotnet run "${CLAUDE_PLUGIN_ROOT}/scripts/a.cs" -- "x.json"'
    assert g.plugin_root_refs(text) == ["scripts/a.cs"]
```

Append the harness at the end of the file:

```python
if __name__ == "__main__":
    TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in TESTS:
        try:
            t()
            print("PASS  %s" % t.__name__)
        except BaseException as e:
            failed += 1
            print("FAIL  %s: %s: %s" % (t.__name__, type(e).__name__, e))
    print("%d/%d passed" % (len(TESTS) - failed, len(TESTS)))
    sys.exit(1 if failed else 0)
```

- [ ] **Step 2: Run it to make sure it fails**

Run: `python3 scripts/test_generate_skills_tree.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'generate_skills_tree'`

- [ ] **Step 3: Write the minimal implementation**

Create `scripts/generate_skills_tree.py`:

```python
#!/usr/bin/env python3
"""generate_skills_tree.py - build skills/ from plugins/*/skills/.

The skills.sh CLI copies a skill DIRECTORY and nothing above it, so a skill
that names ${CLAUDE_PLUGIN_ROOT}/references/... installs and then fails. This
generator writes a resolved copy of every skill into skills/<name>/ at the
repo root: the files it names, the files those import, its vendored licence,
and its command's argument-hint (ADRs 0153-0164).

The tree is generated and committed. Never hand-edit it; check_skills_tree.py
fails the build if you do.

Usage:
  python3 scripts/generate_skills_tree.py [--repo PATH] [--out PATH]
"""
import argparse
import collections
import io
import os
import re
import sys

PLUGINS_DIRNAME = "plugins"
TREE_DIRNAME = "skills"

# A reference is ${CLAUDE_PLUGIN_ROOT}/ followed by a path. The character class
# deliberately excludes '.' as a FIRST character so the documented prose form
# ${CLAUDE_PLUGIN_ROOT}/... is not read as a path (spec, Global Constraints).
REF_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_][A-Za-z0-9_./-]*)")

Skill = collections.namedtuple("Skill", "plugin name src_dir")


def read_text(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def frontmatter_name(text):
    """The value of `name:` in the leading --- block, or None.

    Claude Code reads frontmatter only when the opening --- is the file's
    first line, so this does too.
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        if line.startswith("name:"):
            return line[len("name:"):].strip().strip('"').strip("'")
    return None


def plugin_root_refs(text):
    """Relative paths named after ${CLAUDE_PLUGIN_ROOT}/, in order, unique."""
    out = []
    for m in REF_RE.finditer(text):
        ref = m.group(1).rstrip(".,;:)")
        if ref and ref not in out:
            out.append(ref)
    return out


def discover_skills(repo):
    """Every skill under plugins/*/skills/*/SKILL.md, sorted by plugin then dir."""
    root = os.path.join(repo, PLUGINS_DIRNAME)
    found = []
    if not os.path.isdir(root):
        return found
    for plugin in sorted(os.listdir(root)):
        skills_dir = os.path.join(root, plugin, "skills")
        if not os.path.isdir(skills_dir):
            continue
        for dirname in sorted(os.listdir(skills_dir)):
            src = os.path.join(skills_dir, dirname)
            md = os.path.join(src, "SKILL.md")
            if not os.path.isfile(md):
                continue
            name = frontmatter_name(read_text(md))
            if name is None:
                continue
            found.append(Skill(plugin, name, src))
    return found
```

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `python3 scripts/test_generate_skills_tree.py`
Expected: `6/6 passed`, exit 0

- [ ] **Step 5: Run it against the real repo as a smoke check**

```bash
python3 -c "
import sys; sys.path.insert(0,'scripts')
import generate_skills_tree as g
s = g.discover_skills('.')
print(len(s), 'skills')
names = [x.name for x in s]
import collections
print('duplicate names:', [n for n,c in collections.Counter(names).items() if c>1])
"
```

Expected:

```text
55 skills
duplicate names: []
```

If the count is not 55 or duplicates appear, Task 1 is incomplete — fix that before continuing.

- [ ] **Step 6: Commit**

```bash
git add scripts/generate_skills_tree.py scripts/test_generate_skills_tree.py
git commit -m "feat(skills-tree): discover skills and scan plugin-root references"
```

---

### Task 3: Dependency resolution

Resolve each reference to a real file, then follow what that file imports. This is what brings `map_core.py` along for `chart-map` and `work-map`, which no `SKILL.md` mentions (ADR 0155).

**Files:**
- Modify: `scripts/generate_skills_tree.py`
- Modify: `scripts/test_generate_skills_tree.py`

**Interfaces:**
- Consumes: `Skill`, `plugin_root_refs` from Task 2.
- Produces:
  - `is_excluded(rel) -> bool` — True for a `test_*` basename or any path with a `fixtures` component.
  - `local_imports(py_path) -> list[str]` — module names imported by that file that exist as `.py` siblings.
  - `resolve_files(plugin_root, refs) -> dict[str, str]` — maps plugin-relative path → absolute source path, including transitively imported siblings. Explicitly named files are always included, even when `is_excluded` says otherwise.

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_generate_skills_tree.py`, above the `__main__` harness:

```python
def test_excluded_covers_test_files_and_fixtures():
    assert g.is_excluded("scripts/test_thing.py") is True
    assert g.is_excluded("scripts/fixtures/model.yaml") is True
    assert g.is_excluded("scripts/thing.py") is False
    assert g.is_excluded("references/latest_notes.md") is False


def test_local_imports_finds_only_siblings_that_exist():
    repo = _repo()
    try:
        d = os.path.join(repo, "scripts")
        _write(os.path.join(d, "a.py"),
               "import os\nimport map_core\nfrom helper import x\n")
        _write(os.path.join(d, "map_core.py"), "x = 1\n")
        found = g.local_imports(os.path.join(d, "a.py"))
        assert found == ["map_core"], found
    finally:
        shutil.rmtree(repo)


def test_resolve_pulls_a_transitive_import_no_skill_names():
    repo = _repo()
    try:
        root = os.path.join(repo, "plugins", "p")
        _write(os.path.join(root, "scripts", "local_map_ops.py"),
               "import map_core\n")
        _write(os.path.join(root, "scripts", "map_core.py"), "import deeper\n")
        _write(os.path.join(root, "scripts", "deeper.py"), "x = 1\n")
        got = g.resolve_files(root, ["scripts/local_map_ops.py"])
        assert sorted(got) == ["scripts/deeper.py",
                               "scripts/local_map_ops.py",
                               "scripts/map_core.py"], sorted(got)
    finally:
        shutil.rmtree(repo)


def test_resolve_skips_excluded_siblings_but_honours_a_named_one():
    repo = _repo()
    try:
        root = os.path.join(repo, "plugins", "p")
        _write(os.path.join(root, "scripts", "a.py"), "import test_a\n")
        _write(os.path.join(root, "scripts", "test_a.py"), "x = 1\n")
        _write(os.path.join(root, "scripts", "fixtures", "m.yaml"), "k: v\n")
        got = g.resolve_files(root, ["scripts/a.py"])
        assert sorted(got) == ["scripts/a.py"], sorted(got)
        got2 = g.resolve_files(root, ["scripts/a.py", "scripts/fixtures/m.yaml"])
        assert sorted(got2) == ["scripts/a.py", "scripts/fixtures/m.yaml"], sorted(got2)
    finally:
        shutil.rmtree(repo)


def test_resolve_raises_on_a_reference_that_does_not_exist():
    repo = _repo()
    try:
        root = os.path.join(repo, "plugins", "p")
        os.makedirs(root)
        try:
            g.resolve_files(root, ["references/missing.md"])
            raise AssertionError("expected MissingReference")
        except g.MissingReference as e:
            assert "references/missing.md" in str(e), e
    finally:
        shutil.rmtree(repo)
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 scripts/test_generate_skills_tree.py`
Expected: five FAIL lines reporting `AttributeError: module 'generate_skills_tree' has no attribute 'is_excluded'` (and the same for `local_imports`, `resolve_files`, `MissingReference`).

- [ ] **Step 3: Write the implementation**

Append to `scripts/generate_skills_tree.py`:

```python
IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)


class MissingReference(Exception):
    """A SKILL.md names a file that is not in its plugin."""


def is_excluded(rel):
    """Test files and fixtures do not travel unless a SKILL.md names them."""
    parts = rel.split("/")
    if "fixtures" in parts[:-1] or parts[-1] == "fixtures":
        return True
    return parts[-1].startswith("test_")


def local_imports(py_path):
    """Module names imported by py_path that exist as .py siblings.

    A regex, not ast.parse: the sources are this repo's own scripts, and a
    file that fails to parse must not take the whole build down with it.
    """
    directory = os.path.dirname(py_path)
    out = []
    for mod in IMPORT_RE.findall(read_text(py_path)):
        if mod in out:
            continue
        if os.path.isfile(os.path.join(directory, mod + ".py")):
            out.append(mod)
    return out


def resolve_files(plugin_root, refs):
    """Every file a skill needs: what it names, plus transitive local imports.

    Returns {plugin-relative path: absolute source path}. A named file is
    always included; an excluded file reached only by import is dropped.
    """
    resolved = {}
    queue = [(r, True) for r in refs]
    while queue:
        rel, named = queue.pop(0)
        if rel in resolved:
            continue
        absolute = os.path.join(plugin_root, rel.replace("/", os.sep))
        if not os.path.isfile(absolute):
            if named:
                raise MissingReference(
                    "%s names %s, which does not exist" % (plugin_root, rel))
            continue
        if not named and is_excluded(rel):
            continue
        resolved[rel] = absolute
        if rel.endswith(".py"):
            parent = os.path.dirname(rel)
            for mod in local_imports(absolute):
                sibling = "%s/%s.py" % (parent, mod) if parent else mod + ".py"
                queue.append((sibling, False))
    return resolved
```

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `python3 scripts/test_generate_skills_tree.py`
Expected: `11/11 passed`, exit 0

- [ ] **Step 5: Prove it against the real `chart-map`, the case that motivated the rule**

```bash
python3 -c "
import sys; sys.path.insert(0,'scripts')
import generate_skills_tree as g, os
src='plugins/decision-map/skills/chart-map'
refs=g.plugin_root_refs(g.read_text(os.path.join(src,'SKILL.md')))
files=g.resolve_files('plugins/decision-map', refs)
print('named:', refs)
print('resolved:', sorted(files))
"
```

Expected: `resolved` includes `scripts/map_core.py`, which is **not** in `named`. If it is missing, the import tracing is broken.

- [ ] **Step 6: Commit**

```bash
git add scripts/generate_skills_tree.py scripts/test_generate_skills_tree.py
git commit -m "feat(skills-tree): follow local imports so a bundled script arrives whole (ADR 0155)"
```

---

### Task 4: Rewriting and emitting one skill

**Files:**
- Modify: `scripts/generate_skills_tree.py`
- Modify: `scripts/test_generate_skills_tree.py`

**Interfaces:**
- Consumes: `resolve_files` from Task 3.
- Produces:
  - `rewrite_refs(text) -> str` — `.md` targets become relative, everything else becomes `${CLAUDE_SKILL_DIR}/…`.
  - `apply_argument_hint(text, hint) -> str` — inserts or replaces `argument-hint:` in the frontmatter.
  - `licence_for(name) -> str | None` — the licence filename a vendored skill carries.
  - `emit_skill(skill, out_root, hints) -> str` — writes one generated directory and returns its path.

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_generate_skills_tree.py`:

```python
def test_rewrite_sends_md_relative_and_everything_else_to_skill_dir():
    text = ('see `${CLAUDE_PLUGIN_ROOT}/references/x.md`\n'
            'python "${CLAUDE_PLUGIN_ROOT}/scripts/y.py"\n'
            'load "${CLAUDE_PLUGIN_ROOT}/scripts/fixtures/m.yaml"\n')
    out = g.rewrite_refs(text)
    assert "`references/x.md`" in out, out
    assert '"${CLAUDE_SKILL_DIR}/scripts/y.py"' in out, out
    assert '"${CLAUDE_SKILL_DIR}/scripts/fixtures/m.yaml"' in out, out
    assert "CLAUDE_PLUGIN_ROOT" not in out, out


def test_rewrite_leaves_the_prose_ellipsis_alone():
    text = 'always wrap `"${CLAUDE_PLUGIN_ROOT}/..."`'
    assert g.rewrite_refs(text) == text


def test_argument_hint_is_inserted_after_description():
    text = "---\nname: a\ndescription: d\n---\n\nbody\n"
    out = g.apply_argument_hint(text, '"[x]"')
    assert out == '---\nname: a\ndescription: d\nargument-hint: "[x]"\n---\n\nbody\n', out


def test_argument_hint_replaces_an_existing_one():
    text = '---\nname: a\nargument-hint: "[old]"\n---\n\nbody\n'
    out = g.apply_argument_hint(text, '"[new]"')
    assert 'argument-hint: "[new]"' in out and "[old]" not in out, out


def test_licence_mapping_covers_the_seven_vendored_skills():
    assert g.licence_for("wait-what") == "LICENSE-mattpocock-skills"
    assert g.licence_for("sp-writing-plans") == "LICENSE-superpowers"
    assert g.licence_for("sp-grill-with-doc") is None
    assert g.licence_for("grill-then-plan") is None


def test_emit_writes_skill_files_and_the_named_reference():
    repo = _repo()
    try:
        src = _skill(repo, "p", "one", "one",
                     'run `${CLAUDE_PLUGIN_ROOT}/scripts/y.py`\n')
        _write(os.path.join(repo, "plugins", "p", "scripts", "y.py"), "x = 1\n")
        out = os.path.join(repo, "skills")
        g.emit_skill(g.Skill("p", "one", src), out, {})
        md = io.open(os.path.join(out, "one", "SKILL.md"), encoding="utf-8").read()
        assert "${CLAUDE_SKILL_DIR}/scripts/y.py" in md, md
        assert os.path.isfile(os.path.join(out, "one", "scripts", "y.py"))
    finally:
        shutil.rmtree(repo)


def test_emit_uses_the_frontmatter_name_as_the_directory():
    repo = _repo()
    try:
        src = _skill(repo, "p", "gamma", "delta")
        out = os.path.join(repo, "skills")
        g.emit_skill(g.Skill("p", "delta", src), out, {})
        assert os.path.isdir(os.path.join(out, "delta"))
        assert not os.path.isdir(os.path.join(out, "gamma"))
    finally:
        shutil.rmtree(repo)
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 scripts/test_generate_skills_tree.py`
Expected: seven FAIL lines reporting missing attributes `rewrite_refs`, `apply_argument_hint`, `licence_for`, `emit_skill`.

- [ ] **Step 3: Write the implementation**

Append to `scripts/generate_skills_tree.py`:

```python
# The rewritten form rewrite_refs() produces, so Task 6's checker can prove
# each target landed in the directory the CLI will copy.
SKILL_DIR_REF_RE = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/([A-Za-z0-9_][A-Za-z0-9_./-]*)")

SUPERPOWERS_LICENCE = "LICENSE-superpowers"
MATTPOCOCK_LICENCE = "LICENSE-mattpocock-skills"

VENDORED = {
    "sp-brainstorming": SUPERPOWERS_LICENCE,
    "sp-executing-plans": SUPERPOWERS_LICENCE,
    "sp-receiving-code-review": SUPERPOWERS_LICENCE,
    "sp-requesting-code-review": SUPERPOWERS_LICENCE,
    "sp-subagent-driven-development": SUPERPOWERS_LICENCE,
    "sp-writing-plans": SUPERPOWERS_LICENCE,
    "wait-what": MATTPOCOCK_LICENCE,
}


def licence_for(name):
    """The licence file a vendored skill must carry (ADR 0158)."""
    return VENDORED.get(name)


def rewrite_refs(text):
    """Rewrite plugin-root references by kind (ADR 0164).

    A .md target becomes a path relative to the skill directory - the Agent
    Skills standard form. Everything else becomes ${CLAUDE_SKILL_DIR}/..., so
    a Bash command resolves from any working directory. An unclassifiable
    target falls back to ${CLAUDE_SKILL_DIR}, which is never wrong in
    Claude Code.
    """
    def sub(m):
        ref = m.group(1)
        trailing = ""
        while ref and ref[-1] in ".,;:)":
            trailing = ref[-1] + trailing
            ref = ref[:-1]
        if not ref:
            return m.group(0)
        if ref.endswith(".md"):
            return ref + trailing
        return "${CLAUDE_SKILL_DIR}/" + ref + trailing
    return REF_RE.sub(sub, text)


def apply_argument_hint(text, hint):
    """Set argument-hint in the leading frontmatter block."""
    if not hint or not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    head, tail = text[3:end], text[end:]
    lines = [ln for ln in head.splitlines() if not ln.startswith("argument-hint:")]
    inserted = False
    out = []
    for ln in lines:
        out.append(ln)
        if not inserted and ln.startswith("description:"):
            out.append("argument-hint: " + hint)
            inserted = True
    if not inserted:
        out.append("argument-hint: " + hint)
    return "---" + "\n".join(out) + tail


def emit_skill(skill, out_root, hints):
    """Write one resolved skill directory. Returns its path."""
    # src_dir is <repo>/plugins/<plugin>/skills/<dirname>; up two is the plugin.
    plugin_root = os.path.dirname(os.path.dirname(skill.src_dir))
    dest = os.path.join(out_root, skill.name)
    os.makedirs(dest, exist_ok=True)

    for entry in sorted(os.listdir(skill.src_dir)):
        source = os.path.join(skill.src_dir, entry)
        target = os.path.join(dest, entry)
        if os.path.isdir(source):
            _copy_tree(source, target)
        else:
            _copy_file(source, target, rewrite=entry.endswith(".md"))

    md_path = os.path.join(dest, "SKILL.md")
    text = read_text(md_path)
    hint = hints.get(skill.name)
    if hint:
        text = apply_argument_hint(text, hint)
        _write_text(md_path, text)

    refs = plugin_root_refs(read_text(os.path.join(skill.src_dir, "SKILL.md")))
    for rel, absolute in sorted(resolve_files(plugin_root, refs).items()):
        target = os.path.join(dest, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        _copy_file(absolute, target, rewrite=rel.endswith(".md"))

    licence = licence_for(skill.name)
    if licence:
        _copy_file(os.path.join(plugin_root, licence),
                   os.path.join(dest, licence), rewrite=False)
    return dest


def _write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _copy_file(source, target, rewrite):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if rewrite:
        _write_text(target, rewrite_refs(read_text(source)))
    else:
        with open(source, "rb") as fsrc, open(target, "wb") as fdst:
            fdst.write(fsrc.read())


def _copy_tree(source, target):
    for root, _dirs, files in os.walk(source):
        for entry in sorted(files):
            src = os.path.join(root, entry)
            rel = os.path.relpath(src, source)
            _copy_file(src, os.path.join(target, rel),
                       rewrite=entry.endswith(".md"))
```

Note `plugin_root_refs` is read from the **source** `SKILL.md`, not the already-rewritten copy — after rewriting there are no plugin-root tokens left to find.

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `python3 scripts/test_generate_skills_tree.py`
Expected: `18/18 passed`, exit 0

- [ ] **Step 5: Commit**

```bash
git add scripts/generate_skills_tree.py scripts/test_generate_skills_tree.py
git commit -m "feat(skills-tree): rewrite references, carry the licence and the argument-hint (ADRs 0157, 0158, 0164)"
```

---

### Task 5: The generator CLI, and the committed tree

**Files:**
- Modify: `scripts/generate_skills_tree.py`
- Modify: `scripts/test_generate_skills_tree.py`
- Create: `skills/**` (55 directories, generated)
- Modify: `.gitignore` (assert the tree is **not** ignored)

**Interfaces:**
- Consumes: `emit_skill` from Task 4.
- Produces:
  - `collect_argument_hints(repo) -> dict[str, str]` — skill name → hint, only where exactly one command names that skill with a non-empty hint.
  - `build(repo, out_root) -> list[str]` — emits every skill, returns the generated directory names.
  - `main(argv=None) -> int` — the CLI.

- [ ] **Step 1: Write the failing tests**

Append to `scripts/test_generate_skills_tree.py`:

```python
def _command(repo, plugin, filename, skill, hint):
    body = "---\ndescription: d\n"
    if hint is not None:
        body += "argument-hint: %s\n" % hint
    body += "---\n\nUse the **`%s`** skill.\n" % skill
    _write(os.path.join(repo, "plugins", plugin, "commands", filename), body)


def test_hints_are_collected_from_commands_that_name_one_skill():
    repo = _repo()
    try:
        _command(repo, "p", "run.md", "orchestrator", '"[path]"')
        assert g.collect_argument_hints(repo) == {"orchestrator": '"[path]"'}
    finally:
        shutil.rmtree(repo)


def test_an_empty_hint_is_not_collected():
    repo = _repo()
    try:
        _command(repo, "p", "a.md", "one", '""')
        _command(repo, "p", "b.md", "two", None)
        assert g.collect_argument_hints(repo) == {}
    finally:
        shutil.rmtree(repo)


def test_two_commands_hinting_the_same_skill_collect_neither():
    repo = _repo()
    try:
        _command(repo, "p", "a.md", "one", '"[x]"')
        _command(repo, "q", "b.md", "one", '"[y]"')
        assert g.collect_argument_hints(repo) == {}
    finally:
        shutil.rmtree(repo)


def test_build_emits_one_directory_per_skill_and_clears_stale_ones():
    repo = _repo()
    try:
        _skill(repo, "p", "one", "one")
        _skill(repo, "p", "two", "two")
        out = os.path.join(repo, "skills")
        os.makedirs(os.path.join(out, "stale"))
        _write(os.path.join(out, "stale", "SKILL.md"), "---\nname: stale\n---\n")
        built = g.build(repo, out)
        assert built == ["one", "two"], built
        assert sorted(os.listdir(out)) == ["one", "two"], os.listdir(out)
    finally:
        shutil.rmtree(repo)
```

- [ ] **Step 2: Run to verify they fail**

Run: `python3 scripts/test_generate_skills_tree.py`
Expected: four FAIL lines for missing `collect_argument_hints` and `build`.

- [ ] **Step 3: Write the implementation**

Append to `scripts/generate_skills_tree.py`:

```python
SKILL_REF_RE = re.compile(r"\*\*`?([a-z0-9][a-z0-9-]*)`?\*\*")
HINT_RE = re.compile(r"^argument-hint:\s*(.+?)\s*$", re.M)


def collect_argument_hints(repo):
    """skill name -> argument-hint, from the command wrappers (ADR 0157).

    Only an unambiguous pairing is carried: exactly one command naming that
    skill, with a non-empty hint. Two commands hinting one skill, or a command
    that names no skill, are skipped rather than guessed at.
    """
    root = os.path.join(repo, PLUGINS_DIRNAME)
    seen = {}
    if not os.path.isdir(root):
        return {}
    for plugin in sorted(os.listdir(root)):
        commands = os.path.join(root, plugin, "commands")
        if not os.path.isdir(commands):
            continue
        for entry in sorted(os.listdir(commands)):
            if not entry.endswith(".md"):
                continue
            text = read_text(os.path.join(commands, entry))
            hint_match = HINT_RE.search(text)
            skill_match = SKILL_REF_RE.search(text)
            if not hint_match or not skill_match:
                continue
            hint = hint_match.group(1)
            if hint in ('""', "''", ""):
                continue
            seen.setdefault(skill_match.group(1), []).append(hint)
    return dict((k, v[0]) for k, v in seen.items() if len(v) == 1)


def build(repo, out_root):
    """Emit every skill into out_root, replacing whatever was there."""
    skills = discover_skills(repo)
    hints = collect_argument_hints(repo)
    names = set(s.name for s in skills)
    if os.path.isdir(out_root):
        for entry in sorted(os.listdir(out_root)):
            path = os.path.join(out_root, entry)
            if os.path.isdir(path) and entry not in names:
                _remove_tree(path)
    for skill in skills:
        dest = os.path.join(out_root, skill.name)
        if os.path.isdir(dest):
            _remove_tree(dest)
        emit_skill(skill, out_root, hints)
    return sorted(names)


def _remove_tree(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))
    os.rmdir(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    parser.add_argument("--out", default=None,
                        help="defaults to <repo>/skills")
    args = parser.parse_args(argv)
    out = args.out or os.path.join(args.repo, TREE_DIRNAME)
    built = build(args.repo, out)
    print("generated %d skills into %s" % (len(built), out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `python3 scripts/test_generate_skills_tree.py`
Expected: `22/22 passed`, exit 0

- [ ] **Step 5: Confirm the tree is not gitignored**

```bash
git check-ignore -v skills 2>&1 || echo "not ignored - good"
```

Expected: `not ignored - good`. If a rule matches, add a negation to `.gitignore` before continuing — a silently ignored tree would ship nothing.

- [ ] **Step 6: Generate the real tree**

```bash
python3 scripts/generate_skills_tree.py --repo .
```

Expected: `generated 55 skills into ./skills`

- [ ] **Step 7: Verify the invariants by hand before trusting the checker**

```bash
echo "directories: $(ls -d skills/*/ | wc -l | tr -d ' ')"
echo "surviving plugin-root tokens: $(grep -rl 'CLAUDE_PLUGIN_ROOT' skills/ | wc -l | tr -d ' ')"
echo "dir != frontmatter name:"
for d in skills/*/; do
  n=$(sed -n 's/^name: *//p' "$d/SKILL.md" | head -1)
  [ "$n" = "$(basename "$d")" ] || echo "  MISMATCH $d -> $n"
done
echo "licences:"; ls skills/wait-what/LICENSE-mattpocock-skills skills/sp-writing-plans/LICENSE-superpowers
echo "the map_core case:"; ls skills/chart-map/scripts/map_core.py skills/work-map/scripts/map_core.py
```

Expected: `directories: 55`, `surviving plugin-root tokens: 0`, no MISMATCH lines, and all four file listings succeed.

- [ ] **Step 8: Prove the whole point end to end, against the local tree**

```bash
tmp=$(mktemp -d) && cd "$tmp" && \
  npx --yes skills@latest add "$OLDPWD" --skill chart-map --agent claude-code -y \
  && ls -R .claude/skills/chart-map | head -20; cd - >/dev/null
```

Expected: one skill installed, and `.claude/skills/chart-map/scripts/map_core.py` present. This is the failure the whole plan exists to remove — if `map_core.py` is missing here, stop and fix Task 3.

- [ ] **Step 9: Commit**

```bash
git add scripts/generate_skills_tree.py scripts/test_generate_skills_tree.py skills
git commit -m "feat(skills-tree): generate the committed skills/ tree, all 55 skills (ADRs 0153, 0154, 0161)"
```

---

### Task 6: The checker

**Files:**
- Create: `scripts/check_skills_tree.py`
- Create: `scripts/test_check_skills_tree.py`

**Interfaces:**
- Consumes: `build`, `discover_skills`, `frontmatter_name`, `read_text` from the generator module.
- Produces: `check(repo) -> list[str]` (findings, empty when clean) and `main(argv=None) -> int` (0 clean, 1 findings, 2 cannot run).

- [ ] **Step 1: Write the failing tests**

Create `scripts/test_check_skills_tree.py`:

```python
#!/usr/bin/env python3
"""Tests for check_skills_tree.py.
Run: python3 scripts/test_check_skills_tree.py   (from the repo root)"""
import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import check_skills_tree as c
import generate_skills_tree as g


def _write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _repo_with(skills):
    repo = tempfile.mkdtemp(prefix="checktree-")
    for dirname, name, body in skills:
        _write(os.path.join(repo, "plugins", "p", "skills", dirname, "SKILL.md"),
               "---\nname: %s\ndescription: d\n---\n\n%s" % (name, body))
    g.build(repo, os.path.join(repo, "skills"))
    return repo


def test_a_freshly_generated_tree_is_clean():
    repo = _repo_with([("one", "one", "body\n")])
    try:
        assert c.check(repo) == [], c.check(repo)
    finally:
        shutil.rmtree(repo)


def test_a_hand_edited_file_is_a_finding():
    repo = _repo_with([("one", "one", "body\n")])
    try:
        _write(os.path.join(repo, "skills", "one", "SKILL.md"),
               "---\nname: one\ndescription: d\n---\n\nEDITED\n")
        findings = c.check(repo)
        assert any("SKILL.md" in f for f in findings), findings
    finally:
        shutil.rmtree(repo)


def test_a_missing_generated_skill_is_a_finding():
    repo = _repo_with([("one", "one", "body\n")])
    try:
        shutil.rmtree(os.path.join(repo, "skills", "one"))
        findings = c.check(repo)
        assert any("one" in f for f in findings), findings
    finally:
        shutil.rmtree(repo)


def test_an_extra_directory_in_the_tree_is_a_finding():
    repo = _repo_with([("one", "one", "body\n")])
    try:
        _write(os.path.join(repo, "skills", "ghost", "SKILL.md"),
               "---\nname: ghost\n---\n")
        findings = c.check(repo)
        assert any("ghost" in f for f in findings), findings
    finally:
        shutil.rmtree(repo)


def test_a_duplicate_source_name_is_a_finding():
    repo = _repo_with([("one", "same", "body\n")])
    try:
        _write(os.path.join(repo, "plugins", "q", "skills", "two", "SKILL.md"),
               "---\nname: same\ndescription: d\n---\n\nbody\n")
        findings = c.check(repo)
        assert any("same" in f and "twice" in f for f in findings), findings
    finally:
        shutil.rmtree(repo)


def test_a_surviving_plugin_root_token_is_a_finding():
    repo = _repo_with([("one", "one", "body\n")])
    try:
        path = os.path.join(repo, "skills", "one", "SKILL.md")
        text = io.open(path, encoding="utf-8").read()
        _write(path, text + "\n${CLAUDE_PLUGIN_ROOT}/references/x.md\n")
        findings = c.check(repo)
        assert any("CLAUDE_PLUGIN_ROOT" in f for f in findings), findings
    finally:
        shutil.rmtree(repo)


def test_a_reference_pointing_outside_the_skill_dir_is_a_finding():
    repo = _repo_with([("one", "one", "body\n")])
    try:
        path = os.path.join(repo, "skills", "one", "SKILL.md")
        text = io.open(path, encoding="utf-8").read()
        _write(path, text + "\nrun `${CLAUDE_SKILL_DIR}/scripts/gone.py`\n")
        findings = c.check(repo)
        assert any("gone.py" in f for f in findings), findings
    finally:
        shutil.rmtree(repo)


def test_main_exits_1_on_findings_and_0_when_clean():
    repo = _repo_with([("one", "one", "body\n")])
    try:
        assert c.main(["--repo", repo]) == 0
        shutil.rmtree(os.path.join(repo, "skills", "one"))
        assert c.main(["--repo", repo]) == 1
    finally:
        shutil.rmtree(repo)


if __name__ == "__main__":
    TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in TESTS:
        try:
            t()
            print("PASS  %s" % t.__name__)
        except BaseException as e:
            failed += 1
            print("FAIL  %s: %s: %s" % (t.__name__, type(e).__name__, e))
    print("%d/%d passed" % (len(TESTS) - failed, len(TESTS)))
    sys.exit(1 if failed else 0)
```

- [ ] **Step 2: Run to verify it fails**

Run: `python3 scripts/test_check_skills_tree.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'check_skills_tree'`

- [ ] **Step 3: Write the implementation**

Create `scripts/check_skills_tree.py`:

```python
#!/usr/bin/env python3
"""check_skills_tree.py - prove skills/ still matches plugins/*/skills/.

Regenerates the tree into a temporary directory and compares it byte for
byte against the committed one, then asserts the invariants from ADR 0162 and
the spec. It REPORTS and never writes to skills/ - a person (or CI) reads the
findings and runs generate_skills_tree.py to repair them.

Usage:
  python3 scripts/check_skills_tree.py [--repo PATH]

Exit codes: 0 clean, 1 findings, 2 cannot run.
"""
import argparse
import collections
import io
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate_skills_tree as g


def _files_under(root):
    """Every file under root, as {posix relative path: bytes}."""
    out = {}
    for base, _dirs, files in os.walk(root):
        for name in sorted(files):
            path = os.path.join(base, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            with open(path, "rb") as f:
                out[rel] = f.read().replace(b"\r\n", b"\n")
    return out


def check(repo):
    """Return a list of findings. Empty means clean."""
    findings = []

    names = [s.name for s in g.discover_skills(repo)]
    for name, count in sorted(collections.Counter(names).items()):
        if count > 1:
            findings.append(
                "name '%s' is declared twice - the CLI keeps one and drops "
                "the rest (ADR 0156)" % name)

    committed_root = os.path.join(repo, g.TREE_DIRNAME)
    temp_root = tempfile.mkdtemp(prefix="skillstree-check-")
    try:
        g.build(repo, temp_root)
        expected = _files_under(temp_root)
        actual = _files_under(committed_root) if os.path.isdir(committed_root) else {}

        for rel in sorted(set(expected) - set(actual)):
            findings.append("missing from skills/: %s" % rel)
        for rel in sorted(set(actual) - set(expected)):
            findings.append("not generated by the sources: skills/%s" % rel)
        for rel in sorted(set(expected) & set(actual)):
            if expected[rel] != actual[rel]:
                findings.append(
                    "differs from what the sources generate: skills/%s" % rel)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    if os.path.isdir(committed_root):
        for rel, data in sorted(_files_under(committed_root).items()):
            if b"${CLAUDE_PLUGIN_ROOT}" in data:
                findings.append(
                    "CLAUDE_PLUGIN_ROOT survives in skills/%s - it expands to "
                    "nothing outside a plugin install" % rel)
        for rel, data in sorted(_files_under(committed_root).items()):
            if not rel.endswith(".md"):
                continue
            skill_dir = rel.split("/")[0]
            for named in g.SKILL_DIR_REF_RE.findall(data.decode("utf-8", "replace")):
                target = os.path.join(committed_root, skill_dir,
                                      named.replace("/", os.sep))
                if not os.path.isfile(target):
                    findings.append(
                        "skills/%s names %s, which is not in that skill "
                        "directory - the CLI copies nothing else" % (rel, named))

        for entry in sorted(os.listdir(committed_root)):
            md = os.path.join(committed_root, entry, "SKILL.md")
            if not os.path.isfile(md):
                continue
            declared = g.frontmatter_name(g.read_text(md))
            if declared != entry:
                findings.append(
                    "skills/%s declares name '%s' - the CLI installs by the "
                    "frontmatter name, so the two must match (ADR 0162)"
                    % (entry, declared))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    if not os.path.isdir(os.path.join(args.repo, g.PLUGINS_DIRNAME)):
        sys.stderr.write("cannot run: no %s/ under %s\n"
                         % (g.PLUGINS_DIRNAME, args.repo))
        return 2
    findings = check(args.repo)
    for f in findings:
        print("FINDING  %s" % f)
    if findings:
        print("\n%d finding(s). Repair with: "
              "python3 scripts/generate_skills_tree.py" % len(findings))
        return 1
    print("skills/ matches plugins/*/skills/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the tests and make sure they pass**

Run: `python3 scripts/test_check_skills_tree.py`
Expected: `8/8 passed`, exit 0

- [ ] **Step 5: Run the checker against the real repo**

```bash
python3 scripts/check_skills_tree.py --repo .; echo "exit=$?"
```

Expected: `skills/ matches plugins/*/skills/` and `exit=0`.

- [ ] **Step 6: Prove it actually catches drift**

```bash
echo "DRIFT" >> skills/wait-what/SKILL.md
python3 scripts/check_skills_tree.py --repo .; echo "exit=$?"
git checkout -- skills/wait-what/SKILL.md
python3 scripts/check_skills_tree.py --repo .; echo "exit=$?"
```

Expected: first run reports a finding naming `skills/wait-what/SKILL.md` and `exit=1`; after the checkout, clean and `exit=0`. A checker that passes on a deliberately broken tree is worse than none.

- [ ] **Step 7: Commit**

```bash
git add scripts/check_skills_tree.py scripts/test_check_skills_tree.py
git commit -m "feat(skills-tree): checker proves the tree matches its sources (ADR 0159)"
```

---

### Task 7: CI

**Files:**
- Create: `.github/workflows/skills-tree.yml`

**Interfaces:**
- Consumes: both test suites and `check_skills_tree.py`.
- Produces: a required signal on every push and pull request.

- [ ] **Step 1: Write the workflow**

```yaml
name: skills-tree

on:
  push:
  pull_request:

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Generator tests
        run: python3 scripts/test_generate_skills_tree.py

      - name: Checker tests
        run: python3 scripts/test_check_skills_tree.py

      - name: skills/ matches plugins/*/skills/
        run: python3 scripts/check_skills_tree.py --repo .
```

No `pip install` step: the generator, the checker and their tests are standard library only, and CI must stay that way.

- [ ] **Step 2: Verify the workflow parses**

```bash
python3 -c "
import sys
try:
    import yaml
except ImportError:
    sys.exit('PyYAML not installed locally - skip this check, GitHub will parse it')
print(sorted(yaml.safe_load(open('.github/workflows/skills-tree.yml'))))
"
```

Expected: either the key list `['jobs', 'name', 'on']` (note: PyYAML parses the bare key `on` as the boolean `True`, so seeing `True` in that list is correct, not a bug), or the skip message.

- [ ] **Step 3: Run locally exactly what CI will run**

```bash
python3 scripts/test_generate_skills_tree.py && \
python3 scripts/test_check_skills_tree.py && \
python3 scripts/check_skills_tree.py --repo . && echo "CI would pass"
```

Expected: `22/22 passed`, `8/8 passed`, the clean checker line, then `CI would pass`.

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/skills-tree.yml
git commit -m "ci: fail the build when skills/ drifts from its sources (ADR 0159)"
```

- [ ] **Step 5: Record that the run is still unproven**

Do **not** push from here. A push is a side effect outside this worktree and belongs to
the branch-finishing conversation, not to a task.

A workflow that has never run is not a gate, and this one has not run. Step 3 proves the
three commands succeed locally on this machine's Python; it does not prove the workflow
parses on GitHub's runner or that the checkout gives it the same tree. State that in your
report as an open item, so it reaches the human who decides whether to push:

> CI is written and locally equivalent, but has never executed. First push must be
> watched: `gh run list --workflow=skills-tree --limit 1` should report `success`.

---

### Task 8: The documents

**Files:**
- Modify: `README.md` (the existing `## Install` block)
- Create: `INSTALL.md`

**Interfaces:**
- Consumes: the working commands proved in Tasks 5 and 6.
- Produces: the user-facing explanation. Nothing depends on it.

- [ ] **Step 1: Add the npx channel to the README Install block**

In `README.md`, directly after the existing plugin install block and before the "Then add whichever backlog or planning plugin you need" paragraph, insert:

````markdown
Or install the skills on their own — no marketplace, no plugin, files you own and can
edit. This works on Claude Code and on any other agent skills.sh supports:

```text
# everything
npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --all

# just one
npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill grill-then-plan
```

The two routes are alternatives, not steps — [INSTALL.md](INSTALL.md) explains which to
pick and what each one leaves out.
````

No skill names beyond the single worked example, no counts, no versions — ADR 0090 still binds this page.

- [ ] **Step 2: Verify the README claim by running it**

```bash
repo=$(pwd)
tmp=$(mktemp -d) && cd "$tmp"
npx --yes skills@latest add "$repo" --skill grill-then-plan --agent claude-code -y
ls .claude/skills
cd "$repo"
```

Expected: exactly `grill-then-plan`.

The probe targets the **local checkout**, not `ThodsaphonSonthiphin/workflow-daily-work`.
This branch is not pushed, so the GitHub form would install the pre-generation tree and
report a false pass. The local path exercises the same discovery and copy code — the CLI
accepts a local path as a source. What it does not prove is that the published repo
serves the same thing; that is confirmed after the branch merges and is called out in
Task 7's open item.

- [ ] **Step 3: Write `INSTALL.md`**

Create `INSTALL.md` at the repo root with exactly this content:

`````markdown
# Installing workflow-daily-work

There are two ways in. They are alternatives, not steps — pick one. Installing both
leaves you with two copies of every skill.

## Two ways to install

| | plugin channel | npx channel |
|---|---|---|
| the command | `/plugin install dev-workflows@workflow-daily-work` | `npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --all` |
| the unit | a whole plugin | one skill, or all of them |
| who owns the files | Claude Code — a managed, read-only bundle | you — plain files you can read and edit |
| updates | automatic | explicit: `npx skills@latest update <name>` |
| commands and hooks | yes | **no** — skills only |
| short aliases (`/ask`, `/feynman`) | yes | **no** — you type the skill's own name |
| other agents | Claude Code and Antigravity | every agent skills.sh supports |

Take the plugin channel if you want the whole toolkit and never want to think about it
again. Take the npx channel if you want one skill in an unrelated project, or you want to
read and change what the skill actually says.

## The flag that installs everything by accident

Measured 2026-08-29 against this repo:

```text
npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill=wait-what   # installs ALL of them
npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill wait-what   # installs one
```

The only difference is the `=`. This is the CLI's own argument parsing, not something
this repo can change — and `--skill=<name>` is the form the wider ecosystem's
documentation shows, which is why it is worth calling out. Write the flag with a space.

When you do mean everything, say so with `--all`. Without either flag the CLI opens an
interactive picker, which is fine by hand and unhelpful in a script.

## Command names

Short aliases live in the plugin channel. Through npx you type the skill's own name:

| plugin channel | npx channel |
|---|---|
| `/dev-workflows:ask` | `/asking-to-understand` |
| `/dev-workflows:feynman` | `/feynman-explain` |
| `/dev-workflows:daily` | `/daily` |
| `/dev-workflows:sa-doc` | `/sa-doc` |
| `/dev-workflows:career-growth` | `/career-growth` |
| `/dev-workflows:verify-then-advise` | `/verify-then-advise` |
| `/dev-workflows:wait-what` | `/wait-what` |
| `/decision-map:chart` | `/chart-map` |
| `/decision-map:work` | `/work-map` |
| `/ado-backlog:run` | `/findings-to-ado-backlog` |
| `/ado-backlog:my-work` | `/my-work` |
| `/ado-backlog:setup-check` | `/ado-auth` |
| `/github-backlog:run` | `/findings-to-github-issues` |
| `/github-backlog:my-work` | `/github-my-work` |
| `/github-backlog:github-auth` | `/github-auth` |
| `/github-backlog:setup-check` | `/github-auth` |

A skill installed at `.claude/skills/<name>/` is invocable as `/<name>`. Where a skill
sets `disable-model-invocation: true`, that stops Claude reaching for it on its own — it
never stops you typing it.

## What the npx channel does not carry

- **No hooks.** Nothing is wired into session start. Every skill still works; nothing
  happens automatically.
- **No short aliases.** See the table above.
- **No automatic updates.** Run `npx skills@latest update <name>` when you want a newer
  version. Nothing tells you one exists.
- **No commands directory.** The CLI installs skills and only skills.

## Renamed skills

Two skills in the GitHub pipeline were renamed so they stop colliding with their Azure
DevOps twins:

| old | new |
|---|---|
| `extract-findings` (GitHub) | `github-extract-findings` |
| `triage-findings` (GitHub) | `github-triage-findings` |

The Azure DevOps skills keep the short names. If you installed the GitHub pair under the
old names, remove and re-add them:

```text
npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill github-extract-findings
npx skills@latest add ThodsaphonSonthiphin/workflow-daily-work --skill github-triage-findings
```

## Machine setup, either way

Installing the skill is not the same as being able to run it. These are once per machine:

| you installed | do this | check it |
|---|---|---|
| anything from `dev-workflows` | Python 3 on PATH. Several skills hand off to the upstream `superpowers` plugin at plan-execution time: `/plugin marketplace add anthropics/claude-plugins-official` then `/plugin install superpowers@claude-plugins-official`. | ask for a plan and confirm the handoff lands |
| anything from `ado-backlog` | `pip install openpyxl`, `az login`, and set `AZDO_ORG` / `AZDO_PROJECT` to **bare names** (`Cartagena365`, `GlassHull`) — not URLs. `AZDO_PAT` is the fallback when Entra tokens are unavailable. | `/ado-auth` |
| anything from `github-backlog` | `pip install openpyxl`, `gh auth login`, and set `GH_OWNER` / `GH_REPO`. | `/github-auth` |

The `setup-check` commands are plugin-channel only. Through npx, run `/ado-auth` or
`/github-auth` instead — same checks, invoked by skill name.
`````

- [ ] **Step 4: Verify every command in INSTALL.md actually runs**

For each fenced `npx` command in the file, run it in a throwaway directory and confirm the count it claims:

```bash
repo=$(pwd)
tmp=$(mktemp -d) && cd "$tmp"
npx --yes skills@latest add "$repo" --skill=wait-what --agent claude-code -y >/dev/null 2>&1
echo "equals form installed: $(ls .claude/skills | wc -l | tr -d ' ')   (expect 55)"
rm -rf .claude
npx --yes skills@latest add "$repo" --skill wait-what --agent claude-code -y >/dev/null 2>&1
echo "space form installed: $(ls .claude/skills | wc -l | tr -d ' ')   (expect 1)"
cd "$repo"
```

Local path again, and for the same reason as Step 2.

If the equals-form count is no longer the full set, the CLI has been fixed upstream — soften section 2 to say so rather than leaving a false warning in place.

- [ ] **Step 5: Check the alias table against the shipped commands**

```bash
for f in plugins/*/commands/*.md; do
  plugin=$(echo "$f" | cut -d/ -f2); cmd=$(basename "$f" .md)
  skill=$(grep -oE '\*\*`?[a-z0-9-]+`?\*\*' "$f" | head -1 | tr -d '*`')
  grep -q "/$plugin:$cmd\`" INSTALL.md || echo "MISSING ROW  /$plugin:$cmd -> $skill"
done
```

Expected: no output. Every shipped command has a row.

- [ ] **Step 6: Verify the links resolve**

```bash
grep -o '](\([^)]*\))' README.md INSTALL.md | sed 's/.*](//;s/)//' \
  | grep -v '^http' | while read -r p; do [ -e "$p" ] || echo "BROKEN  $p"; done
```

Expected: no output.

- [ ] **Step 7: Commit**

```bash
git add README.md INSTALL.md
git commit -m "docs: the front page carries both install commands, INSTALL.md carries the rest (ADRs 0160, 0163)"
```

---

## Follow-up, not part of this plan

- `PLAYBOOK.md` gains no row: it indexes skills, and this adds none.
- ADR 0090 refused a CI badge because nothing stood behind it. Task 7 changes that, so a `skills-tree` badge may be added to `README.md` — a separate, one-line change.
- `check_vendored_superpowers.py` and `check_plugin_copies.py` are run by hand for the same reason this checker exists. Moving them into the same workflow is the obvious next step and is deliberately out of scope here.
