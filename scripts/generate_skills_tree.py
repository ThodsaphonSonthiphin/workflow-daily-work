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


IMPORT_RE = re.compile(r"^\s*(?:import|from)\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)


class MissingReference(Exception):
    """A SKILL.md names a file that is not in its plugin."""


def is_excluded(rel):
    """Test files and fixtures do not travel unless a SKILL.md names them."""
    parts = rel.split("/")
    if "fixtures" in parts[:-1] or parts[-1] == "fixtures":
        return True
    return parts[-1].startswith("test_")


def local_imports(py_path):
    """Module names imported by py_path that exist as .py siblings.

    A regex, not ast.parse: the sources are this repo's own scripts, and a
    file that fails to parse must not take the whole build down with it.
    """
    directory = os.path.dirname(py_path)
    out = []
    for mod in IMPORT_RE.findall(read_text(py_path)):
        if mod in out:
            continue
        if os.path.isfile(os.path.join(directory, mod + ".py")):
            out.append(mod)
    return out


def resolve_files(plugin_root, refs):
    """Every file a skill needs: what it names, plus transitive local imports.

    Returns {plugin-relative path: absolute source path}. A named file is
    always included; an excluded file reached only by import is dropped.
    """
    resolved = {}
    queue = [(r, True) for r in refs]
    while queue:
        rel, named = queue.pop(0)
        if rel in resolved:
            continue
        absolute = os.path.join(plugin_root, rel.replace("/", os.sep))
        if not os.path.isfile(absolute):
            if named:
                raise MissingReference(
                    "%s names %s, which does not exist" % (plugin_root, rel))
            continue
        if not named and is_excluded(rel):
            continue
        resolved[rel] = absolute
        if rel.endswith(".py"):
            parent = os.path.dirname(rel)
            for mod in local_imports(absolute):
                sibling = "%s/%s.py" % (parent, mod) if parent else mod + ".py"
                queue.append((sibling, False))
    return resolved


# The rewritten form rewrite_refs() produces, so Task 6's checker can prove
# each target landed in the directory the CLI will copy.
SKILL_DIR_REF_RE = re.compile(r"\$\{CLAUDE_SKILL_DIR\}/([A-Za-z0-9_][A-Za-z0-9_./-]*)")

SUPERPOWERS_LICENCE = "LICENSE-superpowers"
MATTPOCOCK_LICENCE = "LICENSE-mattpocock-skills"

VENDORED = {
    "sp-brainstorming": SUPERPOWERS_LICENCE,
    "sp-executing-plans": SUPERPOWERS_LICENCE,
    "sp-receiving-code-review": SUPERPOWERS_LICENCE,
    "sp-requesting-code-review": SUPERPOWERS_LICENCE,
    "sp-subagent-driven-development": SUPERPOWERS_LICENCE,
    "sp-writing-plans": SUPERPOWERS_LICENCE,
    "wait-what": MATTPOCOCK_LICENCE,
}


def licence_for(name):
    """The licence file a vendored skill must carry (ADR 0158)."""
    return VENDORED.get(name)


def rewrite_refs(text):
    """Rewrite plugin-root references by kind (ADR 0164).

    A .md target becomes a path relative to the skill directory - the Agent
    Skills standard form. Everything else becomes ${CLAUDE_SKILL_DIR}/..., so
    a Bash command resolves from any working directory. An unclassifiable
    target falls back to ${CLAUDE_SKILL_DIR}, which is never wrong in
    Claude Code.
    """
    def sub(m):
        ref = m.group(1)
        trailing = ""
        while ref and ref[-1] in ".,;:)":
            trailing = ref[-1] + trailing
            ref = ref[:-1]
        if not ref:
            return m.group(0)
        if ref.endswith(".md"):
            return ref + trailing
        return "${CLAUDE_SKILL_DIR}/" + ref + trailing
    return REF_RE.sub(sub, text)


def apply_argument_hint(text, hint):
    """Set argument-hint in the leading frontmatter block."""
    if not hint or not text.startswith("---"):
        return text
    end = text.find("\n---", 3)
    if end == -1:
        return text
    head, tail = text[3:end], text[end:]
    lines = [ln for ln in head.splitlines() if not ln.startswith("argument-hint:")]
    inserted = False
    out = []
    for ln in lines:
        out.append(ln)
        if not inserted and ln.startswith("description:"):
            out.append("argument-hint: " + hint)
            inserted = True
    if not inserted:
        out.append("argument-hint: " + hint)
    return "---" + "\n".join(out) + tail


def emit_skill(skill, out_root, hints):
    """Write one resolved skill directory. Returns its path."""
    # src_dir is <repo>/plugins/<plugin>/skills/<dirname>; up two is the plugin.
    plugin_root = os.path.dirname(os.path.dirname(skill.src_dir))
    dest = os.path.join(out_root, skill.name)
    os.makedirs(dest, exist_ok=True)

    for entry in sorted(os.listdir(skill.src_dir)):
        source = os.path.join(skill.src_dir, entry)
        target = os.path.join(dest, entry)
        if os.path.isdir(source):
            _copy_tree(source, target)
        else:
            _copy_file(source, target, rewrite=entry.endswith(".md"))

    md_path = os.path.join(dest, "SKILL.md")
    text = read_text(md_path)
    hint = hints.get(skill.name)
    if hint:
        text = apply_argument_hint(text, hint)
        _write_text(md_path, text)

    refs = plugin_root_refs(read_text(os.path.join(skill.src_dir, "SKILL.md")))
    for rel, absolute in sorted(resolve_files(plugin_root, refs).items()):
        target = os.path.join(dest, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        _copy_file(absolute, target, rewrite=rel.endswith(".md"))

    licence = licence_for(skill.name)
    if licence:
        _copy_file(os.path.join(plugin_root, licence),
                   os.path.join(dest, licence), rewrite=False)
    return dest


def _write_text(path, text):
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _copy_file(source, target, rewrite):
    os.makedirs(os.path.dirname(target), exist_ok=True)
    if rewrite:
        _write_text(target, rewrite_refs(read_text(source)))
    else:
        with open(source, "rb") as fsrc, open(target, "wb") as fdst:
            fdst.write(fsrc.read())


def _copy_tree(source, target):
    for root, _dirs, files in os.walk(source):
        for entry in sorted(files):
            src = os.path.join(root, entry)
            rel = os.path.relpath(src, source)
            _copy_file(src, os.path.join(target, rel),
                       rewrite=entry.endswith(".md"))
