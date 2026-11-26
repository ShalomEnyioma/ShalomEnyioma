#!/usr/bin/env python3
"""Build <workdir>/edl.json (the cut list) from analysis.json, cutting on the AUDIO.

  python3 edl.py <workdir> [--cut 81-82,140] [--cut-time 82.9-86.6] [--say 30=Money]
                           [--bridge 0.10] [--pre 0.03] [--post 0.06] [--models DIR]

Why audio, not ASR timestamps: ASR word times drift by up to ~0.4 s, which both
leaves silences in and clips the ends of words. Here every boundary comes from
the creator's own loudness:

  1. Speech frames (10 ms) = louder than a threshold set between her noise floor
     and her speech level. Phone recordings gate silence to about -90 dB, speech
     sits around -15 dB, so the split is clean.
  2. Runs of speech closer than --bridge (0.10 s; the gap inside a word such as a
     "t" or "p") are joined. EVERY other gap is removed. That is the creator's
     rule: no micro-silences at all.
  3. Each run gets --pre / --post seconds so word onsets/tails are never clipped.
  4. Each run is transcribed on its own (short audio => accurate words) and runs
     with no words (mic handling, breaths, bumps) are dropped.
  5. --cut drops words: the cut boundary is snapped to the quietest 10 ms frame
     between the neighbouring words, so it never lands inside a word.
  6. Clip pieces: the original clip, trimmed at both edges to where the clip's
     speech starts/stops (its own internal pauses are the clip creator's pacing
     and are left alone).

The first run (no --cut) prints every word as [id]word with its time: pick the ids
to cut from that list, then run again with --cut.
"""
import argparse, json, os, sys, wave
import numpy as np

SR = 16000
HOP = 160  # 10 ms
FILLERS = {"", "hm", "hmm", "mm", "mmm", "m", "um", "umm", "uh", "uhh", "ah", "eh", "er", "erm", "oh"}


def load(path):
    w = wave.open(path)
    return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def db_env(a):
    n = len(a) // HOP
    fr = a[: n * HOP].reshape(n, HOP)
    return 20 * np.log10(np.sqrt(np.mean(fr ** 2, axis=1)) + 1e-6)


def ids(spec):
    out = set()
    for part in filter(None, (spec or "").split(",")):
        a, _, b = part.partition("-")
        out.update(range(int(a), int(b or a) + 1))
    return out


def runs_of(mask):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]: j += 1
            out.append([i, j]); i = j
        else:
            i += 1
    return out


def recognizer(models):
    import sherpa_onnx
    d = os.path.join(models, "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8")
    return sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=f"{d}/encoder.int8.onnx", decoder=f"{d}/decoder.int8.onnx", joiner=f"{d}/joiner.int8.onnx",
        tokens=f"{d}/tokens.txt", model_type="nemo_transducer", num_threads=4)


def transcribe(rec, audio, t0, t1):
    """Words in [t0,t1] with times clamped into the segment."""
    pad = int(0.25 * SR)
    s, e = int(t0 * SR), int(t1 * SR)
    seg = np.concatenate([np.zeros(pad, np.float32), audio[s:e], np.zeros(pad, np.float32)])
    st = rec.create_stream(); st.accept_waveform(SR, seg); rec.decode_stream(st)
    words, cur = [], None
    for tok, ts in zip(st.result.tokens, st.result.timestamps):
        t = min(max(t0 + ts - 0.25, t0), t1)
        if tok.startswith("▁") or tok.startswith(" ") or cur is None:
            if cur: words.append(cur)
            cur = {"w": tok.lstrip("▁ "), "start": round(t, 3)}
        else:
            cur["w"] += tok
    if cur: words.append(cur)
    words = [w for w in words if w["w"].strip(".,!?'\" ")]
    for k, w in enumerate(words):
        w["end"] = words[k + 1]["start"] if k + 1 < len(words) else round(t1, 3)
    return words


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir")
    ap.add_argument("--cut", default="", help="word ids to remove (wrong takes, editor instructions)")
    ap.add_argument("--cut-time", default="", help="rec-time ranges to remove, e.g. 82.9-86.6,90-91.2")
    ap.add_argument("--say", action="append", default=[], help="ID=TEXT caption fix; ID= hides the word")
    ap.add_argument("--bridge", type=float, default=0.07)
    ap.add_argument("--thr", type=float, default=None, help="speech threshold in dB (default: auto). Lower it for a quiet recording whose soft words fall under the auto threshold; keep it above the pauses' noise")
    ap.add_argument("--clip-no-trim", action="store_true", help="never trim clip edges (auto when the clip has no speech)")
    ap.add_argument("--pre", type=float, default=0.02)
    ap.add_argument("--post", type=float, default=0.04)
    ap.add_argument("--models", default=os.environ.get("REACTION_MODELS", os.path.expanduser("~/.cache/reaction-edit/models")))
    a = ap.parse_args()
    W = a.workdir
    an = json.load(open(os.path.join(W, "analysis.json")))
    me, cl = load(os.path.join(W, "me.wav")), load(os.path.join(W, "clip.wav"))
    env = db_env(me)
    # clip edges: judge speech by the 1-4 kHz band, so a music bed under the clip is not mistaken for talking
    from scipy.signal import butter, sosfiltfilt
    cenv = db_env(sosfiltfilt(butter(4, [1000, 4000], btype="band", fs=SR, output="sos"), cl))

    # ---- creator speech mask
    floor, level = np.percentile(env, 10), np.percentile(env, 90)
    thr = max(floor + 30, level - 27)   # breaths and room tails (~-44 dB) count as silence
    if a.thr is not None: thr = a.thr
    runs_clip = sorted(an["clip_runs"], key=lambda r: r["me_start"])
    allowed = np.ones(len(env), bool)
    for r in runs_clip:
        allowed[int(r["me_start"] * 100) - 2: int(r["me_end"] * 100) + 2] = False
    for rng in filter(None, a.cut_time.split(",")):
        s, e = map(float, rng.split("-")); allowed[int(s * 100): int(e * 100)] = False
    mask = (env > thr) & allowed
    rs = runs_of(mask)
    merged = []
    for s, e in rs:                                      # bridge in-word gaps only
        if merged and (s - merged[-1][1]) * 0.01 <= a.bridge and allowed[merged[-1][1]:s].all():
            merged[-1][1] = e
        else:
            merged.append([s, e])
    segs = [[s * 0.01, e * 0.01] for s, e in merged if (e - s) >= 6]  # >= 60 ms

    # ---- words per segment (transcribe groups of nearby segments together for context)
    rec = recognizer(a.models)
    words, groups, g = [], [], []
    for sg in segs:
        if g and sg[0] - g[-1][1] > 0.6: groups.append(g); g = []
        g.append(sg)
    if g: groups.append(g)
    for g in groups:
        ws = transcribe(rec, me, g[0][0], g[-1][1])
        for w in ws:   # attach each word to the segment containing (or nearest to) its start
            mid = w["start"] + 0.05
            best = min(range(len(g)), key=lambda k: 0 if g[k][0] <= mid <= g[k][1] else min(abs(mid - g[k][0]), abs(mid - g[k][1])))
            w["seg"] = (g[best][0], g[best][1])
            words.append(w)
    for i, w in enumerate(words): w["i"] = i
    seg_words = {}
    for w in words: seg_words.setdefault(w["seg"], []).append(w)
    # A burst with no word of its own is kept when it touches speech (it is the end or
    # start of a neighbouring word, e.g. "what | happens"); only isolated bursts are noise.
    # The recogniser sometimes stamps a word a little early, so the sound of the word itself
    # ("authen-tic") can be a CHAIN of short wordless bursts after the segment that got the word.
    # Grow outwards from kept speech: a wordless burst within 0.25 s of kept speech (or of a burst
    # already kept this way) is kept, up to 4 steps / 1.5 s from the speech it hangs off.
    cut_ids = ids(a.cut)
    speech = {k for k, sg in enumerate(segs) if (sg[0], sg[1]) in seg_words
              and any(w["i"] not in cut_ids for w in seg_words[(sg[0], sg[1])])}
    kept = {k for k, sg in enumerate(segs) if (sg[0], sg[1]) in seg_words}
    anchor = {k: k for k in speech}
    for _ in range(4):
        grown = False
        for k, sg in enumerate(segs):
            if k in kept: continue
            for j in (k - 1, k + 1):
                if j in anchor and (abs(segs[j][1] - sg[0]) < 0.25 or abs(sg[1] - segs[j][0]) < 0.25):
                    a0 = segs[anchor[j]]
                    if max(0.0, sg[0] - a0[1], a0[0] - sg[1]) <= 1.5:
                        kept.add(k); anchor[k] = anchor[j]; seg_words[(sg[0], sg[1])] = []; grown = True
                        break
        if not grown: break
    segs = [sg for k, sg in enumerate(segs) if k in kept]

    # ---- apply word cuts by splitting segments at the quietest frame between words
    cut = ids(a.cut)
    fixes = dict(s.split("=", 1) for s in a.say)
    for w in words:
        if str(w["i"]) in fixes: w["caption"] = fixes[str(w["i"])]

    def quiet_between(t0, t1):
        i0, i1 = int(t0 * 100), max(int(t0 * 100) + 1, int(t1 * 100))
        return (i0 + int(np.argmin(env[i0:i1]))) * 0.01

    pieces_me = []
    for s, e in segs:
        ws = seg_words[(s, e)]
        cur_s, cur_w = s, []
        for k, w in enumerate(ws):
            if w["i"] in cut:
                if cur_w:
                    b = quiet_between(cur_w[-1]["start"] + 0.05, w["start"] + 0.1)
                    pieces_me.append([cur_s, b, cur_w]); cur_w = []
                nxt = ws[k + 1] if k + 1 < len(ws) else None
                cur_s = quiet_between(w["start"] + 0.05, nxt["start"] + 0.1) if nxt else e
                continue
            cur_w.append(w)
        if cur_w or not ws: pieces_me.append([cur_s, e, cur_w])

    # ---- assemble timeline
    items = [("me", p[0], p) for p in pieces_me] + [("clip", r["me_start"], r) for r in runs_clip]
    items.sort(key=lambda x: x[1])
    cthr = np.percentile(cenv, 10) + 10
    pieces = []
    for kind, t, o in items:
        if kind == "clip":
            ci, co = int(o["clip_start"] * 100), int(o["clip_end"] * 100)
            pieces.append({"type": "clip", "clip_in": o["clip_start"], "clip_out": o["clip_end"]})
            continue
        s, e, ws = o
        near = [q for q in pieces_me if q is not o and (abs(q[0] - e) < 0.25 or abs(s - q[1]) < 0.25)]
        if e - s < 0.35 and not near:   # isolated tiny piece: keep it only if, heard alone, it is a real word
            alone = [w["w"].lower().strip(".,!?'\" ") for w in transcribe(rec, me, s, e)]
            if not [x for x in alone if x not in FILLERS]:
                print(f"dropped filler/noise piece {s:.2f}-{e:.2f}: {alone}"); continue
        pin, pout = max(0.0, s - a.pre), e + a.post
        if pieces and pieces[-1]["type"] == "me" and pin < pieces[-1]["out"]:
            pin = pieces[-1]["out"]
        pieces.append({"type": "me", "in": round(pin, 3), "out": round(pout, 3),
                       "words": [{"w": w["w"], "start": max(pin, w["start"]), "end": min(pout, w["end"]),
                                  **({"caption": w["caption"]} if "caption" in w else {})} for w in ws],
                       "text": " ".join(w["w"] for w in ws)})
    # ---- clip edges, judged on the clip's 1-4 kHz speech band (a music bed doesn't count)
    loud = cenv > cthr
    for k in range(1, len(loud) - 12):                      # bridge in-word dips < 0.12 s
        if not loud[k] and loud[k - 1]:
            j = k
            while j < len(loud) and not loud[j] and j - k < 12: j += 1
            if j < len(loud) and loud[j] and j - k < 12: loud[k:j] = True
    def speech_at(t): i = int(t * 100); return 0 <= i < len(loud) and loud[i]
    def gap_edges(t):   # (start, end) of the quiet gap containing t
        i = j = int(t * 100)
        while i > 0 and not loud[i - 1]: i -= 1
        while j < len(loud) and not loud[j]: j += 1
        return i * 0.01, j * 0.01
    clips = [p for p in pieces if p["type"] == "clip"]
    # music-only clip (no talking): its pictures carry the story, so never trim it; pieces
    # that she paused between are joined exactly at the pause
    clip_words = transcribe(rec, cl, 0, min(len(cl) / SR, 20.0))
    music_only = a.clip_no_trim or len(clip_words) < 3
    if music_only:
        print("clip has no speech: clip edges are not trimmed")
        for k in range(1, len(clips)):
            if abs(clips[k]["clip_in"] - clips[k - 1]["clip_out"]) < 0.6:
                clips[k]["clip_in"] = clips[k - 1]["clip_out"]
        clips = []
    for k, p in enumerate(clips):
        prev = clips[k - 1] if k else None
        joined = prev is not None and abs(p["clip_in"] - prev["clip_out"]) < 0.4
        if joined:
            B = (p["clip_in"] + prev["clip_out"]) / 2
            if speech_at(B):          # paused mid-phrase: join exactly, lose nothing
                prev["clip_out"] = p["clip_in"] = round(B, 3)
            else:                     # paused in a silence: trim the silence on both sides
                g0, g1 = gap_edges(B)
                prev["clip_out"] = round(g0 + 0.08, 3); p["clip_in"] = round(max(g0 + 0.08, g1 - 0.03), 3)
        elif not speech_at(p["clip_in"]):   # silent lead-in (also at 0:00) is trimmed
            p["clip_in"] = round(max(gap_edges(p["clip_in"])[1] - 0.03, 0), 3)
        nxt = clips[k + 1] if k + 1 < len(clips) else None
        if not (nxt and abs(nxt["clip_in"] - p["clip_out"]) < 0.4) and not speech_at(p["clip_out"] - 0.01):
            p["clip_out"] = round(gap_edges(p["clip_out"] - 0.01)[0] + 0.08, 3)
    json.dump({"reaction": an["reaction"], "clip": an["clip"], "face": an["face"], "pieces": pieces},
              open(os.path.join(W, "edl.json"), "w"), indent=1)

    # ---- report
    print(f"speech threshold {thr:.1f} dB (floor {floor:.1f}, level {level:.1f}); bridge {a.bridge}s")
    line = []
    for w in words:
        mark = "~~" if w["i"] in cut else ""
        line.append(f"[{w['i']}|{w['start']:.2f}]{mark}{w['w']}{mark}")
    print("WORDS: " + "  ".join(line))
    tot = 0
    for p in pieces:
        d = (p["clip_out"] - p["clip_in"]) if p["type"] == "clip" else (p["out"] - p["in"]); tot += d
        print(f"CLIP {p['clip_in']:6.2f}-{p['clip_out']:6.2f} ({d:.1f}s)" if p["type"] == "clip"
              else f"ME   {p['in']:6.2f}-{p['out']:6.2f} ({d:.2f}s) {p['text']}")
    print(f"{len(pieces)} pieces, {tot:.1f}s")


if __name__ == "__main__":
    main()
