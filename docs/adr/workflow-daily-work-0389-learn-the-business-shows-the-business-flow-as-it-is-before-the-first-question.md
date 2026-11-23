# learn-the-business shows the business flow as it is before the first question

```mermaid
flowchart TD
    Q{"what does the person see<br/>before the first question?"} -->|chosen| A["the Business flow: the work as it runs today<br/>around the part - one or two steps before it,<br/>the part, one or two after - shown once per sitting"]
    Q -->|rejected| B["at most three lines of evidence, as before - the<br/>skill reads the flow in its ground search and the<br/>person never sees it, so the answer is a guess"]
    Q -->|rejected| C["the whole program, mapped first - still the long<br/>survey ADR 0371 turned down; the flow here is<br/>three to seven lines around one part"]
    Q -->|rejected| D["show the flow only after a wrong answer - the<br/>person is judged on a guess first, and the<br/>result in the note records nothing they know"]
    Q -->|rejected| E["hand off to feynman-explain or asking-to-understand<br/>first - two skills to load before one question, and<br/>both teach the mechanism, not who hands work to whom"]
```

Ruled 2026-11-23 by the user, after using the skill: "ไม่ได้สอน existing flow ก่อนถาม". The
ground search of step 1 already gave the skill the flow; only the person lacked it. The flow
is shown once per sitting, a later question repeats the one line it is about, and the flow
is shown again only when the Backward chain steps to a part that is not on it.

ADR 0371 is unchanged in what it chose - the first question is still about the part the
person is touching, and the chain still walks backward. Its rejected "mapped first" branch
stays rejected: that was a map of the whole program.

The practice this follows is current-state ("as-is") analysis before any question about
change, and showing a worked example to a newcomer before testing them. Both are named here
as *general knowledge*; no source was read for them in the session that made this ruling.
