#!/usr/bin/env python3
r"""local_map_ops.py — decision-map local-markdown backend (ADR 0042).

Map lives at <root>/<slug>/map.md, tickets at <root>/<slug>/tickets/<slug>.md.
Contract: plugins/decision-map/references/data-contracts.md. Stdlib only.

Re-chart policy (ADR 0057, superseding round 1's refuse-by-default):
`chart` is ADDITIVE. It names two acts — initial charting and incremental
fog graduation — and one code path serves both. On a map folder that already
exists it creates only the tickets whose key is absent and merges
`notYetSpecified` / `outOfScope` lines into the map body without disturbing
anything else. Re-running identical input is a byte-identical no-op, which
also makes a partially-failed chart resumable. The map's
title/destination/notes are never rewritten additively; a difference is
reported, not applied.

Additive means UNION, and the guarantee is "never removes, never reorders,
never overwrites" -- not "never touches" (ADR 0058). An existing ticket may
gain a `blocked_by` entry and NOTHING else: every other byte of the file is
unchanged. That one exception exists because the alternative was worse --
dropping the edge left `frontier()` reporting a ticket as actionable when a
just-created ticket was meant to block it, silently, which is exactly what
the frontier must never do.

`force=True` (CLI: --force) is the explicit full rewrite. It is DESTRUCTIVE:
it discards the recorded resolutions, claims and blocking edges of every item
the input NAMES -- not of the whole map. Its reach is exactly the items the
plan labels OVERWRITE; a ticket named only in a `blocks` list is still a
`merge` and keeps everything, and a ticket the input does not mention is not
in the plan at all and is untouched. It is never needed to add tickets. See
_FORCE_COST -- no message in this module may recommend --force without saying
what it costs.

Round 1's Critical — a re-run must never silently destroy recorded state —
is still guarded, now by skipping rather than refusing. `chart(real=False)`
(the default dry run) reports the SAME actions a real run would take,
labeling every planned file "create" / "skip (exists)" / "merge" /
"OVERWRITE", and a file labeled "skip (exists)" is never written.

THE MARKER INVARIANT (review round 4, finding N1) -- the one rule the whole
module rests on:

    Every decision-map marker in a generated file was written by this
    module, because every user-supplied string is escaped on the way in.

Enforced, not asserted. `_scrub()` escapes the marker prefix in every
user-supplied string before it reaches a file, and every write goes through
`_assert_regions()`, which refuses to write a file that does not hold
exactly zero or one well-formed marker region. That is what lets
`resolve()` find the block it owns by searching for its own markers: the
search can no longer match user text, because user text can no longer
contain a marker. See the marker constants below for the three rounds of
failure that establish why nothing weaker works.

Escaping is ORDER-SENSITIVE: any transformation that runs after the escape
can put a marker back together. `_fm_value()` therefore flattens line breaks
BEFORE escaping, never after (round 5, finding N4), and flattens using the
reader's own `str.splitlines()` so the writer and the parser cannot disagree
about what a line break is (round 5, finding N7).

THE PATH INVARIANT (round 5, finding N5) -- the second thing the module
rests on:

    Every filesystem path this module builds is <root>/<safe-slug>/... ,
    because every identifier that becomes a path segment goes through
    `_safe_segment()`.

`chart()` has slug-validated the keys it creates since round 1, but the
identifiers the other subcommands accept at runtime were unchecked, so
`claim --ticket ../../../VICTIM` rewrote an arbitrary .md file outside
--root at exit code 0. `_map_dir()` and `_ticket_path()` are now the only
ways a map or ticket path is constructed, and both validate.

CLI failure contract: stdout carries JSON or nothing. A known, actionable
failure prints one line to stderr and exits EXIT_ERROR; an unexpected crash
still raises, so the two are distinguishable.

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
of the four valid types, and every `blocks` target must exist either in this
same `inp` or already in the map on disk (ADR 0058 -- an edge may name an
existing ticket without re-listing it). A malformed map_input.json fails
cleanly with
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
# a marker in a file is proof this module put it there. _assert_regions()
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
# Task 3b / ADR 0057: `chart` is additive, so the two authored lists in the
# map body must be merged into rather than rewritten. They get their own
# regions for the same reason the decisions index has one -- so the merge can
# find exactly the lines the tool owns without splitting the document on
# heading patterns, which is what cost rounds 1-3.
_FOG_START = "<!-- decision-map:fog:start -->"
_FOG_END = "<!-- decision-map:fog:end -->"
_SCOPE_START = "<!-- decision-map:scope:start -->"
_SCOPE_END = "<!-- decision-map:scope:end -->"

# Which regions each generated file may hold. _assert_regions checks a file
# against its own list, and checks that NO decision-map marker outside those
# regions is present -- so adding a region here is the only way to introduce
# a new legal marker.
_MAP_REGIONS = ((_DECISIONS_START, _DECISIONS_END),
                (_FOG_START, _FOG_END),
                (_SCOPE_START, _SCOPE_END))
_TICKET_REGIONS = ((_RESOLUTION_START, _RESOLUTION_END),)

# The placeholder the tool writes into an empty list region. It is tool-owned,
# not user content, so the merge drops it as soon as a real line arrives.
_EMPTY_LIST_LINE = "- (none)"

# Never recommend --force without saying what it costs (review F2). The
# reviewer followed the old advice -- "re-chart with --force to rewrite it" --
# and watched it erase a resolution, its frontmatter and its index entry:
# round 1's Critical harm, actively recommended by this module's own
# messages. Any text that steers a user toward --force must carry this.
_FORCE_COST = ("--force fully rewrites every item named in the input and "
               "DISCARDS their recorded resolutions, claims and blocking edges")


def _region_re(start, end):
    return re.compile(
        re.escape(start) + r".*?" + re.escape(end) + r"\n?", re.DOTALL)


_RESOLUTION_BLOCK_RE = _region_re(_RESOLUTION_START, _RESOLUTION_END)
_DECISIONS_BLOCK_RE = _region_re(_DECISIONS_START, _DECISIONS_END)


def _region_body(text, start, end):
    """The text strictly between one marker pair, or None if absent.

    Literal `str.find` on the exact markers -- no pattern at all, so there is
    nothing to anchor wrongly. Returns None rather than guessing when the
    region is missing.
    """
    i = text.find(start)
    if i < 0:
        return None
    j = text.find(end, i + len(start))
    if j < 0:
        return None
    return text[i + len(start):j]


def _replace_region(text, start, end, new_body):
    """Swap the content between one marker pair, leaving the rest byte-identical."""
    i = text.find(start)
    if i < 0:
        return text
    j = text.find(end, i + len(start))
    if j < 0:
        return text
    return text[:i + len(start)] + new_body + text[j:]


class ChartValidationError(ValueError):
    """map_input.json failed validation. Raised before anything is written."""


class UnsafeIdentifierError(ValueError):
    """A value used as a path segment (a map slug or a ticket id) is not a
    safe slug. Raised BEFORE the path is built, so nothing outside the map
    folder is ever opened, read or written.

    chart() has slug-validated the keys it writes since round 1, but the
    identifiers the other subcommands accept at runtime (--ticket, --map,
    --blocked-by) were never checked -- `_ticket_path` was byte-identical
    across rounds 1-4 -- so `claim --ticket ../../../VICTIM` rewrote an
    arbitrary .md file outside --root, at exit code 0, lossily round-tripping
    that file's own frontmatter on the way through (review round 5, N5)."""


class InvalidEdgeError(ValueError):
    """A blocking edge is unusable: it names its own ticket. Raised before
    anything is written. A self-edge permanently quarantines the ticket --
    frontier() reports it blocked by something that can never close, so it is
    never takeable and never resolvable (review F2 / L16)."""


class CliUsageError(ValueError):
    """A subcommand was invoked without an argument it needs. Raised before
    any work, and reported as a one-line message rather than a traceback."""


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


def _assert_regions(text, regions, what):
    """Refuse to write `text` unless every declared region is well formed and
    no decision-map marker appears outside them.

    The backstop for _scrub(): if a future change adds a user-input path and
    forgets to scrub it, this fails loudly at the write instead of silently
    losing user content on some later resolve() -- which is exactly how the
    same defect survived three fix rounds.

    The final stray-prefix check is the part that generalises: it is what
    makes "a marker in this file was written by this module" checkable
    without enumerating every marker that could ever exist. Dropping it
    survived the round-5 suite (review finding F6), so it now has its own
    regression test.
    """
    problem = None
    accounted = 0
    for start, end in regions:
        n_start, n_end = text.count(start), text.count(end)
        accounted += n_start + n_end
        if n_start > 1 or n_end > 1:
            problem = f"{n_start} start / {n_end} end markers (expected at most one of each)"
        elif n_start != n_end:
            problem = f"unpaired markers ({n_start} start, {n_end} end)"
        elif n_start and text.index(start) > text.index(end):
            problem = "end marker precedes start marker"
        if problem:
            problem = f"region {start!r}: {problem}"
            break
    if not problem and text.count(_MARKER_PREFIX) != accounted:
        problem = (f"{text.count(_MARKER_PREFIX)} decision-map marker(s) present but only "
                   f"{accounted} belong to a declared region")
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


def _validate_chart_input(inp, root=None):
    """Validate `inp` before chart() writes anything (dry-run or real).

    `root`, when given, lets the `blocks` check accept a target that already
    exists in the map rather than requiring it to be re-listed in tickets[]
    (ADR 0058 / review F3).

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
    - every `blocks` target must exist EITHER in this same `inp` OR already in
      the map on disk (ADR 0058 -- the round-1 "must be re-listed in tickets[]"
      rule is gone; see the check itself for why)
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
        # A key is a CROSS-BACKEND identity: ADO and GitHub carry it in an
        # HTML comment (<!-- decision-map:key:<key> -->), and the HTML spec
        # forbids "--" inside comment text -- sanitizers and rich-text editors
        # rewrite or truncate such a comment, which would silently break the
        # key->item join and re-create every ticket. Rejected here, at the one
        # place keys are minted, rather than in _SAFE_SLUG_RE: tightening that
        # would make _all_tickets silently skip an existing "a--b.md" and
        # would reject --ticket for a file that legitimately exists.
        if "--" in key:
            raise ChartValidationError(
                f"invalid ticket key {key!r}: must not contain '--'. The key is "
                "carried in an HTML comment on ADO and GitHub, where '--' is "
                "not allowed inside comment text; use a single hyphen")
        if t["type"] not in VALID_TICKET_TYPES:
            raise ChartValidationError(
                f"ticket {key!r}: invalid type {t['type']!r}; "
                f"must be one of {sorted(VALID_TICKET_TYPES)}")
        _require(where, t, "blocks", list, False)
        keys.add(key)
    for t in inp["tickets"]:
        for blocked in t.get("blocks") or []:
            if blocked == t["key"]:
                raise ChartValidationError(
                    f"ticket {t['key']!r} blocks itself: the edge would leave "
                    "it waiting on a ticket that can never close, so it would "
                    "never appear on the frontier")
            if blocked in keys:
                continue
            # ADR 0058 / review F3: an edge may name a ticket that already
            # exists on disk without re-listing it in tickets[]. The round-1
            # rule ("must be a key in this same input") existed only so pass 2
            # could never hit a file pass 1 had not created; additive chart
            # unions into existing files, so the real requirement is that the
            # target exist SOMEWHERE. Reading the filesystem here is a
            # pre-write check, so nothing is written before it passes.
            if (root is not None and isinstance(blocked, str)
                    and _SAFE_SLUG_RE.match(blocked)
                    and _ticket_path(root, slug, blocked).exists()):
                continue
            raise ChartValidationError(
                f"ticket {t['key']!r} blocks unknown ticket {blocked!r} "
                "(not in this map_input's tickets[], and no such ticket "
                "exists in the map)")


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
    """One frontmatter value, flattened to a single line and THEN escaped.

    The marker invariant's choke point for frontmatter: no frontmatter value
    is ever generated content, so every one of them is scrubbed here rather
    than at each caller (title, gist, assignee, blocked-by entries ...).

    Frontmatter here is one physical line per key. An embedded line break
    would otherwise either truncate the value (the rest silently dropped on
    read) or corrupt a later key's parse (review round 1 finding); flattening
    also guarantees the map.md index entries built from these values are
    exactly one line each.

    TWO ORDERING/COVERAGE RULES, both load-bearing, both learned the hard way:

    1. Flatten FIRST, escape SECOND (round 5, finding N4). Escaping first is
       a hole: "<!--\\ndecision-map:resolution:start -->" contains no marker
       for _scrub to find, and flattening it afterwards RECONSTITUTES a live
       marker that no escape ever saw. Unpaired that raised
       MarkerIntegrityError mid-chart with map.md already on disk; paired it
       sailed through _assert_regions and wrote live markers into a
       generated file -- falsifying the invariant this module rests on.
    2. Flatten with the READER's own splitter (round 5, finding N7). _fm_parse
       splits this block with str.splitlines(), so " ".join(s.splitlines())
       covers exactly what the reader recognises, by construction, and the
       two cannot drift apart. The previous hand-listed CRLF/LF/CR set missed
       eight separators splitlines() honours -- U+000B, U+000C, U+001C,
       U+001D, U+001E, U+0085, U+2028, U+2029 -- any of which let
       `claim --user "me<sep>status: closed"` forge a real frontmatter key,
       silently closing the ticket and dropping it out of the frontier.
    """
    return _one_line(v)


def _one_line(v):
    """Flatten to a single line, THEN escape -- see _fm_value for both rules.

    Shared by frontmatter values and by the one-line items in the map's fog /
    out-of-scope regions, so a list item can never split across two physical
    lines (which would break the merge's line-wise dedup) and can never
    reconstitute a marker after the escape has run.
    """
    s = "" if v is None else str(v)
    return _scrub(" ".join(s.splitlines()))


def _fm_dump(fm):
    lines = []
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(_fm_value(x) for x in v)}]")
        else:
            lines.append(f"{k}: {_fm_value(v)}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def _safe_segment(value, kind):
    """Return `value` if it is safe to use as a single path segment.

    THE enforcing line for the path half of the module: every filesystem path
    this module builds goes through here or through _map_dir/_ticket_path
    below, so a traversal payload is rejected before any path is constructed.
    It uses the SAME _SAFE_SLUG_RE that chart() applies to the keys it
    creates, so it can never reject an identifier this module could
    legitimately have produced.
    """
    if not isinstance(value, str) or not _SAFE_SLUG_RE.match(value):
        raise UnsafeIdentifierError(
            f"invalid {kind} {value!r}: must be a safe slug (letters, digits, "
            "'-', '_'; no path separators, drive letters, '..', or line breaks)")
    return value


def _map_dir(root, slug):
    return Path(root) / _safe_segment(slug, "map slug")


def _ticket_path(root, slug, ticket):
    return _map_dir(root, slug) / "tickets" / f"{_safe_segment(ticket, 'ticket id')}.md"


def _load_ticket(root, slug, ticket):
    text = _ticket_path(root, slug, ticket).read_text(encoding="utf-8")
    return _fm_parse(text)


def _save_ticket(root, slug, ticket, fm, body):
    text = _fm_dump(fm) + body
    # THE enforcing line for the ticket half of the marker invariant: every
    # write of every ticket, from every subcommand, passes through here.
    _assert_regions(text, _TICKET_REGIONS, f"ticket {ticket!r}")
    _ticket_path(root, slug, ticket).write_text(text, encoding="utf-8")


def _write_map_md(path, text):
    """THE enforcing line for the map.md half of the marker invariant."""
    _assert_regions(text, _MAP_REGIONS, "map.md")
    path.write_text(text, encoding="utf-8")


def _ticket_json(root, slug, ticket):
    fm, _ = _load_ticket(root, slug, ticket)
    return {
        "key": ticket, "id": ticket,
        "name": fm.get("title", ticket),
        # forward slashes always -- backslash is Markdown's escape character,
        # so a Windows-native path here would break every [name](url) link
        # (review round 1 finding).
        "url": _ticket_path(root, slug, ticket).as_posix(),
        "type": fm.get("type", "grilling"), "mode": fm.get("mode", "HITL"),
        "status": fm.get("status", "open"),
        "assignee": fm.get("assignee") or None,
        # Output shape uses "blockedBy" (upstream blockers); the on-disk
        # frontmatter key stays "blocked_by" (see _load_ticket / _save_ticket).
        "blockedBy": fm.get("blocked_by", []),
        "gist": fm.get("gist") or None,
    }


def _all_tickets(root, slug):
    tdir = _map_dir(root, slug) / "tickets"
    if not tdir.exists():
        return []
    # Only stems this module could itself have created. A hand-added file
    # with a name that is not a safe slug is not a ticket -- skipping it
    # keeps read/frontier working instead of tripping _safe_segment on a
    # name that came from the filesystem rather than from the caller.
    keep, skipped = [], []
    for p in sorted(tdir.glob("*.md")):
        (keep if _SAFE_SLUG_RE.match(p.stem) else skipped).append(p)
    # ...but say so. Silently skipping made a hand-added file invisible: a
    # session reads the frontier and believes a decision is unrepresented
    # while it is sitting on disk. stderr only -- stdout stays JSON-only and
    # the JSON shape is unchanged, because the contract documents it and both
    # flow skills parse it (review F2).
    for p in skipped:
        print(f"warning: ignoring {p.name!r} in {slug}/tickets: the filename is not a "
              "safe slug (letters, digits, '-', '_'), so it is not a decision-map "
              "ticket and no command will see it", file=sys.stderr)
    return [p.stem for p in keep]


def _region_text(start, end, lines):
    return start + "\n" + "".join(ln + "\n" for ln in lines) + end


def _merge_region_lines(body, items):
    """Union the existing one-line items with `items`, existing order first.

    Never removes and never reorders what is already there (ADR 0057) -- new
    lines are appended. The tool-owned "- (none)" placeholder is dropped as
    soon as a real line exists, and restored if the result is empty.
    """
    existing = [ln for ln in (body or "").splitlines()
                if ln.strip() and ln.strip() != _EMPTY_LIST_LINE]
    seen = set(existing)
    for x in items:
        line = f"- {_one_line(x)}"
        if line not in seen:
            existing.append(line)
            seen.add(line)
    return existing or [_EMPTY_LIST_LINE]


def _count_added_lines(body, merged_lines):
    """How many lines the merge actually ADDS to one map.md list region.

    Not `len(merged) - len(existing)`: the tool-owned "- (none)" placeholder
    is dropped when the first real line arrives and restored when the list
    empties, so the arithmetic is off by one in either direction. Count the
    merged lines that were not already there instead.
    """
    existing = {ln for ln in (body or "").splitlines()
                if ln.strip() and ln.strip() != _EMPTY_LIST_LINE}
    return sum(1 for ln in merged_lines
               if ln != _EMPTY_LIST_LINE and ln not in existing)


def _map_merge_detail(added):
    """The one-line `detail` for a map-body merge: what it will add.

    The contract requires every `merge` entry to name what it adds, because
    that string is what the ADR-0039 gate shows the user before the write. A
    map-body merge that reported `detail: null` rendered as a bare
    `merge .../map.md` -- an unnamed write, approved blind.

    `added` is [(noun, count), ...] for the regions that gained lines. The
    fallback covers the one way a merge can change bytes without adding a
    line: a hand-edited region whose blank lines or stale placeholder the
    merge normalises away. Saying "adds 0 lines" there would be a lie.
    """
    parts = [f"{n} {noun} line" + ("s" if n != 1 else "") for noun, n in added]
    if not parts:
        return "normalises the map body's list regions (no new lines)"
    return "adds " + ", ".join(parts)


def _render_map_md(m):
    """The whole map.md, as written by an initial chart or by --force."""
    fog = _region_text(_FOG_START, _FOG_END,
                       _merge_region_lines("", m.get("notYetSpecified") or []))
    oos = _region_text(_SCOPE_START, _SCOPE_END,
                       _merge_region_lines("", m.get("outOfScope") or []))
    return (
        # _one_line, not _scrub: these three are single-line slots in the
        # rendered document -- an H1, and one paragraph under each of two
        # headings -- so they get the same flatten-then-escape treatment every
        # other user string in this module gets (see _fm_value). _scrub alone
        # neutralises the marker but leaves line breaks, and both harms were
        # silent: read_map()'s splitlines()[0] truncated a two-line title with
        # no error and no divergence entry, and a newline-bearing destination
        # injected a second "## Notes" heading AHEAD of the real one, into the
        # file a human is meant to read and hand-edit. Both skills describe the
        # destination as "one or two lines", so that shape is invited.
        f"# {_one_line(m['title'])}\n\n"
        "```mermaid\ngraph TD\n    MAP[\"map (this file)\"] --> T[\"tickets/*.md — one decision each\"]\n"
        "    T --> D[\"Decisions so far (index below)\"]\n```\n\n"
        f"## Destination\n{_one_line(m['destination'])}\n\n"
        f"## Notes\n{_one_line(m.get('notes') or '')}\n\n"
        # Every list under a heading below is a GENERATED region, delimited so
        # an additive re-chart can merge into it, and resolve() can rebuild the
        # decisions index, without pattern-searching the rest of the file.
        f"## Decisions so far\n\n{_DECISIONS_START}\n{_DECISIONS_END}\n\n"
        f"## Not yet specified\n\n{fog}\n\n"
        f"## Out of scope\n\n{oos}\n")


_SCALAR_MAP_FIELDS = ("title", "destination", "notes")


def _plan_map_md(base, inp, force):
    """-> (action, text_or_None, detail_or_None, divergences) for map.md.

    Additive by default (ADR 0057): an existing map.md keeps its authored
    prose byte-for-byte and only its fog / out-of-scope regions are merged
    into. "skip (exists)" is returned only when the merge would change
    nothing, so the dry run's promise that a skip never writes stays true.

    `detail` is the contract's one-line "what this merge adds" string, and is
    None on every action other than "merge" -- detail is meaningful only
    where something is modified in place.
    """
    p = base / "map.md"
    m = inp["map"]
    if not p.exists():
        return "create", _render_map_md(m), None, []
    if force:
        return "OVERWRITE", _render_map_md(m), None, []
    existing = p.read_text(encoding="utf-8")
    div = []
    # Scalars are never rewritten on the additive path. The only way to change
    # them via this tool is --force, which rewrites the WHOLE map and discards
    # every recorded resolution, claim and edge -- so the divergence message
    # below leads with the hand-edit instead (review F2).
    # The check is containment of the flattened value in the flattened file:
    # it drives a REPORT only, never a write, so it deliberately avoids
    # splitting the document into sections to compare field-by-field.
    flat_existing = " ".join(existing.splitlines())
    for field in _SCALAR_MAP_FIELDS:
        value = m.get(field)
        if value and _one_line(value) not in flat_existing:
            div.append(f"map {field!r} in the input differs from the map on disk; "
                       f"left unchanged. To apply it you must re-chart, but "
                       f"{_FORCE_COST} -- editing map.md by hand is usually "
                       "the right move instead")
    text = existing
    added = []
    for start, end, items, label, noun in (
            (_FOG_START, _FOG_END, m.get("notYetSpecified") or [],
             "notYetSpecified", "fog"),
            (_SCOPE_START, _SCOPE_END, m.get("outOfScope") or [],
             "outOfScope", "out-of-scope")):
        body = _region_body(text, start, end)
        if body is None:
            if items:
                div.append(
                    f"this map.md predates the {label} region, so its "
                    f"{len(items)} line(s) were not merged. Add the "
                    f"{label} markers to map.md by hand to enable merging; "
                    f"re-charting would also fix it, but {_FORCE_COST}")
            continue
        merged_lines = _merge_region_lines(body, items)
        merged = _region_text(start, end, merged_lines)
        text = _replace_region(text, start, end, merged[len(start):-len(end)])
        gained = _count_added_lines(body, merged_lines)
        if gained:
            added.append((noun, gained))
    if text == existing:
        return "skip (exists)", None, None, div
    return "merge", text, _map_merge_detail(added), div


def _chart_plan(root, inp, force):
    """Return (entries, map_text, divergences) for everything chart() would do.

    Each entry is {"path", "action", "detail"}. action is one of:
      - "create"        the file doesn't exist yet
      - "skip (exists)" the file exists and will not be touched at all
      - "merge"         the file exists and is modified in place, additively:
                        map.md gaining fog / out-of-scope lines, or a ticket
                        gaining a blockedBy entry (ADR 0058)
      - "OVERWRITE"     the file exists and force=True (explicit full rewrite)
    "refuse" is gone: ADR 0057 supersedes refuse-by-default. A "skip" must
    never write -- the surviving guard on round 1's Critical -- which is why
    "merge" is its own label rather than being folded into "skip".

    The blockedBy unions are computed HERE, before the dry run returns, so
    the ADR-0039 approval gate sees every write (review F1: they used to be
    computed after the dry-run early return, leaving the gate silent about a
    file the real run would modify).
    """
    slug = inp["target"]["slug"]
    base = _map_dir(root, slug)
    map_action, map_text, map_detail, div = _plan_map_md(base, inp, force)
    entries = [{"path": base / "map.md", "action": map_action,
                "detail": map_detail}]
    by_path = {base / "map.md": entries[0]}
    action_by_key = {}
    for t in inp["tickets"]:
        p = base / "tickets" / (t["key"] + ".md")
        if not p.exists():
            action = "create"
        else:
            action = "OVERWRITE" if force else "skip (exists)"
        action_by_key[t["key"]] = action
        entry = {"path": p, "action": action, "detail": None}
        entries.append(entry)
        by_path[p] = entry
    pending = {}
    for t in inp["tickets"]:
        for blocked in t.get("blocks") or []:
            if action_by_key.get(blocked) in ("create", "OVERWRITE"):
                continue                      # written fresh; edge goes in with it
            fm, _ = _load_ticket(root, slug, blocked)
            if t["key"] in fm.get("blocked_by", []):
                continue                      # already unioned: genuinely no change
            blockers = pending.setdefault(_ticket_path(root, slug, blocked), [])
            if t["key"] not in blockers:      # `blocks` may name the same target twice
                blockers.append(t["key"])
    for p, blockers in pending.items():
        entry = by_path.get(p)
        if entry is None:                     # target not re-listed in tickets[]
            entry = {"path": p, "action": "skip (exists)", "detail": None}
            entries.append(entry)
            by_path[p] = entry
        entry["action"] = "merge"
        entry["detail"] = "unions blockedBy: " + ", ".join(blockers)
    return entries, map_text, div


def chart(root, inp, real, force=False):
    """Bulk-create (or explicitly re-chart, with force=True) a map + its
    tickets. See the module docstring for the full re-chart policy."""
    _validate_chart_input(inp, root)
    slug = inp["target"]["slug"]
    base = _map_dir(root, slug)
    entries, map_text, div = _chart_plan(root, inp, force)
    actions = {e["path"]: e["action"] for e in entries}
    if not real:
        # The human-readable plan goes to STDERR: every subcommand's contract
        # is that stdout carries JSON or nothing, so `chart --input x | jq`
        # works (round 5). The same plan is in the returned JSON's "planned".
        print("DRY RUN — planned files:", file=sys.stderr)
        for e in entries:
            detail = f"  [{e['detail']}]" if e["detail"] else ""
            print(f"  {e['action']} {e['path']}{detail}", file=sys.stderr)
        for d in div:
            print(f"  divergence: {d}", file=sys.stderr)
        return {"backend": "local", "dryRun": True,
                "planned": [{"path": str(e["path"]), "action": e["action"],
                             "detail": e["detail"]} for e in entries],
                "divergence": div}
    (base / "tickets").mkdir(parents=True, exist_ok=True)
    if actions[base / "map.md"] != "skip (exists)":
        _write_map_md(base / "map.md", map_text)
    # pass 1: create the absent tickets; pass 2: union the blocking edges
    # (create-then-wire, spec §9). Safe because _validate_chart_input already
    # confirmed every `blocks` target is either in this input or on disk.
    for t in inp["tickets"]:
        # ONLY create/OVERWRITE write a fresh ticket. "merge" must fall
        # through to pass 2: it means the file exists and gains a blockedBy
        # entry, so rewriting it here would reset the very status, assignee
        # and resolution ADR 0058 promises to preserve.
        if actions[base / "tickets" / (t["key"] + ".md")] not in ("create", "OVERWRITE"):
            continue
        fm = {"title": t["title"], "type": t["type"], "mode": _mode(t["type"]),
              "status": "open", "assignee": "", "blocked_by": [], "gist": ""}
        _save_ticket(root, slug, t["key"], fm,
                     f"\n## Question\n\n{_scrub(t['question'])}\n")
    # ADR 0058: the edge is UNIONED into whatever file holds it, existing or
    # not. block() appends only when absent and does not write otherwise, so
    # an existing ticket gains one blockedBy entry and nothing else, and an
    # identical re-run stays byte-identical. It routes through _save_ticket,
    # so _assert_regions still covers this write.
    for t in inp["tickets"]:
        for blocked in t.get("blocks") or []:
            block(root, slug, blocked, t["key"])
    for d in div:
        print(f"chart: divergence: {d}", file=sys.stderr)
    out = read_map(root, slug)
    out["divergence"] = div
    return out


def read_map(root, slug):
    map_path = _map_dir(root, slug) / "map.md"
    map_md = map_path.read_text(encoding="utf-8")
    title = map_md.splitlines()[0].lstrip("# ").strip()
    dest = ""
    dm = re.search(r"## Destination\n(.+?)(\n\n|\n##)", map_md, re.DOTALL)
    if dm:
        dest = dm.group(1).strip()
    return {"backend": "local",
            "map": {"id": slug, "name": title,
                    "url": map_path.as_posix(),
                    "destination": dest},
            "tickets": [_ticket_json(root, slug, t) for t in _all_tickets(root, slug)]}


def frontier(root, slug):
    # Assert the map exists before reporting on it. Without this a slug that
    # does not exist yields three empty buckets and exit 0 -- indistinguishable
    # from a map whose every decision is resolved, which is what work-map would
    # then tell the user. Reading map.md fails the same way read_map does
    # (OSError -> exit 2), so both entry points agree on what "no such map"
    # looks like.
    (_map_dir(root, slug) / "map.md").read_text(encoding="utf-8")

    out = {"frontier": [], "blocked": [], "claimed": []}
    tickets = {t: _ticket_json(root, slug, t) for t in _all_tickets(root, slug)}
    for key, t in tickets.items():
        if t["status"] != "open":
            continue
        # A blocker that no longer exists is NOT a satisfied blocker. Treating
        # an absent key as cleared means deleting a blocker silently promotes
        # its dependents onto the frontier, and a session then starts work the
        # map still says is not ready. Keep them blocked and name what is
        # missing; on a tracker (items deleted, moved, re-parented) this is the
        # common case, not the edge case.
        missing = [b for b in t["blockedBy"] if b not in tickets]
        open_blockers = [b for b in t["blockedBy"]
                         if b in tickets and tickets[b]["status"] == "open"]
        open_blockers += [b for b in missing if b not in open_blockers]
        if t["assignee"]:
            out["claimed"].append({"id": key, "name": t["name"], "assignee": t["assignee"]})
        elif open_blockers:
            entry = {"id": key, "name": t["name"], "blockedBy": open_blockers}
            if missing:
                entry["missingBlockers"] = missing
            out["blocked"].append(entry)
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
    # --blocked-by is a ticket identifier too. Validating it also keeps the
    # "blocked_by: [a, b]" frontmatter list parseable, since a value carrying
    # a comma or a line break would otherwise corrupt it on read.
    _safe_segment(blocked_by, "blocked-by ticket id")
    if blocked_by == ticket:
        raise InvalidEdgeError(
            f"ticket {ticket!r} cannot block itself: the edge would leave it "
            "waiting on a ticket that can never close, so it would never "
            "appear on the frontier again")
    fm, body = _load_ticket(root, slug, ticket)
    # The target must exist in this map. chart() already rejects an edge to a
    # ticket that is in neither the input nor the map; block() used to accept
    # one, return rc=0 and write a phantom key that blocked the ticket for
    # ever. Same validation surface, same rule -- and reading it raises the
    # same FileNotFoundError any missing ticket does, which main() renders as
    # a clean one-line error.
    _load_ticket(root, slug, blocked_by)
    deps = fm.get("blocked_by", [])
    # Union, and do not write at all when the edge is already there. The
    # no-write path is what makes an additive re-chart byte-identical rather
    # than merely equivalent (ADR 0058) -- a rewrite would be a no-op only if
    # parse/dump round-trips exactly, which is not a property worth betting
    # a byte-identity guarantee on.
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
    map_path = _map_dir(root, slug) / "map.md"
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


# Exit codes. 0 success; EXIT_ERROR a known, actionable failure reported as
# one line on stderr; anything else (an unexpected crash) still surfaces as a
# traceback and Python's own exit 1 -- deliberately distinct, so a caller can
# tell "you passed something wrong" from "this tool is broken".
EXIT_OK = 0
EXIT_ERROR = 2

# Every failure below is the user's to act on, so each gets a one-line
# message naming the problem AND the remedy instead of a traceback (deferred
# in rounds 1-4; landed in round 5 after N4 showed the error path actively
# misdirects -- a reconstituted marker reported itself as "hand-edited
# markers in the file", which was false).
_REMEDY = {
    CliUsageError: "run with --help to see the arguments this subcommand needs",
    ChartValidationError: "correct the field named above in map_input.json and re-run",
    UnsafeIdentifierError: "pass the id exactly as chart created it",
    InvalidEdgeError: "a ticket cannot block itself; name a different --blocked-by",
    MarkerIntegrityError: "remove the stray decision-map marker comments from that file by hand",
    json.JSONDecodeError: "make sure --input points at valid JSON",
}
_DEFAULT_REMEDY = "check the path and permissions, then re-run"

# (attribute on the parsed args, the flag the user types)
_REQUIRED_CLI_ARGS = {
    "chart": [("input", "--input")],
    "read": [("slug", "--map")],
    "frontier": [("slug", "--map")],
    "claim": [("slug", "--map"), ("ticket", "--ticket")],
    "resolve": [("slug", "--map"), ("ticket", "--ticket"), ("gist", "--gist")],
    "comment": [("slug", "--map"), ("ticket", "--ticket"), ("body_file", "--body-file")],
    "block": [("slug", "--map"), ("ticket", "--ticket"), ("blocked_by", "--blocked-by")],
}


def _check_cli_args(a):
    missing = [flag for attr, flag in _REQUIRED_CLI_ARGS[a.cmd]
               if getattr(a, attr, None) is None]
    if missing:
        raise CliUsageError(
            f"{a.cmd} needs {' and '.join(missing)}")


def _dispatch(a):
    _check_cli_args(a)
    body = Path(a.body_file).read_text(encoding="utf-8") if a.body_file else None
    if a.cmd == "chart":
        inp = json.loads(Path(a.input).read_text(encoding="utf-8"))
        return chart(a.root, inp, real=a.real and not a.dry, force=a.force)
    if a.cmd == "read":
        return read_map(a.root, a.slug)
    if a.cmd == "frontier":
        return frontier(a.root, a.slug)
    if a.dry:
        # --dry-run is inert on every mutating subcommand: report, touch
        # nothing. It must still validate every identifier the real run
        # would, or it reports success for a call that exits 2 for real --
        # an inert but untruthful dry run (review finding F3).
        _safe_segment(a.slug, "map slug")
        _safe_segment(a.ticket, "ticket id")
        if a.cmd == "block":
            _safe_segment(a.blocked_by, "blocked-by ticket id")
        return {"dryRun": True, "wouldRun": a.cmd, "ticket": a.ticket}
    if a.cmd == "claim":
        return claim(a.root, a.slug, a.ticket, a.user)
    if a.cmd == "resolve":
        return resolve(a.root, a.slug, a.ticket, a.gist, a.link, body)
    if a.cmd == "comment":
        return comment(a.root, a.slug, a.ticket, body)
    return block(a.root, a.slug, a.ticket, a.blocked_by)


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
                     help="chart only: full rewrite of an existing map. DESTRUCTIVE -- "
                          "discards every recorded resolution, claim and blocking edge. "
                          "Not needed to add tickets: chart is additive by default")
    a = ap.parse_args()
    try:
        result = _dispatch(a)
    except (CliUsageError, ChartValidationError, InvalidEdgeError,
            UnsafeIdentifierError, MarkerIntegrityError,
            json.JSONDecodeError, OSError) as e:
        remedy = next((r for cls, r in _REMEDY.items() if isinstance(e, cls)),
                      _DEFAULT_REMEDY)
        # one line, flattened, on stderr -- stdout stays empty so a caller
        # piping it never sees half a JSON document
        problem = " ".join(str(e).split())
        if problem.startswith(f"{a.cmd}: "):       # don't say "chart: chart: ..."
            problem = problem[len(a.cmd) + 2:]
        print(f"error: {a.cmd}: {problem} -- {remedy}", file=sys.stderr)
        return EXIT_ERROR
    text = json.dumps(result, indent=2)
    if a.output:
        Path(a.output).write_text(text, encoding="utf-8")
    print(text)
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
