#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fish Audio TTS → mp3. Alternative voice provider for 抖音 narration — used for the
community character voices (e.g. 赛马娘 / 哈基米) that don't exist in 火山/豆包. Mirrors
volc_tts.py's CLI so make_rich_video.py can call either provider interchangeably.

Credentials (do NOT hardcode):
  FISH_API_KEY    - Fish Audio API key (Bearer token), from fish.audio → API Keys
  FISH_TTS_MODEL  - backbone: "s1" (default, cheaper) or "s2-pro"
Creds file fallback (env absent): ~/.config/fish_tts.json
  {"api_key": "...", "model": "s1", "voice": "<reference_id>"}

Usage:
  python fish_tts.py --text "你好" --out v.mp3 --voice <reference_id> [--speed 1.0] [--model s1]
"""
import argparse, json, os, sys, urllib.request, urllib.error

API = "https://api.fish.audio/v1/tts"


def synth(text, out, api_key, reference_id, model, speed):
    body = {
        "text": text,
        "reference_id": reference_id,
        "format": "mp3",
        "mp3_bitrate": 128,
        "normalize": True,
        "latency": "normal",
        "prosody": {"speed": float(speed)},
    }
    req = urllib.request.Request(
        API, data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": "Bearer " + api_key,
            "Content-Type": "application/json",
            "model": model,
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            ctype = r.headers.get("Content-Type", "")
            data = r.read()
    except urllib.error.HTTPError as e:
        sys.stderr.write("FISH TTS HTTP %d: %s\n" % (e.code, e.read().decode("utf-8", "replace")[:500]))
        raise SystemExit(2)
    except urllib.error.URLError as e:
        sys.stderr.write("FISH TTS network error: %s\n" % e)
        raise SystemExit(2)
    # success = raw audio bytes; an error can come back as JSON (even with 200)
    if "application/json" in ctype or data[:1] in (b"{", b"["):
        sys.stderr.write("FISH TTS unexpected JSON: " + data[:400].decode("utf-8", "replace") + "\n")
        raise SystemExit(2)
    if not data or len(data) < 200:
        sys.stderr.write("FISH TTS empty/too-small audio (%d bytes)\n" % len(data))
        raise SystemExit(2)
    with open(out, "wb") as f:
        f.write(data)
    print(f"[fish_tts] wrote {out} ({len(data)} bytes), model={model}, ref={reference_id}")
    return out


def _load_creds(voice, model):
    api_key = os.getenv("FISH_API_KEY", "").strip()
    for cand in (os.getenv("FISH_TTS_CREDS_FILE"),
                 os.path.expanduser("~/.config/fish_tts.json"),
                 "/root/.config/fish_tts.json"):
        if api_key and voice:
            break
        if cand and os.path.exists(cand):
            try:
                c = json.load(open(cand, encoding="utf-8"))
            except (OSError, ValueError):
                continue
            api_key = api_key or str(c.get("api_key", "")).strip()
            if not model and c.get("model"):
                model = str(c["model"]).strip()
            if not voice and c.get("voice"):
                voice = str(c["voice"]).strip()
    return api_key, voice, model


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text")
    ap.add_argument("--text-file")
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", "--reference-id", dest="voice", default=os.getenv("FISH_TTS_VOICE", ""))
    ap.add_argument("--model", default=os.getenv("FISH_TTS_MODEL", "") or "")
    ap.add_argument("--speed", default=os.getenv("FISH_TTS_SPEED", "1.0"))
    args = ap.parse_args()

    api_key, voice, model = _load_creds(args.voice or "", args.model or "")
    model = model or "s1"
    if not api_key:
        sys.stderr.write("Missing FISH_API_KEY (env or ~/.config/fish_tts.json).\n")
        raise SystemExit(2)
    if not voice:
        sys.stderr.write("Missing --voice/--reference-id (Fish Audio model id).\n")
        raise SystemExit(2)

    text = args.text
    if args.text_file:
        text = open(args.text_file, encoding="utf-8").read().strip()
    if not text:
        sys.stderr.write("No --text / --text-file.\n")
        raise SystemExit(2)
    synth(text, args.out, api_key, voice, model, args.speed)


if __name__ == "__main__":
    main()
