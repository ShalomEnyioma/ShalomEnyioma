#!/usr/bin/env python3
"""Analyse a reaction recording against the clip being reacted to.

  python3 analyze.py <reaction.mp4> <clip.mp4> <workdir> [--models DIR]

Writes <workdir>/analysis.json and prints a readable timeline:
  * clip runs   - where the recording is the clip playing into the mic, and
                  which part of the original clip that was (audio cross-correlation)
  * words       - every word the creator says, with start/end in the recording
  * face        - where the creator's head is in the 1080x1920 frame (for captions)
  * edl         - a first-pass edit decision list (see SKILL.md) that render.py reads

Nothing here is final: review the timeline, edit edl.json, then render.
"""
import argparse, json, os, subprocess, sys, wave
import numpy as np

SR = 16000
LISTEN_CUES = [  # phrases that only tell the viewer to listen; cut by default
    "listen to this", "listen to her", "listen to him", "listen to what", "let's listen", "let us listen",
    "let's hear", "let us hear", "let's continue", "let us continue", "continue hearing", "continue listening",
    "hear what she", "hear what he", "watch this", "let's see what", "let us see what", "let's watch",
    "need you to listen", "want you to listen", "check this out",
]


def sh(*a):
    subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def to_wav(src, dst):
    sh("ffmpeg", "-y", "-i", src, "-vn", "-ac", "1", "-ar", str(SR), dst)
    w = wave.open(dst)
    return np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32) / 32768


def probe_duration(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f],
                         capture_output=True, text=True).stdout
    return float(out.strip())


# ---------------------------------------------------------------- alignment
def align(me, cl, win_s=1.0, hop_s=0.25, thr=0.3, min_hits=5, ext_thr=0.18):
    """Find where the recording is the clip playing. A real playback keeps the SAME
    offset (rec time - clip time) for seconds on end; chance matches do not."""
    from scipy.signal import butter, sosfiltfilt, fftconvolve
    sos = butter(4, [300, 3400], btype="band", fs=SR, output="sos")
    a, b = sosfiltfilt(sos, me)[::4], sosfiltfilt(sos, cl)[::4]
    sr = SR // 4
    win, hop = int(win_s * sr), int(hop_s * sr)
    c2 = np.concatenate([[0], np.cumsum(b ** 2)])
    energy = np.sqrt(c2[win:] - c2[:-win]) + 1e-9
    hits = []  # (rec_t, ncc, offset)
    for s in range(0, len(a) - win, hop):
        x = a[s:s + win] - a[s:s + win].mean()
        nx = np.linalg.norm(x)
        if nx < 1e-3:
            continue
        ncc = fftconvolve(b, x[::-1], mode="valid") / (energy * nx)
        k = int(np.argmax(ncc))
        if ncc[k] >= thr:
            hits.append((s / sr, float(ncc[k]), s / sr - k / sr))

    def ncc_at(t, off):
        s, k = int(t * sr), int((t - off) * sr)
        if s < 0 or k < 0 or s + win > len(a) or k + win > len(b):
            return -1.0
        x, y = a[s:s + win] - a[s:s + win].mean(), b[k:k + win] - b[k:k + win].mean()
        return float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-9))

    # cluster hits by offset, then split each cluster where it goes quiet for > 1.25 s
    hits.sort(key=lambda h: h[2])
    clusters, cur = [], []
    for h in hits:
        if cur and abs(h[2] - np.median([c[2] for c in cur])) > 0.08:
            clusters.append(cur); cur = []
        cur.append(h)
    if cur: clusters.append(cur)
    runs = []
    for c in clusters:
        c.sort()
        group = [c[0]]
        for h in c[1:] + [None]:
            if h is not None and h[0] - group[-1][0] <= 1.25:
                group.append(h); continue
            span = group[-1][0] - group[0][0]
            if len(group) >= min_hits and span >= 1.0:
                off = float(np.median([g[2] for g in group]))
                st, en = group[0][0], group[-1][0]
                while ncc_at(st - hop_s, off) >= ext_thr: st -= hop_s   # grow into quiet edges
                while ncc_at(en + hop_s, off) >= ext_thr: en += hop_s
                runs.append({"me_start": round(st, 2), "me_end": round(en + win_s, 2), "offset": round(off, 3),
                             "hits": len(group), "mean_ncc": round(float(np.mean([g[1] for g in group])), 2)})
            if h is not None: group = [h]
    runs.sort(key=lambda r: r["me_start"])
    # overlapping runs: keep the stronger one
    out = []
    for r in runs:
        if out and r["me_start"] < out[-1]["me_end"] - 0.3:
            if r["hits"] * r["mean_ncc"] > out[-1]["hits"] * out[-1]["mean_ncc"]: out[-1] = r
            continue
        out.append(r)
    # tighten edges with short windows: a 1 s window that only half-overlaps the
    # playback still correlates, which would swallow the creator's first words
    fw, fh = 0.4, 0.05
    def fine(t, off):
        s, k, n = int(t * sr), int((t - off) * sr), int(fw * sr)
        if s < 0 or k < 0 or s + n > len(a) or k + n > len(b): return -1.0
        x, y = a[s:s + n] - a[s:s + n].mean(), b[k:k + n] - b[k:k + n].mean()
        return float(np.dot(x, y) / (np.linalg.norm(x) * np.linalg.norm(y) + 1e-9))
    for r in out:
        off, st, en = r["offset"], r["me_start"], r["me_end"]
        t, last_ok = en - 1.2, None
        while t <= en:
            if fine(t, off) >= 0.25: last_ok = t
            t += fh
        if last_ok is not None: r["me_end"] = round(last_ok + fw, 2)
        t, first_ok = st + 1.0, None
        while t >= st - 0.2:
            if fine(t, off) >= 0.25: first_ok = t
            t -= fh
        if first_ok is not None: r["me_start"] = round(first_ok, 2)
    prev_end = -1.0
    for r in out:
        r["clip_start"] = round(max(0.0, r["me_start"] - r["offset"]), 2)
        r["clip_end"] = round(r["me_end"] - r["offset"], 2)
        if r["clip_start"] < prev_end:          # creator rewound: don't show the same lines twice
            r["replayed_from"] = r["clip_start"]; r["clip_start"] = round(prev_end, 2)
        prev_end = r["clip_end"]
    return out


def snap_quiet(audio, t, radius=0.35):
    """Move t to the quietest 20 ms frame within +-radius (a natural pause)."""
    f = int(0.02 * SR)
    lo, hi = max(0, int((t - radius) * SR)), min(len(audio) - f, int((t + radius) * SR))
    best, bt = 1e9, t
    for s in range(lo, hi, f // 2):
        e = float(np.sqrt(np.mean(audio[s:s + f] ** 2))) + abs(s / SR - t) * 0.01
        if e < best:
            best, bt = e, s / SR
    return round(bt, 3)


# ---------------------------------------------------------------- speech
def words_for_regions(me, regions, models):
    import sherpa_onnx
    d = os.path.join(models, "sherpa-onnx-nemo-parakeet-tdt-0.6b-v2-int8")
    rec = sherpa_onnx.OfflineRecognizer.from_transducer(
        encoder=os.path.join(d, "encoder.int8.onnx"), decoder=os.path.join(d, "decoder.int8.onnx"),
        joiner=os.path.join(d, "joiner.int8.onnx"), tokens=os.path.join(d, "tokens.txt"),
        model_type="nemo_transducer", num_threads=4)
    words = []
    for (rs, re_) in regions:
        seg = me[int(rs * SR):int(re_ * SR)]
        # parakeet is happiest with < ~25 s chunks: split on the quietest points
        chunks, start = [], 0
        while len(seg) - start > 22 * SR:
            cut = int(snap_quiet(seg, (start / SR) + 20, radius=2.0) * SR)
            chunks.append((start, cut)); start = cut
        chunks.append((start, len(seg)))
        for (cs, ce) in chunks:
            st = rec.create_stream(); st.accept_waveform(SR, seg[cs:ce]); rec.decode_stream(st)
            r = st.result
            base = rs + cs / SR
            cur = None
            for tok, ts in zip(r.tokens, r.timestamps):
                if tok.startswith("▁") or tok.startswith(" ") or cur is None:
                    if cur: words.append(cur)
                    cur = {"w": tok.lstrip("▁ "), "start": round(base + ts, 3)}
                else:
                    cur["w"] += tok
            if cur: words.append(cur)
    # end times: up to the next word, capped by speech energy
    for i, w in enumerate(words):
        nxt = words[i + 1]["start"] if i + 1 < len(words) else w["start"] + 0.6
        guess = w["start"] + 0.12 + 0.06 * len(w["w"])
        w["end"] = round(min(nxt, guess, w["start"] + 0.9), 3)
    words = [w for w in words if w["w"]]
    for i, w in enumerate(words):
        w["i"] = i
    return words


def speech_intervals(me, models, min_sil=0.12):
    """Fine-grained speech/no-speech map of the recording (for silence cutting)."""
    import sherpa_onnx
    cfg = sherpa_onnx.VadModelConfig()
    cfg.silero_vad.model = os.path.join(models, "silero_vad.onnx")
    cfg.silero_vad.min_silence_duration = min_sil
    cfg.silero_vad.min_speech_duration = 0.08
    cfg.silero_vad.threshold = 0.4
    cfg.sample_rate = SR
    vad = sherpa_onnx.VoiceActivityDetector(cfg, buffer_size_in_seconds=600)
    out = []
    for i in range(0, len(me), 512):
        vad.accept_waveform(me[i:i + 512])
        while not vad.empty():
            out.append((vad.front.start / SR, (vad.front.start + len(vad.front.samples)) / SR)); vad.pop()
    vad.flush()
    while not vad.empty():
        out.append((vad.front.start / SR, (vad.front.start + len(vad.front.samples)) / SR)); vad.pop()
    return out


def refine_word_ends(words, vad):
    """Clamp each word's end to the end of the speech burst it sits in."""
    for w in words:
        for (s, e) in vad:
            if s - 0.1 <= w["start"] <= e:
                w["end"] = round(min(w["end"], e + 0.02) if w["end"] > e else w["end"], 3)
                break


# ---------------------------------------------------------------- face
def face_box(video, times):
    import cv2
    casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    boxes = []
    for t in times:
        p = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1",
                            "-vf", "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920",
                            "-f", "image2pipe", "-vcodec", "png", "-"], capture_output=True).stdout
        img = cv2.imdecode(np.frombuffer(p, np.uint8), cv2.IMREAD_GRAYSCALE)
        if img is None: continue
        f = casc.detectMultiScale(img, 1.1, 6, minSize=(160, 160))
        if len(f):
            x, y, w, h = max(f, key=lambda b: b[2] * b[3])
            boxes.append((x, y, w, h))
    if not boxes:
        return None
    x, y, w, h = [int(np.median([b[k] for b in boxes])) for k in range(4)]
    return {"x": x, "y": y, "w": w, "h": h, "head_top": max(0, int(y - 0.55 * h)), "samples": len(boxes)}


# ---------------------------------------------------------------- edl
def first_pass_edl(words, runs, vad, clip_audio, gap_keep=0.06, pad=0.04):
    """Speaker pieces = words grouped with all pauses > ~gap removed; clip pieces = the original clip."""
    low = " ".join(w["w"].lower().strip(".,!?") for w in words)
    # mark listen cues
    cut = set()
    toks = [w["w"].lower().strip(".,!?\"'") for w in words]
    for cue in LISTEN_CUES:
        c = cue.split()
        for i in range(len(toks) - len(c) + 1):
            if toks[i:i + len(c)] == c:
                # cut the sentence/clause the cue sits in: back to the previous , . ! ? and
                # forward to the next one (never more than 12 words either way)
                a, b = i, i + len(c) - 1
                while a > 0 and i - a < 12 and not words[a - 1]["w"].rstrip("\"'")[-1:] in ",.!?": a -= 1
                while b + 1 < len(words) and b - i < 12 and not words[b]["w"].rstrip("\"'")[-1:] in ".!?": b += 1
                cut.update(range(a, b + 1))
    items = []
    for w in words:
        items.append(("me", w["start"], w))
    for r in runs:
        items.append(("clip", r["me_start"], r))
    items.sort(key=lambda x: x[1])
    edl, cur = [], None
    for kind, t, obj in items:
        if kind == "clip":
            if cur: edl.append(cur); cur = None
            edl.append({"type": "clip", "clip_in": snap_quiet(clip_audio, obj["clip_start"]),
                        "clip_out": snap_quiet(clip_audio, obj["clip_end"]), "note": "clip the creator played"})
            continue
        if obj["i"] in cut:
            continue
        s, e = obj["start"] - pad, obj["end"] + pad
        if cur and s - cur["out"] <= gap_keep and obj["i"] == cur["last"] + 1:
            cur["out"], cur["last"] = round(e, 3), obj["i"]
            cur["text"] += " " + obj["w"]
        else:
            if cur: edl.append(cur)
            cur = {"type": "me", "in": round(max(0, s), 3), "out": round(e, 3), "first": obj["i"], "last": obj["i"], "text": obj["w"]}
    if cur: edl.append(cur)
    return edl, sorted(cut)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reaction"); ap.add_argument("clip"); ap.add_argument("workdir")
    ap.add_argument("--models", default=os.environ.get("REACTION_MODELS", os.path.expanduser("~/.cache/reaction-edit/models")))
    a = ap.parse_args()
    os.makedirs(a.workdir, exist_ok=True)
    me = to_wav(a.reaction, os.path.join(a.workdir, "me.wav"))
    cl = to_wav(a.clip, os.path.join(a.workdir, "clip.wav"))
    runs = align(me, cl)
    dur = len(me) / SR
    # The creator often starts talking while the clip's last syllable is still playing.
    # Her own voice is much louder than the phone speaker, so look at the last 0.9 s of
    # each run and end the run where a loud word starts.
    rms = lambda s, e: float(np.sqrt(np.mean(me[int(s * SR):int(e * SR)] ** 2) + 1e-12))
    for r in runs:
        base = rms(r["me_start"], r["me_end"])
        zone = words_for_regions(me, [(max(r["me_start"], r["me_end"] - 0.9), r["me_end"] + 0.3)], a.models)
        for w in zone:
            if w["start"] < r["me_end"] and rms(w["start"], w["start"] + 0.2) > 2.0 * base:
                r["me_end"] = round(w["start"] - 0.04, 2)
                r["clip_end"] = round(r["me_end"] - r["offset"], 2)
                break
    prev = None
    for r in runs:   # tiny gaps between consecutive clip pieces: keep the clip continuous
        if r["clip_start"] < 1.0 and prev is None: r["clip_start"] = 0.0
        if prev is not None and 0 < r["clip_start"] - prev["clip_end"] < 1.0: r["clip_start"] = prev["clip_end"]
        prev = r
    # speaker regions = everything outside clip runs
    regions, t = [], 0.0
    for r in runs:
        if r["me_start"] - t > 0.3: regions.append((t, r["me_start"]))
        t = r["me_end"]
    if dur - t > 0.3: regions.append((t, dur))
    vad = speech_intervals(me, a.models)
    words = words_for_regions(me, regions, a.models)
    refine_word_ends(words, vad)
    sample_t = [ (s + e) / 2 for (s, e) in regions for _ in [0] ][:12] or [dur / 2]
    face = face_box(a.reaction, sample_t)
    edl, cut = first_pass_edl(words, runs, vad, cl)
    res = {"reaction": os.path.abspath(a.reaction), "clip": os.path.abspath(a.clip), "duration": dur,
           "clip_runs": runs, "regions": regions, "face": face, "words": words, "listen_cut_word_ids": cut}
    json.dump(res, open(os.path.join(a.workdir, "analysis.json"), "w"), indent=1)
    json.dump({"reaction": res["reaction"], "clip": res["clip"], "face": face, "pieces": edl},
              open(os.path.join(a.workdir, "edl.json"), "w"), indent=1)
    # readable timeline
    print(f"duration {dur:.1f}s  face={face}")
    for r in runs:
        print(f"CLIP  rec {r['me_start']:6.2f}-{r['me_end']:6.2f}  = clip {r['clip_start']:6.2f}-{r['clip_end']:6.2f}")
    line, last = [], None
    for w in words:
        mark = "~~" if w["i"] in cut else ""
        if last is not None and w["start"] - last > 0.5:
            print("   ".join(line)); line = []
        line.append(f"[{w['i']}|{w['start']:.2f}]{mark}{w['w']}{mark}")
        last = w["end"]
    print("   ".join(line))
    print(f"\nEDL: {len(edl)} pieces, est. length {sum((p['out']-p['in']) if p['type']=='me' else (p['clip_out']-p['clip_in']) for p in edl):.1f}s")


if __name__ == "__main__":
    main()
