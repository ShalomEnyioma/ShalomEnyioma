---
name: faceless-niche-research
description: Incomelabs' standard method for finding and validating faceless YouTube niches, built on Nick Winter's (@NickWinterYTA) niche-bending system (market + format, audience bend, obvious/creative niche bend, authority re-frame, re-made proven outliers), run with ScrapeCreators/vidIQ and our policy guardrails. Use EVERY time the user asks to find, pick, validate, compare or bend a niche, research a new faceless/automation channel, choose niches for a done-for-you client, or build a video idea bank for a niche — even if they don't mention Nick Winter.
---

# Faceless niche research (Nick Winter method, Incomelabs edition)

Full source playbook with timestamps: `research/nickwinter/framework.md` (read sections A, B, C, E, F before a big research job). Transcripts (git-ignored) are in `research/nickwinter/transcripts/`.

## Core model
**Niche = market + format.** The *format* is the proven part (title structure, video style, narrator, thumbnail style). The *market* is what we choose: **big in the real world, unsaturated on YouTube**. Never clone a winning channel 1:1 — "he is already making the 10K, there's no more 10K for you." We take a proven format and **bend** it.

Every viral niche moves through 4 stages: **(1) new format** (don't play here unless very creative) → **(2) audience bends** (1–4 weeks later) → **(3) obvious niche bends** (same time, speed matters) → **(4) creative niche bends** (weeks to years later — where the money is). Identify which stage a seed is in.

## The bends (always generate all five for each seed)
| Bend | What it is | Rule / test |
|---|---|---|
| **Audience bend** | Same format + market for another country/language (US→UK/CA/AU→DE/ES/FR/PT-BR) or presenter demographic | Only if that audience's **reality actually differs** (UK truckers ✅, UK "heating without electricity" ❌). **Adapt, never translate.** Check RPM — some language ports earn very little. |
| **Obvious niche bend** | Adjacent market, same audience type (cats→dogs, Toyota→Chevrolet) | Easy to spot → be fast; check nobody strong is there yet |
| **Creative niche bend** | Non-obvious market that fits the format's appeal (cat psychology→birds→Japanese child-raising) | Needs TAM proof + empty YouTube lane; the creative leap is ours (AI suggests only obvious ones) |
| **Authority re-frame** | Same proven concept explained by a more credible/intriguing authority ("what Japanese police teach seniors…", "KGB tradecraft…") | Must be **factual and sourced** — real institutions/documents, never a fake expert persona |
| **Re-made proven outliers** | Our own original version of topics that went viral before, even 4–5 years ago, from any channel/brand | Topic + structure only; **original researched script**, our own packaging |
Also: sub-niching down (whales out of "ocean"), seasonal re-skin (Christmas/winter), series/persona variants of a format.

## Process (run in order, record everything)
1. **Find seeds (outliers from small/new channels).** We don't have TubeLab/NexLev, so use:
   - ScrapeCreators `SCRAPECREATORS_SEARCH_YOUTUBE` (1 credit/page): `sort_by: popular`, `upload_date: this_month` (or `this_year` for evergreen), `duration: between_3_and_20_min` / `over_20_min`, `region: US`.
   - `SCRAPECREATORS_GET_YOUTUBE_CHANNEL` (pass `cache_max_age: "7d"` — free on cache hit) for subs, video count, join date, country.
   - `SCRAPECREATORS_LIST_YOUTUBE_CHANNEL_VIDEOS` (`sort: popular`) to see a channel's outliers vs its average.
   - vidIQ `vidiq_outliers` / `vidiq_keyword_research` only for finalists (credits are scarce — ask before heavy use).
   - Seed = a **recent video far above that channel's own average**, ideally on a young/small channel. Subscriber count itself is not a quality signal.
   - Trace ports back to the **US original**.
   - If the user later subscribes to TubeLab (Outliers Finder → "new viral videos from small channels"; Niche Finder sorted by views/day) or NexLev, prefer those for seeding.
2. **Decompose each seed:** market, format, stage (1–4).
3. **Generate bends:** for each seed produce audience / obvious / creative / authority / re-made-outlier candidates (aim for 10–20 total).
4. **Validate each bend:**
   - **TAM:** a real market-size or participation statistic from a credible source (verify, don't trust AI numbers).
   - **Title-swap search:** take the seed's best title, swap the market/audience word, search YouTube. Empty or weak = open lane; strong first mover = skip.
   - **Breadth:** list 30+ distinct video ideas or drop it (one-video topics belong on a broader channel).
   - **Audience value:** older (45–65+) / affluent / buyer audiences → higher RPM, longer watch time. Ad-friendly?
   - **Policy:** not politics/fake news, not fiction without a face, can be **genuinely educational and sourced**, won't look templated ("if an average viewer can tell it's automated, don't run it").
   - **Unit economics:** our cost per video vs expected views × RPM.
5. **Score** finalists on the scorecard below and pick. For a DFY client: Primary = best odds of YPP inside the deadline; Bonus = different audience, long-term earner.
6. **Build the idea bank** for each chosen niche:
   - Find 5–10 same-vibe channels **that have outliers** (drop ones without).
   - Pull their popular video lists → extract **~30 winning title formats** → these become the title rules.
   - Ask for "trends emerging in recent videos", then **"10 more ideas that haven't been done yet in this niche"** (that phrase matters).
   - Mine comments on the top 2–3 videos (100k+ views; skip 3–5k-view videos).
   - Competitor outlier rule for ongoing idea flow: video ≥7k views after 48h, or ≥4k within 12h.
7. **Launch rules:** 5–10 videos ready before Day 1; judge only after 5–10 uploads (low views + OK impressions = packaging; no impressions = channel/launch issue); track CTR + AVD per upload; re-mine our own comments weekly.

## Scorecard (1–5 each × weight, max 90)
| Criterion | Weight |
|---|---|
| Proven demand (outliers on small/new channels, recent) | ×3 |
| Retention potential at target length | ×3 |
| **Bend strength** (how differentiated/unclaimed our lane is after the title-swap test) | ×2 |
| Subscriber pull (series, loyal/older audience) | ×2 |
| Advertiser value / audience age & wealth | ×2 |
| Competition gap | ×1 |
| Production cost & speed | ×1 |
| Policy safety (inverted risk) | ×3 |
| Topic depth (30–50+ ideas) | ×1 |

## Output (always)
For each recommended niche: seed channel(s) with data, the stage, the exact bend used and why, TAM stat + source, title-swap search result, 3–5 proof channels (links, subs, standout video: title/views/date/length), 10 original sample titles, 30 title formats (for the chosen niche), channel-name ideas, risks. Never invent numbers — every figure from a tool response or cited source. Save client work in the client's private folder, not the public repo.

## Hard guardrails — never copy these parts of his playbook
No bought/aged accounts, anti-detect browsers or proxies to hide operators; no fake human "expert" personas selling to viewers; no evading AI-detection/SynthID (tick AI disclosure honestly); no copying scripts, near-identical thumbnails or re-uploads; no mass-produced templated output; no bypassing third-party/YouTube limits; no politics/fake-news volume plays; treat his income claims as unverified marketing. See framework section F.
