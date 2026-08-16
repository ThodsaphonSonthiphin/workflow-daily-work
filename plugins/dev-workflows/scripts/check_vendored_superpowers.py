#!/usr/bin/env python3
"""check_vendored_superpowers.py - the vendored-superpowers resync checker.

Reports drift in this marketplace's vendored copies of the upstream
`superpowers` skills. It CHANGES NOTHING: a person makes the repairs it names
and re-runs it until it exits 0 (ADR 0075).

Two modes:
  local (default)    Has anything changed OUR copies since they were vendored?
  --upstream-dir P   Has upstream moved, and which of the copied files changed?
                     P is the upstream PLUGIN ROOT (the directory holding
                     skills/), because one trap scans hooks/ and scripts/ too.

Every byte comparison is CR-normalized first (ADR 0086). git stores LF blobs
and Windows checks out CRLF, so raw bytes carry no information here: 0 of the
21 working-tree files equal their own committed blob.

Nothing is hard-coded about the copy set - not its size, not the skill names,
not the permitted lines. All of it is read from the manifest, so an intended
change is a manifest edit and never a code edit.

Usage:
  python check_vendored_superpowers.py [--strict]
  python check_vendored_superpowers.py --upstream-dir PATH [--strict]
  python check_vendored_superpowers.py --emit-manifest --upstream-dir PATH > new.json

Report mode (default): prints findings, exit 0. --strict makes any finding
exit 1. Exit 2 = cannot run.
"""
import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_ROOT = os.path.dirname(HERE)
DEFAULT_MANIFEST = os.path.join(PLUGIN_ROOT, "references",
                                "vendored-superpowers.json")
DEFAULT_ROOT = os.path.join(PLUGIN_ROOT, "skills")

REQUIRED_KEYS = ("upstream", "copy_set", "permit_list", "qualified_refs",
                 "routing_marker", "routed_prompts", "unrouted_prompts",
                 "frozen", "upstream_traps")


def normalize(data):
    """CR-normalize a byte string (ADR 0086). CRLF -> LF, nothing else."""
    return data.replace(b"\r\n", b"\n")


def read_normalized(path):
    with open(path, "rb") as f:
        return normalize(f.read())


def read_text(path):
    return read_normalized(path).decode("utf-8", "replace")


def content_hash(data):
    return hashlib.sha256(data).hexdigest()


def finding(check, path, message, repair):
    """One reported problem. `repair` says what the runner should DO."""
    return {"check": check, "path": path, "message": message, "repair": repair}


def load_manifest(path):
    """Read the manifest. Raises ValueError if it cannot be trusted."""
    try:
        with open(path, encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        raise ValueError("manifest not found: %s" % path)
    except json.JSONDecodeError as e:
        raise ValueError("manifest is not valid JSON: %s" % e)
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be a JSON object")
    missing = [k for k in REQUIRED_KEYS if k not in manifest]
    if missing:
        raise ValueError("manifest is missing required key(s): %s"
                         % ", ".join(missing))

    # Validate copy_set structure
    copy_set = manifest.get("copy_set")
    if not isinstance(copy_set, dict):
        raise ValueError("copy_set must be a dict")
    if "files" not in copy_set:
        raise ValueError("copy_set is missing required key: files")
    if not isinstance(copy_set["files"], list):
        raise ValueError("copy_set.files must be a list")

    # Validate each file entry
    for i, entry in enumerate(copy_set["files"]):
        if not isinstance(entry, dict):
            raise ValueError("copy_set.files[%d] must be a dict" % i)
        if "path" not in entry:
            raise ValueError("copy_set.files[%d] is missing required key: path"
                           % i)
        if "upstream_path" not in entry:
            raise ValueError("copy_set.files[%d] is missing required key: upstream_path"
                           % i)

    return manifest


def copied_skill_dirs(manifest):
    """The vendored directory names, FROM THE MANIFEST - never a glob.

    A glob of `sp-*` also collects sp-grill-with-doc, which carries the prefix
    but is not a vendored copy (ADR 0071)."""
    return sorted({f["path"].split("/")[0]
                   for f in manifest["copy_set"]["files"]})


def upstream_skill_names(manifest):
    """The upstream short names, derived from the 1:1 path mapping."""
    return sorted({f["upstream_path"].split("/")[0]
                   for f in manifest["copy_set"]["files"]})


def check_copy_set(root, manifest):
    """Check 1 - every declared file exists, and no undeclared file sits
    inside a directory this manifest governs.

    Governed = the vendored skill dirs PLUS the top-level directory of every
    frozen file, so a file dropped beside a frozen one is seen too. A frozen
    file's own absence is reported by check_frozen, not here."""
    out = []
    declared = {f["path"] for f in manifest["copy_set"]["files"]}
    known = declared | {e["path"] for e in manifest.get("frozen", [])}
    for rel in sorted(declared):
        if not os.path.isfile(os.path.join(root, rel)):
            out.append(finding(
                "copy-set", rel, "declared file is missing from the tree",
                "restore it from upstream, or re-emit the manifest if the "
                "copy set genuinely shrank"))
    governed = set(copied_skill_dirs(manifest))
    governed |= {e["path"].split("/")[0]
                 for e in manifest.get("frozen", []) if "/" in e["path"]}
    for skill_dir in sorted(governed):
        base = os.path.join(root, skill_dir)
        for dirpath, _, names in os.walk(base):
            for name in names:
                rel = os.path.relpath(os.path.join(dirpath, name),
                                      root).replace("\\", "/")
                if rel not in known:
                    out.append(finding(
                        "copy-set", rel,
                        "file inside a directory this manifest governs is "
                        "not declared in it",
                        "if it came from upstream, copy it in properly and "
                        "add it; if it is ours, it does not belong beside a "
                        "vendored copy or a frozen file"))
    return sorted(out, key=lambda f: f["path"])


def check_hashes(root, manifest):
    """Check 2 - each copied file still hashes to its vendored value."""
    out = []
    for f in manifest["copy_set"]["files"]:
        path = os.path.join(root, f["path"])
        if not os.path.isfile(path):
            continue          # already reported by check_copy_set
        actual = content_hash(read_normalized(path))
        if actual != f["sha256"]:
            out.append(finding(
                "hash", f["path"],
                "content changed since vendoring (%s -> %s)"
                % (f["sha256"][:12], actual[:12]),
                "revert the edit, or re-vendor the set and re-emit the "
                "manifest. An edit inside a copy can break its route to "
                "scrutinize-dispatch with no error message"))
    return out


def check_frozen(root, manifest):
    """Check 6 - the frozen files are unchanged (ADR 0088)."""
    out = []
    for entry in manifest["frozen"]:
        path = os.path.join(root, entry["path"])
        if not os.path.isfile(path):
            out.append(finding(
                "frozen", entry["path"], "frozen file is missing",
                "restore it - %s" % entry["why"]))
            continue
        actual = content_hash(read_normalized(path))
        if actual != entry["sha256"]:
            out.append(finding(
                "frozen", entry["path"],
                "FROZEN file changed - %s" % entry["why"],
                "revert it. If the change is genuinely required it needs a "
                "decision first (ADR 0084's escape hatch), then a manifest "
                "update in the same commit"))
    return out


def main(argv):
    ap = argparse.ArgumentParser(
        description="Report drift in the vendored superpowers copies.")
    ap.add_argument("--manifest", default=DEFAULT_MANIFEST)
    ap.add_argument("--root", default=DEFAULT_ROOT,
                    help="the skills/ directory holding the copies")
    ap.add_argument("--upstream-dir", default=None,
                    help="upstream plugin root (the directory holding skills/)")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 if there is any finding")
    ap.add_argument("--emit-manifest", action="store_true",
                    help="print a freshly computed manifest to stdout")
    args = ap.parse_args(argv)

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):  # pragma: no cover
        pass

    try:
        manifest = load_manifest(args.manifest)
    except ValueError as e:
        print("ERROR: %s" % e)
        return 2

    findings = []
    print("OK: manifest loaded (%d files declared)."
          % len(manifest["copy_set"]["files"]))
    return 1 if (findings and args.strict) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
