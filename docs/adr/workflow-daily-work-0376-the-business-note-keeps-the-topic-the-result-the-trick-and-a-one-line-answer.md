# The business note keeps the topic, the result, the trick and a one-line answer

```mermaid
flowchart TD
    Q{"what does one row of the note hold,<br/>and what does the next run do with it?"} -->|chosen| A["date, the part, how the person answered, the trick,<br/>and the answer in one line with its source mark.<br/>A weak row is asked again after 3 days when the part<br/>is touched again; a row whose ADR or code changed<br/>since is marked 'may be old'"]
    Q -->|rejected| B["the topic only - what the user literally asked for,<br/>but the searched answer and its source are thrown away"]
    Q -->|rejected| C["topic and result, no answer line - re-asking works,<br/>but the file cannot be read as a review sheet or<br/>handed to learn-with-flashcard"]
```

Ruled 2026-11-21 by the user. The file has two more lists, from ADRs 0372 and 0373: branches
not yet asked, and questions for the client or BA. It is Markdown, the person may edit it,
and their edit wins. The 3 days rest on no evidence.
