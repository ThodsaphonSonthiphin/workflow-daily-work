"""test_picture_record.py — unit tests for the picture-record.py helper.

picture-record.py owns an append-only machine contract that other skills read,
so a format or key bug silently serves wrong answers to every caller. These
tests lock the constants against the contract document, path precedence, the
row schema, append-only behaviour, and every lookup outcome.

Run from the repo root:
    python -m pytest plugins/dev-workflows/scripts/test_picture_record.py -v

(`pytest` is not on PATH in this environment — invoke via `python -m pytest`.)
"""

import importlib.util
import io
import json
import os
import re

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_SPEC = importlib.util.spec_from_file_location(
    "picture_record", os.path.join(_HERE, "picture-record.py")
)
pr = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pr)

CONTRACT = os.path.join(_HERE, os.pardir, "references", "picture-record-contract.md")


# ---------- the contract document is the source of truth (ADR 0138) ----------
def test_contract_doc_and_script_agree_on_the_question_kinds():
    doc = io.open(CONTRACT, encoding="utf-8").read()
    seg = doc.split("## Question kinds")[1].split("\n## ")[0]
    names = re.findall(r"^\|\s*`([a-z-]+)`\s*\|", seg, re.M)
    assert tuple(names) == pr.QUESTION_KINDS


def test_contract_doc_and_script_agree_on_the_row_fields():
    doc = io.open(CONTRACT, encoding="utf-8").read()
    seg = doc.split("## Row fields")[1].split("\n## ")[0]
    names = re.findall(r"^\|\s*`([a-z0-9_]+)`\s*\|", seg, re.M)
    assert tuple(names) == pr.ROW_FIELDS


def test_v1_ships_exactly_two_kinds_plus_other():
    # ADR 0140: a kind invented for an unwired caller is a guess.
    assert pr.QUESTION_KINDS == ("on-screen-text", "requirement", "other")


# ---------- resolve_path precedence (ADR 0142) ----------
def test_resolve_path_flag_wins_over_env_and_gitroot():
    got = pr.resolve_path(path="/explicit/x.jsonl", env_value="/env/y.jsonl", git_root="/repo")
    assert got == "/explicit/x.jsonl"


def test_resolve_path_env_wins_over_gitroot():
    got = pr.resolve_path(path=None, env_value="/env/y.jsonl", git_root="/repo")
    assert got == "/env/y.jsonl"


def test_resolve_path_falls_back_to_gitroot_filename():
    got = pr.resolve_path(path=None, env_value=None, git_root="/repo/root")
    assert got == os.path.join("/repo/root", pr.FILE_NAME)


def test_resolve_path_returns_none_when_not_in_repo():
    # None so the CLI can ask the user rather than failing (ADR 0142).
    assert pr.resolve_path(path=None, env_value=None, git_root=None) is None


# ---------- hashing (the first half of the key, ADR 0136) ----------
def test_hash_file_is_stable_and_content_addressed(tmp_path):
    a = tmp_path / "a.png"
    b = tmp_path / "b.png"
    a.write_bytes(b"\x89PNG same bytes")
    b.write_bytes(b"\x89PNG same bytes")
    assert pr.hash_file(str(a)) == pr.hash_file(str(b))
    assert len(pr.hash_file(str(a))) == 64


def test_hash_file_changes_when_one_byte_changes(tmp_path):
    p = tmp_path / "c.png"
    p.write_bytes(b"\x89PNG v1")
    first = pr.hash_file(str(p))
    p.write_bytes(b"\x89PNG v2")
    assert pr.hash_file(str(p)) != first


# ---------- helpers used by the row tests ----------
def _row(**over):
    base = dict(
        image_sha256="a" * 64,
        source="C:/tmp/send-dialog.png",
        source_kind="local-path",
        question_kind="on-screen-text",
        question_detail="the words on the primary button",
        answer="Send",
        asked_by="document-what-shipped",
        read_on="2026-08-24T15:40:00+07:00",
    )
    base.update(over)
    return pr.make_row(**base)


# ---------- detail normalisation ----------
def test_normalize_detail_folds_case_and_whitespace():
    assert pr.normalize_detail("  The   WORDS on\tthe button ") == "the words on the button"


def test_normalize_detail_handles_none():
    assert pr.normalize_detail(None) == ""


# ---------- the row schema ----------
def test_make_row_emits_every_field_in_contract_order():
    assert tuple(_row().keys()) == pr.ROW_FIELDS


def test_make_row_stamps_schema_version():
    assert _row()["schema_version"] == pr.SCHEMA_VERSION


def test_validate_row_rejects_an_unknown_question_kind():
    with pytest.raises(ValueError, match="question_kind"):
        _row(question_kind="error-state")


def test_validate_row_rejects_an_unknown_source_kind():
    with pytest.raises(ValueError, match="source_kind"):
        _row(source_kind="sharepoint")


def test_validate_row_rejects_an_extra_field():
    bad = dict(_row())
    bad["screenshot_notes"] = "everything else I saw"
    with pytest.raises(ValueError, match="unknown field"):
        pr.validate_row(bad)


def test_validate_row_rejects_a_missing_field():
    bad = dict(_row())
    del bad["answer"]
    with pytest.raises(ValueError, match="missing required field"):
        pr.validate_row(bad)


# ---------- append-only (ADR 0143) ----------
def test_append_row_writes_one_json_line(tmp_path):
    rec = str(tmp_path / pr.FILE_NAME)
    pr.append_row(rec, _row())
    lines = io.open(rec, encoding="utf-8").read().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["answer"] == "Send"


def test_appending_leaves_every_earlier_line_byte_identical(tmp_path):
    # This is the test that protects against the whole-file-rewrite scar behind ADR 0143.
    rec = str(tmp_path / pr.FILE_NAME)
    pr.append_row(rec, _row(answer="Send"))
    first = io.open(rec, encoding="utf-8", newline="").read()
    pr.append_row(rec, _row(question_detail="the page title", answer="Send quote"))
    after = io.open(rec, encoding="utf-8", newline="").read()
    assert after.startswith(first)
    assert after[len(first):].count("\n") == 1


def test_iter_rows_round_trips_what_was_appended(tmp_path):
    rec = str(tmp_path / pr.FILE_NAME)
    pr.append_row(rec, _row(answer="Send"))
    pr.append_row(rec, _row(question_detail="the page title", answer="Send quote"))
    got = [r["answer"] for r in pr.iter_rows(rec)]
    assert got == ["Send", "Send quote"]


def test_iter_rows_on_a_missing_file_yields_nothing(tmp_path):
    assert list(pr.iter_rows(str(tmp_path / "nope.jsonl"))) == []


def test_iter_rows_names_the_line_number_of_bad_json(tmp_path):
    rec = tmp_path / pr.FILE_NAME
    rec.write_text('{"ok": 1}\nnot json\n', encoding="utf-8")
    with pytest.raises(ValueError, match="line 2"):
        list(pr.iter_rows(str(rec)))
