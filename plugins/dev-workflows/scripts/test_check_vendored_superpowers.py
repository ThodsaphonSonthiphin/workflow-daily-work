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
                                        check_frozen, bare_name_re,
                                        check_bare_names)


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
            {"path": "sp-test/SKILL.md", "upstream_path": "test/SKILL.md",
             "sha256": "0" * 64}
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


def test_missing_frozen_file_is_flagged_and_copy_set_ignores_it(tmp_path=None):
    """The frozen-file missing-file branch: check_frozen reports it, check_copy_set returns empty.
    This tests the split: frozen files are NOT governed by check_copy_set."""
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        os.remove(os.path.join(root, "frozen/SKILL.md"))
        # check_copy_set should not report the missing frozen file (not in governed dirs)
        copy_set_out = check_copy_set(root, m)
        assert copy_set_out == []
        # check_frozen should report it
        frozen_out = check_frozen(root, m)
        assert len(frozen_out) == 1
        assert frozen_out[0]["path"] == "frozen/SKILL.md"


def test_copy_set_file_missing_sha256_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.json")
        manifest = _valid_manifest()
        # Remove sha256 from the copy_set file entry
        manifest["copy_set"]["files"][0].pop("sha256", None)
        with open(p, "w", encoding="utf-8") as f:
            json.dump(manifest, f)
        assert main(["--manifest", p, "--root", d]) == 2


def test_frozen_entry_missing_sha256_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.json")
        manifest = _valid_manifest()
        # Add a frozen entry without sha256
        manifest["frozen"] = [{"path": "frozen/SKILL.md", "why": "test"}]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(manifest, f)
        assert main(["--manifest", p, "--root", d]) == 2


def test_valid_manifest_with_empty_sha256_in_frozen(tmp_path=None):
    """Task 5 bootstrap writes empty sha256 initially, so empty string is permitted."""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.json")
        manifest = _valid_manifest()
        # Add a frozen entry with empty sha256 (Task 5 bootstrap case)
        manifest["frozen"] = [{"path": "frozen/SKILL.md", "sha256": "", "why": "test"}]
        with open(p, "w", encoding="utf-8") as f:
            json.dump(manifest, f)
        # Should load successfully (not validate the value, just the presence of key)
        loaded = load_manifest(p)
        assert loaded == manifest


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


def test_bare_name_re_is_case_insensitive():
    """Case-insensitive matching catches capitalized mentions like 'Brainstorming'."""
    pat = bare_name_re(["brainstorming", "writing-plans"])
    assert pat.search("Brainstorming Ideas Into Designs")  # capitalized
    assert pat.search("WRITING-PLANS are next")            # all caps
    assert pat.search("brainstorming in lowercase")        # original case


def test_unreviewed_detected_regardless_of_entry_order(tmp_path=None):
    """UNREVIEWED must be detected regardless of permit entry order.

    Two entries claim the same line, both occurrences present in the file, one
    REVIEW: and one with a real reason. The check must flag UNREVIEWED
    regardless of which order the entries appear in the manifest."""
    with tempfile.TemporaryDirectory() as d:
        root, m, permitted = _permit_tree(d)
        # Write the line twice so both permit entries are satisfied
        p = os.path.join(root, "sp-brainstorming/SKILL.md")
        _write(p, "header\n%s\n%s\n" % (permitted, permitted), eol="\r\n")
        # Add a second entry for the same line, one reviewed and one not
        m["permit_list"].append(
            {"file": "sp-brainstorming/SKILL.md",
             "text": permitted,
             "why": "REVIEW: state why this is inert"})
        out_first_order = check_bare_names(root, m)
        # Reverse the order: REVIEW entry first, reviewed entry second
        m["permit_list"].reverse()
        out_second_order = check_bare_names(root, m)
        # Both should report UNREVIEWED regardless of order
        checks_first = sorted(f["check"] for f in out_first_order)
        checks_second = sorted(f["check"] for f in out_second_order)
        assert checks_first == ["permit-list/UNREVIEWED"]
        assert checks_second == ["permit-list/UNREVIEWED"]


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
