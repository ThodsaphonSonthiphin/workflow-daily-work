# The arrow keys are proved in the real viewer with a published demo

```mermaid
flowchart TD
    Q{"A local browser test cannot show that the arrow keys work<br/>inside the claude.ai artifact viewer. How is that proved?"}
    Q -->|chosen| A["Publish the sequence pack's assembled demo as a new private<br/>artifact. The owner opens it and presses the arrow keys once"]
    Q -->|rejected| B["Rebuild the 2026-11-20 walkthrough on the new pack and<br/>publish over its URL: also proves the example can be rebuilt,<br/>but it is extra work and it changes an artifact that belongs<br/>to another project and holds that project's client data"]
    Q -->|rejected| C["Test locally only, with a simulated iframe: leaves the one<br/>environment the complaint came from unmeasured"]
```

The complaint that started this work was made about a walkthrough shown in the claude.ai
artifact viewer, which embeds the page in an iframe. Automated tests run in a local browser:
they can prove the listener, the modifier-key guard and the focus hint on a page opened
directly and on a page inside a local iframe. They cannot open the real viewer.

So the last step of the work is a measurement by a person. The sequence pack's demo, which
contains only invented data, is published as a new private artifact, and the owner checks
three things: the hint shows before the first click, the arrow keys step after it, and the
hint is no longer visible. The result is recorded with the work. The 2026-11-20 artifact is not
touched.

Result, 2026-11-22: the sequence demo built from the branch was published as a new private artifact and the owner tried it in the claude.ai viewer: the left and right arrow keys step the walkthrough. (The owner reported the keys; the hint line was not reported on separately.)
