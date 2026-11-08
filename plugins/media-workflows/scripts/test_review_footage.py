import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import review_footage as rf

HERE = Path(__file__).resolve().parent
HAVE_FFMPEG = shutil.which("ffmpeg") and shutil.which("ffprobe")


class Pure(unittest.TestCase):
    def test_frame_times_are_centred_in_equal_slices(self):
        self.assertEqual(rf.frame_times(8.0, 4), [1.0, 3.0, 5.0, 7.0])

    def test_creation_time_tag_wins(self):
        info = {"format": {"tags": {"creation_time": "2025-01-01T05:00:00Z"}}}
        self.assertEqual(rf.capture_time(info, "/x/VID_20250101_000000.mp4"),
                         ("2025-01-01T05:00:00+00:00", "creation_time"))

    def test_stream_creation_time_is_used_when_format_has_none(self):
        info = {"format": {}, "streams": [{"tags": {"creation_time": "2026-11-07T07:00:00Z"}}]}
        self.assertEqual(rf.capture_time(info, "/x/a.mp4")[1], "creation_time")

    def test_file_name_is_the_fallback(self):
        self.assertEqual(rf.capture_time({"format": {}}, "/x/VID_20250101_120000.mp4"),
                         ("2025-01-01T12:00:00+00:00", "file name"))

    def test_mtime_is_the_last_resort(self):
        with tempfile.NamedTemporaryFile(suffix=".mp4") as fh:
            os.utime(fh.name, (1_800_000_000, 1_800_000_000))
            when, source = rf.capture_time({"format": {}}, fh.name)
        self.assertEqual(source, "mtime")
        self.assertEqual(dt.datetime.fromisoformat(when).timestamp(), 1_800_000_000)

    def test_a_rotated_portrait_clip_reports_its_shown_size(self):
        info = {"streams": [{"codec_type": "video", "width": 3840, "height": 2160,
                             "side_data_list": [{"rotation": -90}]}]}
        self.assertEqual(rf.display_size(info), (2160, 3840))
        info["streams"][0]["side_data_list"] = [{"rotation": 180}]
        self.assertEqual(rf.display_size(info), (3840, 2160))

    def test_parts_split_at_the_gap(self):
        clips = [{"capture_time": f"2026-11-07T{h}:00+00:00"} for h in
                 ("09:00", "09:15", "09:40", "13:00")]
        parts = rf.split_parts(clips, 20)
        self.assertEqual([len(p) for p in parts], [2, 1, 1])

    def test_rms_lines_are_parsed_and_silence_floors(self):
        text = ("frame:0 pts:0 pts_time:0\nlavfi.astats.Overall.RMS_level=-23.41\n"
                "frame:1 pts:8000 pts_time:0.5\nlavfi.astats.Overall.RMS_level=-inf\n")
        self.assertEqual(rf.parse_rms(text), [-23.4, -120.0])

    def test_creation_time_is_found_on_a_later_stream(self):
        info = {"format": {}, "streams": [{"tags": {}},
                                          {"tags": {"creation_time": "2026-11-07T07:00:00Z"}}]}
        self.assertEqual(rf.capture_time(info, "/x/VID_20250101_000000.mp4"),
                         ("2026-11-07T07:00:00+00:00", "creation_time"))

    def test_row_image_seeks_each_frame_before_decoding(self):
        calls = []

        def fake_run(cmd):
            calls.append(cmd)
            if cmd[-1].endswith((".png", ".jpg")):
                open(cmd[-1], "wb").close()
            return ""

        with tempfile.TemporaryDirectory() as tmp, \
                mock.patch("review_footage.run", side_effect=fake_run):
            rf.row_image("/x/clip.mov", [0.5, 1.5, 2.5], os.path.join(tmp, "row.jpg"), tmp)
        cells = [c for c in calls if c[-1].endswith(".png")]
        self.assertEqual([c[c.index("-ss") + 1] for c in cells], ["0.500", "1.500", "2.500"])
        for c in cells:
            self.assertLess(c.index("-ss"), c.index("-i"))


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not installed")
class WithFfmpeg(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)

        def make(name, size, seconds, when, audio=True):
            cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                   "-i", f"testsrc=size={size}:rate=30:duration={seconds}"]
            if audio:
                cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}",
                        "-c:a", "aac", "-shortest"]
            cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-metadata", f"creation_time={when}", str(cls.dir / name)]
            subprocess.run(cmd, check=True)

        make("late.mov", "320x240", 1, "2026-11-07T11:00:00Z")
        make("first.mov", "320x240", 2, "2026-11-07T09:00:00Z")
        make("silent.mov", "240x320", 3, "2026-11-07T09:05:00Z", audio=False)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
                        "-i", "testsrc=size=320x240:rate=30:duration=1",
                        "-f", "lavfi", "-i", "sine=frequency=440:duration=5",
                        "-c:a", "aac", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-metadata", "creation_time=2026-11-07T09:10:00Z",
                        str(cls.dir / "skew.mov")], check=True)
        cls.out = cls.dir / "review"
        cls.result = rf.review([str(cls.dir / n) for n in ("late.mov", "first.mov", "silent.mov")],
                               str(cls.out), frames=4, gap_minutes=20)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_clips_are_sorted_by_capture_time_and_split_into_parts(self):
        self.assertEqual([c["name"] for c in self.result["clips"]],
                         ["first.mov", "silent.mov", "late.mov"])
        self.assertEqual([p["clips"] for p in self.result["parts"]],
                         [["first.mov", "silent.mov"], ["late.mov"]])

    def test_numbers_per_clip(self):
        first = self.result["clips"][0]
        self.assertAlmostEqual(first["duration"], 2.0, delta=0.1)
        self.assertEqual((first["width"], first["height"]), (320, 240))
        self.assertEqual(first["frame_times"], rf.frame_times(first["duration"], 4))
        self.assertEqual(len(first["loudness_db"]), 4)  # 2 s in 0.5 s steps
        self.assertGreater(min(first["loudness_db"]), -40)
        self.assertEqual(self.result["clips"][1]["loudness_db"], [])  # no audio stream

    def test_row_image_is_one_cell_per_frame(self):
        info = rf.probe(str(self.out / self.result["clips"][0]["row_image"]))
        self.assertEqual(rf.display_size(info), (rf.CELL_W * 4, rf.CELL_H))

    def test_part_sheet_stacks_the_rows(self):
        info = rf.probe(str(self.out / self.result["parts"][0]["sheet"]))
        self.assertEqual(rf.display_size(info), (rf.CELL_W * 4, rf.CELL_H * 2))

    def test_review_json_is_written(self):
        written = json.loads((self.out / "review.json").read_text("utf-8"))
        self.assertEqual(written, self.result)

    def test_duration_comes_from_the_video_stream(self):
        result = rf.review([str(self.dir / "skew.mov")], str(self.dir / "skew-review"), frames=4)
        self.assertAlmostEqual(result["clips"][0]["duration"], 1.0, delta=0.1)

    def test_a_seek_past_the_last_frame_names_the_clip(self):
        with self.assertRaisesRegex(RuntimeError, "first.mov"):
            rf.row_image(str(self.dir / "first.mov"), [99.0],
                         str(self.dir / "miss.jpg"), str(self.dir))

    def test_cli(self):
        proc = subprocess.run([sys.executable, str(HERE / "review_footage.py"),
                               str(self.dir / "first.mov"), "--out", str(self.dir / "cli"),
                               "--frames", "2"], capture_output=True, text=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("1 clips, 1 parts", proc.stdout)


if __name__ == "__main__":
    unittest.main()
