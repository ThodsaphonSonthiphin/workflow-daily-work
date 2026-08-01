import contextlib
import copy
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import local_map_ops as ops


def _snapshot(base):
    """Return {relative posix path: sha256 hexdigest} for every file under
    `base`. Used to prove a dry run truly wrote nothing (round-2 finding N5:
    the prior assertion compared one file's contents to itself and could
    never fail, regardless of what chart() actually did)."""
    snap = {}
    if not base.exists():
        return snap
    for p in sorted(base.rglob("*")):
        if p.is_file():
            snap[p.relative_to(base).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    return snap

# Derived by scanning, not hand-listed (round 5, N7): every character
# str.splitlines() treats as a line break. _fm_parse splits the frontmatter
# block with splitlines(), so the writer's normaliser must cover exactly this
# set. Scanning to 0x2200 covers all of them with margin; a separate one-off
# scan of the full 0x110000 range confirmed there are no others.
_SPLITLINES_SEPARATORS = [chr(c) for c in range(0x2200)
                          if len(("a" + chr(c) + "b").splitlines()) > 1]

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
    # REWRITTEN for Task 3b / ADR 0054: the guard is unchanged in substance --
    # recorded state must survive an un-forced re-chart -- but the mechanism
    # is now "skip every existing file" rather than "refuse the whole run".
    # Byte-identity is a strictly stronger assertion than the old one.
    def test_rechart_skips_existing_files_by_default(self):
        self._chart()
        ops.resolve(self.root, "example-effort", "auth-model",
                    "per-tenant keys", link=None, body=None)
        ops.claim(self.root, "example-effort", "rollout-order", "pon")
        before = _snapshot(self.root / "example-effort")
        ops.chart(self.root, INPUT, real=True)          # no longer raises
        self.assertEqual(_snapshot(self.root / "example-effort"), before)
        # nothing was destroyed
        m = ops.read_map(self.root, "example-effort")
        auth = next(t for t in m["tickets"] if t["key"] == "auth-model")
        rollout = next(t for t in m["tickets"] if t["key"] == "rollout-order")
        self.assertEqual(auth["status"], "closed")
        self.assertEqual(auth["gist"], "per-tenant keys")
        self.assertEqual(rollout["assignee"], "pon")

    # REWRITTEN for Task 3b: the action vocabulary lost "refuse" and gained
    # "skip (exists)". The dry-run-writes-nothing guard (round-2 N5) is
    # unchanged and still verified by content hash.
    def test_rechart_dry_run_reports_create_skip_overwrite_accurately(self):
        self._chart()
        base = self.root / "example-effort"
        before = _snapshot(base)
        self.assertTrue(before, "sanity: the chart fixture must have written files to snapshot")
        # default (force=False): every existing file must be reported "skip (exists)"
        out_default = ops.chart(self.root, INPUT, real=False)
        actions_default = {p["path"]: p["action"] for p in out_default["planned"]}
        self.assertTrue(actions_default)
        self.assertTrue(all(a == "skip (exists)" for a in actions_default.values()),
                        actions_default)
        self.assertNotIn("refuse", set(actions_default.values()))
        # dry run never writes, regardless of force -- verified via a real
        # content hash snapshot (round-2 finding N5: the prior version of
        # this assertion compared one file's contents to itself, which is
        # vacuously true no matter what chart() does; a mutant that made a
        # --force dry run clobber every file still passed the whole suite).
        self.assertEqual(_snapshot(base), before)
        # force=True: same files must be reported "OVERWRITE", not silently "create"
        out_force = ops.chart(self.root, INPUT, real=False, force=True)
        actions_force = {p["path"]: p["action"] for p in out_force["planned"]}
        self.assertTrue(all(a == "OVERWRITE" for a in actions_force.values()))
        self.assertEqual(_snapshot(base), before)

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

    # ------------------------------------------------------------------
    # Fix round 2 — regression tests for review findings N1-N3, N5
    # ------------------------------------------------------------------

    # N1 (Important, regression from the round-1 fix): the round-1 fix made
    # resolve() strip "## Resolution\n.*\Z" (anchored to end-of-string) before
    # re-appending -- but comment() can append AFTER a resolve (the CLI has no
    # closed-ticket guard on comment), so a second resolve()'s \Z-anchored
    # strip deleted the user-authored comment along with the stale Resolution.
    def test_resolve_after_comment_preserves_the_comment(self):
        self._chart()
        ops.resolve(self.root, "example-effort", "auth-model", "first gist", link=None, body=None)
        ops.comment(self.root, "example-effort", "auth-model", "user comment after resolve")
        ops.resolve(self.root, "example-effort", "auth-model", "second gist", link=None, body=None)
        ticket_md = (self.root / "example-effort" / "tickets" / "auth-model.md").read_text(encoding="utf-8")
        self.assertIn("user comment after resolve", ticket_md)
        self.assertEqual(ticket_md.count("## Resolution"), 1)
        self.assertIn("second gist", ticket_md)
        self.assertNotIn("first gist", ticket_md)

    # N2 (Important): target.slug was never validated, so it could carry a
    # ticket key straight past the map folder -- direct-probe-confirmed
    # against HEAD: "../../pwned-slug" landed two directories above the temp
    # root, and "C:/Windows/Temp/pwned-slug" wrote directly under
    # C:\Windows\Temp. Both payloads plus one more (absolute unix-style path)
    # must now be rejected before any file is written.
    def test_chart_rejects_unsafe_map_slug_dotdot(self):
        bad = copy.deepcopy(INPUT)
        bad["target"]["slug"] = "../../pwned-slug-n2"
        escape_target = (self.root / "../../pwned-slug-n2").resolve()
        try:
            with self.assertRaises(ops.ChartValidationError):
                ops.chart(self.root, bad, real=True)
            self.assertFalse(escape_target.exists())
        finally:
            if escape_target.exists():
                shutil.rmtree(escape_target, ignore_errors=True)

    def test_chart_rejects_unsafe_map_slug_drive_path(self):
        bad = copy.deepcopy(INPUT)
        bad["target"]["slug"] = "C:/Windows/Temp/pwned-slug-n2b"
        escape_target = Path("C:/Windows/Temp/pwned-slug-n2b")
        try:
            with self.assertRaises(ops.ChartValidationError):
                ops.chart(self.root, bad, real=True)
            self.assertFalse(escape_target.exists())
        finally:
            if escape_target.exists():
                shutil.rmtree(escape_target, ignore_errors=True)

    def test_chart_rejects_unsafe_map_slug_absolute_unix_path(self):
        bad = copy.deepcopy(INPUT)
        bad["target"]["slug"] = "/etc/pwned-slug-n2c"
        with self.assertRaises(ops.ChartValidationError):
            ops.chart(self.root, bad, real=True)

    # N3 (Minor, but directly protects round-1's Critical): _SAFE_SLUG_RE
    # used "$" (which, in Python, also matches just before a trailing
    # newline) instead of "\Z". A key like "okname\n" therefore passed
    # validation, then died with OSError while writing the ticket file --
    # AFTER map.md was already on disk (the exact half-written state the
    # module docstring claims can't happen). Must now be rejected up front.
    def test_chart_rejects_ticket_key_with_trailing_newline(self):
        bad = copy.deepcopy(INPUT)
        bad["tickets"][0]["key"] = "okname\n"
        with self.assertRaises(ops.ChartValidationError):
            ops.chart(self.root, bad, real=True)
        self.assertFalse((self.root / "example-effort").exists())

    # ------------------------------------------------------------------
    # Fix round 3 — regression tests for review findings R1-R3
    # ------------------------------------------------------------------

    # R1 (Important, introduced by round 2's fix): a --body-file containing
    # its own "## " sub-heading (e.g. "## Rationale") made the round-2
    # lookahead-based strip stop INSIDE the old Resolution block, orphaning
    # its tail. Each re-resolve leaves one more stale sub-heading behind --
    # unbounded accumulation, reintroducing round-1 finding 3's harm through
    # a documented, ordinary --resolve --body-file argument.
    def test_resolve_with_heading_in_body_does_not_accumulate(self):
        self._chart()
        ops.resolve(self.root, "example-effort", "auth-model", "gist one",
                    link=None, body="## Rationale\n\nfirst reasoning")
        ops.resolve(self.root, "example-effort", "auth-model", "gist two",
                    link=None, body="## Rationale\n\nsecond reasoning")
        ops.resolve(self.root, "example-effort", "auth-model", "gist three",
                    link=None, body="## Rationale\n\nthird reasoning")
        ticket_md = (self.root / "example-effort" / "tickets" / "auth-model.md").read_text(encoding="utf-8")
        self.assertEqual(ticket_md.count("## Resolution"), 1)
        self.assertEqual(ticket_md.count("## Rationale"), 1)
        self.assertIn("gist three", ticket_md)
        self.assertIn("third reasoning", ticket_md)
        self.assertNotIn("gist one", ticket_md)
        self.assertNotIn("gist two", ticket_md)
        self.assertNotIn("first reasoning", ticket_md)
        self.assertNotIn("second reasoning", ticket_md)

    # R2 (Important, residual of round-2's N1 fix -- narrowed, not closed):
    # the strip regex has no "^"/MULTILINE anchor and its leading "\n*" can
    # match zero characters, so the literal substring "## Resolution\n" is
    # matched WHEREVER it appears -- including inside a ticket's own Question
    # text, at a line start or truly mid-line -- deleting real user content on
    # the very FIRST resolve(), before any resolution has ever been recorded.
    def test_resolve_first_call_does_not_corrupt_question_with_heading_text_at_line_start(self):
        inp = copy.deepcopy(INPUT)
        inp["target"]["slug"] = "r2-line-effort"
        question = "Should the process include\n## Resolution\nas a required governance step?"
        inp["tickets"] = [
            {"key": "line-start", "title": "Process question", "type": "task",
             "question": question, "blocks": []},
        ]
        ops.chart(self.root, inp, real=True)
        ops.resolve(self.root, "r2-line-effort", "line-start", "resolved", link=None, body=None)
        ticket_md = (self.root / "r2-line-effort" / "tickets" / "line-start.md").read_text(encoding="utf-8")
        self.assertIn("as a required governance step?", ticket_md)

    def test_resolve_first_call_does_not_corrupt_question_with_mid_line_heading_text(self):
        inp = copy.deepcopy(INPUT)
        inp["target"]["slug"] = "r2-mid-effort"
        question = "Consider this idea: ## Resolution\nand what it implies for our timeline?"
        inp["tickets"] = [
            {"key": "mid-line", "title": "Inline question", "type": "task",
             "question": question, "blocks": []},
        ]
        ops.chart(self.root, inp, real=True)
        ops.resolve(self.root, "r2-mid-effort", "mid-line", "resolved", link=None, body=None)
        ticket_md = (self.root / "r2-mid-effort" / "tickets" / "mid-line.md").read_text(encoding="utf-8")
        self.assertIn("and what it implies for our timeline?", ticket_md)

    # R3 (Minor): the module docstring claims malformed input "fails cleanly
    # ... instead of writing a half-finished map folder" -- false for a
    # ticket missing "title" or "question" (or the map missing "title"/
    # "destination"): chart() raised a bare KeyError mid-pass-1, after map.md
    # and earlier tickets were already on disk, and the resulting partial
    # folder then trips refuse-by-default on retry, nudging the user toward
    # the destructive --force path.
    def test_chart_rejects_ticket_missing_required_field(self):
        bad = copy.deepcopy(INPUT)
        del bad["tickets"][1]["question"]  # rollout-order, second in the list
        with self.assertRaises(ops.ChartValidationError):
            ops.chart(self.root, bad, real=True)
        # must fail before ANY file is written -- not even auth-model.md
        # (the first, valid ticket), which chart's pass-1 loop would already
        # have written to disk by the time it reached the invalid one
        self.assertFalse((self.root / "example-effort").exists())

    def test_chart_rejects_map_missing_required_field(self):
        bad = copy.deepcopy(INPUT)
        del bad["map"]["destination"]
        with self.assertRaises(ops.ChartValidationError):
            ops.chart(self.root, bad, real=True)
        self.assertFalse((self.root / "example-effort").exists())

    # ------------------------------------------------------------------
    # Fix round 4 — regression tests for review findings N1, N2
    #
    # N1 (Important): round 3 replaced the needle ("## Resolution" -> a
    # namespaced HTML comment) but not the MECHANISM -- resolve() still
    # located the region it owns by pattern-searching a body whose every byte
    # is user-controlled (chart() writes `question` verbatim, comment() writes
    # `body_text`, resolve() writes `gist`/`link`/`body`). A user string
    # carrying a marker therefore reproduced BOTH earlier harms: unbounded
    # accumulation (round-1 finding 3) via an END marker, and silent deletion
    # of user text (round-2 finding N1) via a START marker. The fix escapes
    # every marker occurrence in every user-supplied string on the way in, so
    # "only resolve() ever writes these markers" is enforced, not asserted.
    # ------------------------------------------------------------------

    def _ticket_text(self, slug, ticket):
        return (self.root / slug / "tickets" / f"{ticket}.md").read_text(encoding="utf-8")

    # N1 harm (a): an END marker inside --body-file made the non-greedy match
    # stop early -- 5 resolves left 5 orphaned tails and 5 stray markers, the
    # file growing 274 -> 478 chars monotonically.
    def test_resolve_body_containing_end_marker_does_not_accumulate(self):
        self._chart()
        lengths = []
        for i in range(1, 6):
            ops.resolve(self.root, "example-effort", "auth-model", f"gist-{i}",
                        link=None,
                        body=f"Reasoning {i}.\n{ops._RESOLUTION_END}\nTAIL-{i}")
            text = self._ticket_text("example-effort", "auth-model")
            lengths.append(len(text))
            self.assertEqual(text.count(ops._RESOLUTION_START), 1,
                             f"resolve #{i}: exactly one region start expected")
            self.assertEqual(text.count(ops._RESOLUTION_END), 1,
                             f"resolve #{i}: exactly one region end expected")
            self.assertIn(f"TAIL-{i}", text, f"resolve #{i}: own body tail lost")
            self.assertIn("per-tenant or shared?", text)
        final = self._ticket_text("example-effort", "auth-model")
        for i in range(1, 5):
            self.assertNotIn(f"TAIL-{i}\n", final)   # no orphaned tails
            self.assertNotIn(f"gist-{i}", final)     # no stale gists
        # every payload is the same length, so an unchanging file length is a
        # direct assertion that nothing accumulated across the 5 resolves
        self.assertEqual(lengths, [lengths[0]] * 5,
                         f"file grew across resolves: {lengths}")

    # N1 harm (b): a Question carrying a well-formed marker PAIR lost its
    # inner text on the very FIRST resolve.
    def test_resolve_does_not_eat_a_marker_pair_inside_the_question(self):
        inp = copy.deepcopy(INPUT)
        inp["target"]["slug"] = "pair-effort"
        question = (f"Should we do X?\n{ops._RESOLUTION_START}\n## Resolution\n\n"
                    f"USER-AUTHORED-EXAMPLE\n{ops._RESOLUTION_END}\nAnd what about Y?")
        inp["tickets"] = [{"key": "t1", "title": "T one", "type": "task",
                           "question": question, "blocks": []}]
        ops.chart(self.root, inp, real=True)
        ops.resolve(self.root, "pair-effort", "t1", "answered", link=None, body=None)
        text = self._ticket_text("pair-effort", "t1")
        self.assertIn("USER-AUTHORED-EXAMPLE", text)
        self.assertIn("Should we do X?", text)
        self.assertIn("And what about Y?", text)
        # exactly one live region -- resolve()'s own; the Question's copies are
        # escaped, so they are text, not markers
        self.assertEqual(text.count(ops._RESOLUTION_START), 1)
        self.assertEqual(text.count(ops._RESOLUTION_END), 1)

    # N1 harm (b), worse variant: a Question carrying only the START marker
    # lost its prose and its trailing sentence on the SECOND resolve.
    def test_resolve_does_not_eat_prose_after_a_lone_start_marker_in_the_question(self):
        inp = copy.deepcopy(INPUT)
        inp["target"]["slug"] = "lone-effort"
        question = (f"Should we do X?\n{ops._RESOLUTION_START}\n"
                    f"IMPORTANT-USER-PROSE-AFTER-FAKE-START\nAnd Y?")
        inp["tickets"] = [{"key": "t1", "title": "T one", "type": "task",
                           "question": question, "blocks": []}]
        ops.chart(self.root, inp, real=True)
        ops.resolve(self.root, "lone-effort", "t1", "first", link=None, body=None)
        ops.comment(self.root, "lone-effort", "t1", "a human note")
        ops.resolve(self.root, "lone-effort", "t1", "second", link=None, body=None)
        text = self._ticket_text("lone-effort", "t1")
        self.assertIn("IMPORTANT-USER-PROSE-AFTER-FAKE-START", text)
        self.assertIn("And Y?", text)
        self.assertIn("a human note", text)
        self.assertIn("second", text)
        self.assertNotIn("first", text)
        self.assertEqual(text.count(ops._RESOLUTION_START), 1)
        self.assertEqual(text.count(ops._RESOLUTION_END), 1)

    # N1 harm (b), the exact harm round 2 was supposed to close: a comment()
    # written BEFORE the first resolve, carrying a START marker, was deleted
    # by the second resolve.
    def test_resolve_does_not_delete_an_early_comment_containing_a_marker(self):
        self._chart()
        ops.comment(self.root, "example-effort", "auth-model",
                    f"heads up {ops._RESOLUTION_START} IMPORTANT-COMMENT-BODY")
        ops.resolve(self.root, "example-effort", "auth-model", "first", link=None, body=None)
        ops.resolve(self.root, "example-effort", "auth-model", "second", link=None, body=None)
        text = self._ticket_text("example-effort", "auth-model")
        self.assertIn("IMPORTANT-COMMENT-BODY", text)
        self.assertIn("second", text)
        self.assertNotIn("first", text)
        self.assertEqual(text.count(ops._RESOLUTION_START), 1)
        self.assertEqual(text.count(ops._RESOLUTION_END), 1)

    # N1, leak half: a marker in --gist / --link leaked verbatim into map.md's
    # Decisions-so-far index line and into the `gist` field of read/frontier.
    def test_markers_in_gist_and_link_do_not_leak_into_map_or_json(self):
        self._chart()
        ops.resolve(self.root, "example-effort", "auth-model",
                    f"answer {ops._RESOLUTION_END} tail",
                    link=f"docs/{ops._RESOLUTION_START}.md", body=None)
        map_md = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        self.assertNotIn(ops._RESOLUTION_START, map_md)
        self.assertNotIn(ops._RESOLUTION_END, map_md)
        self.assertIn("answer", map_md)
        m = ops.read_map(self.root, "example-effort")
        auth = next(t for t in m["tickets"] if t["key"] == "auth-model")
        self.assertNotIn(ops._RESOLUTION_START, auth["gist"])
        self.assertNotIn(ops._RESOLUTION_END, auth["gist"])
        text = self._ticket_text("example-effort", "auth-model")
        self.assertEqual(text.count(ops._RESOLUTION_START), 1)
        self.assertEqual(text.count(ops._RESOLUTION_END), 1)

    # N1, extension: map.md's Decisions-so-far index was found by the same
    # class of pattern search (a "^- [...](tickets/<key>.md)" line regex over
    # the whole file), so a map `notes` line shaped like an index entry was
    # substituted away by resolve(). The index is now a generated region and
    # is rebuilt from the ticket files, so nothing outside it is ever touched.
    def test_resolve_does_not_clobber_an_index_shaped_line_in_notes(self):
        inp = copy.deepcopy(INPUT)
        inp["target"]["slug"] = "notes-effort"
        inp["map"] = dict(inp["map"])
        inp["map"]["notes"] = ("prior art:\n"
                               "- [Auth model?](tickets/auth-model.md) — USER-AUTHORED-NOTE\n"
                               "keep reading")
        ops.chart(self.root, inp, real=True)
        ops.resolve(self.root, "notes-effort", "auth-model", "REAL-GIST",
                    link=None, body=None)
        map_md = (self.root / "notes-effort" / "map.md").read_text(encoding="utf-8")
        self.assertIn("USER-AUTHORED-NOTE", map_md)
        self.assertIn("keep reading", map_md)
        self.assertIn("REAL-GIST", map_md)
        self.assertEqual(map_md.count("tickets/auth-model.md"), 2)  # the note + the index entry
        # re-resolving still updates exactly the generated entry
        ops.resolve(self.root, "notes-effort", "auth-model", "SECOND-GIST",
                    link=None, body=None)
        map_md = (self.root / "notes-effort" / "map.md").read_text(encoding="utf-8")
        self.assertIn("USER-AUTHORED-NOTE", map_md)
        self.assertIn("SECOND-GIST", map_md)
        self.assertNotIn("REAL-GIST", map_md)
        self.assertEqual(map_md.count("tickets/auth-model.md"), 2)

    # N1, backstop: the escape is the prevention, but every write also asserts
    # the file holds at most one well-formed region. A hand-edited file with a
    # stray marker must make the module REFUSE to write, not silently corrupt.
    def test_write_refuses_when_a_hand_edited_file_has_stray_markers(self):
        self._chart()
        p = self.root / "example-effort" / "tickets" / "auth-model.md"
        p.write_text(p.read_text(encoding="utf-8") + f"\n{ops._RESOLUTION_END}\n",
                     encoding="utf-8")
        with self.assertRaises(ops.MarkerIntegrityError):
            ops.claim(self.root, "example-effort", "auth-model", "pon")

    # ------------------------------------------------------------------
    # N2 (Minor, re-opens R3): validation was presence-only, so a wrong-TYPED
    # field reproduced R3's exact partial-folder harm -- `title: [1, 2]` raised
    # TypeError from _fm_dump AFTER map.md and the first ticket were on disk --
    # while `title: null`, a dict, an int and `question: null` were silently
    # accepted and written. Validate types in the same pre-write pass.
    # ------------------------------------------------------------------

    def _assert_rejected_without_writing(self, bad):
        """chart() must raise ChartValidationError and leave the filesystem
        byte-identical -- not even the <slug>/ directory, which would trip
        refuse-by-default on retry and push the user toward --force."""
        before = _snapshot(self.root)
        with self.assertRaises(ops.ChartValidationError):
            ops.chart(self.root, bad, real=True)
        self.assertEqual(_snapshot(self.root), before,
                         "validation must run before ANY write")
        self.assertFalse(any(self.root.iterdir()))

    def test_chart_rejects_wrong_typed_ticket_fields(self):
        for field, value in [("title", [1, 2]), ("title", None), ("title", {"a": 1}),
                             ("title", 42), ("question", None), ("question", 7),
                             ("type", None), ("key", 5)]:
            with self.subTest(field=field, value=value):
                bad = copy.deepcopy(INPUT)
                bad["tickets"][1][field] = value   # second ticket: pass 1 would
                                                   # already have written map.md
                                                   # and the first ticket
                self._assert_rejected_without_writing(bad)

    def test_chart_rejects_wrong_typed_map_fields(self):
        for field, value in [("title", None), ("title", 42), ("destination", None),
                             ("destination", ["a"]), ("notes", 3),
                             ("notYetSpecified", 5), ("outOfScope", "mobile"),
                             ("notYetSpecified", [1, 2])]:
            with self.subTest(field=field, value=value):
                bad = copy.deepcopy(INPUT)
                bad["map"][field] = value
                self._assert_rejected_without_writing(bad)

    # ------------------------------------------------------------------
    # Fix round 5 -- review findings N4, N5, N7
    # ------------------------------------------------------------------

    # N4: _fm_value scrubbed BEFORE collapsing line breaks, so a marker split
    # by a newline carried no marker for _scrub to find and was then
    # RECONSTITUTED into a live one by the very next collapse. Unpaired ->
    # MarkerIntegrityError mid-chart with map.md already on disk (R3's
    # partial-folder harm through a new door). Paired -> passed
    # _assert_one_region and wrote live markers into a generated file, which
    # falsifies the round-4 invariant outright.
    def test_split_marker_is_not_reconstituted_when_frontmatter_is_collapsed(self):
        inp = copy.deepcopy(INPUT)
        inp["target"]["slug"] = "n4a-effort"
        inp["tickets"] = [{"key": "t1", "type": "task", "question": "q?",
                           "title": "<!--\ndecision-map:resolution:start --> TAIL-A",
                           "blocks": []}]
        ops.chart(self.root, inp, real=True)          # must not raise
        text = self._ticket_text("n4a-effort", "t1")
        self.assertEqual(text.count(ops._RESOLUTION_START), 0)
        self.assertEqual(text.count(ops._RESOLUTION_END), 0)
        self.assertIn(ops._MARKER_ESCAPED_PREFIX, text)
        self.assertIn("TAIL-A", text)
        # the whole map folder landed, not a half-written one
        self.assertTrue((self.root / "n4a-effort" / "map.md").exists())

    def test_split_marker_pair_is_not_reconstituted_and_never_goes_live(self):
        inp = copy.deepcopy(INPUT)
        inp["target"]["slug"] = "n4b-effort"
        inp["tickets"] = [{"key": "t1", "type": "task", "question": "q?",
                           "title": ("<!--\ndecision-map:resolution:start --> MID "
                                     "<!--\ndecision-map:resolution:end --> TAIL-B"),
                           "blocks": []}]
        ops.chart(self.root, inp, real=True)
        text = self._ticket_text("n4b-effort", "t1")
        self.assertEqual(text.count(ops._RESOLUTION_START), 0)
        self.assertEqual(text.count(ops._RESOLUTION_END), 0)
        self.assertIn("MID", text)
        self.assertIn("TAIL-B", text)
        # and the same payload through --gist must not reach map.md live
        ops.resolve(self.root, "n4b-effort", "t1",
                    "<!--\ndecision-map:resolution:end --> GIST-TAIL",
                    link=None, body=None)
        text = self._ticket_text("n4b-effort", "t1")
        self.assertEqual(text.count(ops._RESOLUTION_START), 1)   # resolve's own
        self.assertEqual(text.count(ops._RESOLUTION_END), 1)
        map_md = (self.root / "n4b-effort" / "map.md").read_text(encoding="utf-8")
        self.assertNotIn(ops._RESOLUTION_START, map_md)
        self.assertNotIn(ops._RESOLUTION_END, map_md)
        self.assertEqual(map_md.count(ops._DECISIONS_START), 1)
        self.assertIn("GIST-TAIL", map_md)

    # N5 (Important): _ticket_path is byte-identical across all five commits --
    # the runtime --ticket / --map identifiers were never validated, so
    # claim/comment/resolve/block rewrote arbitrary .md files OUTSIDE --root,
    # lossily round-tripping the victim's own frontmatter on the way through.
    def _traversal_fixture(self):
        """--root is a SUBdirectory, so a traversal payload can be proven to
        land outside --root rather than merely outside the map folder."""
        mroot = self.root / "maps"
        mroot.mkdir()
        victim = self.root / "VICTIM.md"
        victim.write_text(
            "---\ntitle: not a ticket\nstatus: precious\n---\n\nUNRELATED FILE\n",
            encoding="utf-8")
        inp = copy.deepcopy(INPUT)
        ops.chart(mroot, inp, real=True)
        return mroot, victim

    TRAVERSALS = ["../../../VICTIM", "..\\..\\..\\VICTIM", "../VICTIM",
                  "C:/Windows/Temp/dm-r5-victim", "C:\\Windows\\Temp\\dm-r5-victim",
                  "/etc/passwd", "foo/bar", "", "..", None]

    def test_runtime_ticket_id_cannot_escape_the_map_folder(self):
        mroot, victim = self._traversal_fixture()
        before = _snapshot(self.root)
        body = self.root / "b.md"
        body.write_text("x", encoding="utf-8")
        before = _snapshot(self.root)
        for payload in self.TRAVERSALS:
            for op, args in [
                    ("claim", lambda t: ops.claim(mroot, "example-effort", t, "attacker")),
                    ("comment", lambda t: ops.comment(mroot, "example-effort", t, "hi")),
                    ("resolve", lambda t: ops.resolve(mroot, "example-effort", t,
                                                      "g", link=None, body=None)),
                    ("block", lambda t: ops.block(mroot, "example-effort", t, "auth-model")),
            ]:
                with self.subTest(op=op, payload=payload):
                    with self.assertRaises(ops.UnsafeIdentifierError):
                        args(payload)
                    self.assertEqual(_snapshot(self.root), before,
                                     "a rejected traversal must leave the filesystem "
                                     "byte-identical, inside AND outside --root")
        self.assertIn("UNRELATED FILE", victim.read_text(encoding="utf-8"))
        self.assertIn("status: precious", victim.read_text(encoding="utf-8"))

    def test_runtime_map_slug_cannot_escape_the_root(self):
        mroot, _ = self._traversal_fixture()
        before = _snapshot(self.root)
        for payload in self.TRAVERSALS:
            for op, fn in [("read", ops.read_map), ("frontier", ops.frontier)]:
                with self.subTest(op=op, payload=payload):
                    with self.assertRaises(ops.UnsafeIdentifierError):
                        fn(mroot, payload)
                    self.assertEqual(_snapshot(self.root), before)
            with self.subTest(op="claim-slug", payload=payload):
                with self.assertRaises(ops.UnsafeIdentifierError):
                    ops.claim(mroot, payload, "auth-model", "attacker")
                self.assertEqual(_snapshot(self.root), before)

    def test_block_rejects_an_unsafe_blocked_by_identifier(self):
        self._chart()
        before = _snapshot(self.root)
        for payload in ["../../evil", "a, b", "x\ny", None]:
            with self.subTest(payload=payload):
                with self.assertRaises(ops.UnsafeIdentifierError):
                    ops.block(self.root, "example-effort", "auth-model", payload)
                self.assertEqual(_snapshot(self.root), before)

    def test_a_stray_unsafely_named_file_does_not_break_read_or_frontier(self):
        self._chart()
        (self.root / "example-effort" / "tickets" / "not a ticket.md").write_text(
            "hand added\n", encoding="utf-8")
        m = ops.read_map(self.root, "example-effort")          # must not raise
        self.assertEqual(len(m["tickets"]), 3)
        ops.frontier(self.root, "example-effort")              # must not raise

    # N7: _fm_value normalised only CRLF/LF/CR, but _fm_parse splits the
    # frontmatter block with splitlines(), which also breaks on U+000B,
    # U+000C, U+001C, U+001D, U+001E, U+0085, U+2028 and U+2029 -- so
    # `claim --user "me<sep>status: closed"` forged a real frontmatter key and
    # the ticket silently reported itself closed.
    def test_writer_normalises_every_line_break_the_reader_splits_on(self):
        self._chart()
        for sep in _SPLITLINES_SEPARATORS:
            with self.subTest(sep="U+%04X" % ord(sep)):
                ops.claim(self.root, "example-effort", "rollout-order",
                          f"me{sep}status: closed{sep}gist: forged")
                t = next(x for x in ops.read_map(self.root, "example-effort")["tickets"]
                         if x["key"] == "rollout-order")
                self.assertEqual(t["status"], "open", "forged a status key")
                self.assertIsNone(t["gist"], "forged a gist key")
                self.assertIn("status: closed", t["assignee"],
                              "the text must survive as part of the assignee value")

    # ------------------------------------------------------------------
    # Task 3b -- `chart` is additive by default (ADR 0054)
    # ------------------------------------------------------------------

    def _plus_ticket(self, key="fog-graduate", blocks=None):
        inp = copy.deepcopy(INPUT)
        inp["tickets"].append({"key": key, "title": "Graduated from fog",
                               "type": "research", "question": "newly specified?",
                               "blocks": blocks or []})
        return inp

    def test_additive_chart_adds_a_ticket_and_leaves_existing_bytes_identical(self):
        self._chart()
        base = self.root / "example-effort"
        before = _snapshot(base)
        ops.chart(self.root, self._plus_ticket(), real=True)      # no --force
        after = _snapshot(base)
        self.assertIn("tickets/fog-graduate.md", after)
        for path, digest in before.items():
            self.assertEqual(after[path], digest,
                             f"{path} must be byte-identical after an additive chart")

    def test_rechart_identical_input_is_a_byte_identical_no_op(self):
        self._chart()
        base = self.root / "example-effort"
        before = _snapshot(base)
        ops.chart(self.root, INPUT, real=True)
        self.assertEqual(_snapshot(base), before, "re-charting identical input must be a no-op")
        ops.chart(self.root, INPUT, real=True)                    # and again
        self.assertEqual(_snapshot(base), before)

    def test_additive_chart_preserves_a_resolution_and_its_index_entry(self):
        self._chart()
        ops.claim(self.root, "example-effort", "api-limits", "pon")
        ops.resolve(self.root, "example-effort", "auth-model", "per-tenant keys",
                    link="docs/adr/0007-x.md", body="## Rationale\n\nblast radius")
        base = self.root / "example-effort"
        before = _snapshot(base)
        ops.chart(self.root, self._plus_ticket(), real=True)
        auth = self._ticket_text("example-effort", "auth-model")
        self.assertEqual(after_start := auth.count(ops._RESOLUTION_START), 1, after_start)
        self.assertIn("per-tenant keys", auth)
        self.assertIn("blast radius", auth)
        self.assertEqual(before["tickets/auth-model.md"],
                         _snapshot(base)["tickets/auth-model.md"])
        m = ops.read_map(self.root, "example-effort")
        auth_json = next(t for t in m["tickets"] if t["key"] == "auth-model")
        self.assertEqual(auth_json["status"], "closed")
        self.assertEqual(next(t for t in m["tickets"]
                              if t["key"] == "api-limits")["assignee"], "pon")
        map_md = (base / "map.md").read_text(encoding="utf-8")
        self.assertIn("[Auth model?](tickets/auth-model.md) — per-tenant keys", map_md)

    def test_additive_chart_merges_fog_and_scope_without_duplication(self):
        self._chart()
        inp = self._plus_ticket()
        inp["map"] = dict(inp["map"])
        inp["map"]["notYetSpecified"] = ["how to deploy", "NEW-FOG-LINE"]
        inp["map"]["outOfScope"] = ["mobile app", "NEW-SCOPE-LINE"]
        ops.chart(self.root, inp, real=True)
        map_md = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        self.assertEqual(map_md.count("- how to deploy"), 1, "existing line duplicated")
        self.assertEqual(map_md.count("- mobile app"), 1, "existing line duplicated")
        self.assertEqual(map_md.count("- NEW-FOG-LINE"), 1)
        self.assertEqual(map_md.count("- NEW-SCOPE-LINE"), 1)
        # order preserved: the pre-existing line stays first
        self.assertLess(map_md.index("- how to deploy"), map_md.index("- NEW-FOG-LINE"))
        # the merge must not disturb the decisions region
        self.assertEqual(map_md.count(ops._DECISIONS_START), 1)
        # and merging the same input again changes nothing
        before = _snapshot(self.root / "example-effort")
        ops.chart(self.root, inp, real=True)
        self.assertEqual(_snapshot(self.root / "example-effort"), before)
        # ADR 0054: "never remove existing ones". An input that OMITS a line
        # already on disk must not delete it -- the merge is a union, not a
        # replacement. (Without this the suite could not tell a real merge
        # from "wipe the region and write the input", because every other
        # case here happens to re-list the lines already present.)
        inp2 = self._plus_ticket()
        inp2["map"] = dict(inp2["map"])
        inp2["map"]["notYetSpecified"] = ["ONLY-THIS-ONE"]
        inp2["map"]["outOfScope"] = []
        ops.chart(self.root, inp2, real=True)
        map_md = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        for kept in ("- how to deploy", "- NEW-FOG-LINE", "- mobile app",
                     "- NEW-SCOPE-LINE", "- ONLY-THIS-ONE"):
            self.assertIn(kept, map_md, f"{kept} must survive a merge that omits it")

    def test_additive_chart_leaves_divergent_destination_and_notes_alone(self):
        self._chart()
        inp = self._plus_ticket()
        inp["map"] = dict(inp["map"])
        inp["map"]["destination"] = "A COMPLETELY DIFFERENT DESTINATION"
        inp["map"]["notes"] = "DIFFERENT NOTES"
        out = ops.chart(self.root, inp, real=True)
        map_md = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        self.assertIn("a spec", map_md, "on-disk destination must survive")
        self.assertIn("use grill-with-docs", map_md, "on-disk notes must survive")
        self.assertNotIn("A COMPLETELY DIFFERENT DESTINATION", map_md)
        self.assertNotIn("DIFFERENT NOTES", map_md)
        fields = " ".join(out["divergence"])
        self.assertIn("destination", fields)
        self.assertIn("notes", fields)
        # --force is how you actually change them
        ops.chart(self.root, inp, real=True, force=True)
        map_md = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        self.assertIn("A COMPLETELY DIFFERENT DESTINATION", map_md)

    # REWRITTEN for ADR 0055: the edge is now UNIONED into the existing ticket
    # instead of being dropped and reported. The guarantee is restated as
    # "never removes, never reorders, never overwrites" -- so this test pins
    # the scoped identity: exactly one blockedBy entry gained, every other
    # byte of the file unchanged.
    def test_additive_chart_unions_a_new_edge_into_an_existing_ticket(self):
        self._chart()
        base = self.root / "example-effort"
        target = base / "tickets" / "api-limits.md"
        # The target carries RECORDED STATE. Without this the test cannot
        # distinguish a union from "rewrite the ticket fresh, then append the
        # edge" -- a default-valued ticket looks identical either way, and
        # that is exactly the bug an adversarial probe caught here: a ticket
        # whose action became "merge" fell through pass 1's skip check and
        # had its claim silently cleared.
        ops.claim(self.root, "example-effort", "api-limits", "pon")
        ops.comment(self.root, "example-effort", "api-limits", "a human note")
        before_text = target.read_text(encoding="utf-8")
        self.assertIn("assignee: pon", before_text)
        before_tree = _snapshot(base)
        ops.chart(self.root, self._plus_ticket(blocks=["api-limits"]), real=True)
        after_text = target.read_text(encoding="utf-8")
        # the edge is live in the model, and api-limits is not offered as
        # actionable (it reports under `claimed` because it is claimed --
        # frontier() checks assignee before blockers)
        m = ops.read_map(self.root, "example-effort")
        api = next(t for t in m["tickets"] if t["key"] == "api-limits")
        self.assertIn("fog-graduate", api["blockedBy"],
                      "the unioned edge must be visible to readers")
        f = ops.frontier(self.root, "example-effort")
        self.assertNotIn("api-limits", [t["id"] for t in f["frontier"]])
        self.assertIn("api-limits", [t["id"] for t in f["claimed"]])
        # scoped identity: ONLY the blocked_by line changed
        b_lines, a_lines = before_text.splitlines(), after_text.splitlines()
        self.assertEqual(len(b_lines), len(a_lines), "line count must not change")
        differing = [i for i, (x, y) in enumerate(zip(b_lines, a_lines)) if x != y]
        self.assertEqual(len(differing), 1,
                         f"exactly one line may change, got {differing}")
        self.assertTrue(a_lines[differing[0]].startswith("blocked_by:"),
                        f"the changed line must be blocked_by, got {a_lines[differing[0]]!r}")
        self.assertEqual(b_lines[differing[0]], "blocked_by: []")
        self.assertEqual(a_lines[differing[0]], "blocked_by: [fog-graduate]")
        # the recorded state is explicitly still there
        self.assertIn("assignee: pon", after_text)
        self.assertIn("a human note", after_text)
        # every OTHER ticket is still byte-identical
        for path, digest in before_tree.items():
            if path != "tickets/api-limits.md":
                self.assertEqual(_snapshot(base)[path], digest, f"{path} changed")
        # unioning the same edge again is a no-op, byte for byte
        frozen = _snapshot(base)
        ops.chart(self.root, self._plus_ticket(blocks=["api-limits"]), real=True)
        self.assertEqual(_snapshot(base), frozen,
                         "re-unioning an edge already present must change nothing")

    def test_additive_chart_unions_an_edge_without_relisting_the_target(self):
        """ADR 0055 / F3: an edge may name a ticket that exists on disk but is
        not re-listed in this input's tickets[]."""
        self._chart()
        inp = copy.deepcopy(INPUT)
        inp["tickets"] = [{"key": "late-arrival", "title": "Late", "type": "task",
                           "question": "q?",
                           "blocks": ["rollout-order", "api-limits"]}]
        # api-limits is open, unclaimed and unblocked, so it is on the
        # frontier right now -- ADR 0055's stated harm is that it would STAY
        # there while a just-created ticket is meant to block it.
        self.assertIn("api-limits",
                      [t["id"] for t in ops.frontier(self.root, "example-effort")["frontier"]])
        ops.chart(self.root, inp, real=True)
        m = ops.read_map(self.root, "example-effort")
        rollout = next(t for t in m["tickets"] if t["key"] == "rollout-order")
        self.assertIn("late-arrival", rollout["blockedBy"])
        self.assertIn("auth-model", rollout["blockedBy"], "existing edge must survive")
        self.assertEqual(len(m["tickets"]), 4)
        f = ops.frontier(self.root, "example-effort")
        self.assertNotIn("api-limits", [t["id"] for t in f["frontier"]],
                         "a blocked ticket must not still be reported actionable")
        self.assertIn("late-arrival",
                      {b["id"]: b["blockedBy"] for b in f["blocked"]}.get("api-limits", []))

    def test_chart_still_rejects_an_edge_to_a_target_that_exists_nowhere(self):
        self._chart()
        before = _snapshot(self.root)
        bad = self._plus_ticket(blocks=["ghost-ticket"])
        with self.assertRaises(ops.ChartValidationError):
            ops.chart(self.root, bad, real=True)
        self.assertEqual(_snapshot(self.root), before)

    # F1: the edge was computed only AFTER the dry-run returned, so the
    # ADR-0039 approval gate was silent about a write it was about to make.
    def test_dry_run_reports_the_edge_it_will_union(self):
        self._chart()
        base = self.root / "example-effort"
        before = _snapshot(base)
        out = ops.chart(self.root, self._plus_ticket(blocks=["api-limits"]), real=False)
        entries = {Path(p["path"]).name: p for p in out["planned"]}
        self.assertEqual(entries["api-limits.md"]["action"], "merge",
                         "a ticket that will gain an edge is not a skip")
        self.assertIn("fog-graduate", entries["api-limits.md"].get("detail") or "",
                      f"the plan must name the edge: {entries['api-limits.md']}")
        self.assertEqual(entries["auth-model.md"]["action"], "skip (exists)")
        self.assertEqual(_snapshot(base), before, "a dry run must never write")
        # the plan told the truth: the real run changes exactly that file
        ops.chart(self.root, self._plus_ticket(blocks=["api-limits"]), real=True)
        after = _snapshot(base)
        self.assertNotEqual(after["tickets/api-limits.md"], before["tickets/api-limits.md"])
        self.assertEqual(after["tickets/auth-model.md"], before["tickets/auth-model.md"])

    def test_dry_run_stderr_renders_the_edge_detail(self):
        self._chart()
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ops.chart(self.root, self._plus_ticket(blocks=["api-limits"]), real=False)
        text = err.getvalue()
        self.assertIn("merge", text)
        # assert the DETAIL specifically -- "fog-graduate" alone is no proof,
        # the created ticket's own path line already contains that word
        self.assertIn("unions blockedBy", text,
                      f"the human rendering must name the edge too: {text!r}")

    def test_dry_run_json_carries_divergence_and_edge_only_targets(self):
        self._chart()
        inp = copy.deepcopy(INPUT)
        inp["tickets"] = [{"key": "late-arrival", "title": "Late", "type": "task",
                           "question": "q?", "blocks": ["api-limits"]}]
        inp["map"] = dict(inp["map"], destination="DIFFERENT")
        out = ops.chart(self.root, inp, real=False)
        # the plan must include a target that is NOT re-listed in tickets[]
        names = {Path(p["path"]).name: p for p in out["planned"]}
        self.assertIn("api-limits.md", names,
                      f"an edge-only target must appear in the plan: {list(names)}")
        self.assertEqual(names["api-limits.md"]["action"], "merge")
        # the dry run must carry divergence too, not only the real run
        self.assertIn("divergence", out)
        self.assertTrue(any("destination" in d for d in out["divergence"]),
                        f"dry-run divergence lost: {out}")

    def test_dry_run_stderr_renders_divergence(self):
        self._chart()
        inp = self._plus_ticket()
        inp["map"] = dict(inp["map"], destination="DIFFERENT")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ops.chart(self.root, inp, real=False)
        self.assertIn("divergence", err.getvalue())
        self.assertIn("destination", err.getvalue())

    def test_real_run_stderr_renders_divergence(self):
        self._chart()
        inp = self._plus_ticket()
        inp["map"] = dict(inp["map"], destination="DIFFERENT")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            ops.chart(self.root, inp, real=True)
        self.assertIn("divergence", err.getvalue())
        self.assertIn("destination", err.getvalue())

    def test_block_does_not_rewrite_when_the_edge_is_already_present(self):
        """The byte-identical no-op depends on block() not writing at all --
        a rewrite happens to produce the same bytes for files this module
        wrote, so only a file that does NOT round-trip exactly can prove it."""
        self._chart()
        p = self.root / "example-effort" / "tickets" / "rollout-order.md"
        odd = p.read_text(encoding="utf-8").replace(
            "blocked_by: [auth-model]", "blocked_by:   [auth-model]")
        self.assertIn("blocked_by:   [auth-model]", odd, "sanity: fixture rewritten")
        p.write_text(odd, encoding="utf-8")
        ops.block(self.root, "example-effort", "rollout-order", "auth-model")
        self.assertEqual(p.read_text(encoding="utf-8"), odd,
                         "block() must not write when the edge is already present")
        ops.chart(self.root, INPUT, real=True)      # additive re-chart, same edge
        self.assertEqual(p.read_text(encoding="utf-8"), odd,
                         "an additive re-chart must not rewrite it either")

    # F2: every message that steers the user to --force must say what --force
    # destroys. The reviewer followed this advice and lost a resolution.
    def test_force_advice_always_warns_what_force_destroys(self):
        """Every message that steers the user to re-charting must state the
        cost -- checked across BOTH divergence sources, not just the scalar
        one, since each builds its own sentence."""
        def assert_warned(messages, label):
            self.assertTrue(messages, f"sanity: expected {label} divergence")
            warned = 0
            for message in messages:
                if "--force" in message or "re-chart" in message.lower():
                    lowered = message.lower()
                    self.assertTrue(
                        any(w in lowered for w in ("discard", "destroy")),
                        f"{label}: advice must state the cost: {message!r}")
                    self.assertIn("resolution", lowered,
                                  f"{label}: name what is lost: {message!r}")
                    warned += 1
            self.assertTrue(warned, f"{label}: no message mentioned re-charting")

        # source 1: a divergent scalar
        self._chart()
        inp = self._plus_ticket()
        inp["map"] = dict(inp["map"], destination="DIFFERENT", notes="DIFFERENT")
        assert_warned(ops.chart(self.root, inp, real=True)["divergence"], "scalar")

        # source 2: a map.md predating the list regions
        inp2 = copy.deepcopy(INPUT)
        inp2["target"] = dict(inp2["target"], slug="legacy-effort")
        ops.chart(self.root, inp2, real=True)
        mp = self.root / "legacy-effort" / "map.md"
        legacy = mp.read_text(encoding="utf-8")
        for marker in (ops._FOG_START, ops._FOG_END, ops._SCOPE_START, ops._SCOPE_END):
            legacy = legacy.replace(marker, "")
        mp.write_text(legacy, encoding="utf-8")
        inp2["map"] = dict(inp2["map"], notYetSpecified=["how to deploy", "NEW"])
        assert_warned(ops.chart(self.root, inp2, real=True)["divergence"], "legacy region")

    # N5 (parked Minor): the legacy map.md path -- an existing map with no fog
    # or scope regions -- was never exercised.
    def test_legacy_map_without_list_regions_is_reported_not_mangled(self):
        self._chart()
        mp = self.root / "example-effort" / "map.md"
        legacy = mp.read_text(encoding="utf-8")
        legacy = legacy.replace(ops._FOG_START, "").replace(ops._FOG_END, "")
        legacy = legacy.replace(ops._SCOPE_START, "").replace(ops._SCOPE_END, "")
        mp.write_text(legacy, encoding="utf-8")
        inp = self._plus_ticket()
        inp["map"] = dict(inp["map"], notYetSpecified=["how to deploy", "BRAND-NEW-FOG"])
        out = ops.chart(self.root, inp, real=True)
        after = mp.read_text(encoding="utf-8")
        self.assertIn("- how to deploy", after, "legacy content must survive untouched")
        self.assertNotIn("BRAND-NEW-FOG", after, "must not guess where to insert")
        self.assertTrue(any("notYetSpecified" in d for d in out["divergence"]),
                        f"the un-merged lines must be reported: {out['divergence']}")
        self.assertTrue((self.root / "example-effort" / "tickets"
                         / "fog-graduate.md").exists(), "the ticket still lands")

    def test_additive_chart_dry_run_labels_create_and_skip_and_writes_nothing(self):
        self._chart()
        base = self.root / "example-effort"
        before = _snapshot(base)
        out = ops.chart(self.root, self._plus_ticket(), real=False)
        actions = {Path(p["path"]).name: p["action"] for p in out["planned"]}
        self.assertEqual(actions["fog-graduate.md"], "create")
        self.assertEqual(actions["auth-model.md"], "skip (exists)")
        self.assertEqual(actions["rollout-order.md"], "skip (exists)")
        self.assertNotIn("refuse", set(actions.values()))
        self.assertEqual(_snapshot(base), before, "a dry run must never write")
        # a `skip` must never write: the real run agrees with the plan
        ops.chart(self.root, self._plus_ticket(), real=True)
        after = _snapshot(base)
        for name, action in actions.items():
            if action == "skip (exists)":
                key = f"tickets/{name}" if name != "map.md" else "map.md"
                self.assertEqual(after[key], before[key], f"{name} was labelled skip but changed")

    def test_markers_in_fog_and_scope_survive_the_additive_path_escaped(self):
        self._chart()
        inp = self._plus_ticket()
        inp["map"] = dict(inp["map"])
        inp["map"]["notYetSpecified"] = [f"how to deploy",
                                         f"FOG {ops._RESOLUTION_START} TAIL",
                                         f"SPLIT <!--\ndecision-map:decisions:start --> TAIL2"]
        inp["map"]["outOfScope"] = [f"SCOPE {ops._DECISIONS_END} TAIL3"]
        ops.chart(self.root, inp, real=True)
        map_md = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        self.assertEqual(map_md.count(ops._RESOLUTION_START), 0)
        self.assertEqual(map_md.count(ops._DECISIONS_START), 1)   # the real region only
        self.assertEqual(map_md.count(ops._DECISIONS_END), 1)
        for canary in ("TAIL", "TAIL2", "TAIL3"):
            self.assertIn(canary, map_md)
        ops.resolve(self.root, "example-effort", "auth-model", "g", link=None, body=None)
        map_md = (self.root / "example-effort" / "map.md").read_text(encoding="utf-8")
        self.assertEqual(map_md.count(ops._DECISIONS_START), 1)
        self.assertIn("TAIL2", map_md)

    def test_additive_chart_refuses_traversal_the_same_way(self):
        self._chart()
        before = _snapshot(self.root)
        bad = self._plus_ticket()
        bad["target"] = dict(bad["target"], slug="../../../pwned")
        with self.assertRaises(ops.ChartValidationError):
            ops.chart(self.root, bad, real=True)
        self.assertEqual(_snapshot(self.root), before)

    # F6 (parked Minor, closed here because this change touches the assertion):
    # _assert_regions' "every decision-map marker belongs to a declared region"
    # check was load-bearing but unguarded -- a mutant dropping it survived the
    # whole suite. This test passes against 3f0f61e by design; it is validated
    # against a mutant instead (see the report).
    def test_write_refuses_when_a_stray_marker_prefix_is_present(self):
        self._chart()
        p = self.root / "example-effort" / "tickets" / "auth-model.md"
        p.write_text(p.read_text(encoding="utf-8") + "\n<!-- decision-map:bogus -->\n",
                     encoding="utf-8")
        with self.assertRaises(ops.MarkerIntegrityError):
            ops.claim(self.root, "example-effort", "auth-model", "pon")

    def test_chart_rejects_wrong_typed_containers(self):
        cases = []
        bad = copy.deepcopy(INPUT); bad["tickets"] = {"a": 1}; cases.append(bad)
        bad = copy.deepcopy(INPUT); bad["tickets"][0] = "not a dict"; cases.append(bad)
        bad = copy.deepcopy(INPUT); bad["map"] = "not a dict"; cases.append(bad)
        bad = copy.deepcopy(INPUT); del bad["target"]; cases.append(bad)
        bad = copy.deepcopy(INPUT); bad["target"]["slug"] = 7; cases.append(bad)
        bad = copy.deepcopy(INPUT); bad["tickets"][0]["blocks"] = "rollout-order"
        cases.append(bad)
        bad = copy.deepcopy(INPUT); bad["tickets"][0]["blocks"] = [1]; cases.append(bad)
        del bad
        for i, case in enumerate(cases):
            with self.subTest(case=i):
                self._assert_rejected_without_writing(case)


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

    def _run_full(self, argv):
        """Drive main() and return (exit_code, stdout, stderr).

        Round 5: main() no longer raises for a known failure -- it prints one
        line to stderr and returns a distinct exit code, and stdout carries
        JSON or nothing. Streams must therefore be captured separately.
        """
        old_argv = sys.argv
        sys.argv = ["local_map_ops.py"] + argv
        out, err = io.StringIO(), io.StringIO()
        try:
            with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                rc = ops.main()
        finally:
            sys.argv = old_argv
        return rc, out.getvalue(), err.getvalue()

    def _run(self, argv):
        rc, out, err = self._run_full(argv)
        self.assertEqual(rc, 0, f"expected success, got rc={rc}: {err}")
        return out

    def test_cli_chart_dry_run_then_real_then_frontier(self):
        rc, out, err = self._run_full(
            ["chart", "--root", str(self.root), "--input", str(self.input_path)])
        self.assertEqual(rc, 0)
        # the human-readable plan goes to stderr; stdout is pure JSON
        self.assertIn("DRY RUN", err)
        self.assertEqual(json.loads(out)["dryRun"], True)
        self.assertFalse((self.root / "example-effort").exists())

        out = self._run(["chart", "--root", str(self.root), "--input", str(self.input_path), "--real"])
        data = json.loads(out)
        self.assertEqual(data["backend"], "local")
        self.assertTrue((self.root / "example-effort" / "map.md").exists())

        out = self._run(["frontier", "--root", str(self.root), "--map", "example-effort"])
        data = json.loads(out)
        self.assertIn("auth-model", [t["id"] for t in data["frontier"]])

    # F3 (parked Minor, closed here because Task 3b is about dry-run
    # truthfulness): --dry-run short-circuited BEFORE the identifier guard, so
    # `claim --dry-run --ticket ../../../VICTIM` reported rc=0 "wouldRun" for a
    # call the real run rejects with rc=2. Inert, but an untruthful dry run.
    def test_cli_dry_run_validates_identifiers_before_reporting_success(self):
        self._run(["chart", "--root", str(self.root), "--input", str(self.input_path),
                   "--real"])
        for argv in (["claim", "--ticket", "../../../VICTIM", "--user", "x"],
                     ["resolve", "--ticket", "../../../VICTIM", "--gist", "g"],
                     ["block", "--ticket", "auth-model", "--blocked-by", "../../x"],
                     ["claim", "--ticket", "auth-model", "--user", "x"]):
                     # last one is valid and must still succeed
            full = argv[:1] + ["--root", str(self.root), "--map", "example-effort",
                               "--dry-run"] + argv[1:]
            rc, out, err = self._run_full(full)
            unsafe = any(".." in a for a in argv)
            with self.subTest(argv=argv):
                if unsafe:
                    self.assertEqual(rc, ops.EXIT_ERROR,
                                     "a dry run must reject what the real run rejects")
                    self.assertEqual(out, "")
                else:
                    self.assertEqual(rc, 0)
                    self.assertEqual(json.loads(out)["dryRun"], True)

    # REWRITTEN for Task 3b / ADR 0054: the CLI-level re-chart assertion flips
    # from "refuses with EXIT_ERROR" to "succeeds additively". The clean-error
    # contract it also guarded (round 5) is still covered, by
    # test_cli_known_failures_are_clean_one_line_errors.
    def test_cli_claim_resolve_and_additive_rechart(self):
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

        # CLI-level re-chart is now ADDITIVE (ADR 0054): it succeeds, writes
        # nothing that already exists, and preserves the resolution above.
        base = self.root / "example-effort"
        before = _snapshot(base)
        rc, out, err = self._run_full(
            ["chart", "--root", str(self.root), "--input", str(self.input_path), "--real"])
        self.assertEqual(rc, 0)
        self.assertEqual(json.loads(out)["backend"], "local")
        self.assertEqual(_snapshot(base), before,
                         "an additive re-chart of identical input must write nothing")
        # explicit --force opt-in still works from the CLI
        out = self._run(["chart", "--root", str(self.root), "--input", str(self.input_path),
                          "--real", "--force"])
        data = json.loads(out)
        self.assertEqual(data["backend"], "local")

    # Deferred across rounds 1-4, landed in round 5: known failures must not
    # surface as raw tracebacks with empty stdout.
    def test_cli_known_failures_are_clean_one_line_errors(self):
        self._run(["chart", "--root", str(self.root), "--input", str(self.input_path),
                   "--real"])
        cases = {
            "unsafe ticket id": ["claim", "--root", str(self.root), "--map",
                                 "example-effort", "--ticket", "../../../VICTIM"],
            "unsafe map slug": ["frontier", "--root", str(self.root), "--map", "../.."],
            "missing ticket file": ["claim", "--root", str(self.root), "--map",
                                    "example-effort", "--ticket", "nope"],
            "missing --input": ["chart", "--root", str(self.root), "--real"],
            "missing --map": ["claim", "--root", str(self.root), "--ticket", "auth-model"],
            "missing --gist": ["resolve", "--root", str(self.root), "--map",
                               "example-effort", "--ticket", "auth-model"],
            "unreadable --input": ["chart", "--root", str(self.root), "--input",
                                   str(self.root / "nope.json"), "--real"],
        }
        for label, argv in cases.items():
            with self.subTest(case=label):
                rc, out, err = self._run_full(argv)
                self.assertEqual(rc, ops.EXIT_ERROR,
                                 "known failure needs its own exit code")
                self.assertEqual(out, "", "stdout must carry JSON or nothing")
                self.assertEqual(len(err.strip().splitlines()), 1,
                                 f"expected exactly one line of diagnostics, got: {err!r}")
                self.assertTrue(err.startswith("error: "), err)

    def test_cli_process_exit_code_is_wired(self):
        """The in-process tests above check main()'s return value; this one
        proves __main__ actually turns it into a process exit code."""
        script = Path(ops.__file__)
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        ok = subprocess.run(
            [sys.executable, str(script), "chart", "--root", str(self.root),
             "--input", str(self.input_path)], capture_output=True, text=True, env=env)
        self.assertEqual(ok.returncode, 0)
        json.loads(ok.stdout)                     # stdout is pure JSON
        bad = subprocess.run(
            [sys.executable, str(script), "claim", "--root", str(self.root),
             "--map", "example-effort", "--ticket", "../../../VICTIM"],
            capture_output=True, text=True, env=env)
        self.assertEqual(bad.returncode, ops.EXIT_ERROR)
        self.assertEqual(bad.stdout, "")
        self.assertNotIn("Traceback", bad.stderr)
        self.assertTrue(bad.stderr.startswith("error: "), bad.stderr)

    def _write_body(self, text):
        p = self.root / "body.md"
        p.write_text(text, encoding="utf-8")
        return p


if __name__ == "__main__":
    unittest.main()
