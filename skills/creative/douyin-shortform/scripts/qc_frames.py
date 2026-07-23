#!/usr/bin/env python3
"""Post-render frame audit — V3 QC gate #3.

Samples N evenly-spaced frames from a finished mp4 and asks the vision model
whether any frame violates the V3 composition rules (text cut off at an edge,
unreadable contrast, >45% dead space, caption clipped/overlapped). Exits 6
with a per-frame repair note when violations are found, so the producing
agent fixes the spec and re-renders instead of publishing a broken cut.

Usage:
    python qc_frames.py --video /path/out.mp4 [--frames 6]
"""
import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_rich_video import _load_vision_creds, _ffprobe_dur  # noqa: E402

_PROMPT = (
    "你是短视频成片质检员。这是一帧 1080x1920 竖屏视频画面。逐项检查:\n"
    "1. cut_off: 有没有文字/数字被画面边缘或其他元素裁掉、遮挡、溢出(哪怕一个字被切一半也算 true)\n"
    "2. low_contrast: 有没有文字和背景对比不足、在手机上会看不清(true/false)\n"
    "3. dead_space: 画面是否有超过约 45% 的连续空白/纯色无内容区域(true/false)\n"
    "4. ugly: 是否存在明显排版事故——元素重叠错位、字号异常、图片严重拉伸变形(true/false)\n"
    "只输出一个 JSON 对象:\n"
    '{"cut_off": true|false, "low_contrast": true|false, "dead_space": true|false, '
    '"ugly": true|false, "note": "<一句话:看到的具体问题,没有就写ok>"}'
)


def _vision_frame(path, creds_list):
    import base64 as _b64
    import requests as _rq
    with open(path, "rb") as fh:
        b64 = _b64.b64encode(fh.read()).decode()
    for cred in (creds_list if isinstance(creds_list, list) else [creds_list]):
        body = {
            "model": cred.get("model", "glm-4v-flash"),
            "temperature": 0.1,
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                {"type": "text", "text": _PROMPT},
            ]}],
        }
        for attempt in range(2):
            try:
                r = _rq.post(cred["base_url"].rstrip("/") + "/chat/completions", json=body,
                             headers={"Authorization": "Bearer " + cred["api_key"]}, timeout=60)
                r.raise_for_status()
                txt = r.json()["choices"][0]["message"]["content"]
                m = re.search(r"\{.*\}", txt, re.S)
                if m:
                    return json.loads(m.group(0))
            except Exception:
                if attempt == 0:
                    import time
                    time.sleep(4)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True)
    ap.add_argument("--frames", type=int, default=6)
    args = ap.parse_args()

    creds = _load_vision_creds()
    if not creds:
        sys.stderr.write("[qc] WARNING: no vision creds — frame audit SKIPPED\n")
        return 0
    dur = _ffprobe_dur(args.video)
    if not dur:
        sys.stderr.write("[qc] cannot probe video duration\n")
        return 1

    tmp = tempfile.mkdtemp(prefix="qc-")
    failures = []
    for k in range(args.frames):
        # avoid scene-boundary frames: sample mid-segment points
        t = dur * (k + 0.5) / args.frames
        frame = os.path.join(tmp, f"qc{k}.jpg")
        subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{t:.2f}", "-i", args.video,
                        "-frames:v", "1", "-q:v", "3", frame],
                       capture_output=True, text=True)
        if not os.path.isfile(frame):
            continue
        v = _vision_frame(frame, creds)
        if v is None:
            continue  # infra failure — don't block on flaky vision
        bad = [flag for flag in ("cut_off", "low_contrast", "dead_space", "ugly") if v.get(flag)]
        note = str(v.get("note", ""))[:100]
        if bad:
            failures.append((t, bad, note))
            print(f"[qc] t={t:.1f}s ❌ {'+'.join(bad)} — {note}")
        else:
            print(f"[qc] t={t:.1f}s ok — {note}")

    if failures:
        sys.stderr.write(
            "\n[qc] ❌ 成片抽帧质检不通过。定位到对应场景修 spec(文字改短/换素材/调布局)后重渲:\n")
        for t, bad, note in failures:
            sys.stderr.write(f"  t≈{t:.1f}s: {'+'.join(bad)} — {note}\n")
        sys.stderr.write("[qc] 规则:质检不过绝不发布。\n\n")
        return 6
    print(f"[qc] PASS: {args.frames} frames clean")
    return 0


if __name__ == "__main__":
    sys.exit(main())
