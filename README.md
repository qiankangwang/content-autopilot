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
| **`social-media/social-media-automation`** | Strategy — *what* to make, per platform | per-platform content guidelines, cron prompt template |
| **`social-media/content-publishing`** | Publishing — the *one* canonical upload path per platform + verify-before-claim | `browser_upload` modes, `browser_xhs_publish` / `browser_douyin_publish`, evidence gate |
| **`creative/douyin-shortform`** | Video — human-quality vertical short videos | `make_rich_video.py`, `make_xhs_cards.py`, `volc_tts.py`, `fish_tts.py` |

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
   vivi voice + motion   │                  │
                         ▼                  ▼
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
  `未确认发布`. A fabricated success is treated as a hard failure.
- **One canonical path, no flailing.** Exactly one upload method per platform. The
  skills explicitly rule out the dead ends (fresh sandbox Playwright, QR re-scans on
  an already-logged-in session, the `xhs` library / API-sign hacks).
- **Make it look human.** No flat text-on-gradient slides read by a robotic TTS.
  Videos are kinetic "keynote" motion graphics (code cards, big stats, before/after,
  bullets) voiced by a natural neural voice and auto-synced to it.
- **Anti-同质化.** The 小红书 card generator seeds a cohesive theme + layout from the
  topic, so daily posts stay visually distinct (batch-identical templates get
  throttled).
- **No spammy CTA.** Videos close on the *content* point — never "关注我 / 点赞 / 一键三连".

## Repository layout

```
skills/
  social-media/
    social-media-automation/
      SKILL.md
      references/
        content-examples.md       # post patterns per platform
        cron-prompt-template.md    # self-contained daily-content cron prompt
        zhihu-publishing.md        # 知乎-specific notes
    content-publishing/
      SKILL.md
  creative/
    douyin-shortform/
      SKILL.md
      scripts/
        make_rich_video.py         # spec.json → 1080×1920 H.264/AAC mp4 (one command)
        make_xhs_cards.py          # spec.json → 小红书 cover + carousel cards
        volc_tts.py                # 火山/豆包 TTS (vivi)  → mp3
        fish_tts.py                # Fish Audio TTS (character voices) → mp3
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
- **Playwright (Chromium)** — renders the HTML/CSS motion graphics
  (`pip install playwright && playwright install chromium`).
- **CJK fonts** — `fonts-noto-cjk` (the card generator needs a CJK font installed).
- **Pillow** — `make_xhs_cards.py` (`pip install pillow`).
- **A TTS provider** for narration (see below).
- **Hermes `browser_*` tools** — for the publishing skill (a logged-in browser session).

## Configuration

No secrets are committed. The TTS scripts read credentials from environment
variables, falling back to a small JSON creds file if the env is absent.

**火山引擎 / 豆包 (default voice `vivi`)** — `volc_tts.py`:

| Env var | Meaning |
|---------|---------|
| `VOLC_TTS_APPID`   | 火山控制台 TTS app APPID |
| `VOLC_TTS_TOKEN`   | Access Token |
| `VOLC_TTS_VOICE`   | voice_type (default `zh_female_vv_uranus_bigtts`) |
| `VOLC_TTS_CLUSTER` | default `volcano_tts` |

Creds-file fallback (when env is unset): `~/.config/volc_tts.json`
`{"appid": "...", "token": "...", "cluster": "volcano_tts"}`.

**Fish Audio (optional, for community character voices)** — `fish_tts.py`:
`FISH_API_KEY`, `FISH_TTS_MODEL` (`s1`|`s2-pro`), or `~/.config/fish_tts.json`.

## Using the scripts directly

```bash
# Build a video from a spec
python skills/creative/douyin-shortform/scripts/make_rich_video.py \
  --spec spec.json --out out.mp4

# Build a 小红书 cover + carousel
python skills/creative/douyin-shortform/scripts/make_xhs_cards.py \
  --spec cards.json --outdir ./cards
```

See the `douyin-shortform` SKILL.md for the full `spec.json` schema and scene types.

## License

[MIT](LICENSE).
