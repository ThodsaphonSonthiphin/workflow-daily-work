# ADR 0004 — /daily router uses hybrid interaction: menu by default, argument to jump

- **Status:** Accepted
- **Date:** 2026-06-11

## Context

ADR 0001 ships a `/daily` router as the single memorized entry point into the daily
arc. The interaction model had three candidates: an interactive menu (bare `/daily`
asks "where are you in your day?"), argument-driven jumps (`/daily wrap` goes
straight to a station), or a hybrid of both.

The whole point of the router is that the owner lost track of skill names. A
pure-argument design reintroduces the memorization problem (forget the station word
→ stuck). A pure-menu design taxes every invocation with a round-trip even after
the stations become muscle memory.

## Decision

Hybrid:

- **Bare `/daily`** → shows the station menu: (1) starting my day, (2) working /
  stuck, (3) filing findings, (4) reporting status, (5) wrapping up. Picking
  WORKING asks one more question (designing / broke / advising / auditing /
  explaining / why-does-this-exist / second-opinion / legacy) and routes per the
  playbook — including the conditional debug chain (ADR 0003).
- **`/daily <station>`** → jumps directly (e.g. `/daily wrap` → invoice-generator).
  Unrecognized arguments fall back to the menu, never to an error.

Only one thing must be memorized: `/daily`. Station words are an optional
accelerator learned through the menu itself (the menu displays them).

## Consequences

- ➕ Zero-memory entry point; the menu teaches its own shortcuts.
- ➕ Power use stays fast; no menu tax once stations are familiar.
- ➕ Unknown argument → menu fallback means the command never dead-ends.
- ➖ The skill must parse a free-text argument; station words need stable, short,
  documented aliases (in PLAYBOOK.md and the command's argument-hint).

## Alternatives considered

- **Menu only** — rejected: permanent round-trip tax on every invocation.
- **Argument only** — rejected: recreates the memorization problem the router
  exists to solve.
