# A click on a step dot goes to that step

```mermaid
flowchart TD
    Q{"The numbered step dots only show where the reader is.<br/>Should they also move the reader?"}
    Q -->|chosen| A["A click on dot N renders step N"]
    Q -->|rejected| B["Dots, and also step links inside the narration:<br/>needs a new attribute in authored narration and a<br/>check that the step number exists. Wait for a<br/>walkthrough that the dots do not serve"]
    Q -->|rejected| C["Leave the dots as indicators: going from step 12 back<br/>to step 9 and returning costs six key presses"]
```

A narration sometimes sends the reader back ("look again at check 2 in the activity diagram,
step 9"). With only Previous and Next that is three presses back and three forward. A click
on a dot now sets the current step to that dot's number and renders it.

Jumping is safe because every scene describes the whole page state and the engine clears the
mode before it runs a scene; no scene depends on the scene before it having run. The dots
are built by the engine, so every mode gets this and no mode pack changes.
