# ShallyBuilds editing style ("Red Stage")

Our own take on the presenter-plus-graphics format: white grid stage, red labels and a red-framed presenter. It deliberately differs from the references (dark charcoal stage, purple accents, serif captions).

## Two modes
| Mode | Look | Use for |
|---|---|---|
| `stage` | White grid background · red header pill at top · floating white cards in the middle · presenter in a red-bordered rounded frame in the bottom third | Hooks with proof, every list item, steps, comparisons, CTA |
| `aroll` | Full-frame presenter, white captions with shadow, optional `punchIn` zoom (1 → 1.12–1.16) | Emotional lines, punchlines, the "wake-up" line |

Switch mode every **3–8 seconds**. Start in `stage` (hook + proof), cut to `aroll` for the punchline, then alternate.

## Scene rules
- Every list item gets its own `stage` scene with `number` set (1, 2, 3) and a 2–4 word `header`.
- Headers: Title Case, ≤ 28 characters, no full stops.
- Cards: max 3–4 short lines, ≤ 5 words per line. One idea per card.
- Card types (`studio/src/types.ts`): `list`, `steps`, `stat`, `image`, `tags`, `compare`, `text`, `cta`.
  - `steps` for how-to sequences · `compare` for before/after or wrong/right · `stat` for one big number (only verified numbers) · `tags` for "all you need" / ingredients · `image` for generated visuals · `cta` always on the last scene.
- Last scene: `stage` + `cta` card ("Link in bio 👆") + `ding`.

## Sound
- `riser` on the first scene, `hit` on cuts to a-roll punchlines, `pop` or `whoosh` on new list items, `click` for UI steps, `ding` on the CTA.
- Music: optional low bed (`music` in spec, volume ≈ 0.10–0.15). Use only music we own or generated (e.g. vidIQ music generation), never trending copyrighted tracks inside the render.

## Captions
- Word-by-word, uppercase Inter Black, max 3 words per line.
- Active word = white text on a red pill.
- On stage: dark ink text above the presenter frame. On a-roll: white text with shadow, lower-middle.

## Filming spec for the presenter
- 9:16 vertical (TikTok ratio), 1080×1920 if possible, 30 fps.
- Face in the upper-middle of the frame with space above the head (the stage crop keeps the top ~60 % of the frame).
- Plain or tidy background, light in front of you, mic close.
- One continuous take per script is easiest. Pauses are fine because we cut on captions.
