# Research playbook

Goal: find **what topics and formats are working right now**, then write our own. Spend credits carefully.

## Accounts to study
See `accounts.md` (edit it to add or remove). Our own account `@shallybuilds` is included so we learn what our audience already responds to.

## Tools
| Need | Tool | Cost |
|---|---|---|
| Profile stats | Composio `SCRAPECREATORS_GET_TIKTOK_PROFILE` | 1 credit |
| Top / latest videos | `SCRAPECREATORS_LIST_TIKTOK_PROFILE_VIDEOS` (`sort_by: popular` and `latest`) | 1 credit/page |
| Transcript | `SCRAPECREATORS_GET_TIKTOK_VIDEO_TRANSCRIPT` (`use_ai_as_fallback: true` only if needed) | 1 (+10) |
| Find outliers by topic | vidIQ `vidiq_instagram_tiktok_outlier_search` (audience: `Culture/Region: Nigeria; Global: false; Demographics: young adults 18-35 wanting to earn online with AI;`) | 5 credits |
| Watch a video (editing breakdown) | vidIQ `vidiq_watch_shortform_content` (full URL, not vm.tiktok short links) | 10 credits |
| Nigerian gist / news | WebSearch + WebFetch on reputable outlets (Punch, Premium Times, Channels, TechCabal, BusinessDay); confirm with 2 sources | free |

## What to record (in `research/notes/YYYY-MM-DD.md`)
For each strong video: URL, views, saves, comments, length, date, **topic**, **hook type**, **body framework**, **CTA type**, **visual format**. Patterns only, no copied lines.

## Signals that matter
- **Saves ÷ views ≥ 2 %** means people want to come back to it, so make the tutorial version.
- **Comments ÷ views ≥ 0.5 %** means the topic sparks conversation, so use it as a hook.
- Videos 35–55 s usually beat 90 s+ ones in this niche.
- Recent (< 30 days) beats old for "latest" topics.

## Save transcripts
Every transcript read goes to `research/transcripts/<handle>_<videoId>_<slug>.txt`, so the originality checker covers it.
