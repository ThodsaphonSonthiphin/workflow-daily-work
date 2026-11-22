# The checker reads sequence state names, and setLife takes an array

```mermaid
flowchart TD
    Q{"Two calls passed the checker and did nothing in the page:<br/>setLife(['lfUser','lfApi'], 'active') - the checker read the array,<br/>setLife took one id - and setMsg('m1', 'firing'),<br/>a lifeline state given to a message. What stops them?"}
    Q -->|chosen| A["setLife takes one id or an array, like setMsg.<br/>The scene pass checks the state name of every<br/>setLife and setMsg call against the states the pack styles"]
    Q -->|rejected| B["Read an array only after setMsg: the natural next line<br/>after setMsg(['m1','m2'], ...) still fails, now with an error,<br/>when it could simply work"]
    Q -->|rejected| C["Warn in the page at run time: the checker never runs<br/>the page, and nobody reads the console of a walkthrough"]
    Q -->|rejected| D["Leave both parked: a silent no-op is the one failure<br/>the scene pass exists to catch"]
```

Found by the whole-branch review, each measured on a scratch copy of the demo: with
`setLife(['lfUser', 'lfApi'], 'active')` the checker exited 0 and all four lifelines kept
the class `seq-life`; with `setMsg('m1', 'firing')` the checker exited 0 and the arrow
stayed unlit. The two state lists differ on purpose (`magic` on a message, `locked` and
`firing` on a lifeline), which makes the mix-up easy.

`setLife(ids, state)` now loops over `[].concat(ids)`. `check-walkthrough.py` has a pass
F3 beside the scene-id pass: lifeline states `active, firing, locked, blocked, done, error,
dimmed`, message states `active, done, error, magic, dimmed`, and the empty string for
both. A state built at run time is not read, the same limit as a built id. One test
with two cases covers the state check; a text test pins the setLife loop. An earlier ruling had parked the state check; this replaces it.
