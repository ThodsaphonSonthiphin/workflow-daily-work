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


def validate(model):
    report = Report()
    actors = {a.get("id") for a in model.get("actors") or []}
    use_cases = {u.get("id") for u in model.get("use_cases") or []}
    _check_duplicate_ids(model, report)
    _check_actor_refs(model, actors, report)
    _check_scope_use_cases(model, use_cases, report)
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
