# The Business flow is plain lines of person, action and handoff, with no reason on them

```mermaid
flowchart TD
    Q{"what shape does the<br/>Business flow take?"} -->|chosen| A["three to seven numbered text lines: who, does what,<br/>whom the work goes to; a Source mark on every line;<br/>the part's line marked 'you are here';<br/>what happens, never why"]
    Q -->|rejected| B["a Mermaid or BPMN diagram - the flow is read in<br/>the chat, where a diagram language may show as<br/>source text; and BPMN's symbols must be learned first"]
    Q -->|rejected| C["the flow of the code: trigger, filter, action -<br/>that is the mechanism, asking-to-understand's ground,<br/>and it never reaches a person"]
    Q -->|rejected| D["a paragraph of prose - no step numbers for the<br/>question to point at, and no place for one<br/>Source mark per fact"]
    Q -->|rejected| E["the reasons written on the flow - the question<br/>then has nothing left to ask, and ADR 0369's<br/>answer-before-reveal is lost"]
```

Proposed by Claude and accepted by the user on 2026-11-23, with ADR 0389. The line shape -
a person, one action, a handoff - is the sentence shape of Domain Storytelling, taken as
*general knowledge*; none of that method's notation is used.

The diagram convention (ADRs 0005-0009) covers Markdown documents a skill generates. The
Business flow is chat output and is written to no file, so it is outside that convention.

A step no source states is written with `?` and the mark *assumed*, and becomes a question
for the client when the flow is shown (ADR 0373 already sends every *assumed* line there).
The person is a role in the client's business; `ระบบ` is written only where the program acts
with nobody behind it. A table name or an expression never stands in for a person - a
`path:line` appears only inside the mark.
