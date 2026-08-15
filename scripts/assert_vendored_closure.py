# scripts/assert_vendored_closure.py
"""Assert the vendored copy set is exactly 21 files in six sp- directories."""
import io, sys, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

ROOT = pathlib.Path("plugins/dev-workflows/skills")
EXPECTED = {
    "sp-brainstorming": 8,
    "sp-writing-plans": 2,
    "sp-executing-plans": 1,
    "sp-requesting-code-review": 2,
    "sp-receiving-code-review": 1,
    "sp-subagent-driven-development": 7,
}
DEAD = [
    "sp-brainstorming/spec-document-reviewer-prompt.md",
    "sp-writing-plans/plan-document-reviewer-prompt.md",
]

failures, total = [], 0
for name, count in EXPECTED.items():
    d = ROOT / name
    if not d.is_dir():
        failures.append("missing directory %s" % name)
        continue
    n = sum(1 for p in d.rglob("*") if p.is_file())
    total += n
    if n != count:
        failures.append("%s has %d files, expected %d" % (name, n, count))
    if not (d / "SKILL.md").is_file():
        failures.append("%s has no SKILL.md - the Antigravity installer skips it" % name)

if total != 21:
    failures.append("total is %d files, expected 21" % total)

for rel in DEAD:
    if not (ROOT / rel).is_file():
        failures.append("dead-file detector missing: %s (ADR 0074 keeps it on purpose)" % rel)

lic = pathlib.Path("plugins/dev-workflows/LICENSE-superpowers")
if not lic.is_file():
    failures.append("LICENSE-superpowers is missing")
else:
    t = lic.read_text(encoding="utf-8")
    for needle in ("MIT", "Jesse Vincent", "b36e0829c6d0", "MODIFIED"):
        if needle not in t:
            failures.append("LICENSE-superpowers missing %r" % needle)

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)
print("PASS: 21 files across six sp- directories, licence present")
