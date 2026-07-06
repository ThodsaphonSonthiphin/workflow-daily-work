---
name: sa-doc
description: Generate a complete System Analysis & Design document (use cases, sequence/activity/state diagrams, class + ER model, data dictionary, architecture, screens, traceability) from one validated central model — Markdown canonical, PDF optional. Trigger on /sa-doc, "ทำเอกสาร SA", "เขียนเอกสารวิเคราะห์และออกแบบระบบ", "ทำ project report วิชา SA", "generate SA document", "system analysis document", "SA&D report", "SDD", or when the user hands over a brief/requirements/codebase and asks for a full design document. Do NOT use for a single ad-hoc diagram, for explaining a problem interactively (problem-description), or for reviewing an existing document (scrutinize).
---

# sa-doc — SA&D document generator

One validated model, one consistent document. Every section of the output is
derived from `sa-model.yaml`; a Python validator blocks generation until the
model is referentially consistent. This exists because hand-written SA
documents rot by copy-paste: the reviewed specimen carried 30+ cross-artifact
contradictions (see the ADR).

## When NOT to use

- One diagram or one section on demand — just draw it, no model needed.
- Explaining a problem interactively → `problem-description`.
- Reviewing/critiquing an existing SA document → `scrutinize`.

## Flow

### 1. Intake

Gather the input (file paths, pasted text, or the conversation so far).
Detect the input language → document language (an explicit language request
wins). Ask the user, in one round:

1. **Profile** — `academic` (course report: adds literature, Gantt plan,
   budget, bibliography) or `professional` (work SDD: adds security design,
   deployment, test-case seed).
2. **Output** — `md`, `pdf`, or `both`.
3. **Project name** — suggest one from the input.

Working directory: `./SA-<project>/` under the current directory unless the
user names another.

### 2. Build the model

Write `SA-<project>/sa-model.yaml` following `references/model-contract.md`
(the schema lives only there). Fill everything the input answers; for required
slots the input does not answer, ask — grouped, fewest possible questions.
`TBD` is acceptable and tracked; **never invent domain facts** (actors, fields,
prices, rules). The bundled example
`${CLAUDE_PLUGIN_ROOT}/scripts/fixtures/sa-model-bookstore.yaml` shows a
complete, clean model.

### 3. Validate — the gate

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/validate_model.py SA-<project>/sa-model.yaml
```

- **Errors block generation.** Fix the model; ask the user when the fix is a
  domain decision. Re-run until exit 0.
- **Warnings** are shown to the user and either fixed or explicitly accepted —
  never silently ignored.
- The TBD inventory is carried into the final summary.

Never write the document while the validator reports errors.

### 4. Generate the document

Write `SA-<project>/SA-<project>.md` from the model using
`references/template-core.md` plus the profile file
(`references/template-academic.md` / `references/template-professional.md`).
Rules:

- Facts come from the model only; prose connects, never introduces.
- Diagrams follow `${CLAUDE_PLUGIN_ROOT}/references/diagram-convention.md` —
  one Mermaid overview at the top, type-matched section diagrams
  (`sequenceDiagram`, `erDiagram`, `flowchart TD`, `stateDiagram-v2`).
- The 13-field use case semantics in the core template are non-negotiable
  (postcondition = guaranteed state; extensions anchored to steps; no
  boilerplate).

### 5. Render (pdf/both only)

```
python ${CLAUDE_PLUGIN_ROOT}/scripts/render_doc.py SA-<project>/SA-<project>.md --pdf
```

Produces a self-contained HTML and prints it to PDF with headless Edge/Chrome.
No browser found → the script says so and the HTML plus print instructions is
the deliverable; do not treat that as a failure. Offline machines: pass
`--marked-js` / `--mermaid-js` with local copies.

## Wrap-up

Summarize: file paths, warnings the user accepted, the TBD inventory (what is
still unknown), and offer next steps — `generating-test-cases` for a test
suite from the use cases, or the backlog pipeline to file open TBDs as work
items. To change the document later, edit `sa-model.yaml`, re-validate,
regenerate — never patch the generated file by hand.

## Rules

- Never generate while the validator reports errors.
- Never invent domain facts; ask or record TBD.
- Never patch the generated document directly — the model is the source of truth.
- The schema is defined only in `references/model-contract.md`; do not restate
  it elsewhere.
