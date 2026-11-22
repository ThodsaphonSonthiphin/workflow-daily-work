# A supporting diagram is never shown larger than it was drawn

```mermaid
flowchart TD
    Q{"A kit picture is drawn in a view box 540 units wide<br/>with 13px text. The kit CSS said width: 100%.<br/>In a full-width panel it came out 1349px wide,<br/>its text 32px beside 14px narration. How wide may it get?"}
    Q -->|chosen| A["width: 100% with max-width: 540px.<br/>Shown at its drawn size or smaller, never enlarged.<br/>Every kit picture uses a view box 540 units wide"]
    Q -->|rejected| B["Leave width: 100%: the picture fills the panel,<br/>2.5 times its drawn size on a desktop, and an activity<br/>diagram alone is taller than the screen"]
    Q -->|rejected| C["A cap per picture, set by the author:<br/>one more number to get wrong, and the kit rule<br/>is no authored CSS"]
```

Found by the Task 4 review, measured at 1440x900 on a diagram-mode page with both
skeletons shown: container 1385px, each picture 1349px wide (scale 2.50), picture text
32.5px, narration text 14.5px; the activity picture was 794px tall. The kit's own preview
page hid this, because its column is 560px wide.

`svg.uml` now has `max-width: 540px`. The kit's rule list says to draw in a view box 540
units wide. On a narrow page the picture still shrinks with its panel (309px wide on a
400px page). Measured after the change on the sequence demo: 540px in one column at
1024-1340px, 462-507px in the side column at 1341-1500px.
