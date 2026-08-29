#!/usr/bin/env python3
"""check_skills_tree.py - prove skills/ still matches plugins/*/skills/.

Regenerates the tree into a temporary directory and compares it byte for
byte against the committed one, then asserts the invariants from ADR 0162 and
the spec. It REPORTS and never writes to skills/ - a person (or CI) reads the
findings and runs generate_skills_tree.py to repair them.

Usage:
  python3 scripts/check_skills_tree.py [--repo PATH]

Exit codes: 0 clean, 1 findings, 2 cannot run.
"""
import argparse
import collections
import io
import os
import posixpath
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generate_skills_tree as g

# A bare relative path naming a markdown document: at least one directory
# segment, then a `.md` file. The lookbehind keeps the match off the tail of a
# longer path and off an already-rewritten ${CLAUDE_SKILL_DIR}/... token.
#
# Requiring BOTH a slash and the .md suffix is what keeps ordinary English out
# of the check: `and/or` has no extension, `read/write.md` names no real file.
# The finding needs a third thing on top - the path must resolve to a real file
# in the owning plugin - so prose can only be flagged by naming a plugin file.
BARE_MD_REF_RE = re.compile(
    r"(?<![\w/${.-])"
    r"([A-Za-z0-9_][A-Za-z0-9_.-]*(?:/[A-Za-z0-9_][A-Za-z0-9_.-]*)+\.md)\b")

# Directories the generated tree deliberately never carries (spec S3,
# Exclusions: "Commands and hooks are not represented in the tree"). A skill
# naming a file under one is describing a plugin-channel feature, not
# resolving a reference - `daily` and `ticket-trace` both do, correctly.
NEVER_TRAVELS = ("hooks", "commands")


def _files_under(root):
    """Every file under root, as {posix relative path: bytes}."""
    out = {}
    for base, _dirs, files in os.walk(root):
        for name in sorted(files):
            path = os.path.join(base, name)
            rel = os.path.relpath(path, root).replace(os.sep, "/")
            with open(path, "rb") as f:
                out[rel] = f.read().replace(b"\r\n", b"\n")
    return out


def _bare_reference_findings(repo, tree_files):
    """The first half of the spec S3 invariant: a relative path a generated
    file names must resolve inside its own skill directory.

    The rewriter only ever followed `${CLAUDE_PLUGIN_ROOT}/...`. A plugin-level
    file named by a BARE relative path - `references/data-contracts.md` - was
    invisible to it, so the reference travelled and the file did not, and the
    installed skill read as if the document were there.

    A finding needs all three of these, and the third is what stops the check
    crying wolf: the path is shaped like a path, it names a real file under the
    skill's OWN plugin root, and no such file arrived in the skill directory.
    Prose can only be flagged by naming a file the plugin actually has.

    Scoped to `.md` targets - the read half of ADR 0164. The run half already
    has its clause above, over `${CLAUDE_SKILL_DIR}/...`, and a bare path to a
    script is a run path written the wrong way, which that clause is the right
    place to grow into.
    """
    findings = []
    plugin_roots = dict(
        (s.name, os.path.dirname(os.path.dirname(s.src_dir)))
        for s in g.discover_skills(repo))
    for rel, data in sorted(tree_files.items()):
        if not rel.endswith(".md"):
            continue
        parts = rel.split("/")
        skill_dir, here = parts[0], "/".join(parts[:-1])
        plugin_root = plugin_roots.get(skill_dir)
        if plugin_root is None:
            continue  # a stray directory; the drift comparison already said so
        for named in dict.fromkeys(
                BARE_MD_REF_RE.findall(data.decode("utf-8", "replace"))):
            if named.split("/")[0] in NEVER_TRAVELS or g.is_excluded(named):
                continue
            if not os.path.isfile(
                    os.path.join(plugin_root, named.replace("/", os.sep))):
                continue
            # A markdown link resolves against the containing file; prose in a
            # nested file often spells the path from the skill root instead.
            # Either arrival counts - the point is that the file is present.
            if (posixpath.normpath(posixpath.join(here, named)) in tree_files
                    or "%s/%s" % (skill_dir, named) in tree_files):
                continue
            findings.append(
                "skills/%s names %s, a file its plugin has and the skill does "
                "not - write it as ${CLAUDE_PLUGIN_ROOT}/%s in the source so "
                "the generator resolves it (ADR 0170)" % (rel, named, named))
    return findings


def check(repo):
    """Return a list of findings. Empty means clean."""
    findings = []

    names = [s.name for s in g.discover_skills(repo)]
    for name, count in sorted(collections.Counter(names).items()):
        if count > 1:
            findings.append(
                "name '%s' is declared twice - the CLI keeps one and drops "
                "the rest (ADR 0156)" % name)

    committed_root = os.path.join(repo, g.TREE_DIRNAME)
    temp_root = tempfile.mkdtemp(prefix="skillstree-check-")
    try:
        g.build(repo, temp_root)
        expected = _files_under(temp_root)
        actual = _files_under(committed_root) if os.path.isdir(committed_root) else {}

        for rel in sorted(set(expected) - set(actual)):
            findings.append("missing from skills/: %s" % rel)
        for rel in sorted(set(actual) - set(expected)):
            findings.append("not generated by the sources: skills/%s" % rel)
        for rel in sorted(set(expected) & set(actual)):
            if expected[rel] != actual[rel]:
                findings.append(
                    "differs from what the sources generate: skills/%s" % rel)
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)

    if os.path.isdir(committed_root):
        tree_files = _files_under(committed_root)
        for rel, data in sorted(tree_files.items()):
            # Only a .md file is reference-rewritten, and only a token followed by
            # a real path is a reference at all. A ${CLAUDE_PLUGIN_ROOT} inside a
            # .cs comment, or the documented prose form ${CLAUDE_PLUGIN_ROOT}/...
            # which names nothing, are both legitimate survivors (ADR 0164, and
            # the ruling recorded against Task 5).
            if not rel.endswith(".md"):
                continue
            for named in g.REF_RE.findall(data.decode("utf-8", "replace")):
                findings.append(
                    "skills/%s still names ${CLAUDE_PLUGIN_ROOT}/%s - that "
                    "expands to nothing outside a plugin install" % (rel, named))
        for rel, data in sorted(tree_files.items()):
            if not rel.endswith(".md"):
                continue
            skill_dir = rel.split("/")[0]
            for named in g.SKILL_DIR_REF_RE.findall(data.decode("utf-8", "replace")):
                target = os.path.join(committed_root, skill_dir,
                                      named.replace("/", os.sep))
                if not os.path.isfile(target):
                    findings.append(
                        "skills/%s names %s, which is not in that skill "
                        "directory - the CLI copies nothing else" % (rel, named))

        findings.extend(_bare_reference_findings(repo, tree_files))

        for entry in sorted(os.listdir(committed_root)):
            md = os.path.join(committed_root, entry, "SKILL.md")
            if not os.path.isfile(md):
                continue
            declared = g.frontmatter_name(g.read_text(md))
            if declared != entry:
                findings.append(
                    "skills/%s declares name '%s' - the CLI installs by the "
                    "frontmatter name, so the two must match (ADR 0162)"
                    % (entry, declared))
    return findings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", default=".")
    args = parser.parse_args(argv)
    if not os.path.isdir(os.path.join(args.repo, g.PLUGINS_DIRNAME)):
        sys.stderr.write("cannot run: no %s/ under %s\n"
                         % (g.PLUGINS_DIRNAME, args.repo))
        return 2
    findings = check(args.repo)
    for f in findings:
        print("FINDING  %s" % f)
    if findings:
        print("\n%d finding(s). Repair with: "
              "python3 scripts/generate_skills_tree.py" % len(findings))
        return 1
    print("skills/ matches plugins/*/skills/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
