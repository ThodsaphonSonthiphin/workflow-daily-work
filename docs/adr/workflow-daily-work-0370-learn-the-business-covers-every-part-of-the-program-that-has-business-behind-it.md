# learn-the-business covers every part of the program that has business behind it

```mermaid
flowchart TD
    Q{"what may the skill ask about?"} -->|chosen| A["every part with a business decision behind it, in six<br/>kinds: data, process, rule, people, output, connection.<br/>A part the platform made (createdon, an id) is<br/>skipped and listed on one line"]
    Q -->|rejected| B["tables and fields only - the user corrected this:<br/>'ไม่ได้ถามแค่ table กับฟิว ทุกอย่างที่ business<br/>เกี่ยวกับโปรแกรม'"]
    Q -->|rejected| C["every part in order, system parts too - most answers<br/>would be 'the platform made it', and the person<br/>stops trying"]
```

Ruled 2026-11-21 by the user. The six kinds are an open set: data (table, field, choice
value, relationship), process (flow, job, trigger), rule (condition, threshold, validation,
default), people (role, permission, recipient), output (report, email, screen), connection
(external system, API). A part of a new kind is added to the list, not forced into one.
