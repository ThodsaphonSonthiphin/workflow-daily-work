# The skill description stays under the listing cap, with the forward clause first

```mermaid
flowchart TD
    Q{the description grew to ~2,040 characters; Claude Code<br/>truncates the skill listing at 1,536 (description +<br/>when_to_use) and the Agent Skills spec caps it at 1,024} -->|chosen| A["rewrite to about 1,000 characters: both directions in
    the first sentence, the forward clause before the Thai
    backward phrases, the verdict and status words intact,
    the broad triggers ('traceability', 'มี test ไหม') dropped
    so the skill does not steal other skills' prompts"]
    Q -->|rejected| B["keep the long text and move the forward clause earlier
    - still over the listing cap, so whatever sits last is
    cut, and the 1,024 spec limit stays broken"]
    Q -->|rejected| C["keep it as it was - the forward triggers began at
    character ~1,511 and would never reach the model"]
```

Ruled 2026-10-30 at the whole-plan review, after the limit was measured in the docs
(code.claude.com/docs/en/skills.md: "truncated at 1,536 characters in the skill listing";
agentskills.io/specification: "Max 1024 characters"). House precedent had drifted past
1,024 (`guide-and-verify` ~1,941) but under 1,536; this skill is the first to be cut by
the listing cap, so it is the first to be written to the spec limit.
