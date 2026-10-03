# A change — the eight steps

> This method was copied from `guide-and-verify` on 2026-10-03 and is kept here separately
> (ADR 0231). Edit it here; nothing loads the original.

A **change** is one thing a person must do before a row can pass: install software, open a
firewall rule, create an account. You do not make it. You write it, the person makes it, and you
prove that it landed.

Every change runs the same eight steps, in this order, one change at a time. Never run two
changes together: batching saves a few minutes and costs an afternoon when something breaks and
nobody knows which change did it.

## 1. Who acts

Name the owner of this change — the user, or a team — and say the boundary again when the owner
is new to the run: you read and you test; they change. If the owner is not in the session, the
change is handed over; see *A change that belongs to another team* below.

## 2. Measure before

Run the row's read-only check now, or ask the person to run it and paste the output. Write the
result into the row, with the time.

**Never write a step from a document.** A ticket, a wiki page and your own notes from yesterday
were true when written and drift silently. Only the live system says where it is today. If the
check shows that the change is already in place, record that and skip the change.

## 3. Save the before-state

For everything this change touches, save its full present state before the person acts — not
only the one value the test will read:

- software on a server: the installed software with its versions, and the state of every service
  the old system runs on that server;
- a firewall rule: the present rules between the two zones, or the export the network team can
  give;
- an account or a permission: the account's present memberships and grants.

The test proves *whether* something moved; only the before-state shows *what*. Do this even when
the change looks reversible: an undo you cannot name the target of is not a recovery.

Commands that read the state of a server:

```
# Windows, in PowerShell
Get-ItemProperty HKLM:\Software\Microsoft\Windows\CurrentVersion\Uninstall\* |
  Select-Object DisplayName, DisplayVersion
Get-Service | Where-Object Status -eq Running

# Linux
dpkg -l          # or: rpm -qa
systemctl list-units --type=service --state=running
```

**Put it where it outlives the session** — beside the document, attached to the ticket, or in a
directory the document names. A before-state in a scratch folder dies with the session and
leaves the next person as blind as if you had never taken it.

**Ask first only when it needs the person.** If you can read the state yourself, take it and say
that you took it. If it needs their hands or a permission you do not hold, ask in one line: *"I
will save the present state of `<what>` first — is that all right?"* Only an explicit no is a
decline; a vague reply, a changed subject and silence are not. On an explicit no, write *"no
before-state, by the owner's decision"* in the record of the change, and carry that label into
every later claim about it.

A before-state never holds a secret.

## 4. State the expected result, and what must not change

Write both before the person acts.

- **The expected result** — what the row's test must print afterwards: *no `8.0.` line → a line
  that starts with `8.0.`*; *`TcpTestSucceeded : False` → `True`*. A result with no target
  written beforehand is a description, not a check: you will read it and decide it looks fine.
- **What must not change** — name the neighbours and measure them now: the services of the old
  application still run; the runtime the old application uses is still installed; the other
  rules between the two zones are the same. This is what catches the change that did one thing
  too many, which no success check ever does.

**A predicted outcome is a claim, and it needs evidence like any other.** "The installer does not
restart the web server" is a claim about a product. Confirm it in the vendor's documentation, or
by a probe, before it enters a step. A wrong prediction is worse than none: the person reads a
correct result as a failure, or a broken one as a pass.

## 5. Give the steps, one at a time, in the fixed shape

One step is one reversible unit of work. Use this shape every time — the person learns it once
and then reads it fast:

```
## Step N — <what this achieves, in plain words>

**Go to:** <a real address, a server name, or an exact navigation path>

**Do:**
1. <one action>
2. <one action>

**Do not:**
- <thing> — <why, in one clause>

**How to verify yourself:** <a read-only check the person can run alone>

**Then report:** <who to tell, and where the result is written down>
```

Rules that make the shape work:

- **One action per numbered line.** "Download the installer, run it and restart the service" is
  three lines.
- **A real address beats a description.** Give the server name, the URL, the exact path. If it
  may not resolve, give it anyway and add the route as a fallback in one line.
- **Every "do not" carries its reason.** A prohibition without a reason gets ignored the moment
  it is inconvenient.
- **Name the destructive near-miss.** The dangerous instruction is not the one you gave; it is
  the thing next to it that looks the same. If they add a rule for one port, name the rule
  beside it that must not be touched, and say what happens if it is.
- **Order by dependency, and say when order does not matter.** People reorder steps that look
  independent. If step 2 must follow step 1, say why in half a sentence.
- **Never batch.** One step, verify, then the next.
- **Say when a step is one-way.** Before it, add a numbered line that reads the present value
  and writes it somewhere retrievable, and say plainly that the action cannot be undone. A
  person who knows a step is one-way reads it twice.
- **Aim the report line at whoever will actually be there.** In a live session it is *"tell me,
  and I run the test"*. In a change that lands days later it names a destination that outlives
  the session — the row, a ticket.

Keep the prose short. The person reads it with a console open in the other window.

## 6. Check after

When the person reports the change done, run the row's test again and report before → after.
Check the expected result **and** what must not change.

**Check through a different channel from the one they changed it in.** If they clicked in a
console, read the machine state — a command, an export, a query. The console they edited in is
the one surface guaranteed to show what it thinks it just saved. For a connection, the different
channel is the test itself, run from the row's From part: the firewall console says the rule
exists; only the test says that traffic passes.

**When there is no second channel**, say so and change the wording. The result is
*"reported by the operator, not independently measured"* — never "measured". Write it into the
row with that label; the row stays open.

## 7. A mismatch stops the work

If the check does not give the expected result — or something that must not change did change —
and every part of the change is recorded as done, that is a **problem**. Stop, and go to *A
problem* below. Never tell the person to try again: a half-applied change is the common outcome,
and a redo on top of it makes it worse.

If the check fails because a part of the change is not done yet — the rule is requested but not
approved — that is not a problem. The change is still in progress.

## 8. Record the result

Write the result into the row: the value, the date and time, and who ran the check. Mark the
change **checked**. "Done" is worth little. *"Done — `dotnet --list-sdks` shows an 8.0 line; the
three services of the old application still Running; measured 2026-10-10 09:14 by the server's
administrator"* is worth the whole session.

Then give the person the check they can run without you — one command, one look. They will meet
this system again when you are not there.

## Saved is not applied

Most things a person changes have two states: the change that exists, and the change that is
live. A plain test reads the live state, so a change that is saved but not applied reads as
"nothing happened". People then redo correct work, or decide the tool is broken.

| What was changed | Saved | Live | What closes the gap |
|---|---|---|---|
| A firewall rule | approved, or saved in the management console | active on the firewall | on many firewalls, a commit, a push or an install of the policy |
| A DNS record | edited | resolving for the servers that ask | time — the old answer is cached until it expires |
| Software on a server | installed | used by the running service | a restart of the service; a new session for a changed PATH |
| A database account | created | able to read | the grant on the tables |
| A cloud network rule | saved | in effect on the interface | time, usually short |

Find out which one you are dealing with before you write the step, because they need different
instructions: an apply action is its **own numbered line**, never a clause inside another line;
a delay is a warning not to redo work that already succeeded. Tell the person that their own
check doubles as an apply-detector: *"if the old result is still there, it is not applied
yet."*

## A change that belongs to another team

The person who makes the change is often not in the session — the network team opens the
firewall rule — and the change may land days later. Such a change gets the same eight steps,
written for a reader who has only the document:

- every identifier in full: source, destination, port, protocol, the name of the rule;
- nothing that points back at the session — no "as discussed", no "the server above";
- a report line that names where the result is recorded: the row, or a ticket;
- its after-check recorded as owed until someone runs the test.

Set the status of the change to **handed over**. One line — "ask the network team to open the
port" — is not a hand-over: the team has to work out source, destination and port again, and
afterwards nobody can say whether it was done.

## A problem — hand off to debug-mantra

A problem is a test that fails when every change it needs is recorded as done. It is the one
moment where something misbehaved and a person is about to act on a guess — a second firewall
request, a reinstall. Do not diagnose by improvising, and never propose a redo on an unverified
cause. Hand off to `debug-mantra`, in this order.

**1. The Freeze line goes out first.** Before the mantra, before any question, the person reads:

> Test failed: row `<ID>` expected `<expected>`, got `<result>`.
> Do not redo the change or alter anything on either system — a redo destroys the state that
> tells not-saved from not-applied from wrong-object. I am finding out why first.

Then load `debug-mantra` through your harness's mechanism and follow it as written. Its recital
stays verbatim and complete; only the Freeze line comes before it. What changes is what you
already hold when it opens.

**2. What you already hold, per step** — do not ask the person for any of it:

| debug-mantra step | you already have |
|---|---|
| ① reproduce | the row's test and its recorded results — the failing test is the repro. The environment is the one the document names; there is no "local or deployed?" to ask |
| ② fail path | the layers between the two ends of the connection — name resolution, route, each firewall, the host's own firewall, the listener, TLS, the account and its permission — and the numbered lines of the change just made |
| ③ falsify | **hypothesis #1 is always saved-is-not-applied.** Read the pending state first; the table under *Saved is not applied* says where it lives. Rank the rest yourself |
| ④ breadcrumbs | the results already written in the rows, each with its date — a half-applied change shows as two of them that contradict each other |

**3. No second channel.** The hand-off fires anyway. Step ① is met by one read-only look that
the person takes and pastes back. A read-only look is not a redo: the Freeze line forbids
changes, not looks. That run, and every claim built on it, carries the label
*reported by the operator, not independently measured*.

**4. A second problem in the same run.** The run is one debug session. Send the Freeze line
again and re-enter at step ①. Do not recite the mantra a second time, and keep the ledger: the
earlier runs are still evidence, because the systems and the people are the same.

**5. When the cause is confirmed.** Write a **Corrected step** in the fixed shape — the missing
apply as its own numbered line — asserted against the failed measurement as its baseline. If the
cause was yours — a wrong expected output, a wrong prediction — say so; the corrected thing is
then the document. Write the cause and both times into the row: *"C-01 failed 09:14 — cause:
rule saved, not pushed; corrected step landed 09:31, False → True"*. If the cause is a real
defect in a system and not a missed action, name it as such, stop the change there, and leave
the run for the debug chain: fix, post-mortem, report.

## Write for someone who is tired

Short sentences. One instruction per sentence. Plain words. Use the person's own words for their
systems. Do not editorialise about risk in the steps: put the reason in the "do not" clause and
move on.
