#!/usr/bin/env python3
"""plan_cuts.py - turn a shot plan in beats into frame-exact cuts and trims.

Reads plan.json (fps, bpm, song_in, drop, shots[] with clip, alias_id,
full_duration, source_in, beats, part), writes back per shot: source_in snapped
to a frame, start, end, duration, source_out, trim_start, trim_end; and a
top-level "drop_check". A shot with beats <= 0 and a negative song_in (given, or
needed to land the drop) are rejected; the latter names the bars to cut.
Exit 0 when every shot fits its clip and the drop lands within one frame of
the first fast shot's start; exit 1 otherwise. Never calls Edits (ADR 0298).

Usage: python3 plan_cuts.py <plan.json>
"""
import json
import math
import sys

REQUIRED_TOP = ("fps", "bpm", "song_in", "drop", "shots")
REQUIRED_SHOT = ("clip", "alias_id", "full_duration", "source_in", "beats", "part")


def to_frame(seconds, fps):
    """Nearest frame, halves rounded up (never banker's rounding)."""
    return math.floor(seconds * fps + 0.5)


def compute(plan):
    """Return (plan with computed fields, list of error strings)."""
    errors = []
    for key in REQUIRED_TOP:
        if key not in plan:
            errors.append(f"plan: missing '{key}'")
    if errors:
        return plan, errors
    fps, beat = plan["fps"], 60.0 / plan["bpm"]
    if plan["song_in"] < 0:
        errors.append(f"song_in: negative - {shorten(plan['song_in'], beat)}")
    beats_so_far, prev_frame = 0, 0
    for n, shot in enumerate(plan["shots"], start=1):
        missing = [k for k in REQUIRED_SHOT if k not in shot]
        if missing:
            errors.append(f"shot {n}: missing {', '.join(missing)}")
            continue
        if shot["part"] not in ("slow", "fast"):
            errors.append(f"shot {n}: part must be 'slow' or 'fast', got '{shot['part']}'")
        if shot["beats"] <= 0:
            errors.append(f"shot {n}: beats must be positive")
            continue
        # Edits trims to whole frames, so the in-point is one before anything is derived.
        shot["source_in"] = round(to_frame(shot["source_in"], fps) / fps, 3)
        beats_so_far += shot["beats"]
        end_frame = to_frame(beats_so_far * beat, fps)
        shot["n"] = n
        shot["start"] = round(prev_frame / fps, 3)
        shot["end"] = round(end_frame / fps, 3)
        shot["duration"] = round((end_frame - prev_frame) / fps, 3)
        shot["source_out"] = round(shot["source_in"] + shot["duration"], 3)
        shot["trim_start"] = round(shot["source_in"], 3)
        shot["trim_end"] = round(shot["full_duration"] - shot["source_out"], 3)
        if shot["trim_end"] < 0:
            errors.append(
                f"shot {n}: source_out {shot['source_out']:.3f} passes the clip's "
                f"full_duration {shot['full_duration']:.3f}")
        prev_frame = end_frame
    if errors:
        return plan, errors
    plan["drop_check"] = drop_check(plan)
    dc = plan["drop_check"]
    if dc["drop_shot"] is None:
        errors.append("drop: no shot has part 'fast', so there is no drop shot")
    elif not dc["ok"]:
        if dc["suggested_song_in"] < 0:
            fix = ("song_in for that boundary would be negative - "
                   + shorten(dc["suggested_song_in"], beat))
        else:
            fix = f"song_in for that boundary is {dc['suggested_song_in']:.3f}"
        errors.append(
            f"drop: lands at {dc['drop_timeline']:.3f}, {dc['offset_frames']:+.1f} frames "
            f"from shot {dc['drop_shot']}'s start {dc['boundary']:.3f}; {fix}")
    return plan, errors


def shorten(song_in, beat):
    """A negative song_in means the slow part outlasts the song before the drop."""
    bars = math.ceil(-song_in / (4 * beat) - 1e-9)
    return f"shorten the slow part by {bars} bars"


def drop_check(plan):
    """Where the drop lands, against the start of the first fast shot."""
    fps, beat = plan["fps"], 60.0 / plan["bpm"]
    fast = [s for s in plan["shots"] if s["part"] == "fast"]
    if not fast:
        return {"ok": False, "drop_timeline": plan["drop"] - plan["song_in"],
                "drop_shot": None, "boundary": None, "offset_frames": None,
                "suggested_song_in": None}
    first = fast[0]
    beats_before = sum(s["beats"] for s in plan["shots"][: first["n"] - 1])
    drop_timeline = plan["drop"] - plan["song_in"]
    offset_frames = (drop_timeline - first["start"]) * fps
    return {
        "ok": abs(offset_frames) <= 1.0 + 1e-9,
        "drop_timeline": round(drop_timeline, 3),
        "drop_shot": first["n"],
        "boundary": first["start"],
        "offset_frames": round(offset_frames, 2),
        # Edits snaps a slipped in-point to a frame, so the suggestion is one too.
        "suggested_song_in": round(to_frame(plan["drop"] - beats_before * beat, fps) / fps, 3),
    }


def main(argv):
    if len(argv) != 2:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    path = argv[1]
    with open(path, encoding="utf-8") as fh:
        plan = json.load(fh)
    plan, errors = compute(plan)
    if errors:
        for e in errors:
            print(e)
        return 1
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(plan, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    dc = plan["drop_check"]
    print(f"{len(plan['shots'])} shots, {plan['shots'][-1]['end']:.3f} s; drop at "
          f"{dc['drop_timeline']:.3f} on shot {dc['drop_shot']} "
          f"({dc['boundary']:.3f}, {dc['offset_frames']:+.2f} frames)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
