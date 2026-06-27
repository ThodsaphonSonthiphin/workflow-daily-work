# problem-description Term Drill-Down (Phase 1) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a cross-cutting "term drill-down" primitive to the `problem-description` skill so a reader can click an unfamiliar term mid-walkthrough and read a short, glossary-grounded definition in a side drawer with see-also hops — landing in both existing modes (diagram + tables).

**Architecture:** A self-contained side drawer (`#termDrawer`) is declared once in each template, toggled via the same `.hidden` pattern every other panel uses. A `GLOSSARY` object (inlined from `CONTEXT.md` at authoring time) holds `{term, short, seeAlso, source}` per drillable term. Drillable terms in narration are `<span class="term" data-term="key">`; a single delegated `document` click listener opens the drawer (survives per-scene `innerHTML` swaps). A `drawerStack` array powers `← back`; `render(step)` calls `closeDrawer()` so stepping always closes it. The drawer lives **outside** scene state — `clearAllStates()` never touches it and no scene references it — so the idempotent-scene rule is preserved.

**Tech Stack:** Plain HTML/CSS/vanilla JS (self-contained single file, no build, no deps). Verification uses a throwaway Python 3 cross-check script (referential integrity) plus a browser smoke test (Playwright MCP if available, else manual).

## Global Constraints

- **Self-contained single file** — no external CSS/JS/fonts/images; everything inlined. (problem-description SKILL.md output contract.)
- **No new color tokens** — reuse the existing palette: `#5fb4ff` info/accent, `#7ed4ff` accent-bright, `#1a2330`/`#141b26` panel, `#e0e6ed` text, `#6b7785`/`#8a96a3` muted. (SKILL.md "Color tokens — don't change".)
- **Idempotent scenes are sacrosanct** — no scene function may `createElement`/`appendChild` or reference the drawer. Drawer code is *framework*, not scene code (same category as `buildProgressDots()`).
- **The drawer uses the shared `.hidden { display: none !important; }` toggle** already defined in both templates — do not add a competing show/hide mechanism.
- **Both templates get the byte-identical framework block** (CSS `.term`/`.drawer*`, the `#termDrawer` HTML, and the JS `GLOSSARY`-framework + wiring). Only the `GLOSSARY` *demo entries* and the demo `data-term` spans differ per template.
- **Content grounded in CONTEXT.md** (ADR 0017): a term present in the project glossary uses its wording with `source: 'CONTEXT.md'`; otherwise a one-line authored `short` with `source: 'authored'`.
- **Scope is Phase 1 only.** No new visualization modes, no mode framework, no browser render-verification of generated walkthroughs (ADR 0016 sequences those later).

**Reference docs (read before starting):**
- Spec: [docs/superpowers/specs/2026-06-27-problem-description-term-drill-down-design.md](2026-06-27-problem-description-term-drill-down-design.md) *(in ../specs/)* — full path `docs/superpowers/specs/2026-06-27-problem-description-term-drill-down-design.md`
- ADRs [0016](../../adr/0016-problem-description-drill-down-first.md), [0017](../../adr/0017-drill-down-content-grounded-in-context-md.md), [0018](../../adr/0018-drill-down-is-side-drawer-with-see-also-hops.md)
- Term **Term drill-down** in [CONTEXT.md](../../../CONTEXT.md)

**Scratchpad dir (throwaway build artifacts):**
`C:\Users\THODSA~1.SON\AppData\Local\Temp\claude\c--Repo2-workflow-daily-work\07f300f1-2044-4695-85a3-7e2432887ea6\scratchpad`
(referred to below as `<SCRATCH>`.)

---

## File structure

| File | Responsibility | Change |
|---|---|---|
| `plugins/dev-workflows/skills/problem-description/template-diagram.html` | Diagram-mode scaffold | Add drawer CSS + `#termDrawer` HTML + GLOSSARY-framework JS + `closeDrawer()` in `render()` + demo terms |
| `plugins/dev-workflows/skills/problem-description/template.html` | Tables-mode scaffold | Same drawer additions |
| `plugins/dev-workflows/skills/problem-description/SKILL.md` | Skill instructions | Document drill-down in Phase 1/4/5 + Common Mistakes |
| `<SCRATCH>/drawer-mockup.html` | De-risk mockup (throwaway) | Create |
| `<SCRATCH>/check_drilldown.py` | Referential-integrity checker (throwaway) | Create |

The drawer primitive is identical across the two templates, so it is authored & validated **once** in the mockup (Task 1), gated by a static checker (Task 2), then ported to each template (Tasks 3–4).

---

## Canonical snippets (used verbatim in Tasks 1, 3, 4)

These four blocks are the drill-down primitive. They are repeated in full inside each task that needs them (read tasks out of order safely).

**[CSS_BLOCK]** — insert immediately *before* the line `.hidden { display: none !important; }` in each template's `<style>`:

```css
  /* ---- term drill-down: drillable term affordance ---- */
  .term { border-bottom: 1px dotted #5fb4ff; color: #5fb4ff; cursor: help; }
  .term:hover { color: #7ed4ff; }

  /* ---- term drill-down: side drawer (uses the shared .hidden toggle) ---- */
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
```

**[DRAWER_HTML]** — insert immediately *after* the closing `</div>` of the `.controls` block and *before* the `</div>` that closes `.container`:

```html
  <!-- ============ TERM DRILL-DOWN DRAWER (declared once; toggled by openTerm/closeDrawer) ============ -->
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
```

**[DRILLDOWN_JS]** — the framework. Insert as a block *after* the template's last DOM-helper function (`setNarration` in diagram mode / `setSceneTitle` in tables mode) and *before* `clearAllStates`:

```javascript
/* =============================================================================
   TERM DRILL-DOWN — framework (reader-driven overlay, NOT scene state).
   Authoring only edits GLOSSARY below; never call these from a scene.
   ============================================================================= */
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
```

> The framework uses `classList.remove/add/toggle('hidden')` directly (not the templates' `show()`/`hide()` helpers) so the block is byte-identical across both templates regardless of which helper each defines.

**[WIRING_JS]** — insert *after* the three nav button `onclick` handlers and *before* `buildProgressDots();`:

```javascript
/* TERM DRILL-DOWN — wiring. Delegated on document so it survives narration innerHTML swaps. */
document.addEventListener('click', (e) => {
  const termEl = e.target.closest('[data-term]');
  if (termEl) { openTerm(termEl.dataset.term); return; }
  const hopEl = e.target.closest('[data-hop]');
  if (hopEl) { hopTerm(hopEl.dataset.hop); return; }
});
document.getElementById('drawerClose').onclick = closeDrawer;
document.getElementById('drawerBack').onclick  = backTerm;
```

**[RENDER_EDIT]** — make `closeDrawer()` the first line inside `function render(step) {` so step navigation always closes the drawer:

```javascript
function render(step) {
  closeDrawer();          // <-- ADD: term drawer is transient; close on any step change
  clearAllStates();
  if (scenes[step]) scenes[step]();
  // ...rest unchanged...
```

---

### Task 1: De-risk — standalone drawer mockup

Author the primitive once in a throwaway mockup and confirm it looks and behaves right in a real browser before touching the shipped templates (spec "Suggested first build step").

**Files:**
- Create: `<SCRATCH>/drawer-mockup.html`

**Interfaces:**
- Produces: the validated `[CSS_BLOCK]`, `[DRAWER_HTML]`, `[DRILLDOWN_JS]`, `[WIRING_JS]` snippets that Tasks 3–4 paste verbatim. Public JS surface: `openTerm(key)`, `hopTerm(key)`, `backTerm()`, `closeDrawer()`, and the global `GLOSSARY` object.

- [ ] **Step 1: Write the mockup file**

Create `<SCRATCH>/drawer-mockup.html` with this exact content (it embeds all four canonical snippets plus a minimal harness):

```html
<!DOCTYPE html>
<html lang="th"><head><meta charset="UTF-8"><title>drawer mockup</title>
<style>
  * { box-sizing: border-box; }
  body { margin:0; padding:24px; background:#0a0e14; color:#e0e6ed;
         font-family:'Segoe UI','Tahoma',sans-serif; }
  .narration { background:#1a2330; padding:14px 18px; border-radius:6px;
               border-left:3px solid #5fb4ff; font-size:15px; line-height:1.7; max-width:680px; }
  button { background:#5fb4ff; color:#0a0e14; border:none; padding:8px 16px;
           border-radius:6px; font-weight:700; cursor:pointer; }
  button.tertiary { background:#2a3441; color:#e0e6ed; }
  /* ---- term drill-down: drillable term affordance ---- */
  .term { border-bottom: 1px dotted #5fb4ff; color: #5fb4ff; cursor: help; }
  .term:hover { color: #7ed4ff; }
  /* ---- term drill-down: side drawer (uses the shared .hidden toggle) ---- */
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
  .hidden { display: none !important; }
</style></head>
<body>
  <div class="narration" id="narration">
    ทดสอบ: ทุก scene เป็น <span class="term" data-term="idempotent">idempotent</span>
    และ DB ใช้ <span class="term" data-term="demo-key">demo key</span> เป็น lookup. ลองคลิกศัพท์.
  </div>
  <p><button id="nextBtn">ถัดไป → (จำลอง: ควรปิด drawer)</button></p>

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

<script>
const GLOSSARY = {
  'idempotent': {
    term: 'idempotent',
    short: 'an operation that lands on the same state no matter how many times it runs — the rule every scene in this walkthrough follows.',
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

let drawerStack = [];
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
document.getElementById('nextBtn').onclick = closeDrawer;  // simulates render() closing the drawer
</script>
</body></html>
```

- [ ] **Step 2: Open the mockup and verify behavior (this is the test)**

Open `<SCRATCH>/drawer-mockup.html` in a browser. **If the Playwright MCP is available**, drive it:

Run (tool calls):
1. `browser_navigate` → `file:///C:/Users/THODSA~1.SON/AppData/Local/Temp/claude/c--Repo2-workflow-daily-work/07f300f1-2044-4695-85a3-7e2432887ea6/scratchpad/drawer-mockup.html`
2. `browser_snapshot` — note the two `.term` spans are present.
3. `browser_click` the `idempotent` term.
4. `browser_snapshot` — Expected: `#termDrawer` visible; `#drawerTerm` = "idempotent"; `#drawerDef` non-empty; one see-also chip "demo key"; `#drawerBack` hidden.
5. `browser_click` the "demo key" see-also chip.
6. `browser_snapshot` — Expected: `#drawerTerm` = "demo key"; `#drawerSource` text = "จาก CONTEXT.md"; `#drawerBack` now visible; no see-also chips.
7. `browser_click` `#drawerBack` → Expected: back to "idempotent".
8. `browser_click` the "ถัดไป →" button → Expected: `#termDrawer` hidden (simulated step change).
9. `browser_click` the `idempotent` term again, then `browser_click` `#drawerClose` → Expected: drawer hidden.

**If Playwright MCP is not available**, open the file manually and confirm the same nine behaviors by eye.

Expected: all behaviors pass. If the drawer overlaps content awkwardly or colors look off, adjust `[CSS_BLOCK]` here (this is the cheap place to fix it) and re-verify before Task 3.

- [ ] **Step 3: Commit** (the mockup is throwaway in scratchpad — nothing to commit; record completion in your task tracker and proceed).

---

### Task 2: Static cross-check tool (referential integrity gate)

A deterministic, browser-free checker that gates Tasks 3–4: every `data-term` and every `seeAlso` key must resolve to a `GLOSSARY` entry, the drawer scaffold must be present, and no scene may reference the drawer. Written test-first: it FAILS against the current (unmodified) templates.

**Files:**
- Create: `<SCRATCH>/check_drilldown.py`

**Interfaces:**
- Consumes: a template `.html` path as `argv[1]`.
- Produces: exit code 0 (all checks pass) or 1 (prints each failure). Used by Tasks 3, 4, and 6.

- [ ] **Step 1: Write the checker**

Create `<SCRATCH>/check_drilldown.py`:

```python
import re, sys

def fail(msgs):
    for m in msgs: print("FAIL:", m)
    sys.exit(1)

def main(path):
    src = open(path, encoding="utf-8").read()
    errs = []

    # 1. Scaffold present
    if 'id="termDrawer"' not in src:
        errs.append('#termDrawer element missing')
    m = re.search(r'const GLOSSARY\s*=\s*\{(.*?)\n\};', src, re.S)
    if not m:
        errs.append('GLOSSARY object missing')
        fail(errs)
    glossary_body = m.group(1)

    # 2. GLOSSARY top-level keys: 'key': { ... }
    gloss_keys = set(re.findall(r"^\s*'([\w-]+)'\s*:\s*\{", glossary_body, re.M))
    if not gloss_keys:
        errs.append('no GLOSSARY entries parsed')

    # 3. Every data-term="X" resolves
    for t in re.findall(r'data-term="([^"]+)"', src):
        if t not in gloss_keys:
            errs.append(f'data-term="{t}" has no GLOSSARY entry')

    # 4. Every seeAlso key resolves
    for arr in re.findall(r'seeAlso\s*:\s*\[([^\]]*)\]', glossary_body):
        for k in re.findall(r"'([\w-]+)'", arr):
            if k not in gloss_keys:
                errs.append(f'seeAlso "{k}" has no GLOSSARY entry')

    # 5. Each entry has term/short/source
    for key in gloss_keys:
        block = re.search(r"'" + re.escape(key) + r"'\s*:\s*\{(.*?)\}", glossary_body, re.S)
        body = block.group(1) if block else ''
        for field in ('term', 'short', 'source'):
            if re.search(r'\b' + field + r'\s*:', body) is None:
                errs.append(f'GLOSSARY["{key}"] missing field: {field}')

    # 6. No scene references the drawer (idempotent-scene rule)
    s = re.search(r'const scenes\s*=\s*\[(.*?)\n\];', src, re.S)
    if s:
        scenes_body = s.group(1)
        for forbidden in ('openTerm', 'closeDrawer', 'termDrawer', 'GLOSSARY', 'drawerStack'):
            if forbidden in scenes_body:
                errs.append(f'scene code references "{forbidden}" — drawer must stay out of scenes')
    else:
        errs.append('could not locate scenes[] array')

    if errs: fail(errs)
    print(f'OK: {len(gloss_keys)} glossary terms, all references resolve, scenes clean')

if __name__ == '__main__':
    main(sys.argv[1])
```

- [ ] **Step 2: Run it against an unmodified template to confirm it fails**

Run:
```bash
python "<SCRATCH>/check_drilldown.py" "plugins/dev-workflows/skills/problem-description/template-diagram.html"
```
Expected: exit 1, prints `FAIL: #termDrawer element missing` and `FAIL: GLOSSARY object missing`.

- [ ] **Step 3: Commit** (throwaway in scratchpad — nothing to commit; proceed).

---

### Task 3: Add the drawer to the diagram template

Port the validated primitive into `template-diagram.html` and seed demo terms so the scaffold stays browser-runnable.

**Files:**
- Modify: `plugins/dev-workflows/skills/problem-description/template-diagram.html`
- Verify with: `<SCRATCH>/check_drilldown.py`

**Interfaces:**
- Consumes: `[CSS_BLOCK]`, `[DRAWER_HTML]`, `[DRILLDOWN_JS]`, `[WIRING_JS]`, `[RENDER_EDIT]` from the canonical snippets section; checker from Task 2.
- Produces: a diagram template whose `GLOSSARY` demo keys are `idempotent` and `demo-key`.

- [ ] **Step 1: Add the CSS.** Insert `[CSS_BLOCK]` immediately before the line `.hidden { display: none !important; }` in `<style>` (currently the last rule, ~line 220).

```css
  /* ---- term drill-down: drillable term affordance ---- */
  .term { border-bottom: 1px dotted #5fb4ff; color: #5fb4ff; cursor: help; }
  .term:hover { color: #7ed4ff; }

  /* ---- term drill-down: side drawer (uses the shared .hidden toggle) ---- */
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
```

- [ ] **Step 2: Add the drawer HTML.** Insert `[DRAWER_HTML]` after the `</div>` that closes `<div class="controls">` and before the `</div>` that closes `<div class="container">`:

```html
  <!-- ============ TERM DRILL-DOWN DRAWER (declared once; toggled by openTerm/closeDrawer) ============ -->
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
```

- [ ] **Step 3: Add the GLOSSARY (demo entries).** Insert immediately after the `const LABELS = [...]` line (~line 333):

```javascript

/* =============================================================================
   TERM DRILL-DOWN — glossary inlined from CONTEXT.md at authoring time.
   One entry per drillable term used in narration:
     key:     stable slug used in data-term="..." and in seeAlso
     term:    display name shown in the drawer header
     short:   the short definition (CONTEXT.md wording, or authored fallback)
     seeAlso: array of other GLOSSARY keys to hop to (optional)
     source:  'CONTEXT.md' | 'authored'
   DEMO entries below — replace with terms from your walkthrough.
   ============================================================================= */
const GLOSSARY = {
  'idempotent': {
    term: 'idempotent',
    short: 'an operation that lands on the same state no matter how many times it runs — the rule every scene in this walkthrough follows.',
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
```

- [ ] **Step 4: Add the drill-down framework.** Insert `[DRILLDOWN_JS]` after the `setNarration(...)` function definition (~line 377) and before `function clearAllStates()`:

```javascript
/* =============================================================================
   TERM DRILL-DOWN — framework (reader-driven overlay, NOT scene state).
   Authoring only edits GLOSSARY above; never call these from a scene.
   ============================================================================= */
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
```

- [ ] **Step 5: Close the drawer on step change.** In `function render(step) {`, add `closeDrawer();` as the first line (before `clearAllStates();`):

```javascript
function render(step) {
  closeDrawer();
  clearAllStates();
  if (scenes[step]) scenes[step]();
```

- [ ] **Step 6: Add the wiring.** Insert `[WIRING_JS]` after the `resetBtn.onclick` line (~line 501) and before `buildProgressDots();`:

```javascript
/* TERM DRILL-DOWN — wiring. Delegated on document so it survives narration innerHTML swaps. */
document.addEventListener('click', (e) => {
  const termEl = e.target.closest('[data-term]');
  if (termEl) { openTerm(termEl.dataset.term); return; }
  const hopEl = e.target.closest('[data-hop]');
  if (hopEl) { hopTerm(hopEl.dataset.hop); return; }
});
document.getElementById('drawerClose').onclick = closeDrawer;
document.getElementById('drawerBack').onclick  = backTerm;
```

- [ ] **Step 7: Seed demo terms into the demo scenes.** In scene 0, change the narration body so it contains a drillable term; in scene 2, add the second term.

Scene 0 — replace the existing body line:
```javascript
      <br/>กด <strong>ถัดไป →</strong> เพื่อดู 3-step demo. แทนที่ scenes ด้านล่างเพื่อสร้าง walkthrough จริง
```
with:
```javascript
      และทุก scene เป็น <span class="term" data-term="idempotent">idempotent</span> (ลองคลิกศัพท์ดูคำนิยาม)
      <br/>กด <strong>ถัดไป →</strong> เพื่อดู 3-step demo. แทนที่ scenes ด้านล่างเพื่อสร้าง walkthrough จริง
```

Scene 2 — replace the existing body line:
```javascript
      Server แปลง request เป็น query → ส่งไป DB เพื่อ read value
```
with:
```javascript
      Server แปลง request เป็น query → ส่งไป DB เพื่อ read value จาก <span class="term" data-term="demo-key">demo key</span>
```

- [ ] **Step 8: Run the static checker — expect PASS**

Run:
```bash
python "<SCRATCH>/check_drilldown.py" "plugins/dev-workflows/skills/problem-description/template-diagram.html"
```
Expected: exit 0, prints `OK: 2 glossary terms, all references resolve, scenes clean`.

- [ ] **Step 9: Browser smoke test (Playwright MCP if available, else manual)**

`browser_navigate` → `file:///C:/Repo2/workflow%20daily%20work/plugins/dev-workflows/skills/problem-description/template-diagram.html`, then:
- Click the `idempotent` term → Expected: `#termDrawer` visible, def shown, see-also chip "demo key", `#drawerBack` hidden.
- Click "demo key" chip → Expected: header swaps to "demo key", source line "จาก CONTEXT.md", `#drawerBack` visible.
- Click `#drawerBack` → Expected: back to "idempotent".
- Click `ถัดไป →` → Expected: drawer hidden; diagram advances to Step 1.
- Click `↻ เริ่มใหม่` → Expected: back to Step 0, drawer still hidden, no residue.

- [ ] **Step 10: Commit**

```bash
git add "plugins/dev-workflows/skills/problem-description/template-diagram.html"
git commit -m "feat(problem-description): add term drill-down drawer to diagram template"
```

---

### Task 4: Add the drawer to the tables template

Same primitive, ported to `template.html`. Demo terms `idempotent` and `cascade` (the tables demo already discusses CASCADE).

**Files:**
- Modify: `plugins/dev-workflows/skills/problem-description/template.html`
- Verify with: `<SCRATCH>/check_drilldown.py`

**Interfaces:**
- Consumes: the canonical snippets; checker from Task 2.
- Produces: a tables template whose `GLOSSARY` demo keys are `idempotent` and `cascade`.

- [ ] **Step 1: Add the CSS.** Insert `[CSS_BLOCK]` immediately before `.hidden { display: none !important; }` in `<style>` (~line 173):

```css
  /* ---- term drill-down: drillable term affordance ---- */
  .term { border-bottom: 1px dotted #5fb4ff; color: #5fb4ff; cursor: help; }
  .term:hover { color: #7ed4ff; }

  /* ---- term drill-down: side drawer (uses the shared .hidden toggle) ---- */
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
```

- [ ] **Step 2: Add the drawer HTML.** Insert `[DRAWER_HTML]` after the `</div>` closing `<div class="controls">` and before the `</div>` closing `<div class="container">` (~line 292):

```html
  <!-- ============ TERM DRILL-DOWN DRAWER (declared once; toggled by openTerm/closeDrawer) ============ -->
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
```

- [ ] **Step 3: Add the GLOSSARY (demo entries).** Insert immediately after the `const ID_LIST = [...]` line (~line 301):

```javascript

/* =============================================================================
   TERM DRILL-DOWN — glossary inlined from CONTEXT.md at authoring time.
   One entry per drillable term used in narration:
     key:     stable slug used in data-term="..." and in seeAlso
     term:    display name shown in the drawer header
     short:   the short definition (CONTEXT.md wording, or authored fallback)
     seeAlso: array of other GLOSSARY keys to hop to (optional)
     source:  'CONTEXT.md' | 'authored'
   DEMO entries below — replace with terms from your walkthrough.
   ============================================================================= */
const GLOSSARY = {
  'idempotent': {
    term: 'idempotent',
    short: 'an operation that lands on the same state no matter how many times it runs — the rule every scene in this walkthrough follows.',
    seeAlso: ['cascade'],
    source: 'authored'
  },
  'cascade': {
    term: 'CASCADE',
    short: 'an FK rule that deletes the child rows automatically when the parent row is deleted.',
    seeAlso: [],
    source: 'CONTEXT.md'
  }
};
```

- [ ] **Step 4: Add the drill-down framework.** Insert `[DRILLDOWN_JS]` after the `setSceneTitle(...)` function (~line 347) and before `function clearAllStates()`:

```javascript
/* =============================================================================
   TERM DRILL-DOWN — framework (reader-driven overlay, NOT scene state).
   Authoring only edits GLOSSARY above; never call these from a scene.
   ============================================================================= */
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
```

- [ ] **Step 5: Close the drawer on step change.** In `function render(step) {`, add `closeDrawer();` as the first line (before `clearAllStates();`):

```javascript
function render(step) {
  closeDrawer();
  clearAllStates();
  if (scenes[step]) scenes[step]();
```

- [ ] **Step 6: Add the wiring.** Insert `[WIRING_JS]` after the `resetBtn.onclick` handler (~line 465) and before `buildProgressDots();`:

```javascript
/* TERM DRILL-DOWN — wiring. Delegated on document so it survives narration innerHTML swaps. */
document.addEventListener('click', (e) => {
  const termEl = e.target.closest('[data-term]');
  if (termEl) { openTerm(termEl.dataset.term); return; }
  const hopEl = e.target.closest('[data-hop]');
  if (hopEl) { hopTerm(hopEl.dataset.hop); return; }
});
document.getElementById('drawerClose').onclick = closeDrawer;
document.getElementById('drawerBack').onclick  = backTerm;
```

- [ ] **Step 7: Seed demo terms into the demo scenes.**

Scene 0 — replace:
```javascript
      กด <strong>ถัดไป →</strong> เพื่อดู demo 3 steps. แทนที่ scenes ด้านล่างเพื่อสร้าง walkthrough จริง
```
with:
```javascript
      ทุก scene เป็น <span class="term" data-term="idempotent">idempotent</span> (ลองคลิกศัพท์ดูคำนิยาม)<br><br>
      กด <strong>ถัดไป →</strong> เพื่อดู demo 3 steps. แทนที่ scenes ด้านล่างเพื่อสร้าง walkthrough จริง
```

Scene 2 — replace:
```javascript
      <strong style="color:#ff8888">Rule 1 บอกว่า:</strong> เมื่อ family ลบ — ลบ transaction ทุกแถวที่ FamilyId ตรงกัน<br>
```
with:
```javascript
      <strong style="color:#ff8888">Rule 1 บอกว่า:</strong> เมื่อ family ลบ ให้ <span class="term" data-term="cascade">CASCADE</span> — ลบ transaction ทุกแถวที่ FamilyId ตรงกัน<br>
```

- [ ] **Step 8: Run the static checker — expect PASS**

Run:
```bash
python "<SCRATCH>/check_drilldown.py" "plugins/dev-workflows/skills/problem-description/template.html"
```
Expected: exit 0, prints `OK: 2 glossary terms, all references resolve, scenes clean`.

- [ ] **Step 9: Browser smoke test (Playwright MCP if available, else manual)**

`browser_navigate` → `file:///C:/Repo2/workflow%20daily%20work/plugins/dev-workflows/skills/problem-description/template.html`, then:
- Click `idempotent` (Step 0) → drawer opens, see-also "CASCADE", back hidden.
- Click "CASCADE" chip → header swaps to "CASCADE", source "จาก CONTEXT.md", back visible.
- Click `← ย้อน` → back to idempotent.
- Click `ถัดไป →` twice to reach Step 2, click the `CASCADE` term in the narration → drawer opens on "cascade".
- Click `↻ เริ่มใหม่` → Step 0, drawer hidden, rows/badges reset (no residue).

- [ ] **Step 10: Commit**

```bash
git add "plugins/dev-workflows/skills/problem-description/template.html"
git commit -m "feat(problem-description): add term drill-down drawer to tables template"
```

---

### Task 5: Document drill-down in SKILL.md

Teach the authoring workflow: source terms from CONTEXT.md, author the GLOSSARY, mark beyond-prerequisite terms, and verify.

**Files:**
- Modify: `plugins/dev-workflows/skills/problem-description/SKILL.md`

**Interfaces:**
- Consumes: nothing at runtime. Documents the surface produced in Tasks 3–4.

- [ ] **Step 1: Extend Phase 1** (after the "prerequisites" bullet block, before the "Then pick the mode" sentence). Add:

```markdown
4. **The unfamiliar terms** — list the terms the narration will use that fall *beyond*
   the prerequisites (domain jargon, schema names, project concepts). These become
   **drillable terms** (see Phase 4). Read the project's `CONTEXT.md` (or the mapped
   context via `CONTEXT-MAP.md`) and pull the definition for each term that exists there;
   for a beyond-prerequisite term **not** in the glossary, write a one-line definition
   yourself. A term the reader already knows is **not** made drillable — over-marking
   turns the narration into a sea of dotted underlines.
```

- [ ] **Step 2: Add a Phase 4 subsection** (after the Mode A / Mode B insertion-zone lists, before "**Critical rule** (both modes)"). Add:

```markdown
**Term drill-down (both modes).** Both templates ship a self-contained side drawer
(`#termDrawer`) plus a `GLOSSARY` object. To make a term drillable:

1. Add an entry to `GLOSSARY`, keyed by a stable slug:

   ```js
   'glasshull-scope': {
     term:    'glasshull scope',                 // display name in the drawer
     short:   'the records a workflow may touch in one transaction',  // CONTEXT.md wording or authored
     seeAlso: ['row-lock', 'transaction'],       // other GLOSSARY keys to hop to
     source:  'CONTEXT.md'                        // or 'authored' for a fallback definition
   }
   ```

2. In the narration, wrap the word: `<span class="term" data-term="glasshull-scope">glasshull scope</span>`.

Rules: `source: 'CONTEXT.md'` must quote the glossary; use `'authored'` only when the
term is absent from `CONTEXT.md` (and consider offering to add it there). The drawer is
**framework, not a scene** — never call `openTerm`/`closeDrawer`/`GLOSSARY` from a scene
function, and the no-`createElement`-in-scenes rule does **not** apply to the drawer's
own code. `render()` already calls `closeDrawer()` on every step change.
```

- [ ] **Step 3: Extend the Phase 5 self-test checklist.** After the existing last checkbox (the identifier-collision item), add:

```markdown
- [ ] **Drill-down referential integrity:** every `data-term="X"` has a `GLOSSARY[X]`
      entry, and every `seeAlso` key resolves to a `GLOSSARY` entry
- [ ] **Grounding:** every `GLOSSARY` entry marked `source: 'CONTEXT.md'` matches the
      glossary wording; `'authored'` is used only for terms absent from `CONTEXT.md`
- [ ] **Drawer is orthogonal:** no scene function references the drawer
      (`openTerm`/`closeDrawer`/`termDrawer`/`GLOSSARY`); `clearAllStates()` does not
      touch it; `Next` / `Prev` / `Reset` close the drawer and leave no residue
- [ ] **See-also hops:** clicking a see-also chip swaps the drawer; `← back` restores
      the prior term; with no `CONTEXT.md`, drillable terms still work via `authored`
      definitions
```

- [ ] **Step 4: Add Common Mistakes rows.** Append to the Common Mistakes table:

```markdown
| Invented term definitions instead of CONTEXT.md | Source from the project glossary; author a fallback only when the term is absent (ADR 0017). |
| Over-marking — every other word is drillable | Mark only terms *beyond* the reader's stated prerequisites. |
| A scene opens/closes/reads the drawer | The drawer is reader-driven framework, never scene state. Keep scenes pure. |
| `data-term` with no `GLOSSARY` entry (drawer no-ops) | Every `data-term` and `seeAlso` key must resolve to a `GLOSSARY` entry. |
```

- [ ] **Step 5: Commit**

```bash
git add "plugins/dev-workflows/skills/problem-description/SKILL.md"
git commit -m "docs(problem-description): document term drill-down authoring in SKILL.md"
```

---

### Task 6: Final verification against the spec's acceptance criteria

Confirm all 8 acceptance criteria on both shipped templates.

**Files:**
- Verify only: both templates + `SKILL.md`.

- [ ] **Step 1: Static checker on both templates**

Run:
```bash
python "<SCRATCH>/check_drilldown.py" "plugins/dev-workflows/skills/problem-description/template-diagram.html"
python "<SCRATCH>/check_drilldown.py" "plugins/dev-workflows/skills/problem-description/template.html"
```
Expected: both print `OK: 2 glossary terms, all references resolve, scenes clean` (exit 0). Covers criteria 1, 2, 3, 7 (scenes-clean half).

- [ ] **Step 2: Browser smoke test on both templates** (Playwright MCP, else manual), per Task 3 Step 9 and Task 4 Step 9. Covers criteria 4, 5, 6, 7 (residue), 8.

- [ ] **Step 3: Tick the spec's acceptance list.** Open the spec's "Verification / acceptance criteria" section and confirm each of the 8 boxes is satisfied by Steps 1–2:
  1. every `data-term` resolves — checker
  2. every `seeAlso` resolves — checker
  3. CONTEXT.md-sourced entries match wording — manual read (demo entries are authored/CONTEXT.md-tagged; for real walkthroughs this is the author's check)
  4. clicking a term opens the drawer — browser
  5. see-also swaps; back restores — browser
  6. Next/Prev/Reset close the drawer, no residue — browser
  7. no scene references the drawer; clearAllStates untouched — checker + read
  8. works with no CONTEXT.md via authored defs — the demo `'idempotent'` entry is `source:'authored'` and works — browser

- [ ] **Step 4: Confirm no regression to the existing demos.** In both templates, step 0→last with the drawer closed behaves exactly as before the change (diagram boxes light/arrows fire; tables rows/badges/rules update). The drawer must not alter stepping when untouched.

- [ ] **Step 5: Final commit (if any verification fixes were made)**

```bash
git add -A "plugins/dev-workflows/skills/problem-description/"
git commit -m "test(problem-description): verify term drill-down against acceptance criteria"
```

---

## Self-Review

**1. Spec coverage**

| Spec section | Task |
|---|---|
| §1 Content source (GLOSSARY, inlined, grounded-first, authored fallback) | Tasks 3.3, 4.3, 5.1, 5.2 |
| §2 Container (drawer, openTerm/closeDrawer/back-stack, see-also hop) | Tasks 1, 3.2–3.6, 4.2–4.6 |
| §3 Affordance (`.term` dotted-underline + accent + cursor) | `[CSS_BLOCK]` in Tasks 1, 3.1, 4.1 |
| §4 Idempotency (drawer outside scene state; render closes it) | `[RENDER_EDIT]` 3.5, 4.5; checker scenes-clean 2, 6 |
| §5 Which terms drillable (beyond prerequisites) | Task 5.1 |
| Changes to templates | Tasks 3, 4 |
| Changes to SKILL.md (Phase 1/4/5 + Common Mistakes) | Task 5 |
| 8 acceptance criteria | Task 6 |
| Suggested first build step (mockup) | Task 1 |
| Non-goals (no new modes / framework / render-verify) | Honored — none added |

No gaps.

**2. Placeholder scan:** No "TBD"/"handle edge cases"/"similar to Task N" — every code block is complete and repeated in full per task. The `[INSERT: ...]` strings remaining in the templates are the *templates'* own authoring placeholders (pre-existing, out of scope), not plan placeholders.

**3. Type consistency:** Function names are stable across all tasks and the checker: `openTerm`, `hopTerm`, `backTerm`, `closeDrawer`, `renderTerm`, global `GLOSSARY`, `drawerStack`. DOM ids stable: `termDrawer`, `drawerTerm`, `drawerSource`, `drawerDef`, `drawerSeeAlsoTitle`, `drawerSeeAlso`, `drawerBack`, `drawerClose`. Entry fields stable: `term`/`short`/`seeAlso`/`source`. The checker (Task 2) asserts exactly these. Consistent.

---

## Execution Handoff

(Filled in by the writing-plans handoff prompt after save.)
