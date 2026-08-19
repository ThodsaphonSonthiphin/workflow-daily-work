#!/usr/bin/env python3
"""check_plugin_copies.py - find every copy of a plugin or skill, and grade it.

Reports where a plugin or bare skill exists on THIS machine and whether each
copy matches the source. It CHANGES NOTHING: a person reads the report and
makes the repair it names (ADR 0104).

Nothing about any particular machine is hard-coded. Every location is derived
at run time from the marketplace registry, so the same code runs unchanged on
a machine it has never seen (ADR 0108).

Usage:
  python check_plugin_copies.py --plugin NAME [--marketplace NAME] [--strict]
  python check_plugin_copies.py --plugin NAME --root PATH [--root PATH ...]

Exit codes: 0 clean, 1 findings under --strict, 2 cannot run.
"""
import argparse
import hashlib
import json
import os
import subprocess
import sys


def normalize(data):
    """CR-normalize a byte string (ADR 0086). CRLF -> LF, nothing else."""
    return data.replace(b"\r\n", b"\n")


def content_hash(data):
    return hashlib.sha256(data).hexdigest()


def read_normalized(path):
    with open(path, "rb") as f:
        return normalize(f.read())


def _die(message):
    sys.stderr.write("cannot run: %s\n" % message)
    sys.exit(2)


def load_registry(claude_home):
    """The marketplace registry. This is the only discovery root that is
    assumed to exist at a fixed place."""
    path = os.path.join(claude_home, "plugins", "known_marketplaces.json")
    if not os.path.isfile(path):
        _die("no marketplace registry at %s" % path)
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except ValueError as exc:
        _die("the marketplace registry is not valid JSON (%s)" % exc)


def marketplace_root(registry, marketplace):
    """Where the marketplace's own tree lives.

    A `directory` source means the repo working tree IS the load path -
    editing that tree is the deploy, and the cache is only a snapshot.
    """
    entry = registry.get(marketplace)
    if entry is None:
        _die("no marketplace named %r in the registry (known: %s)"
             % (marketplace, ", ".join(sorted(registry)) or "none"))
    source = entry.get("source") or {}
    if source.get("source") == "directory" and source.get("path"):
        return source["path"]
    location = entry.get("installLocation")
    if not location:
        _die("marketplace %r records neither a directory source nor an "
             "installLocation" % marketplace)
    return location


def plugin_root(mkt_root, plugin):
    """The plugin's directory, read from the marketplace manifest rather than
    assumed to be plugins/<name>."""
    manifest = os.path.join(mkt_root, ".claude-plugin", "marketplace.json")
    if not os.path.isfile(manifest):
        _die("no marketplace manifest at %s" % manifest)
    try:
        with open(manifest, encoding="utf-8") as f:
            data = json.load(f)
    except ValueError as exc:
        _die("the marketplace manifest is not valid JSON (%s)" % exc)
    for entry in data.get("plugins") or []:
        if entry.get("name") == plugin:
            return os.path.normpath(os.path.join(mkt_root, entry["source"]))
    _die("marketplace manifest %s lists no plugin named %r" % (manifest, plugin))


def source_skills(root):
    """{skill name: path to its SKILL.md} for one plugin tree."""
    skills_dir = os.path.join(root, "skills")
    found = {}
    if not os.path.isdir(skills_dir):
        return found
    for name in sorted(os.listdir(skills_dir)):
        candidate = os.path.join(skills_dir, name, "SKILL.md")
        if os.path.isfile(candidate):
            found[name] = candidate
    return found
