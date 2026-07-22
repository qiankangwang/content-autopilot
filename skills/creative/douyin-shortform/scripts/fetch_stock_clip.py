#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Real stock footage for media scenes — Pexels video search (free license).

The quality ceiling of the pipeline was material: page recordings and
screenshots read cheap, AI clips read plastic. Pexels serves millions of
professionally shot HD/4K clips (city aerials, server rooms, labs, chip fabs,
crowds, weather...) free for commercial use, no attribution required.

Material priority for media scenes is now:
  event footage (fetch_web_clip) > STOCK (this) > AI motion (gen_scene_video,
  ≤4) > AI still (gen_scene_image, ≤1)

Creds: ~/.config/pexels.json  {"api_key": "..."}   (free key from pexels.com/api)

Usage:
  python fetch_stock_clip.py --query "server room night" --out /path/clip2.mp4
      [--index 1]     # take the 2nd-best hit when the 1st doesn't fit
      [--seconds 12]  # trim cap (default 12s; scenes only need 3-6s)

Keywords must be ENGLISH (Pexels indexes English only). Search 2-3 word
concrete nouns ("data center aisle", "city traffic night"), not sentences.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.parse
import urllib.request

CREDS_PATHS = [os.path.expanduser("~/.config/pexels.json"),
               "/root/.config/pexels.json"]
API = "https://api.pexels.com/videos/search"
# Pexels/Cloudflare 403s the default Python-urllib UA; a plain tool UA passes
UA = "hermes-fetch-stock/1.0 (+https://www.pexels.com/api/)"


def _key():
    for p in CREDS_PATHS:
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as fh:
                    return json.load(fh)["api_key"]
            except (OSError, ValueError, KeyError):
                continue
    return None


def _pick_file(video):
    """Best portrait file: tallest H.264 ≤1920 tall (covers 1080x1920 after
    the renderer's cover-fit; 4K wastes bandwidth)."""
    files = [f for f in video.get("video_files", [])
             if (f.get("height") or 0) >= 960 and "mp4" in (f.get("file_type") or "")]
    if not files:
        return None
    files.sort(key=lambda f: (min(f.get("height") or 0, 1920), f.get("width") or 0),
               reverse=True)
    return files[0]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--query", required=True, help="ENGLISH keywords, 2-3 concrete words")
    ap.add_argument("--out", required=True)
    ap.add_argument("--index", type=int, default=0, help="take the Nth candidate (0-based)")
    ap.add_argument("--seconds", type=float, default=12.0, help="trim cap")
    args = ap.parse_args()

    key = _key()
    if not key:
        sys.stderr.write("no pexels creds (~/.config/pexels.json {\"api_key\": ...})\n")
        return 2

    q = urllib.parse.urlencode({"query": args.query, "orientation": "portrait",
                                "size": "medium", "per_page": 12})
    req = urllib.request.Request(API + "?" + q,
                                 headers={"Authorization": key, "User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            data = json.load(r)
    except Exception as e:
        sys.stderr.write(f"pexels search failed: {e}\n")
        return 1
    videos = data.get("videos") or []
    # portrait-shaped, sane duration (3-60s), best-match order preserved
    usable = [v for v in videos
              if (v.get("height") or 0) > (v.get("width") or 1)
              and 3 <= (v.get("duration") or 0) <= 60]
    if not usable:
        sys.stderr.write(f"no usable portrait hits for '{args.query}' "
                         f"({len(videos)} raw) — try broader/different English keywords\n")
        return 3
    if args.index >= len(usable):
        sys.stderr.write(f"index {args.index} out of range ({len(usable)} hits)\n")
        return 3
    v = usable[args.index]
    f = _pick_file(v)
    if not f:
        sys.stderr.write("hit has no usable mp4 file\n")
        return 3

    tmp = args.out + ".dl.mp4"
    try:
        dreq = urllib.request.Request(f["link"], headers={"User-Agent": UA})
        with urllib.request.urlopen(dreq, timeout=300) as r, open(tmp, "wb") as fh:
            while True:
                chunk = r.read(1 << 20)
                if not chunk:
                    break
                fh.write(chunk)
    except Exception as e:
        sys.stderr.write(f"download failed: {e}\n")
        return 1
    # trim + strip audio (scenes are voiced by TTS; stock audio is never used)
    r2 = subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", tmp,
                         "-t", f"{args.seconds:.1f}", "-an", "-c:v", "copy", args.out],
                        capture_output=True, text=True)
    if r2.returncode != 0 or not os.path.isfile(args.out):
        os.replace(tmp, args.out)      # copy-trim can fail on odd keyframes — keep full
    else:
        os.remove(tmp)
    print(f"[fetch_stock_clip] wrote {args.out} "
          f"({os.path.getsize(args.out)//1024}KB, {v.get('duration')}s src, "
          f"{f.get('width')}x{f.get('height')}, pexels id={v.get('id')} by {(v.get('user') or {}).get('name','?')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
