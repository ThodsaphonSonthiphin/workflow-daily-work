#!/usr/bin/env python3
r"""local_map_ops.py — decision-map local-markdown backend (ADR 0042).

Map lives at <root>/<slug>/map.md, tickets at <root>/<slug>/tickets/<slug>.md.
Contract: plugins/decision-map/references/data-contracts.md. Stdlib only.

The marker invariant, the region merge, the input validation and the failure
vocabulary now live in `map_core` (ADR 0062), shared with the GitHub backend.
They are imported below under this module's historical `_name` spellings, so
this file reads as it always did and its suite keeps testing the same symbols.
What stays here is what is genuinely local: frontmatter, paths, file I/O.

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

THE PATH INVARIANT (round 5, finding N5) -- what this module rests on beyond
the shared marker invariant:

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

`inp` is validated before any file is written, in both dry-run and real mode
(see `map_core.validate_chart_input` for the full list and for the review
rounds behind each check). A malformed map_input.json fails cleanly with
ChartValidationError instead of writing a half-finished map folder or
crossing outside the intended root.
"""
import argparse, json, re, sys
from pathlib import Path

from map_core import (
    AFK_TYPES, VALID_TICKET_TYPES,
    SAFE_SLUG_RE as _SAFE_SLUG_RE,
    MARKER_PREFIX as _MARKER_PREFIX,
    MARKER_ESCAPED_PREFIX as _MARKER_ESCAPED_PREFIX,
    RESOLUTION_START as _RESOLUTION_START, RESOLUTION_END as _RESOLUTION_END,
    DECISIONS_START as _DECISIONS_START, DECISIONS_END as _DECISIONS_END,
    FOG_START as _FOG_START, FOG_END as _FOG_END,
    SCOPE_START as _SCOPE_START, SCOPE_END as _SCOPE_END,
    GRAPH_START as _GRAPH_START, GRAPH_END as _GRAPH_END,
    MAP_REGIONS as _MAP_REGIONS, TICKET_REGIONS as _TICKET_REGIONS,
    EMPTY_LIST_LINE as _EMPTY_LIST_LINE, FORCE_COST as _FORCE_COST,
    SCALAR_MAP_FIELDS as _SCALAR_MAP_FIELDS,
    REQUIRED_MAP_FIELDS as _REQUIRED_MAP_FIELDS,
    REQUIRED_TICKET_FIELDS as _REQUIRED_TICKET_FIELDS,
    ChartValidationError, UnsafeIdentifierError, InvalidEdgeError,
    CliUsageError, MarkerIntegrityError,
    scrub as _scrub, one_line as _one_line, mode as _mode,
    assert_regions as _assert_regions, safe_segment as _safe_segment,
    region_re as _region_re, region_body as _region_body,
    replace_region as _replace_region, region_text as _region_text,
    merge_region_lines as _merge_region_lines,
    count_added_lines as _count_added_lines,
    map_merge_detail as _map_merge_detail,
    render_map_body as _render_map_body,
    scalar_divergences as _scalar_divergences,
    merge_map_lists as _merge_map_lists,
    decisions_region as _decisions_region,
    position_diagram_region as _position_diagram_region,
    set_graph_region as _set_graph_region,
    require as _require, validate_chart_input as _validate_chart_input_core,
)

# The only frontmatter key that is ever written/read as a list. Every other
# key is a plain (one-line) string, even if its value happens to start with
# "[" and end with "]" (see _fm_parse's docstring).
_LIST_FM_KEYS = {"blocked_by"}

_RESOLUTION_BLOCK_RE = _region_re(_RESOLUTION_START, _RESOLUTION_END)
_DECISIONS_BLOCK_RE = _region_re(_DECISIONS_START, _DECISIONS_END)
_GRAPH_BLOCK_RE = _region_re(_GRAPH_START, _GRAPH_END)


def _validate_chart_input(inp, root=None):
    """Validate `inp` before chart() writes anything (dry-run or real).

    `root`, when given, lets the `blocks` check accept a target that already
    exists in the map rather than requiring it to be re-listed in tickets[]
    (ADR 0058 / review F3). Reading the filesystem there is a pre-write check,
    so nothing is written before it passes.
    """
    exists = None
    if root is not None:
        def exists(key):
            slug = (inp.get("target") or {}).get("slug")
            if not isinstance(slug, str) or not _SAFE_SLUG_RE.match(slug):
                return False
            return _ticket_path(root, slug, key).exists()
    _validate_chart_input_core(inp, ticket_exists=exists)


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

    The two ordering/coverage rules that make this safe -- flatten before
    escaping, and flatten with the reader's own splitter -- live in
    `map_core.one_line`, which is where both were learned the hard way.
    """
    return _one_line(v)


def _fm_dump(fm):
    lines = []
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(_fm_value(x) for x in v)}]")
        else:
            lines.append(f"{k}: {_fm_value(v)}")
    return "---\n" + "\n".join(lines) + "\n---\n"


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


def _children_of(root, slug, key):
    """Every ticket this one unblocks -- i.e. whose blocked_by names it.

    A ticket's parents are in its own frontmatter, but its children are only
    discoverable by looking at everyone else, so rendering either end of the
    diagram costs a scan of the map. That is the price of drawing children at
    all (spec 1, "Both ends"); on the GitHub backend the same information is
    already in the snapshot and costs nothing.
    """
    out = []
    for other in _all_tickets(root, slug):
        if other == key:
            continue
        fm, _ = _load_ticket(root, slug, other)
        if key in fm.get("blocked_by", []):
            out.append(other)
    return sorted(out)


def _graph_region_for(root, slug, key):
    fm, _ = _load_ticket(root, slug, key)
    return _position_diagram_region(key, fm.get("blocked_by", []),
                                    _children_of(root, slug, key))


def _render_map_md(m):
    """The whole map.md, as written by an initial chart or by --force.

    Only the prologue is local: the H1 (a tracker carries the name in the
    item's own title field) and an overview diagram naming files rather than
    sub-issues. Everything below it is `map_core.render_map_body`, so the two
    backends cannot drift on the regions the merge reaches into.
    """
    prologue = (
        f"# {_one_line(m['title'])}\n\n"
        "```mermaid\ngraph TD\n    MAP[\"map (this file)\"] --> T[\"tickets/*.md — one decision each\"]\n"
        "    T --> D[\"Decisions so far (index below)\"]\n```\n\n")
    return _render_map_body(m, prologue)


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
    div = _scalar_divergences(m, existing)
    text, added, list_div = _merge_map_lists(existing, m)
    div += list_div
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
                     f"\n{_position_diagram_region(t['key'], [], [])}"
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
    regenerated wholesale inside its own marker region (`map_core.
    decisions_region` formats it; the ordering rule lives there). Nothing
    outside the region is read or touched -- which is what stops a
    user-authored, index-shaped line elsewhere in map.md (in `notes`, say)
    from being substituted away, and stops a multi-line gist from splitting
    one entry into an orphanable pair. Every title/gist here comes from
    frontmatter, so it is already scrubbed and already single-line.
    """
    entries = []
    for key in _all_tickets(root, slug):
        fm, _ = _load_ticket(root, slug, key)
        if fm.get("status") != "closed":
            continue
        entries.append((fm.get("title") or key, f"tickets/{key}.md",
                        fm.get("gist") or ""))
    region = _decisions_region(entries)
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
    marker comments (review round 3, findings R1/R2 -- see map_core's marker
    constants for why two rounds of markdown-pattern guessing both failed).
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
