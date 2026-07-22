# content-autopilot

A small, opinionated **skill pack for the [Hermes agent](https://github.com/NousResearch/hermes-agent)** that turns it into a hands-off **抖音 (Douyin) video bot** — from topic to a finished, human-looking vertical short video to a *verified* publish — with 小红书 (Xiaohongshu) cards and 知乎 (Zhihu) answers included as secondary channels.

The core loop is Douyin-first: *make* the video with a one-command rich-motion-graphics builder (rotating visual styles, natural neural voice, background music, real B-roll), then *ship* it through one canonical, fully-automated publish path with a strict **verify-before-claim** honesty gate — the agent never reports a post as live unless it actually shows up in 作品管理.

> **Status:** these are Hermes agent skills, not a standalone CLI. They assume the
> agent's `browser_*` tools (a persistent, logged-in browser session) and a
> terminal/container backend. The Python scripts under `douyin-shortform/scripts`
> run on their own and are useful anywhere.

## The Douyin pipeline

### 1. Make the video — `creative/douyin-shortform`

One command turns a `spec.json` into a finished 1080×1920 H.264/AAC mp4:

```bash
python skills/creative/douyin-shortform/scripts/make_rich_video.py \
  --spec spec.json --out out.mp4
```

- **Rotating style engine (`richlib/`).** Each render picks one of five visual
  languages (editorial 杂志 / notebook 手写 / terminal 终端 / tabloid 快报 /
  keynote 聚光) by topic affinity + anti-repeat, then randomizes palette and
  layout within it — consecutive videos rarely share a look. You write content;
  the engine dresses it.
- **Real material, not AI wallpaper.** `media` scenes (page-scroll recordings,
  web video clips, screenshots — with data overlays) and step-by-step `diagram`
  scenes mix with kinetic text cards. B-roll helpers included:
  `record_page_clip.py` (scrolling page capture → webm) and `fetch_web_clip.py`
  (yt-dlp download + cut of official footage). `gen_scene_image.py` is the
  flat-illustration fallback when no real material exists.
- **Natural voice + BGM.** Narration is voiced by a natural neural voice
  (火山/豆包 TTS via `volc_tts.py`, with per-scene emotion tags; Fish Audio
  character voices via `fish_tts.py` optional), and low-volume background music
  is auto-rotated by content mood and ducked under the speech.
- **The engine enforces quality.** It refuses to render specs with duplicated
  narration, text-card stuffing, or too little real material, and runs an
  optional vision check that rejects login walls / webpage junk / irrelevant
  media — printing a per-scene repair work order instead of shipping a bad video.

See the `douyin-shortform` SKILL.md for the full `spec.json` schema and scene types.

### 2. Ship it — `social-media/content-publishing`

One canonical upload path, fully automated, no human in the loop unless 风控
demands one:

- **Upload with binding verification.** `browser_upload` sets the file on 抖音's
  hidden `<input type=file>` in the already-logged-in session and confirms via
  `verify_text` markers that the SPA actually accepted it, returning
  `bound:true/false` — a rendered publish form alone is *not* proof the video
  bound (that caused the old draft-only failures).
- **Publish with `browser_douyin_publish`, not a bare click.** It waits out
  upload/transcode and the content pre-check (auto-clicking 重新检测, retrying
  through 「检测人数过多」 busy toasts), trusted-clicks 发布, then confirms the
  post is actually listed in **作品管理**.
- **Detection-busy handling.** On `reason:"detection_busy"` the draft is safe:
  wait ~7 minutes, retry once, and stop at a maximum of two publish calls —
  never loop.
- **作品管理 is the only authority.** A 发布成功 toast or the editor URL renaming
  is *not* proof (抖音 renames its own URL, which previously caused false 已发布
  reports). `published:true` means the post was seen in 作品管理 (审核中 counts);
  an SMS/captcha 风控 wall is reported honestly as 「未确认发布」 with a
  screenshot, never faked.

## How the flow fits together

```
                 social-media-automation
                 (pick angle, write copy)
                            │
                            ▼
                    douyin-shortform
                  make_rich_video.py
              spec.json → 1080×1920 mp4          (secondary: 小红书 cards
              natural voice + BGM                 via make_xhs_cards.py,
              + rotating styles                   知乎 answers as text)
                            │                               │
                            ▼                               ▼
                    content-publishing
     browser_upload (bound:true) → browser_douyin_publish → 作品管理 check
               (小红书: drop-upload → browser_xhs_publish; 知乎: editor)
                            │
                            ▼
                  已发布 (with evidence) or 未确认发布
```

## The three skills

| Skill | Job | Key pieces |
|-------|-----|-----------|
| **`creative/douyin-shortform`** | Video — human-quality vertical short videos | `make_rich_video.py` + the `richlib/` style engine, B-roll helpers, TTS scripts, `make_xhs_cards.py` |
| **`social-media/content-publishing`** | Publishing — the *one* canonical upload path per platform + verify-before-claim | `browser_upload` modes (upload binding via `verify_text`/`bound`), `browser_douyin_publish` / `browser_xhs_publish` publish contract, evidence gate |
| **`social-media/social-media-automation`** | Strategy — *what* to make, per platform | per-platform content guidelines, identity-leak self-check, cron prompt template |

## Also included: 小红书 & 知乎

The same strategy + publishing skills cover the two secondary platforms:

- **小红书 image notes** — `make_xhs_cards.py` builds a designed cover + 干货
  carousel from a spec JSON, seeding a cohesive theme + layout from the topic
  (batch-identical templates get throttled). Upload **must** use
  `browser_upload(..., drop=true)` — 小红书's uploader only reacts to a drag-drop
  `DataTransfer` and silently ignores `setInputFiles`. Publishing goes through
  `browser_xhs_publish` (the 发布 button is a closed-shadow element whose
  clickable pill is right-anchored — center-clicking misses), verified in
  笔记管理.
- **知乎 answers** — plain text through the logged-in editor, no file upload;
  platform-specific notes in `references/zhihu-publishing.md`.

## Design principles

- **Verify before you claim.** "I clicked 发布" is not "已发布". A post is only
  reported live with a permalink, a DOM change, or a screenshot. No evidence →
  `未确认发布`. A fabricated success is treated as a hard failure. (For 抖音 the
  only accepted proof is the post showing up in 作品管理.)
- **One canonical path, no flailing.** Exactly one upload method per platform. The
  skills explicitly rule out the dead ends (fresh sandbox Playwright, QR re-scans on
  an already-logged-in session, the `xhs` library / API-sign hacks).
- **Make it look human.** No flat text-on-gradient slides read by a robotic TTS.
  Videos lean on real material (page-scroll recordings, web video clips, screenshots,
  animated diagrams) mixed with kinetic text cards, voiced by a natural neural voice
  with low-volume background music ducked under the speech.
- **Rotate the look.** The video builder's `richlib/` style engine picks one of five
  visual languages per render by topic affinity + anti-repeat, then randomizes
  palette and layout within it — consecutive videos rarely share a look. The 小红书
  card generator seeds a cohesive theme + layout from the topic for the same reason.
- **The engine enforces quality.** `make_rich_video.py` refuses to render specs with
  duplicated narration, text-card stuffing, or too little real material, and runs an
  optional vision check that rejects login walls / webpage junk / irrelevant media —
  printing a per-scene repair work order instead of shipping a bad video.
- **No spammy CTA.** Videos close on the *content* point — never "关注我 / 点赞 / 一键三连".
- **No identity leaks.** Content never names a school / city / grade / employer; the
  strategy skill ships a grep self-check to run before every publish.

## Repository layout

```
skills/
  creative/
    douyin-shortform/
      SKILL.md
      scripts/
        make_rich_video.py         # spec.json → 1080×1920 H.264/AAC mp4 (one command)
        richlib/                   # rotating visual-style engine (5 styles + registry)
        record_page_clip.py        # scrolling page capture → webm B-roll clip
        fetch_web_clip.py          # yt-dlp download + cut → webm clip (official footage)
        gen_scene_image.py         # flat-illustration fallback when no real material exists
        make_xhs_cards.py          # spec.json → 小红书 cover + carousel cards
        volc_tts.py                # 火山/豆包 TTS (+ per-scene emotion tags) → mp3
        fish_tts.py                # Fish Audio TTS (character voices) → mp3
        assets/
          bgm/                     # user-supplied public-domain music (see its README)
          fonts/                   # user-supplied handwriting font (see its README)
  social-media/
    content-publishing/
      SKILL.md
    social-media-automation/
      SKILL.md
      references/
        content-examples.md        # post patterns per platform
        cron-prompt-template.md    # self-contained daily-content cron prompt
        zhihu-publishing.md        # 知乎-specific notes
```

## Install

Drop the skills into your Hermes skills directory (it walks the tree recursively):

```bash
git clone https://github.com/wangkant/content-autopilot.git
cp -r content-autopilot/skills/* ~/.hermes/skills/
# (or point HERMES_SKILLS_DIR at the cloned skills/ folder)
```

The agent then loads `douyin-shortform`, `content-publishing`, and
`social-media-automation` like any other skill.

## Requirements

- **`ffmpeg` / `ffprobe`** — video assembly and probing (`make_rich_video.py`).
- **Playwright (Chromium)** — renders the HTML/CSS motion graphics and records
  page clips (`pip install playwright && playwright install chromium`).
- **`yt-dlp`** — only for `fetch_web_clip.py` (cutting official web footage).
- **CJK fonts** — `fonts-noto-cjk` (the card generator needs a CJK font installed).
- **Pillow** — `make_xhs_cards.py` (`pip install pillow`).
- **A TTS provider** for narration (see below).
- **Hermes `browser_*` tools** — for the publishing skill (a logged-in browser session).

## Assets (not committed)

Two asset directories under `douyin-shortform/scripts/assets/` are intentionally
empty — supply your own files:

- **`assets/bgm/`** — public-domain background-music mp3s (e.g. from
  [FreePD](https://freepd.com/)), named `chill-*.mp3` / `upbeat-*.mp3` so the
  mood-based auto-rotation can pick by content energy. Optional; without tracks
  the videos render voice-only.
- **`assets/fonts/`** — a handwriting CJK font for the notebook style:
  [LXGW WenKai](https://github.com/lxgw/LxgwWenKai) (SIL OFL 1.1). Optional;
  without it the notebook style falls back to sans.

## Configuration

No secrets are committed. The TTS scripts read credentials from environment
variables, falling back to a small JSON creds file if the env is absent.

**火山引擎 / 豆包** — `volc_tts.py`:

| Env var | Meaning |
|---------|---------|
| `VOLC_TTS_APPID`   | 火山控制台 TTS app APPID |
| `VOLC_TTS_TOKEN`   | Access Token |
| `VOLC_TTS_VOICE`   | voice_type (the video pipeline defaults to `zh_male_beijingxiaoye_moon_bigtts`) |
| `VOLC_TTS_CLUSTER` | default `volcano_tts` |

Creds-file fallback (when env is unset): `~/.config/volc_tts.json`
`{"appid": "...", "token": "...", "cluster": "volcano_tts"}`.

**Fish Audio (optional, for community character voices)** — `fish_tts.py`:
`FISH_API_KEY`, `FISH_TTS_MODEL` (`s1`|`s2-pro`), or `~/.config/fish_tts.json`.

**Zhipu (optional)** — the media vision gate in `make_rich_video.py` and the
illustration fallback `gen_scene_image.py` read `~/.config/zhipu_vision.json`
(`{"base_url": "...", "api_key": "...", "model": "glm-4v-flash"}`). Without it
the vision gate is skipped (with a warning) and illustration generation is
unavailable.

## Using the scripts directly

```bash
# Build a video from a spec (style auto-rotates; --style forces one)
python skills/creative/douyin-shortform/scripts/make_rich_video.py \
  --spec spec.json --out out.mp4

# Record a scrolling page capture as B-roll
python skills/creative/douyin-shortform/scripts/record_page_clip.py \
  --url https://github.com/x/y --out clip1.webm --seconds 6

# Cut a clip out of an official web video
python skills/creative/douyin-shortform/scripts/fetch_web_clip.py \
  --url <video page or mp4 url> --out clip2.webm --start 12 --seconds 8

# Build a 小红书 cover + carousel
python skills/creative/douyin-shortform/scripts/make_xhs_cards.py \
  --spec cards.json --outdir ./cards
```

See the `douyin-shortform` SKILL.md for the full `spec.json` schema and scene types
(including `media` scenes with data overlays and step-by-step `diagram` scenes).

## Disclaimer · 免责声明

This project is an automation **reference for personal/experimental use**. If you
run it, you are the operator and you own the consequences:

- **Platform terms.** Automated posting and browser automation may conflict with
  the user agreements of 抖音 / 小红书 / 知乎. Accounts can be rate-limited,
  restricted, or banned. Use a burner/secondary account if unsure; the authors
  and contributors accept no liability for account or business losses.
  自动化发布可能违反平台用户协议,账号可能被限流、限权或封禁,后果由使用者自行承担。
- **AI-content labeling.** Chinese regulation (《人工智能生成合成内容标识办法》,
  effective 2025-09-01) requires AI-generated content to be labeled. The publish
  flow keeps 抖音's AI 声明 enabled — do **not** disable it, and follow whatever
  labeling rules apply in your jurisdiction.
  发布流程默认勾选平台的 AI 生成声明,请勿关闭。
- **Content responsibility.** You are responsible for what you publish: factual
  accuracy, no misleading claims, and the rights to any material the pipeline
  ingests (B-roll footage, screenshots, music you place in `assets/bgm/`, fonts).
  `fetch_web_clip.py` is for short quotes of official/public footage — respect
  copyright and each source's terms.
  发布内容的真实性、版权(素材/音乐/字体/引用片段)由使用者自行负责。
- **No warranty.** Provided *as is* under the MIT license, without warranty of
  any kind. Nothing here is legal advice.

## License

[MIT](LICENSE).
