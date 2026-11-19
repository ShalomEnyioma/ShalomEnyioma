# Finding the ORIGINAL clip behind someone else's reaction

The creator sometimes uploads a clip that is itself another creator's reaction
(a person talking over it, a picture-in-picture inset, a stitch, a screen
recording, a compilation, a news page's repost). **Never edit with that clip.**
Find the original post it came from and use that. Rule of thumb for "original":
the earliest post of that exact footage, by the person who filmed it, with no
one else's face or voice added.

## 1. Spot it
A clip needs this step when any frame shows: someone other than the subject
talking to camera, an inset video, TikTok UI (likes/share column, captions bar)
recorded on screen, a "repost"/news logo, or several unrelated videos stitched.
Grab 8-10 frames across the clip and look.

## 2. Collect clues from the reaction clip
- The on-screen caption of the inner video (e.g. "POV: Your department finalists
  signed out and someone's mum brought a goat for him").
- Any watermark: TikTok's download watermark shows `@handle` (bottom-left/right,
  moves around; check several frames at full size).
- Screen recordings show the poster's display name, caption, location tag and
  TikTok's "Search · ..." suggestion bar: zoom into the lower third.
- Place, people, date clues from transcripts of reposts ("As posted by Chisom on TT").

## 3. Search (ScrapeCreators via Composio, account `scrapecreators_matted-roe`)
- `SCRAPECREATORS_SEARCH_TIKTOK_BY_KEYWORD` with several phrasings of the story
  (sort by relevance AND date-posted), `SCRAPECREATORS_SEARCH_TIKTOK_TOP` with
  TikTok's own search suggestion if one is visible.
- Keep posts from the first day or two of the story; sort by time.
- Most results are reposts/compilations. Download the short first-hand ones and
  make a contact sheet (one frame each, labelled) to compare visually; audio can
  differ because reactors add music, so trust pictures + caption text.
- Once a handle is known: `SCRAPECREATORS_LIST_TIKTOK_PROFILE_VIDEOS` (handle,
  latest) and pick the post whose caption/date match; the original is usually the
  earliest and by far the most viewed.

## 4. Download it (TikTok's hosts are blocked in this container)
In `COMPOSIO_REMOTE_WORKBENCH`:
1. `SCRAPECREATORS_GET_TIKTOK_VIDEO` -> `aweme_detail.video.download_no_watermark_addr.url_list`
   (fall back to `play_addr_h264`, `play_addr`); `requests.get` with a browser
   User-Agent and `Referer: https://www.tiktok.com/`.
2. `upload_local_file(path)` -> it returns an `s3_url` on backend.composio.dev
   (blocked here) and an `s3key`. Resolve the short link inside the workbench
   (`requests.get(s3_url, allow_redirects=False).headers['Location']`): that is a
   presigned r2.cloudflarestorage.com URL, which this container CAN download.
3. `curl` it here within the hour.
4. Save a copy in Drive for later runs with `GOOGLEDRIVE_RESUMABLE_UPLOAD`
   (`file_to_upload: {name, mimetype, s3key}`, `folder_to_upload_to`: TO BE EDITED)
   named "<title> (original).mp4". This also works for files over 10 MB.

## 5. Confirm before editing
Frames of the original must show the same footage and caption as the inner video
of the reaction clip. Then run the normal reaction pipeline with the ORIGINAL as
`clip.mp4`. Her recording was made playing the reactor's version, so clip-run
detection may find little or nothing: map her clip moments by hand (her
transcript tells you what she played; find those lines/moments in the original)
and set `clip_runs` in analysis.json.

Credit the original poster (not the reactor) in the caption suggestion.

## Worked example: "Final year" (Nov 2026)
Reactor clip: a man in a kitchen talking over the goat sign-out video. Search for
the story found 70+ reposts. Two screen-recording reposts showed the caption +
display name "CHISOM_" and the watermark `@saintclaire_`. Profile listing gave
https://www.tiktok.com/@saintclaire_/video/7670505273852841217 (5 Aug 2026 11:18 UTC,
3.8M plays, 98 s), the earliest post. Saved as "Final year (original).mp4".
