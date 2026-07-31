#!/usr/bin/env python3
"""local_map_ops.py — decision-map local-markdown backend (ADR 0042).

Map lives at <root>/<slug>/map.md, tickets at <root>/<slug>/tickets/<slug>.md.
Contract: plugins/decision-map/references/data-contracts.md. Stdlib only.
"""
import argparse, json, re, sys
from pathlib import Path

AFK_TYPES = {"research"}


def _mode(ticket_type):
    return "AFK" if ticket_type in AFK_TYPES else "HITL"


def _fm_parse(text):
    """Parse the leading --- frontmatter block into a dict (flat, list via [a, b])."""
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    fm = {}
    if not m:
        return fm, text
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, v = line.split(":", 1)
        v = v.strip()
        if v.startswith("[") and v.endswith("]"):
            inner = v[1:-1].strip()
            fm[k.strip()] = [s.strip() for s in inner.split(",") if s.strip()]
        else:
            fm[k.strip()] = v
    return fm, text[m.end():]


def _fm_dump(fm):
    lines = []
    for k, v in fm.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(v)}]")
        else:
            lines.append(f"{k}: {v if v is not None else ''}")
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
        "url": str(Path(root) / slug / "tickets" / f"{ticket}.md"),
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


def chart(root, inp, real):
    slug = inp["target"]["slug"]
    base = Path(root) / slug
    plan = [f"create {base / 'map.md'}"] + [
        f"create {base / 'tickets' / (t['key'] + '.md')}" for t in inp["tickets"]]
    if not real:
        print("DRY RUN — planned files:")
        for line in plan:
            print(f"  {line}")
        return {"backend": "local", "dryRun": True, "planned": plan}
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
    # pass 1: create tickets; pass 2: wire blocking (create-then-wire, spec §9)
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
                    "url": str(Path(root) / slug / "map.md"), "destination": dest},
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
    fm, tbody = _load_ticket(root, slug, ticket)
    fm["status"] = "closed"
    fm["gist"] = gist
    detail = f"\nDetail: {link}\n" if link else ""
    extra = f"\n{body}\n" if body else ""
    _save_ticket(root, slug, ticket, fm,
                 tbody + f"\n## Resolution\n\n{gist}\n{detail}{extra}")
    map_path = Path(root) / slug / "map.md"
    map_md = map_path.read_text(encoding="utf-8")
    entry = f"- [{fm['title']}](tickets/{ticket}.md) — {gist}\n"
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
    a = ap.parse_args()
    body = Path(a.body_file).read_text(encoding="utf-8") if a.body_file else None
    if a.cmd == "chart":
        inp = json.loads(Path(a.input).read_text(encoding="utf-8"))
        result = chart(a.root, inp, real=a.real and not a.dry)
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
