# plugins/dev-workflows/hooks/session-start.py
"""SessionStart hook: re-point the one skill the upstream superpowers hook names.

The upstream plugin injects skills/using-superpowers/SKILL.md verbatim at session
start, and that text names superpowers:brainstorming as the entry into the arc.
This marketplace vendors six of those skills under an sp- prefix so their reviewer
dispatches reach scrutinize-dispatch. Both texts arrive in one merged attachment,
so this text must win on specificity, not on position (ADR 0070).

Emits nothing when the dev-workflows copies are not present, so a partial install
degrades to silence rather than to a wrong instruction.
"""
import io, json, os, sys, pathlib

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

root = pathlib.Path(os.environ.get("CLAUDE_PLUGIN_ROOT", ""))
# All six vendored copies, named explicitly -- never a "sp-*" glob, which would
# also match sp-grill-with-doc, an unrelated pre-existing skill that is not one
# of the six (controller Ruling 16). A partial install (any one of the six
# missing) must degrade to silence, the same as a fully absent install.
REQUIRED_COPIES = (
    "sp-brainstorming",
    "sp-writing-plans",
    "sp-executing-plans",
    "sp-requesting-code-review",
    "sp-receiving-code-review",
    "sp-subagent-driven-development",
)
if not all((root / "skills" / name / "SKILL.md").is_file() for name in REQUIRED_COPIES):
    sys.exit(0)

TEXT = (
    "IMPORTANT - this marketplace vendors the superpowers review skills. "
    "When you would invoke superpowers:brainstorming, superpowers:writing-plans, "
    "superpowers:executing-plans, superpowers:subagent-driven-development, "
    "superpowers:requesting-code-review or superpowers:receiving-code-review, "
    "you MUST invoke dev-workflows:sp-brainstorming, dev-workflows:sp-writing-plans, "
    "dev-workflows:sp-executing-plans, dev-workflows:sp-subagent-driven-development, "
    "dev-workflows:sp-requesting-code-review or dev-workflows:sp-receiving-code-review "
    "instead of the upstream skill of the same name. This is not a preference: the "
    "upstream copies send every code review to the built-in reviewer, and the sp- "
    "copies send it to dev-workflows:scrutinize-dispatch, which is the whole reason "
    "they exist. Every other superpowers skill is unchanged - use it as normal."
)

print(json.dumps({
    "hookSpecificOutput": {
        "hookEventName": "SessionStart",
        "additionalContext": TEXT,
    }
}))
