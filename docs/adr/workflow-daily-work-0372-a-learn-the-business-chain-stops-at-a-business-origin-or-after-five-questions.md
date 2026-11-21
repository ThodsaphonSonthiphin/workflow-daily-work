# A learn-the-business chain stops at a business origin or after five questions

```mermaid
flowchart TD
    Q{"when does the backward chain stop?"} -->|chosen| A["at a business origin - a person, money, a law or a<br/>contract, with nothing in the program behind it - or<br/>after five questions, whichever is first; 'continue'<br/>goes on; a branch not taken is written in the note"]
    Q -->|rejected| B["only at the business origin - some chains are<br/>eight to ten questions long"]
    Q -->|rejected| C["only after five questions - the sitting can end<br/>one step before the answer that explains the rest"]
```

Ruled 2026-11-21 by the user. A chain also stops where no source says more; that point is a
question for the client (ADR 0373). The five is borrowed from `practice-english-writing`'s
sitting and rests on no evidence. Where a chain forks, one branch is walked and the others
are noted as not yet asked.
