#!/usr/bin/env python3
"""Background-noise reduction for her recording (creator, 27 Nov: "do better without swallowing the voice").
Learns the room noise from the quietest 10% of the recording (her pauses) and removes only that noise
(spectral gating, noisereduce), at 85% strength with smoothing so her voice stays natural.
  python3 denoise.py in.wav out.wav [strength=0.85]"""
import sys, numpy as np, soundfile as sf, noisereduce as nr
x, sr = sf.read(sys.argv[1]); prop=float(sys.argv[3]) if len(sys.argv) > 3 else 0.85
fr = sr // 100; n = len(x) // fr
e = 10*np.log10((x[:n*fr].reshape(n, fr)**2).mean(1) + 1e-12)
thr = np.percentile(e, 10) + 6          # the quietest frames = room noise only
q = e < thr
noise = np.concatenate([x[i*fr:(i+1)*fr] for i in range(n) if q[i]]) if q.sum() > 50 else x[:sr]
y = nr.reduce_noise(y=x, sr=sr, y_noise=noise, stationary=True, prop_decrease=prop, n_std_thresh_stationary=1.5, freq_mask_smooth_hz=300, time_mask_smooth_ms=60)
sf.write(sys.argv[2], y, sr)
print('noise sample %.1fs' % (len(noise)/sr))
