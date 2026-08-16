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
                                        upstream_skill_names, main,
                                        check_copy_set, check_hashes,
                                        check_frozen)


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


def _valid_manifest():
    """Build a manifest with all 9 REQUIRED_KEYS and a proper copy_set.files."""
    return {
        "upstream": {},
        "copy_set": {"files": [
            {"path": "sp-test/SKILL.md", "upstream_path": "test/SKILL.md"}
        ]},
        "permit_list": [],
        "qualified_refs": [],
        "routing_marker": "",
        "routed_prompts": [],
        "unrouted_prompts": [],
        "frozen": [],
        "upstream_traps": []
    }


def test_valid_manifest_returns_intact(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.json")
        manifest = _valid_manifest()
        with open(p, "w", encoding="utf-8") as f:
            json.dump(manifest, f)
        loaded = load_manifest(p)
        assert loaded == manifest


def test_main_returns_0_with_valid_manifest(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.json")
        manifest = _valid_manifest()
        with open(p, "w", encoding="utf-8") as f:
            json.dump(manifest, f)
        assert main(["--manifest", p, "--root", d]) == 0


def test_manifest_missing_copy_set_files_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.json")
        manifest = _valid_manifest()
        manifest["copy_set"] = {}  # missing "files" key
        with open(p, "w", encoding="utf-8") as f:
            json.dump(manifest, f)
        assert main(["--manifest", p, "--root", d]) == 2


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
