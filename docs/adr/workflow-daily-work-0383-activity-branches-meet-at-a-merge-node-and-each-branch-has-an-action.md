# Activity branches meet at a merge node, and each branch has an action

```mermaid
flowchart TD
    Q{"The activity skeleton drew the [yes] flow and the [no] flow<br/>straight into one action, and the [no] branch was a line<br/>with loose text beside it. In UML an action with two flows in<br/>waits for both, so that action could never start.<br/>How do branches come back together?"}
    Q -->|chosen| A["At a merge node: a diamond with two flows in,<br/>one flow out and no guard. Each branch has its own action.<br/>The subset of ADR 0363 gains the merge node"]
    Q -->|rejected| B["Keep the subset without a merge: each branch runs<br/>to the final node on its own. The picture can then not<br/>show that both branches give the same answer,<br/>which is the question it is there to answer"]
    Q -->|rejected| C["Leave it: every author copies the skeleton,<br/>and the copy teaches a join where a merge is meant"]
```

Found by the Task 4 review. ADR 0363 exists so that a picture that says UML on screen
follows the notation. The skeleton now reads: find the user, decide, `[yes]` make a token
and send the link, `[no]` make nothing and send nothing, merge, answer 200 OK, end. The
loose text "nothing made, nothing sent" is gone: it is the action on the `[no]` branch.

The rule is in three places an author reads: the kit's rule list, SKILL.md's notation
section and SKILL.md's pre-delivery checklist. The caption tells the reader the two
diamonds apart by their arrows: two out is a decision, two in is a merge. The sequence
demo carries the same picture. A test counts two diamonds in the activity skeleton.
