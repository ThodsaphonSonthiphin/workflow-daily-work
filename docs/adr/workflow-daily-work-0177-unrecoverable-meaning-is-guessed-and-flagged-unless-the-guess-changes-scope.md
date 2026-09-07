# An unrecoverable meaning is guessed and flagged — unless the guess changes scope

```mermaid
flowchart TD
    Q{"Thai bare nouns carry no number, so 'delete<br/>the file in folder test' cannot tell one file<br/>from every file. The rewrite must not change<br/>the user's meaning, but here the meaning is<br/>not in the text to preserve. What then?"}
    Q -->|chosen| A["Guess the likely reading and FLAG the guess<br/>visibly - except where the guess would<br/>change the SCOPE of an instruction, where<br/>it stops and asks. One rule, one carve-out<br/>on the only case that is expensive to get<br/>wrong."]
    Q -->|rejected| B["Always ask. Never puts words in the user's<br/>mouth, but every bare noun is<br/>number-ambiguous and articles are the top<br/>error class in the evidence, so it fires<br/>constantly and the skill becomes an<br/>interrogation."]
    Q -->|rejected| C["Preserve the ambiguity - correct only what<br/>can be verified. Sounds honest, but English<br/>has no number-neutral noun: the output<br/>reads as definitely-singular, so it commits<br/>to a reading anyway, silently, which is<br/>worse than committing to one out loud."]
```

The research on ticket #16 established the mechanism: a Thai bare noun is unmarked for
number and for definiteness, and plurality is carried by a numeral-plus-classifier or a
quantifier that English does not require. When the user writes *the file*, the number is
not merely unstated — it was never encoded. There is nothing to preserve.

English offers no neutral form to fall back on, which is what disqualifies the
preserve-the-ambiguity option. Emitting *the file* is not a refusal to decide; it is a
decision to say singular, made silently. Between deciding silently and deciding out
loud, out loud wins.

Asking every time is correct and unusable. Articles and noun number are the two highest
frequency error classes in every study surveyed, so the ambiguity is not an edge case —
it is most sentences. A skill that halts on each one costs more attention than writing
the English by hand, which is the failure mode it exists to remove.

So: **guess the most probable reading, and mark the guess** where the user can see it,
so correcting it costs one word. **Except** when the guess would change the scope of an
instruction — how many things get deleted, which records get touched, whether an action
applies once or repeatedly. There the cheap-to-correct assumption stops holding, because
the message may be acted on before the flag is read, so the skill asks instead.

The carve-out is scoped to instruction scope specifically, not to some general notion of
risk: risk is unbounded and would collapse this back into always-ask.

This binds `build-fixer` (#22) and constrains #18, which must render a guess flag
distinctly from an error label — they are different claims. A guess says *I decided
something you did not say*; an error label says *you got this wrong*. Presenting them
alike would teach the user that their unmarked plural was a mistake, which
[ADR 0178](workflow-daily-work-0178-the-target-register-is-detected-per-message-not-fixed.md)
guards against in a different form.
