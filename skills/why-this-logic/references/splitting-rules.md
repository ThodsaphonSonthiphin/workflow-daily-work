# Splitting rules - what is one decision point

One decision point is the smallest thing that could have its own source. If two parts of
a line could have come from two different tickets, two different people or two different
years, they are two rows.

## Split

| in the thing | one row each |
|---|---|
| `a and b`, `a or b` | each term |
| `x > 30`, `status eq 914120001` | the comparison **and** the literal, when the literal could come from somewhere other than the comparison (a threshold from a ticket, a code from an option set); otherwise one row |
| `rate = 0.15`, `"Vehicles"`, `MG_ReminderAgeDays (7)` | the literal |
| a default - `= 0`, `?? "UNMATCHED"`, `Default No` | the default |
| a branch - `if / else`, `case`, `switch` | the branch condition; the literals inside the body get their own rows |
| a filter in a ticket, a query in a flow, a mapping in a config, a rule in a document | the same rules - the thing need not be code |

## Do not split

- `i < list.length`, `item != null`, a loop guard - mechanics with no separate source: one
  row, or none.
- Two literals that the same sentence of the same source fixes together (`Mon-Fri 08:00`)
  - one row, citing that sentence.

## Always

- **Row 0 is the origin of the text itself** - the commit, the generating script, the
  template, the person who wrote the ticket body. On a ticket whose body a script
  produced, row 0 is what shows the ticket is a copy.
- Quote each decision point **as written** - the exact operator, the exact literal, the
  exact field name - so the row can be found again.
- Cap a run at the rows the user pointed at. More than about twelve: say so, and ask which
  part to trace first.

## Worked split - `Elevate` #151

```
and (mgw_loggingstatus eq 914120001 or mgw_loggingstatus eq 914120003)
```

| row | decision point |
|---|---|
| 0 | origin of the story text |
| 1 | `and (mgw_loggingstatus … )` - why the filter has this term at all |
| 2 | `914120001` and `914120003` - what the two numbers mean (one row: the same option set maps both; two rows if the sources turn out to differ) |

Row 1 and row 2 have different answers: the spec's Workflow 3 never names the field
(row 1: no source), and the spec defines the field by label only (row 2: cannot check
from the document).
