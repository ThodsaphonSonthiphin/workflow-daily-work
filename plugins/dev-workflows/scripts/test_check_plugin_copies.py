#!/usr/bin/env python3
"""Tests for check_plugin_copies.py.
Run: python test_check_plugin_copies.py   (or: pytest)"""
import json
import os
import subprocess
import tempfile

import check_plugin_copies
from check_plugin_copies import (normalize, content_hash, read_normalized,
                                 load_registry, marketplace_root,
                                 plugin_root, source_skills, git_output,
                                 source_blockers, _git_dir_above)


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
        try:
            load_registry(d)
            raise AssertionError("load_registry should have exited with 2")
        except SystemExit as exc:
            assert exc.code == 2, f"Expected exit 2, got {exc.code}"


def test_malformed_registry_exits_2():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "plugins", "known_marketplaces.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write("{not json")
        try:
            load_registry(d)
            raise AssertionError("load_registry should have exited with 2")
        except SystemExit as exc:
            assert exc.code == 2, f"Expected exit 2, got {exc.code}"


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
    try:
        marketplace_root({}, "nope")
        raise AssertionError("marketplace_root should have exited with 2")
    except SystemExit as exc:
        assert exc.code == 2, f"Expected exit 2, got {exc.code}"


def test_plugin_root_follows_the_marketplace_manifest():
    with tempfile.TemporaryDirectory() as d:
        _marketplace(d, "myplug", "./plugins/myplug")
        got = plugin_root(d, "myplug")
        assert got == os.path.normpath(os.path.join(d, "plugins", "myplug"))


def test_plugin_absent_from_the_manifest_exits_2():
    with tempfile.TemporaryDirectory() as d:
        _marketplace(d, "myplug", "./plugins/myplug")
        try:
            plugin_root(d, "other")
            raise AssertionError("plugin_root should have exited with 2")
        except SystemExit as exc:
            assert exc.code == 2, f"Expected exit 2, got {exc.code}"


def test_source_skills_finds_only_dirs_holding_a_skill_file():
    with tempfile.TemporaryDirectory() as d:
        _write(os.path.join(d, "skills", "alpha", "SKILL.md"), "a\n")
        _write(os.path.join(d, "skills", "beta", "SKILL.md"), "b\n")
        os.makedirs(os.path.join(d, "skills", "gamma"))
        _write(os.path.join(d, "skills", "delta", "notes.md"), "d\n")
        assert sorted(source_skills(d)) == ["alpha", "beta"]


def test_plugin_entry_missing_source_key_exits_2():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, ".claude-plugin", "marketplace.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": "mkt", "plugins": [
                {"name": "myplug", "version": "1.0.0"}]}, f)
        try:
            plugin_root(d, "myplug")
            raise AssertionError("plugin_root should have exited with 2")
        except SystemExit as exc:
            assert exc.code == 2, f"Expected exit 2, got {exc.code}"


def test_plugins_value_is_string_instead_of_list_exits_2():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, ".claude-plugin", "marketplace.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"name": "mkt", "plugins": "not a list"}, f)
        try:
            plugin_root(d, "myplug")
            raise AssertionError("plugin_root should have exited with 2")
        except SystemExit as exc:
            assert exc.code == 2, f"Expected exit 2, got {exc.code}"


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


def test_git_dir_above_finds_dot_git_in_parent():
    with tempfile.TemporaryDirectory() as d:
        _git_init = ["git", "init", "-q", "-b", "main", d]
        subprocess.run(_git_init, check=True, capture_output=True)
        plug = os.path.join(d, "plugins", "myplug")
        os.makedirs(plug, exist_ok=True)
        assert _git_dir_above(plug) is True


def test_git_dir_above_recognizes_dot_git_as_file_in_worktree():
    with tempfile.TemporaryDirectory() as d:
        git_dir = os.path.join(d, "git_dir")
        os.makedirs(git_dir)
        worktree = os.path.join(d, "worktree")
        os.makedirs(worktree)
        # Create a .git file (not directory) to simulate a worktree
        git_file = os.path.join(worktree, ".git")
        with open(git_file, "w") as f:
            f.write("gitdir: %s\n" % git_dir)
        assert _git_dir_above(worktree) is True


def test_git_dir_above_returns_false_for_non_git():
    with tempfile.TemporaryDirectory() as d:
        assert _git_dir_above(d) is False


def test_git_present_but_refusing_to_answer_is_a_blocker():
    with tempfile.TemporaryDirectory() as d:
        plug = _repo_with_plugin(d)
        # Simulate git refusing to answer by replacing git_output temporarily
        original_git_output = check_plugin_copies.git_output
        try:
            # Stub out git_output to return None on rev-parse
            def stub_git_output(repo, *args):
                if args and args[0] == "rev-parse":
                    return None
                return original_git_output(repo, *args)
            check_plugin_copies.git_output = stub_git_output
            blockers = source_blockers(plug)
            assert len(blockers) == 1
            assert "git could not determine" in blockers[0]
        finally:
            check_plugin_copies.git_output = original_git_output


def test_git_status_failure_is_a_blocker():
    with tempfile.TemporaryDirectory() as d:
        plug = _repo_with_plugin(d)
        # Stub git_output to fail on status command
        original_git_output = check_plugin_copies.git_output
        try:
            def stub_git_output(repo, *args):
                if args and args[0] == "status":
                    return None
                return original_git_output(repo, *args)
            check_plugin_copies.git_output = stub_git_output
            blockers = source_blockers(plug)
            assert len(blockers) == 1
            assert "git status could not run" in blockers[0]
        finally:
            check_plugin_copies.git_output = original_git_output

if __name__ == "__main__":
    TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in TESTS:
        try:
            t()
            print(f"PASS  {t.__name__}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL  {t.__name__}: {e}")
    print(f"{len(TESTS) - failed}/{len(TESTS)} passed")
    import sys
    sys.exit(1 if failed else 0)
