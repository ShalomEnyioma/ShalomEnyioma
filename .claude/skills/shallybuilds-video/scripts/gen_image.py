#!/usr/bin/env python3
"""Generate an image with Google's Gemini image model (same family as Google Flow).

Needs a free Google AI Studio key in the GEMINI_API_KEY environment variable.
Images are written as PNG; vertical 9:16 by default for TikTok.

  python3 gen_image.py "prompt text" -o studio/public/images/hook.png
  python3 gen_image.py "prompt" -o out.png --aspect 1:1 --model gemini-2.5-flash-image
"""
import argparse
import base64
import json
import os
import sys
from pathlib import Path

import requests

API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
STYLE = (
    "Clean modern style, bright white background with bold red (#E11D2E) accents, "
    "high contrast, no text unless asked, no logos or watermarks of other brands."
)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--aspect", default="9:16")
    ap.add_argument("--model", default=os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"))
    ap.add_argument("--no-style", action="store_true", help="skip the ShallyBuilds style suffix")
    a = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        sys.exit("GEMINI_API_KEY is not set. Add it in the environment settings (free key: aistudio.google.com/apikey).")

    prompt = a.prompt if a.no_style else f"{a.prompt}\n\n{STYLE}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"responseModalities": ["IMAGE"], "imageConfig": {"aspectRatio": a.aspect}},
    }
    r = requests.post(API.format(model=a.model), headers={"x-goog-api-key": key}, json=body, timeout=180)
    if r.status_code != 200:
        sys.exit(f"Gemini error {r.status_code}: {r.text[:600]}")
    for cand in r.json().get("candidates", []):
        for part in cand.get("content", {}).get("parts", []):
            data = part.get("inlineData") or part.get("inline_data")
            if data:
                out = Path(a.out)
                out.parent.mkdir(parents=True, exist_ok=True)
                out.write_bytes(base64.b64decode(data["data"]))
                print("wrote", out)
                return
    sys.exit("No image in response: " + json.dumps(r.json())[:600])


if __name__ == "__main__":
    main()
