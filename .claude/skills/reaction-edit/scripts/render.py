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


def mezzanine(src, dst, preview, denoise=False):
    """Upright, constant 30 fps, 1080x1920 cover-crop, starting at t=0, plus normalised 48 kHz audio.
    denoise (her recording): creator's complaint 27 Nov "too much noise in the background": cut the hum
    below 100 Hz and the hiss above 11 kHz, then FFT + non-local-means noise reduction before loudness."""
    if os.path.exists(dst):
        return
    sh(["ffmpeg", "-y", "-i", src, "-vf",
        "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,setsar=1,fps=30,format=yuv420p",
        "-c:v", "libx264", "-preset", "ultrafast" if preview else "veryfast", "-crf", "16",
        "-af", ("highpass=f=100,lowpass=f=11000,afftdn=nr=30:nf=-45:tn=1,anlmdn=s=7," if denoise else "highpass=f=70,")
        + "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2",
        "-c:a", "pcm_s16le", "-fps_mode", "cfr", dst])


def content_crop_y(path):
    """Top of a 1080x1350 (4:5) window over the part of a 1080x1920 clip that has picture: rows that are
    near-black/flat in every sampled frame (letterbox bars) are skipped, and the window is centred on the rest."""
    import numpy as np
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout.strip() or 10)
    rows = []
    for t in np.linspace(0.1, 0.9, 7) * dur:
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-vf", "scale=108:192,format=gray",
                            "-f", "rawvideo", "-"], capture_output=True)
        if len(r.stdout) == 108 * 192:
            rows.append(np.frombuffer(r.stdout, np.uint8).reshape(192, 108).astype(float))
    if not rows:
        return 0.05
    f = np.stack(rows)
    live = (f.std(axis=2).max(axis=0) > 12) | (f.mean(axis=2).max(axis=0) > 40)   # any frame shows detail/light on this row
    idx = np.where(live)[0]
    if len(idx) == 0:
        return 0.05
    top, bot = idx[0] / 192, (idx[-1] + 1) / 192
    win = 1350 / 1920
    if bot - top <= win:
        y = (top + bot) / 2 - win / 2
    else:
        y = top                                     # tall picture: keep its top (captions/titles live there)
    return float(min(max(0.0, y), 1 - win))


def subject_crop(path, times):
    """Coach's rule (22 Nov): show the clip's speaker from about the belly/waist to the top of the head,
    not the ceiling, fan, lights or on-screen titles above them. Finds the speaker's face on frames taken
    inside the clip parts that are used, and returns a 4:5 crop (w, h, x, y) in the 1080x1920 clip:
    a little headroom above the head, down to roughly the belly. None when no face is found (animals,
    landscapes, films), in which case the picture-area crop is used."""
    try:
        import cv2, numpy as np
    except Exception:
        return None
    casc = cv2.CascadeClassifier(os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml"))
    boxes = []
    for t in times:
        r = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", path, "-frames:v", "1", "-f", "image2pipe",
                            "-vcodec", "png", "-"], capture_output=True).stdout
        img = cv2.imdecode(np.frombuffer(r, np.uint8), cv2.IMREAD_GRAYSCALE) if r else None
        if img is None: continue
        f = casc.detectMultiScale(img, 1.1, 6, minSize=(90, 90))
        if len(f):
            boxes.append(max(f, key=lambda b: b[2] * b[3]))
    if len(boxes) < max(2, len(times) // 3):
        return None
    x, y, w, h = [float(np.median([b[k] for b in boxes])) for k in range(4)]
    ch = min(1350.0, 4.6 * h)                  # ~0.65 face-heights of headroom above the brow, down to the belly
    cw = ch * 4 / 5
    # close-up (the 4:5 box can't reach the belly anyway): keep less headroom, so a title sitting just
    # above the head stays out of the box (Allow that pepper rest, 26 Nov)
    top = y - (0.38 if 4.6 * h > 1350 else 0.65) * h
    cx = x + w / 2 - cw / 2
    cx = min(max(0.0, cx), 1080 - cw); top = min(max(0.0, top), 1920 - ch)
    ev = lambda v: int(v) // 2 * 2
    return ev(cw), ev(ch), ev(cx), ev(top)


def ass_time(t):
    t = max(0, t); h = int(t // 3600); m = int(t % 3600 // 60); s = t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def text_width(text, size, font_file="/usr/share/fonts/opentype/inter/Inter-Black.otf"):
    try:
        from PIL import ImageFont
        return 1.22 * ImageFont.truetype(font_file, size).getlength(text) + 2 * len(text) + 20   # libass scale + spacing + outline
    except Exception:
        return 0.62 * size * len(text)


def captions(pieces, words, y, font, size, path, x=540, fit=None):
    """fit=(t_end, lo, hi): captions starting before t_end (the hook, while the frozen clip box is on
    screen) must stay between x=lo and x=hi (beside the box); they slide over and, only if needed,
    shrink (never below 40 px)."""
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
            # during the hook (frozen box beside her) start a new chunk before it gets too wide to fit
            if fit and chunk and w["text"] and w["s"] < fit[0] - 0.01:
                wide = " ".join([c["text"] for c in chunk] + [w["text"]])
                if text_width(wide, 66) > (fit[2] - fit[1]) and w["s"] - chunk[0]["s"] > 0.15:
                    ev.append((chunk[0]["s"], w["s"], " ".join(c["text"] for c in chunk).strip(" ,"))); chunk = []
            if w["text"]: chunk.append(w)
            text = " ".join(c["text"] for c in chunk)
            last = k + 1 == len(run)
            if chunk and (len(chunk) >= 3 or len(text) >= 14 or w["raw"][-1:] in ".!?" or (w["raw"][-1:] == "," and len(chunk) >= 2) or last):
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
            tags = f"\\pos({x},{y})"
            if fit and s < fit[0] - 0.01:
                lo, hi = fit[1], fit[2]
                fs = size
                while fs > 40 and text_width(t, fs) > hi - lo:
                    fs -= 2
                w = text_width(t, fs)
                cx = int(min(max(x, lo + w / 2), hi - w / 2))
                tags = f"\\pos({cx},{y})" + (f"\\fs{fs}" if fs != size else "")
            f.write(f"Dialogue: 0,{ass_time(s)},{ass_time(e)},Cap,,0,0,0,,{{{tags}}}{t}\n")
    return len(ev)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("workdir"); ap.add_argument("out")
    ap.add_argument("--caption-y", type=int, default=None, help="baseline of the caption in px (default: just above the head)")
    ap.add_argument("--font", default="Inter Black"); ap.add_argument("--size", type=int, default=88)
    ap.add_argument("--fontsdir", default="/usr/share/fonts")
    ap.add_argument("--preview", action="store_true", help="fast low-quality render")
    ap.add_argument("--layout", choices=["full", "pip"], default="pip",
                    help="full: clip fills the frame. pip: she stays on screen (her footage from while the clip played) "
                         "and the clip plays in a box in the top corner away from her face, with the clip's sound")
    ap.add_argument("--cta", default="none",
                    help="follow-button animation top-left (assets/follow_cta.mov). OFF by default: her coach asked to hide it "
                         "until after 60 days of one-on-one coaching (from 22 Nov 2026). Pass the .mov path to switch it on")
    ap.add_argument("--clip-crop", default="subject", choices=["subject", "picture"],
                    help="subject: crop the clip to its speaker, belly to top of head (coach's rule); picture: whole picture area")
    ap.add_argument("--hook-freeze", default="on", choices=["on", "off"],
                    help="while she talks before the first clip part (the hook), show the clip frozen in its box")
    ap.add_argument("--box", default=None, help="pip box as W,H,X,Y in px (default: 600x750 in the top-right corner)")
    ap.add_argument("--clip-crop-rect", default=None, help="pip: exact crop of the clip as W,H,X,Y in its 1080x1920 frame (e.g. to cut letterbox bars)")
    ap.add_argument("--clip-crop-y", type=float, default=None, help="pip: top of the clip's 4:5 crop, as a fraction of its height (default: centred on the clip's picture, skipping black bars)")
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
    # creator's rule (26 Nov): big clip box top-right. In pip her whole picture moves down (top filled with a
    # blurred stretch of the wall) so her eyes sit just below the box; the box only overlaps her hair.
    shift = 0
    if a.layout == "pip" and edl.get("clip") and face:
        eyes = face.get("y", 900) + 0.42 * face.get("h", 450)
        shift = int(min(420, max(0, 80 + 750 + 140 - eyes))) // 2 * 2
        if shift: print(f"her picture moved down {shift}px so the clip box clears her eyes")
    y = a.caption_y or max(260, (face.get("head_top") or 600) - 30 + shift)
    ass = os.path.join(W, "captions.ass")
    # centre the caption over her head (she isn't always in the middle of the frame)
    x = int(min(780, max(300, face.get("x", 270) + face.get("w", 540) / 2))) if face else 540
    # filter graph
    nc = sum(p["type"] == "clip" for p in pieces)
    pip = a.layout == "pip" and has_clip
    use_cta = bool(a.cta) and a.cta != "none" and os.path.exists(a.cta)
    if pip:
        # her footage under each clip piece = the moment of her recording where that clip part played
        # RULE: while the clip plays she is only watching. Her footage under the box must come from the
        # moment that exact clip part was playing in her recording, and must never contain her speaking
        # (that shows her mouthing words with no sound, then saying them again).
        runs = an.get("clip_runs") or []
        talk = [(p["in"], p["out"]) for p in pieces if p["type"] == "me"]
        # her words outside the clip runs (inside a run, the mic is hearing the clip speaker, not her)
        talk += [(w["start"], w["end"]) for w in an.get("words", [])
                 if not any(r["me_start"] - 0.15 <= (w["start"] + w["end"]) / 2 <= r["me_end"] + 0.15 for r in runs)]
        bad = []
        for p in pieces:
            if p["type"] != "clip": continue
            mid = (p["clip_in"] + p["clip_out"]) / 2
            inside = [r for r in runs if r.get("replayed_from", r["clip_start"]) - 0.05 <= mid <= r["clip_end"] + 0.05]
            r = inside[0] if inside else min(runs, key=lambda r: abs(r["clip_start"] - p["clip_in"]))
            # her phone may have played the clip faster/slower: map clip time -> rec time linearly over the run
            c0 = r.get("replayed_from", r["clip_start"])
            m0, m1 = r["me_start"] + 0.15, r["me_end"] - 0.5        # keep clear of her mouth moving into/out of a line
            speed = max(0.5, (r["clip_end"] - c0) / max(0.5, r["me_end"] - r["me_start"]))
            b0 = max(m0, min(m1 - 0.5, m0 + (p["clip_in"] - c0) / speed))
            b1 = min(m1, max(b0 + 0.5, m0 + (p["clip_out"] - c0) / speed))
            p["bg_in"], p["bg_out"] = q(b0), q(b1)          # stretched/squeezed to the clip piece's length
            hit = [t for t in talk if t[0] < b1 - 0.02 and t[1] > b0 + 0.02]
            if hit:
                bad.append(f"clip {p['clip_in']:.2f}-{p['clip_out']:.2f}: her footage {b0:.2f}-{b1:.2f} has her talking at {hit[0][0]:.2f}-{hit[0][1]:.2f}")
        if bad:
            raise SystemExit("pip layout refused, she would be seen speaking silently under the clip:\n  " + "\n  ".join(bad)
                             + "\nFix clip_runs (me_start/me_end) so they cover only the time the clip was playing.")
        if a.box:
            bw, bh, bx, by = map(int, a.box.split(","))
        else:
            # creator's rule (26 Nov): the clip box is BIG, about a third of the screen, always in the TOP-RIGHT
            # corner; it may overlap her hair/forehead while she watches. 600x750 (4:5) just under TikTok's top tabs.
            bw, bh, by = 600, 750, 80
            bx = 1080 - bw - 24
        crop = None
        if a.clip_crop == "subject" and a.clip_crop_y is None:
            ts = []
            for p in pieces:
                if p["type"] == "clip":
                    ts += [p["clip_in"] + (p["clip_out"] - p["clip_in"]) * f for f in (0.15, 0.5, 0.85)]
            crop = subject_crop(cl_m, ts[:12])
        if a.clip_crop_rect:
            crop = tuple(int(v) for v in a.clip_crop_rect.split(","))
        if crop:
            cw, ch, cx, cy = crop
            box_crop = f"crop={cw}:{ch}:{cx}:{cy}"
            print(f"pip box {bw}x{bh} at {bx},{by}, clip cropped to the speaker: {cw}x{ch} at {cx},{cy}")
        else:
            if a.clip_crop_y is None:
                a.clip_crop_y = content_crop_y(cl_m)
            box_crop = f"crop=1080:1350:0:{int(a.clip_crop_y * 1920)}"
            print(f"pip box {bw}x{bh} at {bx},{by}, no speaker found: clip crop from {a.clip_crop_y:.2f} of its height")
    # RULE (coach, 22 Nov): when she opens with her own words (the hook, before the first clip part),
    # the clip she is reacting to sits FROZEN in its box on the frame it will start from; it plays only
    # once she stops talking.
    hook = []
    if pip and a.hook_freeze != "off":
        for k, p in enumerate(pieces):
            if p["type"] == "clip": break
            hook.append(k)
    first_clip = next((p for p in pieces if p["type"] == "clip"), None)
    hook_end = sum(pieces[k]["_dur"] for k in hook)
    still = None
    if hook and first_clip:
        still = os.path.join(W, "hook_still.png")
        sh(["ffmpeg", "-y", "-ss", f"{first_clip['clip_in'] + 0.04:.3f}", "-i", cl_m, "-frames:v", "1", "-vf",
            f"{box_crop},scale={bw}:{bh},setsar=1", still])
        print(f"hook: clip frozen in its box for the first {hook_end:.1f}s while she talks")
    n_caps = captions(pieces, an["words"], y, a.font, a.size, ass, x, fit=((hook_end, 40, bx - 24) if bx + bw / 2 > 540 else (hook_end, bx + bw + 24, 1040)) if still else None)
    nma = sum(p["type"] == "me" for p in pieces)          # her audio pieces
    nm = nma + (nc if pip else 0)                          # her video pieces (+ backgrounds under pip clips)
    mv0 = "[0:v]"
    if shift:
        g0 = [f"[0:v]split=2[sha][shb]", f"[sha]crop=1080:{1920 - shift}:0:0,pad=1080:1920:0:{shift}[shc]",
              f"[shb]crop=1080:240:0:0,scale=1080:{shift},boxblur=20:2[shd]", "[shc][shd]overlay=0:0[mshift]"]
        mv0 = "[mshift]"
    else:
        g0 = []
    g = g0 + [f"{mv0}split={nm}" + "".join(f"[mv{i}]" for i in range(nm)) if nm > 1 else f"{mv0}null[mv0]",
         f"[0:a]asplit={nma}" + "".join(f"[ma{i}]" for i in range(nma)) if nma > 1 else "[0:a]anull[ma0]",
         f"[1:v]split={nc}" + "".join(f"[cv{i}]" for i in range(nc)) if nc > 1 else "[1:v]null[cv0]",
         f"[1:a]asplit={nc}" + "".join(f"[ca{i}]" for i in range(nc)) if nc > 1 else "[1:a]anull[ca0]"]
    if nc == 0: g = g[:2]
    still_in = (2 if has_clip else 1) if still else None
    if still and len(hook) > 1:
        g.append(f"[{still_in}:v]split={len(hook)}" + "".join(f"[st{i}]" for i in range(len(hook))))
    elif still:
        g.append(f"[{still_in}:v]null[st0]")
    cat, im, ic, ia = "", 0, 0, 0
    for k, p in enumerate(pieces):
        if p["type"] == "me":
            s, e, v, au = p["in"], p["out"], f"mv{im}", f"ma{ia}"; im += 1; ia += 1
        else:
            s, e, v, au = p["clip_in"], p["clip_out"], f"cv{ic}", f"ca{ic}"; ic += 1
        d = e - s
        if p["type"] == "clip" and pip:
            bg = f"mv{im}"; im += 1
            b0, b1 = p["bg_in"], p["bg_out"]
            g.append(f"[{bg}]trim=start={b0}:end={b1},setpts=(PTS-STARTPTS)*{d / (b1 - b0):.5f},fps=30[bg{k}]")
            g.append(f"[{v}]trim=start={s}:end={e},setpts=PTS-STARTPTS,{box_crop},"
                     f"scale={bw}:{bh},setsar=1[bx{k}]")
            g.append(f"[bg{k}][bx{k}]overlay={bx}:{by}:shortest=1,trim=duration={d:.4f},setpts=PTS-STARTPTS[v{k}]")
        elif still and k in hook:
            g.append(f"[{v}]trim=start={s}:end={e},setpts=PTS-STARTPTS[hb{k}]")
            g.append(f"[hb{k}][st{hook.index(k)}]overlay={bx}:{by}:shortest=1,trim=duration={d:.4f},setpts=PTS-STARTPTS[v{k}]")
        else:
            g.append(f"[{v}]trim=start={s}:end={e},setpts=PTS-STARTPTS[v{k}]")
        g.append(f"[{au}]atrim=start={s}:end={e},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:d=0.008,afade=t=out:st={max(0, d - 0.008):.4f}:d=0.008[a{k}]")
        cat += f"[v{k}][a{k}]"
    g.append(f"{cat}concat=n={len(pieces)}:v=1:a=1[vc][ac]")
    if use_cta:
        cta_in = (2 if has_clip else 1) + (1 if still else 0)
        g.append(f"[vc]subtitles={ass}:fontsdir={a.fontsdir}[vs]")
        g.append(f"[{cta_in}:v]format=argb[cta]")
        g.append("[vs][cta]overlay=x=30:y=200:shortest=0:eof_action=pass:format=auto,format=yuv420p[vout]")
    else:
        g.append(f"[vc]subtitles={ass}:fontsdir={a.fontsdir}[vout]")
    g.append("[ac]alimiter=limit=0.95[aout]")
    cta_args = ["-stream_loop", "-1", "-i", a.cta] if use_cta else []
    still_args = ["-loop", "1", "-framerate", str(FPS), "-i", still] if still else []
    sh(["ffmpeg", "-y", "-i", me_m] + (["-i", cl_m] if has_clip else []) + still_args + cta_args + ["-t", f"{sum(p['_dur'] for p in pieces):.3f}", "-filter_complex", ";".join(g), "-map", "[vout]", "-map", "[aout]",
        "-c:v", "libx264", "-preset", "ultrafast" if a.preview else "medium", "-crf", "28" if a.preview else "19",
        "-profile:v", "high", "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", a.out])
    tot = sum(p["_dur"] for p in pieces)
    print(f"rendered {a.out}: {len(pieces)} pieces, {tot:.1f}s, {n_caps} caption chunks, caption baseline y={y}")


if __name__ == "__main__":
    main()
