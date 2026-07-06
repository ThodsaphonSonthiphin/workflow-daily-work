#!/usr/bin/env python3
"""validate_model.py — referential-integrity gate for sa-doc's sa-model.yaml.

Usage: python validate_model.py <path-to-sa-model.yaml>
Exit codes: 0 = clean (warnings allowed), 1 = errors, 2 = cannot run.
Every rule exists because the reviewed Project SA.pdf failed it.
"""
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    print("ERROR: PyYAML is required. Install with: pip install pyyaml")
    sys.exit(2)


class Report:
    def __init__(self):
        self.errors = []    # list[(rule, message)]
        self.warnings = []  # list[(rule, message)]
        self.tbds = []      # list[path-string]

    def error(self, rule, msg):
        self.errors.append((rule, msg))

    def warn(self, rule, msg):
        self.warnings.append((rule, msg))

    @property
    def ok(self):
        return not self.errors


def load_model(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _ids(items):
    return [i.get("id") for i in (items or [])]


def _check_duplicate_ids(model, report):
    """E6 — id uniqueness across every id-carrying list."""
    sections = {
        "actors": model.get("actors"),
        "use_cases": model.get("use_cases"),
        "entities": model.get("entities"),
        "screens": model.get("screens"),
        "nfrs": model.get("nfrs"),
        "security": model.get("security"),
        "problem.current_problems": (model.get("problem") or {}).get("current_problems"),
        "problem.objectives": (model.get("problem") or {}).get("objectives"),
        "problem.benefits": (model.get("problem") or {}).get("benefits"),
    }
    for name, items in sections.items():
        ids = _ids(items)
        for dup in sorted({i for i in ids if i and ids.count(i) > 1}):
            report.error("E6", f"duplicate id '{dup}' in {name}")


def _check_actor_refs(model, actors, report):
    """E1 — every referenced actor exists."""
    for uc in model.get("use_cases") or []:
        for a in uc.get("actors") or []:
            if a not in actors:
                report.error("E1", f"{uc.get('id')} references unknown actor '{a}'")
        for step in uc.get("main_flow") or []:
            a = step.get("actor")
            if a and a not in actors:
                report.error("E1", f"{uc.get('id')} step {step.get('step')} "
                                   f"references unknown actor '{a}'")
    for sc in model.get("scope") or []:
        if sc.get("actor") not in actors:
            report.error("E1", f"scope '{sc.get('capability')}' references "
                               f"unknown actor '{sc.get('actor')}'")


def _check_scope_use_cases(model, use_cases, report):
    """E2 — every scope capability lists >= 1 existing use case."""
    for sc in model.get("scope") or []:
        refs = sc.get("use_cases") or []
        cap = sc.get("capability")
        if not refs:
            report.error("E2", f"scope capability '{cap}' lists no use case")
        for u in refs:
            if u not in use_cases:
                report.error("E2", f"scope capability '{cap}' references "
                                   f"unknown use case '{u}'")


BOOL_TYPES = {"bool", "boolean", "bit"}


def _fields_by_entity(model):
    return {e.get("id"): {f.get("name") for f in e.get("fields") or []}
            for e in model.get("entities") or []}


def _check_fk_targets(model, report):
    """E3 — every fk targets an existing entity.field."""
    fields = _fields_by_entity(model)
    for ent in model.get("entities") or []:
        for f in ent.get("fields") or []:
            fk = f.get("fk")
            if not fk:
                continue
            target_entity, _, target_field = str(fk).partition(".")
            if target_entity not in fields or target_field not in fields[target_entity]:
                report.error("E3", f"{ent.get('id')}.{f.get('name')} fk '{fk}' "
                                   f"targets a non-existent field")


def _check_step_field_refs(model, report):
    """E4 — step field refs exist on the use case's entities."""
    fields = _fields_by_entity(model)
    for uc in model.get("use_cases") or []:
        allowed = set()
        for eid in uc.get("entities") or []:
            allowed |= {f"{eid}.{name}" for name in fields.get(eid, set())}
        steps = (uc.get("main_flow") or []) + (uc.get("extensions") or [])
        for step in steps:
            for ref in step.get("fields") or []:
                if ref not in allowed:
                    report.error("E4", f"{uc.get('id')} references '{ref}' which "
                                       f"is not on its entities")


def _check_states(model, entities, use_cases, report):
    """E5 — state groups are storable and transitions reference real use cases."""
    for group in model.get("states") or []:
        eid, fname = group.get("entity"), group.get("field")
        ent = entities.get(eid)
        if ent is None:
            report.error("E5", f"states group references unknown entity '{eid}'")
            continue
        field = next((f for f in ent.get("fields") or []
                      if f.get("name") == fname), None)
        if field is None:
            report.error("E5", f"states group for {eid} names missing field '{fname}'")
            continue
        n_states = len(group.get("states") or [])
        if str(field.get("type", "")).lower() in BOOL_TYPES and n_states > 2:
            report.error("E5", f"{eid}.{fname} is boolean but must hold "
                               f"{n_states} states")
        for t in group.get("transitions") or []:
            uc = t.get("uc")
            if uc and uc not in use_cases:
                report.error("E5", f"transition {t.get('from')}->{t.get('to')} "
                                   f"references unknown use case '{uc}'")


def _month_index(ym):
    year, _, month = str(ym).partition("-")
    return int(year) * 12 + int(month)


def _check_plan(model, report):
    """E7 — plan phases: from <= to, ordered, no gap between phases."""
    phases = (model.get("plan") or {}).get("phases") or []
    prev_to = None
    for ph in phases:
        try:
            start, end = _month_index(ph.get("from")), _month_index(ph.get("to"))
        except (ValueError, TypeError):
            report.error("E7", f"phase '{ph.get('name')}' has a malformed month")
            continue
        if start > end:
            report.error("E7", f"phase '{ph.get('name')}' starts after it ends")
        if prev_to is not None and start > prev_to + 1:
            report.error("E7", f"phase '{ph.get('name')}' leaves a gap in the plan")
        if prev_to is not None and start < prev_to - 12:
            report.error("E7", f"phase '{ph.get('name')}' jumps backwards")
        prev_to = max(end, prev_to) if prev_to is not None else end


def _check_profile(model, report):
    """E8 — professional profile requires a non-empty security section."""
    profile = (model.get("meta") or {}).get("profile")
    if profile == "professional" and not model.get("security"):
        report.error("E8", "profile=professional requires a non-empty "
                           "security section")


def validate(model):
    report = Report()
    actors = {a.get("id") for a in model.get("actors") or []}
    use_cases = {u.get("id") for u in model.get("use_cases") or []}
    entities = {e.get("id"): e for e in model.get("entities") or []}
    _check_duplicate_ids(model, report)
    _check_actor_refs(model, actors, report)
    _check_scope_use_cases(model, use_cases, report)
    _check_fk_targets(model, report)
    _check_step_field_refs(model, report)
    _check_states(model, entities, use_cases, report)
    _check_plan(model, report)
    _check_profile(model, report)
    return report


def print_report(report):
    for rule, msg in report.errors:
        print(f"ERROR   {rule}: {msg}")
    for rule, msg in report.warnings:
        print(f"WARNING {rule}: {msg}")
    if report.tbds:
        print(f"TBD ({len(report.tbds)}):")
        for path in report.tbds:
            print(f"  - {path}")
    print(f"{len(report.errors)} error(s), {len(report.warnings)} warning(s), "
          f"{len(report.tbds)} TBD(s)")


def main(argv):
    if len(argv) != 2:
        print(__doc__)
        return 2
    report = validate(load_model(argv[1]))
    print_report(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
