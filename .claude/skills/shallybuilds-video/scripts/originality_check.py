#!/usr/bin/env python3
"""Check a new script against competitor transcripts for copied wording.

Fails (exit 1) when the draft shares any run of MAX_RUN+ consecutive words with
a source, or when more than MAX_OVERLAP of its 4-word phrases appear in the
sources. Common filler phrases ("in this video", "follow for more") are ignored.

  python3 originality_check.py draft.txt --sources research/transcripts/
  python3 originality_check.py draft.txt --sources a.txt b.vtt
"""
import argparse
import re
import sys
from pathlib import Path

MAX_RUN = 6          # longest allowed identical word run
MAX_OVERLAP = 0.05   # max share of 4-grams found in sources
N = 4

STOCK = {
    "follow me for more", "link in my bio", "click the link in", "the link in my", "in my bio to",
    "let me show you", "show you how to", "i'll send it to", "and i'll send you", "comment and i'll send",
    "in this video i", "make money with ai", "you need to know", "one of the best", "at the end of",
}


def words(text: str):
    text = re.sub(r"\d\d:\d\d:\d\d\.\d+\s*-->\s*\d\d:\d\d:\d\d\.\d+", " ", text)
    text = re.sub(r"WEBVTT|\[[^\]]*\]|`[^`]*`", " ", text)
    return re.findall(r"[a-z0-9']+", text.lower().replace("’", "'"))


def ngrams(ws, n):
    return [" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)]


def longest_run(a, b_set_by_len, b_words_joined):
    best, best_phrase = 0, ""
    for i in range(len(a)):
        for j in range(i + best + 1, len(a) + 1):
            phrase = " ".join(a[i:j])
            if f" {phrase} " in b_words_joined:
                best, best_phrase = j - i, phrase
            else:
                break
    return best, best_phrase


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("draft")
    ap.add_argument("--sources", nargs="+", required=True)
    a = ap.parse_args()

    files = []
    for s in a.sources:
        p = Path(s)
        files += sorted(f for f in p.rglob("*") if f.is_file() and f.suffix in {".txt", ".vtt", ".md", ".json"}) if p.is_dir() else [p]
    if not files:
        sys.exit("no source files found")

    draft = words(Path(a.draft).read_text(encoding="utf-8"))
    d_grams = [g for g in ngrams(draft, N) if g not in STOCK]
    failed = False
    print(f"Draft: {len(draft)} words · checked against {len(files)} source file(s)\n")
    for f in files:
        src = words(f.read_text(encoding="utf-8", errors="ignore"))
        joined = " " + " ".join(src) + " "
        s_grams = set(ngrams(src, N))
        shared = [g for g in d_grams if g in s_grams]
        overlap = len(shared) / max(1, len(d_grams))
        run, phrase = longest_run(draft, None, joined)
        bad = run >= MAX_RUN or overlap > MAX_OVERLAP
        failed |= bad
        status = "FAIL" if bad else "ok  "
        print(f"[{status}] {f.name}: 4-gram overlap {overlap:.1%}, longest shared run {run} words")
        if bad:
            if run >= MAX_RUN:
                print(f"        copied run: \"{phrase}\"")
            for g in sorted(set(shared))[:8]:
                print(f"        shared phrase: \"{g}\"")
    print("\nRESULT:", "REWRITE NEEDED" if failed else "ORIGINAL ✓")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
