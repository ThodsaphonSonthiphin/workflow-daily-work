---
name: learn-with-flashcard
description: "Turn what was asked and answered in this session (or a ticket, runbook, codebase or document the user names) into a flashcard page for spaced review, so short-term answers become long-term memory. Programmer-level cards - each flow or component's name, inputs (with keys), outputs, tables, choice values and logic - where every logic answer is a Mermaid flowchart plus a real example and a cited source. Use when the user says ทำ flashcard, ทำ flash card, ทบทวน, จำให้ได้, เปลี่ยน short term memory เป็น long term memory, make flashcards, quiz me with cards, help me memorise this, or learn with flashcard. Not for Socratic questioning (asking-to-understand), not for explaining one concept (feynman-explain), not for a step-by-step walkthrough (problem-description)."
---

# Learn with flashcard

Make a flashcard page that the user flips, grades ("ยังไม่แม่น" / "จำได้") and revisits until each card is known. The page is one self-contained HTML file built from `assets/flashcards-template.html`.

## What the user wants from the cards (ADR 0334)

1. **Programmer-level questions.** For every flow, API, table or component in scope, ask what a programmer needs to work on it:
   - its name, what it does, and which tables it reads or writes;
   - its inputs, with their internal keys (for example `text`, `text_1`) and which are required;
   - its outputs and their possible values;
   - the choice / option-set values, with their numbers;
   - its logic: how it decides, branches, filters, computes, fails;
   - the traps (platform rules that break a save or a run).
2. **Logic is always a Mermaid flowchart.** Not a bullet list, not ASCII art. Decisions are diamonds `Q{"...?"}` with labelled Yes/No edges.
3. **Each logic card = flowchart, then one real example** (real values and dates from a dev environment, a test run, or the source), then a table only if it adds something.
4. **Each card cites its source** (ticket, decision number, runbook step, test run, spec page and section).
5. **The user's language for questions and prose** (Thai is fine). Chart labels stay short, mostly code names.

## Steps

1. **Collect the questions.** List every question the user asked in this session, or the topics in the source they named. Then add the programmer-level questions above that the topic needs but nobody asked.
2. **Get every fact from a source, not from memory.** Read the runbook, ticket, code or document for each answer. Copy values exactly (names, keys, numbers, dates). If a fact is only planned or intended, not measured, say so on the card ("ยังไม่ได้รัน", "เป็นเจตนา"). Never invent a value.
3. **Split into atomic cards.** One fact or one decision per card. Group them into 3-6 decks (for example: overview, flow 1, flow 2, email, confusing terms). Card kinds:
   - `fact`: `q`, `a` (HTML: list or table), `src`;
   - `logic`: `q`, `chart` (Mermaid), `ex` (HTML, the real example), optional `a`, `src`.
4. **Write the Mermaid charts with these rules** (they keep the parser happy):
   - Start with `flowchart TD` (or `LR`).
   - Put every label with spaces or symbols in double quotes: `A["text"]`, `Q{"question?"}`, `R(["end"])`, edge labels `-- "label" -->`.
   - Line breaks are `<br/>`. Do not use `#`, `;`, other `<` tags, or a double quote inside a label. Write "ticket 148", not "#148"; write "and" or "the ampersand", not `&` inside a label (`A & B --> C` as node grouping is fine).
   - In long chains, declare the nodes first, then the edges.
   - Edges out of a whole block: `subgraph TRY ["Try"] ... end` then `TRY -. "failed" .-> X`.
5. **Build the page.** Copy `assets/flashcards-template.html` to a temporary folder. Replace `{{TITLE}}` (a 2-4 word name), `{{SUBTITLE}}` (one line: what the deck covers) and `{{STORE_KEY}}` (a unique slug plus `-v1`). Replace the sample `DECKS` and `CARDS` arrays. Keep everything else: the template loads Mermaid 10.9.1 from cdnjs and renders each chart with `mermaid.render` when its card opens, because cards are drawn at run time and a host's static Mermaid support never sees them. `assets/example-phone-log-flashcards.html` is a full worked deck (33 cards) to copy patterns from.
6. **Check.** Run `node scripts/check_flashcards.js <page.html>`. It runs the page script, then checks ids, decks, kinds, that each logic card has a chart and an example, the placeholders, and the Mermaid rules above. Fix every issue and run it again until it says `no issues`.
7. **Publish.** If your harness can publish an HTML page as a shareable artifact, publish the file there and follow that mechanism's own first-step rules (for example, a required quickstart call before a new artifact). With no such mechanism, give the user the file's full path to open in a browser. To change a deck later, edit the same file and publish it again to the same place.
8. **Report.** Give the link or path and a table of decks (name, card count, what they cover). Say which facts are unmeasured, and say you have not seen the rendered page unless you previewed it. Suggest 2-3 days of review with "เฉพาะที่ยังไม่แม่น" on.

## The page (already in the template)

- Flip by tap or Space; grade with 1 (the card comes back 4 cards later in this round) or 2.
- Filters: deck, all / only not yet known, kind (Logic / Fact), shuffle, and a list view of all cards.
- Progress is kept per card in the viewer's browser (`localStorage`, key = `STORE_KEY`); a card counts as known after 2 correct answers. Change `STORE_KEY` when the card set changes completely.
- Deck colours follow deck order (5 colours); light and dark themes; Mermaid redraws when the theme changes.
