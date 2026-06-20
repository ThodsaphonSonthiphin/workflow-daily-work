#!/usr/bin/env python3
"""Install the dev-workflows skills into Google Antigravity.

Claude Code installs this plugin through its marketplace and expands
``${CLAUDE_PLUGIN_ROOT}`` for any bundled-file reference. Antigravity does
neither: it discovers skills by folder, matches them semantically on their
``description``, and resolves bundled-file references *relative to the skill
directory* with **no variable expansion**.

So this installer keeps the Claude-native source untouched and produces a
working Antigravity copy: it stages each skill into Antigravity's skills
directory, copies the plugin-level ``references/`` and ``scripts/`` into a shared
support folder beside them, and rewrites every ``${CLAUDE_PLUGIN_ROOT}/...``
reference in the staged copy to the real absolute path. The source tree is never
modified, so Claude Code keeps working exactly as before.

Usage (run with the repo's Python; Antigravity must already be installed):

    python install-antigravity.py                 # IDE global  ~/.gemini/config/skills
    python install-antigravity.py --scope cli      # CLI global  ~/.gemini/antigravity-cli/skills
    python install-antigravity.py --scope project --project /path/to/repo   # <repo>/.agents/skills
    python install-antigravity.py --dest /tmp/x    # explicit target (used for testing)
    python install-antigravity.py --dry-run        # show what would happen, write nothing
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

# .antigravity/install-antigravity.py  ->  plugin root is the parent of .antigravity/
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
SHARED_DIRNAME = ".dev-workflows-shared"  # dot-prefixed: not itself a skill (no SKILL.md)


def target_skills_dir(args: argparse.Namespace) -> Path:
    if args.dest:
        return Path(args.dest).expanduser().resolve()
    if args.scope == "project":
        base = Path(args.project).expanduser().resolve() if args.project else Path.cwd()
        return base / ".agents" / "skills"
    if args.scope == "cli":
        return Path.home() / ".gemini" / "antigravity-cli" / "skills"
    # default: IDE global
    return Path.home() / ".gemini" / "config" / "skills"


def discover_skills() -> list[Path]:
    skills_root = PLUGIN_ROOT / "skills"
    return sorted(p for p in skills_root.iterdir() if (p / "SKILL.md").is_file())


def _fwd(p: Path) -> str:
    """Absolute path with forward slashes — accepted by Python, PowerShell, and POSIX."""
    return str(p).replace("\\", "/")


def rewrite_plugin_root(text: str, dest: Path) -> tuple[str, int]:
    """Replace every ${CLAUDE_PLUGIN_ROOT}/... reference with a real absolute path.

    Three observed shapes, mapped to where the installer actually puts the files:
      ${CLAUDE_PLUGIN_ROOT}/references/  -> <dest>/.dev-workflows-shared/references/
      ${CLAUDE_PLUGIN_ROOT}/scripts/     -> <dest>/.dev-workflows-shared/scripts/
      ${CLAUDE_PLUGIN_ROOT}/skills/      -> <dest>/            (skills are staged flat)
    """
    shared = _fwd(dest / SHARED_DIRNAME)
    dest_fwd = _fwd(dest)
    replacements = {
        "${CLAUDE_PLUGIN_ROOT}/references/": f"{shared}/references/",
        "${CLAUDE_PLUGIN_ROOT}/scripts/": f"{shared}/scripts/",
        "${CLAUDE_PLUGIN_ROOT}/skills/": f"{dest_fwd}/",
    }
    count = 0
    for needle, repl in replacements.items():
        count += text.count(needle)
        text = text.replace(needle, repl)
    return text, count


def _ignore(_dir: str, names: list[str]) -> set[str]:
    return {n for n in names if n in {"__pycache__"} or n.endswith(".pyc")}


def main() -> int:
    ap = argparse.ArgumentParser(description="Install dev-workflows skills into Antigravity.")
    ap.add_argument("--scope", choices=["ide", "cli", "project"], default="ide",
                    help="ide = ~/.gemini/config/skills (default), cli = "
                         "~/.gemini/antigravity-cli/skills, project = <repo>/.agents/skills")
    ap.add_argument("--project", help="repo root for --scope project (default: cwd)")
    ap.add_argument("--dest", help="explicit target skills dir (overrides --scope)")
    ap.add_argument("--dry-run", action="store_true", help="print actions, write nothing")
    args = ap.parse_args()

    dest = target_skills_dir(args)
    skills = discover_skills()
    if not skills:
        print(f"ERROR: no skills found under {PLUGIN_ROOT / 'skills'}", file=sys.stderr)
        return 1

    print(f"Source plugin : {PLUGIN_ROOT}")
    print(f"Target skills : {dest}")
    print(f"Skills to stage: {len(skills)} ({', '.join(p.name for p in skills)})")
    print(f"Shared support : {dest / SHARED_DIRNAME} (references/ + scripts/)")
    if args.dry_run:
        print("\n[dry-run] nothing written.")
        return 0

    if not dest.parent.parent.exists() and args.scope in ("ide", "cli") and not args.dest:
        print(f"\nWARNING: {dest.parent.parent} does not exist — is Antigravity installed?\n"
              f"Proceeding to create {dest} anyway.", file=sys.stderr)

    dest.mkdir(parents=True, exist_ok=True)
    total_rewrites = 0

    # 1. Stage each skill flat into the skills dir.
    for skill in skills:
        out = dest / skill.name
        if out.exists():
            shutil.rmtree(out)
        shutil.copytree(skill, out, ignore=_ignore)

    # 2. Stage plugin-level references/ and scripts/ into the shared support dir.
    shared = dest / SHARED_DIRNAME
    if shared.exists():
        shutil.rmtree(shared)
    shared.mkdir(parents=True)
    for sub in ("references", "scripts"):
        src = PLUGIN_ROOT / sub
        if src.is_dir():
            shutil.copytree(src, shared / sub, ignore=_ignore)

    # 3. Rewrite ${CLAUDE_PLUGIN_ROOT}/... in every staged markdown file.
    staged_md = list(dest.rglob("*.md"))
    leftover_files: list[Path] = []
    for md in staged_md:
        original = md.read_text(encoding="utf-8")
        rewritten, n = rewrite_plugin_root(original, dest)
        if n:
            md.write_text(rewritten, encoding="utf-8")
            total_rewrites += n
        if "${CLAUDE_PLUGIN_ROOT}" in rewritten:
            leftover_files.append(md)

    print(f"\nStaged {len(skills)} skills, rewrote {total_rewrites} "
          f"${{CLAUDE_PLUGIN_ROOT}} reference(s) across {len(staged_md)} markdown files.")
    if leftover_files:
        print("WARNING: unresolved ${CLAUDE_PLUGIN_ROOT} remains in:", file=sys.stderr)
        for f in leftover_files:
            print(f"  - {f}", file=sys.stderr)
        return 2

    print("Done. Reload Antigravity so it rediscovers the skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
