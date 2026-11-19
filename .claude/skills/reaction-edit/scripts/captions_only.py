#!/usr/bin/env python3
"""CAPTIONS-ONLY mode: a talking-head video with NO clip to react to.

  python3 captions_only.py <video.mp4> <workdir> [--say 12=Omo] [--models DIR]
  python3 render.py <workdir> "<name> - EDITED.mp4"

Nothing is cut, nothing is added: the whole video plays as recorded, and the
creator's speech gets the same captions as the reaction edits (1-3 words, just
above her head). First run prints every word as [id|time]word; fix ASR spellings
with --say and run again, then render.

Word times come from short speech runs found on the AUDIO (same detector as
edl.py), so captions appear when she actually says the words.
"""
import argparse, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from analyze import to_wav, face_box, probe_duration  # noqa: E402
from edl import db_env, runs_of, recognizer, transcribe, FILLERS  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video"); ap.add_argument("workdir")
    ap.add_argument("--say", action="append", default=[], help="ID=TEXT caption fix; ID= hides the word")
    ap.add_argument("--models", default=os.environ.get("REACTION_MODELS", os.path.expanduser("~/.cache/reaction-edit/models")))
    a = ap.parse_args()
    W = a.workdir; os.makedirs(W, exist_ok=True)
    wav = os.path.join(W, "me.wav")
    me = to_wav(a.video, wav)
    dur = probe_duration(a.video)
    env = db_env(me)
    floor, level = np.percentile(env, 10), np.percentile(env, 90)
    thr = max(floor + 30, level - 27)
    runs = [[s * 0.01, e * 0.01] for s, e in runs_of(env > thr) if e - s >= 6]
    groups, g = [], []
    for r in runs:
        if g and r[0] - g[-1][1] > 0.6: groups.append(g); g = []
        g.append(r)
    if g: groups.append(g)
    cache = os.path.join(W, "words.json")
    if os.path.exists(cache):
        words = json.load(open(cache))
    else:
        rec = recognizer(a.models)
        words = []
        for g in groups:
            for w in transcribe(rec, me, g[0][0], g[-1][1]):
                # a word must start inside speech: if its time fell in a pause, move it to the next run
                for s, e in g:
                    if w["start"] < s: w["start"] = s; break
                    if s <= w["start"] <= e: break
                if w["w"].lower().strip(".,!?'\" ") not in FILLERS:
                    words.append(w)
        for k, w in enumerate(words):
            w["i"] = k
            w["end"] = min(w["end"], words[k + 1]["start"]) if k + 1 < len(words) else w["end"]
        json.dump(words, open(cache, "w"), indent=1)
    fixes = dict(s.split("=", 1) for s in a.say)
    for w in words:
        w.pop("caption", None)
        if str(w["i"]) in fixes: w["caption"] = fixes[str(w["i"])]
    face_file = os.path.join(W, "face.json")
    if os.path.exists(face_file):
        face = json.load(open(face_file))
    else:
        face = face_box(a.video, list(np.linspace(1, max(1.5, dur - 1), 10)))
        json.dump(face, open(face_file, "w"))
    piece = {"type": "me", "in": 0.0, "out": round(dur, 3), "words": words, "text": " ".join(w["w"] for w in words)}
    json.dump({"reaction": os.path.abspath(a.video), "clip": None, "face": face, "pieces": [piece]},
              open(os.path.join(W, "edl.json"), "w"), indent=1)
    json.dump({"words": words, "clip_runs": []}, open(os.path.join(W, "analysis.json"), "w"))
    print(f"duration {dur:.1f}s, {len(words)} words, face={face}")
    print("WORDS: " + "  ".join(f"[{w['i']}|{w['start']:.2f}]{w.get('caption', w['w'])}" for w in words))


if __name__ == "__main__":
    main()
