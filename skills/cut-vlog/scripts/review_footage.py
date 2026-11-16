#!/usr/bin/env python3
"""review_footage.py - one row image, a loudness trace and a capture time per clip.

For each clip: duration, display size and capture time (the creation_time tag,
else a YYYYMMDD_HHMMSS file name, else the file's mtime); --frames frames taken
at (i + 0.5) x duration / frames, tiled into one row image; RMS loudness in
0.5-second steps. Clips are sorted by capture time and split into parts wherever
two clips are more than --gap-minutes apart; each part gets one stacked sheet.
Writes <out>/review.json. Needs ffmpeg and ffprobe on PATH. Never calls Edits
(ADR 0298).

Usage: python3 review_footage.py <clip>... --out <dir> [--frames 8] [--gap-minutes 20]
"""
import argparse
import concurrent.futures
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

CELL_W, CELL_H = 240, 180
STEP = 0.5
NAME_RE = re.compile(r"(\d{8})_(\d{6})")


def run(cmd):
    try:
        return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"{cmd[0]} failed: {e.stderr.strip()}") from e


def probe(path):
    return json.loads(run(["ffprobe", "-v", "error", "-print_format", "json",
                           "-show_format", "-show_streams", path]))


def display_size(info):
    """(width, height) as shown, swapping for a 90 or 270 degree rotation."""
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), None)
    if video is None:
        return None, None
    w, h = video.get("width"), video.get("height")
    rotation = video.get("tags", {}).get("rotate")
    for side in video.get("side_data_list", []):
        if "rotation" in side:
            rotation = side["rotation"]
    if rotation is not None and int(float(rotation)) % 180 != 0:
        w, h = h, w
    return w, h


def capture_time(info, path):
    """(ISO-8601 time in UTC, where it came from)."""
    value = info.get("format", {}).get("tags", {}).get("creation_time")
    if not value:
        for s in info.get("streams", []):
            value = s.get("tags", {}).get("creation_time")
            if value:
                break
    if value:
        t = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=dt.timezone.utc)
        return t.astimezone(dt.timezone.utc).isoformat(), "creation_time"
    m = NAME_RE.search(os.path.basename(path))
    if m:
        t = dt.datetime.strptime("".join(m.groups()), "%Y%m%d%H%M%S")
        return t.replace(tzinfo=dt.timezone.utc).isoformat(), "file name"
    t = dt.datetime.fromtimestamp(os.path.getmtime(path), dt.timezone.utc)
    return t.isoformat(), "mtime"


def frame_times(duration, frames):
    return [round((i + 0.5) * duration / frames, 3) for i in range(frames)]


def split_parts(clips, gap_minutes):
    """clips sorted by capture time -> list of lists, split at gaps > gap_minutes."""
    parts, prev = [], None
    for c in clips:
        t = dt.datetime.fromisoformat(c["capture_time"])
        if prev is None or (t - prev).total_seconds() > gap_minutes * 60:
            parts.append([])
        parts[-1].append(c)
        prev = t
    return parts


def parse_rms(text):
    """ametadata print output -> RMS levels in dB, one per STEP (-inf -> -120)."""
    levels = []
    for line in text.splitlines():
        if "lavfi.astats.Overall.RMS_level=" in line:
            v = line.split("=", 1)[1].strip()
            levels.append(-120.0 if v in ("-inf", "inf", "nan") else round(float(v), 1))
    return levels


def loudness(path, info):
    if not any(s.get("codec_type") == "audio" for s in info.get("streams", [])):
        return []
    rate = 16000
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-vn", "-af",
         f"aresample={rate},asetnsamples=n={int(rate * STEP)}:p=0,"
         "astats=metadata=1:reset=1,"
         "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-",
         "-f", "null", "-"],
        check=True, capture_output=True, text=True).stdout
    return parse_rms(out)


def row_image(path, times, dest, tmp):
    cells = []
    for i, t in enumerate(times):
        cell = os.path.join(tmp, f"cell_{i:02d}.png")
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
             "-vf", f"scale={CELL_W}:{CELL_H}:force_original_aspect_ratio=decrease,"
                    f"pad={CELL_W}:{CELL_H}:(ow-iw)/2:(oh-ih)/2", cell])
        if not os.path.exists(cell):
            raise RuntimeError(f"{os.path.basename(path)}: no frame at {t:.3f} s")
        cells.append(cell)
    run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(tmp, "cell_%02d.png"),
         "-vf", f"tile={len(cells)}x1", "-frames:v", "1", dest])


def review_clip(path, out_dir, frames):
    info = probe(path)
    video = next((s for s in info.get("streams", []) if s.get("codec_type") == "video"), {})
    duration = float(video.get("duration") or info["format"]["duration"])
    width, height = display_size(info)
    when, source = capture_time(info, path)
    name = os.path.basename(path)
    times = frame_times(duration, frames)
    row = os.path.join(out_dir, f"row_{os.path.splitext(name)[0]}.jpg")
    with tempfile.TemporaryDirectory() as tmp:
        row_image(path, times, row, tmp)
    return {"file": os.path.abspath(path), "name": name, "duration": round(duration, 3),
            "width": width, "height": height, "capture_time": when,
            "capture_source": source, "frame_times": times,
            "row_image": os.path.basename(row), "loudness_step": STEP,
            "loudness_db": loudness(path, info)}


def part_sheet(rows, dest):
    if len(rows) == 1:
        shutil.copyfile(rows[0], dest)
        return
    cmd = ["ffmpeg", "-v", "error", "-y"]
    for r in rows:
        cmd += ["-i", r]
    cmd += ["-filter_complex", f"vstack=inputs={len(rows)}", "-frames:v", "1", dest]
    run(cmd)


def review(paths, out_dir, frames=8, gap_minutes=20):
    os.makedirs(out_dir, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as pool:
        clips = list(pool.map(lambda p: review_clip(p, out_dir, frames), paths))
    clips.sort(key=lambda c: c["capture_time"])
    parts = []
    for n, group in enumerate(split_parts(clips, gap_minutes), start=1):
        sheet = f"part_{n:02d}.jpg"
        part_sheet([os.path.join(out_dir, c["row_image"]) for c in group],
                   os.path.join(out_dir, sheet))
        for c in group:
            c["part"] = n
        parts.append({"n": n, "start": group[0]["capture_time"],
                      "end": group[-1]["capture_time"],
                      "clips": [c["name"] for c in group], "sheet": sheet})
    result = {"frames": frames, "gap_minutes": gap_minutes, "clips": clips, "parts": parts}
    with open(os.path.join(out_dir, "review.json"), "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=2)
        fh.write("\n")
    return result


def main(argv):
    ap = argparse.ArgumentParser(description="Review a day's clips for cut-vlog.")
    ap.add_argument("clips", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--gap-minutes", type=float, default=20)
    args = ap.parse_args(argv[1:])
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            print(f"{tool} not found - install it with: brew install ffmpeg", file=sys.stderr)
            return 2
    result = review(args.clips, args.out, args.frames, args.gap_minutes)
    print(f"{len(result['clips'])} clips, {len(result['parts'])} parts -> "
          f"{os.path.join(args.out, 'review.json')}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
