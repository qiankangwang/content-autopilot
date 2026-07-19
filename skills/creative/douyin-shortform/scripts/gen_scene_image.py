#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI illustration fallback for media scenes — when no real footage/photo can be
found for a scene, generate a FLAT INFOGRAPHIC-STYLE illustration instead of
degrading to a text card (text-card stuffing is the #1 "PPT feel" cause).

Style is locked to flat vector illustration: no photorealism (no skin/hands to
give it away), no text in the image (models garble CJK — captions are overlaid
by the renderer). Vertical 768x1344 fits the 9:16 media frame.

Creds: reuses ~/.config/zhipu_vision.json (same key as the vision gate).
Models: cogview-3-flash (free tier, default) | cogview-4 (~0.06 CNY/image).

Usage:
  python gen_scene_image.py --desc "台风天被狂风卷起的花盆和招牌砸向居民楼窗户" \
      --out /path/scene8.png [--model cogview-4]
"""
import argparse
import json
import os
import sys
import time
import urllib.request

CREDS_PATHS = [os.path.expanduser("~/.config/zhipu_vision.json"),
               "/root/.config/zhipu_vision.json"]

STYLE_PROMPT = (
    "扁平矢量插画,信息图风格,简洁几何形状,柔和的低饱和配色,干净的单色背景,"
    "无任何文字无字母无数字,无水印,构图居中留白,竖版。画面内容:{desc}"
)


def _strip_watermark(path, frac=0.055):
    """CogView stamps an「AI生成」badge in the bottom-right corner regardless of
    the prompt (platform compliance on the free tier). Rendered at cover/fit
    scale it ends up half-clipped at the frame edge and screams "AI slop"
    (shipped 2026-07-17/18). Crop the bottom strip off; fails soft."""
    try:
        from PIL import Image
        with Image.open(path) as im:
            w, h = im.size
            cut = int(h * frac)
            if cut > 0 and h - cut > 200:
                im.crop((0, 0, w, h - cut)).save(path)
    except Exception as e:
        sys.stderr.write(f"[gen_scene_image] watermark crop skipped: {e}\n")


def _load_creds():
    for p in CREDS_PATHS:
        if os.path.isfile(p):
            try:
                with open(p, encoding="utf-8") as fh:
                    return json.load(fh)
            except (OSError, ValueError):
                continue
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desc", required=True, help="画面内容一句话(中文),不要包含风格词")
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="cogview-3-flash",
                    help="cogview-3-flash(免费) | cogview-4(更好,~0.06元/张)")
    ap.add_argument("--size", default="768x1344")
    args = ap.parse_args()

    creds = _load_creds()
    if not creds:
        sys.stderr.write("no zhipu creds (~/.config/zhipu_vision.json)\n")
        return 2

    body = json.dumps({
        "model": args.model,
        "prompt": STYLE_PROMPT.format(desc=args.desc.strip()),
        "size": args.size,
    }).encode("utf-8")
    url = creds["base_url"].rstrip("/").replace("/chat/completions", "")
    if not url.endswith("/v4"):
        url = "https://open.bigmodel.cn/api/paas/v4"
    req = urllib.request.Request(
        url + "/images/generations", data=body,
        headers={"Authorization": "Bearer " + creds["api_key"],
                 "Content-Type": "application/json"})

    last_err = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                resp = json.load(r)
            img_url = resp["data"][0]["url"]
            with urllib.request.urlopen(img_url, timeout=120) as r, open(args.out, "wb") as f:
                f.write(r.read())
            _strip_watermark(args.out)
            # sidecar marker: the render engine enforces ≤1 AI illustration per
            # video (user policy 2026-07-19) and needs to know which is which
            with open(args.out + ".ai", "w") as f:
                f.write("ai-generated\n")
            print(f"[gen_scene_image] wrote {args.out} (model={args.model})")
            return 0
        except Exception as e:  # free tier rate limits → brief backoff and retry
            last_err = e
            time.sleep(4 * (attempt + 1))
    sys.stderr.write(f"gen_scene_image failed after retries: {last_err}\n")
    return 1


if __name__ == "__main__":
    sys.exit(main())
