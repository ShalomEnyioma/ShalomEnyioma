---
name: reaction-edit
description: Edit a raw talking-head REACTION recording into a finished 9:16 reaction video. Cuts every micro-silence and wrong take, cuts "let's listen to this"-type lines, replaces the parts where the creator played the clip into the mic with the ORIGINAL clip full-screen, and adds captions just above the creator's head. Use when the user asks to edit a reaction video, or drops a reaction recording plus the clip it reacts to (e.g. in the Drive "CONTENT CREATION/TO BE EDITED" folder).
---

# Reaction video editor

## The creator's rules (do not change them)

1. **Cut ALL micro-silences.** Every pause longer than ~0.14 s between kept words is removed. Nothing else is trimmed for pacing.
2. **Cut wrong takes**: false starts, restarts, repeated phrases, fumbles. Keep the final, clean version of each line.
3. **Cut "listen" lines**: anything that only tells the viewer to listen/watch ("I need you to listen to this", "let's continue hearing what she has to say", "watch this").
4. **Clip parts are fully overlaid.** While the creator recorded, she held the mic to her phone so the clip's audio was captured. Those stretches mark *which part of the clip she wants heard*. In the edit they are replaced by the original clip, video AND audio, covering the whole 1080x1920 frame (no picture-in-picture, no split screen).
5. **Ratio 9:16** (1080x1920, 30 fps).
6. **Captions only on the creator's speech**, positioned **just above her head**, 1 to 3 words at a time. No captions over the clip (it has its own).
7. That's all. No music, zooms, sound effects, B-roll or transitions unless the user asks.

## Inputs

Two files per video, normally in Drive `CONTENT CREATION/TO BE EDITED`:
- the reaction recording (large, phone video; often 100 MB+, HEVC, rotated)
- the clip being reacted to (small, usually the downloaded TikTok)

Tell them apart by size/duration and by the frames (the creator vs the other person). Getting them:
- Files under 10 MB: Google Drive connector `download_file_content` (it saves to disk and prints the path).
- Larger files: Composio `GOOGLEDRIVE_DOWNLOAD_FILE` (account = the creator's Drive) returns a signed `s3url`; `curl` it within the hour.

## Pipeline

```bash
SK=.claude/skills/reaction-edit/scripts
bash $SK/setup.sh "$MODELS"                                    # once per machine (~1.1 GB, cached)
python3 -I $SK/analyze.py reaction.mp4 clip.mp4 WORK --models "$MODELS"
#   prints: CLIP runs (rec time -> clip time), every word as [id|time]word,
#   ~~struck~~ words = auto-detected "listen" lines, and the face/caption position
python3 -I $SK/edl.py WORK --cut <ids> --keep <ids> --say <id=Text> ...
#   prints the final piece list; repeat until it reads right
python3 -I $SK/render.py WORK "OUT.mp4"                       # ~1 min after the first run
```

### Review step (this is where the judgement goes)

Read the analyze.py transcript top to bottom like an editor:
- **Wrong takes**: a phrase said twice, a restart ("when you have bigger ones, bigger amounts of money" -> cut "bigger ones,"), a sentence abandoned midway. `--cut` the ids of the discarded version.
- **Listen lines**: confirm the ~~struck~~ words are only the listen instruction. `--keep` anything wrongly struck; `--cut` any listen line it missed.
- **Clip runs**: each should match a moment she played the clip. If a run is missing or extra, fix `clip_runs` in `analysis.json` (rec start/end, clip start/end) and rerun edl.py.
- **Instructions to the editor said on camera** ("cut that part", "remove this", "start again"): cut the instruction AND the flubbed line it refers to.
- **Listen lines inside a useful sentence**: the auto-strike takes the whole clause. "I want you to watch this clip with me, but we're going to come from a different perspective" -> cut only up to "but", `--keep` the rest (and `--say` a capital on the new first word).
- **Clip edges**: check each clip piece's in/out against the clip's own word timings (run `analyze.py`'s parakeet on clip.wav, or peek at a few seconds). The first clip usually starts at 0:00 even if detection says ~1 s; never start or end a clip piece mid-word.
- **Short replays** (under ~1.5 s, too short to auto-detect; her audio is quiet like the playback, ~1/3 of her own voice level): usually she paused too early and replayed the line. Prefer letting the main clip piece run through that line and drop the replay, so it's heard once. Edit `clip_runs` in `analysis.json` (`clip_start`/`clip_end`) and `--cut` the replay's words.
- **Caption spelling**: the ASR is English-only. Fix Nigerian words and mishearings with `--say` (e.g. `--say 30=Money --say 76=Omo, --say 77=` where an empty value hides a word). This changes captions only, never the audio.
- Never cut the creator's actual opinion, story or punchline to shorten the video.

### Check before delivering

1. Grab frames at a creator piece, at each clip piece and at a cut, and look at them: the clip must fill the frame, captions must sit above the head without covering the face and without running off the edges.
2. `ffprobe` the output: 1080x1920, 30 fps, h264 + aac, duration about equal to the sum printed by edl.py.
3. If captions look off, rerun render.py with `--caption-y <px>` (baseline) or `--size`.

### Deliver

- Send the MP4 to the user with `SendUserFile` (display: render). Name it `<original name> - EDITED.mp4`.
- Drive connector uploads are capped at 10 MB, so a finished video usually can't go back to Drive from here. Say so; don't re-encode it to a lower quality just to fit unless the user asks.
- Report: final length vs raw length, what was cut (listen lines, wrong takes), and any caption words you corrected.

## How it works (for debugging)

- **Clip detection** (analyze.py `align`): band-passed audio, 1 s windows every 0.25 s, normalised cross-correlation against the whole clip. A real playback keeps the same offset (rec time minus clip time) for seconds; chance matches don't. Runs are grown into quiet edges, tightened with 0.4 s windows, and cut where her own (much louder) voice starts. If she rewound and replayed a bit, the repeat is dropped so the viewer hears each clip line once.
- **Words**: NVIDIA Parakeet TDT 0.6B (sherpa-onnx, offline) on everything outside the clip runs, with token timestamps; word ends are clamped to the speech burst (Silero VAD).
- **Pieces** (edl.py): consecutive kept words merge when the gap is under `--gap` (0.06 s) after `--pad` (0.04 s) on each side; edges then grow until the voice level has actually dropped, so no word is clipped.
- **Render**: both inputs are converted once to upright CFR 1080x1920 mezzanines with loudness-normalised (-14 LUFS) audio; pieces are frame-snapped, trimmed, given 8 ms fades and concatenated; captions are an ASS file (Inter Black, white, black outline) burned in at `head_top - 30` px.
