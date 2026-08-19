# Copies are found by scanning derived roots, not a declared manifest

```mermaid
flowchart TD
    Q{how does the audit learn<br/>where the copies are?} -->|chosen| A["scan - walk derived roots for
    directories holding a SKILL.md whose
    name matches a source skill; finds
    copies nobody registered"]
    Q -->|rejected| B["a manifest in the source repo naming
    each consumer - exact, fast, reviewable
    in git, but it only ever lists the
    copies somebody remembered to add,
    and the unlisted copy is the one that
    silently drifts"]
```

The problem being solved is that copies exist which nobody is tracking. A manifest
answers a different question - *are the copies I know about current?* - and would
have stayed silent about exactly the case that prompted this work.

The scan pays for that reach with false positives: a directory named after one of our
skills may belong to an unrelated project. That cost is not accepted, it is removed -
ADR 0107 grades every hit by content provenance, so a name match alone can never be
reported as our drift. With that in place the scan's only remaining cost is time,
which the prune list and the derived roots of ADR 0108 keep bounded.
