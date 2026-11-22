#!/usr/bin/env python3
"""Build the follow-button CTA: a red TikTok-style "Follow" button pops up, a cursor glides to it,
clicks, the button turns to "Following", then everything fades. plays for 2 s once every 10 s, no other words
(TikTok penalises "follow my account" style text, so the CTA only shows the button itself).

  python3 make_cta.py <outdir>
writes   <outdir>/follow_cta.mov        transparent loop (qtrle, alpha) used by render.py --cta
         <outdir>/follow_cta_green.mp4  same on a green screen (for CapCut etc.)
         <outdir>/follow_cta.gif        green-screen GIF preview
"""
import math, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFilter, ImageFont

FPS, SECONDS = 30, 2.0     # the animation itself
CYCLE = 10.0               # it appears once every 10 s (creator's rule, 22 Nov); hidden the rest of the time
W, H = 460, 200            # overlay size in the 1080x1920 frame
SS = 3                     # supersampling for smooth edges
RED, GREY, DARK = (254, 44, 85), (241, 241, 242), (22, 24, 35)
FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"


def ease_out_back(t, s=1.7):
    t -= 1
    return t * t * ((s + 1) * t + s) + 1


def ease_in_out(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0, min(1, t)))


def cursor_shape(size):
    """Classic arrow pointer (white with black outline), tip at (0,0)."""
    s = size / 24.0
    pts = [(0, 0), (0, 17), (4.2, 13.2), (7, 19.5), (9.6, 18.4), (6.9, 12.3), (12.4, 12.3)]
    return [(x * s, y * s) for x, y in pts]


def frame(i, n):
    t = i / n
    img = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
    bw, bh = 300 * SS, 84 * SS
    bx, by = 24 * SS, 40 * SS
    cx, cy = bx + bw / 2, by + bh / 2
    # timeline
    pop = min(1, t / 0.13)
    scale = max(0.06, ease_out_back(pop)) if pop < 1 else 1.0
    click_t = 0.46
    pressed = click_t - 0.02 <= t <= click_t + 0.04
    if pressed:
        scale *= 0.94
    following = t >= click_t
    fade = 1.0 if t < 0.85 else max(0.0, 1 - (t - 0.85) / 0.15)
    # shadow + button
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    sw, sh = bw * scale, bh * scale
    x0, y0 = cx - sw / 2, cy - sh / 2
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([x0, y0 + 6 * SS, x0 + sw, y0 + sh + 6 * SS], radius=sh / 2, fill=(0, 0, 0, 110))
    shadow = shadow.filter(ImageFilter.GaussianBlur(8 * SS))
    layer = Image.alpha_composite(layer, shadow)
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0, y0, x0 + sw, y0 + sh], radius=sh / 2, fill=(GREY if following else RED) + (255,))
    label = "Following" if following else "Follow"
    font = ImageFont.truetype(FONT, int(38 * SS * scale))
    tw, th = d.textbbox((0, 0), label, font=font)[2:]
    d.text((cx - tw / 2, cy - th / 2 - 4 * SS * scale), label, font=font, fill=(DARK if following else (255, 255, 255)) + (255,))
    # click ripple
    if click_t <= t <= click_t + 0.25:
        r = (t - click_t) / 0.25
        rad = (20 + 70 * r) * SS
        tx, ty = cx + 40 * SS, cy + 8 * SS
        d.ellipse([tx - rad, ty - rad, tx + rad, ty + rad], outline=(255, 255, 255, int(220 * (1 - r))), width=int(4 * SS))
    # cursor
    if t >= 0.12:
        k = ease_in_out((t - 0.12) / (click_t - 0.14))
        sx, sy = W * SS * 0.98, H * SS * 1.05
        tx, ty = cx + 40 * SS, cy + 8 * SS
        px, py = sx + (tx - sx) * k, sy + (ty - sy) * k
        if t > click_t + 0.08:                      # drift away a little after the click
            k2 = ease_in_out((t - click_t - 0.08) / 0.3)
            px, py = px + 26 * SS * k2, py + 22 * SS * k2
        cs = 68 * SS * (0.86 if pressed else 1.0)
        pts = [(px + x, py + y) for x, y in cursor_shape(cs)]
        d.polygon(pts, fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=int(3 * SS))
    if fade < 1:
        a = layer.getchannel("A").point(lambda v: int(v * fade))
        layer.putalpha(a)
    img = Image.alpha_composite(img, layer)
    return img.resize((W, H), Image.LANCZOS)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out, exist_ok=True)
    n = int(FPS * SECONDS)
    with tempfile.TemporaryDirectory() as tmp:
        blank = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        for i in range(int(FPS * CYCLE)):
            (frame(i, n) if i < n else blank).save(os.path.join(tmp, f"f{i:03d}.png"))
        seq = os.path.join(tmp, "f%03d.png")
        run = lambda a: subprocess.run(["ffmpeg", "-v", "error", "-y"] + a, check=True)
        run(["-framerate", str(FPS), "-i", seq, "-c:v", "qtrle", "-pix_fmt", "argb", os.path.join(out, "follow_cta.mov")])
        run(["-f", "lavfi", "-i", f"color=c=0x00FF00:s={W}x{H}:r={FPS}", "-framerate", str(FPS), "-i", seq,
             "-filter_complex", "[0][1]overlay=shortest=1,format=yuv420p", "-c:v", "libx264", "-crf", "16",
             os.path.join(out, "follow_cta_green.mp4")])
        run(["-i", os.path.join(out, "follow_cta_green.mp4"), "-vf", "split[a][b];[a]palettegen[p];[b][p]paletteuse",
             "-loop", "0", os.path.join(out, "follow_cta.gif")])
    print("wrote", out)


if __name__ == "__main__":
    main()
