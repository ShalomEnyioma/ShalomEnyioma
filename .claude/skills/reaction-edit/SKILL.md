---
name: reaction-edit
description: Edit the creator's TikTok recordings. Reaction mode (recording + clip): edit a raw talking-head REACTION recording into a finished 9:16 reaction video. Cuts every silence (strictly, on the audio) and wrong takes, keeps the "watch this with me" reaction intro, replaces the parts where the creator played the clip into the mic with the ORIGINAL clip full-screen, and adds captions just above the creator's head. Captions-only mode (a talking-head recording with NO clip): add captions and nothing else. Use when the user asks to edit a reaction video or caption a talking-head video, or drops a reaction recording plus the clip it reacts to (e.g. in the Drive "CONTENT CREATION/TO BE EDITED" folder).
---

# Reaction video editor

## The creator's rules (do not change them)

1. **Cut ALL silences, strictly.** Every moment she is not speaking is removed: pauses between words and sentences, looking down, moving the mic to/from the phone, putting the mic down, breaths. Boundaries are taken from the AUDIO, never from ASR word times (those drift up to 0.4 s and both leave silence in and clip words). Nothing she actually says may be clipped: let every word finish.
2. **Cut wrong takes only when they are clearly wrong takes**: a sentence abandoned and restarted, a repeated phrase, a spoken instruction to the editor ("cut that part") together with the flubbed line it refers to. Don't cut small words, fillers inside a sentence or anything that might be intentional. When unsure, keep it and mention it.
3. **KEEP the reaction intro** ("I want you to watch this clip with me", "I need you to watch this video with me"). It tells viewers this is a reaction video. The creator explicitly asked for it to stay. Mid-video bridging lines like "let's continue hearing what she has to say" may be cut (she approved that in the first video); if in doubt, keep and ask.
4. **Clip parts play in a box while she stays on screen (coach layout, the creator's standing choice).** While she recorded, she held the mic to her phone; those stretches mark *which part of the clip she wants heard*. In the edit the ORIGINAL clip (video and its own audio) plays in a 4:5 box in the top corner away from her face, and under it she is on screen watching: her own footage from the moment that clip part was playing in her recording. When she speaks, it is her alone, full frame, with captions. (`render.py` does this by default: `--layout pip`.)
5. **Ratio 9:16** (1080x1920, 30 fps).
6. **Captions only on the creator's speech**, positioned **just above her head**, 1 to 3 words at a time. No captions over the clip (it has its own).
7. That's all. No music, zooms, sound effects, B-roll or transitions unless the user asks.
8. **Clip and creator never overlap.** While the clip plays, she is only watching or listening; while she speaks, the clip is not playing. She is never seen speaking without sound while the clip plays, and no line of hers is ever seen or heard twice. (In the pip layout her footage under the box must come from the exact moment that clip part was playing in her recording, never from a moment she was talking: render.py refuses otherwise. Check with a face strip: sample her face every ~1 s through every clip part and confirm her mouth is closed or reacting, not talking.)
9. **Follow-button CTA on every video (creator's choice, 22 Nov).** A small looping animation sits at the TOP-LEFT for the whole video: a red TikTok-style "Follow" button pops up, a cursor glides to it and clicks, it turns to "Following", fades, repeats every 2 s. NO words like "follow my account" anywhere (TikTok flags that); the button alone is the CTA. The clip box always goes TOP-RIGHT so they never collide. Asset: `assets/follow_cta.mov` (made by `scripts/make_cta.py`, which also writes a green-screen MP4 and GIF); render.py adds it by default (`--cta none` to switch off). Applies to captions-only videos too.

## One video at a time (creator's rule)

When there are several videos to edit, do them strictly ONE AFTER ANOTHER:
1. Edit video 1 completely.
2. Cross-check it against EVERY rule (silence check, word check for clipped/missing words, clip is the original and plays in the box, face strip shows her only watching under the clip (rule 8), intro kept, only clear wrong takes cut, captions above the head, 9:16, ffprobe, frames).
3. Fix anything that fails and re-check.
4. Send it to the chat (SendUserFile) and move its raw files to DONE.
5. Only then start video 2.
Never batch-render several and check afterwards; never start the next one while the current one has an open problem.

## Two modes

| What she uploads | Mode | What to do |
|---|---|---|
| A recording **plus** the clip it reacts to | **Reaction** | Everything below: rules 1-7. |
| A recording **alone** (just her talking, no clip to react to) | **Captions only** | Add captions, and that is all: no cuts, no silence removal, nothing added. The video plays exactly as recorded. |

### Captions-only mode

```bash
python3 -I $SK/captions_only.py video.mp4 WORK --models "$MODELS"          # prints WORDS [id|time]word
python3 -I $SK/captions_only.py video.mp4 WORK --models "$MODELS" --say 37=eight --say 38=ball. --say 56=
python3 -I $SK/render.py WORK "<name> - EDITED.mp4"
```
- Same caption style and position as reaction mode (1-3 words, just above her head, Inter Black, white with black outline).
- Review the WORDS like an editor: fix accent mishearings (cross-check doubtful lines with whisper small.en), and hide stammered or restarted words in the captions only (`--say ID=`). The audio and video are never changed.
- Check: duration equals the original, frames show captions above the head, then deliver as usual.

## The clip must be the ORIGINAL

If the uploaded clip is someone else's reaction to a video (another person talking over it, an inset, a screen recording of TikTok, a repost or compilation), do NOT use it. Find the original post that footage came from and edit with that: see `references/find-original.md` (search, download through the Composio workbench, save "<title> (original).mp4" to TO BE EDITED, confirm by frames). Credit the original poster.

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
#   finds the CLIP runs (rec time -> clip time) and the face/caption position
python3 -I $SK/edl.py WORK --models "$MODELS"
#   cuts on the audio and prints WORDS as [id|time]word plus the piece list. Nothing is cut yet
python3 -I $SK/edl.py WORK --models "$MODELS" --cut 9-30,82-88 --say <id=Text> ...   # ids/ranges comma-separated in ONE --cut
#   ids come from THIS script's WORDS line (they change whenever clip_runs change: re-read them)
python3 -I $SK/render.py WORK "OUT.mp4"                       # ~1 min after the first run
python3 -I $SK/check_gaps.py OUT.mp4 -45                      # must print "none" for her pieces
```

### Review step (this is where the judgement goes)

Read the analyze.py transcript top to bottom like an editor:
- **Wrong takes**: a phrase said twice, a restart ("when you have bigger ones, bigger amounts of money" -> cut "bigger ones,"), a sentence abandoned midway. `--cut` the ids of the discarded version.
- **Clip runs**: each should match a moment she played the clip. If a run is missing or extra, fix `clip_runs` in `analysis.json` (rec start/end, clip start/end) and rerun edl.py.
- **Instructions to the editor said on camera** ("cut that part", "remove this", "start again"): cut the instruction AND the flubbed line it refers to.
- **Clip edges**: check each clip piece's in/out against the clip's own word timings (run `analyze.py`'s parakeet on clip.wav, or peek at a few seconds). The first clip usually starts at 0:00 even if detection says ~1 s; never start or end a clip piece mid-word.
- **Short replays** (under ~1.5 s, too short to auto-detect; her audio is quiet like the playback, ~1/3 of her own voice level): she held the mic up, so she wants it heard. Add it to `clip_runs` in `analysis.json` (find its clip time by cross-correlating that second against clip.wav) so it plays as a full-screen clip moment, like the rest of the clip.
- **Music-only clips** (no one talking, e.g. an animal video with a song): edl.py detects this and never trims the clip edges; pieces she paused between are joined exactly, so no footage is lost.
- **Asides** ("what am I saying?", talking to someone off camera, usually quieter than her normal voice): cut them, like an editor instruction. Re-check doubtful lines with the second model (whisper small.en) before deciding.
- **Playback speed**: her phone sometimes plays the clip faster (~1.25x), so the offset drifts and detection stops early. If her transcript contains the clip speaker's words right after a clip run, extend that run by hand (rec end = where her own voice starts; clip end = a clean word boundary in the ORIGINAL clip, at normal speed).
- **Watch the WHOLE clip before deciding where it ends.** If her playback stops before the clip's payoff (the moment the clip is about and that she reacts to, e.g. "Left church": the uncle lights a cigarette after leaving church), extend the clip piece to include it, normally to the clip's end. Her stopping early is not a choice to cut the punchline.
- **Accidental clip snippets before the real playback** (she tapped play, then restarted from 0:00): cut them like a false start.
- **Clipped words are the worst error.** Bursts of her voice with no word of their own (word endings like "acti-vities", "hap-pens") are kept automatically when they touch speech; never drop them. Confirm by listing `kept wordless burst` pieces and checking each is -10..-25 dB voice, not a bump.
- **Clip playback that analyze.py misses** (her phone played it ~1.25x and held close, so it is as loud as her voice): her transcript then contains the clip speaker's sentences. Map them by hand: get the clip's word times (normal speed) and set `clip_runs` (rec start/end where the playback is, clip start/end at clean sentence boundaries); `--cut-time` scrubbing fragments and false starts.
- **Silent / mime reactions** (no speech in her recording, e.g. recreating another creator's gestures): ask which sound plays under her part before editing. For a lip-sync to another creator's audio, build ONE continuous soundtrack (clip audio, real silence, their line placed on her matching moment) as a WAV and mux it; never rely on adelay/apad gaps, they leave timestamp holes that drop audio on some players. Credit both creators.
- **Caption spelling**: the ASR is English-only. In her accent "eagle" comes out as "ego"/"Igolo"; fix every one. Fix Nigerian words and mishearings with `--say` (e.g. `--say 30=Money --say 76=Omo, --say 77=` where an empty value hides a word). This changes captions only, never the audio.
- Never cut the creator's actual opinion, story or punchline to shorten the video.

### Layouts
- `--layout pip` (DEFAULT, the creator's standing choice since 21 Nov): she stays on screen, using her own footage from while the clip played, and the clip plays with its sound in a 4:5 box in the top corner away from her face. The box is sized automatically (top 160 px, bottom just above her forehead, 4:5) and put in the corner opposite her face; `--box W,H,X,Y` overrides. The 4:5 crop is centred on the clip's picture, skipping black bars (`--clip-crop-y` overrides). Her footage under the box is mapped from `clip_runs` by playback speed (her phone often played ~1.25x, so it is slowed to fit) and kept 0.15 s after a run starts and 0.5 s before it ends, so her mouth never moves into a line under the clip. If a clip piece runs past what she watched (e.g. the payoff added later), shorten that run's `me_end` to where she still sits watching, and the footage is stretched to cover it. render.py REFUSES to render if any footage under the box overlaps her speech (kept pieces or her words outside runs).
- `--layout full`: the clip fills the frame. Only if she asks for it.
- Check every pip render with a face strip (her face every ~1 s through every clip part): mouth closed or reacting (smile, frown, gasp), never talking; she must not be leaning out of frame. Also check the same clip line never plays twice (drop replay pieces that repeat a line already played). Check frames: the box must sit over the wall or her hair, never over her eyes or mouth. Then run the face-strip check from rule 8.

### Check before delivering

0. **Silence check**: `check_gaps.py OUT.mp4 -45` must list no gaps inside her pieces (it maps output times; compare with the piece list). Fix and re-render if it does.
0b. **Word check**: transcribe the output's creator pieces and compare with the WORDS list: every kept word must be there and complete, no filler sounds (hmm/uh/lip smacks) left as their own pieces.
1. Grab frames at a creator piece, at each clip piece and at a cut, and look at them: the clip must fill the frame, captions must sit above the head without covering the face and without running off the edges.
2. `ffprobe` the output: 1080x1920, 30 fps, h264 + aac, duration about equal to the sum printed by edl.py.
3. If captions look off, rerun render.py with `--caption-y <px>` (baseline) or `--size`.

### Deliver

- Send the MP4 to the user with `SendUserFile` (display: render). Name it `<original name> - EDITED.mp4`.
- Drive connector uploads are capped at 10 MB, so a finished video usually can't go back to Drive from here. Say so; don't re-encode it to a lower quality just to fit unless the user asks.
- Add a row to the record sheet "Edited Videos Record" (Sheets artifact https://claude.ai/artifact/VA6ARh4Aaue4y9KHD53L5n, Claude Docs project e404c207-18f6-4252-9639-2cf8fa8e93d1, sheet "Videos"): #, title, status Edited, mode, date, raw sec, edited sec, clip used/credit, what was cut, captions to check, notes. Write under the last record, never over a filled row.
- Report: final length vs raw length, what was cut (listen lines, wrong takes), and any caption words you corrected.

## How it works (for debugging)

- **Clip detection** (analyze.py `align`): band-passed audio, 1 s windows every 0.25 s, normalised cross-correlation against the whole clip. A real playback keeps the same offset (rec time minus clip time) for seconds; chance matches don't. Runs are grown into quiet edges, tightened with 0.4 s windows, and cut where her own (much louder) voice starts. If she rewound and replayed a bit, the repeat is dropped so the viewer hears each clip line once.
- **Words**: NVIDIA Parakeet TDT 0.6B (sherpa-onnx, offline) on everything outside the clip runs, with token timestamps; word ends are clamped to the speech burst (Silero VAD).
- **Pieces** (edl.py): 10 ms loudness frames; speech = louder than max(floor+30, speech_level-27) dB (about -40 dB on her phone, where silence is gated to ~-90). Runs closer than 0.07 s (inside a word) join; every other gap is removed; 0.02 s / 0.04 s kept before/after each run. Each group of runs is transcribed on its own for accurate words; wordless runs and tiny filler-only runs are dropped. `--cut` splits at the quietest 10 ms between words. Clip edges use the clip's 1-4 kHz band so its music bed isn't mistaken for speech; where she paused mid-phrase the two clip pieces join exactly, where she paused in a silence the silence is trimmed.
- **Render**: both inputs are converted once to upright CFR 1080x1920 mezzanines with loudness-normalised (-14 LUFS) audio; pieces are frame-snapped, trimmed, given 8 ms fades and concatenated; captions are an ASS file (Inter Black, white, black outline) burned in at `head_top - 30` px.
