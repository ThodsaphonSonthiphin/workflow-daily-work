# PLAYBOOK — the daily-work arc

One page: **what to reach for, when.** The only command you must remember is
**`/daily`** (installed as `/dev-workflows:daily` — typing `/daily` finds it via
autocomplete). Everything else is reachable from there or from this page.

## The daily circle

```mermaid
flowchart TD
    DAILY(["⌨ /daily"]) -.start.-> START
    DAILY -.work.-> WORK
    DAILY -.file.-> FILE
    DAILY -.report.-> REPORT
    DAILY -.wrap.-> WRAP

    subgraph CIRCLE [" the daily circle "]
        START["☀️ 1. START<br/><b>ado-backlog:my-work</b><br/>what's on my plate"]
        WORK["🔧 2. WORKING<br/><b>situational toolbox</b><br/>(see router below)"]
        FILE["📋 3. FILING<br/><b>findings-to-ado-backlog</b> (batch)<br/><b>ado-create-work-items</b> (direct)"]
        REPORT["📣 4. REPORTING<br/><b>management-talk</b>"]
        WRAP["🌙 5. WRAP-UP<br/><b>invoice-generator</b><br/>Tribletext from commits"]

        START --> WORK
        WORK --> FILE
        FILE --> REPORT
        REPORT --> WRAP
        WRAP -- next day --> START
    end
```

| Station | Say | Skill that runs |
|---|---|---|
| 1. START | `/daily start` | `ado-backlog:my-work` — ADO task hub (GitHub view on request) |
| 2. WORKING | `/daily work` | the situational router below |
| 3. FILING | `/daily file` | `findings-to-ado-backlog` (batch) or `ado-create-work-items` (direct) — GitHub twins on request |
| 4. REPORTING | `/daily report` | `management-talk` |
| 5. WRAP-UP | `/daily wrap` | `invoice-generator` — run it every day; it builds from commits |

## WORKING — the situational router

```mermaid
flowchart TD
    WORK{"🔧 WORKING<br/>what's happening?"}

    WORK -- designing something --> GTP["grill-then-plan"]
    WORK -- advising on a system --> SDV["study-design-verify"]
    WORK -- auditing names/mappings --> NA["naming-audit /<br/>fit-gap-analysis"]
    WORK -- explaining a problem --> PD["problem-description"]
    WORK -- why does this exist? --> TT["ticket-trace"]
    WORK -- second opinion --> SC["scrutinize /<br/>dual-verifier"]
    WORK -- new legacy codebase --> DTL["drive-to-legacy"]
    WORK -- new CRM / D365 org --> CA["crm-archaeology"]

    WORK -- 💥 something broke --> DM["debug-mantra<br/>(diagnose)"]
    DM --> Q{"fix involves a<br/>design choice?"}
    Q -- no, mechanical --> FIX["fix it"]
    Q -- yes --> GTP2["grill-then-plan<br/>(capture decision first)"]
    GTP2 --> FIX
    FIX --> PM["post-mortem"]
    PM --> MT["management-talk"]
    WORK -- need a test-case suite --> GTC["generating-test-cases"]
    PM -. regression case .-> GTC
    GTC -. fails/TBD .-> FILEHINT["findings-to-ado-backlog"]
```

| When… | Reach for |
|---|---|
| designing something new | `grill-then-plan` |
| something broke | `debug-mantra`, then the debug chain below |
| advising on how a system should work | `study-design-verify` |
| auditing names / labels / mappings | `naming-audit` / `fit-gap-analysis` |
| explaining a complex problem | `problem-description` |
| "why does this code/ticket exist?" | `ticket-trace` |
| second opinion on a plan / PR / change | `scrutinize` / `dual-verifier` |
| unfamiliar legacy codebase | `drive-to-legacy` |
| unfamiliar Dynamics 365 / Dataverse org | `crm-archaeology` |
| need a repeatable test-case suite (feature / change / fixed bug) | `generating-test-cases` |

### The debug chain (ADRs 0003 + 0011)

```
something broke → debug-mantra (diagnose)
   ├─ fix is mechanical/obvious   → fix → post-mortem → generating-test-cases → management-talk
   └─ fix involves a design choice → grill-then-plan (document the decision FIRST)
                                     → fix → post-mortem → generating-test-cases → management-talk
```

The chain flows into REPORTING by itself: post-mortem's output is what
management-talk reshapes for the channel.

**It runs both ways.** If you enter `grill-then-plan` directly to design a fix
for something that misbehaves but the cause isn't verified yet, it hands off to
`debug-mantra` first, then grills against the confirmed cause (ADR 0011). One
invariant guards both entry points: **never plan a fix on an unverified cause.**

## /daily usage

- **`/daily`** — shows the 5-station menu. Pick a number.
- **`/daily <station>`** — jumps straight there: `start` · `work` · `file` ·
  `report` · `wrap` (synonyms accepted: `morning`, `stuck`, `findings`, `status`,
  `done`). An unrecognized word falls back to the menu — never an error.

## Maintenance rule

**Every new skill adds one row to this file, in the same commit.** A skill missing
from the playbook is invisible (see the convention in [CLAUDE.md](CLAUDE.md), and
ADR [0001](docs/adr/0001-playbook-plus-daily-router.md)).
