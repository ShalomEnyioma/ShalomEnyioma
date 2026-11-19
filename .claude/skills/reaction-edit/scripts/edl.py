#!/usr/bin/env python3
"""Rebuild <workdir>/edl.json from analysis.json after reviewing the transcript.

  python3 edl.py <workdir> [--cut 81-82,140] [--keep 34-41] [--gap 0.06] [--pad 0.04]

--cut   word ids to remove (wrong takes, false starts, repeats)
--keep  word ids to keep even though analyze.py marked them as a "listen to this" cue
Every pause longer than about gap+2*pad seconds between kept words is removed.
"""
import argparse, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from analyze import first_pass_edl, to_wav  # noqa: E402


def ids(spec):
    out = set()
    for part in filter(None, (spec or "").split(",")):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir"); ap.add_argument("--cut", default=""); ap.add_argument("--keep", default="")
    ap.add_argument("--gap", type=float, default=0.06); ap.add_argument("--pad", type=float, default=0.04)
    ap.add_argument("--say", action="append", default=[], help="ID=TEXT caption fix; ID= hides the word")
    a = ap.parse_args()
    import wave, numpy as np
    an = json.load(open(os.path.join(a.workdir, "analysis.json")))
    import wave, numpy as np
    w = wave.open(os.path.join(a.workdir, "clip.wav"))
    clip_audio = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    edl, auto_cut = first_pass_edl(an["words"], an["clip_runs"], None, clip_audio, gap_keep=a.gap, pad=a.pad)
    remove = (set(auto_cut) - ids(a.keep)) | ids(a.cut)
    # re-run grouping with the final cut set
    words = [dict(w, _drop=w["i"] in remove) for w in an["words"]]
    pieces, cur = [], None
    items = sorted([("me", w["start"], w) for w in words] + [("clip", r["me_start"], r) for r in an["clip_runs"]],
                   key=lambda x: x[1])
    from analyze import snap_quiet
    for kind, t, o in items:
        if kind == "clip":
            if cur: pieces.append(cur); cur = None
            pieces.append({"type": "clip", "clip_in": snap_quiet(clip_audio, o["clip_start"]) if o["clip_start"] > 0 else 0.0,
                           "clip_out": snap_quiet(clip_audio, o["clip_end"])})
            continue
        if o["_drop"]:
            if cur: pieces.append(cur); cur = None
            continue
        s, e = o["start"] - a.pad, o["end"] + a.pad
        if cur and s - cur["out"] <= a.gap:
            cur["out"], cur["last"] = round(e, 3), o["i"]; cur["text"] += " " + o["w"]
        else:
            if cur: pieces.append(cur)
            cur = {"type": "me", "in": round(max(0, s), 3), "out": round(e, 3), "first": o["i"], "last": o["i"], "text": o["w"]}
    if cur: pieces.append(cur)
    # never clip a word: grow each piece's edges until the voice has actually stopped
    w = wave.open(os.path.join(a.workdir, "me.wav"))
    me = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768
    fr = 160  # 10 ms
    env = np.sqrt(np.convolve(me ** 2, np.ones(fr) / fr, mode="same"))
    speech_lvl = np.percentile(env[env > 1e-4], 90)
    quiet = 0.12 * speech_lvl
    lvl = lambda t: float(env[min(len(env) - 1, max(0, int(t * 16000)))])
    for k, p in enumerate(pieces):
        if p["type"] != "me": continue
        nxt_lim = pieces[k + 1]["in"] if k + 1 < len(pieces) and pieces[k + 1]["type"] == "me" else p["out"] + 0.3
        prv_lim = pieces[k - 1]["out"] if k > 0 and pieces[k - 1]["type"] == "me" else p["in"] - 0.2
        t = p["out"]
        while t < min(nxt_lim, p["out"] + 0.3) and lvl(t) > quiet: t += 0.01
        p["out"] = round(t + 0.03, 3)
        t = p["in"]
        while t > max(prv_lim, p["in"] - 0.15) and lvl(t) > quiet: t -= 0.01
        p["in"] = round(max(t - 0.02, prv_lim if k > 0 and pieces[k - 1]["type"] == "me" else 0.0), 3)
    # caption text fixes (ASR spelling): --say 30=Money --say 76=Omo, --say 77=
    fixes = dict(s.split("=", 1) for s in a.say)
    for wd in an["words"]:
        if str(wd["i"]) in fixes: wd["caption"] = fixes[str(wd["i"])]
    json.dump(an, open(os.path.join(a.workdir, "analysis.json"), "w"), indent=1)
    json.dump({"reaction": an["reaction"], "clip": an["clip"], "face": an["face"], "pieces": pieces},
              open(os.path.join(a.workdir, "edl.json"), "w"), indent=1)
    tot = 0
    for p in pieces:
        if p["type"] == "clip":
            d = p["clip_out"] - p["clip_in"]; print(f"CLIP {p['clip_in']:6.2f}-{p['clip_out']:6.2f} ({d:.1f}s)")
        else:
            d = p["out"] - p["in"]; print(f"ME   {p['in']:6.2f}-{p['out']:6.2f} ({d:.2f}s) {p['text']}")
        tot += d
    print(f"{len(pieces)} pieces, {tot:.1f}s")


if __name__ == "__main__":
    main()
