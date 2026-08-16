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
        failures.append("missing file %s" % p)
        continue
    t = p.read_text(encoding="utf-8")
    if "../requesting-code-review/" in t:
        failures.append("%s still points at ../requesting-code-review/ (needs sp-)" % rel)
    if "../using-superpowers/" in t:
        failures.append("%s still points at ../using-superpowers/ - that skill is "
                        "never staged; qualify it as superpowers:using-superpowers" % rel)

# class 3 - plugin-root-relative path becomes skill-relative
p = ROOT / "sp-brainstorming/SKILL.md"
if not p.is_file():
    failures.append("missing file %s" % p)
elif "skills/brainstorming/visual-companion.md" in p.read_text(encoding="utf-8"):
    failures.append("sp-brainstorming/SKILL.md still uses a plugin-root path for its own file")

# class 4 - qualified handoffs among the six become short sp- names
p = ROOT / "sp-writing-plans/SKILL.md"
if not p.is_file():
    failures.append("missing file %s" % p)
else:
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
# 3b - reintroducing a plugin-qualified reference to any of the six copied
# skills, anywhere in the six vendored directories, is a regression: those six
# names are the ones this task short-formed to sp-*.
QUALIFIED_COPY_NAMES = [
    "superpowers:brainstorming",
    "superpowers:writing-plans",
    "superpowers:executing-plans",
    "superpowers:requesting-code-review",
    "superpowers:receiving-code-review",
    "superpowers:subagent-driven-development",
]

missing_dirs = [d for d in VENDORED_DIRS if not (ROOT / d).is_dir()]
if missing_dirs:
    failures.append("missing vendored directories: %s" % ", ".join(missing_dirs))
for d in VENDORED_DIRS:
    dpath = ROOT / d
    if not dpath.is_dir():
        continue
    for p in dpath.glob("**/*.md"):
        t = p.read_text(encoding="utf-8")
        if "scrutinize" in t and "scrutinize-dispatch" not in t:
            failures.append("%s references scrutinize but not scrutinize-dispatch" % p)
        for name in QUALIFIED_COPY_NAMES:
            if name in t:
                failures.append("%s still references the plugin-qualified %s - the six "
                                 "copied names must be short-formed to sp-*" % (p, name))

# class 5 - the host SessionStart hook re-points arc entry to sp-brainstorming
import json
hj = pathlib.Path("plugins/dev-workflows/hooks/hooks.json")
if not hj.is_file():
    failures.append("hooks.json is missing")
else:
    cfg = json.loads(hj.read_text(encoding="utf-8"))
    ss = cfg.get("hooks", {}).get("SessionStart")
    if not ss:
        failures.append("no SessionStart hook registered")
    else:
        blob = json.dumps(ss)
        if "session-start.py" not in blob:
            failures.append("SessionStart does not call session-start.py")
        if "${CLAUDE_PLUGIN_ROOT}" not in blob:
            failures.append("hook command must use ${CLAUDE_PLUGIN_ROOT}, not a hard-coded path")
hp = pathlib.Path("plugins/dev-workflows/hooks/session-start.py")
if not hp.is_file():
    failures.append("session-start.py is missing")
else:
    t = hp.read_text(encoding="utf-8")
    if "sp-brainstorming" not in t:
        failures.append("hook text does not name sp-brainstorming")
    if "instead of" not in t.lower():
        failures.append("hook text does not name the conflict outright (ADR 0070)")

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)
print("PASS: rewrite pass classes 1-4 applied")
