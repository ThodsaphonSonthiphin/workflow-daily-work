# scripts/assert_scrutinize_dispatch.py
"""Assert scrutinize-dispatch carries its four deltas from scrutinize (ADR 0084)."""
import io, sys, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SKILL = pathlib.Path("plugins/dev-workflows/skills/scrutinize-dispatch/SKILL.md")
FROZEN = pathlib.Path("plugins/dev-workflows/skills/scrutinize/SKILL.md")

if not SKILL.is_file():
    sys.exit("FAIL: %s does not exist" % SKILL)

text = SKILL.read_text(encoding="utf-8")
failures = []

# frontmatter
for needle in ("name: scrutinize-dispatch", "effort: max"):
    if needle not in text:
        failures.append("frontmatter missing %r" % needle)

# delta 2 - native severity vocabulary
for needle in ("#### Critical (Must Fix)",
               "#### Important (Should Fix)",
               "#### Minor (Nice to Have)"):
    if needle not in text:
        failures.append("severity heading missing %r" % needle)

# delta 3 - the cannot-verify channel
if "⚠️ Cannot verify from diff:" not in text:
    failures.append("missing the cannot-verify channel token")

# delta 1 - blast-radius scope, and NOT scrutinize's end-to-end stance
if "blast radius" not in text:
    failures.append("missing the blast-radius scope rule")
if "The diff is the entry point, not the scope" in text:
    failures.append("carries scrutinize's end-to-end scope stance - delta 1 not applied")

# delta 4 - upstream verdicts
for needle in ("Ready to merge", "Task quality"):
    if needle not in text:
        failures.append("verdict vocabulary missing %r" % needle)

# carried over from scrutinize
for needle in ("simpler", "Cite or it didn't happen", "No flattery"):
    if needle not in text:
        failures.append("dropped a carried-over rule: %r" % needle)

# the freeze
if not FROZEN.is_file():
    failures.append("frozen scrutinize is missing")
elif "scrutinize-dispatch" in FROZEN.read_text(encoding="utf-8"):
    failures.append("FROZEN scrutinize was modified - it must not mention the copy")

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)
print("PASS: scrutinize-dispatch carries all four deltas; scrutinize untouched")
