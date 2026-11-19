#!/usr/bin/env python3
"""Render a reaction video from <workdir>/edl.json.

  python3 render.py <workdir> <out.mp4> [--caption-y PX] [--font "Inter Black"] [--size 80] [--preview]

* 1080x1920, 30 fps, H.264 + AAC.
* Creator pieces: the recording, cut to the kept words (pauses removed).
* Clip pieces: the ORIGINAL clip, video and audio, filling the whole frame.
* Captions: creator speech only, 1-3 words at a time, centred just above the head.
* Both audio sources are loudness-normalised to -14 LUFS so levels match; every
  cut gets an 8 ms fade so there are no clicks.
"""
import argparse, json, os, subprocess

FPS = 30


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stderr[-3000:])


def q(t):  # snap to the frame grid so audio and video cut at the same instant
    return round(round(t * FPS) / FPS, 4)


def mezzanine(src, dst, preview):
    """Upright, constant 30 fps, 1080x1920 cover-crop, starting at t=0, plus normalised 48 kHz audio."""
    if os.path.exists(dst):
        return
    sh(["ffmpeg", "-y", "-i", src, "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast" if preview else "veryfast", "-crf", "16",
        "-af", "highpass=f=70,loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2",
        "-c:a", "pcm_s16le", "-fps_mode", "cfr", dst])


def ass_time(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def captions(pieces, words, y, font, size, path, x=540):
    by_id = {w["i"]: w for w in words}
    ev, t_out = [], 0.0
    # Words of consecutive creator pieces flow together (a jump cut inside a sentence
    # must not leave a lone word on screen); a clip piece ends the run.
    runs, cur = [], []
    for p in pieces:
        if p["type"] == "clip":
            if cur: runs.append(cur); cur = []
            t_out += p["_dur"]; continue
        ws = p["words"] if "words" in p else [by_id[i] for i in range(p["first"], p["last"] + 1) if i in by_id]
        for w in ws:
            cur.append({"text": w.get("caption", w["w"]), "raw": w["w"],
                        "s": t_out + max(0, w["start"] - p["in"]), "e": t_out + min(p["_dur"], w["end"] - p["in"]),
                        "piece_end": t_out + p["_dur"]})
        t_out += p["_dur"]
    if cur: runs.append(cur)
    for run in runs:
        chunk = []
        for k, w in enumerate(run):
            if w["text"]: chunk.append(w)
            text = " ".join(c["text"] for c in chunk)
            last = k + 1 == len(run)
            if chunk and (len(chunk) >= 3 or len(text) >= 14 or w["raw"][-1:] in ",.!?" or last):
                e = run[k + 1]["s"] if not last else w["piece_end"]
                ev.append((chunk[0]["s"], e, text.strip(" ,"))); chunk = []
    # no gaps/overlaps between consecutive caption events inside one piece
    for k in range(len(ev) - 1):
        if 0 < ev[k + 1][0] - ev[k][1] < 0.25:
            ev[k] = (ev[k][0], ev[k + 1][0], ev[k][2])
        if ev[k][1] > ev[k + 1][0]:
            ev[k] = (ev[k][0], ev[k + 1][0], ev[k][2])
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Cap,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00000000,&H64000000,0,0,0,0,100,100,2,0,1,8,2,2,60,60,0,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    with open(path, "w") as f:
        f.write(head)
        for s, e, t in ev:
            if e - s < 0.05: continue
            f.write(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,{{\\pos({x},{y})}}{t}\n")
    return len(ev)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir"); ap.add_argument("out")
    ap.add_argument("--caption-y", type=int, default=None, help="baseline of the caption in px (default: just above the head)")
    ap.add_argument("--font", default="Inter Black"); ap.add_argument("--size", type=int, default=88)
    ap.add_argument("--fontsdir", default="/usr/share/fonts")
    ap.add_argument("--preview", action="store_true", help="fast low-quality render")
    a = ap.parse_args()
    W = a.workdir
    edl = json.load(open(os.path.join(W, "edl.json")))
    an = json.load(open(os.path.join(W, "analysis.json")))
    me_m, cl_m = os.path.join(W, "me_mezz.mkv"), os.path.join(W, "clip_mezz.mkv")
    mezzanine(edl["reaction"], me_m, a.preview)
    has_clip = bool(edl.get("clip"))           # captions-only videos have no clip
    if has_clip:
        mezzanine(edl["clip"], cl_m, a.preview)
    pieces = edl["pieces"]
    for p in pieces:
        if p["type"] == "me":
            p["in"], p["out"] = q(p["in"]), q(p["out"]); p["_dur"] = round(p["out"] - p["in"], 4)
        else:
            p["clip_in"], p["clip_out"] = q(p["clip_in"]), q(p["clip_out"]); p["_dur"] = round(p["clip_out"] - p["clip_in"], 4)
    pieces = [p for p in pieces if p["_dur"] >= 2 / FPS]
    face = edl.get("face") or {}
    y = a.caption_y or max(260, (face.get("head_top") or 600) - 30)
    ass = os.path.join(W, "captions.ass")
    # centre the caption over her head (she isn't always in the middle of the frame)
    x = int(min(780, max(300, face.get("x", 270) + face.get("w", 540) / 2))) if face else 540
    n_caps = captions(pieces, an["words"], y, a.font, a.size, ass, x)
    # filter graph
    nm = sum(p["type"] == "me" for p in pieces); nc = len(pieces) - nm
    g = [f"[0:v]split={nm}" + "".join(f"[mv{i}]" for i in range(nm)) if nm > 1 else "[0:v]null[mv0]",
         f"[0:a]asplit={nm}" + "".join(f"[ma{i}]" for i in range(nm)) if nm > 1 else "[0:a]anull[ma0]",
         f"[1:v]split={nc}" + "".join(f"[cv{i}]" for i in range(nc)) if nc > 1 else "[1:v]null[cv0]",
         f"[1:a]asplit={nc}" + "".join(f"[ca{i}]" for i in range(nc)) if nc > 1 else "[1:a]anull[ca0]"]
    if nc == 0: g = g[:2]
    cat, im, ic = "", 0, 0
    for k, p in enumerate(pieces):
        if p["type"] == "me":
            s, e, v, au = p["in"], p["out"], f"mv{im}", f"ma{im}"; im += 1
        else:
            s, e, v, au = p["clip_in"], p["clip_out"], f"cv{ic}", f"ca{ic}"; ic += 1
        d = e - s
        g.append(f"[{v}]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{k}]")
        g.append(f"[{au}]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:d=0.008,afade=t=out:st={max(0, d - 0.008):.4f}:d=0.008[a{k}]")
        cat += f"[v{k}][a{k}]"
    g.append(f"{cat}concat=n={len(pieces)}:v=1:a=1[vc][ac]")
    g.append(f"[vc]subtitles={ass}:fontsdir={a.fontsdir}[vout]")
    g.append("[ac]alimiter=limit=0.95[aout]")
    sh(["ffmpeg", "-y", "-i", me_m] + (["-i", cl_m] if has_clip else []) + ["-filter_complex", ";".join(g), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "ultrafast" if a.preview else "medium", "-crf", "28" if a.preview else "19",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", a.out])
    tot = sum(p["_dur"] for p in pieces)
    print(f"rendered {a.out}: {len(pieces)} pieces, {tot:.1f}s, {n_caps} caption chunks, caption baseline y={y}")


if __name__ == "__main__":
    main()
