# scripts/assert_conventions.py
import io, sys, json, pathlib
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
failures = []

SKILLS = ["scrutinize-dispatch", "sp-brainstorming", "sp-writing-plans",
          "sp-executing-plans", "sp-requesting-code-review",
          "sp-receiving-code-review", "sp-subagent-driven-development"]
pb = pathlib.Path("PLAYBOOK.md").read_text(encoding="utf-8")
for s in SKILLS:
    if s not in pb:
        failures.append("PLAYBOOK.md has no row for %s" % s)

pj = json.loads(pathlib.Path("plugins/dev-workflows/.claude-plugin/plugin.json").read_text(encoding="utf-8"))
mk = json.loads(pathlib.Path(".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
entry = next((p for p in mk["plugins"] if p["name"] == "dev-workflows"), None)
if entry is None:
    failures.append("dev-workflows missing from marketplace.json")
elif entry["version"] != pj["version"]:
    failures.append("version mismatch: plugin.json %s vs marketplace.json %s"
                    % (pj["version"], entry["version"]))

ctx = pathlib.Path("CONTEXT.md").read_text(encoding="utf-8")
for term in ("Vendored Skill", "Reviewer prompt"):
    if term not in ctx:
        failures.append("CONTEXT.md missing glossary term %r" % term)
if "scrutinize-dispatch" not in ctx:
    failures.append("CONTEXT.md glossary still routes to scrutinize, not scrutinize-dispatch (ADR 0084)")
if "0084" not in ctx:
    failures.append("CONTEXT.md glossary does not cite ADR 0084")
for stale in ("translates on the way out", "severity words the prompt translates"):
    if stale in ctx:
        failures.append("CONTEXT.md still describes the deleted translation layer: %r" % stale)

if failures:
    for f in failures:
        print("FAIL: %s" % f)
    sys.exit(1)
print("PASS: PLAYBOOK rows, version parity, glossary terms")
