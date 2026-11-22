# A supporting diagram must answer a question the main diagram cannot, and three is the most

```mermaid
flowchart TD
    Q{"When does a walkthrough get a supporting UML diagram,<br/>and how many?"}
    Q -->|chosen| A["Only when a step raises a question the main diagram cannot<br/>answer. The author writes that question in one sentence and<br/>it becomes the caption. At most three in a walkthrough.<br/>None is a correct number"]
    Q -->|rejected| B["At least one in every walkthrough: a problem with no question<br/>about structure or conditions gets a picture added<br/>to meet the rule"]
    Q -->|rejected| C["No limit: the panels turn into a gallery and pull<br/>the reader's eye off the main diagram"]
```

The walkthrough published on 2026-11-20 had three supporting diagrams in seventeen steps, and each
answered something its sequence diagram could not show: where a field lives (class), what
is checked before a value is given out (activity), and how two ways of keying a record
differ (class). That is the rule. The skill picks the type from the
question:

| The step asks | Supporting diagram |
|---|---|
| what the data looks like, which field holds it, how many to how many | class diagram |
| what is checked, in what order, and where the path splits | activity diagram |

In Phase 1 the author lists each planned supporting diagram with the one-sentence question
it answers. A diagram without such a sentence is not drawn. Three is the most, because that
is what the one real walkthrough needed; a walkthrough with none is complete.
