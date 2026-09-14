# handoff — the conversation travels: a vendored, modified copy with a cloud destination, reachable at any moment

- **Date:** 2026-09-14
- **Status:** Approved for planning (pending owner sign-off on this spec)
- **ADRs:** [0227](../../adr/workflow-daily-work-0227-handoff-is-vendored-from-mattpocock-skills-as-a-modified-copy.md),
  [0228](../../adr/workflow-daily-work-0228-the-cloud-destination-commits-and-pushes-the-handoff-into-the-repo.md),
  [0229](../../adr/workflow-daily-work-0229-handoff-is-reachable-at-any-moment-a-daily-footer-beside-save-not-a-hook-in-one-skill.md)
  (precedents: [0004](../../adr/0004-daily-router-hybrid-interaction.md) the Save footer,
  [0132](../../adr/workflow-daily-work-0132-document-what-shipped-runs-only-when-typed.md) manual invocation,
  [0158](../../adr/workflow-daily-work-0158-the-vendored-notice-travels-per-skill-when-the-skill-is-the-unit-shipped.md) the licence travels)
- **Plugin:** `dev-workflows` — `0.55.0 → 0.56.0` (plugin.json and marketplace.json together)
- **Glossary:** `CONTEXT.md` gains a *handoff terms* section with **Handoff document** and
  **Save state vs Handoff** (already written)
- **Already drafted on branch `handoff-skill`:** `skills/handoff/SKILL.md`, `commands/handoff.md`,
  the `LICENSE-mattpocock-skills` entry, the `generate_skills_tree.py` map + test, ADRs 0227–0229,
  CONTEXT.md. The plan verifies these against this spec rather than rewriting them.

```mermaid
flowchart TD
    U["user, at ANY moment of any conversation"] -->|"/dev-workflows:handoff [cloud] <what next>"| H["handoff skill (ADR 0227)<br/>compact the live thread: in flight · why · next ·<br/>unrecorded decisions · suggested skills · refs not copies · redact"]
    M["/daily menu footer (ADR 0229)<br/>💾 Save state anytime · 🚀 Hand off anytime"] -.reminds.-> U
    H --> D{"destination?"}
    D -->|default| T["OS temp dir — print the path"]
    D -->|cloud (ADR 0228)| R["docs/superpowers/handoffs/&lt;date&gt;-&lt;slug&gt;.md<br/>commit (after any uncommitted spec/plan/ADR) → push branch, never main"]
    R --> L["launch line: web Create session on the branch ·<br/>`claude --cloud \"Read &lt;path&gt; and continue from it.\"`<br/>+ 'plugins absent on cloud' + return path (teleport / fetch)"]
    L --> C["cloud session clones the branch, reads the file, works on claude/…"]
```

Read left to right: one command, usable anywhere, whose only branch is *where the file
goes*. The footer is a reminder, not a hook; no skill calls `handoff`.

## 1. The problem

On 2026-09-14 a plan was finished and the execution question offered two options, both
"run it here". The owner wanted it run in a Claude Code cloud session, and the crossing
had to be done by hand: commit the uncommitted docs, push a branch, work out the launch
command, warn that the cloud machine has none of this machine's plugins. Upstream
`mattpocock-skills:handoff` compacts a conversation for another agent but writes to temp,
which a cloud session cannot see, and says "call the Skill tool", which this repo's
harness-neutral rule forbids. The owner's framing: *"copy skill handoff มาเป็นของเรา
จะได้ใช้ตอนอื่นด้วย"* and *"ต้องทำได้ทุก step ที่คุยกับ AI ไม่ใช่แค่จังหวะไหนจังหวะเดียว
หรือกับสกิลเดียว"*.

## 2. Scope

- **In:** the vendored, modified `handoff` skill and its command wrapper; the licence
  entry; the generator's vendored map (+ test); the second `/daily` footer line and the
  sentence beside it; one PLAYBOOK row plus the PLAYBOOK's `/daily save` bullet gaining
  its twin; `plugin.json` / `marketplace.json` description + version; the regenerated
  `skills/` tree; ADRs 0227–0229 and the glossary (done).
- **Out (deliberate):** any edit to `sp-writing-plans`, `grill-then-plan` or any other
  skill to call `handoff` (ADR 0229 rejected B and C); `agents/openai.yaml` from
  upstream; upstream's `in-progress/claude-handoff` (background-agent variant); an eval
  (the skill is manual-invocation prose with no measurable gate — the same call as
  `wait-what`); a checker for mattpocock copies (only `wait-what` and `handoff` exist,
  and the licence file lists them).

## 3. The skill — `plugins/dev-workflows/skills/handoff/SKILL.md` (ADR 0227)

Frontmatter: `name: handoff`; a trigger-rich `description` naming the five situations
and the `cloud` word; `argument-hint: "[cloud] what will the next session be used for?"`;
`disable-model-invocation: true`. Body, in this order — the plan checks the draft
section by section:

1. **Portability, not compression** — the five-row trigger table (harness swap,
   directory/repo move, colleague, fork, **cloud session**); arguments tailor the
   document; the word `cloud` anywhere in the arguments selects the cloud destination.
2. **What goes in** — one small Mermaid diagram at the top (done → in flight → next);
   the live thread incl. decisions no artifact records yet; a *Suggested skills* section
   naming plugin-qualified skills "the way its harness loads skills"; references not
   copies; unverified beliefs marked *assumed, not verified*; secrets redacted.
3. **Where it goes — the destination decides** — the two-row table (default temp with
   the path printed; `cloud` into the repo, committed and pushed); the "point at the
   file, never paste the summary" rule with upstream's reason.
4. **The cloud destination, step by step** — the six steps of §4 below.
5. **It's working if** — six bullets, adapted from upstream's docs, plus "on `cloud`,
   the branch the document names is on GitHub and holds the file".

Wording rules: no "Skill tool"; no `${CLAUDE_PLUGIN_ROOT}` needed (the skill names no
bundled file); `claude --cloud` / `claude --teleport` are named because the destination
*is* Claude Code cloud, with the web route given first for a machine where `claude` is
not on the PATH.

## 4. The `cloud` destination (ADR 0228)

| step | what the skill does | what the user sees |
|---|---|---|
| 1 | `git status`; if on `main`, say "branch first" and stop until a branch exists; if the spec/plan/ADRs this session wrote are uncommitted, **offer** the commit (assisted git) | the list of uncommitted files and one yes/no |
| 2 | write `docs/superpowers/handoffs/<YYYY-MM-DD>-<slug>.md`, commit with an explicit path list, push the branch | the branch name and the file path |
| 3 | the *Suggested skills* section says *may be absent on cloud*; when a plan exists the document names its path and states the plan is self-contained; no promised review loop that needs a local-only skill | — |
| 4 | print the launch both ways: web (claude.ai/code → Create session → repo → branch) and `claude --cloud "Read <path> and continue from it."` | two lines to copy |
| 5 | name the return path (`claude --teleport <session>` or fetch + checkout the `claude/…` branch) and what to re-run locally before merge | one paragraph |
| 6 | the file stays after the work lands | — |

`<slug>` is a lowercase-kebab of the argument's subject (≤ 5 words), or of the current
branch name when no argument is given.

## 5. Reachable at any moment (ADR 0229)

- **`commands/handoff.md`** — thin wrapper, `description` + `argument-hint`, hands
  `$ARGUMENTS` to the skill; invocable as `/dev-workflows:handoff`.
- **`/daily` menu footer** gains one line under the Save line, in
  `plugins/dev-workflows/skills/daily/SKILL.md`:

  ```
  💾 Save state anytime: /daily save "<note>"
  🚀 Hand off anytime:   /dev-workflows:handoff [cloud] "<what next>"
  ```

  and the sentence after the menu block becomes: *The `Next time` line teaches the
  station shortcuts; the 💾 and 🚀 lines teach the two accelerators — save keeps your
  resume-point here, handoff sends the work away (ADR 0229) — all three graduate users
  from the menu. Save and Handoff are footers, not a sixth or seventh option: the circle
  stays five stations (ADR 0004).* The `description` frontmatter of `daily` is not
  changed (the footer is not a station and not a hand-off target).
- **PLAYBOOK.md** — one new row after the `wait-what` row (L94):

  ```
  | the work has to TRAVEL — another harness, another machine or repo, a colleague, a forked side task, or a Claude Code cloud session | `handoff` (`/dev-workflows:handoff [cloud] "<what next>"`) — compacts the live thread into one handoff document (refs, not copies; secrets redacted; suggested skills named); default lands in temp, `cloud` commits and pushes it into `docs/superpowers/handoffs/` because a cloud session clones from GitHub. Usable at any moment; the 🚀 footer of `/daily` reminds you. Vendored from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT) and MODIFIED (ADRs 0227–0229); manual invocation only |
  ```

  and the `/daily save` bullet (L153) gains one trailing sentence: *Its twin for when
  the work leaves this machine is `/dev-workflows:handoff` (ADR 0229).*

## 6. Licence, generator, manifests

- **`plugins/dev-workflows/LICENSE-mattpocock-skills`** — a second "Vendored files"
  block, *copied and MODIFIED*, pinned to mattpocock-skills 1.2.3 / upstream commit
  `6654f6b60cd9d5be8b54c6fafe44346dabeb3b76`, listing each modification; the wrapper
  sentence names both `commands/wait-what.md` and `commands/handoff.md` (drafted).
- **`scripts/generate_skills_tree.py`** — `VENDORED["handoff"] = MATTPOCOCK_LICENCE`
  so the generated `skills/handoff/` carries the licence (ADR 0158);
  `scripts/test_generate_skills_tree.py` asserts it (drafted).
- **`plugins/dev-workflows/.claude-plugin/plugin.json`** and the `dev-workflows` entry of
  **`.claude-plugin/marketplace.json`** — `0.55.0 → 0.56.0`; each `description` gains,
  before *"Growth:"*: *Handing work elsewhere: handoff (/dev-workflows:handoff — compacts
  the conversation into a handoff document for a new harness, another machine, a
  colleague or a Claude Code cloud session; `cloud` commits and pushes it because cloud
  clones from GitHub. Usable at any moment; a /daily footer beside Save reminds you.
  Vendored from mattpocock/skills under MIT and MODIFIED, see LICENSE-mattpocock-skills;
  disable-model-invocation is true, so it runs only when the user asks).*
- **`skills/`** regenerated with `python3 scripts/generate_skills_tree.py --repo .`,
  verified with `check_skills_tree.py`; `check_vendored_superpowers.py --strict` must
  still pass (nothing under `skills/sp-*` changes, but the run is the proof).

## 7. Self-review

- Placeholders: none — footer text, PLAYBOOK row, description sentence, slug rule and
  the six cloud steps are fixed above.
- Consistency: ADR 0227 = §3 + §6 licence; ADR 0228 = §4; ADR 0229 = §5 and the *Out*
  list (no skill calls handoff).
- Load-bearing claims verified 2026-09-14: the bundled CLI 2.1.270 has `--cloud` and
  `--teleport`; cloud sessions clone from the GitHub branch (claude-code-guide, docs
  cited there) and prior `origin/claude/…` branches exist on this remote; local
  marketplaces/user-scope plugins are not present on the cloud machine (same source);
  `wait-what` precedent — licence file, generator map, PLAYBOOK row, thin command;
  the `/daily` Save footer and ADR 0004's "footer, not a station".
- Assumed, not verified: that the `/daily` footer is where the owner will actually look
  for the reminder — the eval-free skill has no measurement of this; if it is not used,
  the PLAYBOOK row is the durable entry.
