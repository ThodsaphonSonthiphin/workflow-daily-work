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

`inp` is validated before any file is written (in both dry-run and real
mode): the map's own `target.slug` and every ticket `key` must each be a
safe slug (letters/digits/`-`/`_` only, anchored to the exact end of the
string with `\Z` -- not `$`, which in Python also matches just before a
trailing newline and would let e.g. "okname\n" slip through as a path
segment), every ticket `type` must be one of the four valid types, and
every `blocks` target must be a key present in this same `inp`. A malformed
map_input.json fails cleanly with ChartValidationError instead of writing a
half-finished map folder or crossing outside the intended root.
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


class ChartConflictError(Exception):
    """chart(real=True) would overwrite existing map/ticket files and
    force=True was not passed. Raised before anything is written."""


class ChartValidationError(ValueError):
    """map_input.json failed validation. Raised before anything is written."""


def _mode(ticket_type):
    return "AFK" if ticket_type in AFK_TYPES else "HITL"


def _validate_chart_input(inp):
    """Validate `inp` before chart() writes anything (dry-run or real).

    - target.slug must be a safe slug (round 2 finding N2 -- previously
      unvalidated; "../../pwned-slug" and "C:/Windows/Temp/pwned-slug" both
      wrote outside the intended root)
    - every ticket key must be a safe slug (no path separators / '..')
    - every ticket type must be one of the four valid types
    - every `blocks` target must be a key present in this same `inp`
    """
    slug = inp["target"]["slug"]
    if not _SAFE_SLUG_RE.match(slug):
        raise ChartValidationError(
            f"invalid map slug {slug!r}: must be a safe slug "
            "(letters, digits, '-', '_'; no path separators, drive letters, or '..')")
    keys = set()
    for t in inp["tickets"]:
        key = t["key"]
        if not _SAFE_SLUG_RE.match(key):
            raise ChartValidationError(
                f"invalid ticket key {key!r}: must be a safe slug "
                "(letters, digits, '-', '_'; no path separators or '..')")
        if t["type"] not in VALID_TICKET_TYPES:
            raise ChartValidationError(
                f"ticket {key!r}: invalid type {t['type']!r}; "
                f"must be one of {sorted(VALID_TICKET_TYPES)}")
        keys.add(key)
    for t in inp["tickets"]:
        for blocked in t.get("blocks", []):
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


def _fm_dump(fm):
    lines = []
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        else:
            s = "" if v is None else str(v)
            # Frontmatter here is one physical line per key. An embedded
            # newline would otherwise either truncate the value (the rest
            # silently dropped on read) or corrupt a later key's parse
            # (review round 1 finding) — collapse it to a space instead.
            s = s.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
            lines.append(f"{k}: {s}")
    return "---\n" + "\n".join(lines) + "\n---\n"


def _ticket_path(root, slug, ticket):
    return Path(root) / slug / "tickets" / f"{ticket}.md"


def _load_ticket(root, slug, ticket):
    text = _ticket_path(root, slug, ticket).read_text(encoding="utf-8")
    return _fm_parse(text)


def _save_ticket(root, slug, ticket, fm, body):
    _ticket_path(root, slug, ticket).write_text(_fm_dump(fm) + body, encoding="utf-8")


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
    slug = inp["target"]["slug"]
    _validate_chart_input(inp)
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
    fog = "\n".join(f"- {x}" for x in m.get("notYetSpecified", [])) or "- (none)"
    oos = "\n".join(f"- {x}" for x in m.get("outOfScope", [])) or "- (none)"
    (base / "map.md").write_text(
        f"# {m['title']}\n\n"
        "```mermaid\ngraph TD\n    MAP[\"map (this file)\"] --> T[\"tickets/*.md — one decision each\"]\n"
        "    T --> D[\"Decisions so far (index below)\"]\n```\n\n"
        f"## Destination\n{m['destination']}\n\n"
        f"## Notes\n{m.get('notes', '')}\n\n"
        "## Decisions so far\n\n"
        f"## Not yet specified\n{fog}\n\n"
        f"## Out of scope\n{oos}\n",
        encoding="utf-8")
    # pass 1: create tickets; pass 2: wire blocking (create-then-wire, spec §9).
    # Safe because _validate_chart_input already confirmed every `blocks`
    # target is one of this map_input's own ticket keys, so pass 2 can never
    # hit a ticket file that pass 1 didn't just create.
    for t in inp["tickets"]:
        fm = {"title": t["title"], "type": t["type"], "mode": _mode(t["type"]),
              "status": "open", "assignee": "", "blocked_by": [], "gist": ""}
        _save_ticket(root, slug, t["key"], fm, f"\n## Question\n\n{t['question']}\n")
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
    _save_ticket(root, slug, ticket, fm, body + f"\n## Comment\n\n{body_text}\n")
    return {"commented": ticket}


def resolve(root, slug, ticket, gist, link, body):
    """Close `ticket` and record its resolution. Idempotent (review round 1
    finding): re-resolving the same ticket replaces the prior `## Resolution`
    section and the prior "Decisions so far" line rather than accumulating
    duplicate/contradictory ones.
    """
    fm, tbody = _load_ticket(root, slug, ticket)
    fm["status"] = "closed"
    fm["gist"] = gist
    # Drop any previously appended Resolution section -- but only up to the
    # NEXT "## " heading (or end of string if there is none), never past it.
    # A \Z-anchored strip here would delete everything from "## Resolution"
    # to end-of-file, including a comment() appended AFTER a prior resolve()
    # (comment() has no closed-ticket guard, so `resolve -> comment ->
    # resolve` is a real, documented sequence) -- silently destroying a
    # user-authored comment (review round 2, finding N1).
    tbody = re.sub(r"\n*## Resolution\n.*?(?=\n## |\Z)", "", tbody, flags=re.DOTALL)
    detail = f"\nDetail: {link}\n" if link else ""
    extra = f"\n{body}\n" if body else ""
    _save_ticket(root, slug, ticket, fm,
                 tbody + f"\n## Resolution\n\n{gist}\n{detail}{extra}")
    map_path = Path(root) / slug / "map.md"
    map_md = map_path.read_text(encoding="utf-8")
    entry = f"- [{fm['title']}](tickets/{ticket}.md) — {gist}\n"
    line_re = re.compile(
        rf"^- \[.*?\]\(tickets/{re.escape(ticket)}\.md\).*\n?", re.MULTILINE)
    if line_re.search(map_md):
        map_md = line_re.sub(entry, map_md, count=1)
    else:
        map_md = map_md.replace("## Decisions so far\n", "## Decisions so far\n" + entry, 1)
    map_path.write_text(map_md, encoding="utf-8")
    return {"resolved": ticket, "gist": gist}


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
