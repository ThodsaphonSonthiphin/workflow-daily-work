#!/usr/bin/env python3
r"""local_map_ops.py — decision-map local-markdown backend (ADR 0042).

Map lives at <root>/<slug>/map.md, tickets at <root>/<slug>/tickets/<slug>.md.
Contract: plugins/decision-map/references/data-contracts.md. Stdlib only.

Re-chart policy (review round 1, Critical finding): `chart(real=True)` onto a
map folder that already has files on disk REFUSES by default, raising
ChartConflictError before writing anything — a previous chart's recorded
state (claims, resolutions, blocking edges) can never be silently destroyed
by an accidental re-run. Pass force=True (CLI: --force) to explicitly opt
into overwriting every existing file with fresh content — an intentional,
informed action, never a silent one. `chart(real=False)` (the default dry
run) always reports the SAME policy a real run would apply, labeling every
planned file "create" / "OVERWRITE" / "refuse", so the human approval gate
is truthful about what a real run would do.

THE MARKER INVARIANT (review round 4, finding N1) -- the one rule the whole
module rests on:

    Every decision-map marker in a generated file was written by this
    module, because every user-supplied string is escaped on the way in.

Enforced, not asserted. `_scrub()` escapes the marker prefix in every
user-supplied string before it reaches a file, and every write goes through
`_assert_one_region()`, which refuses to write a file that does not hold
exactly zero or one well-formed marker region. That is what lets
`resolve()` find the block it owns by searching for its own markers: the
search can no longer match user text, because user text can no longer
contain a marker. See the marker constants below for the three rounds of
failure that establish why nothing weaker works.

`inp` is validated before any file is written (in both dry-run and real
mode): `map` must have every field chart() reads unconditionally
("title", "destination"), every ticket must have every field chart() reads
unconditionally ("key", "title", "type", "question"), each of those must be
a *string* and not merely present (round 4 finding N2 -- `title: [1, 2]`
used to raise TypeError from _fm_dump after map.md and the first ticket
were already on disk, and `title: null` / a dict / an int / `question:
null` were silently accepted and written), the map's own `target.slug` and
every ticket `key` must each be a safe slug (letters/digits/`-`/`_` only,
anchored to the exact end of the string with `\Z` -- not `$`, which in
Python also matches just before a trailing newline and would let e.g.
"okname\n" slip through as a path segment), every ticket `type` must be one
of the four valid types, and every `blocks` target must be a key present in
this same `inp`. A malformed map_input.json fails cleanly with
ChartValidationError instead of writing a half-finished map folder or
crossing outside the intended root (round 3 finding R3: a ticket missing
"title" or "question" used to raise a bare KeyError mid-write, leaving
exactly the half-finished folder this paragraph claims can't happen --
required-field validation closes that gap).
"""
import argparse, json, re, sys
from pathlib import Path

AFK_TYPES = {"research"}
VALID_TICKET_TYPES = {"research", "prototype", "grilling", "task"}

# Ticket keys AND the map's own target.slug all become path segments
# (<root>/<slug>/... , tickets/<key>.md) -- restrict both to a safe slug so
# neither can ever escape the intended root (e.g. "../../pwned",
# "C:/Windows/Temp/pwned"). Anchored with \Z, not $: in Python, `$` also
# matches just before a trailing newline, so "okname\n" would otherwise
# pass here and only fail later -- as an OSError while writing the ticket
# file, after map.md was already on disk (review round 2, finding N3).
_SAFE_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]*\Z")

# The only frontmatter key that is ever written/read as a list. Every other
# key is a plain (one-line) string, even if its value happens to start with
# "[" and end with "]" (see ChartValidationError / _fm_parse docstring).
_LIST_FM_KEYS = {"blocked_by"}

# ---------------------------------------------------------------------------
# Generated-region markers, and the invariant that makes them trustworthy.
#
# Every generated region in a generated file is delimited by a marker comment
# pair that ONLY this module writes: resolve() owns the span between the
# resolution markers in a ticket file, and the "Decisions so far" index in
# map.md is the span between the decisions markers.
#
# Four review rounds established that finding the region by pattern-matching
# the file is the wrong half of the problem to work on:
#   round 1  append-only            -> duplicate blocks stacked
#   round 2  "## Resolution.*\Z"    -> deleted a user comment
#   round 2b lookahead to "\n## "   -> a --body-file's own "## Rationale"
#                                      orphaned the tail (unbounded growth);
#                                      "## Resolution" inside Question prose
#                                      was deleted on the FIRST resolve
#   round 3  these markers          -> same mechanism, longer needle: a marker
#                                      pasted into question/gist/link/body/
#                                      comment reproduced BOTH harms, and the
#                                      code claimed immunity "by construction"
#                                      while nothing enforced the premise
# The needle was never the problem. What was missing is the write side:
# _scrub() below escapes the marker prefix in every user-supplied string, so
# a marker in a file is proof this module put it there. _assert_one_region()
# then checks that promise on every single write. Widening or re-anchoring
# the search pattern is NOT a fix -- it is round 5.
_MARKER_PREFIX = "<!-- decision-map:"
# "&lt;" is Markdown/HTML's own escape for a literal "<", so the scrubbed text
# still RENDERS as the marker the user typed -- it just stops being an HTML
# comment, and stops matching. Escaping, not mangling. Idempotent: the
# escaped form no longer contains _MARKER_PREFIX, so re-scrubbing is a no-op
# and repeated read/modify/write cycles cannot cascade.
_MARKER_ESCAPED_PREFIX = "&lt;!-- decision-map:"

_RESOLUTION_START = "<!-- decision-map:resolution:start -->"
_RESOLUTION_END = "<!-- decision-map:resolution:end -->"
_DECISIONS_START = "<!-- decision-map:decisions:start -->"
_DECISIONS_END = "<!-- decision-map:decisions:end -->"


def _region_re(start, end):
    return re.compile(
        re.escape(start) + r".*?" + re.escape(end) + r"\n?", re.DOTALL)


_RESOLUTION_BLOCK_RE = _region_re(_RESOLUTION_START, _RESOLUTION_END)
_DECISIONS_BLOCK_RE = _region_re(_DECISIONS_START, _DECISIONS_END)


class ChartConflictError(Exception):
    """chart(real=True) would overwrite existing map/ticket files and
    force=True was not passed. Raised before anything is written."""


class ChartValidationError(ValueError):
    """map_input.json failed validation. Raised before anything is written."""


class MarkerIntegrityError(Exception):
    """A file about to be written does not hold exactly zero or one
    well-formed generated region. Raised INSTEAD of writing, so the module
    refuses rather than corrupts. Every string this module writes is
    scrubbed, so reaching this means either a bug here (a new user-input
    path that forgot _scrub) or a hand-edited file with stray markers."""


def _scrub(value):
    """Escape every decision-map marker in a user-supplied string.

    This is the write-side half of the marker invariant, and the reason
    resolve()'s region search is safe: after this, no user-supplied byte in
    any generated file can be read back as a marker. Apply it to EVERY
    string that originates outside this module -- question, title,
    destination, notes, fog/out-of-scope lines, comment bodies, gist, link,
    resolution body, assignee, blocked-by. `None` becomes "".
    """
    s = "" if value is None else str(value)
    return s.replace(_MARKER_PREFIX, _MARKER_ESCAPED_PREFIX)


def _assert_one_region(text, start, end, what):
    """Refuse to write `text` unless it holds 0 or 1 well-formed regions.

    The backstop for _scrub(): if a future change adds a user-input path and
    forgets to scrub it, this fails loudly at the write instead of silently
    losing user content on some later resolve() -- which is exactly how the
    same defect survived three fix rounds.
    """
    n_start, n_end = text.count(start), text.count(end)
    problem = None
    if n_start > 1 or n_end > 1:
        problem = f"{n_start} start / {n_end} end markers (expected at most one of each)"
    elif n_start != n_end:
        problem = f"unpaired markers ({n_start} start, {n_end} end)"
    elif n_start and text.index(start) > text.index(end):
        problem = "end marker precedes start marker"
    elif text.count(_MARKER_PREFIX) != n_start + n_end:
        problem = (f"{text.count(_MARKER_PREFIX)} decision-map marker(s) present but only "
                   f"{n_start + n_end} belong to this region")
    if problem:
        raise MarkerIntegrityError(
            f"refusing to write {what}: {problem}. Every string this module writes is "
            "escaped, so this indicates hand-edited markers in the file (remove them) "
            "or an unscrubbed input path (a bug in this module).")


def _mode(ticket_type):
    return "AFK" if ticket_type in AFK_TYPES else "HITL"


_REQUIRED_MAP_FIELDS = ("title", "destination")
_REQUIRED_TICKET_FIELDS = ("key", "title", "type", "question")


def _require(where, container, field, kind, required):
    """Presence + TYPE check for one field, returning its value (or None when
    an optional field is absent/null).

    Presence-only validation was round 4's finding N2: `title: [1, 2]`
    reproduced R3's partial-folder harm through a wrong type instead of a
    missing key, and `title: null` / a dict / an int were written silently.
    `null` counts as absent for an optional field and as invalid for a
    required one.
    """
    if field not in container or (container[field] is None and not required):
        if required:
            raise ChartValidationError(f"{where} is missing required field {field!r}")
        return None
    value = container[field]
    if kind is str:
        if not isinstance(value, str):
            raise ChartValidationError(
                f"{where}: field {field!r} must be a string, "
                f"got {type(value).__name__} ({value!r})")
    else:  # list of str
        if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
            raise ChartValidationError(
                f"{where}: field {field!r} must be a list of strings, got {value!r}")
    return value


def _validate_chart_input(inp):
    """Validate `inp` before chart() writes anything (dry-run or real).

    - the top-level containers must be the right shape (a missing/mistyped
      "target"/"map"/"tickets" used to raise a bare KeyError/AttributeError
      rather than the ChartValidationError the docstring promises)
    - map_input's "map" must have every field chart() reads unconditionally,
      and each must be a string (round 3 finding R3 for presence; round 4
      finding N2 for type)
    - every ticket must likewise have every field chart() reads
      unconditionally, each a string (round 3 R3 -- a missing
      "title"/"question" used to raise a bare KeyError mid-pass-1, after
      map.md and earlier tickets were already on disk; round 4 N2 --
      `title: [1, 2]` did the same thing via _fm_dump's ", ".join)
    - optional fields, when present and not null, must be their declared
      type: "notes" a string, "notYetSpecified"/"outOfScope"/"blocks" lists
      of strings
    - target.slug must be a safe slug (round 2 finding N2 -- previously
      unvalidated; "../../pwned-slug" and "C:/Windows/Temp/pwned-slug" both
      wrote outside the intended root)
    - every ticket key must be a safe slug (no path separators / '..')
    - every ticket type must be one of the four valid types
    - every `blocks` target must be a key present in this same `inp`
    """
    if not isinstance(inp, dict):
        raise ChartValidationError(
            f"map_input.json must be a JSON object, got {type(inp).__name__}")
    for name in ("target", "map"):
        if name not in inp:
            raise ChartValidationError(f'map_input.json is missing required key "{name}"')
        if not isinstance(inp[name], dict):
            raise ChartValidationError(
                f'map_input.json\'s "{name}" must be an object, '
                f"got {type(inp[name]).__name__}")
    if "tickets" not in inp:
        raise ChartValidationError('map_input.json is missing required key "tickets"')
    if not isinstance(inp["tickets"], list):
        raise ChartValidationError(
            f'map_input.json\'s "tickets" must be a list, '
            f"got {type(inp['tickets']).__name__}")

    slug = _require('map_input.json\'s "target"', inp["target"], "slug", str, True)
    if not _SAFE_SLUG_RE.match(slug):
        raise ChartValidationError(
            f"invalid map slug {slug!r}: must be a safe slug "
            "(letters, digits, '-', '_'; no path separators, drive letters, or '..')")

    m = inp["map"]
    where_map = 'map_input.json\'s "map"'
    for field in _REQUIRED_MAP_FIELDS:
        _require(where_map, m, field, str, True)
    _require(where_map, m, "notes", str, False)
    for field in ("notYetSpecified", "outOfScope"):
        _require(where_map, m, field, list, False)

    keys = set()
    for i, t in enumerate(inp["tickets"]):
        if not isinstance(t, dict):
            raise ChartValidationError(
                f"tickets[{i}] must be an object, got {type(t).__name__}")
        where = f"ticket {t.get('key', f'#{i}')!r}"
        for field in _REQUIRED_TICKET_FIELDS:
            _require(where, t, field, str, True)
        key = t["key"]
        if not _SAFE_SLUG_RE.match(key):
            raise ChartValidationError(
                f"invalid ticket key {key!r}: must be a safe slug "
                "(letters, digits, '-', '_'; no path separators or '..')")
        if t["type"] not in VALID_TICKET_TYPES:
            raise ChartValidationError(
                f"ticket {key!r}: invalid type {t['type']!r}; "
                f"must be one of {sorted(VALID_TICKET_TYPES)}")
        _require(where, t, "blocks", list, False)
        keys.add(key)
    for t in inp["tickets"]:
        for blocked in t.get("blocks") or []:
            if blocked not in keys:
                raise ChartValidationError(
                    f"ticket {t['key']!r} blocks unknown ticket {blocked!r} "
                    "(not present in this map_input's tickets)")


def _fm_parse(text):
    """Parse the leading --- frontmatter block into a dict.

    Only keys in _LIST_FM_KEYS (currently just "blocked_by") are parsed as a
    list; every other key is kept as a plain string even if its value starts
    with "[" and ends with "]" — a title like "[spike] rollout order [v2]"
    or a gist like "[deferred to ADR 0007, see notes]" must round-trip
    unchanged, not be silently coerced into a list (review round 1 finding).
    """
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    fm = {}
    if not m:
        return fm, text
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        k = k.strip()
        v = v.strip()
        if k in _LIST_FM_KEYS:
            if v.startswith("[") and v.endswith("]"):
                inner = v[1:-1].strip()
                fm[k] = [s.strip() for s in inner.split(",") if s.strip()]
            else:
                fm[k] = []
        else:
            fm[k] = v
    return fm, text[m.end():]


def _fm_value(v):
    """One frontmatter value, escaped and flattened to a single line.

    The marker invariant's choke point for frontmatter: no frontmatter value
    is ever generated content, so every one of them is scrubbed here rather
    than at each caller (title, gist, assignee, blocked-by entries ...).
    """
    s = _scrub(v)
    # Frontmatter here is one physical line per key. An embedded newline
    # would otherwise either truncate the value (the rest silently dropped
    # on read) or corrupt a later key's parse (review round 1 finding) —
    # collapse it to a space instead. It also guarantees the map.md index
    # entries built from these values are exactly one line each.
    return s.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")


def _fm_dump(fm):
    lines = []
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(_fm_value(x) for x in v)}]")
        else:
            lines.append(f"{k}: {_fm_value(v)}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def _ticket_path(root, slug, ticket):
    return Path(root) / slug / "tickets" / f"{ticket}.md"


def _load_ticket(root, slug, ticket):
    text = _ticket_path(root, slug, ticket).read_text(encoding="utf-8")
    return _fm_parse(text)


def _save_ticket(root, slug, ticket, fm, body):
    text = _fm_dump(fm) + body
    # THE enforcing line for the ticket half of the marker invariant: every
    # write of every ticket, from every subcommand, passes through here.
    _assert_one_region(text, _RESOLUTION_START, _RESOLUTION_END,
                       f"ticket {ticket!r}")
    _ticket_path(root, slug, ticket).write_text(text, encoding="utf-8")


def _write_map_md(path, text):
    """THE enforcing line for the map.md half of the marker invariant."""
    _assert_one_region(text, _DECISIONS_START, _DECISIONS_END, "map.md")
    path.write_text(text, encoding="utf-8")


def _ticket_json(root, slug, ticket):
    fm, _ = _load_ticket(root, slug, ticket)
    return {
        "key": ticket, "id": ticket,
        "name": fm.get("title", ticket),
        # forward slashes always -- backslash is Markdown's escape character,
        # so a Windows-native path here would break every [name](url) link
        # (review round 1 finding).
        "url": (Path(root) / slug / "tickets" / f"{ticket}.md").as_posix(),
        "type": fm.get("type", "grilling"), "mode": fm.get("mode", "HITL"),
        "status": fm.get("status", "open"),
        "assignee": fm.get("assignee") or None,
        # Output shape uses "blockedBy" (upstream blockers); the on-disk
        # frontmatter key stays "blocked_by" (see _load_ticket / _save_ticket).
        "blockedBy": fm.get("blocked_by", []),
        "gist": fm.get("gist") or None,
    }


def _all_tickets(root, slug):
    tdir = Path(root) / slug / "tickets"
    return sorted(p.stem for p in tdir.glob("*.md")) if tdir.exists() else []


def _chart_plan(base, inp, force):
    """Return an ordered list of (Path, action) for every file chart() would
    touch. action is one of:
      - "create"    the file doesn't exist yet
      - "OVERWRITE" the file exists and force=True (destructive, explicit
                    opt-in)
      - "refuse"    the file exists and force=False (default) — a real run
                    will raise ChartConflictError rather than touch anything
    """
    targets = [base / "map.md"] + [
        base / "tickets" / (t["key"] + ".md") for t in inp["tickets"]]
    plan = []
    for p in targets:
        if p.exists():
            plan.append((p, "OVERWRITE" if force else "refuse"))
        else:
            plan.append((p, "create"))
    return plan


def chart(root, inp, real, force=False):
    """Bulk-create (or explicitly re-chart, with force=True) a map + its
    tickets. See the module docstring for the full re-chart policy."""
    _validate_chart_input(inp)
    slug = inp["target"]["slug"]
    base = Path(root) / slug
    plan = _chart_plan(base, inp, force)
    if not real:
        print("DRY RUN — planned files:")
        for p, action in plan:
            print(f"  {action} {p}")
        return {"backend": "local", "dryRun": True,
                "planned": [{"path": str(p), "action": action} for p, action in plan]}
    conflicts = [p for p, action in plan if action == "refuse"]
    if conflicts:
        raise ChartConflictError(
            "chart: refusing to overwrite existing file(s) without "
            "force=True/--force: " + ", ".join(str(p) for p in conflicts))
    (base / "tickets").mkdir(parents=True, exist_ok=True)
    m = inp["map"]
    fog = "\n".join(f"- {_scrub(x)}" for x in (m.get("notYetSpecified") or [])) or "- (none)"
    oos = "\n".join(f"- {_scrub(x)}" for x in (m.get("outOfScope") or [])) or "- (none)"
    _write_map_md(
        base / "map.md",
        f"# {_scrub(m['title'])}\n\n"
        "```mermaid\ngraph TD\n    MAP[\"map (this file)\"] --> T[\"tickets/*.md — one decision each\"]\n"
        "    T --> D[\"Decisions so far (index below)\"]\n```\n\n"
        f"## Destination\n{_scrub(m['destination'])}\n\n"
        f"## Notes\n{_scrub(m.get('notes') or '')}\n\n"
        # The index under this heading is a GENERATED region, delimited so
        # resolve() can rebuild it without pattern-searching the rest of the
        # file. Before round 4 it substituted a "- [..](tickets/<key>.md)"
        # line regex over the whole of map.md, so an index-shaped line a user
        # wrote in `notes` was silently overwritten by the resolution gist
        # (the map.md instance of finding N1's root cause).
        f"## Decisions so far\n\n{_DECISIONS_START}\n{_DECISIONS_END}\n\n"
        f"## Not yet specified\n{fog}\n\n"
        f"## Out of scope\n{oos}\n")
    # pass 1: create tickets; pass 2: wire blocking (create-then-wire, spec §9).
    # Safe because _validate_chart_input already confirmed every `blocks`
    # target is one of this map_input's own ticket keys, so pass 2 can never
    # hit a ticket file that pass 1 didn't just create.
    for t in inp["tickets"]:
        fm = {"title": t["title"], "type": t["type"], "mode": _mode(t["type"]),
              "status": "open", "assignee": "", "blocked_by": [], "gist": ""}
        _save_ticket(root, slug, t["key"], fm,
                     f"\n## Question\n\n{_scrub(t['question'])}\n")
    for t in inp["tickets"]:
        for blocked in t.get("blocks", []):
            block(root, slug, blocked, t["key"])
    return read_map(root, slug)


def read_map(root, slug):
    map_md = (Path(root) / slug / "map.md").read_text(encoding="utf-8")
    title = map_md.splitlines()[0].lstrip("# ").strip()
    dest = ""
    dm = re.search(r"## Destination\n(.+?)(\n\n|\n##)", map_md, re.DOTALL)
    if dm:
        dest = dm.group(1).strip()
    return {"backend": "local",
            "map": {"id": slug, "name": title,
                    "url": (Path(root) / slug / "map.md").as_posix(),
                    "destination": dest},
            "tickets": [_ticket_json(root, slug, t) for t in _all_tickets(root, slug)]}


def frontier(root, slug):
    out = {"frontier": [], "blocked": [], "claimed": []}
    tickets = {t: _ticket_json(root, slug, t) for t in _all_tickets(root, slug)}
    for key, t in tickets.items():
        if t["status"] != "open":
            continue
        open_blockers = [b for b in t["blockedBy"]
                         if b in tickets and tickets[b]["status"] == "open"]
        if t["assignee"]:
            out["claimed"].append({"id": key, "name": t["name"], "assignee": t["assignee"]})
        elif open_blockers:
            out["blocked"].append({"id": key, "name": t["name"], "blockedBy": open_blockers})
        else:
            out["frontier"].append({"id": key, "name": t["name"],
                                    "url": t["url"], "type": t["type"]})
    return out


def claim(root, slug, ticket, user):
    fm, body = _load_ticket(root, slug, ticket)
    fm["assignee"] = user
    _save_ticket(root, slug, ticket, fm, body)
    return {"claimed": ticket, "assignee": user}


def block(root, slug, ticket, blocked_by):
    fm, body = _load_ticket(root, slug, ticket)
    deps = fm.get("blocked_by", [])
    if blocked_by not in deps:
        deps.append(blocked_by)
    fm["blocked_by"] = deps
    _save_ticket(root, slug, ticket, fm, body)
    return {"ticket": ticket, "blockedBy": deps}


def comment(root, slug, ticket, body_text):
    fm, body = _load_ticket(root, slug, ticket)
    _save_ticket(root, slug, ticket, fm,
                 body + f"\n## Comment\n\n{_scrub(body_text)}\n")
    return {"commented": ticket}


def _reindex_decisions(root, slug):
    """Rebuild map.md's "Decisions so far" index from the ticket files.

    The index is a projection of the tickets, not accumulated state, so it is
    regenerated wholesale inside its own marker region. There is no per-line
    pattern to match and nothing outside the region is read or touched --
    which is what stops a user-authored, index-shaped line elsewhere in
    map.md (in `notes`, say) from being substituted away, and stops a
    multi-line gist from splitting one entry into an orphanable pair. Every
    title/gist here comes from frontmatter, so it is already scrubbed and
    already single-line.
    """
    entries = []
    for key in _all_tickets(root, slug):
        fm, _ = _load_ticket(root, slug, key)
        if fm.get("status") != "closed":
            continue
        title = fm.get("title") or key
        gist = fm.get("gist") or ""
        entries.append(f"- [{title}](tickets/{key}.md) — {gist}".rstrip() + "\n")
    region = f"{_DECISIONS_START}\n{''.join(entries)}{_DECISIONS_END}\n"
    map_path = Path(root) / slug / "map.md"
    map_md = map_path.read_text(encoding="utf-8")
    if _DECISIONS_BLOCK_RE.search(map_md):
        map_md = _DECISIONS_BLOCK_RE.sub(lambda _m: region, map_md, count=1)
    else:
        # Legacy map.md charted before the region existed. Insert a fresh
        # region rather than trying to recognise the old loose list -- same
        # conservative choice, and same rationale, as resolve()'s legacy
        # ticket path: never guess at the boundary of pre-marker content.
        heading = "## Decisions so far\n"
        if heading in map_md:
            map_md = map_md.replace(heading, heading + "\n" + region, 1)
        else:
            map_md = map_md.rstrip("\n") + f"\n\n## Decisions so far\n\n{region}"
    _write_map_md(map_path, map_md)


def resolve(root, slug, ticket, gist, link, body):
    """Close `ticket` and record its resolution. Idempotent (review round 1
    finding): re-resolving the same ticket replaces the prior resolution
    block and the prior "Decisions so far" line rather than accumulating
    duplicate/contradictory ones.

    The resolution block is delimited by _RESOLUTION_START/_RESOLUTION_END
    marker comments (review round 3, findings R1/R2 -- see the constants'
    comment for why two rounds of markdown-pattern guessing both failed).
    Re-resolving replaces exactly the span between its own markers; the
    Question, any comment() sections, and a --body-file's own "## " sub-
    headings are outside that span and are never touched. That holds because
    of the marker invariant, NOT because markers look unlikely: `gist`,
    `link` and `body` are scrubbed below, exactly as chart() scrubs
    `question` and comment() scrubs its body, so nothing in `tbody` can
    impersonate a marker (review round 4, finding N1 -- before the scrub, a
    marker pasted into any of those five inputs reproduced round 1's
    unbounded accumulation and round 2's silent deletion of user text).

    Legacy tickets resolved before sentinels existed (no start/end markers
    present) are NOT migrated in place: their old, unsentinelled
    "## Resolution" text is left untouched as ordinary ticket content, and a
    fresh sentineled block is appended below it. This is deliberately
    conservative -- guessing at the boundary of pre-sentinel content is
    exactly the fragile pattern that caused rounds 1-3; the one-time cost is
    a single stale legacy section on the FIRST post-upgrade resolve of an
    already-resolved ticket, never an unbounded accumulation and never a
    chance of deleting unrelated content.
    """
    fm, tbody = _load_ticket(root, slug, ticket)
    fm["status"] = "closed"
    fm["gist"] = gist
    detail = f"\nDetail: {_scrub(link)}\n" if link else ""
    extra = f"\n{_scrub(body)}\n" if body else ""
    block = (f"{_RESOLUTION_START}\n## Resolution\n\n{_scrub(gist)}\n{detail}{extra}"
             f"{_RESOLUTION_END}\n")
    if _RESOLUTION_BLOCK_RE.search(tbody):
        tbody = _RESOLUTION_BLOCK_RE.sub(lambda _m: block, tbody, count=1)
    else:
        sep = "" if tbody.endswith("\n\n") else "\n"
        tbody = tbody + sep + block
    _save_ticket(root, slug, ticket, fm, tbody)
    _reindex_decisions(root, slug)
    # report the gist as STORED, not as passed in -- scrubbed and flattened,
    # so callers and the ticket file never disagree
    return {"resolved": ticket, "gist": _fm_value(gist) or None}


def main():
    ap = argparse.ArgumentParser(description="decision-map local backend")
    ap.add_argument("cmd", choices=["chart", "read", "frontier", "claim",
                                    "resolve", "comment", "block"])
    ap.add_argument("--root", default="docs/decision-map")
    ap.add_argument("--input"); ap.add_argument("--output")
    ap.add_argument("--map", dest="slug"); ap.add_argument("--ticket")
    ap.add_argument("--user", default="me"); ap.add_argument("--gist")
    ap.add_argument("--link"); ap.add_argument("--body-file", dest="body_file")
    ap.add_argument("--blocked-by", dest="blocked_by")
    ap.add_argument("--real", action="store_true")
    ap.add_argument("--dry-run", dest="dry", action="store_true")
    ap.add_argument("--force", action="store_true",
                     help="chart only: explicitly allow overwriting an existing map folder")
    a = ap.parse_args()
    body = Path(a.body_file).read_text(encoding="utf-8") if a.body_file else None
    if a.cmd == "chart":
        inp = json.loads(Path(a.input).read_text(encoding="utf-8"))
        result = chart(a.root, inp, real=a.real and not a.dry, force=a.force)
    elif a.cmd == "read":
        result = read_map(a.root, a.slug)
    elif a.cmd == "frontier":
        result = frontier(a.root, a.slug)
    elif a.dry:
        result = {"dryRun": True, "wouldRun": a.cmd, "ticket": a.ticket}
    elif a.cmd == "claim":
        result = claim(a.root, a.slug, a.ticket, a.user)
    elif a.cmd == "resolve":
        result = resolve(a.root, a.slug, a.ticket, a.gist, a.link, body)
    elif a.cmd == "comment":
        result = comment(a.root, a.slug, a.ticket, body)
    elif a.cmd == "block":
        result = block(a.root, a.slug, a.ticket, a.blocked_by)
    text = json.dumps(result, indent=2)
    if a.output:
        Path(a.output).write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
