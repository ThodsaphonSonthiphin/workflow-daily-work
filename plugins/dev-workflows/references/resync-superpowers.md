# Resyncing the vendored superpowers copies

```mermaid
graph TD
    A["resolve upstream sha (git ls-remote)"] --> B["re-copy all 21 files"]
    B --> C["re-apply the seven rewrite classes"]
    C --> D["run the checker (upstream mode)"]
    D --> E{"findings other than [hash]?"}
    E -->|"yes"| F["repair per the checker's fix: text"]
    F --> D
    E -->|"no - only [hash] is left"| G["re-emit the manifest"]
    G --> H["run the checker again, both modes"]
    H --> I{"clean, exit 0?"}
    I -->|"no"| F
    I -->|"yes"| J["commit copies + manifest together"]
```

This is the procedure a person follows to bring the 21 vendored copies under
`plugins/dev-workflows/skills/sp-*` back in line with a new upstream
`obra/superpowers` commit, using `check_vendored_superpowers.py` to drive the
loop and to prove when it is done. The loop is: resolve the sha upstream is
now at, re-copy the whole set, re-apply the rewrites that make the copies
ours, run the checker, repair whatever it names, re-emit the manifest, run the
checker once more to prove the result is clean, then commit copies and
manifest together. The sections below fill in each box.

**`[hash]` findings are the expected output of a correct re-copy, not
defects.** `check_hashes` compares each file against the hash recorded when it
was last vendored, so every file whose content upstream changed reports one —
and those findings clear only when you re-emit the manifest, which is what
records the new hashes. That is why re-emit comes *before* the final clean
run, not after it: waiting for a clean run first would wait forever. Read the
first checker pass for everything *except* `[hash]`, and never "repair" a
`[hash]` finding by reverting a copy you meant to update — that throws the
resync away and leaves the tree looking correct.

## The one network step

Everything starts with a single read-only check against GitHub:

```bash
git ls-remote https://github.com/obra/superpowers HEAD
```

Compare the sha it returns against `upstream.sha` in
`plugins/dev-workflows/references/vendored-superpowers.json` (at the time of
writing: `b36e0829c6d0140e93cfef2ca599b1b07d4a7797`, vendored
`2026-08-16`). If the two match, upstream has not moved since the last vendor
and there is nothing to resync — stop here.

If they differ, obtain `$UP` — a local checkout of upstream's plugin root, at
the sha `git ls-remote` just returned:

```bash
git clone https://github.com/obra/superpowers /tmp/superpowers-upstream
cd /tmp/superpowers-upstream && git checkout <sha-from-ls-remote>
export UP=/tmp/superpowers-upstream
```

## Why all 21 files are re-copied, never a subset

The manifest currently governs 21 files across the 6 wrapped skills
(`sp-brainstorming`, `sp-executing-plans`, `sp-receiving-code-review`,
`sp-requesting-code-review`, `sp-subagent-driven-development`,
`sp-writing-plans`), and every one of those 21 is recorded against the same
single `upstream.sha`.

That single sha is what makes the checker's per-file `state` (`verbatim` or
`edited`) meaningful: `check_upstream_files` compares "what we have" against
"what upstream has right now" (`check_hashes` only compares against the
manifest's own recorded `sha256` from vendor time — it never reads upstream),
and that live comparison only means something if every file was captured at
the same instant. Re-copy a subset at a new sha while leaving the rest at the
old one, and the manifest can no longer tell "we edited this" from "upstream
moved this out from under us" — the two explanations become indistinguishable
for every file that wasn't touched in this pass (ADR 0075). Re-copy the whole
set every time, even the files that turn out unchanged.

**Doing the copy is a manual step — no script under
`plugins/dev-workflows/scripts/` performs it.** Only the checker exists there;
nothing automates the file-by-file copy. The authoritative copy plan is the
manifest itself: for every entry in `copy_set.files`, copy
`$UP/skills/<upstream_path>` over `plugins/dev-workflows/skills/<path>`. Read
both columns straight out of the manifest (`path` is ours, `upstream_path` is
upstream's, both relative to their respective skills roots) rather than
guessing a mapping by hand.

## The seven rewrite classes

After re-copying, seven categories of hand-rewrite get re-applied on top of the
fresh upstream text. Look for these patterns; none of them is a file:line
location, because upstream can move where they land.

- **Class 1 — the two review-dispatch prompts.** Applies only to
  `sp-requesting-code-review/code-reviewer.md` and
  `sp-subagent-driven-development/task-reviewer-prompt.md`. Four of upstream's
  sections collapse into one `## Review method` block that delegates to
  `scrutinize-dispatch`; `code-reviewer.md`'s `## Example Output` section is
  deleted outright; and the `**Reviewer returns:**` line is reworded in both
  files. `re-review-prompt.md` is **excluded** from this class — it is frozen
  and stays byte-identical to upstream (see the manifest's `frozen` entry and
  its `why`); do not rewrite it.
- **Class 2 — cross-skill relative paths.** A relative path that points at a
  sibling vendored skill gets the `sp-` prefix inserted into the skill segment
  of the path. The one exception: `executing-plans`' path into
  `using-superpowers/references/` becomes a qualified `superpowers:` mention
  instead of a path rewrite, because `using-superpowers` itself is not
  vendored.
- **Class 3 — brainstorming's companion path.** Inside `sp-brainstorming`'s
  `SKILL.md`, the path to its visual companion document, originally written
  relative to the plugin root, becomes skill-relative — a bare relative
  filename inside the same skill directory.
- **Class 4 — handoffs naming one of the six.** Any qualified handoff
  (`superpowers:<name>`) that names one of the six vendored skills is rewritten
  to the short `sp-<name>` form. **Bare (unqualified) short names count too** —
  an unprefixed short name resolves to the un-vendored upstream skill with no
  error, and missing that was the Critical defect this checker's bare-name
  check exists to catch (ADR 0087).
- **Class 5 — frontmatter identity.** Each vendored `SKILL.md`'s frontmatter
  `name` and `description` are rewritten; the description names the upstream
  skill this copy displaces, so the displacement is visible on the surface,
  not just in a comment. (The manifest's `permit_list` documents each such
  description line as an intentional, inert bare-name hit.)
- **Class 6 — the two example transcripts.** Upstream's `Strengths:` clause is
  substituted with different wording in two example transcripts, because the
  dispatch engine's output format forbids a `Strengths:` section.
- **Class 7 — the review-model-selection statement.** Three files carry a
  reviewer model-selection statement that upstream does not have:

  - `sp-requesting-code-review/SKILL.md` — a whole `## Model Selection`
    section. Upstream's `requesting-code-review` has no model guidance at all.
  - `sp-requesting-code-review/code-reviewer.md` — a REQUIRED `model:` field
    in the dispatch template, plus a `[MODEL]` placeholder entry. It points at
    its own sibling `SKILL.md`; the section in turn points at
    `sp-subagent-driven-development`'s fuller treatment rather than
    duplicating it.
  - `sp-subagent-driven-development/SKILL.md` — one added paragraph under
    *Turn count beats token price*, tying a reviewer's turn count to the
    **assignment** rather than to the diff. Upstream has the surrounding
    section natively; this paragraph is ours.

  Don't confuse the two skills: upstream's `subagent-driven-development`
  already has its own native Model Selection section, so only the one
  paragraph there is a rewrite. The whole section in `requesting-code-review`
  is ours. All of it exists because an omitted model silently inherits the
  dispatching session's, usually the most expensive one available — the SDD
  path forced a model choice and the ad hoc path did not, though both follow
  the same principle.

  **This class is invisible to `check_upstream_files`'s "rewrite pass looks
  lost" finding** — that finding only fires when an `edited` file becomes
  byte-identical to upstream, and all three files still differ from upstream
  for other reasons (frontmatter, Class 1's collapsed sections), so a re-copy
  that drops this class produces no finding at all. Re-apply it by hand every
  time, and check all three files, not just the two in
  `sp-requesting-code-review`.

## The three upstream traps

Three upstream changes would leave no broken link and no failed build, so the
checker asserts them directly (`check_upstream_traps`, upstream mode only).
The `repair` text below is copied verbatim from that function — it is what the
checker itself prints when a trap fires.

**Trap 1 — brainstorming's handoff must stay bare.** Upstream's own
`brainstorming` skill directory (`upstream_traps.no_qualified_ref_dir`) must
keep handing off by bare, unqualified name, never a qualified
`superpowers:` reference. If upstream adds a qualified reference there, the
repair is:

> the host hook wins that seam because the reference is contestable prose. A
> qualified reference makes it forced, and the hook stops winning. Re-decide
> the hook

**Trap 2 — the host hook's named-skill set.** Our host hook mirrors upstream's
`using-superpowers/SKILL.md` (`upstream_traps.hook_source`) and expects it to
name exactly the skills in `upstream_traps.hook_named_skills` (currently
`brainstorming` and `systematic-debugging`). Two distinct failures both report
as trap 2:

- if that upstream file is gone, the repair is: `re-derive the hook against upstream's new entry point`
- if the file exists but the named-skill set changed, the repair is:

  > a rename makes our hook a silent no-op; a third name means the hook's
  > coverage is incomplete from this version on

**Trap 3 — the two dead document-reviewer prompts stay dead.**
`upstream_traps.dead_prompts` (`spec-document-reviewer-prompt`,
`plan-document-reviewer-prompt`) must stay unreferenced by any live upstream
file under `upstream_traps.dead_prompt_live_dirs` (`skills`, `hooks`,
`scripts`). If a live file references either one, the repair is:

> upstream is reviving the document-review system: two new review touchpoints,
> arriving unannounced. Decide whether they must route too

## Running the checker

Local mode runs six checks, in this order: `check_copy_set`, `check_hashes`,
`check_bare_names`, `check_qualified_refs`, `check_routing`, `check_frozen`.
Upstream mode runs those same six and then two more on top: `check_upstream_files`
and `check_upstream_traps` — eight checks total (`run_checks`).

```bash
python plugins/dev-workflows/scripts/check_vendored_superpowers.py --strict
python plugins/dev-workflows/scripts/check_vendored_superpowers.py --upstream-dir "$UP" --strict
```

`$UP` is a local checkout of upstream's **plugin root** — the directory that
holds its `skills/` — not the `skills/` directory itself.

Exit codes:

- **0** — no findings; or findings were reported but `--strict` was not
  passed.
- **1** — findings exist **and** `--strict` was passed.
- **2** — an operational error, not a finding: the manifest is missing,
  malformed, or missing a required key; `--root` or `--upstream-dir` is not a
  directory; or a declared file could not be read.

Exit 2 also covers manifest-shape failures, which matter because hand-editing
the manifest is a documented workflow (see the next section). `load_manifest`
validates the whole shape before any check runs — every required key, the type
of each top-level section, and the required keys inside `copy_set.files`,
`frozen` and `permit_list` entries — so a bad hand-edit fails cleanly at exit 2
naming the offending path, instead of the checker crashing partway through a
check.

That distinction is load-bearing, not cosmetic: **exit 1 is the `--strict`
findings code the merge gate keys on.** A shape error that escaped validation
would surface as an unhandled traceback and exit 1, making a fat-fingered
manifest indistinguishable from real drift — the gate would fail for the wrong
reason and the operator would go looking for a rewrite that was never lost.

## Re-emitting the manifest

`--emit-manifest` **prints** a freshly computed manifest to stdout — it never
writes anything itself. Redirect the output to a temp file, then move that file
into place:

```bash
python plugins/dev-workflows/scripts/check_vendored_superpowers.py \
  --emit-manifest --upstream-dir "$UP" > /tmp/manifest.new.json && \
  mv /tmp/manifest.new.json plugins/dev-workflows/references/vendored-superpowers.json
```

**Never redirect straight onto the manifest itself.** The shell truncates the
destination file before the program even starts, so every hand-written key —
`permit_list` reasons, `frozen` whys, the routing lists — reads back as absent
and is lost, silently, with no error from the program. (The program does
detect the resulting empty file on the *next* run and refuses with exit 2
rather than emitting from it — but that is the recovery check, not a reason to
skip the temp file. Emit to a temp file and move it every time.)

Any `permit_list` entry the emit marks `REVIEW:` is a new bare-name hit nobody
has judged yet — a person must decide why it is inert (or that it isn't) and
replace the placeholder before that manifest is committed.

`upstream.sha` is **re-read from `$UP` itself** (`git -C "$UP" rev-parse
HEAD`), never carried over from the manifest being replaced. The sha has to
describe the tree the new hashes were computed from; a carried-over value
would stamp fresh files with stale provenance and leave the stop condition in
[The one network step](#the-one-network-step) permanently unreachable, because
the recorded sha could never catch up to upstream's HEAD. If `$UP` is not a
git checkout the emit writes a `REVIEW:` placeholder there too — it will not
invent a sha.

**A refusal you may hit: `refusing to emit - sp-<name> has no counterpart
under upstream's skills/`.** Upstream renamed or deleted a skill we still
vendor. The emit stops rather than continue, because the copy set is built by
matching `sp-<name>` against upstream's `skills/<name>`, and a name that no
longer matches would simply be omitted — dropping a file we still ship out of
the manifest, and therefore out of every check, while the copy sits on disk
looking fine.

Resolve it deliberately, by which case it is:

- **Upstream renamed the skill.** Add the new name to `upstream.mapping` and
  re-run: `"mapping": {"sp-beta": "gamma"}` compares our `sp-beta/` against
  upstream's `skills/gamma/`. This is the usual case, and it is preferred over
  renaming our own copy — our copy's name is how every routing reference in
  this marketplace addresses it, and it should not change because upstream
  reorganised.
- **Upstream deleted the skill.** Decide whether we still want it. Drop our
  copy, or keep it and remove its entry from `copy_set.files` by hand. Keeping
  both the copy and the entry re-fires the `upstream/mapping` finding on every
  run, because `state` is recomputed against upstream each time.

Do not work around the refusal by deleting the entry and re-emitting: that is
the silent drop the refusal exists to prevent, done by hand.

## Two honest limits

State these plainly; neither is settled by a green checker run.

- **The checker asserts that the routing reference exists, not that a dispatch
  obeys it.** `check_routing` confirms `task-reviewer-prompt.md` still names
  the `scrutinize-dispatch` marker — it does not confirm anything ever
  dispatches through that file. `task-reviewer-prompt.md` **has** been used to
  dispatch reviews, but no run through it was ever instrumented to confirm the
  skill actually loaded; only `code-reviewer.md` has an instrumented run. Per
  ADR 0079 that is by design, not a gap — one instrumented run establishes the
  harness mechanism once, and per-file wiring (this checker) is what covers
  the rest. A review report having the right headings is not evidence the
  skill loaded: a capable reviewer holding the output contract produces the
  same headings without loading anything, which is why the signal is the
  tool_use record, not the report's content.
- **Whether the harness accepts a bare skill literal is still unmeasured.** The
  bare-name check (class 4, and `check_bare_names`) asserts that no
  *unintended* bare name exists in the copies. It says nothing about whether a
  bare handoff actually resolves the way a qualified one does when a harness
  dispatches it. A green run does not settle that question — it only means the
  copies match what the manifest currently expects.
