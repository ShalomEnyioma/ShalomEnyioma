#!/usr/bin/env python3
"""Synthesise the template's sound effects from scratch (no samples, no licences).

Writes whoosh, pop, click, riser, hit and ding as 44.1 kHz mono WAVs.
Usage: python3 make_sfx.py [out_dir]   (default: studio/public/sfx)
"""
import math
import random
import struct
import sys
import wave
from pathlib import Path

SR = 44100
random.seed(7)


def write(path: Path, samples):
    peak = max(1e-9, max(abs(s) for s in samples))
    with wave.open(str(path), "w") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(s / peak * 0.9 * 32767)) for s in samples))


def env(i, n, attack=0.01, release=0.5):
    t = i / n
    a = min(1.0, t / attack) if attack else 1.0
    r = max(0.0, 1 - max(0.0, t - (1 - release)) / release) if release else 1.0
    return a * r


def noise_filtered(n, cutoff_fn):
    """One-pole low-pass on white noise with a time-varying cutoff."""
    out, y = [], 0.0
    for i in range(n):
        fc = cutoff_fn(i / n)
        a = 1 - math.exp(-2 * math.pi * fc / SR)
        y += a * (random.uniform(-1, 1) - y)
        out.append(y)
    return out


def whoosh():
    n = int(SR * 0.45)
    s = noise_filtered(n, lambda t: 300 + 5000 * math.sin(math.pi * t))
    return [v * math.sin(math.pi * i / n) ** 2 for i, v in enumerate(s)]


def riser():
    n = int(SR * 0.9)
    s = noise_filtered(n, lambda t: 200 + 7000 * t ** 2)
    tone = [math.sin(2 * math.pi * (180 + 600 * (i / n) ** 2) * i / SR) * 0.3 for i in range(n)]
    return [(v + tone[i]) * (i / n) ** 1.5 for i, v in enumerate(s)]


def pop():
    n = int(SR * 0.12)
    return [math.sin(2 * math.pi * (900 - 600 * i / n) * i / SR) * math.exp(-i / (SR * 0.025)) for i in range(n)]


def click():
    n = int(SR * 0.05)
    return [(random.uniform(-1, 1) * 0.5 + math.sin(2 * math.pi * 3200 * i / SR)) * math.exp(-i / (SR * 0.004)) for i in range(n)]


def hit():
    n = int(SR * 0.6)
    return [
        (math.sin(2 * math.pi * (110 * math.exp(-i / (SR * 0.15)) + 45) * i / SR)
         + random.uniform(-1, 1) * 0.3 * math.exp(-i / (SR * 0.01)))
        * math.exp(-i / (SR * 0.18))
        for i in range(n)
    ]


def ding():
    n = int(SR * 0.8)
    return [
        (math.sin(2 * math.pi * 1318.5 * i / SR) + 0.5 * math.sin(2 * math.pi * 2637 * i / SR))
        * math.exp(-i / (SR * 0.22)) * env(i, n, 0.005, 0.0)
        for i in range(n)
    ]


def main():
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parents[4] / "studio/public/sfx")
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in [("whoosh", whoosh), ("riser", riser), ("pop", pop), ("click", click), ("hit", hit), ("ding", ding)]:
        write(out / f"{name}.wav", fn())
        print("wrote", out / f"{name}.wav")


if __name__ == "__main__":
    main()
