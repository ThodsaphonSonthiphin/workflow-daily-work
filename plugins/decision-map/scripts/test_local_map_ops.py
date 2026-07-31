import contextlib
import copy
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

import local_map_ops as ops

INPUT = {
    "target": {"slug": "example-effort"},
    "map": {"title": "Decision map — example", "destination": "a spec",
            "notes": "use grill-with-docs",
            "notYetSpecified": ["how to deploy"], "outOfScope": ["mobile app"]},
    "tickets": [
        {"key": "auth-model", "title": "Auth model?", "type": "grilling",
         "question": "per-tenant or shared?", "blocks": ["rollout-order"]},
        {"key": "rollout-order", "title": "Rollout order?", "type": "grilling",
         "question": "which env first?", "blocks": []},
        {"key": "api-limits", "title": "API rate limits?", "type": "research",
         "question": "what are the limits?", "blocks": []},
    ],
}

class LocalMapOpsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _chart(self):
        return ops.chart(self.root, INPUT, real=True)

    def test_chart_dry_run_writes_nothing(self):
        ops.chart(self.root, INPUT, real=False)
        self.assertFalse((self.root / "example-effort").exists())

    def test_chart_creates_map_and_tickets(self):
        out = self._chart()
        self.assertTrue((self.root / "example-effort" / "map.md").exists())
        self.assertTrue((self.root / "example-effort" / "tickets" / "auth-model.md").exists())
        self.assertEqual(out["backend"], "local")
        self.assertEqual(len(out["tickets"]), 3)
        modes = {t["key"]: t["mode"] for t in out["tickets"]}
        self.assertEqual(modes["api-limits"], "AFK")
        self.assertEqual(modes["auth-model"], "HITL")

    def test_frontier_excludes_blocked_and_claimed(self):
        self._chart()
        ops.claim(self.root, "example-effort", "api-limits", "pon")
        f = ops.frontier(self.root, "example-effort")
        names = [t["id"] for t in f["frontier"]]
        self.assertIn("auth-model", names)          # open, unblocked, unclaimed
        self.assertNotIn("rollout-order", names)     # blocked by auth-model
        self.assertNotIn("api-limits", names)        # claimed
        self.assertEqual(f["blocked"][0]["blockedBy"], ["auth-model"])
        # P1 regression guard: read_map()'s ticket dicts must expose the
        # upstream-blocker relation under the key "blockedBy" (output shape),
        # never "blocked_by" (that key name is the on-disk frontmatter format).
        m = ops.read_map(self.root, "example-effort")
        rollout = next(t for t in m["tickets"] if t["key"] == "rollout-order")
        self.assertEqual(rollout["blockedBy"], ["auth-model"])
        self.assertNotIn("blocked_by", rollout)

    def test_resolve_closes_and_indexes(self):
        self._chart()
        ops.resolve(self.root, "example-effort", "auth-model",
                    "per-tenant keys", link="docs/adr/0007-x.md", body=None)
        m = ops.read_map(self.root, "example-effort")
        t = next(t for t in m["tickets"] if t["key"] == "auth-model")
        self.assertEqual(t["status"], "closed")
        self.assertEqual(t["gist"], "per-tenant keys")
        map_md = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        self.assertIn("[Auth model?](tickets/auth-model.md) — per-tenant keys", map_md)
        # unblocking: rollout-order now on the frontier
        f = ops.frontier(self.root, "example-effort")
        self.assertIn("rollout-order", [t["id"] for t in f["frontier"]])

    def test_block_adds_edge(self):
        self._chart()
        result = ops.block(self.root, "example-effort", "api-limits", "auth-model")
        # Finding 6: block()'s return value was never asserted, so the P1
        # rename (blocked_by -> blockedBy) was untested — reverting rename #3
        # alone left all tests green. Lock the actual return shape down here.
        self.assertEqual(result, {"ticket": "api-limits", "blockedBy": ["auth-model"]})
        self.assertNotIn("blocked_by", result)
        f = ops.frontier(self.root, "example-effort")
        self.assertNotIn("api-limits", [t["id"] for t in f["frontier"]])

    # ------------------------------------------------------------------
    # Fix round 1 — regression tests for review findings
    # ------------------------------------------------------------------

    # Finding 1 (Critical): re-charting an existing map folder must never
    # silently destroy recorded state (claims, resolutions, blocking edges).
    def test_rechart_refuses_by_default_when_files_exist(self):
        self._chart()
        ops.resolve(self.root, "example-effort", "auth-model",
                    "per-tenant keys", link=None, body=None)
        ops.claim(self.root, "example-effort", "rollout-order", "pon")
        with self.assertRaises(ops.ChartConflictError):
            ops.chart(self.root, INPUT, real=True)
        # nothing was destroyed by the refused attempt
        m = ops.read_map(self.root, "example-effort")
        auth = next(t for t in m["tickets"] if t["key"] == "auth-model")
        rollout = next(t for t in m["tickets"] if t["key"] == "rollout-order")
        self.assertEqual(auth["status"], "closed")
        self.assertEqual(auth["gist"], "per-tenant keys")
        self.assertEqual(rollout["assignee"], "pon")

    def test_rechart_dry_run_reports_create_overwrite_refuse_accurately(self):
        self._chart()
        # default (force=False): every existing file must be reported "refuse"
        out_default = ops.chart(self.root, INPUT, real=False)
        actions_default = {p["path"]: p["action"] for p in out_default["planned"]}
        self.assertTrue(actions_default)
        self.assertTrue(all(a == "refuse" for a in actions_default.values()))
        # force=True: same files must be reported "OVERWRITE", not silently "create"
        out_force = ops.chart(self.root, INPUT, real=False, force=True)
        actions_force = {p["path"]: p["action"] for p in out_force["planned"]}
        self.assertTrue(all(a == "OVERWRITE" for a in actions_force.values()))
        # dry run never writes, regardless of force
        self.assertEqual(
            (self.root / "example-effort" / "tickets" / "auth-model.md").read_text(encoding="utf-8"),
            (self.root / "example-effort" / "tickets" / "auth-model.md").read_text(encoding="utf-8"))

    def test_rechart_with_force_overwrites_explicitly(self):
        self._chart()
        ops.resolve(self.root, "example-effort", "auth-model",
                    "per-tenant keys", link=None, body=None)
        ops.chart(self.root, INPUT, real=True, force=True)
        m = ops.read_map(self.root, "example-effort")
        auth = next(t for t in m["tickets"] if t["key"] == "auth-model")
        # explicit, informed opt-in: fresh content wins
        self.assertEqual(auth["status"], "open")

    # Bundled "validate the input" fixes, alongside finding 4
    def test_chart_rejects_unsafe_ticket_key(self):
        bad = copy.deepcopy(INPUT)
        bad["tickets"][0]["key"] = "../../pwned"
        with self.assertRaises(ops.ChartValidationError):
            ops.chart(self.root, bad, real=True)
        self.assertFalse((self.root / "example-effort").exists())

    def test_chart_rejects_invalid_ticket_type(self):
        bad = copy.deepcopy(INPUT)
        bad["tickets"][0]["type"] = "reserch"
        with self.assertRaises(ops.ChartValidationError):
            ops.chart(self.root, bad, real=True)
        self.assertFalse((self.root / "example-effort").exists())

    # Finding 4: an unknown `blocks` target must fail validation before any
    # file is written — not crash pass 2 with a half-written map folder.
    def test_chart_rejects_unknown_blocks_target(self):
        bad = copy.deepcopy(INPUT)
        bad["tickets"][0]["blocks"] = ["ghost-ticket"]
        with self.assertRaises(ops.ChartValidationError):
            ops.chart(self.root, bad, real=True)
        self.assertFalse((self.root / "example-effort").exists())

    # Finding 2: a frontmatter value that merely looks bracketed must not be
    # coerced into a list — only the known `blocked_by` field is a list.
    def test_bracket_and_comma_values_are_not_coerced_to_lists(self):
        inp = copy.deepcopy(INPUT)
        inp["target"]["slug"] = "brackets-effort"
        inp["tickets"] = [
            {"key": "spike", "title": "[spike] rollout order [v2]", "type": "task",
             "question": "q?", "blocks": []},
        ]
        ops.chart(self.root, inp, real=True)
        m = ops.read_map(self.root, "brackets-effort")
        t = next(t for t in m["tickets"] if t["key"] == "spike")
        self.assertEqual(t["name"], "[spike] rollout order [v2]")
        ops.resolve(self.root, "brackets-effort", "spike",
                    "[deferred to ADR 0007, see notes]", link=None, body=None)
        m2 = ops.read_map(self.root, "brackets-effort")
        t2 = next(t for t in m2["tickets"] if t["key"] == "spike")
        self.assertEqual(t2["gist"], "[deferred to ADR 0007, see notes]")

    def test_newline_in_title_does_not_corrupt_frontmatter(self):
        inp = copy.deepcopy(INPUT)
        inp["target"]["slug"] = "newline-effort"
        inp["tickets"] = [
            {"key": "nl-ticket", "title": "Multi\nline title", "type": "task",
             "question": "q?", "blocks": []},
        ]
        ops.chart(self.root, inp, real=True)
        m = ops.read_map(self.root, "newline-effort")
        t = next(t for t in m["tickets"] if t["key"] == "nl-ticket")
        self.assertNotIn("\n", t["name"])
        # the continuation after the embedded newline must survive (collapsed
        # to a space), not be silently dropped -- a bare title-truncation
        # check here would pass even on the buggy parser, because the
        # dropped continuation line ("line title") has no ":" in it and so
        # doesn't yet corrupt the *next* key's parse.
        self.assertEqual(t["name"], "Multi line title")
        # subsequent frontmatter keys must parse cleanly (not corrupted/dropped)
        self.assertEqual(t["type"], "task")
        self.assertEqual(t["mode"], "HITL")
        self.assertEqual(t["status"], "open")

    # Finding 3: resolve() must be re-entrant.
    def test_resolve_is_idempotent(self):
        self._chart()
        ops.resolve(self.root, "example-effort", "auth-model", "first gist", link=None, body=None)
        ops.resolve(self.root, "example-effort", "auth-model", "second gist", link=None, body=None)
        ticket_md = (self.root / "example-effort" / "tickets" / "auth-model.md").read_text(encoding="utf-8")
        self.assertEqual(ticket_md.count("## Resolution"), 1)
        self.assertIn("second gist", ticket_md)
        self.assertNotIn("first gist", ticket_md)
        map_md = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        self.assertEqual(map_md.count("tickets/auth-model.md"), 1)
        self.assertIn("second gist", map_md)
        self.assertNotIn("first gist", map_md)

    # Finding 5: urls must use forward slashes so `[name](url)` markdown links
    # aren't broken by backslash (Markdown's escape character) on Windows.
    def test_urls_use_forward_slashes(self):
        out = self._chart()
        for t in out["tickets"]:
            self.assertNotIn("\\", t["url"])
        m = ops.read_map(self.root, "example-effort")
        self.assertNotIn("\\", m["map"]["url"])
        for t in m["tickets"]:
            self.assertNotIn("\\", t["url"])
        f = ops.frontier(self.root, "example-effort")
        for t in f["frontier"]:
            self.assertNotIn("\\", t["url"])

    # Finding 6: comment() had no coverage at all.
    def test_comment_appends_section(self):
        self._chart()
        result = ops.comment(self.root, "example-effort", "auth-model",
                              "checking with security team")
        self.assertEqual(result, {"commented": "auth-model"})
        ticket_md = (self.root / "example-effort" / "tickets" / "auth-model.md").read_text(encoding="utf-8")
        self.assertIn("## Comment", ticket_md)
        self.assertIn("checking with security team", ticket_md)


class LocalMapOpsCliTest(unittest.TestCase):
    """Finding 6: main()/argparse had zero coverage. Drive the real CLI
    entry point (sys.argv + main()) rather than calling the functions
    directly, to prove the argument wiring itself works."""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.input_path = self.root / "map_input.json"
        self.input_path.write_text(json.dumps(INPUT), encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, argv):
        old_argv = sys.argv
        sys.argv = ["local_map_ops.py"] + argv
        buf = io.StringIO()
        try:
            with contextlib.redirect_stdout(buf):
                ops.main()
        finally:
            sys.argv = old_argv
        return buf.getvalue()

    def test_cli_chart_dry_run_then_real_then_frontier(self):
        out = self._run(["chart", "--root", str(self.root), "--input", str(self.input_path)])
        self.assertIn("DRY RUN", out)
        self.assertFalse((self.root / "example-effort").exists())

        out = self._run(["chart", "--root", str(self.root), "--input", str(self.input_path), "--real"])
        data = json.loads(out)
        self.assertEqual(data["backend"], "local")
        self.assertTrue((self.root / "example-effort" / "map.md").exists())

        out = self._run(["frontier", "--root", str(self.root), "--map", "example-effort"])
        data = json.loads(out)
        self.assertIn("auth-model", [t["id"] for t in data["frontier"]])

    def test_cli_claim_resolve_and_rechart_refusal(self):
        self._run(["chart", "--root", str(self.root), "--input", str(self.input_path), "--real"])

        out = self._run(["claim", "--root", str(self.root), "--map", "example-effort",
                          "--ticket", "auth-model", "--user", "pon"])
        self.assertEqual(json.loads(out), {"claimed": "auth-model", "assignee": "pon"})

        out = self._run(["resolve", "--root", str(self.root), "--map", "example-effort",
                          "--ticket", "auth-model", "--gist", "per-tenant keys"])
        self.assertEqual(json.loads(out)["resolved"], "auth-model")

        out = self._run(["comment", "--root", str(self.root), "--map", "example-effort",
                          "--ticket", "rollout-order",
                          "--body-file", str(self._write_body("noted"))])
        self.assertEqual(json.loads(out), {"commented": "rollout-order"})

        # CLI-level re-chart refusal (finding 1), not just the function call
        with self.assertRaises(ops.ChartConflictError):
            self._run(["chart", "--root", str(self.root), "--input", str(self.input_path), "--real"])
        # explicit --force opt-in still works from the CLI
        out = self._run(["chart", "--root", str(self.root), "--input", str(self.input_path),
                          "--real", "--force"])
        data = json.loads(out)
        self.assertEqual(data["backend"], "local")

    def _write_body(self, text):
        p = self.root / "body.md"
        p.write_text(text, encoding="utf-8")
        return p


if __name__ == "__main__":
    unittest.main()
