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
