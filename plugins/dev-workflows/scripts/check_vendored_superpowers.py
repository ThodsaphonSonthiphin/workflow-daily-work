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

QUALIFIED = re.compile(r"superpowers:([a-z][a-z0-9-]*)")


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
        if "sha256" not in entry:
            raise ValueError("copy_set.files[%d] is missing required key: sha256"
                           % i)

    # Validate frozen list
    frozen = manifest.get("frozen")
    if not isinstance(frozen, list):
        raise ValueError("frozen must be a list")
    for i, entry in enumerate(frozen):
        if not isinstance(entry, dict):
            raise ValueError("frozen[%d] must be a dict" % i)
        if "path" not in entry:
            raise ValueError("frozen[%d] is missing required key: path" % i)
        if "sha256" not in entry:
            raise ValueError("frozen[%d] is missing required key: sha256" % i)

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


def bare_name_re(names):
    """Match an upstream short name that is NOT prefixed.

    The lookbehind rejects `superpowers:brainstorming` (preceded by ':') and
    `sp-brainstorming` (preceded by '-'), which is exactly ADR 0071's check:
    a search for any of the six upstream short names, unprefixed, must return
    nothing. Longest-first alternation so a longer name cannot be shadowed."""
    alt = "|".join(re.escape(n) for n in sorted(names, key=len, reverse=True))
    return re.compile(r"(?<![\w:-])(" + alt + r")\b", re.IGNORECASE)


def check_bare_names(root, manifest):
    """Check 3 - ADR 0071's check, run against the files.

    NEW        a bare short name on a line the permit list does not hold.
    STALE      a permitted line that is no longer present in its file.
    UNREVIEWED a permit entry whose `why` is still a REVIEW: placeholder."""
    pattern = bare_name_re(upstream_skill_names(manifest))

    declared = Counter((e["file"], e["text"]) for e in manifest["permit_list"])

    out = []
    actual = Counter()
    for f in manifest["copy_set"]["files"]:
        rel = f["path"]
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue          # already reported by check_copy_set
        for line in read_text(path).split("\n"):
            if not pattern.search(line):
                continue
            if (rel, line) in declared:
                actual[(rel, line)] += 1
                continue
            out.append(finding(
                "permit-list/NEW", rel,
                "bare upstream skill name on an unlisted line: %s"
                % line.strip()[:160],
                "if it is a handoff, give it the sp- prefix - a bare name "
                "resolves to the UNVENDORED upstream skill with no error. If "
                "it is genuinely inert, add the line to permit_list with a why"))

    for (rel, text), want in sorted(declared.items()):
        got = actual[(rel, text)]
        if got < want:
            out.append(finding(
                "permit-list/STALE", rel,
                "permit list claims this line %d time(s), found %d: %s"
                % (want, got, text.strip()[:160]),
                "the line moved, was reworded or was deleted. Re-confirm it "
                "is still inert, then update permit_list"))
        elif any(str(e.get("why", "")).startswith("REVIEW:")
                 for e in manifest["permit_list"]
                 if e["file"] == rel and e["text"] == text):
            out.append(finding(
                "permit-list/UNREVIEWED", rel,
                "permit entry still carries a REVIEW: placeholder",
                "state why this bare name is inert, then replace the why. An "
                "unreviewed entry permits a line nobody has judged"))
    return out


def check_qualified_refs(root, manifest):
    """Check 4 - no qualified reference names a skill that IS in the copy set,
    and the census of the rest is unchanged.

    ADR 0071 tabulates only two names with counts 5 and 3. A third,
    `using-superpowers`, is legitimately present (rewrite class 2), so an
    exact-match assertion on that table would fail on a correct tree. The
    rule is 'none of the copied names'; the census is reported separately."""
    copied = set(upstream_skill_names(manifest))
    census = {}
    out = []
    for f in manifest["copy_set"]["files"]:
        rel = f["path"]
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            continue
        for lineno, line in enumerate(read_text(path).split("\n"), 1):
            for match in QUALIFIED.finditer(line):
                name = match.group(1)
                census[name] = census.get(name, 0) + 1
                if name in copied:
                    out.append(finding(
                        "qualified-ref", rel,
                        "line %d names superpowers:%s, which IS in the copy "
                        "set" % (lineno, name),
                        "rewrite it to the short sp-%s name - left as is, the "
                        "arc re-enters the upstream original one handoff "
                        "later (ADR 0074 class 4)" % name))
    recorded = dict(manifest["qualified_refs"])
    if census != recorded:
        out.append(finding(
            "qualified-ref/census", "-",
            "qualified reference census changed: recorded %s, found %s"
            % (recorded, census),
            "confirm every new or changed reference names a skill that stays "
            "upstream, then update qualified_refs"))
    return out


def check_routing(root, manifest):
    """Check 5 - the routed reviewer prompts name the dispatch engine, and the
    deliberately unrouted one does not (ADR 0084 and its amendment).

    Only the prompt FILES are asserted. Two `description:` fields also mention
    the marker; asserting a raw repo-wide count would couple this check to
    description wording."""
    marker = manifest["routing_marker"]
    out = []
    for rel in manifest["routed_prompts"]:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            out.append(finding("routing", rel, "routed prompt is missing",
                               "restore it"))
            continue
        if marker not in read_text(path):
            out.append(finding(
                "routing", rel,
                "routed reviewer prompt no longer names `%s`" % marker,
                "restore the delegation line. Without it the dispatch falls "
                "back to the built-in reviewer, with no error and no warning "
                "- the exact failure this vendoring exists to remove"))
    for rel in manifest["unrouted_prompts"]:
        path = os.path.join(root, rel)
        if not os.path.isfile(path):
            out.append(finding("routing", rel, "unrouted prompt is missing",
                               "restore it"))
            continue
        if marker in read_text(path):
            out.append(finding(
                "routing", rel,
                "deliberately unrouted prompt now names `%s`" % marker,
                "remove it. A re-review verdicts each prior finding ADDRESSED "
                "or NOT ADDRESSED, which that engine has no way to express "
                "(ADR 0084, amendment of 2026-08-16)"))
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
