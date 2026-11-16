import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import plan_cuts

HERE = Path(__file__).resolve().parent
FIXTURE = HERE / "fixtures" / "plan_first_run.json"


def load():
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


class FirstRunNumbers(unittest.TestCase):
    """126 BPM, drop at song time 33.35 s, in-point 18.1 s, 21 shots, 30 fps."""

    def setUp(self):
        self.plan, self.errors = plan_cuts.compute(load())

    def test_no_errors(self):
        self.assertEqual(self.errors, [])

    def test_drop_lands_on_the_first_fast_shot_at_15_233(self):
        dc = self.plan["drop_check"]
        self.assertTrue(dc["ok"])
        self.assertEqual(dc["drop_shot"], 6)
        self.assertEqual(dc["boundary"], 15.233)
        self.assertEqual(dc["drop_timeline"], 15.25)
        self.assertAlmostEqual(dc["offset_frames"], 0.51, places=2)

    def test_total_length_is_78_beats_rounded_to_a_frame(self):
        self.assertEqual(self.plan["shots"][-1]["end"], 37.133)

    def test_every_boundary_is_a_whole_frame(self):
        for s in self.plan["shots"]:
            for key in ("start", "end"):
                frames = s[key] * 30
                self.assertAlmostEqual(frames, round(frames), delta=0.02, msg=(s["n"], key))

    def test_shots_are_contiguous(self):
        shots = self.plan["shots"]
        self.assertEqual(shots[0]["start"], 0.0)
        for a, b in zip(shots, shots[1:]):
            self.assertEqual(a["end"], b["start"])

    def test_a_two_beat_shot_and_the_trims(self):
        s = self.plan["shots"][6]  # shot 7: 2 beats from 17.133
        self.assertEqual((s["start"], s["end"], s["duration"]), (17.133, 18.1, 0.967))
        self.assertEqual(s["source_out"], 1.467)
        self.assertEqual(s["trim_start"], 0.5)
        self.assertEqual(s["trim_end"], round(s["full_duration"] - 1.467, 3))

    def test_the_kept_long_shot_runs_12_beats(self):
        s = self.plan["shots"][14]
        self.assertEqual(s["beats"], 12)
        self.assertEqual(s["duration"], 5.733)


class FrameExactTrims(unittest.TestCase):
    def test_source_in_is_snapped_to_a_frame_and_written_back(self):
        plan = load()
        plan["shots"][6]["source_in"] = 0.517  # 15.51 frames at 30 fps
        plan, errors = plan_cuts.compute(plan)
        self.assertEqual(errors, [])
        s = plan["shots"][6]
        self.assertEqual(s["source_in"], 0.533)
        self.assertEqual(s["trim_start"], 0.533)
        self.assertEqual(s["source_out"], round(0.533 + s["duration"], 3))
        self.assertEqual(s["source_out"], 1.5)


class Rejections(unittest.TestCase):
    def test_a_shot_with_no_beats_is_rejected(self):
        plan = load()
        plan["shots"][3]["beats"] = 0
        plan["shots"][4]["beats"] = -2
        _, errors = plan_cuts.compute(plan)
        self.assertEqual(errors, ["shot 4: beats must be positive",
                                  "shot 5: beats must be positive"])

    def test_a_negative_song_in_names_the_bars_to_cut(self):
        plan = load()
        plan["song_in"] = -2.0  # one bar at 126 BPM is 1.905 s, so two bars
        _, errors = plan_cuts.compute(plan)
        self.assertEqual(errors, ["song_in: negative - shorten the slow part by 2 bars"])

    def test_a_drop_that_needs_a_negative_song_in_says_so_instead(self):
        plan = load()
        plan["drop"] = 10.0  # the drop shot starts at 15.233, 5.233 s after the drop
        _, errors = plan_cuts.compute(plan)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("drop: lands at -8.100"), errors[0])
        self.assertTrue(errors[0].endswith(
            "; song_in for that boundary would be negative - shorten the slow part by 3 bars"),
            errors[0])
        self.assertNotIn("-5.2", errors[0])

    def test_a_shot_past_its_clip_is_rejected(self):
        plan = load()
        plan["shots"][2]["source_in"] = plan["shots"][2]["full_duration"] - 1.0
        _, errors = plan_cuts.compute(plan)
        self.assertEqual(len(errors), 1)
        self.assertTrue(errors[0].startswith("shot 3: source_out"), errors[0])

    def test_a_drop_off_the_boundary_names_the_in_point_that_fixes_it(self):
        plan = load()
        plan["song_in"] = 17.6  # drop now at 15.75, half a second late
        _, errors = plan_cuts.compute(plan)
        self.assertEqual(len(errors), 1)
        self.assertIn("song_in for that boundary is 18.100", errors[0])

    def test_missing_fields_are_named(self):
        plan = load()
        del plan["bpm"]
        del plan["shots"]
        _, errors = plan_cuts.compute(plan)
        self.assertEqual(errors, ["plan: missing 'bpm'", "plan: missing 'shots'"])
        plan = load()
        del plan["shots"][0]["beats"]
        _, errors = plan_cuts.compute(plan)
        self.assertEqual(errors, ["shot 1: missing beats"])

    def test_halves_round_up_not_to_even(self):
        self.assertEqual(plan_cuts.to_frame(0.5 / 30, 30), 1)
        self.assertEqual(plan_cuts.to_frame(2.5 / 30, 30), 3)

    def test_an_all_slow_plan_reports_no_drop_shot(self):
        plan = load()
        for s in plan["shots"]:
            s["part"] = "slow"
        _, errors = plan_cuts.compute(plan)
        self.assertEqual(errors, ["drop: no shot has part 'fast', so there is no drop shot"])

    def test_an_empty_shots_list_reports_no_drop_shot(self):
        plan = load()
        plan["shots"] = []
        _, errors = plan_cuts.compute(plan)
        self.assertEqual(errors, ["drop: no shot has part 'fast', so there is no drop shot"])

    def test_a_part_that_is_not_slow_or_fast_is_named(self):
        plan = load()
        plan["shots"][5]["part"] = "Fast"
        _, errors = plan_cuts.compute(plan)
        self.assertEqual(errors, ["shot 6: part must be 'slow' or 'fast', got 'Fast'"])


class Cli(unittest.TestCase):
    def run_cli(self, plan):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "plan.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(plan, fh)
            proc = subprocess.run([sys.executable, str(HERE / "plan_cuts.py"), path],
                                  capture_output=True, text=True)
            with open(path, encoding="utf-8") as fh:
                return proc, json.load(fh)

    def test_writes_the_cuts_back_and_exits_0(self):
        proc, written = self.run_cli(load())
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("drop at 15.250 on shot 6 (15.233, +0.51 frames)", proc.stdout)
        self.assertEqual(written["shots"][5]["start"], 15.233)

    def test_non_ascii_text_is_written_as_is(self):
        plan = load()
        plan["song"]["title"] = "Café Ñandú"
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "plan.json")
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(plan, fh)
            proc = subprocess.run([sys.executable, str(HERE / "plan_cuts.py"), path],
                                  capture_output=True, text=True)
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn('"Café Ñandú"', text)

    def test_an_error_exits_1_and_leaves_the_file_unchanged(self):
        plan = load()
        plan["song_in"] = 17.6
        before = copy.deepcopy(plan)
        proc, written = self.run_cli(plan)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(written, before)

    def test_an_all_slow_plan_exits_1_with_the_no_drop_line(self):
        plan = load()
        for s in plan["shots"]:
            s["part"] = "slow"
        before = copy.deepcopy(plan)
        proc, written = self.run_cli(plan)
        self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
        self.assertIn("drop: no shot has part 'fast', so there is no drop shot", proc.stdout)
        self.assertEqual(written, before)


if __name__ == "__main__":
    unittest.main()
