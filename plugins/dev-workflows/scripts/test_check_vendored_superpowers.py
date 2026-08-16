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
                                        check_bare_names, check_qualified_refs,
                                        check_routing, emit_manifest,
                                        check_upstream_files,
                                        check_upstream_traps, run_checks,
                                        EmitRefused, resolve_upstream_sha)


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
             "sha256": "0" * 64, "state": "verbatim"}
        ]},
        "permit_list": [],
        # A census (name -> count) and a trap table, both dicts. This helper
        # had them as lists, which no real manifest ever is - the shape checks
        # in load_manifest are what surfaced it.
        "qualified_refs": {},
        "routing_marker": "",
        "routed_prompts": [],
        "unrouted_prompts": [],
        "frozen": [],
        "upstream_traps": {}
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


def test_copy_set_file_missing_state_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.json")
        manifest = _valid_manifest()
        # Remove state from the copy_set file entry
        manifest["copy_set"]["files"][0].pop("state", None)
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


def test_frozen_entry_missing_why_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.json")
        manifest = _valid_manifest()
        # Add a frozen entry without why
        manifest["frozen"] = [{"path": "frozen/SKILL.md", "sha256": "0" * 64}]
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


def test_long_lines_differing_past_160_chars_stay_distinguishable(tmp_path=None):
    """A permitted line over 160 chars, reworded only past character 160,
    must yield a NEW finding and a STALE finding whose messages actually show
    what differs - not two reports truncated down to an identical prefix."""
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "skills")
        filler = "A" * 200
        declared_line = "digraph brainstorming { %s tailDECLARED" % filler
        actual_line = "digraph brainstorming { %s tailACTUAL" % filler
        assert declared_line[:160] == actual_line[:160]
        assert len(declared_line) > 160 and len(actual_line) > 160
        _write(os.path.join(root, "sp-brainstorming/SKILL.md"),
               "header\n%s\n" % actual_line, eol="\r\n")
        manifest = {
            "copy_set": {"files": [
                {"path": "sp-brainstorming/SKILL.md",
                 "upstream_path": "brainstorming/SKILL.md",
                 "state": "edited", "sha256": "x"}]},
            "permit_list": [{"file": "sp-brainstorming/SKILL.md",
                             "text": declared_line,
                             "why": "DOT graph identifier, not a skill reference"}],
        }
        out = check_bare_names(root, manifest)
        by_check = {f["check"]: f["message"] for f in out}
        assert sorted(by_check) == ["permit-list/NEW", "permit-list/STALE"]
        new_msg = by_check["permit-list/NEW"]
        stale_msg = by_check["permit-list/STALE"]
        assert new_msg != stale_msg
        assert "tailACTUAL" in new_msg and "tailDECLARED" not in new_msg
        assert "tailDECLARED" in stale_msg and "tailACTUAL" not in stale_msg


def _ref_tree(d):
    root = os.path.join(d, "skills")
    _write(os.path.join(root, "sp-alpha/SKILL.md"),
           "see superpowers:using-git-worktrees for isolation\n", eol="\r\n")
    manifest = {
        "copy_set": {"files": [{"path": "sp-alpha/SKILL.md",
                                "upstream_path": "alpha/SKILL.md",
                                "state": "edited", "sha256": "x"}]},
        "qualified_refs": {"using-git-worktrees": 1},
    }
    return root, manifest


def test_reference_to_a_non_copied_skill_is_clean(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _ref_tree(d)
        assert check_qualified_refs(root, m) == []


def test_reference_to_a_copied_skill_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _ref_tree(d)
        _write(os.path.join(root, "sp-alpha/SKILL.md"),
               "hand off to superpowers:alpha now\n", eol="\r\n")
        out = check_qualified_refs(root, m)
        assert any(f["check"] == "qualified-ref" for f in out)


def test_census_change_is_flagged(tmp_path=None):
    """A NEW upstream name is legitimate but must be seen, not absorbed."""
    with tempfile.TemporaryDirectory() as d:
        root, m = _ref_tree(d)
        _write(os.path.join(root, "sp-alpha/SKILL.md"),
               "see superpowers:using-git-worktrees and "
               "superpowers:test-driven-development\n", eol="\r\n")
        out = check_qualified_refs(root, m)
        assert [f["check"] for f in out] == ["qualified-ref/census"]


def _route_tree(d):
    root = os.path.join(d, "skills")
    _write(os.path.join(root, "sp-x/code-reviewer.md"),
           "Load the `scrutinize-dispatch` skill.\n", eol="\r\n")
    _write(os.path.join(root, "sp-x/re-review-prompt.md"),
           "Verdict each finding ADDRESSED or NOT ADDRESSED.\n", eol="\r\n")
    manifest = {
        "routing_marker": "scrutinize-dispatch",
        "routed_prompts": ["sp-x/code-reviewer.md"],
        "unrouted_prompts": ["sp-x/re-review-prompt.md"],
    }
    return root, manifest


def test_routed_and_unrouted_prompts_are_clean(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _route_tree(d)
        assert check_routing(root, m) == []


def test_routed_prompt_losing_the_marker_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _route_tree(d)
        _write(os.path.join(root, "sp-x/code-reviewer.md"),
               "Review the diff yourself.\n", eol="\r\n")
        out = check_routing(root, m)
        assert [f["path"] for f in out] == ["sp-x/code-reviewer.md"]


def test_unrouted_prompt_gaining_the_marker_is_flagged(tmp_path=None):
    """ADR 0084's amendment: re-review is deliberately unrouted."""
    with tempfile.TemporaryDirectory() as d:
        root, m = _route_tree(d)
        _write(os.path.join(root, "sp-x/re-review-prompt.md"),
               "Load the `scrutinize-dispatch` skill.\n", eol="\r\n")
        out = check_routing(root, m)
        assert [f["path"] for f in out] == ["sp-x/re-review-prompt.md"]


def test_emit_manifest_round_trips_clean(tmp_path=None):
    """A manifest emitted from a tree must find that tree clean."""
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "skills")
        up = os.path.join(d, "upstream")
        _write(os.path.join(root, "sp-alpha/SKILL.md"), "body\n", eol="\r\n")
        _write(os.path.join(up, "skills/alpha/SKILL.md"), "body\n", eol="\n")
        m = emit_manifest(root, up, None)
        assert check_copy_set(root, m) == []
        assert check_hashes(root, m) == []
        # identical content, different EOL -> verbatim (ADR 0086)
        assert m["copy_set"]["files"][0]["state"] == "verbatim"


def test_emit_manifest_marks_an_edited_file(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "skills")
        up = os.path.join(d, "upstream")
        _write(os.path.join(root, "sp-alpha/SKILL.md"), "ours\n", eol="\r\n")
        _write(os.path.join(up, "skills/alpha/SKILL.md"), "theirs\n", eol="\n")
        m = emit_manifest(root, up, None)
        assert m["copy_set"]["files"][0]["state"] == "edited"


def test_emit_manifest_carries_over_a_reviewed_why(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "skills")
        up = os.path.join(d, "upstream")
        line = "digraph brainstorming {"
        _write(os.path.join(root, "sp-brainstorming/SKILL.md"),
               "%s\n" % line, eol="\r\n")
        _write(os.path.join(up, "skills/brainstorming/SKILL.md"),
               "%s\n" % line, eol="\n")
        previous = {"permit_list": [{"file": "sp-brainstorming/SKILL.md",
                                     "text": line, "why": "DOT identifier"}]}
        m = emit_manifest(root, up, previous)
        assert m["permit_list"][0]["why"] == "DOT identifier"
        m2 = emit_manifest(root, up, None)
        assert m2["permit_list"][0]["why"].startswith("REVIEW:")


def test_emit_refuses_when_the_manifest_was_truncated(tmp_path=None):
    """Redirecting --emit-manifest onto its own input truncates it first.
    Emitting from the empty file would drop every hand-written key in silence,
    so the program must refuse instead."""
    with tempfile.TemporaryDirectory() as d:
        root = os.path.join(d, "skills")
        up = os.path.join(d, "upstream")
        _write(os.path.join(root, "sp-alpha/SKILL.md"), "body\n", eol="\r\n")
        _write(os.path.join(up, "skills/alpha/SKILL.md"), "body\n", eol="\n")
        p = os.path.join(d, "m.json")
        open(p, "w").close()                 # exactly what `>` leaves behind
        assert main(["--emit-manifest", "--root", root,
                     "--manifest", p, "--upstream-dir", up]) == 2


def test_emit_manifest_without_upstream_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        assert main(["--emit-manifest", "--root", d,
                     "--manifest", os.path.join(d, "absent.json")]) == 2



def _upstream_pair(d, ours="body\n", theirs="body\n", state="verbatim"):
    root = os.path.join(d, "skills")
    up = os.path.join(d, "upstream")
    _write(os.path.join(root, "sp-alpha/SKILL.md"), ours, eol="\r\n")
    _write(os.path.join(up, "skills/alpha/SKILL.md"), theirs, eol="\n")
    manifest = {
        "upstream": {"skills_subdir": "skills"},
        "copy_set": {"files": [{"path": "sp-alpha/SKILL.md",
                                "upstream_path": "alpha/SKILL.md",
                                "state": state, "sha256": "x"}]},
    }
    return root, up, manifest


def test_verbatim_file_matching_upstream_is_clean(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, up, m = _upstream_pair(d)
        assert check_upstream_files(root, up, m) == []


def test_verbatim_file_that_upstream_moved_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, up, m = _upstream_pair(d, ours="body\n", theirs="body v2\n")
        out = check_upstream_files(root, up, m)
        assert [f["check"] for f in out] == ["upstream/moved"]


def test_edited_file_identical_to_upstream_is_flagged(tmp_path=None):
    """The rewrite pass was lost - the copy no longer differs from upstream."""
    with tempfile.TemporaryDirectory() as d:
        root, up, m = _upstream_pair(d, state="edited")
        out = check_upstream_files(root, up, m)
        assert [f["check"] for f in out] == ["upstream/moved"]


def test_upstream_deleting_a_copied_file_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, up, m = _upstream_pair(d)
        os.remove(os.path.join(up, "skills/alpha/SKILL.md"))
        out = check_upstream_files(root, up, m)
        assert [f["check"] for f in out] == ["upstream/mapping"]


def test_upstream_adding_a_file_is_flagged(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, up, m = _upstream_pair(d)
        _write(os.path.join(up, "skills/alpha/NEW.md"), "new\n", eol="\n")
        out = check_upstream_files(root, up, m)
        assert [f["check"] for f in out] == ["upstream/added"]


def _trap_tree(d):
    up = os.path.join(d, "upstream")
    _write(os.path.join(up, "skills/brainstorming/SKILL.md"),
           "no qualified refs here\n", eol="\n")
    _write(os.path.join(up, "skills/using-superpowers/SKILL.md"),
           "use superpowers:brainstorming then "
           "superpowers:systematic-debugging\n", eol="\n")
    _write(os.path.join(up, "skills/brainstorming/"
                            "spec-document-reviewer-prompt.md"),
           "dead file\n", eol="\n")
    _write(os.path.join(up, "docs/history.md"),
           "we once used spec-document-reviewer-prompt\n", eol="\n")
    manifest = {
        "upstream": {"skills_subdir": "skills"},
        "upstream_traps": {
            "no_qualified_ref_dir": "brainstorming",
            "hook_source": "using-superpowers/SKILL.md",
            "hook_named_skills": ["brainstorming", "systematic-debugging"],
            "dead_prompts": ["spec-document-reviewer-prompt"],
            "dead_prompt_live_dirs": ["skills", "hooks", "scripts"]},
    }
    return up, manifest


def test_all_three_traps_hold(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        up, m = _trap_tree(d)
        assert check_upstream_traps(up, m) == []


def test_trap_1_qualified_ref_inside_brainstorming(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        up, m = _trap_tree(d)
        _write(os.path.join(up, "skills/brainstorming/SKILL.md"),
               "next use superpowers:writing-plans\n", eol="\n")
        out = check_upstream_traps(up, m)
        assert [f["check"] for f in out] == ["upstream/trap-1"]


def test_trap_2_a_third_hook_named_skill(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        up, m = _trap_tree(d)
        _write(os.path.join(up, "skills/using-superpowers/SKILL.md"),
               "superpowers:brainstorming superpowers:systematic-debugging "
               "superpowers:test-driven-development\n", eol="\n")
        out = check_upstream_traps(up, m)
        assert [f["check"] for f in out] == ["upstream/trap-2"]


def test_trap_3_a_dead_prompt_is_revived(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        up, m = _trap_tree(d)
        _write(os.path.join(up, "skills/brainstorming/SKILL.md"),
               "dispatch spec-document-reviewer-prompt now\n", eol="\n")
        out = check_upstream_traps(up, m)
        assert [f["check"] for f in out] == ["upstream/trap-3"]


def test_trap_3_ignores_docs_and_the_file_itself(tmp_path=None):
    """docs/ mentions are how upstream looks TODAY - only skills/, hooks/ and
    scripts/ count as a revival. The dead file naming itself is not a revival
    either: it is the corpse, not a caller.

    The base fixture already covers the docs/ half. The self-naming half needs
    the dead file to actually say its own name - as written the fixture's
    "dead file" body does not, so deleting the skip in check_upstream_traps
    failed no test at all."""
    with tempfile.TemporaryDirectory() as d:
        up, m = _trap_tree(d)
        _write(os.path.join(up, "skills/brainstorming/"
                                "spec-document-reviewer-prompt.md"),
               "# Spec Document Reviewer Prompt Template\n"
               "invoke me as spec-document-reviewer-prompt\n", eol="\n")
        assert check_upstream_traps(up, m) == []

def test_strict_exits_1_only_when_there_are_findings(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        p = os.path.join(d, "m.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(m, f)
        assert main(["--manifest", p, "--root", root, "--strict"]) == 0
        _write(os.path.join(root, "sp-beta/SKILL.md"), "tampered\n",
               eol="\r\n")
        assert main(["--manifest", p, "--root", root]) == 0        # report
        assert main(["--manifest", p, "--root", root, "--strict"]) == 1


def test_missing_upstream_dir_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        p = os.path.join(d, "m.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(m, f)
        assert main(["--manifest", p, "--root", root,
                     "--upstream-dir", os.path.join(d, "absent")]) == 2


def test_missing_root_exits_2(tmp_path=None):
    with tempfile.TemporaryDirectory() as d:
        root, m = _tiny_tree(d)
        p = os.path.join(d, "m.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(m, f)
        assert main(["--manifest", p,
                     "--root", os.path.join(d, "absent")]) == 2


def test_the_real_repo_tree_is_clean(tmp_path=None):
    """THE REGRESSION GUARD. This is the test that would have caught the
    Critical: a bare short name inside a copy, resolving to the unvendored
    upstream skill with no error message.

    Skips only if the manifest has not been generated yet (Task 5)."""
    import check_vendored_superpowers as mod
    if not os.path.isfile(mod.DEFAULT_MANIFEST):
        print("SKIP  test_the_real_repo_tree_is_clean: no manifest yet")
        return
    assert main(["--strict"]) == 0


def _emit_tree(d, skills=("alpha", "beta")):
    """A root + upstream pair where every sp-<name> has an upstream match."""
    root = os.path.join(d, "skills")
    up = os.path.join(d, "upstream")
    for name in skills:
        _write(os.path.join(root, "sp-" + name, "SKILL.md"), "# %s\n" % name)
        _write(os.path.join(up, "skills", name, "SKILL.md"), "# %s\n" % name)
    return root, up


def test_emit_refuses_when_upstream_renamed_a_governed_skill():
    """The branch's own failure mode, inside the tool built to prevent it.

    emit_manifest skips any sp-<name> with no upstream counterpart, because
    that is how sp-grill-with-doc is excluded. But an upstream RENAME reaches
    the same line, and skipping there deletes a still-vendored file from the
    copy set - silently. check_copy_set cannot then report it, because it
    derives the governed set from the very manifest the file just left.

    Telling the two apart needs the previous manifest: sp-grill-with-doc was
    never governed, a renamed skill was."""
    with tempfile.TemporaryDirectory() as d:
        root, up = _emit_tree(d)
        base = emit_manifest(root, up, None)
        assert len(base["copy_set"]["files"]) == 2

        os.rename(os.path.join(up, "skills", "beta"),
                  os.path.join(up, "skills", "gamma"))
        try:
            emit_manifest(root, up, base)
        except EmitRefused as e:
            assert "sp-beta" in str(e)
        else:
            raise AssertionError("emit dropped sp-beta from the copy set "
                                 "instead of refusing")


def test_emit_still_skips_a_never_governed_sp_dir():
    """The benign half of the same line: sp-grill-with-doc carries the prefix
    but is not a copy, so it must keep being skipped without complaint."""
    with tempfile.TemporaryDirectory() as d:
        root, up = _emit_tree(d)
        _write(os.path.join(root, "sp-grill-with-doc", "SKILL.md"), "# ours\n")
        out = emit_manifest(root, up, emit_manifest(root, up, None))
        assert [f["path"] for f in out["copy_set"]["files"]] == [
            "sp-alpha/SKILL.md", "sp-beta/SKILL.md"]


def test_upstream_mapping_follows_a_rename_without_renaming_our_copy():
    """The escape hatch the refusal points at. Without it the only way to
    follow an upstream rename is to rename our own copy, which changes a
    skill's name in this marketplace for a reason external to it."""
    with tempfile.TemporaryDirectory() as d:
        root, up = _emit_tree(d)
        base = emit_manifest(root, up, None)
        os.rename(os.path.join(up, "skills", "beta"),
                  os.path.join(up, "skills", "gamma"))
        base["upstream"] = dict(base.get("upstream", {}),
                                mapping={"sp-beta": "gamma"})
        out = emit_manifest(root, up, base)
        entry = [f for f in out["copy_set"]["files"]
                 if f["path"] == "sp-beta/SKILL.md"]
        assert entry, "the mapped copy fell out of the copy set"
        assert entry[0]["upstream_path"] == "gamma/SKILL.md"


def test_bad_upstream_mapping_shape_is_a_shape_error():
    with tempfile.TemporaryDirectory() as d:
        m = _valid_manifest()
        m["upstream"] = {"mapping": {"sp-beta": None}}
        p = os.path.join(d, "m.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(m, f)
        try:
            load_manifest(p)
        except ValueError as e:
            assert "upstream.mapping" in str(e)
        else:
            raise AssertionError("a null mapping target loaded cleanly")


def test_emit_never_carries_a_stale_upstream_sha_forward():
    """The manifest records ONE sha for the whole copy set, and it is the only
    record of which upstream commit the copies came from. Carrying the prior
    value forward stamps freshly-copied files with the old provenance, and the
    procedure's stop condition (upstream HEAD == recorded sha) then can never
    be reached - it would compare new files against a sha they never had."""
    with tempfile.TemporaryDirectory() as d:
        root, up = _emit_tree(d)
        stale = "0" * 40
        out = emit_manifest(root, up, {"upstream": {"sha": stale}})
        assert out["upstream"]["sha"] != stale
        # Not a git checkout, so it must say so rather than invent a sha.
        assert out["upstream"]["sha"].startswith("REVIEW:")


def test_emit_manifest_via_main_writes_a_loadable_manifest():
    """The command the procedure document tells operators to run. Its success
    path in main() had no test at all, so every defect above could ship."""
    with tempfile.TemporaryDirectory() as d:
        root, up = _emit_tree(d)
        out_path = os.path.join(d, "emitted.json")
        import io
        import contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = main(["--emit-manifest", "--root", root,
                       "--upstream-dir", up,
                       "--manifest", os.path.join(d, "absent.json")])
        assert rc == 0, "emit exited %d" % rc
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(buf.getvalue())
        # The emitted manifest must satisfy the loader that will read it back.
        loaded = load_manifest(out_path)
        assert len(loaded["copy_set"]["files"]) == 2


def test_manifest_shape_errors_exit_2_not_1():
    """Exit 1 is the --strict findings code the merge gate keys on. A manifest
    whose shape is wrong is an operational error (exit 2); letting it surface
    as an unhandled traceback made it exit 1, i.e. indistinguishable from
    real drift."""
    cases = [
        ("qualified_refs", [], "qualified_refs must be a dict"),
        ("upstream", "not-a-dict", "upstream must be a dict"),
        ("routed_prompts", "not-a-list", "routed_prompts must be a list"),
        ("permit_list", [{"text": "x"}], "missing required key: file"),
        ("permit_list", [{"file": "x"}], "missing required key: text"),
    ]
    with tempfile.TemporaryDirectory() as d:
        for key, value, expected in cases:
            m = _valid_manifest()
            m[key] = value
            p = os.path.join(d, "m.json")
            with open(p, "w", encoding="utf-8") as f:
                json.dump(m, f)
            try:
                load_manifest(p)
            except ValueError as e:
                assert expected in str(e), "%s -> %s" % (key, e)
            else:
                raise AssertionError("%s=%r loaded without complaint"
                                     % (key, value))


def test_null_path_in_copy_set_is_a_shape_error_not_a_crash():
    """A null path used to reach the sort as a None and raise TypeError."""
    with tempfile.TemporaryDirectory() as d:
        m = _valid_manifest()
        m["copy_set"]["files"][0]["path"] = None
        p = os.path.join(d, "m.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(m, f)
        try:
            load_manifest(p)
        except ValueError as e:
            assert "missing required key: path" in str(e)
        else:
            raise AssertionError("a null path loaded without complaint")


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
