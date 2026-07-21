#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI motion b-roll for media scenes — CogVideoX text-to-video (free tier).

Where a scene has no real footage and a STATIC AI image would read as a
slideshow card, generate a short cinematic vertical clip instead. Style is
locked to a consistent "documentary b-roll" look (slow camera moves, muted
grade, shallow depth) so multiple clips in one video feel like one shoot —
NOT the plastic AI-image Ken Burns the user rejected in June.

Rules enforced by the render engine (validate_spec):
  - AI motion clips: at most 4 per video (2-3 recommended)
  - static AI images: still at most 1 per video
Every output gets an `.ai` sidecar marker so the engine can count them.

Creds: reuses ~/.config/zhipu_vision.json (bigmodel.cn key, same as the
vision gate). Model: cogvideox-flash (free) | cogview compatible paid tiers.

Usage:
  python gen_scene_video.py --desc "凌晨的数据中心机房,服务器指示灯闪烁,镜头缓慢推进" \
      --out /path/scene3.mp4 [--model cogvideox-flash]
"""
import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

CREDS_PATHS = [os.path.expanduser("~/.config/zhipu_vision.json"),
               "/root/.config/zhipu_vision.json"]
BASE = "https://open.bigmodel.cn/api/paas/v4"

# one consistent look across every clip in the account — documentary b-roll,
# not showy AI spectacle; no text (models garble CJK), no people's faces
# (uncanny hands/faces are the #1 AI tell)
STYLE_PROMPT = (
    "电影感纪实空镜,竖屏构图,{desc}。缓慢的镜头运动(推进或平移),低饱和冷色调,"
    "浅景深,自然光影,真实质感。画面中无任何文字无字幕无水印,不出现人脸特写。"
)


def _strip_watermark(path, frac=0.058):
    """CogVideoX burns an「AI生成」badge into the bottom-right corner (platform
    compliance on the free tier) — same as CogView images. Crop the bottom
    strip off (we declare AI content at publish time anyway); fails soft."""
    tmp = path + ".crop.mp4"
    r = subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", path,
         "-vf", f"crop=iw:trunc((ih*(1-{frac}))/2)*2:0:0",
         "-c:v", "libx264", "-preset", "fast", "-crf", "19", "-an", tmp],
        capture_output=True, text=True)
    if r.returncode == 0 and os.path.isfile(tmp) and os.path.getsize(tmp) > 10240:
        os.replace(tmp, path)
    else:
        sys.stderr.write(f"[gen_scene_video] watermark crop skipped: {r.stderr[-200:]}\n")
        try:
            os.remove(tmp)
        except OSError:
            pass


def _load_creds():
    for p in CREDS_PATHS:
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as fh:
                    return json.load(fh)
            except (OSError, ValueError):
                continue
    return None


def _api(path, key, body=None, timeout=60):
    req = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode("utf-8") if body else None,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desc", required=True, help="画面内容一句话(中文),不要包含风格词")
    ap.add_argument("--out", required=True, help="output .mp4 path")
    ap.add_argument("--model", default="cogvideox-flash",
                    help="cogvideox-flash(免费) | 更高档模型按 bigmodel 文档")
    ap.add_argument("--size", default="768x1344", help="vertical; auto-dropped if rejected")
    ap.add_argument("--poll-timeout", type=int, default=480)
    args = ap.parse_args()

    creds = _load_creds()
    if not creds:
        sys.stderr.write("no zhipu creds (~/.config/zhipu_vision.json)\n")
        return 2
    key = creds["api_key"]

    body = {"model": args.model,
            "prompt": STYLE_PROMPT.format(desc=args.desc.strip()),
            "with_audio": False}
    if args.size:
        body["size"] = args.size
    task = None
    for attempt in range(3):
        try:
            task = _api("/videos/generations", key, body)
            break
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:300]
            if e.code == 400 and "size" in msg and "size" in body:
                body.pop("size")        # older/free tiers reject custom sizes
                continue
            sys.stderr.write(f"submit failed (HTTP {e.code}): {msg}\n")
            if attempt == 2:
                return 1
            time.sleep(6 * (attempt + 1))
        except Exception as e:
            sys.stderr.write(f"submit failed: {e}\n")
            if attempt == 2:
                return 1
            time.sleep(6 * (attempt + 1))
    tid = (task or {}).get("id")
    if not tid:
        sys.stderr.write(f"no task id in response: {task}\n")
        return 1

    print(f"[gen_scene_video] task {tid} submitted, polling...")
    t0 = time.time()
    url = None
    while time.time() - t0 < args.poll_timeout:
        time.sleep(6)
        try:
            r = _api(f"/async-result/{tid}", key)
        except Exception as e:
            sys.stderr.write(f"poll error (retrying): {e}\n")
            continue
        st = r.get("task_status")
        if st == "SUCCESS":
            vids = r.get("video_result") or []
            url = vids[0].get("url") if vids else None
            break
        if st == "FAIL":
            sys.stderr.write(f"generation failed: {r}\n")
            return 1
    if not url:
        sys.stderr.write(f"timed out after {args.poll_timeout}s (task {tid})\n")
        return 1

    with urllib.request.urlopen(url, timeout=180) as r, open(args.out, "wb") as f:
        f.write(r.read())
    _strip_watermark(args.out)
    with open(args.out + ".ai", "w") as f:
        f.write("ai-generated video\n")
    sz = os.path.getsize(args.out)
    print(f"[gen_scene_video] wrote {args.out} ({sz//1024}KB, model={args.model}, {time.time()-t0:.0f}s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
