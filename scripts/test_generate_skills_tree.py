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


def test_imported_modules_ignores_prose_in_a_docstring():
    repo = _repo()
    try:
        p = os.path.join(repo, "a.py")
        # Both lines are real: local_map_ops.py wraps a docstring onto "from
        # being substituted away", check_plugin_copies.py onto "from content".
        _write(p, '"""Doc.\n\n    stops a line\n'
                  '    from being substituted away, and confirms provenance\n'
                  '    from content.\n    """\nimport os\nimport openpyxl\n')
        assert g.imported_modules(p) == ["os", "openpyxl"], g.imported_modules(p)
    finally:
        shutil.rmtree(repo)


def test_imported_modules_takes_the_top_level_name_and_skips_relatives():
    repo = _repo()
    try:
        p = os.path.join(repo, "a.py")
        _write(p, "import xml.etree.ElementTree as ET\n"
                  "from openpyxl.styles import Font\n"
                  "from . import sibling\n")
        assert g.imported_modules(p) == ["xml", "openpyxl"], g.imported_modules(p)
    finally:
        shutil.rmtree(repo)


def test_imported_modules_falls_back_to_the_regex_on_a_parse_error():
    repo = _repo()
    try:
        p = os.path.join(repo, "a.py")
        _write(p, "import requests\nthis is not python(\n")
        assert g.imported_modules(p) == ["requests"], g.imported_modules(p)
    finally:
        shutil.rmtree(repo)


def test_requirements_name_a_third_party_import():
    repo = _repo()
    try:
        d = os.path.join(repo, "one", "scripts")
        _write(os.path.join(d, "a.py"), "import os\nimport yaml\n")
        got = g.third_party_requirements(os.path.join(repo, "one"))
        assert got == [("pyyaml", "yaml")], got
    finally:
        shutil.rmtree(repo)


def test_requirements_are_empty_when_every_import_is_stdlib():
    repo = _repo()
    try:
        d = os.path.join(repo, "one", "scripts")
        _write(os.path.join(d, "a.py"),
               "import os\nimport json\nfrom pathlib import Path\n")
        assert g.third_party_requirements(os.path.join(repo, "one")) == []
    finally:
        shutil.rmtree(repo)


def test_requirements_do_not_count_a_sibling_module_as_third_party():
    repo = _repo()
    try:
        d = os.path.join(repo, "one", "scripts")
        _write(os.path.join(d, "a.py"), "import map_core\nimport openpyxl\n")
        _write(os.path.join(d, "map_core.py"), "x = 1\n")
        got = g.third_party_requirements(os.path.join(repo, "one"))
        assert got == [("openpyxl", "openpyxl")], got
    finally:
        shutil.rmtree(repo)


def test_requirements_block_lands_below_the_frontmatter():
    text = "---\nname: a\ndescription: d\n---\n\n# a\n\nbody\n"
    out = g.apply_requirements(text, [("pyyaml", "yaml")])
    assert out == ("---\nname: a\ndescription: d\n---\n\n"
                   "<!-- generated: third-party requirements -->\n"
                   "> **Requires:** `pip install pyyaml` — this skill's "
                   "scripts import `yaml`.\n\n# a\n\nbody\n"), out


def test_requirements_block_is_absent_when_nothing_is_needed():
    text = "---\nname: a\ndescription: d\n---\n\n# a\n"
    assert g.apply_requirements(text, []) == text


def test_requirements_block_is_replaced_not_stacked():
    text = "---\nname: a\n---\n\n# a\n"
    once = g.apply_requirements(text, [("pyyaml", "yaml")])
    twice = g.apply_requirements(once, [("openpyxl", "openpyxl")])
    assert twice.count(g.REQUIRES_MARKER) == 1, twice
    assert "pyyaml" not in twice, twice
    assert g.apply_requirements(once, []) == text


def test_emit_states_a_requirement_a_resolved_reference_brought_in():
    repo = _repo()
    try:
        # The importing script is a PLUGIN-level file the SKILL.md names, so
        # the requirement can only be seen after references are resolved.
        src = _skill(repo, "p", "one", "one",
                     'run `${CLAUDE_PLUGIN_ROOT}/scripts/y.py`\n')
        _write(os.path.join(repo, "plugins", "p", "scripts", "y.py"),
               "import yaml\n")
        out = os.path.join(repo, "skills")
        g.emit_skill(g.Skill("p", "one", src), out, {})
        md = io.open(os.path.join(out, "one", "SKILL.md"), encoding="utf-8").read()
        assert "pip install pyyaml" in md, md
        assert md.index(g.REQUIRES_MARKER) < md.index("${CLAUDE_SKILL_DIR}"), md
    finally:
        shutil.rmtree(repo)


def test_emit_leaves_a_stdlib_only_skill_without_a_requirement_line():
    repo = _repo()
    try:
        src = _skill(repo, "p", "one", "one", "body\n")
        _write(os.path.join(src, "scripts", "a.py"), "import os, json\n")
        out = os.path.join(repo, "skills")
        g.emit_skill(g.Skill("p", "one", src), out, {})
        md = io.open(os.path.join(out, "one", "SKILL.md"), encoding="utf-8").read()
        assert g.REQUIRES_MARKER not in md, md
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


def test_rewrite_resolves_an_md_link_against_the_containing_directory():
    text = ('see [x](${CLAUDE_PLUGIN_ROOT}/references/x.md)\n'
            'and [d](${CLAUDE_PLUGIN_ROOT}/docs/d.md)\n'
            'run `${CLAUDE_PLUGIN_ROOT}/scripts/y.py`\n')
    out = g.rewrite_refs(text, "references")
    assert "[x](x.md)" in out, out                 # sibling, not references/x.md
    assert "[d](../docs/d.md)" in out, out         # climbs out of references/
    assert "${CLAUDE_SKILL_DIR}/scripts/y.py" in out, out  # depth-independent


def test_rewrite_leaves_the_prose_ellipsis_alone():
    text = 'always wrap `"${CLAUDE_PLUGIN_ROOT}/..."`'
    assert g.rewrite_refs(text) == text


def test_emit_rewrites_a_nested_reference_relative_to_its_own_file():
    repo = _repo()
    try:
        src = _skill(repo, "p", "one", "one",
                     'read `${CLAUDE_PLUGIN_ROOT}/references/tpl.md`\n')
        _write(os.path.join(repo, "plugins", "p", "references", "tpl.md"),
               "the convention is in `${CLAUDE_PLUGIN_ROOT}/references/conv.md`\n")
        _write(os.path.join(repo, "plugins", "p", "references", "conv.md"), "c\n")
        out = os.path.join(repo, "skills")
        g.emit_skill(g.Skill("p", "one", src), out, {})
        md = io.open(os.path.join(out, "one", "SKILL.md"), encoding="utf-8").read()
        tpl = io.open(os.path.join(out, "one", "references", "tpl.md"),
                      encoding="utf-8").read()
        assert "`references/tpl.md`" in md, md
        # tpl.md sits inside references/, so its sibling is `conv.md` - not
        # `references/conv.md`, which would resolve to references/references/.
        assert "`conv.md`" in tpl, tpl
        assert "references/conv.md" not in tpl, tpl
    finally:
        shutil.rmtree(repo)


def test_emit_rewrites_a_reference_inside_an_owned_subdirectory():
    repo = _repo()
    try:
        src = _skill(repo, "p", "one", "one", "body\n")
        _write(os.path.join(src, "references", "own.md"),
               "see `${CLAUDE_PLUGIN_ROOT}/references/own.md`\n")
        _write(os.path.join(repo, "plugins", "p", "references", "own.md"), "x\n")
        out = os.path.join(repo, "skills")
        g.emit_skill(g.Skill("p", "one", src), out, {})
        own = io.open(os.path.join(out, "one", "references", "own.md"),
                      encoding="utf-8").read()
        assert "`own.md`" in own and "references/own.md" not in own, own
    finally:
        shutil.rmtree(repo)


def test_argument_hint_is_inserted_after_description():
    text = "---\nname: a\ndescription: d\n---\n\nbody\n"
    out = g.apply_argument_hint(text, '"[x]"')
    assert out == '---\nname: a\ndescription: d\nargument-hint: "[x]"\n---\n\nbody\n', out


def test_argument_hint_replaces_an_existing_one():
    text = '---\nname: a\nargument-hint: "[old]"\n---\n\nbody\n'
    out = g.apply_argument_hint(text, '"[new]"')
    assert 'argument-hint: "[new]"' in out and "[old]" not in out, out


def test_argument_hint_lands_after_a_folded_description_block():
    # description: >- opens a YAML block scalar that continues on indented
    # lines; the hint must not be inserted inside that block, or the
    # unindented argument-hint: line breaks the folded scalar.
    text = ("---\nname: a\ndescription: >-\n  line one\n  line two\n"
            "effort: high\n---\n\nbody\n")
    out = g.apply_argument_hint(text, '"[x]"')
    assert out == (
        "---\nname: a\ndescription: >-\n  line one\n  line two\n"
        'argument-hint: "[x]"\neffort: high\n---\n\nbody\n'), out


def test_compiled_python_never_travels():
    assert g.is_compiled_python("scripts/__pycache__/x.cpython-313.pyc")
    assert g.is_compiled_python("scripts/x.pyc")
    assert not g.is_compiled_python("scripts/x.py")
    repo = _repo()
    try:
        src = _skill(repo, "p", "one", "one", "body\n")
        _write(os.path.join(src, "scripts", "x.py"), "x = 1\n")
        _write(os.path.join(src, "scripts", "__pycache__", "x.cpython-313.pyc"), "junk")
        _write(os.path.join(src, "stray.pyc"), "junk")
        out = os.path.join(repo, "skills")
        g.emit_skill(g.Skill("p", "one", src), out, {})
        assert os.path.isfile(os.path.join(out, "one", "scripts", "x.py"))
        assert not os.path.exists(os.path.join(out, "one", "scripts", "__pycache__"))
        assert not os.path.exists(os.path.join(out, "one", "stray.pyc"))
    finally:
        shutil.rmtree(repo)


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


def test_build_leaves_a_symlink_in_the_output_root_alone():
    repo = _repo()
    outside = None
    try:
        _skill(repo, "p", "one", "one")
        out = os.path.join(repo, "skills")
        os.makedirs(out)

        # A symlink whose name matches no skill must not be treated as a
        # stale directory to clean up: following it would walk (and delete)
        # whatever it points at, entirely outside the output tree.
        outside = tempfile.mkdtemp(prefix="skilltree-outside-")
        _write(os.path.join(outside, "keep.txt"), "do not touch\n")
        link = os.path.join(out, "ghost-link")
        os.symlink(outside, link)

        built = g.build(repo, out)

        assert built == ["one"], built
        assert os.path.islink(link), "the symlink itself must survive"
        assert os.path.isdir(outside), "its target must not be walked into"
        assert os.listdir(outside) == ["keep.txt"], os.listdir(outside)
    finally:
        shutil.rmtree(repo)
        if outside:
            shutil.rmtree(outside, ignore_errors=True)


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
