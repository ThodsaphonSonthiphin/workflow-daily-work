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
