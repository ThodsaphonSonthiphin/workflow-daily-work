# Superpowers Review-to-Scrutinize Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Vendor the six review-carrying `superpowers` skills into `dev-workflows` as `sp-*` copies whose review steps route to this repo's frozen `scrutinize`, working on Claude Code and Antigravity, with a runnable resync path back to upstream.

**Architecture:** The upstream plugin stays fully enabled; six skill directories are copied verbatim from `obra/superpowers@b36e082` and then edited in one rewrite pass so their three live reviewer prompts delegate the review *method* to `scrutinize` while keeping their own output contract. A host SessionStart hook re-points the one skill the upstream hook names. Nothing in `scrutinize` is edited — it is frozen by decision.

**Tech Stack:** Markdown skills and commands; Python 3 stdlib for the two new scripts (no third-party imports); plain-assert test files run with `python test_x.py`, matching `check_doc_provenance.py` and its test beside it.

**Spec:** [`docs/decision-map/superpowers-review-to-scrutinize/map.md`](../../decision-map/superpowers-review-to-scrutinize/map.md) — this effort produced a **Decision map** rather than a brainstorming spec, which is what `decision-map` exists to do for work too big for one session. The map's Destination, Notes and 20 closed tickets are the requirements; the normative content is **ADRs 0069–0082** in [`docs/adr/`](../../adr/). Executors read the map and the ADRs it links, not this plan alone.

## Global Constraints

- **`scrutinize` is FROZEN.** Its behaviour, stance and output format are never edited. If a change to it is genuinely required, that change goes into a **new** Skill that is a copy of it — and taking that option changes the effort's destination rather than being a step here (ADR 0076).
- **The vendoring source is `obra/superpowers` at `b36e082`.** The closure is exactly **21 files** over six skill directories: **2407** Markdown lines and **1559** non-Markdown. Verified 2026-08-15 against the live repo; any deviation means the source moved and this plan's line numbers are stale.
- **Eight qualified references must be LEFT ALONE:** `superpowers:finishing-a-development-branch` (×5) and `superpowers:using-git-worktrees` (×3). Those two skills stay upstream and the copies must still reach them. A rewriter matching `superpowers:` broadly breaks all eight (ADR 0075).
- **Short form, no plugin prefix,** for every reference into the copies — `sp-writing-plans`, never `dev-workflows:sp-writing-plans`. No upstream skill name begins with `sp-`, which is what makes this unambiguous on both harnesses (ADR 0071 Decision 2, ADR 0072 Decision 2).
- **The Mermaid diagram convention does NOT reach the six copies or the documents they generate.** It still binds this repo's own skills, ADRs and ticket resolutions. Three **wiring** conventions do bind the copies: plugin-root path shapes, frontmatter, and harness-neutral wording (ADR 0077).
- **`${CLAUDE_PLUGIN_ROOT}` only in the three installer-rewritable shapes:** `/references/…`, `/scripts/…`, `/skills/…`. A fourth shape means updating `install-antigravity.py`'s `rewrite_plugin_root()`. Measured: the 21 vendored files contain **zero** occurrences, so no new shape arrives with them.
- **Versions in sync:** `plugins/dev-workflows/.claude-plugin/plugin.json` and its entry in `.claude-plugin/marketplace.json` must report the same version. Current: **0.37.0**; this plan ships **0.38.0**. Marketplace top-level goes **0.4.0 → 0.5.0**.
- **PLAYBOOK rows are due in the same commit that adds a skill or command** — never a later one (`CLAUDE.md`).
- **ADR numbers and versions are minted from the global max across every ref and worktree**, not `current + 1` from this checkout. Current max: **0082**. Re-verify immediately before merging (ADR 0056).
- **No new ADRs are required.** Every decision this plan implements is already recorded in ADRs 0069–0082. If implementation invalidates one, add its supersession banner **in the same commit** that invalidates it.
- **Scope check (run per `writing-plans`):** this is **one** plan, not several. Tasks 1–5 build the copies and their wiring — one subsystem with one test cycle. Tasks 6–8 are satellites (commands, a setup check, the resync checker) that each depend on the copies existing and cannot produce working software before them. Splitting would create plans that cannot be executed independently, which is the condition the scope check exists to avoid.

---

### Task 1: Attribution — carry the upstream MIT licence before any copied byte lands

**Files:**
- Create: `LICENSE`
- Create: `plugins/dev-workflows/LICENSE-superpowers`

**Interfaces:**
- Produces: the sha string `b36e0829c6d0`, recorded in `LICENSE-superpowers` and re-read by Task 8's resync checker as the single recorded upstream sha.

- [ ] **Step 1: Write the repo's own `LICENSE`**

The repo has never had one, and `plugin.json` already claims `"license": "MIT"`. Create `LICENSE` at the repo root:

```
MIT License

Copyright (c) 2026 Thodsaphon Sonthiphin

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 2: Write `plugins/dev-workflows/LICENSE-superpowers`**

One file for the whole copy set — never a per-file header (the `attribution` ticket). It carries the sha and the MODIFIED marker:

```
The skills in this plugin whose names begin with `sp-` are copies of skills from
the superpowers project, taken at commit b36e0829c6d0, and MODIFIED.

Modifications: their review steps are routed to this marketplace's `scrutinize`
skill, their names carry an `sp-` prefix, and references among them use that
prefix. See docs/adr/0071, 0074, 0075 and 0076.

Upstream: https://github.com/obra/superpowers

MIT License

Copyright (c) 2025 Jesse Vincent

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

Copy the licence body verbatim from `/workspace/obra/superpowers/LICENSE` rather than retyping it; the block above must match that file byte for byte below the `MIT License` line.

- [ ] **Step 3: Verify both files exist and carry the sha**

Run:

```bash
test -f LICENSE && test -f plugins/dev-workflows/LICENSE-superpowers && \
grep -q "b36e0829c6d0" plugins/dev-workflows/LICENSE-superpowers && \
grep -q "MODIFIED" plugins/dev-workflows/LICENSE-superpowers && echo OK
```

Expected: `OK`.

- [ ] **Step 4: Commit**

```bash
git add LICENSE plugins/dev-workflows/LICENSE-superpowers
git commit -m "docs(dev-workflows): carry upstream MIT for the vendored skills, and add the repo LICENSE"
```

---

### Task 2: Vendor the 21 files verbatim, and record their hashes

**Files:**
- Create: `plugins/dev-workflows/skills/sp-brainstorming/` (8 files)
- Create: `plugins/dev-workflows/skills/sp-writing-plans/` (2 files)
- Create: `plugins/dev-workflows/skills/sp-executing-plans/` (1 file)
- Create: `plugins/dev-workflows/skills/sp-subagent-driven-development/` (7 files)
- Create: `plugins/dev-workflows/skills/sp-requesting-code-review/` (2 files)
- Create: `plugins/dev-workflows/skills/sp-receiving-code-review/` (1 file)
- Create: `plugins/dev-workflows/references/vendored-superpowers-manifest.json`

**Interfaces:**
- Produces: `vendored-superpowers-manifest.json`, shape
  `{"upstream": "https://github.com/obra/superpowers", "sha": "b36e0829c6d0", "files": {"<skill>/<relpath>": "<sha256 hex>"}}` — 21 entries, hashes taken from the **upstream** bytes before any edit. Task 8's checker reads exactly this file.

The directories are named `sp-*` from the start; the file contents are untouched. The frontmatter still says `name: brainstorming` at the end of this task — Task 3 fixes that. This intermediate state is committed deliberately: the manifest hashes must describe upstream bytes, so they can only be taken here.

- [ ] **Step 1: Clone the vendoring source at the recorded sha**

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/obra/superpowers /tmp/sp-src
git -C /tmp/sp-src checkout b36e0829c6d0
git -C /tmp/sp-src rev-parse --short HEAD
```

Expected: `b36e082`.

- [ ] **Step 2: Copy the six directories under their `sp-` names**

```bash
cd "$(git rev-parse --show-toplevel)"
for s in brainstorming writing-plans executing-plans \
         subagent-driven-development requesting-code-review receiving-code-review; do
  cp -R "/tmp/sp-src/skills/$s" "plugins/dev-workflows/skills/sp-$s"
done
```

- [ ] **Step 3: Verify the closure — 21 files, 2407 Markdown lines, 1559 non-Markdown**

```bash
cd "$(git rev-parse --show-toplevel)/plugins/dev-workflows/skills"
find sp-brainstorming sp-writing-plans sp-executing-plans \
     sp-subagent-driven-development sp-requesting-code-review \
     sp-receiving-code-review -type f | wc -l
find sp-* -type f -name '*.md' -exec cat {} + | wc -l
find sp-* -type f ! -name '*.md' -exec cat {} + | wc -l
```

Expected: `21`, then `2407`, then `1559`. Any other number means the source moved — stop and re-check the sha rather than continuing.

- [ ] **Step 4: Write the manifest generator and run it once**

Create `plugins/dev-workflows/scripts/build_vendored_manifest.py`:

```python
#!/usr/bin/env python3
"""Regenerate the vendored-superpowers manifest from the staged sp-* skills.

Run once at vendoring time, and again only when the recorded sha changes:
  python build_vendored_manifest.py --sha b36e0829c6d0
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

SKILLS = ["brainstorming", "writing-plans", "executing-plans",
          "subagent-driven-development", "requesting-code-review",
          "receiving-code-review"]
PLUGIN_ROOT = Path(__file__).resolve().parent.parent
UPSTREAM = "https://github.com/obra/superpowers"


def file_hashes(skills_dir):
    out = {}
    for name in SKILLS:
        root = skills_dir / f"sp-{name}"
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            key = f"{name}/{path.relative_to(root).as_posix()}"
            out[key] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sha", required=True, help="upstream commit the copies were taken from")
    args = ap.parse_args(argv)

    hashes = file_hashes(PLUGIN_ROOT / "skills")
    if len(hashes) != 21:
        print(f"ERROR: expected 21 files, found {len(hashes)}", file=sys.stderr)
        return 2

    out = PLUGIN_ROOT / "references" / "vendored-superpowers-manifest.json"
    out.write_text(json.dumps(
        {"upstream": UPSTREAM, "sha": args.sha, "files": hashes},
        indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {out} ({len(hashes)} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 5: Generate the manifest**

```bash
python plugins/dev-workflows/scripts/build_vendored_manifest.py --sha b36e0829c6d0
```

Expected: `wrote .../vendored-superpowers-manifest.json (21 files)`, exit 0.

- [ ] **Step 6: Verify the manifest describes upstream bytes**

```bash
python -c "
import json,hashlib,pathlib
m=json.load(open('plugins/dev-workflows/references/vendored-superpowers-manifest.json'))
src=pathlib.Path('/tmp/sp-src/skills')
bad=[k for k,v in m['files'].items()
     if hashlib.sha256((src/k).read_bytes()).hexdigest()!=v]
print('mismatches:', bad or 'none'); print('count:', len(m['files']))
"
```

Expected: `mismatches: none` and `count: 21`.

- [ ] **Step 7: Commit**

```bash
git add plugins/dev-workflows/skills/sp-* plugins/dev-workflows/references/vendored-superpowers-manifest.json plugins/dev-workflows/scripts/build_vendored_manifest.py
git commit -m "feat(dev-workflows): vendor the six review-carrying superpowers skills verbatim at b36e082 (ADR 0074)"
```

---

### Task 3: The rewrite pass — make the copies coherent as `sp-` skills

**Files:**
- Modify: `plugins/dev-workflows/skills/sp-brainstorming/SKILL.md`
- Modify: `plugins/dev-workflows/skills/sp-writing-plans/SKILL.md`
- Modify: `plugins/dev-workflows/skills/sp-executing-plans/SKILL.md`
- Modify: `plugins/dev-workflows/skills/sp-subagent-driven-development/SKILL.md`
- Modify: `plugins/dev-workflows/skills/sp-requesting-code-review/SKILL.md`
- Modify: `plugins/dev-workflows/skills/sp-receiving-code-review/SKILL.md`
- Modify: `PLAYBOOK.md` (one new grouped section, six rows)

**Interfaces:**
- Consumes: the six directories staged by Task 2.
- Produces: skill names `sp-brainstorming`, `sp-writing-plans`, `sp-executing-plans`, `sp-subagent-driven-development`, `sp-requesting-code-review`, `sp-receiving-code-review` — the exact strings every later task references.

Five classes of edit, over the six `SKILL.md` files. The three **reviewer prompt** files are Task 4's; do not touch them here.

- [ ] **Step 1: Rename each skill in frontmatter**

In each `sp-<name>/SKILL.md`, change `name: <name>` to `name: sp-<name>`. Six edits, one per file.

- [ ] **Step 2: Rewrite each `description` so it names the upstream skill it displaces**

Per ADR 0071 Decision 3, the seam is won on description quality. Each description states what the skill does *and* that it replaces the upstream twin. For `sp-writing-plans`:

```yaml
description: Use when you have a spec or requirements for a multi-step task, before touching code. Replaces superpowers:writing-plans in this marketplace — same method, with its plan-review step routed to this repo's scrutinize skill.
```

Apply the same shape to the other five, keeping each upstream description's own trigger wording ahead of the `Replaces …` sentence.

- [ ] **Step 3: Class 4 — the six qualified references *inside* the copy set go short-form**

These name skills that are themselves copies, so they must point at the copies:

| file | occurrences |
|---|---|
| `sp-writing-plans/SKILL.md` | `superpowers:executing-plans` ×2 → `sp-executing-plans`; `superpowers:subagent-driven-development` ×2 → `sp-subagent-driven-development` |
| `sp-executing-plans/SKILL.md` | `superpowers:subagent-driven-development` ×1 → `sp-subagent-driven-development` |
| `sp-subagent-driven-development/SKILL.md` | `superpowers:requesting-code-review` ×1 → `sp-requesting-code-review` |

No plugin prefix on any of them.

- [ ] **Step 4: Class 2 — the five relative cross-skill paths**

Four in `sp-subagent-driven-development/SKILL.md`, at lines 88, 117, 118 and 454:

`../requesting-code-review/code-reviewer.md` → `../sp-requesting-code-review/code-reviewer.md`

Lines 88, 117 and 118 are graphviz node labels; 454 is a live Markdown link. All four change, so the diagram and the link agree.

The fifth is `sp-executing-plans/SKILL.md:14`, `../using-superpowers/references/`. **This one names one of the eight NON-copied skills**, and it is the open question the map left as fog: nothing stages a `using-superpowers` directory into Antigravity's flat skills directory, so a relative path dangles there whatever Claude Code does with it. Replace the parenthetical with prose that carries no path:

```
(see the per-platform tool references in the superpowers plugin's `using-superpowers` skill)
```

This removes a link that cannot resolve on one of the two required harnesses, and keeps the sentence's meaning. Record the choice on the map's fog line when this task lands.

- [ ] **Step 5: Class 3 — the one plugin-relative path**

`sp-brainstorming/SKILL.md`, the line reading:

```
`skills/brainstorming/visual-companion.md`
```

becomes skill-relative, which is the form Antigravity resolves natively and which `CLAUDE.md` requires for a skill's own files:

```
`visual-companion.md`
```

- [ ] **Step 6: Verify the eight upstream references are untouched**

```bash
cd "$(git rev-parse --show-toplevel)/plugins/dev-workflows/skills"
grep -ro 'superpowers:[a-z-]*' sp-* | sed 's/.*://' | sort | uniq -c
```

Expected exactly:

```
      5 superpowers:finishing-a-development-branch
      3 superpowers:using-git-worktrees
```

Any other `superpowers:` name surviving means a class-4 edit was missed; a count below 5 or 3 means the broad-rewriter trap was sprung and must be reverted.

- [ ] **Step 7: Verify the names and the absence of plugin prefixes**

```bash
grep -h '^name:' plugins/dev-workflows/skills/sp-*/SKILL.md
grep -rn 'dev-workflows:sp-' plugins/dev-workflows/skills/sp-* ; echo "prefix hits above should be none"
```

Expected: six `name: sp-…` lines matching the Interfaces block; no prefix hits.

- [ ] **Step 8: Add the six PLAYBOOK rows**

`CLAUDE.md` requires the row in the same commit as the skill. Add one new grouped section to `PLAYBOOK.md` (ADR 0077 puts the copies in a group of their own rather than scattered through the arc):

```markdown
### Vendored superpowers skills (review routed to `scrutinize`)

| Skill | Reach for it when |
|---|---|
| `sp-brainstorming` | starting a design from a loose idea, and you want a written spec |
| `sp-writing-plans` | you have a spec and need a task-by-task implementation plan |
| `sp-executing-plans` | executing a plan inline, in this session, with checkpoints |
| `sp-subagent-driven-development` | executing a plan with a fresh subagent per task and review between tasks |
| `sp-requesting-code-review` | dispatching a code review of a diff |
| `sp-receiving-code-review` | you are the one who received findings and must act on them |
```

- [ ] **Step 9: Commit**

```bash
git add plugins/dev-workflows/skills/sp-* PLAYBOOK.md
git commit -m "feat(dev-workflows): rewrite the vendored copies as sp- skills (ADR 0071/0074/0075)"
```

---

### Task 4: Route the three reviewer prompts to `scrutinize`

**Files:**
- Modify: `plugins/dev-workflows/skills/sp-requesting-code-review/code-reviewer.md`
- Modify: `plugins/dev-workflows/skills/sp-subagent-driven-development/task-reviewer-prompt.md`
- Modify: `plugins/dev-workflows/skills/sp-subagent-driven-development/re-review-prompt.md`

**Interfaces:**
- Consumes: the skill names produced by Task 3.
- Produces: the three severity translation rows — `blocker → Critical (Must Fix)`, `major → Important (Should Fix)`, `nit → Minor` — asserted by name in Task 8's checker.

This is the whole point of the effort. The prompt file stays the **harness**: it supplies the per-touchpoint context, states the operating rules, and fixes the output contract the controller reads. Only the review *method* is delegated (ADR 0076). `scrutinize` itself is never edited.

The failure this prevents is silent: `scrutinize` reports `blocker/major/nit`, while the controller at `sp-subagent-driven-development/SKILL.md:356` gates on `Critical` or `Important`. Without translation it matches neither and the fix loop never fires, with no error.

- [ ] **Step 1: Insert the delegation block into `code-reviewer.md`**

Add, immediately after the prompt's context section and before its output contract:

```markdown
## How to review

Load the `scrutinize` skill the way your harness loads skills, and use it as the
review method for the diff described above. Do not restate or re-derive its
method here — it is frozen, and this file is only the harness around it.

`scrutinize` reports findings as **blocker / major / nit**. This prompt's output
contract uses different words, and the controller that reads your output gates on
them. Translate every finding on the way out:

| `scrutinize` says | report it as |
|---|---|
| `blocker` | `Critical (Must Fix)` |
| `major` | `Important (Should Fix)` |
| `nit` | `Minor` |

Report nothing in `scrutinize`'s vocabulary. A finding left as `blocker` reaches a
controller that is looking for `Critical`, matches nothing, and is silently dropped.
```

- [ ] **Step 2: Insert the same block into `task-reviewer-prompt.md`**

Identical text, added at the same position relative to that file's context and output-contract sections. Repeat it in full — an executor may read these tasks out of order, and a cross-reference would leave one prompt without the translation table.

- [ ] **Step 3: Insert the same block into `re-review-prompt.md`**

Identical text again, same position. Three files, three copies of the block.

- [ ] **Step 4: Verify all three carry the delegation and the three rows**

```bash
cd "$(git rev-parse --show-toplevel)/plugins/dev-workflows/skills"
for f in sp-requesting-code-review/code-reviewer.md \
         sp-subagent-driven-development/task-reviewer-prompt.md \
         sp-subagent-driven-development/re-review-prompt.md; do
  printf '%-58s scrutinize:%s blocker:%s major:%s nit:%s\n' "$f" \
    "$(grep -c 'scrutinize' "$f")" "$(grep -c 'Critical (Must Fix)' "$f")" \
    "$(grep -c 'Important (Should Fix)' "$f")" "$(grep -c 'Minor' "$f")"
done
```

Expected: every file reports a non-zero count in all four columns.

- [ ] **Step 5: Verify `scrutinize` was not touched**

```bash
git diff --name-only HEAD~4 -- plugins/dev-workflows/skills/scrutinize/ ; echo "should be empty"
```

Expected: no output. `scrutinize` is frozen; a diff here is a plan violation, not a refinement.

- [ ] **Step 6: Commit**

```bash
git add plugins/dev-workflows/skills/sp-requesting-code-review plugins/dev-workflows/skills/sp-subagent-driven-development
git commit -m "feat(dev-workflows): route the three reviewer prompts to scrutinize, translating severities (ADR 0076)"
```

---

### Task 5: The host SessionStart hook

**Files:**
- Modify: `plugins/dev-workflows/hooks/hooks.json`
- Create: `plugins/dev-workflows/hooks/prefer-vendored-superpowers.md`

**Interfaces:**
- Consumes: the six skill names from Task 3.
- Produces: nothing later tasks call; this is a leaf.

The upstream plugin stays fully enabled, and its own SessionStart hook injects text naming `superpowers:brainstorming` and `superpowers:systematic-debugging` by qualified name — an instruction carrying more authority than any skill description. `skillOverrides` cannot silence it (measured inert against plugin skills), so a counter-hook is the lever (ADR 0069/0070). `hooks.json` is currently `{"hooks": {}}`.

**Claude Code only.** Antigravity has no plugin system and no hooks, so neither the upstream hook nor this one exists there; displacement on that harness rests on descriptions alone. That is correct and costs nothing — see ADR 0070's scope note.

- [ ] **Step 1: Write the injected text**

Create `plugins/dev-workflows/hooks/prefer-vendored-superpowers.md`:

```markdown
This marketplace ships `sp-` copies of the superpowers skills that carry a review
step, so their reviews run this repo's `scrutinize` rather than the built-in
reviewer. When a session would reach for one of these, use the copy:

| instead of | use |
|---|---|
| `superpowers:brainstorming` | `sp-brainstorming` |
| `superpowers:writing-plans` | `sp-writing-plans` |
| `superpowers:executing-plans` | `sp-executing-plans` |
| `superpowers:subagent-driven-development` | `sp-subagent-driven-development` |
| `superpowers:requesting-code-review` | `sp-requesting-code-review` |
| `superpowers:receiving-code-review` | `sp-receiving-code-review` |

The other superpowers skills are unaffected and stay in use — including
`superpowers:using-git-worktrees` and `superpowers:finishing-a-development-branch`,
which the copies above still hand off to.
```

- [ ] **Step 2: Register the hook**

Replace the contents of `plugins/dev-workflows/hooks/hooks.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|clear|compact",
        "hooks": [
          {
            "type": "command",
            "command": "cat \"${CLAUDE_PLUGIN_ROOT}/hooks/prefer-vendored-superpowers.md\""
          }
        ]
      }
    ]
  }
}
```

The matcher mirrors the upstream hook's (`startup|clear|compact`) so the two fire on the same events and ours is not absent from a session theirs reaches.

- [ ] **Step 3: Verify the JSON parses and the file is reachable**

```bash
python -m json.tool plugins/dev-workflows/hooks/hooks.json
test -f plugins/dev-workflows/hooks/prefer-vendored-superpowers.md && echo OK
```

Expected: parsed JSON, then `OK`.

- [ ] **Step 4: Verify the hook text names all six copies**

```bash
grep -c '^| `superpowers:' plugins/dev-workflows/hooks/prefer-vendored-superpowers.md
```

Expected: `6`. A count below six means the hook's coverage is incomplete from that moment on.

- [ ] **Step 5: Commit**

```bash
git add plugins/dev-workflows/hooks/
git commit -m "feat(dev-workflows): ship the host SessionStart hook that re-points at the sp- copies (ADR 0070/0073)"
```

---

### Task 6: Repoint the arc into the copies, and demote `grill-then-plan`'s preflight

**Files:**
- Modify: `plugins/dev-workflows/skills/grill-then-plan/SKILL.md` (frontmatter, Step 0, and 3 body references)
- Modify: `plugins/dev-workflows/README.md` (3 references)
- Modify: `plugins/decision-map/skills/work-map/SKILL.md` (2 references)
- Modify: `README.md` (1 reference)

**Interfaces:**
- Consumes: the name `sp-writing-plans` from Task 3.
- Produces: no new interface; this task removes the last executable references to `superpowers:writing-plans` from shipped surfaces.

Two ADRs edit the same file, and two of ADR 0072's eleven references live *inside* the Step 0 that ADR 0080 rewrites. They cannot be separated into two tasks without conflicting edits, so they are one deliverable.

- [ ] **Step 1: Repoint all eleven references to `sp-writing-plans`**

Every occurrence of `superpowers:writing-plans` across the four files becomes `sp-writing-plans`, with **no plugin prefix**, prose lines in the two READMEs included. `work-map` loses its local convention of qualifying cross-plugin references; that cost is accepted and recorded in ADR 0072 Decision 2.

- [ ] **Step 2: Replace `grill-then-plan`'s Step 0 with a non-blocking warning**

Delete the existing six-step Step 0 entirely and put this in its place:

```markdown
## Step 0 — Preflight: one notice, then start

This skill hands off to `sp-writing-plans`, which ships in this same plugin, so that
handoff cannot fail and there is nothing to gate on.

What *can* be missing is the upstream **superpowers** plugin. The copies still hand
off to two skills that stay upstream — `finishing-a-development-branch` and
`using-git-worktrees` — so the plan you produce here is executed by a skill that
needs them.

Check whether the superpowers skills appear in your surfaced skill list or can be
loaded. If they cannot, say this once, then continue:

> superpowers is not installed. Your design spec and implementation plan will be
> written normally; executing that plan will reach `finishing-a-development-branch`
> and `using-git-worktrees`, which are not here. Install it with
> `/plugin install superpowers@claude-plugins-official` (Claude Code) or a
> superpowers skills port (Antigravity) before execution.

Do **not** wait for an answer, and do **not** stop. Then go to Step 1.
```

- [ ] **Step 3: Correct the frontmatter's dependency claim**

In the same file, `Requires the superpowers plugin.` becomes:

```
The plan it produces is executed by skills that require the superpowers plugin.
```

- [ ] **Step 4: Verify no shipped surface names the upstream skill**

```bash
cd "$(git rev-parse --show-toplevel)"
grep -rn 'superpowers:writing-plans' plugins/ README.md PLAYBOOK.md ; echo "hits above should be none"
grep -rc 'sp-writing-plans' plugins/dev-workflows/skills/grill-then-plan/SKILL.md \
  plugins/dev-workflows/README.md plugins/decision-map/skills/work-map/SKILL.md README.md
```

Expected: no hits for the first; the four counts summing to **11** for the second.

- [ ] **Step 5: Verify Step 0 no longer blocks**

```bash
grep -n 'STOP\|Wait for the user to confirm\|Do not start grilling' \
  plugins/dev-workflows/skills/grill-then-plan/SKILL.md ; echo "hits above should be none"
grep -c 'finishing-a-development-branch\|using-git-worktrees' \
  plugins/dev-workflows/skills/grill-then-plan/SKILL.md
```

Expected: no blocking hits; the second count at least `2`. Those two conditions are exactly ADR 0080's stated verification.

- [ ] **Step 6: Commit**

```bash
git add plugins/dev-workflows/skills/grill-then-plan/SKILL.md plugins/dev-workflows/README.md plugins/decision-map/skills/work-map/SKILL.md README.md
git commit -m "feat(dev-workflows): repoint the arc at sp-writing-plans; the preflight warns instead of blocking (ADR 0072/0080)"
```

---

### Task 7: The three user commands become plugin commands

**Files:**
- Create: `plugins/dev-workflows/commands/brainstorm.md`
- Create: `plugins/dev-workflows/commands/write-plan.md`
- Create: `plugins/dev-workflows/commands/execute-plan.md`
- Modify: `PLAYBOOK.md` (three rows)

**Interfaces:**
- Consumes: `sp-brainstorming`, `sp-writing-plans`, `sp-executing-plans` from Task 3.
- Produces: `/dev-workflows:brainstorm`, `/dev-workflows:write-plan`, `/dev-workflows:execute-plan`.

A typed command bypasses the host hook and the skill descriptions together, so the three personal commands in `~/.claude/commands/` lose every touchpoint in the skills they name. Bringing them into the plugin closes that and makes them shippable (ADR 0081).

- [ ] **Step 1: Write `brainstorm.md`**

```markdown
---
description: Start a design session from a loose idea and produce a written spec, with the spec-review step routed to this repo's scrutinize skill.
argument-hint: "<the idea — e.g. 'a queue for the nightly import'>"
---

Use the **`sp-brainstorming`** skill to run a design session on: $ARGUMENTS
```

- [ ] **Step 2: Write `write-plan.md`**

```markdown
---
description: Turn an approved spec into a task-by-task implementation plan, with the plan-review step routed to this repo's scrutinize skill.
argument-hint: "<path to the spec, or the feature name>"
---

Use the **`sp-writing-plans`** skill to write the implementation plan for: $ARGUMENTS
```

- [ ] **Step 3: Write `execute-plan.md`**

```markdown
---
description: Execute an implementation plan task-by-task in this session, with checkpoints, and the code-review step routed to this repo's scrutinize skill.
argument-hint: "<path to the plan file>"
---

Use the **`sp-executing-plans`** skill to execute: $ARGUMENTS
```

- [ ] **Step 4: Add the three PLAYBOOK rows**

Append to the grouped section Task 3 created:

```markdown
Typed entry points: `/dev-workflows:brainstorm`, `/dev-workflows:write-plan`,
`/dev-workflows:execute-plan` — the bare `/brainstorm`, `/write-plan` and
`/execute-plan` find them through autocomplete.
```

- [ ] **Step 5: Verify the commands name the copies and nothing upstream**

```bash
cd "$(git rev-parse --show-toplevel)/plugins/dev-workflows/commands"
grep -l 'superpowers:' brainstorm.md write-plan.md execute-plan.md ; echo "hits above should be none"
grep -h 'Use the' brainstorm.md write-plan.md execute-plan.md
```

Expected: no `superpowers:` hits; three lines naming `sp-brainstorming`, `sp-writing-plans`, `sp-executing-plans`.

- [ ] **Step 6: Delete the personal originals — this step is load-bearing**

A personal command is an exact name match; the plugin one is reached through autocomplete. Leaving the old files means the old files keep winning and the bypass survives while looking fixed.

```bash
rm -f ~/.claude/commands/brainstorm.md ~/.claude/commands/write-plan.md ~/.claude/commands/execute-plan.md
ls ~/.claude/commands/ 2>/dev/null | grep -E '^(brainstorm|write-plan|execute-plan)\.md$' ; echo "hits above should be none"
```

This runs on each machine that has them and cannot be shipped. Task 8's check reports it as a `FAIL` if it is skipped.

- [ ] **Step 7: Commit**

```bash
git add plugins/dev-workflows/commands PLAYBOOK.md
git commit -m "feat(dev-workflows): ship /brainstorm, /write-plan and /execute-plan as plugin commands (ADR 0081)"
```

---

### Task 8: `setup-check` — report the four manual steps the marketplace cannot ship

**Files:**
- Create: `plugins/dev-workflows/scripts/setup_check.py`
- Create: `plugins/dev-workflows/scripts/test_setup_check.py`
- Create: `plugins/dev-workflows/commands/setup-check.md`
- Modify: `PLAYBOOK.md` (one row)

**Interfaces:**
- Consumes: the six skill names (Task 3), the three command names (Task 7).
- Produces: `check_all(env) -> list[tuple[str, str, str]]` returning `(status, what, detail)` triples with `status` in `{"PASS", "WARN", "FAIL"}`; `main(argv) -> int` returning `0` when nothing failed and `1` otherwise.

Four steps arrive on no machine automatically, and every one fails silently: install superpowers; delete a personal `/brainstorm`; run `install-antigravity.py` and re-run it after updates; install a superpowers port. This is the only thing that emits a **positive** signal (ADR 0082).

- [ ] **Step 1: Write the failing test**

Create `plugins/dev-workflows/scripts/test_setup_check.py`:

```python
#!/usr/bin/env python3
"""Tests for setup_check.py. Run: python test_setup_check.py"""
import sys

from setup_check import check_all, main

CLEAN = {"superpowers_installed": True, "personal_commands": [],
         "antigravity_present": False, "antigravity_stale": False,
         "antigravity_port": False}


def test_all_clear_is_four_passes():
    rows = check_all(CLEAN)
    assert len(rows) == 4, rows
    assert all(r[0] == "PASS" for r in rows), rows


def test_missing_superpowers_fails():
    env = dict(CLEAN, superpowers_installed=False)
    row = [r for r in check_all(env) if r[1] == "superpowers plugin"][0]
    assert row[0] == "FAIL", row
    assert "finishing-a-development-branch" in row[2], row


def test_stray_personal_command_fails():
    env = dict(CLEAN, personal_commands=["brainstorm.md"])
    row = [r for r in check_all(env) if r[1] == "personal commands"][0]
    assert row[0] == "FAIL", row
    assert "brainstorm.md" in row[2], row


def test_stale_antigravity_staging_fails():
    env = dict(CLEAN, antigravity_present=True, antigravity_stale=True,
               antigravity_port=True)
    row = [r for r in check_all(env) if r[1] == "antigravity staging"][0]
    assert row[0] == "FAIL", row
    assert "re-run" in row[2], row


def test_absent_antigravity_warns_not_fails():
    env = dict(CLEAN, antigravity_present=False)
    rows = [r for r in check_all(env) if r[1].startswith("antigravity")]
    assert all(r[0] != "FAIL" for r in rows), rows


def test_main_exit_codes():
    assert main(["--json"]) in (0, 1)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("all passed")
    sys.exit(0)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd plugins/dev-workflows/scripts && python test_setup_check.py
```

Expected: `ModuleNotFoundError: No module named 'setup_check'`.

- [ ] **Step 3: Write the implementation**

Create `plugins/dev-workflows/scripts/setup_check.py`:

```python
#!/usr/bin/env python3
"""Report the prerequisites this marketplace cannot ship (ADR 0082).

Read-only. Prints one PASS / WARN / FAIL line per check with a fix for anything
missing, and exits 1 if any check FAILed.

  python setup_check.py [--json]
"""
import argparse
import json
import sys
from pathlib import Path

COMMANDS = ["brainstorm.md", "write-plan.md", "execute-plan.md"]
UPSTREAM_NEEDED = "finishing-a-development-branch and using-git-worktrees"


def probe():
    """Read the machine. Separated from check_all so the tests can inject state."""
    home = Path.home()
    plugins = home / ".claude" / "plugins" / "installed_plugins.json"
    installed = False
    try:
        installed = "superpowers" in plugins.read_text(encoding="utf-8")
    except OSError:
        installed = False
    ag = home / ".gemini" / "config" / "skills"
    return {
        "superpowers_installed": installed,
        "personal_commands": [c for c in COMMANDS
                              if (home / ".claude" / "commands" / c).is_file()],
        "antigravity_present": ag.is_dir(),
        "antigravity_stale": ag.is_dir() and not (ag / "sp-writing-plans").is_dir(),
        "antigravity_port": ag.is_dir() and (ag / "writing-plans").is_dir(),
    }


def check_all(env):
    rows = []

    if env["superpowers_installed"]:
        rows.append(("PASS", "superpowers plugin", "installed"))
    else:
        rows.append(("FAIL", "superpowers plugin",
                     f"not installed. The copies hand off to {UPSTREAM_NEEDED}. "
                     "Fix: /plugin install superpowers@claude-plugins-official"))

    stray = env["personal_commands"]
    if stray:
        rows.append(("FAIL", "personal commands",
                     f"{', '.join(stray)} still in ~/.claude/commands/ and will win "
                     "over the plugin commands. Fix: delete them (ADR 0081)"))
    else:
        rows.append(("PASS", "personal commands", "none shadowing the plugin commands"))

    if not env["antigravity_present"]:
        rows.append(("PASS", "antigravity staging", "antigravity not in use"))
        rows.append(("PASS", "antigravity port", "antigravity not in use"))
        return rows

    if env["antigravity_stale"]:
        rows.append(("FAIL", "antigravity staging",
                     "staged copies predate the sp- skills. Fix: re-run "
                     "install-antigravity.py (it copies, so it must be re-run on update)"))
    else:
        rows.append(("PASS", "antigravity staging", "sp- skills staged"))

    if env["antigravity_port"]:
        rows.append(("PASS", "antigravity port", "a superpowers port is staged"))
    else:
        rows.append(("WARN", "antigravity port",
                     f"no superpowers port staged; {UPSTREAM_NEEDED} will not resolve"))
    return rows


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    rows = check_all(probe())
    if args.json:
        print(json.dumps([{"status": s, "what": w, "detail": d} for s, w, d in rows],
                         indent=2))
    else:
        for status, what, detail in rows:
            print(f"{status:<5} {what:<22} {detail}")
    return 1 if any(s == "FAIL" for s, _, _ in rows) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd plugins/dev-workflows/scripts && python test_setup_check.py
```

Expected: six `ok test_…` lines, then `all passed`.

- [ ] **Step 5: Write the command wrapper**

Create `plugins/dev-workflows/commands/setup-check.md`:

```markdown
---
description: Check the prerequisites this marketplace cannot install for you — the superpowers plugin, stray personal commands that shadow the plugin ones, and the Antigravity staging. Run this on a new machine, or after updating the plugin.
---

Run the prerequisite checker and report the results, then help me fix anything that fails.

Execute:

```
python "${CLAUDE_PLUGIN_ROOT}/scripts/setup_check.py"
```

For each `FAIL` line, give me the exact command to fix it. A `WARN` is mine to judge.
If everything passes, say so plainly — a positive signal is the point of this check.
```

- [ ] **Step 6: Add the PLAYBOOK row**

Append to the grouped section:

```markdown
Setting up a new machine: `/dev-workflows:setup-check` reports the four steps that
do not arrive with the plugin.
```

- [ ] **Step 7: Commit**

```bash
git add plugins/dev-workflows/scripts/setup_check.py plugins/dev-workflows/scripts/test_setup_check.py plugins/dev-workflows/commands/setup-check.md PLAYBOOK.md
git commit -m "feat(dev-workflows): add setup-check for the four unshippable prerequisites (ADR 0082)"
```

---

### Task 9: The resync checker, its procedure, and the version bump

**Files:**
- Create: `plugins/dev-workflows/scripts/check_vendored_superpowers.py`
- Create: `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`
- Create: `plugins/dev-workflows/references/resync-superpowers.md`
- Modify: `plugins/dev-workflows/.claude-plugin/plugin.json` (0.37.0 → 0.38.0)
- Modify: `.claude-plugin/marketplace.json` (dev-workflows entry → 0.38.0; top-level 0.4.0 → 0.5.0)
- Modify: `CLAUDE.md` (repo layout)

**Interfaces:**
- Consumes: `vendored-superpowers-manifest.json` from Task 2; the translation rows from Task 4.
- Produces: exit `0` clean / `1` findings / `2` error, with `--strict` promoting findings to failure — the convention `check_doc_provenance.py` already sets in this directory.

The checker reports and changes nothing. A person makes the edits it names and re-runs it until it exits `0`. It also asserts the three upstream traps, none of which shows up as a broken link or a failed build (ADR 0075).

- [ ] **Step 1: Write the failing test**

Create `plugins/dev-workflows/scripts/test_check_vendored_superpowers.py`:

```python
#!/usr/bin/env python3
"""Tests for check_vendored_superpowers.py. Run: python test_check_vendored_superpowers.py"""
import sys

from check_vendored_superpowers import (check_translation_rows, check_upstream_traps,
                                        check_left_alone)

GOOD_PROMPT = """
| `blocker` | `Critical (Must Fix)` |
| `major` | `Important (Should Fix)` |
| `nit` | `Minor` |
Load the scrutinize skill.
"""


def test_translation_rows_present_is_clean():
    assert check_translation_rows({"code-reviewer.md": GOOD_PROMPT}) == []


def test_missing_translation_row_is_a_finding():
    text = GOOD_PROMPT.replace("| `nit` | `Minor` |", "")
    found = check_translation_rows({"code-reviewer.md": text})
    assert len(found) == 1 and "nit" in found[0], found


def test_qualified_ref_inside_brainstorming_is_a_trap():
    found = check_upstream_traps({"brainstorming/SKILL.md": "see superpowers:writing-plans"},
                                 using_superpowers="superpowers:brainstorming\nsuperpowers:systematic-debugging")
    assert any("brainstorming" in f for f in found), found


def test_third_name_in_using_superpowers_is_a_trap():
    found = check_upstream_traps({"brainstorming/SKILL.md": "no qualified refs here"},
                                 using_superpowers="superpowers:brainstorming\n"
                                                   "superpowers:systematic-debugging\n"
                                                   "superpowers:writing-plans")
    assert any("third" in f.lower() or "coverage" in f.lower() for f in found), found


def test_the_eight_upstream_refs_must_survive():
    text = "superpowers:finishing-a-development-branch " * 5 + \
           "superpowers:using-git-worktrees " * 3
    assert check_left_alone(text) == []
    assert check_left_alone(text.replace("using-git-worktrees", "sp-using-git-worktrees")) != []


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn(); print("ok", name)
    print("all passed")
    sys.exit(0)
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
cd plugins/dev-workflows/scripts && python test_check_vendored_superpowers.py
```

Expected: `ModuleNotFoundError: No module named 'check_vendored_superpowers'`.

- [ ] **Step 3: Write the implementation**

Create `plugins/dev-workflows/scripts/check_vendored_superpowers.py`:

```python
#!/usr/bin/env python3
"""Check the vendored sp-* skills against upstream and against their own rewrite rules.

Reports and changes nothing. A person makes the edits, then re-runs this.

  python check_vendored_superpowers.py [--upstream /path/to/superpowers] [--strict]

Exit: 0 clean, 1 findings, 2 error.
"""
import argparse
import json
import re
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
MANIFEST = PLUGIN_ROOT / "references" / "vendored-superpowers-manifest.json"
PROMPTS = ["sp-requesting-code-review/code-reviewer.md",
           "sp-subagent-driven-development/task-reviewer-prompt.md",
           "sp-subagent-driven-development/re-review-prompt.md"]
ROWS = [("blocker", "Critical (Must Fix)"), ("major", "Important (Should Fix)"),
        ("nit", "Minor")]
HOOK_NAMES = {"superpowers:brainstorming", "superpowers:systematic-debugging"}
LEFT_ALONE = {"superpowers:finishing-a-development-branch": 5,
              "superpowers:using-git-worktrees": 3}


def check_translation_rows(texts):
    """Every reviewer prompt must carry all three severity rows (ADR 0076)."""
    findings = []
    for name, text in sorted(texts.items()):
        for src, dst in ROWS:
            if src not in text or dst not in text:
                findings.append(f"{name}: missing translation row {src} -> {dst}")
    return findings


def check_upstream_traps(upstream_texts, using_superpowers):
    """The three invisible-failure traps (ADR 0075)."""
    findings = []
    for name, text in sorted(upstream_texts.items()):
        if name.startswith("brainstorming/") and re.search(r"superpowers:[a-z-]+", text):
            findings.append(
                f"trap 1: {name} now holds a qualified reference; the prose seam "
                "the host hook wins is now a forced one")
    names = set(re.findall(r"superpowers:[a-z-]+", using_superpowers))
    if names != HOOK_NAMES:
        findings.append(
            f"trap 2: using-superpowers names {sorted(names)}, expected "
            f"{sorted(HOOK_NAMES)} — a rename makes the hook a no-op, a third name "
            "means its coverage is incomplete")
    return findings


def check_left_alone(text):
    """The eight upstream references must survive the rewrite untouched."""
    findings = []
    for ref, expected in sorted(LEFT_ALONE.items()):
        actual = text.count(ref)
        if actual != expected:
            findings.append(f"expected {expected} x {ref}, found {actual}")
    return findings


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream", help="path to a checkout of obra/superpowers")
    ap.add_argument("--strict", action="store_true", help="exit 1 on findings")
    args = ap.parse_args(argv)

    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except OSError as exc:
        print(f"ERROR: cannot read manifest: {exc}", file=sys.stderr)
        return 2

    skills = PLUGIN_ROOT / "skills"
    findings = check_translation_rows(
        {p: (skills / p).read_text(encoding="utf-8") for p in PROMPTS})
    findings += check_left_alone(
        "".join((f).read_text(encoding="utf-8") for f in sorted(skills.rglob("sp-*/**/*.md"))))

    if args.upstream:
        up = Path(args.upstream) / "skills"
        findings += check_upstream_traps(
            {f"brainstorming/{p.name}": p.read_text(encoding="utf-8")
             for p in (up / "brainstorming").glob("*.md")},
            (up / "using-superpowers" / "SKILL.md").read_text(encoding="utf-8"))
        print(f"checked against upstream at {args.upstream} "
              f"(recorded sha {manifest['sha']})")

    for f in findings:
        print(f"FINDING: {f}")
    if not findings:
        print("clean")
        return 0
    return 1 if args.strict else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
```

- [ ] **Step 4: Run the test to verify it passes**

```bash
cd plugins/dev-workflows/scripts && python test_check_vendored_superpowers.py
```

Expected: five `ok test_…` lines, then `all passed`.

- [ ] **Step 5: Run the checker against the real tree**

```bash
python plugins/dev-workflows/scripts/check_vendored_superpowers.py
```

Expected: `clean`, exit 0. A finding here means Task 3 or Task 4 is incomplete — fix that task rather than the checker.

- [ ] **Step 6: Write the procedure document**

Create `plugins/dev-workflows/references/resync-superpowers.md`, with **no line numbers** in it — the program finds those:

```markdown
# Resyncing the vendored superpowers skills

The copies were taken from `obra/superpowers` at the sha recorded in
`references/vendored-superpowers-manifest.json`. Nothing notices when upstream moves;
this is on demand.

1. Clone or update a checkout of `obra/superpowers`.
2. Run `python scripts/check_vendored_superpowers.py --upstream <path>`.
3. Apply, by hand, every edit the checker names. The five classes are: the skill
   name and description; the qualified references *inside* the copy set, which go
   short-form `sp-`; the relative cross-skill paths; the one plugin-relative path,
   which becomes skill-relative; and the three reviewer prompts' delegation to
   `scrutinize` with its severity translation.
4. The eight references to `finishing-a-development-branch` and
   `using-git-worktrees` are **left alone**. A rewriter matching `superpowers:`
   broadly breaks all eight.
5. Re-run the checker until it exits `0`, then regenerate the manifest:
   `python scripts/build_vendored_manifest.py --sha <new sha>`.

The checker reports and changes nothing. The exit code is what says the resync is done.
```

- [ ] **Step 7: Bump the versions and update the repo layout**

In `plugins/dev-workflows/.claude-plugin/plugin.json` set `"version": "0.38.0"`. In `.claude-plugin/marketplace.json` set the `dev-workflows` entry's `"version"` to `"0.38.0"` and the top-level `"version"` to `"0.5.0"`. In `CLAUDE.md`, add to the `plugins/dev-workflows/` block of the layout tree:

```
  skills/sp-*/                    six vendored superpowers copies (ADR 0074) — review
                                  routed to scrutinize; resync via scripts/check_vendored_superpowers.py
  hooks/hooks.json                the host SessionStart hook (ADR 0070)
  LICENSE-superpowers             upstream MIT + the vendoring sha
```

- [ ] **Step 8: Verify the versions match**

```bash
python -c "
import json
p=json.load(open('plugins/dev-workflows/.claude-plugin/plugin.json'))['version']
m=json.load(open('.claude-plugin/marketplace.json'))
e=[x['version'] for x in m['plugins'] if x['name']=='dev-workflows'][0]
print('plugin', p, 'marketplace-entry', e, 'top-level', m['version'])
assert p == e == '0.38.0', (p, e)
print('in sync')
"
```

Expected: `in sync`.

- [ ] **Step 9: Commit**

```bash
git add plugins/dev-workflows/scripts/check_vendored_superpowers.py plugins/dev-workflows/scripts/test_check_vendored_superpowers.py plugins/dev-workflows/references/resync-superpowers.md plugins/dev-workflows/.claude-plugin/plugin.json .claude-plugin/marketplace.json CLAUDE.md
git commit -m "feat(dev-workflows): add the resync checker and procedure, bump to 0.38.0 (ADR 0075)"
```

---

## Self-review notes

Run per `writing-plans`' own checklist, against the map and ADRs 0069–0082.

**Spec coverage.** Every closed ticket maps to a task: `attribution` → 1; `copy-granularity`, `host-plugin` → 2; `skill-naming`, `convention-compliance`, `harness-skill-shadowing` → 3; `reviewer-invocation`, `review-acceptance-check`, `receiving-code-review-role` → 4; `coexistence`, `coexistence-mechanism`, `skilloverrides-live-check` → 5; `arc-rewiring`, `step0-preflight-fate`, `short-ref-resolution` → 6; `user-command-entry` → 7; `override-distribution` → 8; `resync-path`, `antigravity-install` → 9.

**Two things this plan does not do, deliberately.** `review-acceptance-check` (ADR 0079) established that the proof a routed review ran `scrutinize` is the dispatched subagent's own `Skill` record, which never persists — so it is a run, not a gate, and there is no task for it. And ADR 0082's setup check reports but does not enforce; nothing here makes anyone run it. Both are recorded as fog on the map rather than solved.

**One open item Task 3 Step 4 decides.** The map's fog carries `../using-superpowers/references/` as unresolved; this plan chooses to replace the path with prose rather than rewrite it, because no path resolves on both harnesses. If that choice is rejected in review, only that step changes.
