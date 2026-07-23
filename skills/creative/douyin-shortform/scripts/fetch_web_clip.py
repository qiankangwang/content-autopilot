#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fetch a REAL video from the web (bilibili / official sites / news pages) and
cut a pipeline-ready clip (vp9 webm) out of it. One command, in the container:

  python fetch_web_clip.py --url https://www.bilibili.com/video/BVxxxx \
         --out clip1.webm --start 12 --seconds 8

Sources that work on this box's network: bilibili, most CN news/video sites,
direct mp4 links. Use OFFICIAL material (trailers, keynotes, product demos,
news footage) and ALWAYS set a source `caption` on the media scene. Keep cuts
short (≤10s) — this is commentary quoting, not re-uploading.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys
import tempfile


def main():
    ap = argparse.ArgumentParser(description="Download + cut a web video into a webm clip.")
    ap.add_argument("--url", required=True, help="video page URL (bilibili etc.) or direct mp4")
    ap.add_argument("--out", required=True, help="output .webm path")
    ap.add_argument("--start", type=float, default=0.0, help="cut start inside the source (s)")
    ap.add_argument("--seconds", type=float, default=8.0, help="clip length (s), keep ≤10")
    ap.add_argument("--max-height", type=int, default=1080)
    args = ap.parse_args()

    tmp = tempfile.mkdtemp(prefix="fetch-")
    try:
        # Grab a bounded section when the extractor supports it; --max-filesize
        # caps runaway downloads either way.
        end = args.start + args.seconds + 2
        ua = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
        cmd = [
            "yt-dlp", "--no-playlist", "--max-filesize", "300M",
            # bilibili 412s headless-looking clients — send real browser headers
            "--user-agent", ua,
            "--add-header", "Referer: https://www.bilibili.com",
            "-f", f"bv*[height<={args.max_height}]+ba/b[height<={args.max_height}]/b",
            "--download-sections", f"*{max(args.start - 1, 0):.0f}-{end:.0f}",
            "-o", os.path.join(tmp, "src.%(ext)s"), args.url,
        ]
        if "bilibili.com" in args.url:
            # bilibili requires JS-minted seat cookies (buvid3/b_nut …) even
            # logged-out — plain HTTP clients get 412 on every request. Warm
            # them up with a real browser visit and hand the jar to yt-dlp.
            try:
                from playwright.sync_api import sync_playwright
                jar = os.path.join(tmp, "cookies.txt")
                with sync_playwright() as p:
                    b = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
                    pg = b.new_page(user_agent=ua)
                    pg.goto("https://www.bilibili.com", wait_until="domcontentloaded",
                            timeout=30000)
                    pg.wait_for_timeout(2500)
                    cookies = pg.context.cookies()
                    b.close()
                with open(jar, "w", encoding="utf-8") as fh:
                    fh.write("# Netscape HTTP Cookie File\n")
                    for c in cookies:
                        fh.write("\t".join([
                            c.get("domain", ".bilibili.com"), "TRUE",
                            c.get("path", "/") or "/",
                            "TRUE" if c.get("secure") else "FALSE",
                            str(int(c.get("expires") or 2147483647)),
                            c.get("name", ""), c.get("value", ""),
                        ]) + "\n")
                cmd[1:1] = ["--cookies", jar]
            except Exception as e:
                sys.stderr.write(f"[fetch] cookie warmup failed (continuing): {e}\n")
        r = subprocess.run(cmd, capture_output=True, text=True)
        srcs = [f for f in glob.glob(os.path.join(tmp, "src.*")) if not f.endswith(".part")]
        if not srcs:
            # some extractors reject --download-sections — retry plain
            sys.stderr.write("[fetch] sectioned download failed, retrying full: "
                             + r.stderr[-300:] + "\n")
            cmd = [c for c in cmd if not c.startswith("*")]
            cmd.remove("--download-sections")
            r = subprocess.run(cmd, capture_output=True, text=True)
            srcs = [f for f in glob.glob(os.path.join(tmp, "src.*")) if not f.endswith(".part")]
        if not srcs:
            sys.stderr.write("[fetch] ERROR: download failed:\n" + r.stderr[-500:] + "\n")
            return 1
        src = srcs[0]
        # cut + normalize to the renderer's codec (headless chromium: vp8/vp9 only)
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        seek = 1.0 if "--download-sections" in " ".join(cmd) and args.start > 0 else args.start
        r = subprocess.run(
            ["ffmpeg", "-y", "-ss", f"{seek:.2f}", "-i", src, "-t", f"{args.seconds:.2f}",
             "-an", "-c:v", "libvpx-vp9", "-deadline", "good", "-cpu-used", "2",
             "-crf", "26", "-b:v", "0", "-vf", "scale='min(1080,iw)':-2", args.out],
            capture_output=True, text=True,
        )
        if r.returncode != 0 or not os.path.isfile(args.out):
            sys.stderr.write("[fetch] ERROR: cut/encode failed:\n" + r.stderr[-400:] + "\n")
            return 1
        print(f"[fetch] DONE -> {os.path.abspath(args.out)}  ({args.seconds:.0f}s from {args.url})")
        print(f"[fetch] NEXT: use in spec.json as {{\"type\":\"media\",\"video\":\"{os.path.abspath(args.out)}\","
              f"\"caption\":\"来源 · <平台/发布方>\"}}  — caption the source, keep cuts short.")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
