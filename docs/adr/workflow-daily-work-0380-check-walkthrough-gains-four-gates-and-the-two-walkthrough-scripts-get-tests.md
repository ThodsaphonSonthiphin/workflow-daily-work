# check-walkthrough gains four gates, and the two walkthrough scripts get tests

```mermaid
flowchart TD
    Q{"The engine, a new pack and a new kit are changing.<br/>What stops a walkthrough being assembled from stale<br/>or half-used parts?"}
    Q -->|chosen| A["Four new gates in check-walkthrough.py, and a test file<br/>that assembles every pack's demo and runs the checker on it<br/>and on files built to fail each gate"]
    Q -->|rejected| B["Gates only, no tests: nothing shows that a gate can fail,<br/>and the two scripts have no test today"]
    Q -->|rejected| C["A browser test in the checker: needs a browser on every<br/>machine that authors a walkthrough, and the checker must run<br/>where only Python is present"]
```

`check-walkthrough.py` is the only safety net between assembly and the reader, and it is
static: it reads the assembled file and never runs it. It gains four gates.

1. **Keyboard.** The assembled script holds the engine's `keydown` listener and both arrow
   key names. Fails a walkthrough assembled from an engine copy that predates ADR 0356.
2. **Controls first.** The Previous button comes before the narration in the file. Fails an
   engine copy that predates ADR 0358.
3. **UML kit.** A kit class in the page needs the kit's CSS, and the kit's CSS needs at
   least one kit picture. Every picture declares its type and has a caption. There are at
   most three pictures (ADRs 0361, 0363, 0364).
4. **Sequence.** In the sequence mode the legend exists and every message declares its kind
   as `call`, `reply` or `self` (ADR 0363). The scene-id pass learns the sequence setters and
   reads ids from an array argument as well as from a string, so a mistyped id in either
   form still fails.

Neither `assemble-walkthrough.py` nor `check-walkthrough.py` has a test (measured
2026-11-21: no `test_*walkthrough*` file in the repo). A test file is added in
`plugins/dev-workflows/scripts/`, where the plugin's other script tests live. It assembles
the demo of each of the four packs and expects the checker to pass, and it builds one broken
file per gate and expects the checker to fail with that gate's message.

The behaviour a static check cannot see, such as a key press actually moving the step, was
measured once in a browser while this was designed and is measured again in the real viewer
at the end of the work (ADR 0367).
