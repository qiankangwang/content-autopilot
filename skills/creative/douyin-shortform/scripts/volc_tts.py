#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""火山引擎 / 豆包 语音合成 (TTS) → mp3. Natural Chinese neural voice for 抖音 narration.

Credentials come from env (do NOT hardcode):
  VOLC_TTS_APPID   - 火山控制台 语音合成应用的 APPID
  VOLC_TTS_TOKEN   - Access Token
  VOLC_TTS_VOICE   - 音色 voice_type (override with --voice; has a sensible default)
  VOLC_TTS_CLUSTER - default "volcano_tts"

Usage:
  python volc_tts.py --text "你好" --out voice.mp3 [--voice BV701_streaming] [--speed 1.0]
  python volc_tts.py --text-file script.txt --out voice.mp3
"""
import argparse, base64, json, os, sys, uuid, urllib.request, urllib.error

API = "https://openspeech.bytedance.com/api/v1/tts"


def synth(text, out, appid, token, voice, cluster, speed):
    body = {
        "app": {"appid": appid, "token": token, "cluster": cluster},
        "user": {"uid": "hermes"},
        "audio": {"voice_type": voice, "encoding": "mp3", "speed_ratio": float(speed),
                  "loudness_ratio": 1.0},
        "request": {"reqid": uuid.uuid4().hex, "text": text, "operation": "query"},
    }
    req = urllib.request.Request(
        API, data=json.dumps(body).encode("utf-8"),
        headers={"Authorization": "Bearer;" + token, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.load(r)
    except urllib.error.HTTPError as e:
        sys.stderr.write("VOLC TTS HTTP %d: %s\n" % (e.code, e.read().decode("utf-8", "replace")[:500]))
        raise SystemExit(2)
    if resp.get("code") != 3000:  # 3000 = Success on 火山 TTS
        sys.stderr.write("VOLC TTS ERROR: " + json.dumps(resp, ensure_ascii=False)[:400] + "\n")
        raise SystemExit(2)
    audio = base64.b64decode(resp["data"])
    with open(out, "wb") as f:
        f.write(audio)
    dur = (resp.get("addition") or {}).get("duration")
    print(f"[volc_tts] wrote {out} ({len(audio)} bytes), duration={dur}ms, voice={voice}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--text-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default=os.getenv("VOLC_TTS_VOICE", "zh_female_vv_uranus_bigtts"))
    ap.add_argument("--speed", default=os.getenv("VOLC_TTS_SPEED", "1.0"))
    args = ap.parse_args()

    appid = os.getenv("VOLC_TTS_APPID", "").strip()
    token = os.getenv("VOLC_TTS_TOKEN", "").strip()
    cluster = os.getenv("VOLC_TTS_CLUSTER", "volcano_tts").strip()
    # Fallback: the agent container has no host .env / env passthrough, so read a
    # creds file on the persistent /root mount when env vars are absent.
    if not appid or not token:
        for cand in (os.getenv("VOLC_TTS_CREDS_FILE"),
                     os.path.expanduser("~/.config/volc_tts.json"),
                     "/root/.config/volc_tts.json"):
            if cand and os.path.exists(cand):
                try:
                    c = json.load(open(cand, encoding="utf-8"))
                except (OSError, ValueError):
                    continue
                appid = appid or str(c.get("appid", "")).strip()
                token = token or str(c.get("token", "")).strip()
                if c.get("cluster"):
                    cluster = str(c["cluster"]).strip()
                break
    if not appid or not token:
        sys.stderr.write("Missing VOLC_TTS_APPID / VOLC_TTS_TOKEN (env or ~/.config/volc_tts.json).\n")
        raise SystemExit(2)

    text = args.text
    if args.text_file:
        text = open(args.text_file, encoding="utf-8").read().strip()
    if not text:
        sys.stderr.write("No --text / --text-file.\n")
        raise SystemExit(2)
    synth(text, args.out, appid, token, args.voice, cluster, args.speed)


if __name__ == "__main__":
    main()
