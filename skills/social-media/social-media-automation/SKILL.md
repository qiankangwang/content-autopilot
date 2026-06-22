---
name: social-media-automation
description: Content strategy for 小红书/知乎/抖音.
version: 3.0.0
platforms: [windows, linux, macos]
metadata:
  hermes:
    tags: [social-media, content, xiaohongshu, zhihu, douyin]
    related_skills: [content-publishing, douyin-shortform, humanizer]
---

# Social Media Content Strategy

How to plan and write good content for 小红书 (Xiaohongshu), 知乎 (Zhihu), and
抖音 (Douyin). This skill is about WHAT to make. For HOW to publish (the one
canonical upload path + verify-before-claim), use **content-publishing**. For HOW
to make a good video, use **douyin-shortform**.

## When to Use

Whenever you create content for these platforms: choosing an angle, writing copy,
or checking it before it goes out.

## Core Principles

1. **One insight per post.** Don't write overviews. Find one interesting angle and go deep.
2. **Data + opinion.** Every post needs a concrete number, a specific tool name, or a real observation. No vague "AI is changing everything."
3. **Read the room.** Before writing, browse the platform for 2 minutes to see what's trending and how top posts are structured *today*. Don't follow a fixed template — platforms change.
4. **No filler.** If a post can be cut by 30% without losing value, cut it.
5. **De-slop the copy.** Run every script / note / answer through the **humanizer** skill before publishing — strip emoji-bullets, rule-of-three, em-dashes, and hype.

## Content Guidelines

### Xiaohongshu (小红书)
- Title: ≤20 chars. State the value, not clickbait.
- Body: specific tool + exact steps + concrete result ("我用X做了Y，结果是Z").
- One post = one actionable tip someone can try in 5 minutes.
- Cover: clean, portrait, text overlay in the top third.

### Zhihu (知乎)
- Find questions with real engagement (views > 1000, non-joke answers).
- Lead with your conclusion, then explain why.
- 800–2000 Chinese characters. If it needs more, the question is too broad — pick a narrower one.
- Structure: 结论 → 为什么 → 怎么做 → 局限/反方观点.

### Douyin (抖音)
- 15–35 seconds. Hook in the first ~1.5 seconds. One idea per video.
- CTA in the last 5 seconds: "评论区说说你…" not "扣1私你工具名" (spammy).
- **Quality bar:** never ship text-on-gradient slides with a robotic TTS voice
  (reads as low-effort and obviously AI-made). Use the **douyin-shortform** skill:
  natural voice + real visuals (generated keyframes / screen-recording style /
  motion) + word-level captions, 1080×1920, 30fps.
- **Scrap-and-rebuild signals**: "不像真人", "视频没看到" (MEDIA attachment failed),
  "这个视频不好" — any of these means scrap the current video and rebuild with
  the douyin-shortform skill. Do NOT attempt minor edits on a rejected video.
- **No QR for publishing** — `browser_upload` handles uploads in the logged-in
  session (see content-publishing). Don't fall back to QR screenshots. And don't
  spam the messaging channel with a message per step — it rate-limits and images
  stop arriving.

## Publishing

Do NOT improvise a publishing flow here. Hand off to the **content-publishing**
skill — the ONE canonical path is the logged-in browser session + the
`browser_upload` tool (no QR, no sandbox Playwright, no xhs library). Per platform:
- **抖音 video** → build with `douyin-shortform` (`make_rich_video.py`), then publish
  via `content-publishing` (browser_upload → browser_douyin_publish → verify). If
  抖音 demands SMS on 发布, report 未确认发布:需短信验证 + screenshot, never fake.
  Watch for 风控 logout.
- **小红书 图文** → `browser_upload(file_paths=[...], drop=true)` — drag-drop only; a
  normal upload returns success but silently leaves the editor empty.
- **知乎** → no upload (text editor only).
Verify-before-claim: never say 已发布 without a permalink/DOM/screenshot proof.

## Supporting Files

- `references/content-examples.md` — Example post patterns across platforms
- `references/cron-prompt-template.md` — Self-contained cron prompt template
- `references/zhihu-publishing.md` — 知乎-specific publishing notes

## Pitfalls

- Never report 已发布 from "I clicked the button." Evidence first (see content-publishing).
- Don't reinvent the upload path or re-scan QR when a session is already logged in.
- **抖音 upload**: `browser_upload(file_paths=[...], selector="input[type=file]")`
  (the hidden input takes the file directly). Only if the page truly does not
  advance, retry with `drop=true`. NO QR, NO sandbox.
- **小红书 图文 upload REQUIRES `drop=true`; 抖音 video must NOT use drop.** 小红书's
  uploader ignores `setInputFiles` (a normal upload reports success but the editor
  stays EMPTY), so always `browser_upload(..., drop=true)` for 小红书 images. 抖音
  videos use `selector="input[type=file]"` (NOT drop).
- **抖音 video quality**: build with the **douyin-shortform** skill —
  `make_rich_video.py` (rich motion graphics: code cards / stats / compares /
  bullets + a natural 豆包 **vivi** voice, auto-synced). Never edge-tts, never
  Kokoro, never gradient slides, never AI-photo Ken Burns.
