---
name: career-growth
description: "Quarterly career review that turns your real evidence and a live market survey into a defensible moat and a cert-driven growth plan. Builds an evidence-graded skill inventory (resume, repos, cross-repo git history, held certs/LinkedIn, optional Azure DevOps work items, short gap-fill interview), surveys Thailand + SEA + global-remote job markets with live-verified certificates and a triangulated 3-year outlook, proposes moat candidates that must pass four tests (rare, evidenced, paid, durable), lets the user pick, then plans certs and exam-objective-driven mini projects into a personal career git repo. Trigger when the user wants a career review, skill-gap analysis, certification roadmap or plan, job-market survey, \"what should I learn next\", a moat / unique edge / competitive advantage plan, or says \"พัฒนาสกิลตัวเอง\", \"วางแผน cert\", \"ตลาดแรงงานต้องการอะไร\", \"สร้างจุดเด่น\", \"quarterly career review\". Re-run it every quarter. Precedence: reach for this skill for the full periodic review; reach for `verify-then-advise` for a single verified recommendation, or to check whether one named product or credential is still current."
effort: max
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
  ② MARKET      two passes over the rings
  │  2a  job-family scan — profession-anchored,
  │      INVENTORY-BLIND, capped per ring
  │      ⛔ light stop: you confirm the set
  │  2b  deep-dive — family gates read,
  │      genuine counts, certs live-verified,
  │      3-yr outlook triangulated (≥3 signals)
  ▼
  ③ GAP + MOAT  inventory × market
  │    candidates may anchor on any deep-dived
  │    family; a declared destination is a
  │    mandatory candidate
  │    four tests: rare · evidenced ·
  │    paid · durable
  ▼
  ④ PRESENT ⛔  the user picks the moat
  │    (approval gate — nothing below
  │     runs without an explicit pick)
  ▼
  ⑤ PLAN        gate-driven lanes
       one lane per measured family gate;
       cert lane keeps readiness ÷ hours;
       every cert states its (a)/(b) case
       → career repo, assisted commit
```

## Non-negotiable evidence rules

All outside-world fact verification — certificate lifecycle, market demand,
claim grading — is delegated to **`verify-then-advise`**; Station 2 runs its
six-stage method rather than career-growth re-deriving a thinner copy of it.
Rules 1–2 below are consequences of running that method; rule 3 draws on
career-growth's own trend-signal taxonomy, with the sibling contributing
claim grading and the counter-signal hunt that stress-test it:

1. **Never answer certificate questions from memory** — every cert is
   live-verified against the vendor's registry before it may be named
   (`verify-then-advise` stage 2).
2. **Every market claim carries its source and a confidence grade** — one of
   `verify-then-advise`'s four grades (Verified-primary / Corroborated /
   Directional / Unverified); an ungraded claim may not appear in
   `market-report.md`.
3. **No 3-year claim without triangulation** — at least three signal types,
   drawn from this skill's own trend-signal taxonomy
   (`references/market-sources.md`); `verify-then-advise` contributes the
   claim-grading scale and the counter-signal hunt that stress-test the case.

Two rules have no sibling equivalent and stay entirely career-growth's own:

4. **Personal data never enters this plugin or the current project.** All outputs
   go to the career repo. Commits there are assisted — propose, show, let the user
   approve — never automatic.
5. **A verdict-bearing count is a board+genuine pair** — a posting count may
   support a verdict only when it carries both the raw board figure **and** a
   genuine figure from reading the returned titles (method in
   `references/market-sources.md`). A count labeled `unread` may inform but
   never decide. An `[External-research]` count — anything a research run
   reported rather than you measuring it — is a lead to re-measure, never a
   citable count. *Bearing a verdict means* feeding a four-test line, a cert
   or lane ranking, or the family shortlist; round 1's unreproducible counts
   reached all three.

## Step 0 — Preflight

1. **Career repo path** — if `$ARGUMENTS` is present and resolves to a usable
   directory, use it as the career repo path; only ask the user for it (or
   confirm from a previous run) when `$ARGUMENTS` is absent or doesn't resolve.
   Also ask for (or confirm) the **resume file path** and the **list of repo
   roots** to scan. If the career repo doesn't exist or isn't a git repo, offer
   to create/`git init` it.
2. Read `growth-state.md` and the four artifacts from the career repo if present
   (see `references/growth-state-contract.md`). They pre-fill this run; they never
   skip a station. A **v1** file is read, not rejected — migrate it per that
   reference's migration section before using its values.
3. **Profession** — ask for the **coarsest true label** for what the user does
   ("software engineering", "data", "finance"), not their specialisation. This
   is pass 2a's only anchor, and a narrow answer re-creates the bias the two
   passes exist to remove. It is **asked once, ever**: carried in
   `growth-state.md` and confirmed rather than re-asked on later rounds.
4. **Declared destination** (optional) — ask whether the user is already aiming
   at a named target: role + ring + stack (e.g. "Solution Architect, Bangkok,
   Microsoft Business Applications"). **Absent is a valid answer** and the
   normal one on a first round. A declared destination forces its job families
   into pass 2b's deep-dive set and becomes a mandatory candidate in Station 3
   — it is an input to validate, never a shortcut past the Station 4 gate
   (workflow-daily-work-0151).
5. Detect the optional ADO source: if the `ado-backlog` plugin's skills are
   available in this session, plan to use its assigned-work view in Station 1
   with `$env:AZDO_SHOW_DONE = "true"` — that view's default output is open
   work, and only its Done/Resolved table is delivered-work evidence;
   otherwise tell the user the ADO source is skipped and continue.
6. Confirm the target market rings — default **Thailand + SEA + global remote**;
   the user may narrow or swap for this run.

## Station 1 — INVENTORY

Build the skill inventory from five sources (skip cleanly what the user lacks):

1. **Resume** — read the file; extract claimed skills, roles, domains.
2. **Repos + git history** — for each repo root: scan commit history (what was
   built, how recently, how often; languages, frameworks, infra). This is the
   corrective to resume claims.
3. **Held certificates + LinkedIn** — ask the user to paste/export; never scrape.
4. **ADO work items** (only if available per preflight) — run the assigned-work
   view with `$env:AZDO_SHOW_DONE = "true"` and list only its **Done/Resolved**
   items as delivered, org-internal evidence. Open or in-progress items are not
   evidence of delivery and must not be graded `verified`.
5. **Gap-fill interview** — ask only what the evidence cannot show, one question
   at a time, from `references/interview-bank.md`, pre-filled from the previous
   `profile.md` so the user corrects rather than re-answers.

Write **`profile.md`** to the career repo: every entry lists its attesting
source(s) and an evidence grade — `verified` (artifact: repo/cert/work item),
`interview-attested`, or `unverified` (resume-only). Open the document with one
overview Mermaid diagram (skill map grouped by evidence grade).

## Station 2 — MARKET

Two passes over the confirmed rings. Pass 2a looks at the market with no
knowledge of the person; pass 2b spends the research budget only where the
user has agreed it should go (workflow-daily-work-0148, -0149).

Both passes run `verify-then-advise`'s six-stage method — load that skill via
your harness's mechanism. Two of its stages run before any source-list work
and are easy to miss if you assume you already know the method:

- **Inventory the moving parts** (stage 1) — before researching anything,
  list every external entity this round's advice will name (certs, vendors,
  products, market claims) as the verification queue.
- **Compute headline numbers in a script** (stage 6) — any number that
  carries the recommendation is computed from source values, once, in a
  script; never sum rounded per-item parts.

`references/market-sources.md` is the **starting** board and ring list — it
bounds where the survey begins, not where it must stop.

### Pass 2a — inventory-blind job-family scan

This pass **may not read Station 1's output**, and that prohibition is the
whole point: a survey scoped by the skills a person already holds can only
find more of what they already have. Round 1 of this skill scoped Station 2
that way and never counted the job family that later decided the plan.

1. Anchor on the **profession** captured in Step 0 — nothing narrower.
2. Enumerate the **job families** that exist in each ring under that
   profession: named, separately-laddered roles a person is hired *as*, not
   skill keywords. Cap at **8–10 job families per ring** so MARKET stays a
   single-session stage (ADR 0047). When the cap truncates, `market-report.md`
   names the dropped families — a silent truncation reads as "that was all
   there was".
3. Per family record: ring · the titles it appears under · a board count
   labeled `unread` · any entry requirement the list view already exposes.
   Pass 2a counts are **not** verdict-bearing (evidence rule 5), which is why
   an `unread` figure is acceptable here and nowhere downstream.
4. Note where a family has **no ladder in a ring** at all. Round 1's most
   useful structural finding was exactly this shape — a capability that
   existed only as a differentiator inside a conventional title, never as a
   job to apply for.

### The light stop — the user confirms the deep-dive set

Present the per-ring family table and propose the deep-dive set. A family
that is **inventory-adjacent** (it plainly matches Station 1's evidence) or
that belongs to a **declared destination** enters automatically; the user
adds or cuts the rest. This is a light stop, not the Station 4 gate — no moat
is chosen here, and the run continues as soon as the set is agreed.

### Pass 2b — the scoped deep-dive

For each family in the confirmed set:

1. **Read the requirement text** and extract its **family gates** — the
   measurable entry requirements (language level, named certificates, domain
   experience, lead delivery, clearance). Where a board exposes no
   requirement text, say so per family rather than leaving the field absent:
   a gate nobody measured must never become a lane in Station 5.
2. **Count genuinely** — read the returned titles and count only the postings
   actually about that family, recording the board count and the genuine
   count as a dated pair (evidence rule 5; method in
   `references/market-sources.md`).
3. **Certificates** — every cert a posting or partner program names is
   live-verified per `verify-then-advise` stage 2 before it may be mentioned,
   together with its published **preparation-hour** figure and whether a
   **practice assessment** exists. Record "not published" explicitly rather
   than leaving the field absent; Station 5's readiness check needs both.
4. **Counter-signal hunt** (stage 3) — a counter-signal is by definition not
   on a curated list; look for the contradicting view (independent analysts,
   adoption data, post-mortems) before advising a direction.
5. **Institutional-incentive read** (stage 5) — read the user's **employer's**
   partner-program, customer, or team requirements for the families in play,
   and surface any dated cliff running against them. This turns a personal
   wish into an employer-funded case, and it is also the evidence a
   certificate needs to earn a lane in Station 5.
6. **Compensation** where boards expose it (aggregator numbers grade
   `Directional`), and the **3-year outlook** triangulated across at least
   three signal types, with the AI-absorption assessment stated per family.

Write **`market-report.md`** to the career repo: overview Mermaid diagram
(rings × families), **the per-ring family table** from pass 2a with its
dropped-family note, the deep-dive set and who chose each entry, a
**family-gate table per deep-dived family**, the demand table (family · board
count · genuine count · source · date · **confidence grade**), the verified
cert list (code, registry status, `verified_on`, registry URL, published prep
hours or "not published", practice assessment yes/no), the counter-signals
found (or "looked, found none"), the institutional-incentive findings with any
dated cliff, and the triangulated outlook with each signal cited and graded.
Also record **what was not checked** — geographies skipped, sources that
blocked, families dropped by the cap, requirement text a board would not
expose, questions left open. The file is overwritten each run; git history in
the career repo keeps the prior rounds.

## Station 3 — GAP + MOAT

Cross INVENTORY × MARKET, weighted by Station 1's evidence grades: `verified`
skills count as strengths; `interview-attested` ones count as real strengths
whose public evidence is still missing, feeding the `evidenced` test as proof
still to be created rather than proof already held; `unverified` ones count as
gaps to close even when claimed.

- **Gap list** — market-demanded skills the user lacks or holds unverified,
  plus every **family gate** from pass 2b that the inventory does not clear.
- **Moat candidates** — skill *combinations* (never single hot skills). A
  candidate **may anchor on any deep-dived job family**, including one the
  inventory barely touches, as long as it states the gap plainly
  (workflow-daily-work-0149). Each candidate carries:
  - its **gap** — what the person is missing for this combination, drawn from
    the Gap list;
  - the gates it faces: each candidate **lists the family gates it must clear**
    (from pass 2b). Station 5 turns exactly this list into lanes, so a
    candidate whose gates were never measured cannot be planned;
  - a four-test argument, one line per test — `rare` (evidence of scarcity in
    the rings) · `evidenced` (what public proof the user has or would gain) ·
    `paid` (demand claims with sources and confidence grade; a `Directional`
    claim may support a direction but never be the sole basis for this verdict,
    and per evidence rule 5 an `unread` or external-only count may not support
    it at all) · `durable` (the triangulated 3-year case against AI/automation
    absorption — synthesise Station 2's per-family AI-absorption assessments
    into one argument for *this combination*, not per skill).
- **A declared destination is a mandatory candidate.** If Step 0 captured one,
  it appears in this station's candidate set whatever the evidence says, argued
  against the same four tests, alongside **at least one comparator** candidate
  so the user is choosing rather than confirming. A failing verdict is reported
  as a failing verdict; the skill never quietly substitutes a different target
  (workflow-daily-work-0151).
- Anything failing a test may appear only as a labeled **supporting skill** —
  never as a moat candidate. The one exception is a declared destination, which
  stays on the table *with its failures shown*, because the user declared it
  and only the user may withdraw it.

## Station 4 — PRESENT ⛔ approval gate

Present the candidates — a compact table: combination · anchoring job family ·
gap · the family gates to clear · the four test verdicts · strongest evidence —
and ask the user to **pick one moat, or reject all**. On reject: collect the
objections as constraints and loop back to Station 3. Never pick for the user;
never proceed past this gate without an explicit pick. The user may pick a
candidate that failed a test — that is their call to make with the verdict in
front of them, and the pick is recorded with the failure intact.

On a pick, write **`moat.md`** to the career repo: the chosen combination, its
gap, its full four-test argument, the rejected candidates (one line each, why),
and an overview Mermaid decision diagram (chosen vs rejected). It also
**records the chosen candidate's family gates** verbatim — that list is the
input Station 5 plans its lanes from, so a gate missing here is a lane missing
there.

## Station 5 — PLAN

The plan is **gate-driven**: it is built from the family gates recorded in
`moat.md`, not from a certificate list (workflow-daily-work-0152, which
supersedes ADR 0051's cert-driven framing in part). Round 2 of this skill
measured zero certificate mentions across every Ring 1 posting it read, while
the gate that actually blocked the destination — client-facing spoken English —
is closable by no certificate at all.

1. **Draw the lanes.** Create **one lane per measured family gate** from
   `moat.md`: language, certificate, published work, employer/partner
   arithmetic, domain evidence — whatever pass 2b actually measured. **A gate
   with no lane is a planning hole**: name it as one rather than dropping it.
   The converse holds too — a lane with no measured gate behind it does not
   belong in the plan.

2. **Baseline every lane before sizing it.** A lane needs a **measured baseline** before its milestone can be scheduled. This is the certificate
   lane's existing discipline, generalised: a published **practice assessment**
   outranks any estimate for a cert; a scored test or a recorded mock call is
   the baseline for a language lane; a public repo's absence is its own
   baseline for an evidence lane. Where no measurement exists, say so plainly
   and label the figure **unvalidated** — nothing downstream will re-check it.

3. **The certificate lane.** Identify the certs that evidence the moat, each
   already live-verified in Station 2. If the moat needs one Station 2 did not
   verify, verify it now via `verify-then-advise`'s registry-verification stage
   before naming it; if the registry is unreachable or the cert is retired, say
   so and use a non-cert milestone in this lane instead. Fetch each exam's
   **study guide** and extract its objective domains. Then:

   - **Every cert states its justification**, one of exactly two: **(a)** an
     institution or ring demonstrably reads it — a partner-program requirement,
     a posting that names it, an employer rule, each from Station 2's
     institutional-incentive read; or **(b)** it forces capability the
     readiness check graded **unknown**. A cert with neither **is dropped from
     the plan and recorded as dropped**, with its reason, so a later round
     revisits it instead of rediscovering it.
   - **Readiness check** — grade every objective domain against `profile.md`:
     **known** (a `verified` entry attests it) · **partial** · **unknown** (no
     entry, or only `unverified` ones). Estimate **remaining hours** from the
     partial + unknown share weighted by each domain's published exam
     weighting — never from the exam's total nominal prep time, which assumes a
     stranger. Record the grade per domain, not just the total: the domain
     table is what makes a wrong estimate visible next round.
   - **Rank, and show the trade** — order candidate certs by **moat-fit ÷ remaining hours**, not by moat-fit alone. A cert the user has largely
     already earned through delivered work can outrank a closer-fitting one —
     most sharply when the user holds **no live credential**, or when a dated
     employer cliff lands sooner than the closer cert could. Where the two
     orderings disagree, present both with the cost of each in hours and let
     the user choose; never silently resolve it.

4. **Mini projects** — for a certificate lane, design each project *backwards from exam objectives*: the project exists to build the knowledge the exam
   tests, and passing the exam is the milestone. For every other lane, design
   it backwards from that gate's own measurement, and clearing the gate is the
   milestone. Aim each project at what the baseline graded **unknown** — hours
   spent on already-cleared ground buy nothing. Size each to the user's stated
   study hours; if study hours were never captured (the interview's
   *Constraints & preferences* section can be skipped), ask for them now before
   sizing. Offer (never require) to publish each project to a public repo when
   its content allows — record `published_url` when taken.

5. **Zero-study-hour milestones list first — across every lane.** Publishing
   existing work, asking an employer a question, confirming a credential's
   expiry date, booking a language assessment: each buys gate progress without
   spending the scarcest resource, so each is listed ahead of anything costing
   study hours, whichever lane it sits in.

6. Write **`growth-plan.md`** to the career repo: an overview Mermaid diagram
   (lanes × milestones on a quarter timeline); the **lane table** (gate · lane · milestone · baseline (measured / unvalidated) · study hours); for the
   certificate lane, its readiness table per candidate cert with per-domain
   grades, the remaining-hour figure marked validated or unvalidated, the
   ranking with the trade shown, and each cert's (a)/(b) justification; the
   certs dropped and why; then per-project sections (what it builds, the gate
   or objective domains covered, milestone, size, publish decision).

7. **Wrap up:** propose the career-repo commit (assisted — show the diff
   summary, let the user approve). On approval, write/finalise
   **`growth-state.md`**'s `last_run` (and the round's other fields) per
   `references/growth-state-contract.md`, **then** commit all five artifacts
   together — `profile.md`, `market-report.md`, `moat.md`, `growth-plan.md`,
   and `growth-state.md` — so the file asserting a committed round exists is
   itself inside that commit. A committed round is what `last_run` means, so a
   crashed run and a declined commit both leave it unchanged: on decline, do
   not write `growth-state.md` at all. Then print the `next_review_due` date
   with a reminder that re-runs are user-initiated. If the user declines the
   commit, say plainly that the run is not recorded as complete and the next
   run's posting-trend-delta signal will have no prior round to diff against.

## Failure & degradation

| Situation | Behavior |
|---|---|
| A job board 403s | try the alternates in `references/market-sources.md`; only then report the metric unavailable |
| **Pass 2a returns no families for a ring** | report the ring as unsurveyed and continue with the rings that answered — never fall back to inventory keywords, which is the bias the pass exists to remove |
| **A board exposes no requirement text** | record "gates not exposed" for that family; the family may still be deep-dived on counts, but an unmeasured gate must not become a Station 5 lane |
| Vendor cert registry unreachable | withhold cert recommendations — never from memory; keep a previously-targeted cert's existing status and leave its stale `verified_on` in place, noting the verification could not be refreshed. `retired-blocked` is only for a confirmed retirement listing |
| No published prep hours and no practice assessment for a cert | rank it anyway, on the estimate, but label the figure **unvalidated** in `growth-plan.md` and name the missing measurement as a risk — never present an unmeasured estimate as a schedule |
| A gate has no measurable baseline | keep the lane, label its size **unvalidated**, and list the measurement itself as that lane's first (usually zero-study-hour) milestone |
| **A v1 `growth-state.md` is found** | migrate it per `references/growth-state-contract.md` and say what was carried and what defaulted — never rewrite it silently, and never reject the round for it |
| `ado-backlog` absent | skip the ADO source with an explicit notice |
| No web access at all | the run stops after INVENTORY — Stations 2 through 5 do not run, because without market evidence the `paid` and `durable` tests cannot be argued; say why, never fabricate |
| User rejects all candidates | loop to Station 3 with their objections as constraints |

## Relationship to neighbouring skills

- **`verify-then-advise`** — owns retirement-registry lifecycle verification,
  the counter-signal hunt, primary-artifact counting, the institutional-
  incentive read, and the four-grade claim scale. Station 2 runs its
  six-stage method in full; career-growth owns the person-side inventory,
  the trend-signal taxonomy, and the decision structure (the four-test moat
  argument, the approval gate, the readiness-ranked cert plan).
  Precedence: reach for career-growth for the full periodic review; reach for
  `verify-then-advise` for a single verified recommendation, or to check
  whether one named product or credential is still current.
- **`study-design-verify`** — same evidence-grounded stance, aimed at the
  user's own system (code, schemas, live data) rather than the outside world.
  Station 1's repo/git-history/ADO evidence is the closest overlap; if the
  question turns into "how should this system actually work" rather than
  "what does the person and the market look like", hand off there.
