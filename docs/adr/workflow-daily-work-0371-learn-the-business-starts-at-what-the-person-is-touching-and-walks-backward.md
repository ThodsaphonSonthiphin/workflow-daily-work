# learn-the-business starts at what the person is touching and walks backward

> **Added to 2026-11-23 by ADR 0389:** the first question is no longer the first thing the
> person sees. The skill now shows the Business flow - three to seven lines around the part -
> before it. What this ADR chose is unchanged, and its rejected "mapped first" branch stays
> rejected: that was a map of the whole program.

```mermaid
flowchart TD
    Q{"called with no argument,<br/>where do the questions start<br/>and where do they go next?"} -->|chosen| A["the first question is about what the person is<br/>working on now; each next question is one step<br/>backward - the part this one reads, depends on or<br/>exists because of"]
    Q -->|rejected| B["the whole program, mapped first - complete, but a long<br/>survey before question one and questions far from<br/>today's work; still possible when asked for by name"]
    Q -->|rejected| C["ask every time: this work or the whole program -<br/>one more step on every run"]
    Q -->|rejected| D["unrelated questions picked from a list - the person<br/>never sees how the parts join"]
```

Ruled 2026-11-21 by the user: "คำถามแรก เกี่ยวกับสิ่งที่ทำ ไล่ถามส่วนที่เกี่ยวข้องไปเรื่อยๆ
แบบย้อนกลับ". The start is read from the uncommitted changes, the branch's ticket and the
session; the skill names what it picked in its first line, so a wrong pick costs one line.
An argument (a ticket URL, a part's name, "the whole program") always wins.
