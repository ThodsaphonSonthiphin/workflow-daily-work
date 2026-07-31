import json, tempfile, unittest
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
        ops.block(self.root, "example-effort", "api-limits", "auth-model")
        f = ops.frontier(self.root, "example-effort")
        self.assertNotIn("api-limits", [t["id"] for t in f["frontier"]])

if __name__ == "__main__":
    unittest.main()
