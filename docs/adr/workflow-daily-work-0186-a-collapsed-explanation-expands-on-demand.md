# A collapsed explanation expands on demand

```mermaid
flowchart TD
    Q{"Once a class has collapsed to its short<br/>form, the user may still want to know why a<br/>change was made. Is relapse the only route<br/>back to the full explanation?"}
    Q -->|chosen| A["No - the user can ask, and the full Thai<br/>explanation returns for that class without<br/>changing its collapse state. The text<br/>already exists; withholding it would be a<br/>restriction the design never needed."]
    Q -->|rejected| B["Relapse only. Fewer moving parts and it<br/>keeps the card strictly honest about what<br/>the user still needs - but it answers a<br/>direct question with silence, and the one<br/>thing this skill must never do is refuse<br/>to explain."]
```

Collapsing an explanation is a judgement about what the user needs *by default*. It should
never become a judgement about what they are allowed to see. A skill whose purpose is
teaching cannot answer "why did that change?" with "you have seen this ten times already".

So asking expands: the full mechanism text for that class comes back for the message at
hand. The cost is near zero, because the canonical Thai sentence for every class already
has to exist — ticket #25 makes it a maintained asset — so expanding is retrieval, not
generation.

**Asking does not reset the collapse state.** Curiosity is not relapse. Only making the
mistake again after a quiet stretch restores the full form by default
([ADR 0184](workflow-daily-work-0184-a-class-explanation-collapses-after-n-and-returns-on-relapse.md)),
and keeping those two paths separate is what stops a user who reads carefully from being
punished with a permanently longer card.
