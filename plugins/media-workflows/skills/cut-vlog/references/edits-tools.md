# What the Edits tools really do

Every line was measured against Edits on a Mac on 2026-11-07; a line marked
(2026-11-08) was measured or corrected on the live run of that day. A tool's description
says what it is for; this file says what it actually does. When a tool behaves differently
from a line here, correct the line in the same change that works around it.

## Known issue: renders and exports without sound (2026-11-08)

After a project's timeline was cleared with `selectAll` + `delete`, nothing in that project
rendered or exported with audio again: `previewVideo` clips and `export` had a video stream
only, even for a song the user added by hand, and even after the project was reopened.
Clips and a licensed song added through the MCP tools (`addMediaPanelItemsToTimeline`,
`addSongToComposition`) carried no sound in renders, while `getAudioState` said they were
audible; `unmuteTrack` changed nothing. A song the user added by hand, in a project that
had never been cleared, did render (`audioOnsets` measured its tempo). In-app playback can
still sound fine: only a render or an export proves audio. So the skill never clears a
timeline, asks the user to add the song by hand, and stops when a render has no audio
track. Re-check this after every Edits update.

## The tool table

| Tool | What its description does not say |
|---|---|
| `appState` | (2026-11-08) Returns about 60 KB (285 available actions). Read only its `screen`, or call `state` instead. |
| tool set | (2026-11-08) The tools follow the app's screen: after `closeProject` the editor tools disappear and the home tools (`duplicateProject`, `renameProject`, …) appear, and the other way round after `openProject`. |
| `addMediaPanelItemsToTimeline` | With `sourceIn`/`sourceOut` the clip lands on a **new overlay track** (`"newTrack": true`). Add whole clips by `aliasIds`, then trim. Without `startTime` it inserts at the playhead. (2026-11-08) Whole clips are laid out frame-snapped — a 13.375 s source (ffprobe: 13.347 s) read back as 13.367 s; Phase 5's read-back replacement of `full_duration` covers it. Clips added this way carried no sound in renders (known issue above). |
| `trimClip` | `side` is `start` or `end`; a **positive** `delta` trims inward by that many seconds. A negative delta returns `trimmed: true` and changes nothing. A clip cannot grow: delete it, add it again whole, trim from the full length. |
| `seek` | Can start playback. Call `pause` after it. |
| `setTransform` | `fitMode: "fill"` clamps `scale` to 1. To zoom: `allowBeyondCanvas: true`, `scale`, and `x = 0.5 + scale × (0.5 − focusX)` (the same for `y`). `keyframes: "clear"` removes the keyframes `autoReframe` left. |
| `autoReframe` | Needs a person or a face; a shot without one stays centred. |
| `delete` | Deleting every video clip also deletes the music. Element ids change when an element is added again. (2026-11-08) Never empty a timeline with `selectAll` + `delete`: the project then renders without sound (known issue above). Delete clips one at a time, and never the song. |
| `addSongToComposition` | A licensed song arrives with the whole song as its window (`licensedMusicStatus`). (2026-11-08) A song added this way rendered silent: ask the user to add the song by hand instead (known issue above). |
| `tracks` | (2026-11-08) Overlay tracks have `type` `overlay`; the main track is the `video` track whose `behavior` is `magnetic`. An `audio` track can hold `content` `soundEffect` elements beside the `music` one. A busy project also has `text` and `adjustment` elements on overlay tracks. |
| `getMediaPanelItems` | (2026-11-08) Fails with "no media panel — importToMediaPanel opens it". Take alias ids from the library query below (`m.id`) or from `elements` (`aliasId`). |
| `slipClip` | `deltaSeconds` positive moves the in-point later in the song. The new in-point is snapped to a frame (a slip to 18.107 landed at 18.100). The music track ripples to the video's length; `elements` reports its `sourceInPoint`. |
| `audioOnsets`, `audioLevels` | On a licensed song's element they answer "no readable source file" — (2026-11-08) even when `licensedMusicStatus` shows the window complete and its storage managed. Pass the `path` of a `previewVideo` render instead (see below). On a render with no sound they answer "the file has no audio track": stop, never measure from it (known issue above). |
| `beatMarkers` | Empty until the app has analysed the song; then one marker per two beats, `estimatedBpm` at half tempo, and the spacing can wobble after a drop. A cross-check only. |
| `muteTrack` | Takes an element id, not a track id. To silence the clips, `setVolume` 0 on each. |
| `previewVideo` | Renders at most 10 s per call (`startSeconds`, `durationSeconds`, `includeClip: true`). Its clip path is readable by the app's own analysis tools, not by the shell; the HTTP clip route is refused. With the song's alias it fails — (2026-11-08) "Licensed audio window has no file URL". |
| `frameSheet` | With `id` and `path` empty and `times` a comma list, it renders those timeline times into one image. |
| `setExportSettings` | Needs every field: `resolution` as `1920x1080`, `resolutionType` (`720p`, `HD`, `2K`, `4K`), `aspectRatio` as its enum name (`sixteenByNine`, `nineBySixteen`, …), `quality`, `dynamicRange`, `frameRate`. `1080p` and `16:9` are rejected. |
| `export` | Returns as soon as the export starts; poll `exportStatus` until it is done. |
| project | SDR 30 fps footage in an HLG 60 fps project: set `setProjectDynamicRange` `SDR` and `setFrameRate` 30 first. |
| `duplicateProject` | On the home screen only. The copy shares the media, so it costs no disk. (2026-11-08) Takes only `id` and names the copy `<project> copy`: follow it with `renameProject`. Never clear the copy's timeline (known issue above). |

## Finding the clip files

The MCP tools give alias ids, not file paths. Read the paths from the Edits library,
read-only (`mode=ro`); never write to these databases. (2026-11-08) `media_aliases.id` is
the MCP `aliasId`. Managed media (imported into the library) has a `source_path` relative
to `$L/Media/` (for example `Original/<uuid>.mov`); external media has an absolute path.

```bash
L=$(ls -d ~/Movies/Edits/Libraries/*.bsledits | head -1)
sqlite3 "file:$L/Library.db?mode=ro" "select id, name from project_refs;"
P="$L/Projects/<project id from the line above>"
OUT=~/Movies/<project>/review
mkdir -p "$OUT"
# alias id | storage mode | full path, one clip per line, oldest first
sqlite3 "file:$L/Media.db?mode=ro" \
  "attach 'file:$P/MediaIndex.db?mode=ro' as p;
   select m.id, a.storage_mode,
          case when a.source_path like '/%' then a.source_path
               else '$L/Media/' || a.source_path end
   from p.media_aliases m join media_assets a on a.id = m.asset_id
   where a.media_type = 'video' order by a.creation_date;" > "$OUT/clips.txt"
```

Pass the paths to `review_footage.py` from that file, null-separated — never as one shell
variable (zsh does not split `$VAR` into words, and paths can hold spaces):

```bash
cut -d'|' -f3- "$OUT/clips.txt" | tr '\n' '\0' | \
  xargs -0 python3 ${CLAUDE_PLUGIN_ROOT}/scripts/review_footage.py --out "$OUT"
```

## Measuring a licensed song

A licensed song has no file the agent or the app's analysis can open, so measure it from
the timeline:

1. Clips on the timeline, the song added **by hand by the user** at timeline 0 (known
   issue above), read from `elements` (`content` `music`) and slipped to in-point 0.
2. `setVolume` 0 on every clip, so only the music is heard.
3. `previewVideo` with `startSeconds` 0, 10, 20, … and `durationSeconds` 10,
   `includeClip: true`. Each result names a render `path`.
4. `audioOnsets` and `audioLevels` (`hop` 0.5) with `path` set to that render and `id` empty.
   "The file has no audio track" means the render is silent: stop and tell the user.
   Onsets are seconds inside the piece; add the piece's start for timeline time, and the
   song's in-point for song time.
5. Restore every clip's volume.

The drop is a short dip in `levelsDb` followed by a loud hit. The BPM is the onsets'
spacing (`audioOnsets` also reports a `bpm`); check it against `beatMarkers` doubled.
