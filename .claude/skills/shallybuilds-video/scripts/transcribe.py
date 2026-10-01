#!/usr/bin/env python3
"""Word-level captions from real footage, using Gemini (needs GEMINI_API_KEY).

Extracts mono audio with Remotion's bundled ffmpeg, asks Gemini for a
verbatim transcript with per-word start/end times, and prints caption JSON
in the same format as script_to_captions.py.

  python3 transcribe.py studio/public/footage/take1.mp4 > studio/specs/NNN-captions.json
"""
import base64
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

STUDIO = Path(__file__).resolve().parents[4] / "studio"
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
PROMPT = (
    "Transcribe this speech verbatim (keep Nigerian Pidgin words as spoken). "
    "Return ONLY a JSON array, one object per spoken word, in order: "
    '[{"text": "word", "start": seconds, "end": seconds}]. '
    "Times are floats in seconds from the start of the audio, accurate to 0.05s. "
    "Keep punctuation attached to the word it follows."
)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    key = os.environ.get("GEMINI_API_KEY") or sys.exit("GEMINI_API_KEY is not set.")
    model = os.environ.get("GEMINI_TEXT_MODEL", "gemini-2.5-flash")
    src = Path(sys.argv[1]).resolve()

    with tempfile.TemporaryDirectory() as td:
        audio = Path(td) / "audio.mp3"
        subprocess.run(
            ["npx", "remotion", "ffmpeg", "-y", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-b:a", "48k", str(audio)],
            cwd=STUDIO, check=True, capture_output=True,
        )
        b64 = base64.b64encode(audio.read_bytes()).decode()

    body = {
        "contents": [{"parts": [{"inline_data": {"mime_type": "audio/mp3", "data": b64}}, {"text": PROMPT}]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0},
    }
    r = requests.post(API.format(model=model), headers={"x-goog-api-key": key}, json=body, timeout=300)
    if r.status_code != 200:
        sys.exit(f"Gemini error {r.status_code}: {r.text[:600]}")
    text = r.json()["candidates"][0]["content"]["parts"][0]["text"]
    words = json.loads(re.sub(r"^```(json)?|```$", "", text.strip()))
    words = [{"text": w["text"], "start": round(float(w["start"]), 3), "end": round(float(w["end"]), 3)} for w in words]
    json.dump(words, sys.stdout, indent=1)
    print(f"\n{len(words)} words, ends at {words[-1]['end']:.1f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
