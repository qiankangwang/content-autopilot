# auto-content-skills

A small, opinionated **skill pack for the [Hermes agent](https://github.com/NousResearch/hermes-agent)** that turns it into a hands-off content bot for the three big Chinese platforms — **小红书 (Xiaohongshu), 知乎 (Zhihu), and 抖音 (Douyin)**.

It bundles the whole loop an autonomous run actually needs: *what to make* (per-platform content strategy), *how to make it* (a one-command rich-motion-graphics video builder + a 小红书 card generator), and *how to ship it* (one canonical upload path per platform, with a strict **verify-before-claim** honesty gate so the agent never reports a post as live without proof).

> **Status:** these are Hermes agent skills, not a standalone CLI. They assume the
> agent's `browser_*` tools (a persistent, logged-in browser session) and a
> terminal/container backend. The Python scripts under `douyin-shortform/scripts`
> run on their own and are useful anywhere.

## The three skills

| Skill | Job | Key pieces |
|-------|-----|-----------|
| **`social-media/social-media-automation`** | Strategy — *what* to make, per platform | per-platform content guidelines, identity-leak self-check, cron prompt template |
| **`social-media/content-publishing`** | Publishing — the *one* canonical upload path per platform + verify-before-claim | `browser_upload` modes (upload binding via `verify_text`/`bound`), `browser_xhs_publish` / `browser_douyin_publish` publish contract, evidence gate |
| **`creative/douyin-shortform`** | Video — human-quality vertical short videos | `make_rich_video.py` + the `richlib/` style engine, B-roll helpers, `make_xhs_cards.py`, TTS scripts |

## How the flow fits together

```
                 social-media-automation
                 (pick angle, write copy)
                            │
              ┌─────────────┴──────────────┐
              ▼                             ▼
      douyin-shortform               (小红书 cards via
   make_rich_video.py  ─┐            make_xhs_cards.py)
   spec.json → 1080×1920 │                  │
   natural voice + BGM   │                  │
   + rotating styles     ▼                  ▼
                    content-publishing
        browser_upload → browser_xhs_publish / browser_douyin_publish
                    → verify-before-claim (URL / DOM / screenshot)
                            │
                            ▼
                  已发布 (with evidence) or 未确认发布
```

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
  visual languages per render (editorial / notebook / terminal / tabloid / keynote)
  by topic affinity + anti-repeat, then randomizes palette and layout within it —
  consecutive videos rarely share a look. The 小红书 card generator seeds a cohesive
  theme + layout from the topic for the same reason (batch-identical templates get
  throttled).
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
  social-media/
    social-media-automation/
      SKILL.md
      references/
        content-examples.md        # post patterns per platform
        cron-prompt-template.md    # self-contained daily-content cron prompt
        zhihu-publishing.md        # 知乎-specific notes
    content-publishing/
      SKILL.md
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
```

## Install

Drop the skills into your Hermes skills directory (it walks the tree recursively):

```bash
git clone https://github.com/qiankangwang/auto-content-skills.git
cp -r auto-content-skills/skills/* ~/.hermes/skills/
# (or point HERMES_SKILLS_DIR at the cloned skills/ folder)
```

The agent then loads `social-media-automation`, `content-publishing`, and
`douyin-shortform` like any other skill.

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

## License

[MIT](LICENSE).
