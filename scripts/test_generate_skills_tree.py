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


def test_emit_raises_on_reference_collision_with_owned_file():
    repo = _repo()
    try:
        # Create a skill that owns references/x.md
        src = _skill(repo, "p", "one", "one",
                     'see `${CLAUDE_PLUGIN_ROOT}/references/x.md`\n')
        # Write the skill's own references/x.md
        _write(os.path.join(src, "references", "x.md"), "skill content\n")
        # Write a different file at the same path in the plugin
        _write(os.path.join(repo, "plugins", "p", "references", "x.md"),
               "plugin content\n")
        out = os.path.join(repo, "skills")
        try:
            g.emit_skill(g.Skill("p", "one", src), out, {})
            raise AssertionError("expected ReferenceCollision")
        except g.ReferenceCollision as e:
            assert "references/x.md" in str(e), e
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
