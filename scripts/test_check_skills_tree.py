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
