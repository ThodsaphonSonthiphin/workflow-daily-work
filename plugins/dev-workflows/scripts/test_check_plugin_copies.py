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
                                 source_blockers, _git_dir_above, PRUNE,
                                 derive_roots, scan_for_skill_dirs,
                                 PROVENANCE_MIN, line_overlap, historical_hashes,
                                 classify, role_of, repair_for, claimed_install,
                                 agent_list_warning, audit, report, main)


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
    copy = b"some unrelated\ncontent here\ndifferent structure\n"
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


def test_overlap_just_below_provenance_min_is_unrelated():
    """Overlap at 0.69 (just below threshold) yields UNRELATED."""
    # Construct exactly 69 shared lines out of 100 total
    src_lines = ["shared_line_%d" % i for i in range(100)]
    src = "\n".join(src_lines) + "\n"

    # Copy shares first 69 lines from src, adds 31 unique lines
    copy_lines = src_lines[:69] + ["unique_line_%d" % i for i in range(31)]
    copy = "\n".join(copy_lines) + "\n"

    # Verify expected overlap by manual calculation
    src_set = set(line for line in src.splitlines() if line.strip())
    copy_set = set(line for line in copy.splitlines() if line.strip())
    expected_overlap = len(src_set & copy_set) / float(min(len(src_set), len(copy_set)))

    assert expected_overlap == 0.69
    assert expected_overlap < PROVENANCE_MIN

    verdict, overlap = classify(src.encode(), copy.encode())
    assert verdict == "UNRELATED"
    assert overlap < PROVENANCE_MIN


def test_overlap_at_provenance_min_is_stale():
    """Overlap at 0.70 (at or above threshold) yields STALE."""
    # Construct exactly 70 shared lines out of 100 total
    src_lines = ["shared_line_%d" % i for i in range(100)]
    src = "\n".join(src_lines) + "\n"

    # Copy shares first 70 lines from src, adds 30 unique lines
    copy_lines = src_lines[:70] + ["unique_line_%d" % i for i in range(30)]
    copy = "\n".join(copy_lines) + "\n"

    # Verify expected overlap by manual calculation
    src_set = set(line for line in src.splitlines() if line.strip())
    copy_set = set(line for line in copy.splitlines() if line.strip())
    expected_overlap = len(src_set & copy_set) / float(min(len(src_set), len(copy_set)))

    assert expected_overlap == 0.70
    assert expected_overlap >= PROVENANCE_MIN

    verdict, overlap = classify(src.encode(), copy.encode())
    assert verdict == "STALE"
    assert overlap >= PROVENANCE_MIN


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


def test_repair_for_unknown_role_raises_valueerror():
    try:
        repair_for("unknown-role", "path", "source")
        raise AssertionError("repair_for should have raised ValueError for unknown role")
    except ValueError as exc:
        assert "unknown role" in str(exc)


def test_repair_for_returns_distinct_text_per_role():
    cache_text = repair_for("cache", "path", "source")
    worktree_text = repair_for("worktree", "path", "source")
    agent_text = repair_for("agent-store", "path", "source")
    source_text = repair_for("source", "path", "source")
    vendored_text = repair_for("vendored", "path", "source")

    repairs = [cache_text, worktree_text, agent_text, source_text, vendored_text]
    assert len(repairs) == len(set(repairs)), "Some roles return duplicate text"


def test_repair_for_cache_contains_no_write_instructions():
    repair = repair_for("cache", "any/path", "any/source")
    for forbidden in ("copy ", "cp ", "write ", "mv "):
        assert forbidden not in repair.lower(), \
            f"cache repair should not contain '{forbidden}'"


def test_repair_for_worktree_contains_no_write_instructions():
    repair = repair_for("worktree", "any/path", "any/source")
    for forbidden in ("copy ", "cp ", "write ", "mv "):
        assert forbidden not in repair.lower(), \
            f"worktree repair should not contain '{forbidden}'"


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
    # 4 lines, not 3: a 1-line drift (v1 vs v2) then has 3/4 = 75% line
    # overlap, above PROVENANCE_MIN (0.70). At 3 lines the same drift is only
    # 2/3 = 66.7% - below threshold - and would misclassify as UNRELATED
    # instead of STALE. (Deviation from the brief's literal fixture text,
    # forced by PROVENANCE_MIN being corrected from 0.60 to 0.70; see the
    # task report.)
    _write(os.path.join(repo, "plugins", "myplug", "skills", "alpha",
                        "SKILL.md"), "alpha v2\nshared\nlines\nmore\n")
    _registry(claude, {"mkt": {"source": {"source": "directory",
                                          "path": repo},
                               "installLocation": repo}})
    return claude, agents, code, repo


def test_audit_grades_a_matching_and_a_drifted_copy():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        _write(os.path.join(code, "consumer", "vendored", "alpha",
                            "SKILL.md"), "alpha v2\nshared\nlines\nmore\n")
        _write(os.path.join(agents, "skills", "alpha", "SKILL.md"),
               "alpha v1\nshared\nlines\nmore\n")
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
               "alpha v1\nshared\nlines\nmore\n")
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


def test_cache_at_the_claimed_version_is_graded():
    with tempfile.TemporaryDirectory() as d:
        claude = os.path.join(d, "home", ".claude")
        agents = os.path.join(d, "home", ".agents")
        repo = os.path.join(d, "code", "srcrepo")
        os.makedirs(claude)
        os.makedirs(agents)
        os.makedirs(repo)
        _marketplace(repo, "myplug", "./plugins/myplug")
        _write(os.path.join(repo, "plugins", "myplug", "skills", "alpha",
                            "SKILL.md"), "alpha\nline2\nline3\nline4\n")
        _registry(claude, {"mkt": {"source": {"source": "directory",
                                              "path": repo},
                                   "installLocation": repo}})
        claimed_dir = os.path.join(claude, "plugins", "cache", "mkt",
                                   "myplug", "1.0.0")
        _write(os.path.join(claimed_dir, "skills", "alpha", "SKILL.md"),
               "outdated\nline2\nline3\nline4\n")
        with open(os.path.join(claude, "plugins", "installed_plugins.json"),
                  "w", encoding="utf-8") as f:
            json.dump({"version": 2, "plugins": {"myplug@mkt": [
                {"scope": "user", "version": "1.0.0",
                 "installPath": claimed_dir}]}}, f)
        result = audit("myplug", "mkt", claude, agents)
        cache_rows = [r for r in result["rows"] if r["role"] == "cache"]
        assert len(cache_rows) == 1
        assert cache_rows[0]["verdict"] == "STALE"
        assert cache_rows[0]["overlap"] is not None
        assert result["superseded"] == 0


def test_cache_at_a_superseded_version_is_not_graded():
    with tempfile.TemporaryDirectory() as d:
        claude = os.path.join(d, "home", ".claude")
        agents = os.path.join(d, "home", ".agents")
        repo = os.path.join(d, "code", "srcrepo")
        os.makedirs(claude)
        os.makedirs(agents)
        os.makedirs(repo)
        _marketplace(repo, "myplug", "./plugins/myplug")
        _write(os.path.join(repo, "plugins", "myplug", "skills", "alpha",
                            "SKILL.md"), "alpha\nline2\nline3\nline4\n")
        _registry(claude, {"mkt": {"source": {"source": "directory",
                                              "path": repo},
                                   "installLocation": repo}})
        claimed_dir = os.path.join(claude, "plugins", "cache", "mkt",
                                   "myplug", "2.0.0")
        _write(os.path.join(claimed_dir, "skills", "alpha", "SKILL.md"),
               "alpha\nline2\nline3\nline4\n")            # matches the source
        old_dir = os.path.join(claude, "plugins", "cache", "mkt", "myplug",
                               "1.0.0")
        _write(os.path.join(old_dir, "skills", "alpha", "SKILL.md"),
               "nothing\nalike\nat\nall\n")               # wildly different
        with open(os.path.join(claude, "plugins", "installed_plugins.json"),
                  "w", encoding="utf-8") as f:
            json.dump({"version": 2, "plugins": {"myplug@mkt": [
                {"scope": "user", "version": "2.0.0",
                 "installPath": claimed_dir}]}}, f)
        result = audit("myplug", "mkt", claude, agents)
        by_version = {}
        for row in result["rows"]:
            if row["role"] != "cache":
                continue
            if "2.0.0" in row["path"]:
                by_version["claimed"] = row["verdict"]
            elif "1.0.0" in row["path"]:
                by_version["old"] = row["verdict"]
        assert by_version["claimed"] == "IN SYNC"
        assert by_version["old"] == "SUPERSEDED"
        # the wildly different superseded copy must not register as a
        # finding, no matter how different its content is from the source
        assert [r for r in result["rows"] if r["verdict"] == "STALE"] == []
        assert result["superseded"] == 1


def test_a_vendored_subset_produces_no_finding_for_absent_skills():
    with tempfile.TemporaryDirectory() as d:
        claude = os.path.join(d, "home", ".claude")
        agents = os.path.join(d, "home", ".agents")
        repo = os.path.join(d, "code", "srcrepo")
        os.makedirs(claude)
        os.makedirs(agents)
        os.makedirs(repo)
        _marketplace(repo, "myplug", "./plugins/myplug")
        _write(os.path.join(repo, "plugins", "myplug", "skills", "alpha",
                            "SKILL.md"), "alpha\nshared\n")
        _write(os.path.join(repo, "plugins", "myplug", "skills", "beta",
                            "SKILL.md"), "beta\nshared\n")
        _registry(claude, {"mkt": {"source": {"source": "directory",
                                              "path": repo},
                                   "installLocation": repo}})
        _write(os.path.join(d, "code", "consumer", "vendored", "alpha",
                            "SKILL.md"), "alpha\nshared\n")
        result = audit("myplug", "mkt", claude, agents)
        consumer_rows = [r for r in result["rows"] if "consumer" in r["path"]]
        assert len(consumer_rows) == 1
        assert consumer_rows[0]["skill"] == "alpha"
        assert consumer_rows[0]["verdict"] == "IN SYNC"
        # no synthesized finding for beta, which this consumer never vendored
        assert not any(r["skill"] == "beta" and "consumer" in r["path"]
                       for r in result["rows"])


def test_strict_exit_code_agrees_with_the_summary_stale_count():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        _write(os.path.join(agents, "skills", "alpha", "SKILL.md"),
               "alpha v1\nshared\nlines\nmore\n")
        result = audit("myplug", "mkt", claude, agents)
        stale_count = sum(1 for r in result["rows"] if r["verdict"] == "STALE")
        assert stale_count == 1
        argv = ["--plugin", "myplug", "--marketplace", "mkt",
                "--claude-home", claude, "--agents-home", agents]
        assert main(argv) == 0
        strict_exit = main(argv + ["--strict"])
        assert (strict_exit == 1) == (stale_count > 0)


def test_a_copy_under_claude_backups_is_not_graded():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        _write(os.path.join(claude, "backups", "skills-resync-2026-01-01",
                            "alpha", "SKILL.md"), "nothing\nalike\nat\nall\n")
        result = audit("myplug", "mkt", claude, agents)
        backup_rows = [r for r in result["rows"] if "backups" in r["path"]]
        assert len(backup_rows) == 1
        assert backup_rows[0]["verdict"] == "SUPERSEDED"
        assert backup_rows[0]["overlap"] is None
        assert result["backups_excluded"] == 1
        # wildly different content must not register as a finding
        assert [r for r in result["rows"] if r["verdict"] == "STALE"] == []


def test_a_directory_literally_named_backups_outside_claude_home_is_still_graded():
    with tempfile.TemporaryDirectory() as d:
        claude, agents, code, repo = _machine(d)
        _write(os.path.join(code, "someproject", "backups", "alpha",
                            "SKILL.md"), "alpha v1\nshared\nlines\nmore\n")
        result = audit("myplug", "mkt", claude, agents)
        outside = [r for r in result["rows"]
                  if "someproject" in r["path"] and "backups" in r["path"]]
        assert len(outside) == 1
        assert outside[0]["verdict"] == "STALE"
        assert result["backups_excluded"] == 0


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
