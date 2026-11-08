import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import compare_timeline
import plan_cuts

HERE = Path(__file__).resolve().parent
FIX = HERE / "fixtures"


def plan():
    p, errors = plan_cuts.compute(json.loads((FIX / "plan_first_run.json").read_text("utf-8")))
    assert not errors, errors
    return p


def timeline():
    return json.loads((FIX / "timeline_first_run.json").read_text("utf-8"))


def onsets():
    return json.loads((FIX / "onsets_first_run.json").read_text("utf-8"))


def main_clips(tl):
    return [e for e in tl["elements"] if e["trackId"] == "TRACK-MAIN"]


class Trimmed(unittest.TestCase):
    def test_the_first_run_timeline_matches(self):
        self.assertEqual(compare_timeline.compare(plan(), timeline()), [])

    def test_a_shot_one_and_a_half_frames_late_is_named(self):
        tl = timeline()
        main_clips(tl)[7]["startTime"] = 18.1 + 1.5 / 30
        self.assertEqual(compare_timeline.compare(plan(), tl),
                         ["shot 8: start 18.150 ≠ planned 18.100"])

    def test_within_one_frame_is_a_match(self):
        tl = timeline()
        main_clips(tl)[7]["startTime"] = 18.1 + 0.9 / 30
        self.assertEqual(compare_timeline.compare(plan(), tl), [])

    def test_a_negative_trim_that_did_nothing_shows_as_source_out(self):
        tl = timeline()
        clip = main_clips(tl)[3]
        clip["sourceOutPoint"] += 0.5
        self.assertEqual(compare_timeline.compare(plan(), tl, stage="trimmed"),
                         ["shot 4: source out 3.833 ≠ planned 3.333"])

    def test_a_missing_clip_is_counted(self):
        tl = timeline()
        tl["elements"].remove(main_clips(tl)[-1])
        self.assertIn("timeline: 20 clips on the main track, plan has 21",
                      compare_timeline.compare(plan(), tl))

    def test_a_swapped_pair_of_clips_is_named(self):
        tl = timeline()
        c = main_clips(tl)
        c[3]["aliasId"], c[4]["aliasId"] = c[4]["aliasId"], c[3]["aliasId"]
        self.assertEqual(compare_timeline.compare(plan(), tl),
                         ["shot 4: clip ALIAS-05 ≠ planned ALIAS-04",
                          "shot 5: clip ALIAS-04 ≠ planned ALIAS-05"])

    def test_a_clip_without_an_alias_is_named(self):
        tl = timeline()
        del main_clips(tl)[2]["aliasId"]
        self.assertEqual(compare_timeline.compare(plan(), tl),
                         ["shot 3: clip missing from the read-back"])

    def test_a_clip_on_an_overlay_track_is_named(self):
        tl = timeline()
        tl["tracks"].append({"id": "TRACK-OVER", "behavior": "free", "type": "video"})
        main_clips(tl)[-1]["trackId"] = "TRACK-OVER"
        out = compare_timeline.compare(plan(), tl)
        self.assertTrue(out[0].startswith("timeline: 1 clip(s) on an overlay track"), out)

    def test_a_video_clip_on_a_track_typed_overlay_is_named(self):
        # the live app (2026-11-08) types its overlay tracks "overlay", not "video"
        tl = timeline()
        tl["tracks"].append({"id": "TRACK-OVER", "behavior": "free", "type": "overlay"})
        tl["elements"].append({"id": "EL-X", "trackId": "TRACK-OVER", "content": "video",
                               "aliasId": "ALIAS-01", "startTime": 2.0, "endTime": 4.0})
        self.assertEqual(compare_timeline.compare(plan(), tl),
                         ["timeline: 1 clip(s) on an overlay track - "
                          "add whole clips on the main track, then trim"])

    def test_text_on_an_overlay_track_is_named_separately(self):
        tl = timeline()
        tl["tracks"].append({"id": "TRACK-OVER", "behavior": "free", "type": "overlay"})
        tl["elements"] += [
            {"id": "EL-T", "trackId": "TRACK-OVER", "content": "text", "startTime": 0.0, "endTime": 3.0},
            {"id": "EL-A", "trackId": "TRACK-OVER", "content": "adjustment", "startTime": 3.0, "endTime": 6.0}]
        self.assertEqual(compare_timeline.compare(plan(), tl),
                         ["timeline: 2 text/adjustment element(s) on overlay tracks"])


def whole_clips(p, extra=0.0):
    """Every planned clip whole, laid out contiguously, each `extra` s longer than planned."""
    t, els = 0.0, []
    for s in p["shots"]:
        d = s["full_duration"] + extra
        els.append({"trackId": "TRACK-MAIN", "aliasId": s["alias_id"], "startTime": t,
                    "endTime": t + d, "sourceInPoint": 0.0, "sourceOutPoint": d})
        t += d
    return {"tracks": timeline()["tracks"], "elements": els}


class Added(unittest.TestCase):
    def test_clips_7_ms_longer_than_planned_do_not_add_up_to_a_mismatch(self):
        # 21 clips x 7 ms = 147 ms: a running sum would fail shot 6 onwards
        self.assertEqual(compare_timeline.compare(plan(), whole_clips(plan(), 0.007),
                                                  stage="added"), [])

    def test_a_gap_before_shot_4_names_shot_4s_start_only(self):
        tl = whole_clips(plan())
        for e in tl["elements"][3:]:
            e["startTime"] += 0.5
            e["endTime"] += 0.5
        self.assertEqual(compare_timeline.compare(plan(), tl, stage="added"),
                         ["shot 4: start 24.500 ≠ planned 24.000"])

    def test_a_trimmed_clip_names_its_end(self):
        tl = whole_clips(plan())
        c = tl["elements"][1]
        c["sourceInPoint"] = 0.5
        self.assertEqual(compare_timeline.compare(plan(), tl, stage="added"),
                         ["shot 2: source in 0.500 ≠ planned 0.000"])

    def test_a_short_clip_names_its_end_not_the_next_start(self):
        tl = whole_clips(plan())
        shift = -1.0
        tl["elements"][2]["endTime"] += shift
        for e in tl["elements"][3:]:
            e["startTime"] += shift
            e["endTime"] += shift
        self.assertEqual(compare_timeline.compare(plan(), tl, stage="added"),
                         ["shot 3: end 23.000 ≠ planned 24.000"])

    def test_whole_clips_in_order(self):
        p = plan()
        t, els = 0.0, []
        for s in p["shots"]:
            d = s["full_duration"]
            els.append({"trackId": "TRACK-MAIN", "aliasId": s["alias_id"], "startTime": t,
                        "endTime": t + d, "sourceInPoint": 0.0, "sourceOutPoint": d})
            t += d
        tl = {"tracks": timeline()["tracks"], "elements": els}
        self.assertEqual(compare_timeline.compare(p, tl, stage="added"), [])
        # true swap of shots 1 and 2: shot 2's clip now sits at 0.0-8.8, shot 1's at 8.8-17.6
        els[0]["aliasId"], els[1]["aliasId"] = els[1]["aliasId"], els[0]["aliasId"]
        self.assertEqual(compare_timeline.compare(p, tl, stage="added"),
                         ["shot 1: clip ALIAS-02 ≠ planned ALIAS-01",
                          "shot 2: clip ALIAS-01 ≠ planned ALIAS-02"])


class Music(unittest.TestCase):
    def test_deleted_music_is_named(self):
        tl = timeline()
        tl["elements"] = [e for e in tl["elements"] if e["trackId"] != "TRACK-MUSIC"]
        out = compare_timeline.compare(plan(), tl)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("music: no element on an audio track"))

    def test_wrong_in_point(self):
        tl = timeline()
        tl["elements"][-1]["sourceInPoint"] = 0.0
        self.assertEqual(compare_timeline.compare(plan(), tl),
                         ["music: in-point 0.000 ≠ planned 18.100"])

    def test_a_sound_effect_beside_the_music_is_not_a_second_song(self):
        tl = timeline()
        tl["elements"][-1]["content"] = "music"
        tl["elements"].append({"id": "EL-FX", "trackId": "TRACK-MUSIC", "content": "soundEffect",
                               "startTime": 5.0, "endTime": 6.0, "sourceInPoint": 0.0})
        self.assertEqual(compare_timeline.compare(plan(), tl), [])

    def test_only_a_sound_effect_is_no_music(self):
        tl = timeline()
        tl["elements"][-1]["content"] = "soundEffect"
        out = compare_timeline.compare(plan(), tl)
        self.assertEqual(len(out), 1)
        self.assertTrue(out[0].startswith("music: no element on an audio track"), out)

    def test_trimmed_stage_ignores_music(self):
        tl = timeline()
        tl["elements"][-1]["sourceInPoint"] = 0.0
        self.assertEqual(compare_timeline.compare(plan(), tl, stage="trimmed"), [])


class Onsets(unittest.TestCase):
    def test_the_first_run_onsets_pass(self):
        self.assertEqual(compare_timeline.check_onsets(plan(), onsets()), ([], []))

    def test_a_drop_hit_two_frames_off_fails(self):
        o = onsets()
        o["pieces"][0]["onsets"][0] += 2 / 30
        failures, _ = compare_timeline.check_onsets(plan(), o)
        self.assertEqual(len(failures), 1)
        self.assertTrue(failures[0].startswith("drop: cut 15.233"), failures)

    def test_a_fast_cut_three_frames_off_fails(self):
        o = onsets()
        o["pieces"][0]["onsets"][1] += 0.1  # shot 7's hit, now 100 ms late
        failures, notes = compare_timeline.check_onsets(plan(), o)
        self.assertEqual(notes, [])
        self.assertEqual(len(failures), 1)
        self.assertTrue(failures[0].startswith("shot 7: cut 17.133"), failures)

    def test_a_cut_with_no_onset_near_is_a_note_not_a_failure(self):
        o = onsets()
        del o["pieces"][0]["onsets"][1]
        failures, notes = compare_timeline.check_onsets(plan(), o)
        self.assertEqual(failures, [])
        self.assertEqual(notes, ["shot 7: cut 17.133 has no onset within 0.3 s"])

    def test_a_cut_outside_every_render_fails(self):
        o = onsets()
        o["pieces"].pop()
        failures, _ = compare_timeline.check_onsets(plan(), o)
        self.assertTrue(any("is not inside any render" in f for f in failures), failures)


class Cli(unittest.TestCase):
    def run_cli(self, tl, *extra):
        with tempfile.TemporaryDirectory() as tmp:
            pp, tp = os.path.join(tmp, "plan.json"), os.path.join(tmp, "timeline.json")
            with open(pp, "w", encoding="utf-8") as fh:
                json.dump(plan(), fh)
            with open(tp, "w", encoding="utf-8") as fh:
                json.dump(tl, fh)
            return subprocess.run([sys.executable, str(HERE / "compare_timeline.py"), pp, tp,
                                   *extra], capture_output=True, text=True)

    def test_match_exits_0(self):
        proc = self.run_cli(timeline(), "--onsets", str(FIX / "onsets_first_run.json"))
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout.strip(), "match: 21 shots (final)")

    def test_added_stage_match_exits_0(self):
        proc = self.run_cli(whole_clips(plan()), "--stage", "added")
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertEqual(proc.stdout.strip(), "match: 21 shots (added)")

    def test_mismatch_exits_1_and_prints_the_line(self):
        tl = timeline()
        main_clips(tl)[7]["startTime"] = 18.15
        proc = self.run_cli(tl)
        self.assertEqual(proc.returncode, 1)
        self.assertEqual(proc.stdout.strip(), "shot 8: start 18.150 ≠ planned 18.100")


if __name__ == "__main__":
    unittest.main()
