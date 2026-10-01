---
name: shallybuilds-video
description: Make an original ~40-second TikTok/Reel for @shallybuilds — research what's working, write an original script in Shally's voice, check it isn't copied, plan the shots, generate images, and render the finished 1080x1920 video in the ShallyBuilds red/white "stage" style. Use when the user asks for a new video, script, hook, content idea, competitor research for content, or to render/edit a talking-head clip.
---

# ShallyBuilds Video Engine

Brand: **@shallybuilds** (TikTok + brand name) · red `#E11D2E` + white · casual tone · topics: AI, making money with AI, latest Nigerian gist · CTA: **link in bio**.

Read before working: `references/brand.md`, `references/script-rules.md`, `references/style-spec.md`. For research, `references/research.md`.

## Pipeline (do every step, in order)

1. **Pick the topic.** If the user gave one, use it. Otherwise research (step 2) and propose 3 ideas with the evidence (views, saves, date) and let the user pick.
2. **Research patterns, not wording.** Use ScrapeCreators (Composio) and vidIQ per `references/research.md`. Save every competitor transcript you read to `research/transcripts/<handle>_<id>_<slug>.txt`. Note only *patterns* (format, hook type, length, CTA style). Never paste competitor sentences into a draft.
3. **Write the script** per `references/script-rules.md`: 3 hook options + one body + the standard CTA, ≤ 105 spoken words (≈ 40 s). Save to `content/scripts/NNN-slug.txt` (spoken words only; the chosen hook first).
4. **Originality gate.** Run
   `python3 .claude/skills/shallybuilds-video/scripts/originality_check.py content/scripts/NNN-slug.txt --sources research/transcripts/`
   If it prints `REWRITE NEEDED`, rewrite the flagged lines in new words and re-run until `ORIGINAL ✓`. Never weaken the thresholds.
5. **Fact gate.** List every factual claim (tool names, prices, features, news, numbers). Verify each against a primary source (WebSearch/WebFetch or the tool's site). For Nigerian gist, confirm with two reputable outlets and the date. Remove anything unverifiable. No invented quotes, testimonials or earnings.
6. **Show the user** the script, the 3 hooks, the fact list with sources, and the originality result. Get a go-ahead before rendering.
7. **Captions.**
   - With footage: `python3 .claude/skills/shallybuilds-video/scripts/transcribe.py studio/public/footage/<file>.mp4 > studio/specs/NNN-captions.json` (needs `GEMINI_API_KEY`).
   - Without footage (draft / AI voice): `python3 .claude/skills/shallybuilds-video/scripts/script_to_captions.py content/scripts/NNN-slug.txt --wps 2.8 > studio/specs/NNN-captions.json`
8. **Images (optional).** For image cards, generate original visuals:
   `python3 .claude/skills/shallybuilds-video/scripts/gen_image.py "<prompt>" -o studio/public/images/NNN-<name>.png`
   Never prompt for other creators' faces, logos or watermarks.
9. **Shot plan → spec.** Write `studio/specs/NNN.json` (schema in `studio/src/types.ts`, example in `studio/specs/example.json`) following the scene rules in `references/style-spec.md`. Embed the captions array.
10. **Render.** From `studio/`:
    - stills to check layout: `npx remotion still ShallyShort out/NNN-f300.png --frame=300 --props=specs/NNN.json` (look at 3–4 frames, fix overlaps)
    - video: `npx remotion render ShallyShort out/NNN.mp4 --props=specs/NNN.json --concurrency=4`
11. **Deliver.** Send the MP4 with SendUserFile, plus the caption text and hashtags (`references/brand.md`). Commit script, spec and images (not `studio/out/`).
12. **Publish (only on request).** Blotato can post or schedule to TikTok/Instagram/YouTube. Confirm account, caption and time with the user before any publish call.

## Footage
The user films in 9:16 (TikTok ratio). Put clips in `studio/public/footage/`. To fetch a Drive link shared as "Anyone with the link":
`python3 .claude/skills/shallybuilds-video/scripts/fetch_drive.py "<drive link>" studio/public/footage/<name>.mp4`
(needs `drive.usercontent.google.com` allowed in the environment's network settings).

## One-time setup in a fresh container
```
cd studio && npm install
python3 .claude/skills/shallybuilds-video/scripts/make_sfx.py   # only if studio/public/sfx is missing
```

## Credentials
- `GEMINI_API_KEY` (environment variable): images + transcription. Free key from Google AI Studio. Never ask the user to paste keys into chat.
- ScrapeCreators via Composio; vidIQ and Blotato via their connectors.
