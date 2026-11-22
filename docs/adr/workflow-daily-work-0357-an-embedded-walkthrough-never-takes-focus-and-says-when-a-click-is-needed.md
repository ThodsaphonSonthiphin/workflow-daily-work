# An embedded walkthrough never takes focus, and says when a click is needed

```mermaid
flowchart TD
    Q{"Inside an iframe (a published artifact, an editor preview)<br/>the arrow keys reach the walkthrough only after it has focus.<br/>What does the walkthrough do about that?"}
    Q -->|chosen| A["It never calls focus itself. While the document<br/>does not have focus it shows one line:<br/>click this page once to use the arrow keys.<br/>The line goes away when the document gets focus"]
    Q -->|rejected| B["Call window.focus() when the page loads:<br/>it takes focus away from the host page, for example<br/>from a chat box the person is typing in"]
    Q -->|rejected| C["Do nothing: the keys are dead until the first click<br/>and the reader cannot tell why"]
    Q -->|rejected| D["Always show the line: on a page opened directly<br/>the keys already work, so the line is wrong there"]
```

A key event goes to the document that has focus. A walkthrough opened directly in a browser
has focus from the start. A walkthrough shown inside an iframe does not: the host page has
it until the reader clicks inside the frame. The engine therefore shows a hint line next to
the controls when `document.hasFocus()` is false, and hides it on the window's `focus`
event and shows it again on `blur`. The hint is engine chrome, like the step badge; no
scene sets it.

Where the hint sits and how it is hidden changed in ADR 0381: it has a row of its own
under the buttons and turns invisible, so nothing moves when the page gets focus.

The engine does not call `window.focus()`. A page that takes focus when it loads, or when
the host reloads it, moves the caret out of whatever the person was typing in.
