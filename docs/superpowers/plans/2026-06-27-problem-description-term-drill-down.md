# problem-description Term Drill-Down (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cross-cutting "term drill-down" primitive to the `problem-description` skill — click an unfamiliar term mid-walkthrough to open a side drawer with a short, glossary-grounded definition and see-also hops — kept **DRY in a single reference file** that the skill inlines into the self-contained walkthrough it generates.

**Architecture (ADR 0019):** The drawer's CSS + HTML + JS lives **once** in a new `references/term-drilldown.html`, which is both the canonical copyable source (`§CSS` / `§HTML` / `§JS` sections) and a standalone runnable demo. The two templates carry only a short **marker comment** at each insertion point — no drawer code, no `GLOSSARY` — so their existing stepping demo is unchanged. At generation time the skill inlines the reference sections, authors a `GLOSSARY` (terms sourced from `CONTEXT.md`, ADR 0017), adds `closeDrawer()` to `render()`, and marks drillable terms — yielding one self-contained file. The drawer is reader-driven framework, **outside** scene state, so the idempotent-scene rule holds.

**Tech Stack:** Plain HTML/CSS/vanilla JS (self-contained, no build, no deps). Verification: a throwaway Python 3 cross-check script (referential integrity) + a browser smoke test (Playwright MCP if available, else manual) + an assembled sample walkthrough proving the reference + SKILL steps compose.

## Global Constraints

- **Self-contained single file** — generated walkthroughs inline everything; no external CSS/JS/fonts/images. (SKILL.md output contract.)
- **DRY via one source (ADR 0019)** — the drawer primitive exists **once**, in `references/term-drilldown.html`. Templates get markers, not copies. Do not paste the drawer code into the templates.
- **No new color tokens** — reuse: `#5fb4ff` info/accent, `#7ed4ff` accent-bright, `#141b26`/`#1a2330` panel, `#e0e6ed` text, `#6b7785`/`#8a96a3` muted, `#2a3441` border. (SKILL.md "Color tokens — don't change".)
- **Idempotent scenes are sacrosanct** — in a generated walkthrough, no scene may `createElement`/`appendChild` or reference the drawer. Drawer code is *framework* (like `buildProgressDots()`), not scene code; its own `createElement` for chips is allowed.
- **The drawer uses the shared `.hidden { display: none !important; }` toggle** the templates already define — do not add a competing show/hide mechanism, and do not re-copy `.hidden` into a template that already has it.
- **Content grounded in CONTEXT.md (ADR 0017)** — a term in the glossary uses its wording with `source: 'CONTEXT.md'`; otherwise a one-line authored `short` with `source: 'authored'`.
- **Skill files use skill-relative paths** — SKILL.md refers to `references/term-drilldown.html` (not `${CLAUDE_PLUGIN_ROOT}/skills/...`). (CLAUDE.md convention.)
- **Scope is Phase 1 only** — no new visualization modes, no mode framework, no render-verification of generated walkthroughs (ADR 0016 sequences those later). No PLAYBOOK row (enhances an existing skill, not a new one).

**Reference docs (read before starting):**
- Spec: `docs/superpowers/specs/2026-06-27-problem-description-term-drill-down-design.md`
- ADRs [0016](../../adr/0016-problem-description-drill-down-first.md), [0017](../../adr/0017-drill-down-content-grounded-in-context-md.md), [0018](../../adr/0018-drill-down-is-side-drawer-with-see-also-hops.md), [0019](../../adr/0019-drill-down-primitive-single-reference-inlined.md)
- Term **Term drill-down** in [CONTEXT.md](../../../CONTEXT.md)

**Scratchpad dir (throwaway build artifacts), referred to as `<SCRATCH>`:**
`C:\Users\THODSA~1.SON\AppData\Local\Temp\claude\c--Repo2-workflow-daily-work\07f300f1-2044-4695-85a3-7e2432887ea6\scratchpad`

## File structure

| File | Responsibility | Change |
|---|---|---|
| `plugins/dev-workflows/skills/problem-description/references/term-drilldown.html` | Single source of the drawer primitive + runnable demo | **Create** |
| `plugins/dev-workflows/skills/problem-description/template-diagram.html` | Diagram-mode scaffold | Add 3 marker comments |
| `plugins/dev-workflows/skills/problem-description/template.html` | Tables-mode scaffold | Add 3 marker comments |
| `plugins/dev-workflows/skills/problem-description/SKILL.md` | Skill instructions | Document drill-down (Phase 1/4/5 + Common Mistakes) |
| `<SCRATCH>/check_drilldown.py` | Referential-integrity checker (throwaway) | Create & use |
| `<SCRATCH>/sample-walkthrough.html` | Assembled end-to-end proof (throwaway) | Create & verify |

---

### Task 1: Create the single-source reference file

`references/term-drilldown.html` is the one copy of the drawer primitive **and** a standalone runnable demo. It carries clearly-delimited `§CSS` / `§HTML` / `§JS` sections (the bytes to inline into a walkthrough) plus a `DEMO ONLY` harness so the file runs by itself.

**Files:**
- Create: `plugins/dev-workflows/skills/problem-description/references/term-drilldown.html`
- Verify with: `<SCRATCH>/check_drilldown.py` (created here), browser

**Interfaces:**
- Produces: the canonical JS surface `openTerm(key)`, `hopTerm(key)`, `backTerm()`, `closeDrawer()`, `renderTerm(key)`, globals `GLOSSARY` + `drawerStack`; DOM ids `termDrawer`, `drawerTerm`, `drawerSource`, `drawerDef`, `drawerSeeAlsoTitle`, `drawerSeeAlso`, `drawerBack`, `drawerClose`; `GLOSSARY` entry shape `{term, short, seeAlso, source}`. Tasks 2 & 3 reference these by name.

- [ ] **Step 1: Write the reference file**

Create `plugins/dev-workflows/skills/problem-description/references/term-drilldown.html` with exactly this content:

```html
<!DOCTYPE html>
<!--
  =============================================================================
  TERM DRILL-DOWN — single source of truth for the problem-description drawer.
  This file is BOTH (a) the canonical copy of the drill-down primitive and
  (b) a standalone runnable demo (open it directly in a browser).

  TO ADD DRILL-DOWN TO A GENERATED WALKTHROUGH (see SKILL.md Phase 4):
    1. Copy the §CSS block into the walkthrough's <style> (before its .hidden rule).
    2. Copy the §HTML block in just before the </div> that closes .container.
    3. Copy the §JS block into the walkthrough's <script>, after the DOM helpers.
    4. In the walkthrough's render(step), add closeDrawer() as the FIRST line.
    5. Replace the demo GLOSSARY with your terms (sourced from CONTEXT.md) and
       mark terms in narration: <span class="term" data-term="key">…</span>.
  Everything marked "DEMO ONLY" is the standalone harness — do NOT copy it.
  =============================================================================
-->
<html lang="th"><head><meta charset="UTF-8"><title>term drill-down — source + demo</title>
<style>
  /* DEMO ONLY — page chrome + a local .hidden so this file runs standalone. Do not copy;
     a generated walkthrough already defines .hidden and its own body/narration styles. */
  * { box-sizing: border-box; }
  body { margin:0; padding:24px; background:#0a0e14; color:#e0e6ed;
         font-family:'Segoe UI','Tahoma',sans-serif; }
  .narration { background:#1a2330; padding:14px 18px; border-radius:6px;
               border-left:3px solid #5fb4ff; font-size:15px; line-height:1.7; max-width:680px; }
  button { background:#5fb4ff; color:#0a0e14; border:none; padding:8px 16px;
           border-radius:6px; font-weight:700; cursor:pointer; }
  button.tertiary { background:#2a3441; color:#e0e6ed; }
  .hidden { display: none !important; }

  /* ===== §CSS  (copy into the walkthrough's <style>, before its .hidden rule) ===== */
  .term { border-bottom: 1px dotted #5fb4ff; color: #5fb4ff; cursor: help; }
  .term:hover { color: #7ed4ff; }
  .drawer {
    position: fixed; top: 0; right: 0; bottom: 0; width: 340px; max-width: 86vw;
    background: #141b26; border-left: 2px solid #5fb4ff;
    box-shadow: -8px 0 24px #00000088;
    padding: 18px 20px; overflow-y: auto; z-index: 50;
  }
  .drawer-head { display: flex; align-items: flex-start; justify-content: space-between; gap: 10px; }
  .drawer-term { color: #7ed4ff; font-size: 17px; font-weight: 700; line-height: 1.3; }
  .drawer-source { font-size: 10px; color: #6b7785; text-transform: uppercase;
                   letter-spacing: 0.5px; margin: 2px 0 12px; }
  .drawer-def { font-size: 14px; line-height: 1.7; color: #e0e6ed; margin-bottom: 16px; }
  .drawer-seealso-title { font-size: 11px; color: #8a96a3; text-transform: uppercase;
                          letter-spacing: 0.5px; margin-bottom: 8px; }
  .seealso-chip {
    display: inline-block; background: #1a2330; border: 1px solid #2a3441;
    color: #5fb4ff; border-radius: 14px; padding: 4px 12px;
    margin: 0 6px 6px 0; font-size: 13px; cursor: pointer;
  }
  .seealso-chip:hover { background: #233040; border-color: #5fb4ff; }
  .drawer-btns { display: flex; gap: 8px; margin-top: 18px; }
  /* ===== end §CSS ===== */
</style></head>
<body>
  <!-- DEMO ONLY — sample narration + a button that simulates render() closing the drawer. -->
  <div class="narration" id="narration">
    ทดสอบ: ทุก scene เป็น <span class="term" data-term="idempotent">idempotent</span>
    และ DB ใช้ <span class="term" data-term="demo-key">demo key</span> เป็น lookup. ลองคลิกศัพท์.
  </div>
  <p><button id="simNext">ถัดไป → (จำลอง render(): ปิด drawer)</button></p>

  <!-- ===== §HTML  (copy in just before the </div> that closes .container) ===== -->
  <aside id="termDrawer" class="drawer hidden" aria-label="term definition">
    <div class="drawer-head">
      <span class="drawer-term" id="drawerTerm"></span>
      <button class="tertiary" id="drawerClose" title="ปิด">✕</button>
    </div>
    <div class="drawer-source" id="drawerSource"></div>
    <div class="drawer-def" id="drawerDef"></div>
    <div class="drawer-seealso-title hidden" id="drawerSeeAlsoTitle">ดูเพิ่ม</div>
    <div id="drawerSeeAlso"></div>
    <div class="drawer-btns">
      <button class="tertiary hidden" id="drawerBack">← ย้อน</button>
    </div>
  </aside>
  <!-- ===== end §HTML ===== -->

<script>
/* ===== §JS  (copy into the walkthrough's <script>, after the DOM helper functions) ===== */

/* GLOSSARY — inlined from CONTEXT.md at authoring time. REPLACE these demo entries.
     key:'slug'  used in data-term="slug" and in seeAlso
     term:       header shown in the drawer
     short:      CONTEXT.md wording, or an authored one-liner fallback
     seeAlso:    array of other GLOSSARY keys to hop to (optional)
     source:     'CONTEXT.md' | 'authored'                                            */
const GLOSSARY = {
  'idempotent': {
    term: 'idempotent',
    short: 'an operation that lands on the same state no matter how many times it runs — the rule every scene in a walkthrough follows.',
    seeAlso: ['demo-key'],
    source: 'authored'
  },
  'demo-key': {
    term: 'demo key',
    short: 'the lookup key the demo DB stores its value under.',
    seeAlso: [],
    source: 'CONTEXT.md'
  }
};

let drawerStack = [];   // GLOSSARY keys visited this open, for ← back

function renderTerm(key) {
  const entry = GLOSSARY[key];
  if (!entry) return;
  document.getElementById('drawerTerm').textContent = entry.term;
  document.getElementById('drawerSource').textContent =
    entry.source === 'CONTEXT.md' ? 'จาก CONTEXT.md' : 'อธิบายเพิ่มเติม';
  document.getElementById('drawerDef').textContent = entry.short;
  const wrap = document.getElementById('drawerSeeAlso');
  wrap.innerHTML = '';
  const related = (entry.seeAlso || []).filter(k => GLOSSARY[k]);
  if (related.length) {
    document.getElementById('drawerSeeAlsoTitle').classList.remove('hidden');
    related.forEach(k => {
      const chip = document.createElement('span');
      chip.className = 'seealso-chip';
      chip.textContent = GLOSSARY[k].term;
      chip.dataset.hop = k;
      wrap.appendChild(chip);
    });
  } else {
    document.getElementById('drawerSeeAlsoTitle').classList.add('hidden');
  }
  document.getElementById('drawerBack').classList.toggle('hidden', drawerStack.length <= 1);
}

function openTerm(key) {
  if (!GLOSSARY[key]) return;
  drawerStack.push(key);
  renderTerm(key);
  document.getElementById('termDrawer').classList.remove('hidden');
}

function hopTerm(key) {
  if (!GLOSSARY[key]) return;
  drawerStack.push(key);
  renderTerm(key);
}

function backTerm() {
  if (drawerStack.length <= 1) return;
  drawerStack.pop();
  renderTerm(drawerStack[drawerStack.length - 1]);
}

function closeDrawer() {
  drawerStack = [];
  document.getElementById('termDrawer').classList.add('hidden');
}

document.addEventListener('click', (e) => {
  const termEl = e.target.closest('[data-term]');
  if (termEl) { openTerm(termEl.dataset.term); return; }
  const hopEl = e.target.closest('[data-hop]');
  if (hopEl) { hopTerm(hopEl.dataset.hop); return; }
});
document.getElementById('drawerClose').onclick = closeDrawer;
document.getElementById('drawerBack').onclick  = backTerm;
/* ===== end §JS =====
   Reminder: in the walkthrough's render(step), add closeDrawer() as the FIRST line. */

/* DEMO ONLY — the sim button calls closeDrawer() to mimic render() on a step change. */
document.getElementById('simNext').onclick = closeDrawer;
</script>
</body></html>
```

- [ ] **Step 2: Write the referential checker** (`<SCRATCH>/check_drilldown.py`):

```python
import re, sys

def fail(msgs):
    for m in msgs: print("FAIL:", m)
    sys.exit(1)

def main(path):
    src = open(path, encoding="utf-8").read()
    errs = []

    if 'id="termDrawer"' not in src:
        errs.append('#termDrawer element missing')
    m = re.search(r'const GLOSSARY\s*=\s*\{(.*?)\n\};', src, re.S)
    if not m:
        errs.append('GLOSSARY object missing'); fail(errs)
    gbody = m.group(1)

    gloss_keys = set(re.findall(r"^\s*'([\w-]+)'\s*:\s*\{", gbody, re.M))
    if not gloss_keys:
        errs.append('no GLOSSARY entries parsed')

    for t in re.findall(r'data-term="([^"]+)"', src):
        if t not in gloss_keys:
            errs.append(f'data-term="{t}" has no GLOSSARY entry')

    for arr in re.findall(r'seeAlso\s*:\s*\[([^\]]*)\]', gbody):
        for k in re.findall(r"'([\w-]+)'", arr):
            if k not in gloss_keys:
                errs.append(f'seeAlso "{k}" has no GLOSSARY entry')

    for key in gloss_keys:
        blk = re.search(r"'" + re.escape(key) + r"'\s*:\s*\{(.*?)\}", gbody, re.S)
        body = blk.group(1) if blk else ''
        for field in ('term', 'short', 'source'):
            if re.search(r'\b' + field + r'\s*:', body) is None:
                errs.append(f'GLOSSARY["{key}"] missing field: {field}')

    # Idempotency check — only applies to a real walkthrough (has scenes[]).
    s = re.search(r'const scenes\s*=\s*\[(.*?)\n\];', src, re.S)
    if s:
        for forbidden in ('openTerm', 'closeDrawer', 'termDrawer', 'GLOSSARY', 'drawerStack'):
            if forbidden in s.group(1):
                errs.append(f'scene code references "{forbidden}" — drawer must stay out of scenes')

    if errs: fail(errs)
    print(f'OK: {len(gloss_keys)} glossary terms, all references resolve, scenes clean')

if __name__ == '__main__':
    main(sys.argv[1])
```

- [ ] **Step 3: Run the checker against the reference — expect PASS**

Run:
```bash
python "<SCRATCH>/check_drilldown.py" "plugins/dev-workflows/skills/problem-description/references/term-drilldown.html"
```
Expected: exit 0, prints `OK: 2 glossary terms, all references resolve, scenes clean` (no `scenes[]` here, so the scenes check is skipped).

- [ ] **Step 4: Browser smoke test** (Playwright MCP if available, else open manually)

`browser_navigate` → `file:///C:/Repo2/workflow%20daily%20work/plugins/dev-workflows/skills/problem-description/references/term-drilldown.html`, then:
- Click the `idempotent` term → Expected: `#termDrawer` visible; `#drawerTerm` = "idempotent"; `#drawerDef` non-empty; one see-also chip "demo key"; `#drawerBack` hidden.
- Click "demo key" chip → Expected: header "demo key"; `#drawerSource` = "จาก CONTEXT.md"; `#drawerBack` visible; no chips.
- Click `← ย้อน` → Expected: back to "idempotent".
- Click the `ถัดไป →` sim button → Expected: `#termDrawer` hidden.
- Re-open `idempotent`, click `✕` → Expected: hidden.

If anything looks or behaves wrong, fix it here (cheapest place) and re-verify.

- [ ] **Step 5: Commit**

```bash
git add "plugins/dev-workflows/skills/problem-description/references/term-drilldown.html"
git commit -m "feat(problem-description): add term drill-down primitive as single-source reference"
```

---

### Task 2: Add reference markers to both templates

The templates point at the reference instead of carrying the code. Markers are comments only, so the existing stepping demo is untouched.

**Files:**
- Modify: `plugins/dev-workflows/skills/problem-description/template-diagram.html`
- Modify: `plugins/dev-workflows/skills/problem-description/template.html`

**Interfaces:**
- Consumes: `references/term-drilldown.html` (Task 1).
- Produces: nothing at runtime — markers guide the skill at generation time.

- [ ] **Step 1: Diagram template — CSS marker.** In `template-diagram.html`, immediately before the line `.hidden { display: none !important; }` in `<style>`, insert:

```css
  /* term drill-down: inline §CSS from references/term-drilldown.html at generation */
```

- [ ] **Step 2: Diagram template — HTML marker.** Insert after the `</div>` that closes `<div class="controls">` and before the `</div>` that closes `<div class="container">`:

```html
  <!-- term drill-down: inline §HTML from references/term-drilldown.html just before this container closes (at generation) -->
```

- [ ] **Step 3: Diagram template — JS marker.** Insert immediately after the `setNarration(...)` function definition and before `function clearAllStates()`:

```javascript
/* term drill-down: inline §JS from references/term-drilldown.html here (at generation),
   then add closeDrawer() as the FIRST line of render(step). Author a GLOSSARY and mark
   drillable terms in narration with <span class="term" data-term="key">. See SKILL.md Phase 4. */
```

- [ ] **Step 4: Tables template — CSS marker.** In `template.html`, immediately before `.hidden { display: none !important; }` in `<style>`, insert:

```css
  /* term drill-down: inline §CSS from references/term-drilldown.html at generation */
```

- [ ] **Step 5: Tables template — HTML marker.** Insert after the `</div>` that closes `<div class="controls">` and before the `</div>` that closes `<div class="container">`:

```html
  <!-- term drill-down: inline §HTML from references/term-drilldown.html just before this container closes (at generation) -->
```

- [ ] **Step 6: Tables template — JS marker.** Insert immediately after the `setSceneTitle(...)` function and before `function clearAllStates()`:

```javascript
/* term drill-down: inline §JS from references/term-drilldown.html here (at generation),
   then add closeDrawer() as the FIRST line of render(step). Author a GLOSSARY and mark
   drillable terms in narration with <span class="term" data-term="key">. See SKILL.md Phase 4. */
```

- [ ] **Step 7: Verify the templates still run unchanged** (Playwright MCP or manual). For each template, `browser_navigate` to its `file://` URL and:
- Confirm the page loads with no console error.
- Click `ถัดไป →` through to the last step and `↻ เริ่มใหม่` — Expected: the existing demo (boxes/arrows or rows/badges) behaves exactly as before; the markers are inert comments.

URLs:
`file:///C:/Repo2/workflow%20daily%20work/plugins/dev-workflows/skills/problem-description/template-diagram.html`
`file:///C:/Repo2/workflow%20daily%20work/plugins/dev-workflows/skills/problem-description/template.html`

- [ ] **Step 8: Commit**

```bash
git add "plugins/dev-workflows/skills/problem-description/template-diagram.html" "plugins/dev-workflows/skills/problem-description/template.html"
git commit -m "feat(problem-description): mark drill-down insertion points in both templates"
```

---

### Task 3: Document drill-down in SKILL.md + prove end-to-end

Teach the authoring workflow (source terms, inline the reference, mark terms, verify), then follow those exact steps to assemble a sample walkthrough and confirm all 8 acceptance criteria.

**Files:**
- Modify: `plugins/dev-workflows/skills/problem-description/SKILL.md`
- Create & verify: `<SCRATCH>/sample-walkthrough.html`

**Interfaces:**
- Consumes: `references/term-drilldown.html`, both templates, `<SCRATCH>/check_drilldown.py`.

- [ ] **Step 1: Extend Phase 1.** After the "prerequisites" item (numbered list ending at item 3) and before the "Then pick the mode" sentence, add:

```markdown
4. **The unfamiliar terms** — list the terms the narration will use that fall *beyond*
   the prerequisites (domain jargon, schema names, project concepts). These become
   **drillable terms** (Phase 4). Read the project's `CONTEXT.md` (or the mapped context
   via `CONTEXT-MAP.md`) and pull the definition for each term that exists there; for a
   beyond-prerequisite term **not** in the glossary, write a one-line definition yourself.
   A term the reader already knows is **not** made drillable — over-marking turns the
   narration into a sea of dotted underlines.
```

- [ ] **Step 2: Add a Phase 4 subsection.** After the Mode A / Mode B insertion-zone lists and before "**Critical rule** (both modes)", add:

```markdown
**Term drill-down (both modes).** The drawer primitive lives in one place —
`references/term-drilldown.html` — which is also a runnable demo. To add drill-down to
the walkthrough you are generating:

1. Inline its three sections into your output: copy `§CSS` into `<style>` (before the
   `.hidden` rule), `§HTML` just before the `</div>` that closes `.container`, and `§JS`
   into `<script>` after the DOM helpers. Do **not** copy anything marked `DEMO ONLY`.
2. In your `render(step)`, add `closeDrawer()` as the **first** line so stepping closes
   the drawer.
3. Replace the demo `GLOSSARY` with your terms. Each entry:

   ```js
   'glasshull-scope': {
     term:    'glasshull scope',                              // drawer header
     short:   'the records a workflow may touch in one transaction',  // CONTEXT.md wording or authored
     seeAlso: ['row-lock', 'transaction'],                    // other GLOSSARY keys to hop to
     source:  'CONTEXT.md'                                    // or 'authored' for a fallback
   }
   ```

4. Mark each drillable term in narration: `<span class="term" data-term="glasshull-scope">glasshull scope</span>`.

Rules: `source: 'CONTEXT.md'` must quote the glossary; use `'authored'` only when the
term is absent (and consider offering to add it to `CONTEXT.md`). The drawer is
**framework, not a scene** — never call `openTerm`/`closeDrawer`/`GLOSSARY` from a scene
function; the no-`createElement`-in-scenes rule does **not** apply to the drawer's own
code (the templates carry only a marker pointing here).
```

- [ ] **Step 3: Extend the Phase 5 self-test checklist.** After the existing last checkbox (the identifier-collision item), add:

```markdown
- [ ] **Drill-down referential integrity:** every `data-term="X"` has a `GLOSSARY[X]`
      entry, and every `seeAlso` key resolves to a `GLOSSARY` entry
- [ ] **Grounding:** every `GLOSSARY` entry marked `source: 'CONTEXT.md'` matches the
      glossary wording; `'authored'` is used only for terms absent from `CONTEXT.md`
- [ ] **Drawer is orthogonal:** no scene references the drawer
      (`openTerm`/`closeDrawer`/`termDrawer`/`GLOSSARY`); `clearAllStates()` does not
      touch it; `render()` calls `closeDrawer()` first; `Next`/`Prev`/`Reset` close the
      drawer and leave no residue
- [ ] **See-also hops:** clicking a see-also chip swaps the drawer; `← back` restores the
      prior term; with no `CONTEXT.md`, drillable terms still work via `authored` defs
```

- [ ] **Step 4: Add Common Mistakes rows.** Append to the Common Mistakes table:

```markdown
| Invented term definitions instead of CONTEXT.md | Source from the project glossary; author a fallback only when the term is absent (ADR 0017). |
| Over-marking — every other word is drillable | Mark only terms *beyond* the reader's stated prerequisites. |
| Copying the drawer code into the template | The primitive lives once in `references/term-drilldown.html`; inline it at generation (ADR 0019). |
| A scene opens/closes/reads the drawer | The drawer is reader-driven framework, never scene state. Keep scenes pure. |
| `data-term` with no `GLOSSARY` entry (drawer no-ops) | Every `data-term` and `seeAlso` key must resolve to a `GLOSSARY` entry. |
```

- [ ] **Step 5: Assemble a sample walkthrough (end-to-end proof).** Following Step 2 exactly, build `<SCRATCH>/sample-walkthrough.html`:
  1. Copy `plugins/dev-workflows/skills/problem-description/template-diagram.html` to `<SCRATCH>/sample-walkthrough.html`.
  2. Replace the **CSS marker** with the `§CSS` block from `references/term-drilldown.html`.
  3. Replace the **HTML marker** with the `§HTML` block.
  4. Replace the **JS marker** with the `§JS` block, then change its demo `GLOSSARY` to two terms `idempotent` (seeAlso `['demo-key']`, `source:'authored'`) and `demo-key` (`source:'CONTEXT.md'`).
  5. Add `closeDrawer();` as the first line of `render(step)`.
  6. In scene 0's narration, add `และทุก scene เป็น <span class="term" data-term="idempotent">idempotent</span>`; in scene 2's narration, add `จาก <span class="term" data-term="demo-key">demo key</span>`.
  7. Remove any `DEMO ONLY` lines accidentally carried over (there should be none — they live outside the §-sections).

- [ ] **Step 6: Verify the assembled walkthrough against all 8 acceptance criteria.**

Run the checker (now with `scenes[]` present, so the idempotency check is active):
```bash
python "<SCRATCH>/check_drilldown.py" "<SCRATCH>/sample-walkthrough.html"
```
Expected: `OK: 2 glossary terms, all references resolve, scenes clean` — covers criteria 1, 2, 7 (scenes-clean).

Browser (Playwright MCP or manual), `file://` to `<SCRATCH>/sample-walkthrough.html`:
- Step 0: click `idempotent` → drawer opens, def shown, see-also "demo key", back hidden. (crit 4)
- Click "demo key" chip → swaps; source "จาก CONTEXT.md"; back visible. Click `← ย้อน` → back to idempotent. (crit 5)
- Click `ถัดไป →` → drawer closes AND the diagram advances to Step 1 (proves `render()` closeDrawer + no interference). `↻ เริ่มใหม่` → Step 0, drawer closed, no residue. (crit 6, 7-residue)
- Step 0 `idempotent` entry is `source:'authored'` and works → drill-down functions without CONTEXT.md. (crit 8)
- Criterion 3 (CONTEXT.md wording match) is an author-time check; here the `demo-key` entry is tagged `CONTEXT.md` as a stand-in — confirm the mechanism renders `source` correctly. (crit 3 mechanism)

- [ ] **Step 7: Commit**

```bash
git add "plugins/dev-workflows/skills/problem-description/SKILL.md"
git commit -m "docs(problem-description): document term drill-down authoring + verify end-to-end"
```

---

## Self-Review

**1. Spec coverage**

| Spec section | Task |
|---|---|
| §1 Content source (GLOSSARY, inlined, grounded-first, authored fallback) | Task 1 (§JS GLOSSARY), Task 3.1, 3.2 |
| §2 Container (drawer, open/close/back-stack, see-also hop) | Task 1 (§HTML, §JS) |
| §3 Affordance (`.term` dotted-underline + accent + cursor) | Task 1 (§CSS) |
| §4 Idempotency (drawer outside scene state; render closes it) | Task 1 (closeDrawer), Task 3.2 + 3.5 (render edit), checker scenes-clean (1, 3.6) |
| §5 Which terms drillable (beyond prerequisites) | Task 3.1 |
| Single source + template markers (ADR 0019) | Task 1 (reference), Task 2 (markers) |
| Changes to SKILL.md (Phase 1/4/5 + Common Mistakes) | Task 3.1–3.4 |
| 8 acceptance criteria | Task 3.6 |
| Reference doubles as runnable demo | Task 1.4 |
| Non-goals (no new modes / framework / render-verify) | Honored — none added |

No gaps.

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to Task N". Every code block is complete. The `[INSERT: ...]` strings inside the templates are the templates' own pre-existing authoring placeholders (out of scope).

**3. Type consistency:** Names stable across the reference, the checker, and the SKILL docs: `openTerm`, `hopTerm`, `backTerm`, `closeDrawer`, `renderTerm`, `GLOSSARY`, `drawerStack`; ids `termDrawer`/`drawerTerm`/`drawerSource`/`drawerDef`/`drawerSeeAlsoTitle`/`drawerSeeAlso`/`drawerBack`/`drawerClose`; fields `term`/`short`/`seeAlso`/`source`. The checker asserts exactly these. Consistent.

---

## Execution Handoff

(Executing now via subagent-driven-development.)
