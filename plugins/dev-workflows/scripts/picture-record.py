"""picture-record.py — read/write the per-project picture-record.jsonl file.

picture-record.jsonl records what has already been read out of a picture, so a
second run (or a second skill) does not re-open the same image to reach the same
sentence. It is append-only: one JSON object per line, never rewritten. The
canonical schema and question set live in
plugins/dev-workflows/references/picture-record-contract.md.

This script owns ALL read/write so the row format is never corrupted by freehand
edits. Judgment stays in the read-picture SKILL: what the picture shows, which
kind applies, and whether a stored row actually covers the request. This script
never touches git and never writes anything but appended lines.

Subcommands:
  resolve-path [--path P]
      Print the resolved record path (override order: --path > PICTURE_RECORD_FILE
      env > git-root). Exits non-zero with a message when not in a git repo and no
      override is given.
  kinds
      Print the named question set, one per line.
  hash <file>
      Print the SHA-256 of a file's bytes.
  lookup --kind K --detail D (--file F | --source S) [--path P] [--json]
      Report hit / candidates / no-answer plus bytes_verified.
  append --kind K --detail D --answer A --asked-by S
         (--file F | --sha H --source S --source-kind SK) [--path P]
      Validate and append exactly one line.

Importable as a module: resolve_path, hash_file, normalize_detail, make_row,
validate_row, append_row, iter_rows, lookup and Tally are pure functions and
classes whose only side effects are the reads and writes named. The CLI lives
under `if __name__ == "__main__":` so importing never auto-runs.

Dependencies: none beyond the standard library.
"""

import argparse
import hashlib
import io
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone

try:
    sys.stdout.reconfigure(encoding="utf-8")  # Python 3.7+; avoids cp1252 crashes on Windows
except Exception:
    pass

FILE_NAME = "picture-record.jsonl"
ENV_VAR = "PICTURE_RECORD_FILE"
SCHEMA_VERSION = 1

# The named set (ADR 0138). `other` obliges the run to add its new kind to the
# contract document in the same change. test_picture_record.py asserts this tuple
# still matches that document's table.
QUESTION_KINDS = ("on-screen-text", "requirement", "other")

SOURCE_KINDS = ("ado-attachment", "local-path", "url")

# Emit order for a row, key before answer, so a human reading a line sees what was
# asked before what was answered.
ROW_FIELDS = (
    "schema_version",
    "image_sha256",
    "source",
    "source_kind",
    "question_kind",
    "question_detail",
    "answer",
    "read_on",
    "asked_by",
)

_UNSET = object()


def _git_root(cwd=None):
    """Repo root, or None when the cwd is not inside a git repo."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=cwd, capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    root = out.stdout.strip()
    return root or None


def resolve_path(path=None, env_value=None, cwd=None, git_root=_UNSET):
    """--path > PICTURE_RECORD_FILE > git root. None when there is no repo and no
    override, so the caller can ask the user instead of failing (ADR 0142)."""
    if path:
        return path
    if env_value:
        return env_value
    root = _git_root(cwd) if git_root is _UNSET else git_root
    if not root:
        return None
    return os.path.join(root, FILE_NAME)


def hash_file(file_path):
    """SHA-256 of a file's bytes, streamed so a large screenshot is not loaded whole."""
    digest = hashlib.sha256()
    with open(file_path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


_WHITESPACE = re.compile(r"\s+")


def normalize_detail(detail):
    """Fold case and collapse whitespace, so two callers wording the same request
    slightly differently still match. Anything beyond this is judgment and belongs
    in the SKILL, not here."""
    return _WHITESPACE.sub(" ", (detail or "").strip().lower())


def validate_row(row):
    """Raise ValueError unless the row is exactly the contract's nine fields with
    known enum values. Returns the row so callers can wrap it."""
    missing = [name for name in ROW_FIELDS if name not in row]
    if missing:
        raise ValueError("row is missing required field(s): %s" % ", ".join(missing))
    unknown = [name for name in row if name not in ROW_FIELDS]
    if unknown:
        raise ValueError("row carries unknown field(s): %s" % ", ".join(sorted(unknown)))
    if row["schema_version"] != SCHEMA_VERSION:
        raise ValueError(
            "schema_version must be %d, got %r" % (SCHEMA_VERSION, row["schema_version"])
        )
    if row["question_kind"] not in QUESTION_KINDS:
        raise ValueError(
            "question_kind %r is not in the named set (%s)"
            % (row["question_kind"], ", ".join(QUESTION_KINDS))
        )
    if row["source_kind"] not in SOURCE_KINDS:
        raise ValueError(
            "source_kind %r is not one of (%s)"
            % (row["source_kind"], ", ".join(SOURCE_KINDS))
        )
    return row


def make_row(image_sha256, source, source_kind, question_kind, question_detail,
             answer, asked_by, read_on=None):
    """Build one validated row in contract field order."""
    row = {
        "schema_version": SCHEMA_VERSION,
        "image_sha256": image_sha256,
        "source": source,
        "source_kind": source_kind,
        "question_kind": question_kind,
        "question_detail": question_detail,
        "answer": answer,
        "read_on": read_on or datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "asked_by": asked_by,
    }
    return validate_row(row)


def append_row(record_path, row):
    """Append exactly one line. Never rewrites, so no earlier line can be corrupted
    by a bad round-trip (ADR 0143). Returns the line written."""
    validate_row(row)
    line = json.dumps(row, ensure_ascii=False, sort_keys=False) + "\n"
    with io.open(record_path, "a", encoding="utf-8", newline="\n") as handle:
        handle.write(line)
    return line


def iter_rows(record_path):
    """Yield each row in file order — which is chronological, because the file is
    append-only. A blank line is skipped; malformed JSON names its line number."""
    if not record_path or not os.path.exists(record_path):
        return
    with io.open(record_path, encoding="utf-8", newline="") as handle:
        for number, raw in enumerate(handle, 1):
            text = raw.strip()
            if not text:
                continue
            try:
                yield json.loads(text)
            except ValueError:
                raise ValueError("picture record line %d is not valid JSON" % number)
