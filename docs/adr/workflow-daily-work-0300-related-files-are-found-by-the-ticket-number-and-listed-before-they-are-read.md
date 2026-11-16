# Related files are found by the ticket number and listed before they are read

```mermaid
flowchart TD
    Q{"how does the skill find the runbook and the<br/>related files of a ticket?"} -->|chosen| A["it searches the whole project for the ticket's number
    and each child's number - in file names, inside files
    (#151, AB#151, ado-151), in commit messages - and adds
    every file the ticket or the runbook names. It prints
    the list, then reads. No runbook found: it says so and
    asks for a path"]
    Q -->|rejected| B["the user names the paths every run - the number is
    already in the file names; asking costs a turn and
    misses the files the user forgot"]
    Q -->|rejected| C["a fixed list of folders - folder names differ by
    project (this one has documents/ and docs/), and a
    file outside the list is silently skipped"]
```

Ruled 2026-11-16 by the user (Pon), taking the recommended option. The number is matched as
a whole number with its usual prefixes, so `151` does not match `1510` or a date; a hit that
only shares the digits is dropped. Folders such as a snapshot directory are listed with a
file count and are not read file by file. "No runbook" is a stated fact in the briefing and
a question in the check - never a silent pass, because the runbook is where most written
test results live.
