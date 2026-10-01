#!/usr/bin/env python3
"""Turn a script (or a WEBVTT transcript) into word-level caption timings.

Script mode spreads words evenly at a speaking rate, giving a little extra
time to longer words and pausing after punctuation. Use it for a first cut or
when no transcript exists; replace with real timings from transcribe.py when
footage is available.

  python3 script_to_captions.py script.txt --wps 2.6 --start 0.2 > captions.json
  python3 script_to_captions.py transcript.vtt > captions.json
"""
import argparse
import json
import re
import sys


def ts(s: str) -> float:
    h, m, rest = s.split(":")
    return int(h) * 3600 + int(m) * 60 + float(rest)


def from_vtt(text: str):
    words = []
    for m in re.finditer(r"(\d\d:\d\d:\d\d\.\d+)\s*-->\s*(\d\d:\d\d:\d\d\.\d+)\s*\n(.+?)(?:\n\n|\Z)", text, re.S):
        a, b, line = ts(m.group(1)), ts(m.group(2)), " ".join(m.group(3).split())
        toks = line.split()
        weights = [len(t) + 2 for t in toks]
        total, cur = sum(weights), a
        for t, w in zip(toks, weights):
            dur = (b - a) * w / total
            words.append({"text": t, "start": round(cur, 3), "end": round(cur + dur, 3)})
            cur += dur
    return words


def from_script(text: str, wps: float, start: float):
    # Drop stage directions like [ON SCREEN] lines and bracketed notes.
    lines = [l for l in text.splitlines() if l.strip() and not l.strip().startswith(("`", "[ON", "#"))]
    text = re.sub(r"\[[^\]]*\]", " ", " ".join(lines))
    toks = text.split()
    words, cur = [], start
    for t in toks:
        dur = (1 / wps) * (0.7 + 0.3 * min(len(t), 10) / 5)
        words.append({"text": t, "start": round(cur, 3), "end": round(cur + dur, 3)})
        cur += dur + (0.22 if re.search(r"[.!?]$", t) else 0.08 if t.endswith(",") else 0)
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file")
    ap.add_argument("--wps", type=float, default=2.6, help="words per second (2.6 ≈ 156 wpm)")
    ap.add_argument("--start", type=float, default=0.2)
    a = ap.parse_args()
    text = open(a.file, encoding="utf-8").read()
    words = from_vtt(text) if text.lstrip().startswith("WEBVTT") else from_script(text, a.wps, a.start)
    json.dump(words, sys.stdout, indent=1)
    print(f"\n{len(words)} words, ends at {words[-1]['end'] if words else 0:.1f}s", file=sys.stderr)


if __name__ == "__main__":
    main()
