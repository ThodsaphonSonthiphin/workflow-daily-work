# Ways to meet a need

Read this in Phase 4, when a need has no way yet. You propose; the user chooses. The choice is
an architecture decision, and the architecture is theirs — you never pick the way yourself. You
may say in one sentence which way the facts favour, and why.

## How to propose

For one need, show the ways that can work as a small table in the user's own words: the way, one
advantage, one cost. Keep each to one line. When a fact rules a way out, say so and name the fact
with its mark — *"no API: the old HR system has none (told)"* — and do not offer that way as an
option. Then ask which way they choose, and wait for the answer.

## The four common ways

| Way | Advantage | Cost |
|---|---|---|
| **Call the old system's API** | the data is always current | the old system must have an API |
| **Read the old database directly** | quick to build | a table change in the old system breaks the new one |
| **Copy the data on a schedule** | the old system carries load only during the copy | the data lags behind the old system |
| **Share the login system** | no second copy of the passwords | covers login and basic account data only |

A way outside these four may be proposed when a need calls for it — a file drop, a message
queue. Give it one advantage and one cost, like the rest.

## What each way adds to the document

Once the user has chosen, the way decides which rows you write in Phase 5.

| Way | Connection rows | Prerequisite rows | Changes | The need's own test |
|---|---|---|---|---|
| Call the old system's API | the new system to the API's host and port | none | an API account or key; a firewall rule if the path is blocked | one real call that returns one real item, made as the real account |
| Read the old database directly | the new system to the database server and its port | the database client or driver on the new system's server | a read-only account; a grant on the tables or the view; a firewall rule if the path is blocked | one row read as the real account, from the new system's server |
| Copy the data on a schedule | the machine that runs the copy to the old system, and to the new system's store | whatever the copy job runs on | the job; an account for it; a firewall rule if a path is blocked | one copied item is in the new store, and its age is within the agreed lag |
| Share the login system | the new system to the directory or sign-in service and its port | none | a service account, or an application registration | one real sign-in by a real account |

Whatever the way, the need is proven at two levels: its connections answer, **and** its own test
passes. A port that answers is not the test.

## Questions that sharpen a need before you propose

Ask only the ones that the answers so far leave open:

- Does the new system only read the thing, or also change it?
- How fresh must it be — at the moment of use, or as of last night?
- Who owns the thing in the old system, and who can approve access to it?
- Is it personal data? If it is, the owner's approval is part of the change, not an afterthought.
