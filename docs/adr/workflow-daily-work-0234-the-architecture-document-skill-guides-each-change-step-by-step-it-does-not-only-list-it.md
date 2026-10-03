# The architecture-document skill guides each change step by step — it does not only list it

```mermaid
flowchart TD
    Q{the skill finds a change that must happen before the<br/>new system can run - a missing SDK, a blocked port:<br/>does it only list the change, or also guide it?} -->|chosen| A["list it AND guide it — the document names what
    is missing, the owner and the test; the skill also
    walks the person through the change step by step
    and checks each step"]
    Q -->|rejected| B["list it only — what is missing, the owner, the
    test — and leave the change to the owning team's
    own procedure: recommended as the smaller copy;
    ruled out by the owner"]
```

Asked 2026-10-03 with a worked example — the SDK is missing on a server. Listing only
would put the change, its owner and its test in the document and leave the change to the
team that owns the server. That was the recommended option, because firewalls and
servers usually belong to other teams with their own procedures, and because guiding a
change is the work `guide-and-verify` already does. The owner chose the other one: the
skill lists the change and also guides the person through it step by step, and checks
each step.

The consequence lands on ADR 0231: the copy grows. The steps that guide a change — the
fixed step shape, one action per line, the before-state snapshot, the apply step as its
own line, the after-check in a second channel — are now necessary and are copied into
the new skill. The first list of steps to copy had the before-state snapshot as not
needed; that no longer holds. `guide-and-verify` is still neither loaded nor edited.
