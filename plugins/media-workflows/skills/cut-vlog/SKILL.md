---
name: cut-vlog
description: 'Cut a day of phone footage into a short vlog in Meta''s Edits app on a Mac, on the beat of a song the user picks, through the Edits MCP tools. The user''s own style rules come first, the song second, a shot plan sheet is approved before any cut, every edit is read back and compared with the plan, and every export is a new numbered file. Use when the user asks to edit, cut or make a vlog, a family video, a day video or a trip clip from an Edits project; says ตัดต่อวีดีโอ, ตัด vlog, ทำคลิปจากวันนี้, put these clips to music, cut it on the beat; or asks to correct a vlog this skill cut before ("make the beach shot longer", "change the song", "take that shot out"). Do not use it for another editor (Premiere, CapCut, Final Cut, DaVinci Resolve), on Windows or Linux, for voiceover, captions or sound effects, or to post a video to a platform.'
---

# Cut a vlog

A day of phone footage becomes one short video that moves with its music. The method is
fixed: **the user's rules first, the song second, the plan seen before the cut, every edit
checked, the arithmetic in tested scripts.** Each phase below ends in something you can show.

**Known issue (2026-11-08):** a project whose timeline was once emptied renders and exports
without sound, and media the agent adds can render silent. So the user adds the song by
hand, no timeline is ever emptied, and a render or export without audio stops the run —
see `references/edits-tools.md`, *Known issue*. The Phase 1 new-project path and the
Phase 5 step 1 add-then-delete order are workarounds not yet run live (2026-11-08); confirm
them on the next live run.

```
0 pre-flight → short plan (user OKs) → 1 style file + project → 2 footage review → 3 song (user picks) → 4 shot plan (user OKs)
→ 5 cut, each step checked → 6 render check → 7 export vN → 8 corrections
```

## Where things live

| What | Where |
|---|---|
| the user's style file | `~/Movies/cut-vlog/style.md` — template in `references/style-file.md` |
| one project's edit record | `~/Movies/<project>/` (`<project>` = the Edits project's name as worked in) — `record.md`, `plan.json`, `review/`, `checks/`; layout in `references/edit-record.md` |
| what each Edits tool really does | `references/edits-tools.md` — read it before Phase 1 and again before Phase 5 |
| the scripts | `${CLAUDE_PLUGIN_ROOT}/scripts/review_footage.py`, `${CLAUDE_PLUGIN_ROOT}/scripts/plan_cuts.py`, `${CLAUDE_PLUGIN_ROOT}/scripts/compare_timeline.py` |
| exports | `~/Movies/<project>/<project>-v<N>.mp4`, beside the record |

Nothing about the user — their rules, their footage, their family — is ever written
anywhere else. The scripts never call Edits: you call the tools and hand the scripts JSON.

## Phase 0 — Pre-flight

1. Load the Edits MCP tools and call `appState` — read only its `screen` (the reply is about
   60 KB), or call `state` instead. If the tools are not there, or the call fails, **stop**.
   Tell the user the exact error and these fixes, then end the run — do not review footage,
   list songs, or work around it with HTTP calls:
   - open Edits and an editor window, then start a new session;
   - update Edits and update the agent — a tool list the agent rejects (for example
     `tools/list` complaining about `ttlMs` or `cacheScope`) is a version mismatch;
   - restart Edits, then the agent.
2. Check `ffmpeg -version`, `ffprobe -version` and `python3 --version` (3.10 or newer). If
   ffmpeg is missing, offer `brew install ffmpeg` and run it only on a yes.

## Short plan — every run

Phase 0 and the reads of Phase 1 come first, and change nothing: read `style.md`, find the
project (`projects`), find its record folder and the phase it would resume at, and look at
the footage the user pointed to. Then show the user a **short plan** — ten lines or fewer:

- **found:** the Edits project, the footage (where, how many clips, shape, log or not), the
  style file's date or "none yet", and the record folder with the phase to resume at;
- **will do:** each phase this run takes, one line each, naming the points where it waits
  for the user — the song pick, adding the song by hand, the plan sheet;
- **assumed:** every guess read from the request (which folder is the footage, who a person
  named in a rule is), so the user can correct it;
- **asks:** Phase 1's style questions still open, as this run's one round of questions.

Wait for the user's OK. A correction to the short plan changes it and shows it again. Every
write, import, project setting and clip comes after the OK. A correction run (Phase 8)
shows a short plan too: the rows it will change and the version it will export.

## Phase 1 — Style file and project

1. Create `~/Movies/cut-vlog/` if it is missing. Read `~/Movies/cut-vlog/style.md`. If an old
   `~/.claude/cut-vlog/style.md` exists and the new one does not, move it to the new place
   and tell the user (a one-time migration). If it is still missing, the short plan asked **one** round of questions,
   leaving out every one the user has already answered in this conversation:
   frame shape (16:9 or 9:16) · text on screen or none · kind of music · rules for who is
   shown and how · target length. Write the answers into a new `style.md` using the template
   in `references/style-file.md`, each rule dated, and say where you wrote it.
2. Open the Edits project the user named (`projects`, then `openProject`). If the user named
   none, list the projects and ask. If it has no media, ask for a folder and import it.
3. Look for the project's edit record folder, `~/Movies/<project>/` with a `plan.json` or a
   `record.md` in it — first for the opened project's name, then for its copy
   `<project> – cut-vlog` if that folder exists (open the copy if the folder is there). The
   folder name contains spaces and an en dash, so every shell command must quote it
   (`"$HOME/Movies/<project>/..."`).
   - Compare the folder's stored `project_id` with the id of the project you will actually
     work in — after opening the `<project> – cut-vlog` copy when that is the folder found.
     If they differ, ask the user before reusing the folder.
   - If the user renamed the project in Edits, find the old folder by its stored project id:
     scan `~/Movies/*/plan.json` for `"project_id"`. Use the folder found as the project
     folder for the rest of the run, whatever its name, and offer to rename it to the
     current project name.
   - If the project name would give `~/Movies/Edits/` or `~/Movies/cut-vlog/`, or contains
     `/`, ask the user for a different folder name.
   - An old `~/.claude/cut-vlog/projects/<id>/` folder is moved to the project folder when
     you find it (a one-time migration; tell the user): write `<id>` (the old folder's name)
     into `plan.json` as `"project_id"` and into `record.md`'s Project section, and if
     `~/Movies/<project>/` already exists, merge the old folder's contents into it rather
     than nesting it. Old exports sit at `~/Movies/<project>-v<N>.mp4`; mention them and
     continue N after the highest of them.
   If the folder exists, read `record.md` and `plan.json` (whichever are there) and resume
   at the first phase they have not finished; a correction goes to Phase 8. Do not ask for a
   new project or duplicate one that has a record folder. When you create a folder, write
   the Edits project id into `plan.json` (`"project_id"`) and into `record.md`'s Project
   section.
4. Only when there is no record folder: if the timeline already has elements, ask the user
   to make a **new, empty** Edits project named `<project> – cut-vlog` and add the same
   footage to it by hand, then open that project and work there. Never empty a timeline
   with select-all + delete — the project would render without sound (known issue). If the
   user prefers a duplicate, `duplicateProject` (home screen, takes only `id`) and
   `renameProject` it to `<project> – cut-vlog` — but tell the user its timeline must then
   never be cleared (known issue), so the new empty project is the cleaner path.
5. Set the project to the footage: `setProjectDynamicRange` `SDR` and `setFrameRate` 30 for
   SDR 30 fps phone footage; `setAspectRatio` to the style file's shape.

## Phase 2 — Footage review

1. List the project's clips from the Edits library, read-only — alias id, storage mode and
   full path, one per line — with the query in `references/edits-tools.md` under *Finding
   the clip files*.
2. Run `review_footage.py` over those paths, passed null-separated as that section shows
   (never as one shell variable):
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_footage.py <files...> --out "$HOME/Movies/<project>/review"`
3. Look at every row image and every part sheet. For each clip write a candidate into
   `plan.json` under `candidates`: `clip`, `alias_id` (the library query's `m.id`),
   `full_duration` (review.json's `duration` for that clip; Phase 5 replaces it with the
   length Edits reads back), what happens, the best `source_in`, sharp or not, and any style
   rule it breaks. A soft or shaky clip is not a candidate for a key moment. The parts of the
   day come from the review's time gaps.
4. Create `record.md` with its *Project* and *Review* sections, from the template in
   `references/edit-record.md`. From here on the folder holds both files, so a later run
   resumes from it.

## Phase 3 — Song

1. List 5-7 songs that fit the style file's music kind, from the Edits library
   (`searchMusic`, `listMusicTracks` with the trending tab and with searches for known
   songs of that kind). For each: title, artist, its shape (where it builds, where it
   drops, roughly when), and a warning if the lyrics are explicit.
2. **Wait for the pick.** Place no clip on the timeline before the user picks.
3. Ask the user to add the picked song **by hand** in Edits, at 0:00 — a song the agent
   adds rendered silent on 2026-11-08 (known issue). Wait until they say it is there, then
   read its element id from `elements` (the one whose `content` is `music`) and `slipClip`
   it to in-point 0 for the measurement.
4. Measure the song (`references/edits-tools.md`, *Measuring a licensed song*): put enough
   candidate clips on the timeline, whole, to run past the song's drop (no plan exists
   yet, and the music only runs as long as the video); `setVolume` 0 on every clip; render
   the timeline in 10-second pieces with `previewVideo`; run `audioOnsets` and `audioLevels` with each render's `path`; restore
   every volume. Before trusting any measurement, check each render has audio: if
   `audioOnsets` or `audioLevels` answers "the file has no audio track", **stop** and tell
   the user (known issue) — never measure from a silent render. Read the BPM (the onsets'
   spacing; `audioOnsets` also reports one) and the drop (a short dip, then a loud hit). If that dip-then-hit falls within 0.5 s of a piece's edge, render one more 10-second piece centred on it and read the drop from that piece. Then read `beatMarkers`: double its
   `estimatedBpm` and compare — a disagreement of more than 2 BPM means measure again.
5. Write `fps` (the project's frame rate, 30), `bpm`, `drop` (song seconds), the song's
   `title` and `audio_asset_id`, and every measurement into `plan.json`.

## Phase 4 — Shot plan

1. Choose the shots and give each a length in beats:
   - **slow part** (before the drop): whole bars, shots of 4-8 beats; a short dissolve
     only where the day changes place;
   - **the drop**: the strongest moment of the day starts on the hit, on a hard cut;
   - **fast part**: 2 beats per shot, 4 for a key moment, 12 or more for a moment the
     style file says to keep long; hard cuts only;
   - the end: a fade.
   Mark each shot `"part": "slow"` or `"fast"`; the first `fast` shot is the drop shot.
2. Set `song_in` so the drop lands on that shot: `song_in = drop − (beats before it) × 60 / bpm`,
   rounded to a frame. `plan_cuts.py` prints this value when the drop misses.
3. Run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/plan_cuts.py "$HOME/Movies/<project>/plan.json"`.
   It snaps each `source_in` to a frame and writes it back. A shot that runs past its clip
   is fixed by an earlier `source_in` or fewer beats. Only a drop more than one frame off is
   printed with a `song_in` that would land it — or, when that `song_in` would be negative,
   with how many bars to cut from the slow part. Correct the plan and run it again.
4. Render the **shot plan sheet**: `frameSheet` on each clip's source at its planned middle
   (`source_in + duration / 2`), one cell per shot, and show it with each shot's number,
   length in beats and part. Wait for the user's OK or changes. Change the plan and run
   step 3 again until they say OK.

## Phase 5 — Cut

Read `references/edits-tools.md` first. Then, for every step below: write down what the
timeline must look like after it, do it, read the timeline back (`tracks`, then
`elements` with the fields `id, trackId, content, aliasId, startTime, endTime, duration,
sourceInPoint, sourceOutPoint`), save `{"tracks": [...], "elements": [...]}` as
`~/Movies/<project>/checks/<stage>.json`, named by the stage, and run
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/compare_timeline.py "$HOME/Movies/<project>/plan.json" "$HOME/Movies/<project>/checks/<stage>.json" --stage <stage>`.
Fix any mismatch before the next step.

1. **Clips** (`--stage added`): never delete every clip — the timeline holds only what
   Phase 3 put there: whole clips and the song the user added. `seek` 0 and `pause`, then
   `addMediaPanelItemsToTimeline` with every planned `alias_id` in order, in one call,
   without `sourceIn`/`sourceOut`; they go in front of Phase 3's clips. Then `delete`
   Phase 3's clips one at a time (never select-all), and never the song — the planned
   clips go in first because deleting the last video clip also deletes the music. Read the
   timeline back, write each clip's `sourceOutPoint` into its shot's `full_duration` in `plan.json` (Edits' length can differ
   from ffprobe's by a few milliseconds), run `plan_cuts.py` again, and only then check
   `--stage added`. A shot that now runs past its clip goes back to Phase 4.
2. **Trims** (`--stage trimmed`): for each shot, `trimClip` side `start` by `trim_start`
   and side `end` by `trim_end` (skip a zero). Positive deltas only.
3. **Music** (`--stage final`): do not call `addSongToComposition` — use the song the user
   added by hand (its `content` is `music`). Read its `sourceInPoint` from `elements`;
   `slipClip` it by `song_in − sourceInPoint` seconds (a positive delta moves the in-point
   later in the song; the app snaps it to a frame); `setFade` on the music — a short fade in, a 2-second fade out.
4. **Volumes**: clip sound low under the music (0.2-0.4) unless a clip's own sound is the
   moment; read back with `getVolume`.
5. **Framing**: for a clip shot in the other shape, `autoReframe` where it has a person;
   otherwise `setTransform` with `allowBeyondCanvas: true`, `keyframes: "clear"`, and
   `x = 0.5 + scale × (0.5 − focusX)` (same for y). Read back with `getTransform`.
6. **Transitions**: only the dissolves the plan names and the fade at the end.
7. After each of steps 4, 5 and 6, read the timeline back again, save it as
   `checks/final.json` and run `compare_timeline.py --stage final` on it.

Write each step and its result into `record.md` as you go.

## Phase 6 — Render check

1. `frameSheet` of the timeline with one time per shot, at its middle. Look at every cell
   against the style file: who is shown and how, sharpness, framing. You judge this — no
   script does (a rule like "no close-ups of the people in the background" is a visual call).
2. Set every clip's volume to 0, render from 2 s before the drop shot's start (`drop_check.boundary − 2` in `plan.json`) to the end, in 10-second pieces, with
   `previewVideo`, run `audioOnsets` on each (a render with no audio track stops the run,
   as in Phase 3), restore the volumes, and save
   `{"pieces": [{"start": <timeline s>, "duration": <s>, "onsets": [...]}]}` as
   `~/Movies/<project>/checks/onsets.json`. Run
   `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/compare_timeline.py "$HOME/Movies/<project>/plan.json" "$HOME/Movies/<project>/checks/final.json" --onsets "$HOME/Movies/<project>/checks/onsets.json"`.
   The drop's hit must be within one frame of its cut and every other fast cut within two
   frames of an onset; a cut with no onset within 0.3 s is reported, not failed.
3. A failed shot goes back to Phase 5 for that shot only. Save the sheet and the result
   under `checks/`.

## Phase 7 — Export

1. `saveProject`.
2. `setExportSettings` with every field: `resolution` (`1920x1080` for 16:9,
   `1080x1920` for 9:16), `resolutionType` `HD`, `aspectRatio` (`sixteenByNine` or
   `nineBySixteen`), `quality` `high`, `dynamicRange` `SDR`, `frameRate` 30.
3. `export` to `~/Movies/<project>/<project>-v<N>.mp4`, N one more than the highest existing
   in that folder — never over an earlier file. Poll `exportStatus` until it is done.
4. `ffprobe` the file: the planned shape, the planned length within 0.1 s, one video stream
   and one audio stream. A file on disk is not proof the export worked. With no audio
   stream the export failed (known issue): tell the user, and do not deliver it as done.
5. Write the export and its checks into `record.md`. Tell the user the path, what was
   checked, and what was recorded where.

## Phase 8 — Corrections

1. Read `record.md` and `plan.json` — never review the footage or measure the song again
   for a correction that does not change them.
2. Change the rows the correction touches; run `plan_cuts.py`; show only the changed
   shots, before and after, and wait for the OK.
3. Re-cut only what moved. For each changed shot: `delete` only its clip, add it back
   whole with `addMediaPanelItemsToTimeline` and `startTime` at its planned `start`, and
   trim it (`trim_start`, `trim_end`). If `song_in` changed, slip the music again (Phase 5
   step 3's `slipClip`). Then read the whole timeline back, save it as `checks/final.json`
   and run `compare_timeline.py --stage final`. Never delete every clip for a correction —
   that also deletes the music. Then run Phase 6 and export the next version (Phase 7).
4. A rule for every video goes to `style.md`; a change for this video goes to
   `record.md`. Tell the user which one you wrote, and where.

## Never

- Write, import or change anything before the user OKs the short plan.
- Place a clip before the user has picked the song, or cut before they OK the plan sheet.
- Trust an Edits tool's `ok: true` — the read-back is the proof.
- Write the user's rules, footage names or people into anything outside `~/Movies/<project>/` and `~/Movies/cut-vlog/`.
- Overwrite an export.
- Empty a timeline with select-all + delete, or add the song through the tools — the user
  adds it by hand (known issue).
