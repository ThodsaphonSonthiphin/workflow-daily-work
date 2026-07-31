---
name: career-growth
description: Quarterly career review that turns your real evidence and a live market survey into a defensible moat and a cert-driven growth plan. Builds an evidence-graded skill inventory (resume, repos, cross-repo git history, held certs/LinkedIn, optional Azure DevOps work items, short gap-fill interview), surveys Thailand + SEA + global-remote job markets with live-verified certificates and a triangulated 3-year outlook, proposes moat candidates that must pass four tests (rare, evidenced, paid, durable), lets the user pick, then plans certs and exam-objective-driven mini projects into a personal career git repo. Trigger when the user wants a career review, skill-gap analysis, certification roadmap or plan, job-market survey, "what should I learn next", a moat / unique edge / competitive advantage plan, or says "พัฒนาสกิลตัวเอง", "วางแผน cert", "ตลาดแรงงานต้องการอะไร", "สร้างจุดเด่น", "quarterly career review". Re-run it every quarter.
---

# career-growth

Five stations, full run every time, everything written to the user's **career
repo** (a git repo of their choosing — never this plugin, never the current
project). The user — not this skill — picks the career direction.

Print this pipeline diagram verbatim in your first response of a run:

```
CAREER-GROWTH — five stations, full run every time
──────────────────────────────────────────────────

  ① INVENTORY   evidence-graded skill inventory
  │    resume · repos · git history ·
  │    certs/LinkedIn · ADO (if available) ·
  │    gap-fill interview
  ▼
  ② MARKET      live survey — 3 rings
  │    Thailand · SEA · global remote
  │    certs live-verified · 3-yr outlook
  │    triangulated (≥3 signal types)
  ▼
  ③ GAP + MOAT  inventory × market
  │    candidates argued against 4 tests:
  │    rare · evidenced · paid · durable
  ▼
  ④ PRESENT ⛔  the user picks the moat
  │    (approval gate — nothing below
  │     runs without an explicit pick)
  ▼
  ⑤ PLAN        cert-driven guideline
       mini projects from exam objectives
       → career repo, assisted commit
```

## Non-negotiable evidence rules

1. **Never answer certificate questions from memory.** Every cert you mention as
   available must be verified at run time against the vendor's live
   retirement/lifecycle registry — see `references/market-sources.md` for where.
   If the registry is unreachable, withhold cert recommendations; never guess.
2. **Demand claims need a source.** Job-market statements carry the board name and
   posting count. Use only boards that serve automated fetch; on a 403 try the
   listed alternates before reporting a metric unavailable.
3. **No 3-year claim without triangulation** — at least three signal types from
   `references/market-sources.md` (vendor roadmaps, industry surveys, run-to-run
   posting deltas, AI-absorption assessment).
4. **Personal data never enters this plugin or the current project.** All outputs
   go to the career repo. Commits there are assisted — propose, show, let the user
   approve — never automatic.

## Step 0 — Preflight

1. Ask the user for (or confirm from a previous run): the **career repo path**,
   the **resume file path**, and the **list of repo roots** to scan. If the career
   repo doesn't exist or isn't a git repo, offer to create/`git init` it.
2. Read `growth-state.md` and the four artifacts from the career repo if present
   (see `references/growth-state-contract.md`). They pre-fill this run; they never
   skip a station.
3. Detect the optional ADO source: if the `ado-backlog` plugin's skills are
   available in this session, plan to use its assigned-work view in Station 1;
   otherwise tell the user the ADO source is skipped and continue.
4. Confirm the target market rings — default **Thailand + SEA + global remote**;
   the user may narrow or swap for this run.

## Station 1 — INVENTORY

Build the skill inventory from five sources (skip cleanly what the user lacks):

1. **Resume** — read the file; extract claimed skills, roles, domains.
2. **Repos + git history** — for each repo root: scan commit history (what was
   built, how recently, how often; languages, frameworks, infra). This is the
   corrective to resume claims.
3. **Held certificates + LinkedIn** — ask the user to paste/export; never scrape.
4. **ADO work items** (only if available per preflight) — list delivered work
   items as org-internal evidence.
5. **Gap-fill interview** — ask only what the evidence cannot show, one question
   at a time, from `references/interview-bank.md`, pre-filled from the previous
   `profile.md` so the user corrects rather than re-answers.

Write **`profile.md`** to the career repo: every entry lists its attesting
source(s) and an evidence grade — `verified` (artifact: repo/cert/work item),
`interview-attested`, or `unverified` (resume-only). Open the document with one
overview Mermaid diagram (skill map grouped by evidence grade).

## Station 2 — MARKET

Survey each confirmed ring using **only** the bounded source list in
`references/market-sources.md`, under the evidence rules above. For the chosen
skill areas gather: demand (posting counts per ring), the certificates employers
name (each live-verified before it may be mentioned), compensation signals where
boards expose them, and the 3-year outlook (triangulated, with the AI-absorption
assessment stated per skill).

Write **`market-report.md`** to the career repo: overview Mermaid diagram (rings ×
demand), a demand table per ring (skill · postings · source · date), the verified
cert list (code, registry status, `verified_on`, registry URL), and the triangulated
outlook with each signal cited. Do not delete the previous report's insights —
the file is overwritten, git history keeps the rounds.

## Station 3 — GAP + MOAT

Cross INVENTORY × MARKET:

- **Gap list** — market-demanded skills the user lacks or holds unverified.
- **Moat candidates** — skill *combinations* (never single hot skills), each with
  a four-test argument, one line per test:
  `rare` (evidence of scarcity in the rings) · `evidenced` (what public proof the
  user has or would gain) · `paid` (demand claims with sources) · `durable`
  (the triangulated 3-year case against AI/automation absorption — synthesise
  Station 2's per-skill AI-absorption assessments into one argument for *this
  combination*, not per skill).
- Anything failing a test may appear only as a labeled **supporting skill** —
  never as a moat candidate.

## Station 4 — PRESENT ⛔ approval gate

Present the candidates (a compact table: combination · the four test verdicts ·
strongest evidence) and ask the user to **pick one moat, or reject all**. On
reject: collect the objections as constraints and loop back to Station 3. Never
pick for the user; never proceed past this gate without an explicit pick.

On a pick, write **`moat.md`** to the career repo: the chosen combination, its
full four-test argument, the rejected candidates (one line each, why), and an
overview Mermaid decision diagram (chosen vs rejected).

## Station 5 — PLAN

For the chosen moat:

1. **Target certs** — select the certificates that evidence the moat, each
   already live-verified in Station 2. Fetch each exam's **study guide** and
   extract its objective domains.
2. **Mini projects** — design each project *backwards from exam objectives*: the
   project exists to build the knowledge the exam tests; passing the exam is the
   milestone. Size each to the user's stated study hours. Offer (never require)
   to publish each project to a public repo when its content allows — record
   `published_url` when taken.
3. **Non-cert milestones** — any moat component with no matching cert gets an
   explicit alternative milestone (a shipped artifact or delivered work), stated
   in the same pass/fail form.
4. Write **`growth-plan.md`** to the career repo (overview Mermaid diagram: certs
   + projects on a quarter timeline; then per-project sections: objective
   domains covered, milestone, size, publish decision) and update
   **`growth-state.md`** there per `references/growth-state-contract.md` —
   state file last, so a crashed run never records a completed `last_run`.
5. **Wrap up:** propose the career-repo commit (assisted — show the diff summary,
   let the user approve), and print the `next_review_due` date with a reminder
   that re-runs are user-initiated.

## Failure & degradation

| Situation | Behavior |
|---|---|
| A job board 403s | try the alternates in `references/market-sources.md`; only then report the metric unavailable |
| Vendor cert registry unreachable | withhold cert recommendations — never from memory; mark affected certs `retired-blocked` if previously targeted |
| `ado-backlog` absent | skip the ADO source with an explicit notice |
| No web access at all | INVENTORY still runs; MARKET and PLAN stop and say why — never fabricate |
| User rejects all candidates | loop to Station 3 with their objections as constraints |
