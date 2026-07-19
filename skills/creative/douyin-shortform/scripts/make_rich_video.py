#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rich motion-graphics 抖音 builder (1080x1920) — ONE command, INSIDE the container.

This is the CANONICAL 抖音 video pipeline. Narration is 豆包/火山 **vivi** natural
voice via volc_tts.py; audio and slides are auto-synced (each scene voiced
separately so its on-screen duration matches its spoken length).

VISUALS are now a ROTATING STYLE ENGINE (richlib/) — not one fixed look. Each
run the registry picks a style (editorial / notebook / terminal / tabloid /
keynote) by topic affinity + anti-repeat, and the style randomizes WITHIN itself
(palette, layout, texture). So consecutive videos rarely share a look and two
same-style videos still differ. The TTS/timing/cover/mux below is unchanged.

  spec.json -> per-scene vivi TTS -> per-scene duration
            -> richlib style -> HTML/CSS motion graphics via Playwright
            -> ffmpeg: smooth-interpolate + cover + mux -> 1080x1920 H.264/AAC mp4

spec JSON (content only — the STYLE is chosen by the engine, not the spec):
{
  "tag": "AI编程",                  # small label/pill (optional)
  "handle": "@yourhandle",                # bottom handle (default @yourhandle)
  "title": "...",                   # used for style affinity + seed (optional)
  "style": "terminal",              # OPTIONAL hard override of the rotation
  "scenes": [
    {"type":"hook","say":"...","eyebrow":"AI编程","lines":["写完功能","最烦写测试"]},
    {"type":"stat","say":"...","value":"70%","label":"测试初稿 AI 来写"},
    {"type":"code","say":"...","lang":"python","caption":"3秒出骨架","code":"def t():\\n    pass"},
    {"type":"compare","say":"...","before":"手写 · 1.5天","after":"AI起草 · 10分钟"},
    {"type":"bullets","say":"...","head":"我只做三件事","lines":["读边界","补 case","改断言"]},
    {"type":"outro","say":"...","lines":["省下的时间","拿去啃硬逻辑"]}   # content close, NO 关注/点赞 CTA
  ]
}

Usage (inside the agent container):
  python make_rich_video.py --spec spec.json --out /root/hermes-content/douyin/<date>-<topic>.mp4
  # voice creds from /root/.config/volc_tts.json ; override voice: --voice <type>
  # force a style:  --style editorial|notebook|terminal|tabloid|keynote
"""
import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from richlib import base, registry          # noqa: E402
from richlib.base import W, H               # noqa: E402

PAD = 0.18          # silence/breath appended after each scene (s) — tight, 抖音 pacing
MIN_DUR = 1.5       # floor for a scene with no/short audio
# 北京小爷: male, attitude, carries tech-唠嗑 better than vivi's announcer read
# (user verdict 2026-07-12: vivi 播音腔太AI). Container has no host .env, so the
# fallback here IS the effective default.
DEFAULT_VOICE = os.getenv("VOLC_TTS_VOICE", "zh_male_beijingxiaoye_moon_bigtts")

# Background music: bundled public-domain tracks (FreePD collection), mixed LOW
# under the vivi voice — bare narration reads as AI-made and hurts retention.
BGM_DIR = os.path.join(_HERE, "assets", "bgm")
BGM_VOL = 0.14      # bgm gain relative to voice (voice stays at 1.0, normalize=0)
BGM_FADE = 1.5      # fade-out length at the end (s)

# follow/like CTAs — user override 2026-06-19: content-only close, never a 关注/点赞
# CTA. 收藏 ("码住") is deliberately ALLOWED since 2026-07-15: saves are the #1
# distribution signal for knowledge content, and a save prompt doesn't kill 完播.
_CTA_RE = re.compile(
    r"(关注我|关注一下|点关注|求关注|关注\s*[@＠]|一键三连|三连|点赞|点个赞|求赞|"
    r"转发一下|订阅一下|订阅频道|follow\s*me|please\s*subscribe|hit\s*subscribe)",
    re.I,
)

# text-punch card types: fine as seasoning, deadly as the main course. media +
# diagram are the "visual" types; everything else reads as a slide.
_TEXT_CARD_TYPES = {"hook", "stat", "compare", "bullets", "code", "outro"}


def _norm_say(s):
    return re.sub(r"[\s，。！？!?、,.:：;；\"'「」『』]", "", str(s or ""))


def validate_spec(spec):
    """HARD GATE #0 — slideshow-risk checks BEFORE any TTS/render money is spent.
    Born 2026-07-15: a published video narrated the same sentence twice (one say
    string pasted into two scenes) and stuffed 7/9 scenes with text cards after
    material rejections. The engine now refuses both outright."""
    scenes = spec.get("scenes", [])
    problems = []

    # 1. duplicate narration — each scene must own a distinct slice of the script
    seen = {}
    for i, sc in enumerate(scenes):
        key = _norm_say(sc.get("say"))
        if not key:
            continue
        if key in seen:
            problems.append(
                f"scene {seen[key]} 和 scene {i} 的 say 完全相同(「{str(sc.get('say'))[:30]}…」)。"
                f"口播会被念两遍。把口播这句只留给一个场景,另一个场景分到它自己的句子;"
                f"如果两个场景确实共享一句话,合并成一个场景。")
        else:
            seen[key] = i

    # 2. duplicate content cards (same type + same payload = the lazy-fill tell)
    sigs = {}
    for i, sc in enumerate(scenes):
        t = sc.get("type")
        if t == "compare":
            sig = (t, _norm_say(sc.get("before")), _norm_say(sc.get("after")))
        elif t == "stat":
            sig = (t, _norm_say(sc.get("value")), _norm_say(sc.get("label")))
        else:
            continue
        if sig in sigs:
            problems.append(f"scene {sigs[sig]} 和 scene {i} 是内容相同的 {t} 卡——复读凑数。"
                            f"删掉一个,空出的口播换成真实素材(media)场景。")
        else:
            sigs[sig] = i

    # 3. text-card discipline: ≤3 total, never two adjacent
    text_idx = [i for i, sc in enumerate(scenes) if sc.get("type") in _TEXT_CARD_TYPES]
    if len(text_idx) > 3:
        problems.append(
            f"纯文字卡有 {len(text_idx)} 屏(scene {text_idx}),上限 3 屏。"
            f"多出来的换成 media(真实素材)或 diagram。找不到素材才用 AI 插画(全片限 1 张):"
            f"python $SKILL_DIR/scripts/gen_scene_image.py --desc \"<画面内容一句话>\" --out <工作目录>/genN.png")
    for a, b in zip(text_idx, text_idx[1:]):
        if b == a + 1:
            problems.append(f"scene {a} 和 scene {b} 是连续两屏纯文字卡(观众直接划走)。"
                            f"中间的那屏换成 media 或 diagram。")

    # 4. visual coverage: real material must carry the video
    n = len(scenes)
    media_ok = sum(1 for sc in scenes if sc.get("type") == "media" and (
        os.path.isfile(str(sc.get("image", ""))) or os.path.isfile(str(sc.get("video", "")))))
    need = max(2, (n * 3 + 9) // 10)     # ceil(0.3n), floor 2
    if media_ok < need:
        problems.append(
            f"可用的真实素材场景只有 {media_ok} 个(共 {n} 屏),至少要 {need} 个。"
            f"补素材三选一:fetch_web_clip.py(新闻视频) / record_page_clip.py --start-y 700(页面实录) / "
            f"browser_screenshot;都拿不到就 AI 插画兜底(全片限 1 张):"
            f"python $SKILL_DIR/scripts/gen_scene_image.py --desc \"<画面内容>\" --out <工作目录>/genN.png "
            f"然后填进 scene 的 image 字段。")

    # 5. AI illustrations: at most ONE per video (user policy 2026-07-19 — the
    # 07-17/18 videos leaned on 2-3 CogView images each and read as AI slop).
    # Detected via the .ai sidecar gen_scene_image writes + the genN.png naming.
    ai_idx = [i for i, sc in enumerate(scenes) if sc.get("type") == "media" and (
        os.path.isfile(str(sc.get("image", "")) + ".ai")
        or os.path.basename(str(sc.get("image", ""))).lower().startswith("gen"))]
    if len(ai_idx) > 1:
        problems.append(
            f"AI 插画用了 {len(ai_idx)} 张(scene {ai_idx}),全片上限 1 张。"
            f"多出来的换成真实素材(fetch_web_clip / record_page_clip / browser_screenshot),"
            f"真实素材才是画面的主体,AI 插画只是最后的兜底。")

    if problems:
        lines = ["", "[rich] ❌ spec 校验不通过,拒绝出片。按下面逐条修完 spec.json 再重跑同一条命令:"]
        lines += [f"  {k+1}. {p}" for k, p in enumerate(problems)]
        lines += ["[rich] 规则:禁止用文字卡顶替被拒素材;每修一轮重跑,通过之前绝不发布。", ""]
        sys.stderr.write("\n".join(lines))
        sys.exit(4)


def _scrub_cta(say):
    if not say:
        return say
    parts = re.split(r"(?<=[。！？!?\n])", say)
    kept = [p for p in parts if p.strip() and not _CTA_RE.search(p)]
    return "".join(kept).strip()


# ----------------------------------------------------------------------------- TTS + timing
def _ffprobe_dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except (TypeError, ValueError):
        return 0.0


def _tts_scene(say, out_mp3, voice, speed, provider="volc", fish_model="s1", emotion=""):
    say = (say or "").strip()
    if not say:
        return False
    if provider == "fish":
        cmd = [sys.executable, os.path.join(_HERE, "fish_tts.py"),
               "--text", say, "--out", out_mp3, "--model", fish_model, "--speed", str(speed)]
        if voice:
            cmd += ["--voice", voice]
    else:
        cmd = [sys.executable, os.path.join(_HERE, "volc_tts.py"),
               "--text", say, "--out", out_mp3, "--voice", voice, "--speed", str(speed)]
        if emotion:
            cmd += ["--emotion", emotion]
    # one retry with backoff — TTS endpoints flake through the proxy (SSL EOF)
    for attempt in (1, 2):
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode == 0 and os.path.exists(out_mp3):
            return True
        sys.stderr.write(f"[rich] {provider}_tts failed (attempt {attempt}): {r.stderr[:300]}\n")
        if attempt == 1:
            time.sleep(8)
    return False


def _silence(out_mp3, seconds):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", f"{seconds:.3f}", "-c:a", "libmp3lame", "-q:a", "6", out_mp3],
        capture_output=True, text=True, check=True,
    )


# sentence boundaries only (。！？…—— and western .!?; when sentence-final);
# commas/colons stay INSIDE the take so the voice keeps its natural flow
_SENT_SPLIT = re.compile(r"([。！？；!?…]+|——)")


def _sentences(say):
    """Split narration into whole sentences, KEEPING the final punctuation —
    the TTS needs the 问号/叹号 to land the intonation."""
    parts = _SENT_SPLIT.split(str(say or "").strip())
    sents, buf = [], ""
    for p in parts:
        if not p:
            continue
        if _SENT_SPLIT.fullmatch(p):
            buf += p
            if buf.strip():
                sents.append(buf.strip())
            buf = ""
        else:
            buf += p
    if buf.strip():
        sents.append(buf.strip())
    return sents


def build_audio(scenes, workdir, voice, speed, provider="volc", fish_model="s1"):
    """SENTENCE-level synthesis with PROSODY — one flat TTS read per scene was
    the biggest "很AI" tell, but per-subtitle-chunk takes (the previous fix)
    chopped sentences at every comma and stripped the punctuation, so questions
    never sounded like questions. Each whole sentence is one take (punctuation
    included, pacing rules applied), and subtitle chunks inside a sentence get
    their share of the take's REAL duration proportional to char count.
    Returns (voice_mp3, durs, timings) where timings is per-scene
    [(start, end, text), ...] in scene-local seconds."""
    from richlib.base import _sub_chunks
    sil_cache = {}

    def silence_file(sec):
        key = f"{sec:.2f}"
        if key not in sil_cache:
            p = os.path.join(workdir, f"_sil{key}.mp3")
            _silence(p, sec)
            sil_cache[key] = p
        return sil_cache[key]

    base_speed = float(speed)
    parts, durs, timings = [], [], []
    for i, sc in enumerate(scenes):
        say = _scrub_cta(sc.get("say", ""))
        sents = _sentences(say)
        t, sc_timings = 0.0, []
        # designer-annotated prosody: scene-level emotion tag + rate multiplier
        # (spec: "emotion": "surprise|happy|angry|coldness|...", "rate": 0.9-1.15)
        sc_emotion = str(sc.get("emotion", "") or "").strip()
        try:
            sc_rate = min(max(float(sc.get("rate", 1.0) or 1.0), 0.85), 1.2)
        except (TypeError, ValueError):
            sc_rate = 1.0
        if not sents:
            d = max(MIN_DUR - PAD, 0.8)
            parts.append(silence_file(d))
            t = d
        for j, sent in enumerate(sents):
            is_q = sent.rstrip("」』\"'…").endswith(("?", "？"))
            sp = base_speed * sc_rate
            if is_q or "为什么" in sent:
                sp = max(sp - 0.10, 0.95)              # questions land slower
            elif j == len(sents) - 1 and len(sents) > 1:
                sp = max(sp - 0.04, 1.0)               # settle on the closer
            elif j == 0 and i == 0:
                sp = sp + 0.04                         # hook slightly punchier
            seg = os.path.join(workdir, f"_a{i}_{j}.mp3")
            ok = _tts_scene(sent, seg, voice, f"{sp:.2f}", provider, fish_model,
                            emotion=sc_emotion)
            d = _ffprobe_dur(seg) if ok else 0.0
            if not ok or d <= 0:
                # a video with silence where the voiceover should be must never
                # ship — refuse to render rather than substitute silence
                sys.stderr.write(
                    f"[rich] ❌ TTS 不可用(scene {i}, 「{sent[:30]}」合成失败,已重试)。"
                    f"拒绝出片:没有人声的视频绝不能进 ready/。"
                    f"等 TTS 恢复后重跑同一条命令;绝不允许静音顶替人声。\n")
                sys.exit(5)
            parts.append(seg)
            # subtitle chunks ride the sentence take: each gets a share of the
            # REAL take duration proportional to its char count
            chunks = _sub_chunks(sent) or [sent]
            total_chars = sum(len(c) for c in chunks) or 1
            ct = t
            for ch in chunks:
                cd = d * (len(ch) / total_chars)
                sc_timings.append((round(ct, 3), round(ct + cd, 3), ch))
                ct += cd
            t += d
            if j < len(sents) - 1:
                gap = 0.32 if is_q else 0.22           # let a question hang /
                parts.append(silence_file(gap))        # breath between sentences
                t += gap
        parts.append(silence_file(PAD))
        t += PAD
        durs.append(round(t, 3))
        timings.append(sc_timings)
    listf = os.path.join(workdir, "_concat.txt")
    with open(listf, "w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    voice_mp3 = os.path.join(workdir, "_voice.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
         "-c:a", "libmp3lame", "-q:a", "4", voice_mp3],
        capture_output=True, text=True, check=True,
    )
    return voice_mp3, durs, timings


# ----------------------------------------------------------------------------- bgm
def pick_bgm(spec, rng, cli_arg):
    """Resolve the bgm track: spec/CLI 'off' disables; a name matches a bundled
    track; 'auto' picks by MOOD (filename prefix chill-*/upbeat-*), matching the
    content's energy — 科普/讲解 rides chill, 爆点/游戏/快节奏 rides upbeat.
    Deterministic per video (style-engine seed). Drop extra mp3s into assets/bgm
    (with a chill-/upbeat- prefix) and they join the rotation automatically."""
    want = cli_arg if cli_arg not in (None, "", "auto") else spec.get("bgm", "auto")
    if want in (False, "off", "none", "no"):
        return None
    tracks = sorted(glob.glob(os.path.join(BGM_DIR, "*.mp3")))
    if not tracks:
        return None
    if isinstance(want, str) and want not in ("auto", "true"):
        if os.path.isfile(want):
            return want
        for t in tracks:
            if want.lower() in os.path.basename(t).lower():
                return t
        sys.stderr.write(f"[rich] bgm '{want}' not found in {BGM_DIR}; using auto\n")
    blob = " ".join(str(spec.get(k, "")) for k in ("title", "tag")) + " " + " ".join(
        str(sc.get("say", "")) for sc in spec.get("scenes", [])[:2])
    hot = any(w in blob for w in ("游戏", "翻车", "炸", "爆", "逆天", "大战", "撕",
                                  "疯", "崩", "掀桌", "输", "赢"))
    bucket = [t for t in tracks
              if os.path.basename(t).startswith("upbeat-" if hot else "chill-")]
    return rng.choice(bucket or tracks)


def synth_sfx(workdir):
    """Three clean synthetic UI sounds (no external assets): a scene-cut whoosh,
    a stat 'ding', and a soft pop. Mixed low — texture, not karaoke."""
    out = {}
    specs = {
        "whoosh": ["-f", "lavfi", "-i", "anoisesrc=color=pink:d=0.4",
                   "-af", "bandpass=f=850:width_type=h:w=600,afade=t=in:d=0.10,"
                          "afade=t=out:st=0.18:d=0.22,volume=1.6"],
        "ding": ["-f", "lavfi", "-i", "sine=frequency=1318:duration=0.5",
                 "-af", "volume='exp(-7*t)':eval=frame,volume=1.4"],
        "pop": ["-f", "lavfi", "-i", "sine=frequency=520:duration=0.09",
                "-af", "afade=t=out:st=0.03:d=0.06,volume=1.2"],
    }
    for name, args in specs.items():
        p = os.path.join(workdir, f"_sfx_{name}.wav")
        r = subprocess.run(["ffmpeg", "-y"] + args + [p], capture_output=True, text=True)
        if r.returncode == 0 and os.path.isfile(p):
            out[name] = p
    return out


def mix_sfx(audio_mp3, scenes, durs, workdir):
    """Overlay transition/stat SFX at scene boundaries. Fails soft."""
    sfx = synth_sfx(workdir)
    if not sfx:
        return audio_mp3
    events = []          # (time_s, wav)
    t = 0.0
    for i, (sc, d) in enumerate(zip(scenes, durs)):
        if i > 0 and "whoosh" in sfx:
            events.append((max(t - 0.12, 0.0), sfx["whoosh"]))
        if sc.get("type") in ("stat", "compare") and "ding" in sfx:
            events.append((t + 0.15, sfx["ding"]))
        elif sc.get("type") == "diagram" and "pop" in sfx:
            events.append((t + 0.2, sfx["pop"]))
        t += d
    if not events:
        return audio_mp3
    events = events[:14]
    cmd = ["ffmpeg", "-y", "-i", audio_mp3]
    fc, labels = [], []
    for k, (ts, wav) in enumerate(events):
        cmd += ["-i", wav]
        fc.append(f"[{k+1}:a]adelay={int(ts*1000)}|{int(ts*1000)},volume=0.22[e{k}]")
        labels.append(f"[e{k}]")
    fc.append(f"[0:a]{''.join(labels)}amix=inputs={len(events)+1}:duration=first:normalize=0[out]")
    mixed = os.path.join(workdir, "_voice_sfx.mp3")
    r = subprocess.run(cmd + ["-filter_complex", ";".join(fc), "-map", "[out]",
                              "-c:a", "libmp3lame", "-q:a", "4", mixed],
                       capture_output=True, text=True)
    if r.returncode != 0 or not os.path.isfile(mixed):
        sys.stderr.write("[rich] sfx mix failed (keeping base audio)\n")
        return audio_mp3
    return mixed


def mix_bgm(voice_mp3, bgm_path, workdir):
    """Loop the bgm under the voice with SIDECHAIN DUCKING — the track breathes
    up in the narration gaps and tucks 8-10dB under speech (a constant-volume
    bed was one of the flat "AI made this" tells). A whisper of pink-noise room
    tone kills the digital-vacuum silence between phrases. The voice stays at
    full level. Returns the mixed mp3, or the plain voice on any failure."""
    dur = _ffprobe_dur(voice_mp3)
    if dur <= 0:
        return voice_mp3
    mixed = os.path.join(workdir, "_voice_bgm.mp3")
    fade_st = max(0.0, dur - BGM_FADE)
    fc = (
        # bgm bed: a bit louder than the old constant level, then keyed by voice
        f"[1:a]volume={BGM_VOL * 1.9:.3f},afade=t=in:st=0:d=0.8,"
        f"afade=t=out:st={fade_st:.3f}:d={BGM_FADE}[bed];"
        f"[0:a]asplit=2[v][key];"
        f"[bed][key]sidechaincompress=threshold=0.015:ratio=9:attack=60:release=500:"
        f"makeup=1[duck];"
        # room tone: -52dB pink noise, just enough to remove the vacuum
        f"anoisesrc=color=pink:r=44100:a=0.0025:d={dur:.3f}[room];"
        f"[v][duck][room]amix=inputs=3:duration=first:dropout_transition=3:normalize=0[out]"
    )
    r = subprocess.run(
        ["ffmpeg", "-y", "-i", voice_mp3, "-stream_loop", "-1", "-i", bgm_path,
         "-filter_complex", fc, "-map", "[out]",
         "-c:a", "libmp3lame", "-q:a", "4", mixed],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not os.path.exists(mixed):
        sys.stderr.write("[rich] bgm duck mix failed (using plain voice):\n" + r.stderr[-400:] + "\n")
        return voice_mp3
    return mixed


# ----------------------------------------------------------------------------- clips
def _ffprobe_dims(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", path],
        capture_output=True, text=True,
    )
    try:
        w, h = out.stdout.strip().split("\n")[0].split(",")[:2]
        return int(w), int(h)
    except Exception:
        return 0, 0


def prepare_clips(spec, workdir):
    """Normalize `media` video clips for the renderer: headless chromium can't
    decode h264, so anything not already webm is transcoded to vp9; a poster
    frame is extracted (fit-mode blur layer) and the aspect decides fit/cover.
    Mutates the scene dicts in place (video path, _poster, _fit).

    Media images are also COPIED into the container-local workdir first: the
    content dirs are Windows bind mounts, and having chromium raster large
    files over the Docker file-sharing channel was implicated in the 2026-07-15
    render crash cascade. Local reads take the whole variable off the table."""
    for i, sc in enumerate(spec.get("scenes", [])):
        if sc.get("type") == "media" and sc.get("image"):
            src = str(sc["image"])
            if os.path.isfile(src):
                local = os.path.join(workdir, f"_img{i}" + os.path.splitext(src)[1])
                try:
                    shutil.copy(src, local)
                    sc["image"] = local
                except OSError:
                    pass    # fall back to reading in place
    for i, sc in enumerate(spec.get("scenes", [])):
        if sc.get("type") != "media" or not sc.get("video"):
            continue
        src = str(sc["video"])
        if not os.path.isfile(src):
            continue
        clip = src
        if not src.lower().endswith(".webm"):
            clip = os.path.join(workdir, f"_clip{i}.webm")
            r = subprocess.run(
                ["ffmpeg", "-y", "-i", src, "-an", "-c:v", "libvpx-vp9",
                 "-deadline", "realtime", "-cpu-used", "8", "-crf", "34", "-b:v", "0",
                 "-vf", "scale='min(1080,iw)':-2", clip],
                capture_output=True, text=True,
            )
            if r.returncode != 0 or not os.path.isfile(clip):
                sys.stderr.write(f"[rich] clip transcode failed for scene {i}; dropping video\n")
                sc.pop("video", None)
                continue
            sc["video"] = clip
        poster = os.path.join(workdir, f"_poster{i}.jpg")
        subprocess.run(["ffmpeg", "-y", "-i", clip, "-frames:v", "1", "-q:v", "3",
                        "-update", "1", poster], capture_output=True, text=True)
        if os.path.isfile(poster):
            sc["_poster"] = poster
        w, h = _ffprobe_dims(clip)
        if w and h:
            sc["_aspect"] = w / max(h, 1)
            sc["_fit"] = sc["_aspect"] > 0.8


# ----------------------------------------------------------------------------- media verification
# Primary reviewer = Kimi k2.6 vision (the unified vision plan; Moonshot CN
# endpoint). glm-4v-flash stays as the fallback — it let a full-page article
# screenshot through on 2026-07-19 (prompt listed 大段文章正文排版 as junk and
# it still passed), so it is no longer the judge of record.
_VISION_CREDS_PATHS = [os.path.expanduser("~/.config/moonshot_vision.json"),
                       "/root/.config/moonshot_vision.json",
                       os.path.expanduser("~/.config/zhipu_vision.json"),
                       "/root/.config/zhipu_vision.json"]


def _load_vision_creds():
    """Return ALL readable cred sets, priority order (primary first).
    ~ expands to /root in the container, so dedupe by realpath."""
    out, seen = [], set()
    for p in _VISION_CREDS_PATHS:
        rp = os.path.realpath(p)
        if rp in seen or not os.path.isfile(p):
            continue
        seen.add(rp)
        try:
            with open(p, encoding="utf-8") as fh:
                out.append(json.load(fh))
        except Exception:
            pass
    return out


def _vision_check(image_path, say, creds):
    """Ask GLM-4v-flash whether this material is usable as evidence for `say`.
    Returns dict {login_wall, relevant, content} or None on infra failure."""
    import base64 as _b64
    import requests as _rq
    path = image_path
    try:
        if os.path.getsize(path) > 3 * 1024 * 1024:
            from PIL import Image
            im = Image.open(path).convert("RGB")
            im.thumbnail((1080, 4096))
            small = path + ".vchk.jpg"
            im.save(small, "JPEG", quality=85)
            path = small
    except Exception:
        pass
    ext = os.path.splitext(path)[1].lower().lstrip(".") or "png"
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    with open(path, "rb") as fh:
        b64 = _b64.b64encode(fh.read()).decode()
    prompt = (
        "你是严格的短视频素材审查员。这张图/视频帧将作为口播这句话的画面:\n"
        f"「{say}」\n"
        "抖音观众一眼能看出「截网页」很廉价。**网页垃圾**只指以下明确元素:网站导航条/顶部菜单栏、"
        "未播放视频上的大播放按钮▶、右侧点赞评论转发栏、底部无关的推荐视频缩略图、"
        "「打开APP/下载/查看精彩图片」横幅或按钮、搜索框、面包屑。\n"
        "**文字墙**单独判:画面的主体(超过一半面积)是密密麻麻的文章正文/段落文字,"
        "缩到手机竖屏上根本读不清——整页文章截图就是典型。有醒目大标题+少量文字的海报/标题卡不算。\n"
        "⚠️ 以下**不算**垃圾:新闻片自带的角标/台标/小水印、画面里烧进去的新闻字幕条、"
        "日期地点标注、插画风格的示意图——这些都是正常素材。\n"
        "junk_element 必须写出你具体看到了上述哪个元素;写不出来就必须判 false。\n"
        "只输出一个 JSON 对象,不要多余文字:\n"
        '{"login_wall": <有无登录弹窗/扫码二维码/登录遮罩,true|false>, '
        '"webpage_junk": <含上述明确网页外壳元素才 true,否则 false>, '
        '"junk_element": "<具体看到的元素,没有就空字符串>", '
        '"text_wall": <画面主体是大段密集正文文字,true|false>, '
        '"relevant": <画面主要内容与口播主题是否相关,true|false>, '
        '"content": "<一句话:画面主要是什么>"}'
    )
    creds_list = creds if isinstance(creds, list) else [creds]
    for ci, cred in enumerate(creds_list):
        body = {
            "model": cred.get("model", "glm-4v-flash"),
            "temperature": 0.1,
            "messages": [{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/{mime};base64,{b64}"}},
                {"type": "text", "text": prompt},
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
            except Exception as e:
                if attempt == 0:
                    time.sleep(4)      # rate limits (429) need a beat, not a hammer
                else:
                    tag = cred.get("model", "?")
                    if ci == len(creds_list) - 1:
                        sys.stderr.write(f"[rich] vision check unavailable for "
                                         f"{os.path.basename(image_path)} (last={tag}): {e}\n")
                    else:
                        sys.stderr.write(f"[rich] vision {tag} failed, trying fallback: {e}\n")
    return None


def verify_media(spec):
    """HARD GATE: refuse to render when a media scene's material is a login
    wall or unrelated to its narration. Instructions alone did not stop bad
    material (a 小红书 login-wall screenshot captioned 「来源·知乎」 shipped in a
    published video on 2026-07-13) — so the ENGINE enforces it."""
    creds = _load_vision_creds()
    if not creds:
        sys.stderr.write("[rich] WARNING: no vision creds (~/.config/zhipu_vision.json) — "
                         "media verification SKIPPED\n")
        return
    failures = []
    for i, sc in enumerate(spec.get("scenes", [])):
        if sc.get("type") != "media":
            continue
        target = sc.get("_poster") or sc.get("image")
        if not target or not os.path.isfile(str(target)):
            continue
        say = str(sc.get("say", ""))[:120]
        verdict = _vision_check(str(target), say, creds)
        if verdict is None:
            continue    # infra failure — don't block builds on flaky vision
        name = os.path.basename(str(sc.get("video") or sc.get("image")))
        desc = str(verdict.get("content", ""))[:80]
        if verdict.get("login_wall"):
            failures.append((i, name, say, f"登录墙/扫码弹窗 — {desc}"))
        elif verdict.get("text_wall"):
            failures.append((i, name, say,
                             f"整页文字墙(手机上根本读不清)— {desc}。换成文章里的配图/页面实录片段,"
                             f"或干脆用 diagram 把要点画出来"))
        elif verdict.get("webpage_junk") and str(verdict.get("junk_element", "")).strip():
            failures.append((i, name, say,
                             f"截网页外壳({str(verdict.get('junk_element'))[:40]})太廉价 — {desc}"))
        elif verdict.get("relevant") is False:
            failures.append((i, name, say, f"画面与口播无关 — 画面是「{desc}」"))
        else:
            print(f"[rich] media ok: scene {i} [{name}] — {desc}")
    if failures:
        # A refusal alone lets a lazy agent give up — emit a REPAIR WORK ORDER:
        # per failing scene, what to do RIGHT NOW, then rerun.
        lines = ["", "[rich] ❌ 素材审查不通过,拒绝出片。现在按下面的作业单修,修完重跑同一条命令:"]
        for i, name, say, why in failures:
            lines += [
                f"  ── scene {i} [{name}]: {why}",
                f"     这一屏的口播是:「{say[:60]}」— 给它换一份真实相关的画面,三选一:",
                f"       a) 官方/新闻视频: python $SKILL_DIR/scripts/fetch_web_clip.py --url <相关视频页或mp4直链> --out <工作目录>/fix{i}.webm --seconds 8",
                f"       b) 页面实录:     python $SKILL_DIR/scripts/record_page_clip.py --url <新闻原文/GitHub/官网> --out <工作目录>/fix{i}.webm --seconds 6",
                f"       c) 已登录浏览器截图: browser_navigate 相关页面 → browser_screenshot → cp 到工作目录",
                f"       d) 都拿不到 → AI 插画兜底(禁止改成文字卡!全片限 1 张): python $SKILL_DIR/scripts/gen_scene_image.py"
                f" --desc \"<这一屏该画什么,一句话>\" --out <工作目录>/gen{i}.png",
                f"     换好后更新 spec.json 里 scene {i} 的 image/video 字段。",
            ]
        lines += [
            "[rich] 规则:每修一轮就重跑渲染,最多 3 轮;通过之前绝不发布、绝不汇报「已完成」。",
            "",
        ]
        sys.stderr.write("\n".join(lines))
        sys.exit(3)


# ----------------------------------------------------------------------------- visuals (richlib)
def build_html(spec, durs, out_path="", explicit_style=None, timings=None):
    """Pick a style via the registry, let it self-vary, render the document.
    `media` scenes (full-bleed real imagery + Ken Burns) are rendered by base —
    styles only skin the text-punch scenes. A speech-synced subtitle layer runs
    over everything. Returns (html_doc, style, recent_before, ctx)."""
    rng = registry.make_rng(spec, out_path)
    style, recent = registry.select(spec, rng, out_path, explicit_style)
    ctx = style.variant(rng)
    ctx.setdefault("accent", "#FF2E4D")
    if spec.get("lock_accent") and spec.get("accent"):
        ctx["accent"] = spec["accent"]      # let a spec pin its accent if it insists
    css = style.css(ctx)
    scenes = spec.get("scenes", [])
    parts = []
    for i, sc in enumerate(scenes):
        d_i = durs[i] if i < len(durs) else 8.0
        if sc.get("type") == "diagram":
            parts.append(base.diagram_scene(i, sc, ctx, d_i))
            continue
        if sc.get("type") == "media":
            vid = str(sc.get("video", ""))
            img = str(sc.get("image", ""))
            if vid and os.path.isfile(vid):
                parts.append(base.media_scene(i, sc, ctx, "kb0", d_i,
                                              fit=bool(sc.get("_fit")),
                                              aspect=sc.get("_aspect")))
                continue
            if img and os.path.isfile(img):
                fit, aspect = False, None
                try:
                    from PIL import Image
                    with Image.open(img) as im:
                        w, h = im.size
                    aspect = w / max(h, 1)
                    fit = aspect > 0.8   # wider than ~4:5 → contain, don't crop
                except Exception:
                    pass
                kb = rng.choice(["kb0", "kb1", "kb2", "kb3"])
                parts.append(base.media_scene(i, sc, ctx, kb, d_i, fit=fit, aspect=aspect))
                continue
            sys.stderr.write(f"[rich] media scene {i}: no usable image/video — "
                             "falling back to a text card\n")
            sc = dict(sc, type="hook",
                      lines=sc.get("lines") or [str(sc.get("caption") or "")[:12] or "…"])
        parts.append(style.scene(i, sc, ctx))
    scenes_html = "\n".join(parts)
    subs_html = base.build_subs_html(scenes, durs, ctx["accent"], timings=timings, pad=PAD) \
        if not spec.get("no_subs") else ""
    bg = style.background(ctx)
    chrome = style.chrome(spec, ctx)
    doc = base.compose_document(css, bg, chrome, scenes_html, durs, subs_html)
    return doc, style, recent, ctx


# ----------------------------------------------------------------------------- render
def record_frames_subproc(html_path, durs, fps, workdir):
    """Run the frame capture in a FRESH python subprocess. Root cause of the
    2026-07-15 all-nighter: after build_audio's ~40 subprocess calls, a chromium
    launched from the SAME python process crashed on heavy pages 100% of the
    time ("Target crashed"), while an identical launch from a clean process
    succeeded 100%. Never pinned the exact poison (not pids, not fonts, not the
    bind mount, not time) — so the render simply always gets a clean process."""
    argf = os.path.join(workdir, "_render_args.json")
    with open(argf, "w", encoding="utf-8") as f:
        json.dump({"html": html_path, "durs": durs, "fps": fps, "workdir": workdir}, f)
    # NOTE: do NOT point TMPDIR at /var/tmp here — chromium's shared-memory
    # segments need tmpfs semantics and fail on overlayfs ("Unable to capture
    # screenshot"). SHM stays in /tmp (small, transient); only the bulky frame
    # JPEGs live in the /var/tmp workdir.
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "--_render-frames", argf],
                       capture_output=True, text=True)
    sys.stderr.write(r.stderr or "")
    for line in (r.stdout or "").splitlines():
        if line.startswith("__RENDER_RESULT__ "):
            _, frames_dir, n = line.split(" ", 2)
            return frames_dir, int(n)
    raise RuntimeError(f"render subprocess failed (rc={r.returncode}): "
                       f"{(r.stdout or '')[-300:]} {(r.stderr or '')[-300:]}")


def record_frames(html_path, durs, fps, workdir, _attempts=3):
    """Deterministic frame-by-frame render — every frame is exact, so the output
    is true smooth fps regardless of CPU (real-time screen recording dropped
    frames on this box, and blend-interpolating them back looked mushy).

    Python owns the clock: it calls __show(i) at scene boundaries and __step(ms)
    to advance every CSS animation/transition by exactly one frame, then
    screenshots. The page runs in #manual mode (no wall-clock timers).

    The whole capture retries on a fresh browser if chromium dies mid-render —
    the container's headless shell intermittently loses its GPU process right
    after (re)start (SwiftShader init flake, 2026-07-15); a relaunch reliably
    succeeds, so flaky-fatal becomes deterministic.
    """
    last_err = None
    for attempt in range(_attempts):
        try:
            return _record_frames_once(html_path, durs, fps, workdir)
        except Exception as e:
            last_err = e
            sys.stderr.write(f"[rich] browser render attempt {attempt + 1}/{_attempts} "
                             f"died ({str(e)[:160]}) — relaunching\n")
    raise last_err


def _record_frames_once(html_path, durs, fps, workdir):
    from playwright.sync_api import sync_playwright
    frames_dir = os.path.join(workdir, "frames")
    os.makedirs(frames_dir, exist_ok=True)
    total_s = sum(durs)
    n = max(int(round(total_s * fps)), 1)
    step_ms = 1000.0 / fps
    # scene start times -> frame index at which each scene begins
    starts, acc = [], 0.0
    for d in durs:
        starts.append(acc)
        acc += d
    boundaries = {max(int(round(s * fps)), 0): i for i, s in enumerate(starts)}

    with sync_playwright() as p:
        # channel="chromium" = the FULL chromium build, NOT chromium_headless_shell.
        # The headless shell's GPU/SwiftShader stack crash-looped on heavy pages in
        # this WSL container all night 2026-07-15 ("Target crashed" at the first
        # screenshot, env-dependent); the full build renders the same pages fine.
        # --disable-gpu: frame-exact screenshots need no GPU anyway.
        browser = p.chromium.launch(channel="chromium",
                                    args=["--no-sandbox", "--disable-dev-shm-usage",
                                          "--disable-gpu"])
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.goto("file://" + html_path + "#manual")
        page.wait_for_timeout(600)          # fonts/layout settle (wall clock, pre-timeline)
        try:                                # let clip metadata/first frames decode
            page.wait_for_function(
                "[...document.querySelectorAll('video')].every(v => v.readyState >= 2)",
                timeout=15000)
        except Exception:
            pass
        page.evaluate("window.__start()")
        cur_scene, scene_start_f = 0, 0
        for f in range(n):
            if f in boundaries and f > 0:
                cur_scene, scene_start_f = boundaries[f], f
                page.evaluate("window.__show(%d)" % cur_scene)
            if f > 0:
                page.evaluate("window.__step(%f)" % step_ms)
            # video clips don't follow the animation clock — seek to scene-local t
            local_t = (f - scene_start_f) / fps
            page.evaluate("window.__seekVideos(%d, %f)" % (cur_scene, local_t))
            # JPEG q90: ~5-8x smaller than PNG per frame. A 40s video is ~1200
            # frames — PNG frames ballooned the WSL disk (which only ever
            # grows) and helped fill the host drive.
            page.screenshot(path=os.path.join(frames_dir, "f%05d.jpg" % f),
                            type="jpeg", quality=90)
        browser.close()
    return frames_dir, n


def main():
    # hidden mode: clean-process frame capture (see record_frames_subproc)
    if len(sys.argv) == 3 and sys.argv[1] == "--_render-frames":
        with open(sys.argv[2], encoding="utf-8") as f:
            a = json.load(f)
        frames_dir, n = record_frames(a["html"], a["durs"], a["fps"], a["workdir"])
        print(f"__RENDER_RESULT__ {frames_dir} {n}")
        return 0

    ap = argparse.ArgumentParser(description="Build a rich motion-graphics 9:16 抖音 video.")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--style", default=None,
                    help="force a style: editorial|notebook|terminal|tabloid|keynote (default: rotate)")
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help="volc voice_type, OR Fish Audio reference_id when --tts fish")
    ap.add_argument("--tts", choices=["volc", "fish"], default="volc")
    ap.add_argument("--fish-model", default="s1")
    ap.add_argument("--speed", default="1.08",
                    help="TTS speed; 1.08 keeps the pace up (1.0 read as draggy)")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--bgm", default="auto",
                    help="background music: auto (rotate bundled PD tracks) | off | a track name/path")
    ap.add_argument("--skip-verify", action="store_true",
                    help="bypass the media vision gate (debug only)")
    ap.add_argument("--no-audio", action="store_true", help="render silent (debug)")
    ap.add_argument("--dump-html", default=None, help="also write the rendered HTML here (debug)")
    args = ap.parse_args()

    spec = json.load(open(args.spec, encoding="utf-8"))
    scenes = spec.get("scenes", [])
    if not scenes:
        print("ERROR: spec has no scenes", file=sys.stderr)
        return 2

    base.ensure_fonts()      # install bundled handwriting font (idempotent, for notebook style)

    # BOTH /tmp and /var/tmp in the agent container are small tmpfs mounts — a
    # 37s render's ~1100 frame JPEGs (~300MB) overflow them and the renderer
    # dies (headless_shell segfaulted, full chromium reports ENOSPC; this was
    # the root cause of the entire 2026-07-15 crash night). The overlay root
    # (~1TB) is the only real disk, so the work tree lives under /root/.cache.
    # (/root is itself the Windows bind mount, so ~/.cache is NOT overlay —
    # /var/cache is.)
    _work_base = "/var/cache/rich-work" if os.path.isdir("/var/cache") \
        else os.path.expanduser("~/.cache/rich-work")
    try:
        os.makedirs(_work_base, exist_ok=True)
    except OSError:
        _work_base = None
    workdir = tempfile.mkdtemp(prefix="rich-", dir=_work_base)
    if not args.skip_verify:
        validate_spec(spec)        # HARD GATE #0: dup narration / text-card stuffing / media starvation
    prepare_clips(spec, workdir)   # transcode media videos to webm + posters + fit
    if not args.skip_verify:
        verify_media(spec)         # HARD GATE: login walls / unrelated material refuse to render
    if args.no_audio:
        durs = [max(MIN_DUR, 2.6) for _ in scenes]
        voice_mp3 = None
        timings = None
    else:
        voice = args.voice
        if args.tts == "fish" and voice == DEFAULT_VOICE:
            voice = ""
        print(f"[rich] 1/3 {args.tts} voice per phrase ({len(scenes)} scenes, voice={voice or '(creds)'})...")
        voice_mp3, durs, timings = build_audio(scenes, workdir, voice, float(args.speed),
                                               provider=args.tts, fish_model=args.fish_model)
        voice_mp3 = mix_sfx(voice_mp3, scenes, durs, workdir)
        bgm = pick_bgm(spec, registry.make_rng(spec, args.out), args.bgm)
        if bgm:
            voice_mp3 = mix_bgm(voice_mp3, bgm, workdir)
            print(f"[rich] bgm={os.path.basename(bgm)} (vol {BGM_VOL}, PD/FreePD) + sfx")
        else:
            print("[rich] bgm=off")

    html_doc, style, recent, ctx = build_html(spec, durs, args.out, args.style, timings=timings)
    print(f"[rich] 2/3 style={style.id} ({style.label}) accent={ctx.get('accent')} "
          f"render motion graphics ({sum(durs):.1f}s)...")
    if args.dump_html:
        with open(args.dump_html, "w", encoding="utf-8") as f:
            f.write(html_doc)
    hf = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    hf.write(html_doc); hf.close()
    frames_dir, nframes = record_frames_subproc(hf.name, durs, args.fps, workdir)

    print(f"[rich] 3/3 encode {nframes} exact frames + mux...")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    # cover = the settled hook frame (frame-exact, no recorder garbage to hide)
    cover_t = max(0.4, min(1.0, (durs[0] - 0.2) if durs else 1.0))
    cover_idx = min(int(cover_t * args.fps), max(nframes - 1, 0))
    cover_png = os.path.join(frames_dir, "f%05d.jpg" % cover_idx)
    have_cover = os.path.exists(cover_png)

    cmd = ["ffmpeg", "-y", "-framerate", str(args.fps),
           "-i", os.path.join(frames_dir, "f%05d.jpg")]
    if voice_mp3:
        cmd += ["-i", voice_mp3, "-map", "0:v", "-map", "1:a",
                "-c:a", "aac", "-b:a", "192k", "-shortest"]
    else:
        cmd += ["-map", "0:v", "-an"]
    cmd += ["-vf", f"scale={W}:{H},format=yuv420p",
            "-c:v", "libx264", "-preset", "medium", "-crf", "19", args.out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("[rich] ffmpeg failed:\n" + r.stderr[-1200:] + "\n")
        return 1

    registry.commit(args.out, recent, style)     # advance rotation only on success

    abs_out = os.path.abspath(args.out)
    # Designed jpg cover = the composed hook frame, saved next to the mp4. 抖音
    # auto-uses frame-0 as the cover, but this gives a real jpg to set explicitly
    # (the 封面 input only accepts jpg/png/jpeg) + a controlled thumbnail.
    cover_jpg = os.path.splitext(abs_out)[0] + ".cover.jpg"
    if have_cover:
        subprocess.run(["ffmpeg", "-y", "-i", cover_png, "-q:v", "2", cover_jpg],
                       capture_output=True, text=True)
    cover_jpg = cover_jpg if os.path.exists(cover_jpg) else None

    dur = _ffprobe_dur(abs_out)
    print(f"[rich] DONE -> {abs_out}  ({dur:.1f}s, 1080x1920, style={style.id}, frame-exact {args.fps}fps)")
    if cover_jpg:
        print(f"[rich] COVER -> {cover_jpg}  (designed jpg cover, optional: set via 抖音 封面 input)")
    print(f"[rich] NEXT: browser_upload(file_paths=['{abs_out}'], selector='input[type=file]')  -- exact path")
    try:
        os.remove(hf.name)
    except OSError:
        pass
    shutil.rmtree(workdir, ignore_errors=True)   # frames + tts parts (mp4 is muxed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
