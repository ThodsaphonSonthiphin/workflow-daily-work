---
title: Distribution - what makes sure a colleague has superpowers installed before the copies need it?
type: grilling
mode: HITL
status: closed
assignee: override-dist-grill-0602
blocked_by: [coexistence-mechanism]
gist: Re-scoped off the void skillOverrides premise: four manual steps cannot be shipped, and a read-only dev-workflows setup-check reports all four - the ado-backlog/github-backlog pattern.
---

<!-- decision-map:graph:start -->
```mermaid
graph TD
    ME["override-distribution (this ticket)"]
    P0["coexistence-mechanism"] --> ME
    ME --> C0["antigravity-install"]
```
<!-- decision-map:graph:end -->

## Question

Coexistence chose skillOverrides: off on the six upstream review skills - but a plugin cannot ship a settings key. Overrides live in settings.json, not in the marketplace. So how does a colleague who installs this marketplace end up with the six originals switched off: a committed project .claude/settings.json in every consuming repo, a documented manual step in the README, an install script, or something else? And what is the Antigravity equivalent, given the destination requires the copies to run there too? Without a reliable answer, coexistence degrades to 'change nothing' on every machine except this one, silently.

## Comment

## Premise note (2026-08-14): "the six skillOverrides entries" no longer exist

This ticket's title and question assume the mechanism ADR 0069 chose: six
`skillOverrides` entries that a colleague's machine needs. `skilloverrides-live-check`
has since observed that `skillOverrides` has no effect on any plugin-provided skill
on Claude Code 2.1.232, so there are no six entries to distribute.

Do not answer this ticket as written. It is now blocked on
`coexistence-mechanism`, and what needs distributing depends entirely on which way
that goes:

- **whole plugin off** - one `enabledPlugins` entry per machine, plus whatever the
  Antigravity equivalent is. Distribution gets *simpler*, and it is still a
  settings key that a plugin cannot ship, so this ticket's real question survives.
- **plugin fully on** - nothing to distribute at all. This ticket closes as
  not-applicable, and its risk moves into the trigger-competition question on
  `skill-naming`.

Re-scope the title and question when the mechanism is decided.


## Comment

## This ticket's premise no longer holds (2026-08-14, noted from `skill-naming`)

Not a resolution — a scope note left by a session working a different ticket.

The title asks *"how do the six `skillOverrides` entries reach a colleague's machine?"*
There are no `skillOverrides` entries to distribute. `skilloverrides-live-check`
measured on Claude Code **2.1.232** that `skillOverrides` cannot reach a **plugin**
skill by either key form, and [ADR 0070](../../../adr/0070-host-sessionstart-hook-repoints-the-one-skill-the-upstream-hook-names.md)
replaced that lever with a host SessionStart hook shipped by this marketplace. ADR 0070
states the consequence directly: *"no settings key is required on a colleague's
machine."*

So whoever takes this ticket should expect to **re-scope the question before answering
it**, not answer it as written. The distribution question that survives is a different
one, and it is narrower:

- the host hook ships **inside** this marketplace, so it arrives with the plugin — that
  half needs no distribution mechanism at all;
- what does *not* ship inside any plugin is anything living in a colleague's own
  `~/.claude/`. That is now charted as its own ticket, `user-command-entry`, for the
  three commands (`/brainstorm`, `/write-plan`, `/execute-plan`) that name a
  `superpowers:` skill directly and bypass both the hook and the descriptions.

Two consequences for the frontier, which the taker should confirm rather than assume:

1. `antigravity-install` is blocked on this ticket. If the answer here collapses to
   "nothing to distribute", that blocker releases cheaply.
2. This ticket may be closeable as out-of-scope rather than answered. That is the
   taker's call with the user, not this session's.

Also worth checking against the map's fog list: the line about Claude Code's `/skills`
picker showing an override as applied while enforcement ignores it was written when
`skillOverrides` was still the mechanism. With that lever abandoned, that fog line may
be stale too.


## Comment

## Note — this ticket's premise may no longer exist (not a resolution)

Raised while resolving `host-plugin`; recorded so the next session checks the premise
before grilling the question.

This ticket asks how **six `skillOverrides` entries** reach a colleague's machine. There
are no such entries any more:

- `skilloverrides-live-check` measured that `skillOverrides` cannot reach a **plugin**
  skill by either key form on Claude Code 2.1.232.
- [ADR 0070](../../../adr/0070-host-sessionstart-hook-repoints-the-one-skill-the-upstream-hook-names.md)
  replaced that lever with a host SessionStart hook and states outright that **"no
  settings key is required on a colleague's machine."**
- [ADR 0073](../../../adr/0073-vendored-review-skills-live-inside-dev-workflows-not-a-plugin-of-their-own.md)
  puts that hook in `plugins/dev-workflows/hooks/hooks.json`, so it ships with the plugin
  and needs no per-machine distribution step at all.

So the next session should decide between two outcomes rather than answering as written:

1. **Close it as void / out of scope** — nothing is distributed, because nothing is
   configured per machine.
2. **Re-scope it** to the distribution question that *does* survive: a colleague still
   has to have the upstream `superpowers` plugin installed for the eight non-copied
   skills the copies hand off to, and the host hook only steers if this marketplace is
   installed. That is a prerequisites question, not a `skillOverrides` question.

Either way it currently **blocks `antigravity-install`**, and that edge is probably
spurious now — `host-plugin` resolving already made the installer side automatic
(discovery iterates `PLUGIN_ROOT/skills`), so `antigravity-install`'s remaining question
is only whether the copies introduce a `${CLAUDE_PLUGIN_ROOT}` shape outside
`rewrite_plugin_root()`'s three handles.


## Comment

## Constraint from `short-ref-resolution` — a missing copy fails SILENTLY (2026-08-15)

Not a resolution of this ticket. One thing a distribution answer now has to survive.

Measured on Claude Code 2.1.232, 2/2 runs: when a `sp-` copy is **absent** from a machine,
a short-form reference to it does **not** error. The model launches the nearest live twin
instead — `sp-writing-plans` reached **`superpowers:writing-plans`**, with no error, no
warning, and a normal-looking completion. A bare name with *no* twin is refused cleanly,
so the substitution happens only where a twin exists, which the `sp-` convention
guarantees for all six copies.

This ticket owns how the six `skillOverrides` entries reach a colleague's machine. The
finding widens what "reach" has to mean: **a colleague whose install is partial, stale or
mis-scoped does not get an error — they get the upstream review skill the whole effort
exists to displace, and no signal that it happened.** A distribution mechanism that can
half-land is therefore not merely inconvenient; it reproduces the exact silent failure
[ADR 0069](../../../adr/0069-the-upstream-plugin-stays-enabled-its-review-skills-go-off-per-skill.md)'s
option C was rejected for, by a different route.

Worth answering here, or splitting into its own ticket: **is there anything that makes a
missing copy observable?** The three candidates seen so far are a startup assertion in the
copies' own text, a check in the ADR 0075 resync checker, and accepting the risk on the
grounds that the copies ship inside `dev-workflows` and so cannot go missing separately.
The third is the cheapest and is probably right for Claude Code — but it is exactly the
kind of claim that has been wrong twice on this map, and it does not obviously hold for
the Antigravity install, which stages skill directories one at a time.

Evidence and reproduction:
[`short-ref-resolution`](short-ref-resolution.md).

<!-- decision-map:resolution:start -->
## Resolution

Re-scoped off the void skillOverrides premise: four manual steps cannot be shipped, and a read-only dev-workflows setup-check reports all four - the ado-backlog/github-backlog pattern.

Detail: docs/adr/0082-a-read-only-setup-check-reports-the-four-manual-steps-the-marketplace-cannot-ship.md

```mermaid
flowchart TD
    C["a colleague installs this marketplace"]
    C --> SHIP["ships automatically:<br/>the six copies + the host hook (Claude Code)"]
    C --> MAN["does NOT ship - 4 manual steps"]
    MAN --> M1["1. install the superpowers plugin"]
    MAN --> M2["2. delete a personal /brainstorm"]
    MAN --> M3["3. run install-antigravity.py, and RE-run on update"]
    MAN --> M4["4. install a superpowers skills port"]
    MAN --> CHK["dev-workflows:setup-check<br/>read-only, PASS/WARN/FAIL, one line each"]
    CHK -.->|complements| W["ADR 0080's automatic warning<br/>- covers step 1 only"]
    C -.->|displaced| VOID["the original question:<br/>six skillOverrides entries - measured inert,<br/>no subject to distribute"]
```

**Re-scoped before answering, at the owner's direction.** Four earlier sessions each
left a note that this ticket's premise was dead, and each left the void-or-re-scope call
to the taker and the owner. Asked directly, the owner chose to re-scope and answer here
rather than close it void. The question became: *what must a colleague do by hand that
this marketplace cannot ship, and how do they find out?* The owner then chose the check
script — **"สคริปต์ตรวจ"** — over documentation alone, over widening ADR 0080's warning,
and over accepting the risk.

**One thing I raised and then had to withdraw, measured rather than argued.** I first
reported that Antigravity gets no host hook and called it a gap. It is not.
`install-antigravity.py`'s own header records that Antigravity discovers skills by folder
and matches on `description`; there is no plugin system and the installer stages no
hooks. So the **upstream** hook is absent there too, the host hook has nothing to
counter, and its absence costs nothing.

That check did surface a real one: **ADR 0070 names no harness**, so it reads as though
the hook mechanism is universal. A dated scope note is added to it in this same change —
a clarification, not a supersession.

**Why a check and not documentation.** The requirement is already written down, twice —
`README.md:59` and `INSTALL.md:71` — and the gap survived both. A check is also the only
option that emits a **positive** signal; a warning can say something is wrong, only a
check can say everything is right, which is what a new machine actually needs.

**Why not fold it into ADR 0080's warning.** That fires only inside `grill-then-plan`,
while step 3's staleness degrades every skill in the plugin. The two are complements: the
warning is automatic and narrow, the check is on demand and complete.

Step 3 is the one to watch. A stale Antigravity staging is not *missing* — the installer
copies rather than links, so an out-of-date copy answers normally, in the wrong version.
That is the same silent-failure shape `short-ref-resolution` measured 2/2, reached by a
different route.

Recorded in [ADR 0082](../../../adr/0082-a-read-only-setup-check-reports-the-four-manual-steps-the-marketplace-cannot-ship.md).

<!-- decision-map:resolution:end -->
