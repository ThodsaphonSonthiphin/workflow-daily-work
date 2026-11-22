# A self-message loop is 48 wide and its label starts clear of it

```mermaid
flowchart TD
    Q{"The grid of ADR 0366 put a self-message's vertical edge<br/>at x + 72 and its label text at x + 80. The fitted label<br/>background starts 8 left of the text, on top of the edge:<br/>in every state that shows the label the loop was two loose stubs.<br/>The label also ran across the next lifeline. Where do they go?"}
    Q -->|chosen| A["Loop out to x + 52, label text at x + 68.<br/>The background starts at x + 60, 8 clear of the loop.<br/>The label has about 1000/N - 85 units before the next lifeline"]
    Q -->|rejected| B["Keep the loop at x + 72 and move the text to x + 88:<br/>the label gets shorter still and already crossed<br/>the next lifeline"]
    Q -->|rejected| C["Loop out to x + 40: the active arrowhead is 35 long<br/>and the way back is 30, so the loop reads as a blob<br/>(tried, seen in a browser)"]
    Q -->|rejected| D["Less padding left of a start-anchored label:<br/>a second fitting rule for one kind of message"]
```

Found by the Task 5 review, measured at step 5 of the demo: path
`M 379 318 L 447 318 L 447 346 L 385 346`, label background from x 445.8, covering about
83% of the edge at x 447; the background's right edge at 631.7 with the next lifeline at
625.

A self-message at row y on a lifeline at x is now
`M (x + 4) y L (x + 52) y L (x + 52) (y + 28) L (x + 10) (y + 28)` with its label text at
`x + 68, y + 19`. The demo's label is shortened to "4: make a 15-min token". Measured
after: loop edge at 427, label background from 433.8 to 594.9, next lifeline at 625. The
grid test now checks the self-message path and label position.
