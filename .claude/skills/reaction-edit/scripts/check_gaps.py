#!/usr/bin/env python3
"""List every stretch quieter than a threshold (default -45 dB) lasting >= 0.12 s in a rendered video.

  python3 check_gaps.py OUT.mp4 [-45]

Creator pieces must show none at -45 dB. (Clip pieces have their own music bed, so they rarely trip it.)
"""
import sys, subprocess, numpy as np
raw = subprocess.run(["ffmpeg","-v","error","-i",sys.argv[1],"-ac","1","-ar","16000","-f","s16le","-"],capture_output=True).stdout
a = np.frombuffer(raw, np.int16).astype(np.float32)/32768
db = 20*np.log10(np.sqrt(np.mean(a[:len(a)//160*160].reshape(-1,160)**2,axis=1))+1e-6)
thr = float(sys.argv[2]) if len(sys.argv)>2 else -45
q = db < thr; out=[]; i=0
while i < len(q):
    if q[i]:
        j=i
        while j<len(q) and q[j]: j+=1
        if (j-i) >= 12: out.append((i/100,(j-i)/100))
        i=j
    else: i+=1
print(f"gaps >= 0.12s below {thr} dB:", ", ".join(f"{t:.2f}s({d:.2f})" for t,d in out) or "none")
