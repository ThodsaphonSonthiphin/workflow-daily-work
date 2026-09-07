# The progress signal is the quiet list, shown on request

```mermaid
flowchart TD
    Q{"Every count in the profile only ever goes<br/>UP, and nothing records how much the user<br/>wrote. With no denominator, 'fewer errors<br/>this week' is not computable. What can be<br/>reported honestly?"}
    Q -->|chosen| A["The QUIET LIST - the classes that have not<br/>fired in a long time, read straight off<br/>`lastSeen`. A fact, not an inference, and it<br/>needs no denominator. Shown ON REQUEST, so<br/>it never lengthens the card."]
    Q -->|rejected| B["Count of collapsed classes. Reads like a<br/>progress bar and measures ATTENDANCE:<br/>collapse counts exposure days, so it climbs<br/>to 9/9 for a user who learned nothing."]
    Q -->|rejected| C["Add a counter so a rate exists. One integer,<br/>but the denominator wanted is words written,<br/>not corrections run - and the destination<br/>ruled a measured-improvement dataset out of<br/>scope. This is the first step onto it."]
    Q -->|rejected| D["No signal at all. Defensible, but the profile<br/>holds one true fact - which rules have gone<br/>quiet - and refusing to say a true thing<br/>because a different thing would be false is<br/>more caution than the evidence requires."]
```

The profile cannot answer the question it is most often asked. `count`, `distinctDays` and
every `byRegister` figure are **cumulative** — they only rise. And nothing anywhere records
how much English the user wrote, so there is no denominator: a falling weekly count is
indistinguishable from writing less, writing shorter messages, or writing in Thai instead.

One thing in the store *can* fall, and it is the useful one. **`lastSeen` goes stale.** A
class that has not fired in three weeks is a fact — a date, not a division — and it happens
to be the more useful half of what a person wants to know. "Which rules have gone quiet"
locates where you stand better than any total does.

So the signal is a **quiet list**: the classes not seen in a long time, each with how long,
and beside them the classes still firing. Both halves matter; a list of only successes is a
different and worse artefact.

**Shown on request only.** [ADR 0179](workflow-daily-work-0179-the-correction-card-is-lesson-first-and-explains-every-change.md)
chose the lesson-first card and two ADRs since have fought to keep it short. A progress
block on every correction would push the lesson down for something the user did not ask for,
and progress is not a thing anyone needs reported five times a day.

The collapsed-class count was the tempting headline and is the trap: **collapse counts
exposure days, not correctness**. A class collapses because its explanation was shown ten
times, so that number climbs steadily whether or not anything was learned, and reaches 9/9
for a user who never improved.

**How long is "a long time"? The relapse gap, and no new number.**
[ADR 0184](workflow-daily-work-0184-a-class-explanation-collapses-after-n-and-returns-on-relapse.md)
already defines quiet: a class relapses when it fires again after **14 quiet days**, so this
system already holds an opinion about how long silence must last before it means something.
The quiet list uses that same threshold rather than inventing a fourth guessed number.

This keeps the two halves consistent by construction. A class crossing into the quiet list is
exactly a class that would count as a **relapse** if it fired tomorrow — the same fact
reported forward instead of backward. Had the thresholds differed, the skill could have
called a class quiet and then declined to treat its return as a relapse, or the reverse, and
nothing would have flagged the contradiction.

If the relapse gap is ever tuned, the quiet list moves with it. That is intended.
