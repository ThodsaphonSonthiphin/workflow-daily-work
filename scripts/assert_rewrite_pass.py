# scripts/assert_rewrite_pass.py
"""Assert the ADR 0074 rewrite pass, classes 1-4, is fully applied."""
import io, sys, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = pathlib.Path("plugins/dev-workflows/skills")
failures = []

# class 1 - the two live reviewer prompts route to scrutinize-dispatch, by its
# bare name (Antigravity stages skills flat with no plugin namespace, so a
# plugin-qualified name cannot resolve there). re-review-prompt.md is not a
# review - it verdicts prior findings ADDRESSED/NOT ADDRESSED - and is
# deliberately left untouched, so it is not in this list.
PROMPTS = [
    "sp-requesting-code-review/code-reviewer.md",
    "sp-subagent-driven-development/task-reviewer-prompt.md",
]
for rel in PROMPTS:
    p = ROOT / rel
    if not p.is_file():
        failures.append("missing prompt file %s" % rel)
        continue
    t = p.read_text(encoding="utf-8")
    if "scrutinize-dispatch" not in t:
        failures.append("%s does not route to scrutinize-dispatch" % rel)
    if "dev-workflows:scrutinize-dispatch" in t:
        failures.append("%s uses the plugin-qualified name - Antigravity stages "
                         "skills flat with no plugin namespace, so this cannot "
                         "resolve there; use the bare name" % rel)

# class 2 - no cross-skill path may point at a non-sp- sibling
for rel in ["sp-subagent-driven-development/SKILL.md", "sp-executing-plans/SKILL.md"]:
    p = ROOT / rel
    if not p.is_file():
        continue
    t = p.read_text(encoding="utf-8")
    if "../requesting-code-review/" in t:
        failures.append("%s still points at ../requesting-code-review/ (needs sp-)" % rel)
    if "../using-superpowers/" in t:
        failures.append("%s still points at ../using-superpowers/ - that skill is "
                        "never staged; qualify it as superpowers:using-superpowers" % rel)

# class 3 - plugin-root-relative path becomes skill-relative
p = ROOT / "sp-brainstorming/SKILL.md"
if p.is_file() and "skills/brainstorming/visual-companion.md" in p.read_text(encoding="utf-8"):
    failures.append("sp-brainstorming/SKILL.md still uses a plugin-root path for its own file")

# class 4 - qualified handoffs among the six become short sp- names
p = ROOT / "sp-writing-plans/SKILL.md"
if p.is_file():
    t = p.read_text(encoding="utf-8")
    for bad in ("superpowers:executing-plans", "superpowers:subagent-driven-development"):
        if bad in t:
            failures.append("sp-writing-plans still hands off to %s" % bad)

# no copy may reference the frozen human-facing skill
# Explicit directory list, not a sp-* glob: sp-grill-with-doc is a pre-existing
# skill of this repo, not one of the six vendored copies, and must not be
# swept into this check.
VENDORED_DIRS = [
    "sp-brainstorming",
    "sp-writing-plans",
    "sp-executing-plans",
    "sp-requesting-code-review",
    "sp-receiving-code-review",
    "sp-subagent-driven-development",
]
for d in VENDORED_DIRS:
    dpath = ROOT / d
    if not dpath.is_dir():
        continue
    for p in dpath.glob("**/*.md"):
        t = p.read_text(encoding="utf-8")
        if "scrutinize" in t and "scrutinize-dispatch" not in t:
            failures.append("%s references scrutinize but not scrutinize-dispatch" % p)

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)
print("PASS: rewrite pass classes 1-4 applied")
