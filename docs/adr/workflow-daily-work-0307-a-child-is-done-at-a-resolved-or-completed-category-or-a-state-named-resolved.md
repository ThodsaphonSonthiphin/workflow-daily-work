# A child is done at a Resolved or Completed category, or at a State named Resolved

```mermaid
flowchart TD
    Q{"which Azure DevOps States count as done for a<br/>child ticket? The measured process puts the State<br/>named Resolved in category InProgress"} -->|chosen| A["done when the State's category is Resolved or
    Completed, or the State is named Resolved whatever
    its category. Removed stays out of the verdict"]
    Q -->|rejected| B["category only, as ADR 0298 first said - in the
    measured process only Closed would count, so every
    parent with a Resolved child would read NOT READY;
    the user resolves work and rarely closes it"]
    Q -->|rejected| C["a fixed list of names (Resolved, Closed, Done) -
    a custom process with another final name would never
    count as done"]
```

Ruled 2026-11-16 by the controller during execution of the resolve-the-ticket plan, after
Task 1 measured the State categories of type User Story in MackayGoodwin/Elevate: New ->
Proposed, Active -> InProgress, Resolved -> InProgress, Closed -> Completed, Removed ->
Removed. The name `Resolved` is added because it is the State this skill gates: a child that
was itself set to Resolved has passed the same check the parent is about to pass. Amends the
done rule of ADR 0298, which stays in force otherwise. GitHub is unchanged: `closed` is done.
