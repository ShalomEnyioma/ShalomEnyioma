#!/usr/bin/env python3
"""Download a Google Drive file shared as "Anyone with the link".

Needs drive.usercontent.google.com in the environment's allowed domains.

  python3 fetch_drive.py "https://drive.google.com/file/d/<ID>/view?usp=sharing" studio/public/footage/take1.mp4
"""
import re
import sys
from pathlib import Path

import requests


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    link, out = sys.argv[1], Path(sys.argv[2])
    m = re.search(r"/d/([\w-]+)|[?&]id=([\w-]+)", link)
    if not m:
        sys.exit("Could not find a file id in that link.")
    fid = m.group(1) or m.group(2)
    url = f"https://drive.usercontent.google.com/download?id={fid}&export=download&confirm=t"
    out.parent.mkdir(parents=True, exist_ok=True)
    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        if "text/html" in r.headers.get("content-type", ""):
            sys.exit("Drive returned a web page, not the file. Is the file shared as 'Anyone with the link'?")
        with open(out, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    print(f"wrote {out} ({out.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
