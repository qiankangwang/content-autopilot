#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record a real webpage as a short B-roll clip (webm) for `media` video scenes.

Runs INSIDE the container (Playwright chromium). Captures a slow scroll of the
page in a phone-shaped viewport — genuine footage of the thing being discussed,
one command:

  python record_page_clip.py --url https://github.com/x/y --out clip1.webm --seconds 6

Options: --no-scroll (static hold), --wait N (settle seconds before recording),
--width/--height (viewport; default 900x1600 portrait, good for 9:16 media).
The clip is silent; the video pipeline plays it muted under the narration.
"""
import argparse
import glob
import os
import shutil
import sys
import tempfile
import time


def main():
    ap = argparse.ArgumentParser(description="Record a scrolling page capture as a webm clip.")
    ap.add_argument("--url", required=True)
    ap.add_argument("--out", required=True, help="output .webm path")
    ap.add_argument("--seconds", type=float, default=6.0)
    ap.add_argument("--wait", type=float, default=3.0, help="settle time after load before recording starts counting")
    ap.add_argument("--no-scroll", action="store_true", help="hold still instead of scrolling")
    ap.add_argument("--start-y", type=float, default=0.0,
                    help="start recording scrolled this many px down (skip the site header/nav; "
                         "600-900 usually lands on the article body)")
    ap.add_argument("--width", type=int, default=900)
    ap.add_argument("--height", type=int, default=1600)
    args = ap.parse_args()

    import subprocess
    from playwright.sync_api import sync_playwright
    fps = 30
    rec_dir = tempfile.mkdtemp(prefix="clip-")
    try:
        frames = int(args.seconds * fps)
        with sync_playwright() as p:
            browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
            page = browser.new_page(
                viewport={"width": args.width, "height": args.height},
                user_agent=("Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/125.0 Mobile Safari/537.36"),
                locale="zh-CN",
            )
            try:
                page.goto(args.url, wait_until="domcontentloaded", timeout=45000)
            except Exception as e:
                sys.stderr.write(f"[clip] goto warning: {e}\n")
            page.wait_for_timeout(int(args.wait * 1000))
            # Refuse useless footage: a login-walled or blank page recorded fine
            # mechanically but published as seconds of white screen (知乎 wall,
            # 2026-07-13). Fail loudly so the caller picks another source.
            check = page.evaluate(
                "(() => { const t = (document.body && document.body.innerText || '').trim();"
                " return {len: t.length,"
                " wall: /请登录|登录后查看|扫码登录|仅限登录|需要登录/.test(t.slice(0, 4000))}; })()")
            if check["len"] < 300 or (check["wall"] and check["len"] < 1200):
                sys.stderr.write(
                    f"[clip] REFUSING to record: page is blank or login-walled "
                    f"(textLen={check['len']}, loginWall={check['wall']}). "
                    "Pick a different, publicly readable URL (news article / GitHub / "
                    "official site) — do NOT use this clip.\n")
                browser.close()
                return 1
            # Frame-stepped capture — the exact same trick as the main renderer.
            # The old wheel-jump + Playwright screen recorder was CHOPPY (discrete
            # 90px hops + dropped frames); scrolling a fixed 4px per frame and
            # screenshotting each one is glass-smooth by construction, and there
            # is no load lead-in because capture starts after settle.
            max_scroll = page.evaluate(
                "Math.max(0, document.documentElement.scrollHeight - window.innerHeight)")
            base_y = min(args.start_y, max_scroll)
            if base_y:
                # jump past the header BEFORE the first frame — frame 1 is what
                # the vision gate judges, and a nav bar there fails the build
                page.evaluate(f"window.scrollTo(0, {base_y:.1f})")
                # sticky/fixed navs follow the scroll; hide them outright
                page.evaluate(
                    "for (const el of document.querySelectorAll('body *')) {"
                    " const p = getComputedStyle(el).position;"
                    " if (p === 'fixed' || p === 'sticky') el.style.visibility = 'hidden'; }")
            px = 0.0 if args.no_scroll else 4.0   # 4px @30fps = gentle 120px/s glide
            for f in range(frames):
                y = min(base_y + f * px, max_scroll)
                if px:
                    page.evaluate(f"window.scrollTo(0, {y:.1f})")
                page.screenshot(path=os.path.join(rec_dir, "f%05d.jpg" % f),
                                type="jpeg", quality=88)
            browser.close()
        os.makedirs(os.path.dirname(os.path.abspath(args.out)) or ".", exist_ok=True)
        r = subprocess.run(
            ["ffmpeg", "-y", "-framerate", str(fps),
             "-i", os.path.join(rec_dir, "f%05d.jpg"),
             "-an", "-c:v", "libvpx-vp9", "-deadline", "realtime", "-cpu-used", "8",
             "-crf", "32", "-b:v", "0", args.out],
            capture_output=True, text=True,
        )
        if r.returncode != 0 or not os.path.isfile(args.out):
            sys.stderr.write("[clip] encode failed:\n" + r.stderr[-400:] + "\n")
            return 1
        print(f"[clip] DONE -> {os.path.abspath(args.out)}  ({args.seconds:.0f}s, {args.width}x{args.height}, frame-exact {fps}fps)")
        print(f"[clip] NEXT: use in spec.json as {{\"type\":\"media\",\"video\":\"{os.path.abspath(args.out)}\",...}}")
        return 0
    finally:
        shutil.rmtree(rec_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
