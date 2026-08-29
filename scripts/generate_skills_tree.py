#!/usr/bin/env python3
"""generate_skills_tree.py - build skills/ from plugins/*/skills/.

The skills.sh CLI copies a skill DIRECTORY and nothing above it, so a skill
that names ${CLAUDE_PLUGIN_ROOT}/references/... installs and then fails. This
generator writes a resolved copy of every skill into skills/<name>/ at the
repo root: the files it names, the files those import, its vendored licence,
and its command's argument-hint (ADRs 0153-0164).

The tree is generated and committed. Never hand-edit it; check_skills_tree.py
fails the build if you do.

Usage:
  python3 scripts/generate_skills_tree.py [--repo PATH] [--out PATH]
"""
import argparse
import collections
import io
import os
import re
import sys

PLUGINS_DIRNAME = "plugins"
TREE_DIRNAME = "skills"

# A reference is ${CLAUDE_PLUGIN_ROOT}/ followed by a path. The character class
# deliberately excludes '.' as a FIRST character so the documented prose form
# ${CLAUDE_PLUGIN_ROOT}/... is not read as a path (spec, Global Constraints).
REF_RE = re.compile(r"\$\{CLAUDE_PLUGIN_ROOT\}/([A-Za-z0-9_][A-Za-z0-9_./-]*)")

Skill = collections.namedtuple("Skill", "plugin name src_dir")


def read_text(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def frontmatter_name(text):
    """The value of `name:` in the leading --- block, or None.

    Claude Code reads frontmatter only when the opening --- is the file's
    first line, so this does too.
    """
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    for line in text[3:end].splitlines():
        if line.startswith("name:"):
            return line[len("name:"):].strip().strip('"').strip("'")
    return None


def plugin_root_refs(text):
    """Relative paths named after ${CLAUDE_PLUGIN_ROOT}/, in order, unique."""
    out = []
    for m in REF_RE.finditer(text):
        ref = m.group(1).rstrip(".,;:)")
        if ref and ref not in out:
            out.append(ref)
    return out


def discover_skills(repo):
    """Every skill under plugins/*/skills/*/SKILL.md, sorted by plugin then dir."""
    root = os.path.join(repo, PLUGINS_DIRNAME)
    found = []
    if not os.path.isdir(root):
        return found
    for plugin in sorted(os.listdir(root)):
        skills_dir = os.path.join(root, plugin, "skills")
        if not os.path.isdir(skills_dir):
            continue
        for dirname in sorted(os.listdir(skills_dir)):
            src = os.path.join(skills_dir, dirname)
            md = os.path.join(src, "SKILL.md")
            if not os.path.isfile(md):
                continue
            name = frontmatter_name(read_text(md))
            if name is None:
                continue
            found.append(Skill(plugin, name, src))
    return found
