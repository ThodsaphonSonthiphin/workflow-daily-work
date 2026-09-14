# Handoff Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use sp-subagent-driven-development (recommended) or sp-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** ship `dev-workflows:handoff` — a vendored, modified copy of mattpocock's `handoff` with a `cloud` destination — reachable at any moment via a `/daily` footer beside Save.

**Architecture:** The skill, its command wrapper, the licence entry, the generator map and ADRs 0227–0229 are already drafted on branch `handoff-skill`; Task 1 verifies those drafts line by line against the spec and commits them. Tasks 2–4 add the `/daily` footer, the PLAYBOOK row, the two manifests' version and description. Task 5 regenerates the `skills/` tree and runs every checker. No skill is edited to *call* handoff (ADR 0229).

**Tech Stack:** Markdown skills, JSON manifests, Python 3 (`python3` only on this Mac) for the generator, its plain-assert test runner, and the vendored-superpowers checker.

**Spec:** `docs/superpowers/specs/2026-09-14-handoff-skill-design.md` (ADRs 0227–0229 and the CONTEXT.md terms already written on the branch).

## Global Constraints

- Branch `handoff-skill` (already checked out, off `main`). Never commit on `main`.
- Run scripts with `python3`, never `python`. The generator test is a plain script: `python3 scripts/test_generate_skills_tree.py` → prints `N/N passed` and exits 0. There is no pytest on this machine.
- Baselines on the branch today: generator tests **40/40 passed**; `python3 plugins/dev-workflows/scripts/check_vendored_superpowers.py --strict` → `OK: 21 copied files (13 verbatim), 15 permitted bare names, 2 frozen files`.
- Every commit message ends with `Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>` — verbatim; repo policy, not the committer's identity.
- Something auto-stages untracked files on `git` calls: commit with explicit paths — `git add -- <paths> && git commit -m "…" -- <paths>` — and read `git status --short` first.
- `skills/` at the repo root is generated. Never hand-edit it; Task 5 regenerates once with `python3 scripts/generate_skills_tree.py --repo .` and verifies with `python3 scripts/check_skills_tree.py --repo .`.
- `plugins/dev-workflows/.claude-plugin/plugin.json` and the `dev-workflows` entry in `.claude-plugin/marketplace.json` must both say `0.56.0` (Task 4).
- Skills stay harness-neutral: the phrase `Skill tool` must not appear in `skills/handoff/SKILL.md`; skill-relative paths only; `${CLAUDE_PLUGIN_ROOT}` is not needed by this skill.
- `disable-model-invocation: true` stays in the handoff frontmatter (ADR 0227).
- No edit to `sp-writing-plans`, `grill-then-plan`, or any other skill to call `handoff` (ADR 0229). `git diff --stat main -- plugins/dev-workflows/skills/sp-* plugins/dev-workflows/skills/grill-then-plan` must stay empty.

---

### Task 1: verify the drafted skill, wrapper, licence entry and generator map against the spec, then commit them

**Files:**
- Verify (drafted, uncommitted): `plugins/dev-workflows/skills/handoff/SKILL.md`, `plugins/dev-workflows/commands/handoff.md`, `plugins/dev-workflows/LICENSE-mattpocock-skills`, `scripts/generate_skills_tree.py` (the `VENDORED` map, ~L205–213), `scripts/test_generate_skills_tree.py` (~L376–377), `CONTEXT.md` (the *handoff terms* section), `docs/adr/workflow-daily-work-0227-*.md`, `0228-*.md`, `0229-*.md`, `docs/superpowers/specs/2026-09-14-handoff-skill-design.md`, `docs/superpowers/plans/2026-09-14-handoff-skill.md` (this file).

**Interfaces:**
- Consumes: spec §3 (skill body order), §4 (six cloud steps), §6 (licence + generator).
- Produces: the skill name `handoff`, the command `/dev-workflows:handoff`, and `generate_skills_tree.licence_for("handoff") == "LICENSE-mattpocock-skills"` — Task 5 depends on the last.

- [ ] **Step 1: Run the drafted generator test to confirm the map entry is live**

```bash
cd /Users/liusp/Documents/repo/workflow-daily-work
python3 scripts/test_generate_skills_tree.py 2>&1 | tail -1
python3 -c "import sys; sys.path.insert(0,'scripts'); import generate_skills_tree as g; assert g.licence_for('handoff')=='LICENSE-mattpocock-skills'; print('map ok')"
```

Expected: `40/40 passed` and `map ok`.

- [ ] **Step 2: Check the skill body against spec §3 — section order and the harness-neutral rule**

```bash
f=plugins/dev-workflows/skills/handoff/SKILL.md
grep -n "^## " $f
# expect, in this order:
#   ## What goes in
#   ## Where it goes — the destination decides
#   ## The cloud destination, step by step
#   ## It's working if
grep -n -E "^name: handoff|^disable-model-invocation: true|^argument-hint:" $f   # expect all three
grep -n -i "skill tool" $f            # expect NO output
grep -c "cloud" $f                    # expect >= 8
grep -n "docs/superpowers/handoffs/" $f   # expect >= 2
grep -n 'claude --cloud "Read' $f     # expect 1
grep -n "claude --teleport" $f        # expect 1
grep -n -i "mermaid" $f               # expect 1 (the 'one small Mermaid diagram at the top' rule)
```

If any expectation fails, edit the draft until it holds — the spec is the authority, the draft is not.

- [ ] **Step 3: Check the six cloud steps against spec §4**

```bash
sed -n '/^## The cloud destination, step by step/,/^## It/p' $f | grep -n -E "^[0-9]\. \*\*" 
```

Expected: six numbered bold steps, in this order: *Everything must be on the branch* · *Write the file* · *The plugins are not there* · *Give the launch, both ways* · *Say how the result comes back* · *The file stays*. Step 1's text must contain both `Never push \`main\`` and the word `offer` (assisted git).

- [ ] **Step 4: Check the wrapper, the licence entry and the glossary**

```bash
grep -n -E "^description:|^argument-hint:|handoff|\\\$ARGUMENTS" plugins/dev-workflows/commands/handoff.md
# expect: description, argument-hint, "Use the **`handoff`** skill", "Argument: $ARGUMENTS"
grep -n -E "MODIFIED|6654f6b60cd9d5be8b54c6fafe44346dabeb3b76|skills/productivity/handoff/SKILL.md|commands/handoff.md" plugins/dev-workflows/LICENSE-mattpocock-skills
# expect all four
grep -n -E "^\*\*Handoff document\*\*|^\*\*Save state vs Handoff\*\*|^## handoff terms" CONTEXT.md   # expect three lines
ls docs/adr | grep -E "0227|0228|0229"   # expect exactly three files
```

- [ ] **Step 5: Commit the drafts as one "vendor" commit**

```bash
git status --short
git add -- plugins/dev-workflows/skills/handoff/SKILL.md plugins/dev-workflows/commands/handoff.md plugins/dev-workflows/LICENSE-mattpocock-skills scripts/generate_skills_tree.py scripts/test_generate_skills_tree.py CONTEXT.md docs/adr/workflow-daily-work-0227-handoff-is-vendored-from-mattpocock-skills-as-a-modified-copy.md docs/adr/workflow-daily-work-0228-the-cloud-destination-commits-and-pushes-the-handoff-into-the-repo.md docs/adr/workflow-daily-work-0229-handoff-is-reachable-at-any-moment-a-daily-footer-beside-save-not-a-hook-in-one-skill.md docs/superpowers/specs/2026-09-14-handoff-skill-design.md docs/superpowers/plans/2026-09-14-handoff-skill.md
git commit -m "feat(dev-workflows): vendor handoff from mattpocock/skills, MODIFIED with a cloud destination (ADRs 0227-0229)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -- plugins/dev-workflows/skills/handoff plugins/dev-workflows/commands/handoff.md plugins/dev-workflows/LICENSE-mattpocock-skills scripts/generate_skills_tree.py scripts/test_generate_skills_tree.py CONTEXT.md docs/adr docs/superpowers
git status --short   # expect: clean
```

---

### Task 2: the second `/daily` footer line

**Files:**
- Modify: `plugins/dev-workflows/skills/daily/SKILL.md` — the menu block (~L92–103) and the sentence after it (~L105–108).

**Interfaces:**
- Consumes: the command name `/dev-workflows:handoff` (Task 1).
- Produces: nothing downstream; Task 5's regenerated `skills/daily/SKILL.md` carries it.

- [ ] **Step 1: Add the footer line**

Replace, inside the fenced menu block:

```
(Next time: /daily start · work · file · report · wrap)
💾 Save state anytime: /daily save "<note>"
```

with:

```
(Next time: /daily start · work · file · report · wrap)
💾 Save state anytime: /daily save "<note>"
🚀 Hand off anytime:   /dev-workflows:handoff [cloud] "<what next>"
```

- [ ] **Step 2: Replace the sentence after the block**

Replace:

```markdown
The `Next time` line teaches the station shortcuts; the 💾 line teaches the save
accelerator — both graduate users from the menu. Save is a footer, not a sixth
option: the circle stays five stations (ADR 0004).
```

with:

```markdown
The `Next time` line teaches the station shortcuts; the 💾 and 🚀 lines teach the
two accelerators — save keeps your resume-point here, handoff sends the work away
(ADR 0229) — all three graduate users from the menu. Save and Handoff are footers,
not a sixth or seventh option: the circle stays five stations (ADR 0004).
```

- [ ] **Step 3: Verify — the menu still has exactly five numbered options and the frontmatter is untouched**

```bash
f=plugins/dev-workflows/skills/daily/SKILL.md
sed -n '/^Where are you in your day/,/^```/p' $f | grep -c -E "^  [1-5]\. "   # expect 5
grep -c "🚀 Hand off anytime" $f      # expect 1
grep -c "ADR 0229" $f                 # expect 1
git diff -- $f | grep -E "^[-+]description|^[-+]name:"   # expect NO output
```

- [ ] **Step 4: Commit**

```bash
git add -- plugins/dev-workflows/skills/daily/SKILL.md
git commit -m "feat(daily): a second footer — 🚀 Hand off anytime — beside Save (ADR 0229)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -- plugins/dev-workflows/skills/daily/SKILL.md
```

---

### Task 3: PLAYBOOK — the handoff row and the Save bullet's twin sentence

**Files:**
- Modify: `PLAYBOOK.md` — insert one row after the `wait-what` row (~L94); append one sentence to the `/daily save` bullet (~L153–156).

**Interfaces:**
- Consumes: nothing new.
- Produces: the discoverability row CLAUDE.md requires for every new skill.

- [ ] **Step 1: Insert the row**

Directly after the table row that begins `| the agent's *last message* lost you` insert:

```markdown
| the work has to TRAVEL — another harness, another machine or repo, a colleague, a forked side task, or a Claude Code cloud session | `handoff` (`/dev-workflows:handoff [cloud] "<what next>"`) — compacts the live thread into one handoff document (refs, not copies; secrets redacted; suggested skills named); default lands in temp, `cloud` commits and pushes it into `docs/superpowers/handoffs/` because a cloud session clones from GitHub. Usable at any moment; the 🚀 footer of `/daily` reminds you. Vendored from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) and MODIFIED (ADRs 0227–0229); manual invocation only |
```

- [ ] **Step 2: Extend the Save bullet**

The bullet beginning `- **\`/daily save "<note>"\`** (synonyms \`pause\` · \`checkpoint\`)` ends with a sentence about the next session reading `daily-state.md`. Append, as the bullet's last sentence: `Its twin for when the work leaves this machine is \`/dev-workflows:handoff\` (ADR 0229).`

- [ ] **Step 3: Verify**

```bash
grep -c "/dev-workflows:handoff" PLAYBOOK.md         # expect 2
grep -n "the work has to TRAVEL" PLAYBOOK.md          # expect 1 line, directly below the wait-what row
awk -F'|' '/the work has to TRAVEL/{print NF}' PLAYBOOK.md   # expect 4 (a 2-column row renders as 4 fields)
```

- [ ] **Step 4: Commit**

```bash
git add -- PLAYBOOK.md
git commit -m "docs(playbook): handoff row — the work has to travel; save's twin (ADR 0229)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -- PLAYBOOK.md
```

---

### Task 4: version 0.56.0 and the description sentence in both manifests

**Files:**
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json` (`version`, `description`)
- Modify: `.claude-plugin/marketplace.json` (the `dev-workflows` entry: `version` ~L36, `description` ~L35)

**Interfaces:**
- Consumes: nothing new.
- Produces: `0.56.0` in both files.

- [ ] **Step 1: Apply both edits with one script (the descriptions are single long JSON strings — do not hand-edit)**

```bash
cd /Users/liusp/Documents/repo/workflow-daily-work
python3 - <<'EOF'
import json, re
SENT = ("Handing work elsewhere: handoff (/dev-workflows:handoff — compacts the conversation "
        "into a handoff document for a new harness, another machine, a colleague or a Claude "
        "Code cloud session; `cloud` commits and pushes it because cloud clones from GitHub. "
        "Usable at any moment; a /daily footer beside Save reminds you. Vendored from "
        "mattpocock/skills under MIT and MODIFIED, see LICENSE-mattpocock-skills; "
        "disable-model-invocation is true, so it runs only when the user asks). ")
ANCHOR = "Growth: career-growth"

def bump(text):
    assert text.count(ANCHOR) == 1, "anchor must appear exactly once"
    assert 'Handing work elsewhere' not in text, "already applied"
    return text.replace(ANCHOR, SENT + ANCHOR, 1)

p = "plugins/dev-workflows/.claude-plugin/plugin.json"
d = json.load(open(p, encoding="utf-8"))
assert d["version"] == "0.55.0", d["version"]
d["version"] = "0.56.0"
d["description"] = bump(d["description"])
open(p, "w", encoding="utf-8").write(json.dumps(d, indent=2, ensure_ascii=False) + "\n")

p = ".claude-plugin/marketplace.json"
raw = open(p, encoding="utf-8").read()
d = json.loads(raw)
e = next(x for x in d["plugins"] if x["name"] == "dev-workflows")
assert e["version"] == "0.55.0", e["version"]
# Edit the raw text so the rest of the file's formatting is untouched.
raw = raw.replace(json.dumps(e["description"], ensure_ascii=False),
                  json.dumps(bump(e["description"]), ensure_ascii=False), 1)
raw = re.sub(r'("name": "dev-workflows",\n(?:.*\n){1,4}?\s*"version": )"0\.55\.0"', r'\1"0.56.0"', raw, count=1)
open(p, "w", encoding="utf-8").write(raw)
print("bumped")
EOF
```

- [ ] **Step 2: Verify both files parse, agree, and the sentence landed once each**

```bash
python3 - <<'EOF'
import json
p = json.load(open("plugins/dev-workflows/.claude-plugin/plugin.json"))
m = next(e for e in json.load(open(".claude-plugin/marketplace.json"))["plugins"] if e["name"] == "dev-workflows")
assert p["version"] == m["version"] == "0.56.0", (p["version"], m["version"])
assert p["description"].count("Handing work elsewhere") == 1
assert m["description"].count("Handing work elsewhere") == 1
print("versions agree:", p["version"])
EOF
git diff --stat -- plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json   # expect 2 files, small diffs
```

If `plugin.json` re-serialised with a different key order or indentation than before, that is acceptable only if `git diff` shows the version and description lines as the sole changes; otherwise restore the file (`git checkout -- plugins/dev-workflows/.claude-plugin/plugin.json`) and apply the two edits with `sed` on the exact strings instead.

- [ ] **Step 3: Commit**

```bash
git add -- plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "chore(dev-workflows): 0.55.0 -> 0.56.0 — the handoff skill

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -- plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json
```

---

### Task 5: regenerate `skills/`, run every checker, prove nothing vendored moved

**Files:**
- Modify (generated): `skills/handoff/**` (new), `skills/daily/SKILL.md`, and whatever else the generator refreshes.

**Interfaces:**
- Consumes: everything above.
- Produces: a branch ready for whole-branch review and merge.

- [ ] **Step 1: Regenerate and list what changed**

```bash
cd /Users/liusp/Documents/repo/workflow-daily-work
python3 scripts/generate_skills_tree.py --repo .
git status --short skills/ | head -20
ls skills/handoff/    # expect SKILL.md and LICENSE-mattpocock-skills (ADR 0158)
```

- [ ] **Step 2: Run the three checkers**

```bash
python3 scripts/check_skills_tree.py --repo .; echo "skills tree exit=$?"
python3 plugins/dev-workflows/scripts/check_vendored_superpowers.py --strict; echo "vendored exit=$?"
python3 scripts/test_generate_skills_tree.py 2>&1 | tail -1
```

Expected: `skills tree exit=0`; `OK: 21 copied files (13 verbatim), 15 permitted bare names, 2 frozen files` and `vendored exit=0`; `40/40 passed`.

- [ ] **Step 3: Prove no skill was edited to call handoff (ADR 0229) and the generated copy is harness-neutral**

```bash
git diff --stat main -- plugins/dev-workflows/skills/sp-brainstorming plugins/dev-workflows/skills/sp-writing-plans plugins/dev-workflows/skills/sp-executing-plans plugins/dev-workflows/skills/sp-subagent-driven-development plugins/dev-workflows/skills/sp-requesting-code-review plugins/dev-workflows/skills/sp-receiving-code-review plugins/dev-workflows/skills/grill-then-plan
# expect: NO output
grep -rn -i "skill tool" skills/handoff/SKILL.md   # expect NO output
grep -c "🚀 Hand off anytime" skills/daily/SKILL.md   # expect 1
```

- [ ] **Step 4: Commit the tree**

```bash
git add -- skills/
git commit -m "chore(skills): regenerate skills/ after the handoff skill (ADRs 0227-0229)

Co-Authored-By: Claude Fable 5.1 <noreply@anthropic.com>" -- skills/
git status --short   # expect: clean
```

- [ ] **Step 5: Re-verify the ADR numbers against every branch and worktree before merge (CLAUDE.md)**

```bash
git fetch --all --quiet
{ git for-each-ref --format='%(refname)' refs/heads refs/remotes | while read r; do git ls-tree -r --name-only "$r" -- docs/adr 2>/dev/null; done; git worktree list --porcelain | grep '^worktree ' | cut -d' ' -f2- | while read w; do ls "$w"/docs/adr 2>/dev/null; done; } | grep -oE '(^|/)([a-z-]+-)?0*([0-9]{3,4})-' | grep -oE '[0-9]{3,4}' | sort -n | uniq -c | awk '$1>1 && $2>=227'
```

Expected: no output. Any line means another branch minted the same number (branch `decision-map-frontier-sweep` holds 0222–0226 and is expected to be distinct); renumber ours — files, cross-references in the spec, plan, PLAYBOOK row, CONTEXT.md and `daily/SKILL.md` — before merging.
