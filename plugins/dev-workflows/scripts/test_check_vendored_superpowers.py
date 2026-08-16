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
