#!/usr/bin/env python3
"""compare_timeline.py - check an Edits timeline read-back against plan.json.

The second channel of ADR 0296: the agent reads the timeline back with the
Edits tools (`tracks`, `elements`), saves {"tracks": [...], "elements": [...]}
as one JSON file (every main-track element must carry `aliasId`), and this
script compares it with the plan. With --onsets it also checks the fast part's cuts against onsets measured from renders.
Prints one line per mismatch and exits 1 when there is any. Never calls Edits
(ADR 0298).

Stages:
  added    every planned clip whole, in order, on the main track, no overlay:
           per clip, source in 0, length = full_duration, and each clip
           starting where the one before it ends (the first at 0)
  trimmed  every shot's start, end, source in and source out
  final    trimmed + the music element: present, starts at 0, in-point = song_in

Every stage also names clips on an overlay track (any track that is neither the
main track nor audio) and, separately, text/adjustment elements there. The song is
the audio-track element whose `content` is "music" (sound effects are ignored);
read the elements with `content` so the two can be told apart.

Usage: python3 compare_timeline.py <plan.json> <timeline.json>
           [--stage added|trimmed|final] [--tolerance-frames 1] [--onsets <onsets.json>]
"""
import argparse
import json
import sys

ONSET_NEAR = 0.3  # a cut with no onset this close is reported, not failed


def main_track(tracks):
    for t in tracks:
        if t.get("type") == "video" and t.get("behavior") == "magnetic":
            return t["id"]
    return None


def compare(plan, timeline, stage="final", tolerance_frames=1):
    """Return a list of mismatch strings; empty means the timeline matches."""
    fps = plan["fps"]
    tol = tolerance_frames / fps + 1e-6
    tracks, elements = timeline.get("tracks", []), timeline.get("elements", [])
    main = main_track(tracks)
    if main is None:
        return ["timeline: no main video track"]
    out = []
    # Any track that is neither the main track nor audio is an overlay track: the live
    # app types them "overlay" (2026-11-08), the first run's read-back "video".
    over_ids = {t["id"] for t in tracks if t.get("type") != "audio"} - {main}
    on_over = [e for e in elements if e.get("trackId") in over_ids]
    overlay = [e for e in on_over if e.get("content", "video") == "video"]
    if overlay:
        out.append(f"timeline: {len(overlay)} clip(s) on an overlay track - "
                   "add whole clips on the main track, then trim")
    texts = [e for e in on_over if e.get("content") in ("text", "adjustment")]
    if texts:
        out.append(f"timeline: {len(texts)} text/adjustment element(s) on overlay tracks")
    clips = sorted((e for e in elements if e.get("trackId") == main),
                   key=lambda e: e["startTime"])
    shots = plan["shots"]
    if len(clips) != len(shots):
        out.append(f"timeline: {len(clips)} clips on the main track, plan has {len(shots)}")
    names = {"startTime": "start", "endTime": "end",
             "sourceInPoint": "source in", "sourceOutPoint": "source out"}
    prev_end = 0.0  # added stage: each clip starts where the one before it ends
    for shot, clip in zip(shots, clips):
        n = shot["n"]
        alias = clip.get("aliasId")
        if alias is None:
            out.append(f"shot {n}: clip missing from the read-back")
        elif alias != shot["alias_id"]:
            out.append(f"shot {n}: clip {alias} ≠ planned {shot['alias_id']}")
        if stage == "added":
            # Per clip, never a running sum: Edits' whole-clip lengths differ from
            # review.json's by a few ms, and 21 of those add up past a frame.
            start = clip.get("startTime")
            want = {"startTime": prev_end,
                    "endTime": None if start is None else start + shot["full_duration"],
                    "sourceInPoint": 0.0}
            prev_end = clip.get("endTime")
        else:
            want = {"startTime": shot["start"], "endTime": shot["end"],
                    "sourceInPoint": shot["source_in"], "sourceOutPoint": shot["source_out"]}
        for key, value in want.items():
            got = clip.get(key)
            if got is None:
                out.append(f"shot {n}: {names[key]} missing from the read-back")
            elif value is not None and abs(got - value) > tol:
                out.append(f"shot {n}: {names[key]} {got:.3f} ≠ planned {value:.3f}")
    if stage == "final":
        out.extend(check_music(plan, tracks, elements, tol))
    return out


def check_music(plan, tracks, elements, tol):
    # The song is the audio-track element whose content is "music"; sound effects
    # ("soundEffect") share audio tracks. A read-back without `content` counts every
    # audio-track element, as before.
    audio_ids = {t["id"] for t in tracks if t.get("type") == "audio"}
    music = [e for e in elements if e.get("trackId") in audio_ids
             and e.get("content", "music") == "music"]
    if not music:
        return ["music: no element on an audio track - ask the user to add the song "
                "again by hand at 0:00"]
    if len(music) > 1:
        return [f"music: {len(music)} elements on audio tracks, plan has one song"]
    m, out = music[0], []
    if abs(m.get("startTime", 0.0)) > tol:
        out.append(f"music: start {m['startTime']:.3f} ≠ planned 0.000")
    got = m.get("sourceInPoint")
    if got is None:
        out.append("music: sourceInPoint missing from the read-back")
    elif abs(got - plan["song_in"]) > tol:
        out.append(f"music: in-point {got:.3f} ≠ planned {plan['song_in']:.3f}")
    return out


def check_onsets(plan, onsets):
    """Return (failures, notes) for the fast part's cuts against measured onsets.

    onsets = {"pieces": [{"start": <timeline s>, "duration": <s>, "onsets": [<s in piece>]}]}
    """
    fps = plan["fps"]
    pieces = onsets.get("pieces", [])
    hits = sorted(p["start"] + o for p in pieces for o in p.get("onsets", []))
    fast = [s for s in plan["shots"] if s["part"] == "fast"]
    failures, notes = [], []
    for i, shot in enumerate(fast):
        cut, n = shot["start"], shot["n"]
        covered = any(p["start"] <= cut < p["start"] + p.get("duration", 10.0) for p in pieces)
        if not covered:
            failures.append(f"shot {n}: cut {cut:.3f} is not inside any render")
            continue
        nearest = min(hits, key=lambda h: abs(h - cut)) if hits else None
        dist = abs(nearest - cut) if nearest is not None else None
        if i == 0:
            if dist is None or dist > 1 / fps + 1e-6:
                where = "none" if nearest is None else f"{nearest:.3f}"
                failures.append(f"drop: cut {cut:.3f}, nearest onset {where} - "
                                "the hit must be within one frame")
        elif dist is None or dist > ONSET_NEAR:
            notes.append(f"shot {n}: cut {cut:.3f} has no onset within {ONSET_NEAR} s")
        elif dist > 2 / fps + 1e-6:
            failures.append(f"shot {n}: cut {cut:.3f}, nearest onset {nearest:.3f} "
                            f"({dist * 1000:.0f} ms) - more than two frames")
    return failures, notes


def main(argv):
    ap = argparse.ArgumentParser(description="Compare an Edits timeline read-back with plan.json.")
    ap.add_argument("plan")
    ap.add_argument("timeline")
    ap.add_argument("--stage", choices=("added", "trimmed", "final"), default="final")
    ap.add_argument("--tolerance-frames", type=float, default=1)
    ap.add_argument("--onsets")
    args = ap.parse_args(argv[1:])
    with open(args.plan, encoding="utf-8") as fh:
        plan = json.load(fh)
    with open(args.timeline, encoding="utf-8") as fh:
        timeline = json.load(fh)
    if "start" not in plan["shots"][0]:
        print("plan: no computed cuts - run plan_cuts.py first")
        return 1
    problems = compare(plan, timeline, args.stage, args.tolerance_frames)
    notes = []
    if args.onsets:
        with open(args.onsets, encoding="utf-8") as fh:
            failures, notes = check_onsets(plan, json.load(fh))
        problems.extend(failures)
    for line in problems + notes:
        print(line)
    if problems:
        return 1
    print(f"match: {len(plan['shots'])} shots ({args.stage})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
