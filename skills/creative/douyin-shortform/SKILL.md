---
name: douyin-shortform
description: Make human-quality vertical short videos for 抖音 (rich motion-graphics + vivi voice).
version: 2.0.0
platforms: [linux, macos, windows]
prerequisites:
  commands: [ffmpeg, ffprobe]
metadata:
  hermes:
    tags: [creative, video, douyin, shortform, motion-graphics, captions]
    related_skills: [humanizer, content-publishing]
    category: creative
    requires_toolsets: [terminal]
pinned: true
---

# Douyin Short-Form Video (rich motion graphics)

Produce short vertical videos for 抖音 (Douyin) that read like a real person made
them. Each beat is a designed, kinetic "keynote" frame — syntax-highlighted code
cards, big-number stats, before/after compares, animated bullet points — voiced by
a natural neural voice and auto-synced to it.

Two approaches are deliberately avoided:

- ❌ **bare text-on-gradient slideshow + robotic TTS** (edge-tts / Kokoro). Flat
  frames + a synthetic monotone read as low-effort and obviously AI-made.
- ❌ **AI-photo Ken Burns** (a generated still slowly panned). The "AI图" look is
  easy to spot and adds no information.
- ✅ **rich motion graphics + a natural voice** (this skill) — the approved style.

> Don't confuse "kinetic motion graphics" (good, this skill) with "static gradient
> slides" (avoid). The difference is real animation, real layouts (code/stat/compare),
> and a natural voice — not text centered on a flat gradient read by a robot voice.

## HARD RULES (read first)

1. The pipeline is **ONE command**: `scripts/make_rich_video.py --spec spec.json --out <path>`.
   It does everything: voices each scene, times the slides to the real audio,
   renders the motion graphics, and muxes → a finished 1080x1920 H.264/AAC mp4.
2. **Voice = vivi** (`zh_female_vv_uranus_bigtts`, 豆包/火山 via `scripts/volc_tts.py`).
   The script handles TTS — you only write the spec. Credentials load from env or a
   creds file (see `volc_tts.py`). `scripts/fish_tts.py` is an alternative provider
   for community character voices.
3. **Visuals = the spec's scene types** (hook / stat / code / compare / bullets / outro).
   Carry REAL information in the scenes (show the code, the number, the comparison) —
   not just a headline. No gradient slides, no AI photos.
4. **Do NOT modify the scripts** (`make_rich_video.py`, `volc_tts.py`) — they are
   tested and locked. If a build fails, fix your SPEC (text / scene fields), never
   the script.
5. **No 关注/点赞/三连/收藏 CTA** — in 口播 *and* 画面. The outro lands the **content**
   point; never add a `cta` field and never say "关注我 / 点赞 / 一键三连". (The
   script strips these as a safety net, but don't author them — a hard-sell close
   reads as spam and hurts retention.)

## How to Run

Write a `spec.json`, then run one command:

```bash
SKILL_DIR="$(dirname "$(find ~/.hermes/skills -path '*/douyin-shortform/SKILL.md' | head -1)")"
python "$SKILL_DIR/scripts/make_rich_video.py" \
  --spec /root/hermes-content/douyin/<date>-<topic>/spec.json \
  --out  /root/hermes-content/douyin/<date>-<topic>.mp4
# On success it prints:  [rich] DONE -> <path> (Ns, 1080x1920)
```

Override the voice with `--voice <voice_type>` (default vivi). Use container paths
(`/root/...`) when the script runs inside a container; never mix in host paths.

## Spec format

`spec.json` drives the whole video. Global keys: `tag` (accent pill, top-left, optional),
`theme` ("dark"|"light"), `accent` (hex, default 抖音-red `#FF2E4D`), `handle`
(default `@yourhandle`). Then `scenes: [...]`. **Every scene SHOULD have `say`** = the
spoken narration for that beat (the audio AND the per-scene duration come from it).

Scene types (pick what carries the point — mix them, that variety IS the quality):

| type | fields | use for |
| --- | --- | --- |
| `hook` | `lines` (1-2, ≤6 chars each), `eyebrow?` | the opening punch (first ~1.5s) |
| `stat` | `value` (e.g. "70%"), `label`, `unit?` | a single big number that lands |
| `code` | `code` (multi-line, `\n`), `lang`, `caption?` | show real code — syntax-highlighted card |
| `compare` | `before`, `after` | 之前 ❌ vs 现在 ✅ (one short line each) |
| `bullets` | `lines` (2-4 short), `head?` | a short list of steps/points |
| `outro` | `lines` (1-2) | the close — land the point itself, **NO 关注/点赞 CTA** |

Example:

```json
{
  "tag": "AI编程", "theme": "dark", "accent": "#FF2E4D", "handle": "@yourhandle",
  "scenes": [
    {"type":"hook","say":"写完功能,最烦的就是写测试。","eyebrow":"AI 编程","lines":["写完功能","最烦写测试"]},
    {"type":"compare","say":"以前纯手写测试能磨一天半,现在让 AI 起草十分钟。","before":"手写测试 · 1.5 天","after":"AI 起草 · 10 分钟"},
    {"type":"code","say":"我把要测的函数丢给它,三秒出一份骨架。","lang":"python","caption":"3 秒出测试骨架",
     "code":"def test_pay():\n    assert pay(100) == 100   # 正常\n    assert pay(0) == 0       # 边界\n    with raises(Error):\n        pay(-1)              # 异常"},
    {"type":"stat","say":"现在大概七成的测试初稿我都让 AI 先写。","value":"70%","label":"测试初稿 AI 先写"},
    {"type":"bullets","say":"我只做三件事:读它漏的边界,补真实用例,收紧太松的断言。","head":"我只做三件事","lines":["读 AI 漏的边界","补几个真实 case","收紧太松的断言"]},
    {"type":"outro","say":"把省下的时间,拿去啃真正难的逻辑。","lines":["省下的时间","啃真正难的逻辑"]}
  ]
}
```

## Authoring tips (this is where quality comes from)

1. **Script first, then split into scenes.** Write the spoken narration (≤40s total,
   ~110-160 chars, hook in the first ~1.5s), run it through the **humanizer** skill to
   strip AI tells, THEN cut it into 5-8 scene `say` lines.
2. **Match the scene type to the content.** A number → `stat`. A code idea → `code`
   (show actual code, not a description). A before/after → `compare`. Steps → `bullets`.
   Don't make every scene a `hook` — the variety is the point.
3. **Big text ≤6 chars/line** (hook/outro `lines`). Longer auto-shrinks but reads worse.
4. **`code` snippets short** (≤6 lines, real-looking). Comments after `#`/`//` render
   dimmed; keywords/strings/numbers are auto-highlighted.
5. `say` is what's HEARD; the on-screen text is the emphasis, not a transcript — keep
   them aligned but the slide shows the punch, the voice carries the sentence.

## Identity gate (HARD)

Never put 学校 / 城市 / 年级 / 职位 in the video or narration. Self-label "技术博主" /
"AI工具玩家". De-identify any personal experience. Full self-check before building.

## Publishing 抖音

Publish via the **content-publishing** skill on the logged-in browser session:
`browser_navigate` the creator upload page →
`browser_upload(file_paths=[mp4], selector="input[type=file]")` (retry `drop=true`
if the 作品描述/发布 editor doesn't appear in ~10s) → fill title/description/hashtags
with `browser_type` → **`browser_douyin_publish()`** → verify the post is live. NO QR,
NO sandbox, NO throwaway scripts.

⚠️ **风控 caveats:** 抖音 may demand an SMS code on 发布 — the agent canNOT bypass it;
if so, report `未确认发布:需短信验证` + screenshot, never loop or fake 已发布. Repeated
auto-publishing also risks a 风控 logout; if a verify shows logged out, report it
honestly (a QR re-login then needs the account owner). (小红书 图文 and 知乎 text — see
`content-publishing`.)

## Verification (before reporting done)

`OUT` = the exact `--out` path `make_rich_video.py` printed.

1. **Duration + audio:** `ffprobe -v error -show_entries format=duration:stream=codec_type -of default=nw=1 "$OUT"` → ~narration length, both a video and an audio stream.
2. **Resolution / fps:** 1080x1920, 30fps.
3. **Looks rich, not bare:** extract 2-3 frames
   (`ffmpeg -y -ss 3 -i "$OUT" -vframes 1 f.png`) across scenes and inspect them —
   they must show designed layouts (code card / big number / compare / bullets with
   accent + depth), NOT flat centered text on black. If it looks like a bare
   slideshow, the spec is too thin — add `code`/`stat`/`compare` scenes.
