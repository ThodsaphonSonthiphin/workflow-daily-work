#!/usr/bin/env node
// Checks a flashcard page built from assets/flashcards-template.html.
// Usage: node check_flashcards.js <page.html>
// It runs the page script with a stub DOM, then lints DECKS, CARDS and every Mermaid source.
// Exit 0 = no issues, 1 = issues found, 2 = the script does not parse or run.
'use strict';
const fs = require('fs');
const vm = require('vm');

const file = process.argv[2];
if (!file) { console.error('usage: node check_flashcards.js <page.html>'); process.exit(2); }
const html = fs.readFileSync(file, 'utf8');

const issues = [];
for (const ph of ['{{TITLE}}', '{{SUBTITLE}}', '{{STORE_KEY}}']) {
  if (html.includes(ph)) issues.push(`placeholder ${ph} not replaced`);
}

const start = html.lastIndexOf('<script>');
const end = html.lastIndexOf('</script>');
if (start < 0 || end < start) { console.error('no inline <script> found'); process.exit(2); }
let code = html.slice(start + 8, end).replace(/restart\(\);\s*$/, '');
code += '\n;globalThis.__out = { DECKS, CARDS };';

const proxy = () => new Proxy(function () {}, { get: () => proxy(), apply: () => proxy() });
const sandbox = {
  window: {}, console,
  MutationObserver: function () { return { observe() {} }; },
  getComputedStyle: () => ({ getPropertyValue: () => '' }),
  localStorage: { getItem: () => null, setItem() {} },
  document: { documentElement: {}, addEventListener() {}, querySelectorAll: () => [], getElementById: () => proxy() }
};
sandbox.globalThis = sandbox;
try {
  vm.runInNewContext(code, sandbox, { filename: 'page-script.js' });
} catch (e) {
  console.error('script error: ' + e.message);
  process.exit(2);
}
const { DECKS, CARDS } = sandbox.__out;

const deckIds = new Set(DECKS.map(d => d.id));
const seen = new Set();
for (const c of CARDS) {
  const where = `card ${c.id || '(no id)'}`;
  if (!c.id) issues.push(`${where}: missing id`);
  if (seen.has(c.id)) issues.push(`${where}: duplicate id`);
  seen.add(c.id);
  if (!deckIds.has(c.deck)) issues.push(`${where}: deck "${c.deck}" not in DECKS`);
  if (c.kind !== 'logic' && c.kind !== 'fact') issues.push(`${where}: kind must be logic or fact`);
  if (!c.q) issues.push(`${where}: missing q`);
  if (!c.src) issues.push(`${where}: missing src`);
  if (c.kind === 'logic') {
    if (!c.chart) issues.push(`${where}: logic card without a Mermaid chart`);
    if (!c.ex) issues.push(`${where}: logic card without a real example (ex)`);
  }
  if (c.kind === 'fact' && !c.a) issues.push(`${where}: fact card without an answer (a)`);
  if (c.chart) {
    const m = c.chart;
    if (!/^flowchart (TD|TB|LR|RL|BT)\b/.test(m)) issues.push(`${where}: chart must start with "flowchart TD" (or LR)`);
    const bare = m.replace(/<br\/>/g, '');
    if (/#/.test(bare)) issues.push(`${where}: "#" in chart (Mermaid reads it as an entity) - write "ticket 148"`);
    if (/;/.test(bare)) issues.push(`${where}: ";" in chart ends a statement`);
    if (/<(?!br\/>)/.test(m.replace(/<br\/>/g, '<br/>').replace(/<br\/>/g, ''))) issues.push(`${where}: "<" in chart other than <br/>`);
    if (((m.match(/"/g) || []).length) % 2) issues.push(`${where}: odd number of double quotes`);
    m.split('\n').slice(1).forEach((line, i) => {
      const t = line.trim();
      if (!t || /^(subgraph|end$|classDef|class |style |%%)/.test(t)) return;
      // Node text in [..] {..} (..) must be quoted when it has spaces or symbols.
      const noStrings = t.replace(/"[^"]*"/g, '""');
      const unq = noStrings.match(/\w+(\(\[|\[|\{|\()([^"\[\(\]\}\)][^\]\}\)]*)(\]\)|\]|\}|\))/);
      if (unq && /[^\w ]/.test(unq[2])) issues.push(`${where}: line ${i + 2} node label with symbols not in double quotes: ${t}`);
    });
  }
}
for (const d of DECKS) {
  if (!CARDS.some(c => c.deck === d.id)) issues.push(`deck ${d.id}: no cards`);
}

console.log(`decks ${DECKS.length} · cards ${CARDS.length} · logic ${CARDS.filter(c => c.kind === 'logic').length} · fact ${CARDS.filter(c => c.kind === 'fact').length}`);
if (issues.length) { console.log('ISSUES:\n- ' + issues.join('\n- ')); process.exit(1); }
console.log('no issues');
