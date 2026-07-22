---
name: douyin-shortform
description: Make human-quality vertical short videos for 抖音 (rich motion-graphics + natural male voice).
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

⛔ **The PLUMBING is canonical — voice + render + mux are verified working**
(2026-06-18; 2026-06-19 smooth 30fps + clean cover; 2026-06-26 style engine). The voice
is 豆包/火山 **北京小爷** (NOT Kokoro, NOT edge-tts). The output is **information-dense
animated motion graphics** (NOT a static gradient slideshow, NOT AI-photo Ken Burns) —
do not revert those.

🎨 **The LOOK is no longer a single template — it ROTATES.** As of 2026-06-26 the visual
layer is a pluggable **style engine** (`scripts/richlib/`): each render the engine picks
one of several distinct visual languages — **editorial 杂志 / notebook 手写 / terminal 终端 /
tabloid 快报 / keynote 聚光** — by topic affinity + anti-repeat, and randomizes palette +
layout *within* that style. So consecutive videos rarely share a look and two same-style
videos still differ. **You no longer design the look — you write CONTENT; the engine
dresses it.** (This replaced the old single dark-keynote skin the user rejected as 太模板.)
2026-07-19 density overhaul: every style now fills the frame (structural background
furniture + bigger type + ghost glyphs — 大片留白 was rejected as 太丑); wide material
sits on the style's own canvas (no more black blur bars); subtitles and overlay cards
are skinned per style. 2026-07-22 anti-slideshow pass: scene boundaries rotate real
entry transitions (slide/zoom/rise/drop/cut, engine-assigned — never author these),
and AI motion b-roll (gen_scene_video.py) can carry beats that have no real footage.
Stock footage (fetch_stock_clip.py, Pexels) is the material backbone for atmosphere
shots, and every render ends with a cinematic finishing grade (grain + vignette +
tone; --no-grade to disable) that pulls mixed sources into one color world.

Produce short vertical videos for 抖音 that read like a real person made them. Each beat
is a designed, kinetic frame voiced by a natural neural voice and auto-synced to it. This
is what replaced the two old failures:

- ❌ **bare text-on-gradient slideshow + edge-tts/Kokoro** — the user rejected this as
  "不像真人" (robotic voice, flat obvious-AI frames). BANNED.
- ❌ **CogView AI photos + Ken Burns** (old `make_video.py`) — plastic "AI图" look. Gone.
- ✅ **rich motion graphics + 北京小爷 natural voice** (this skill) — the approved style.

> Do NOT confuse "kinetic motion graphics" (good, this skill) with "static gradient
> slides" (banned). The difference is real animation, real layouts (code/stat/compare),
> and the natural voice — not text centered on a flat gradient read by a robot voice.

## HARD RULES (read first)

1. The pipeline is **ONE command**: `scripts/make_rich_video.py --spec spec.json --out <path>`.
   It does everything: voices each phrase with 北京小爷 (prosody-paced), times the slides to the real audio,
   renders the motion graphics, mixes low-volume **background music** under the voice
   (bundled public-domain tracks, auto-rotated; bare narration reads as AI-made), and
   muxes → a finished 1080x1920 H.264/AAC mp4. Disable bgm only if the content demands
   it (`--bgm off` or `"bgm": "off"` in the spec).
2. **Voice = 北京小爷** (`zh_male_beijingxiaoye_moon_bigtts`, user-approved
   2026-07-12; 豆包/火山 via `scripts/volc_tts.py`, creds at
   `/root/.config/volc_tts.json`). It is the ENGINE DEFAULT — do NOT pass
   `--voice` (passing vivi shipped a wrong female-voice video on 07-13).
   NEVER edge-tts, NEVER Kokoro, NEVER faster-whisper. The script handles
   TTS — you only write the spec.
3. **You write CONTENT, the engine picks the LOOK.** Scene types (hook / stat / code /
   compare / bullets / outro) are a *vocabulary* — carry REAL information (show the code,
   the number, the comparison), and arrange them by a chosen narrative structure (see
   "Structure & voice"), NOT the same fixed march every time. Do NOT set `theme`/`accent`/
   `style` — the style engine rotates the visual language automatically.
4. **Don't hand-edit the scripts per video** (`make_rich_video.py`, `volc_tts.py`,
   `richlib/`) — they are the engine. If a build fails, fix your SPEC (text / scene
   fields), not the script. (Force a specific look only via the optional `style` field.)
5. **No 关注/点赞/三连/收藏 CTA** (user override 2026-06-19) — in 口播 *and* 画面. The
   outro lands the **content** point; never add a `cta` field and never say "关注我 /
   点赞 / 一键三连". (The script strips these as a safety net, but don't author them.)

## How to Run

Work inside `/root/hermes-content/douyin/`. Write a `spec.json`, then run one command:

```bash
SKILL_DIR="$(dirname "$(find ~/.hermes/skills -path '*/douyin-shortform/SKILL.md' | head -1)")"
python "$SKILL_DIR/scripts/make_rich_video.py" \
  --spec /root/hermes-content/douyin/<date>-<topic>/spec.json \
  --out  /root/hermes-content/douyin/<date>-<topic>.mp4
# On success it prints:  [rich] DONE -> <path> (Ns, 1080x1920)
```

The engine auto-rotates the look; add `--style editorial|notebook|terminal|tabloid|keynote`
only to force one. Do NOT pass `--voice` (engine default = 北京小爷). Use
container paths (`/root/...`), never host paths (`D:\...`). The script runs in the container.

## Spec format

`spec.json` is **content only** — the engine owns colors/layout. Global keys: `tag`
(small label, optional), `handle` (default `@yourhandle`), `title` (the topic — helps the engine
pick a fitting style + seed its variation; recommended), and optionally `style`
(`editorial|notebook|terminal|tabloid|keynote` to FORCE a look; omit to let it rotate).
Then `scenes: [...]`. **Every scene SHOULD have `say`** = the spoken narration for that
beat (the audio AND the per-scene duration come from it). Do NOT set `theme`/`accent` —
they are ignored now (the engine rotates the palette).

Scene types are a **vocabulary**, not a fixed running order — pick what carries the point,
sequence them by a chosen narrative structure (next section), and don't force a `stat`
when there's no number or `code` when it's not a code story:

| type | fields | use for |
| --- | --- | --- |
| `media` | `image` OR `video` (container path), `caption?` | **the backbone** — a REAL screenshot/photo or a **video clip** of the thing you're talking about. Images get a Ken Burns move; clips play muted under the voice (looped if shorter than the scene). Wide material auto-renders blurred-fill + contained sharp copy, nothing cropped |
| `diagram` | `title?`, `nodes` (2-6: `{label, sub?}` or plain strings), `edges` (labels between consecutive nodes, `""` for plain arrow) | **architecture/flow explanations** — a vertical chain whose nodes and arrows land ONE BY ONE, timed to the narration. Use whenever the script explains 架构/流程/链路 |
| `hook` | `lines` (1-2, ≤6 chars each), `eyebrow?` | the opening punch (first ~1.5s) |
| `stat` | `value` (e.g. "70%"), `label`, `unit?` | a single big number that lands |
| `code` | `code` (multi-line, `\n`), `lang`, `caption?` | show real code — syntax-highlighted card |
| `compare` | `before`, `after` | 之前 ❌ vs 现在 ✅ (one short line each) |
| `bullets` | `lines` (2-4 short), `head?` | a short list of steps/points |
| `outro` | `lines` (1-2) | the close — land the point itself, **NO 关注/点赞 CTA** |

**Speech-synced subtitles are automatic** — every scene's `say` is rendered as big
white bottom-third subtitles (numbers auto-highlighted), phrase by phrase in sync
with the voice. Don't put the narration on the slides; the subs carry it.

### Assemble freely — content decides the mix (NOT a template)

The scene types are LEGO bricks: real footage, page recordings, screenshots,
animated diagrams, data overlays ON footage, punch cards — **compose whatever
this specific story needs, and never the same assembly twice in a row.** The
one test for every scene: *is this the most informative thing the screen could
show while the voice says this line?* If a text card wins that test, use it;
if real footage wins, use that; if the point needs footage AND a number, put
an `overlay` on the media scene and show both at once.

Anti-PPT floor (the only hard rules): never two text cards back-to-back more
than once per video, never reuse one image across scenes, and the video as a
whole must LEAN on real material (footage/recordings/screenshots/diagrams) —
a deck of styled cards is the failure mode, not a style.

**`overlay` on media scenes** — footage + data on screen together:
`{"type":"media","video":"clip.webm","caption":"实录 · 发布会","overlay":{"value":"29/32","label":"小组赛命中"}}`
(`value` = big accent number; `label`/`text` = one short line under it.)

0.5. **Stock footage (first choice for atmosphere/setting shots).** Millions of
   professionally shot portrait HD clips (server rooms, city aerials, labs,
   factories, crowds, weather...), free commercial license:
   `python "$SKILL_DIR/scripts/fetch_stock_clip.py" --query "<english keywords>"
   --out <工作目录>/clipN.mp4` — keywords must be ENGLISH, 2-3 concrete nouns
   ("data center aisle", "chip factory macro"); `--index 1` picks the next
   candidate when the first doesn't fit. Event-specific imagery still needs
   real news footage (fetch_web_clip) — stock covers the LOOK, not the news.
1. **Page-scroll VIDEO clips (real motion from the actual page).** One
   command, runs in your terminal:
   `python "$SKILL_DIR/scripts/record_page_clip.py" --url <article/repo/product> --out /root/hermes-content/douyin/<dir>/clip1.webm --seconds 6`
   → a slow-scrolling phone-viewport capture of the real page (load lead-in
   auto-trimmed). Use for 1-2 media scenes per video. `--no-scroll` for a
   static hold; mp4 sources also accepted (auto-transcoded).
2. **Screenshots via the browser** (for the remaining media scenes):
   `browser_navigate` to the page → `browser_screenshot` → the file lands in
   `/root/.hermes/cache/screenshots/` (visible in your terminal). `cp` the
   newest file into your work dir, e.g.
   `cp "$(ls -t /root/.hermes/cache/screenshots/*.png | head -1)" /root/hermes-content/douyin/<date>-<topic>/shot1.png`
3. Direct image download (`curl -o`) works too when an article has a key image.
   For abstract/mechanism beats with NO real footage, generate an **AI motion
   b-roll clip** (documentary-style vertical, consistent grade):
   `python "$SKILL_DIR/scripts/gen_scene_video.py" --desc "<画面内容一句话>"
   --out <工作目录>/genN.mp4` → scene `video` field. **Hard cap 4 per video
   (2-3 recommended)**; generation takes 1-4 min per clip — poll patiently.
   A STATIC AI illustration (`gen_scene_image.py`, cap **1** per video) is the
   last resort when motion doesn't fit. Real material always outranks both.
   Both scripts write `.ai` sidecars the engine uses to enforce the caps;
   gen_scene_image auto-crops CogView's「AI生成」watermark strip.
4. **Look at each image before using it** (`vision_analyze`) — confirm it shows
   what you'll be saying over it, isn't a cookie banner / 404 / blank page /
   **a full-page wall of article text** (unreadable on a phone; the engine's
   vision gate rejects text walls — use the article's own figure or a diagram
   scene instead).
5. Reference in the spec: `{"type":"media","say":"...","video":"/root/.../clip1.webm","caption":"实录 · GitHub"}`
   or `{"type":"media","say":"...","image":"/root/.../shot1.png","caption":"来源 · 快科技"}`.
   `caption` is a small corner chip (source/label), NOT the narration.
6. **Explaining 架构/流程/链路? Use a `diagram` scene** instead of bullets — the
   nodes and arrows land one by one with the voice.

Example (the AI-写测试 reference video):

```json
{
  "tag": "AI编程", "handle": "@yourhandle", "title": "AI 帮我写测试",
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

## Structure & voice (kill the rhythm/voice template too)

Rotating visuals aren't enough — vary the **narrative shape** and the **spoken register**,
or it still reads as AI slop.

**Pick a structure** (fit the topic; try not to repeat the last video's):
- 悬念式 — 反常/痛点钩子 → 为什么 → 关键证据 → 转折 → 收
- 故事式 — 一个场景/「我…」 → 经过 → 发现 → 普适点
- 暴论式 — 反共识断言 → 大家为什么想错 → 论据 → 让步 → 立场
- 拆解式 — 一个结果 → 步骤 1/2/3 → 收(你也能)
- 辟谣式 — 「都说 X」 → 其实不是 → 真相
- 对比式 — A vs B → 各自 → 结论

**Pick a voice** (can follow the topic; vary it): 老友闲聊 / 冷静解读 / 开发者唠嗑 / 热血快评.

**Banned AI-tells** (口播 AND 画面) — never use: 「你有没有想过」「在这个 AI 时代」「众所周知」
「今天给大家分享」「话不多说」「随着…的发展」「不得不说」「家人们」「绝绝子」, and any
关注/点赞/三连/收藏. Run the script through the **humanizer** skill regardless.

## Authoring tips (this is where quality comes from)

0. **Do the homework before writing (depth is a HARD requirement).** Read 2-3
   different sources on the topic first. The script must contain ≥3 specific facts
   (exact numbers / names / timeline / causal chain), 1 judgment of your own (not a
   restatement of the news), and 1 detail most people don't know. Spend the ~30s
   going DEEP on one point, not skimming three. Self-check before building: "would
   someone who knows this field learn something?" If not, rewrite.
1. **Script first, then split into scenes.** Write the spoken narration (**25-35s
   total, ~90-130 chars** — 50s reads as draggy; hook in the first ~1.5s), run it
   through the **humanizer** skill to strip AI tells, THEN cut it into 6-10 short
   scene `say` lines.
2. **Write like a 抖音 up主, not a news anchor** (user verdict: 新闻稿腔不带劲):
   short spoken sentences, opinions and attitude, rhetorical turns (「结果呢?」
   「离谱的是」「你猜怎么着」), a new hook-point every ~8s (new fact / reversal /
   number punch). Open with the conflict or conclusion — ZERO background windup.
   End on a take that invites comments, not a summary. Banned: 「据报道」「近日」
   「值得注意的是」 and any 新闻联播 phrasing.
3. **通俗易懂 is a HARD requirement (user verdict 2026-07-13)** — write for
   someone who knows NOTHING about the field; every term must be translated
   into daily language: 「渗透率60%」→「每卖10辆新车,6辆是电车」;「平均车龄
   8.2年」→「一辆油车平均开到孩子小学毕业」. Numbers need a reference an
   ordinary person can feel. Self-check: would your 完全不懂行的朋友 follow
   every sentence?
4. **Pace like an editor, not a slide deck.** Most scenes 2-4s; let ONE scene
   breathe at 5-6s max. Types may repeat or be skipped; never use the same layout
   two scenes in a row. Match the scene type to the content: a number → `stat`,
   a code idea → `code` (show actual code), a before/after → `compare`, steps →
   `bullets`. Don't make every scene a `hook`.
5. **Big text ≤6 chars/line** (hook/outro `lines`). Longer auto-shrinks but reads worse.
6. **`code` snippets short** (≤6 lines, real-looking). Comments after `#`/`//` render
   dimmed; keywords/strings/numbers are auto-highlighted.
7. `say` is what's HEARD; the on-screen text is the emphasis, not a transcript — keep
   them aligned but the slide shows the punch, the voice carries the sentence.

## Identity gate (HARD)

Never put 学校 / 城市 / 年级 / 职位 in the video or narration. Self-label "技术博主" /
"AI工具玩家". De-identify any personal experience. Full self-check before building.

## Publishing 抖音 = full-auto with honesty gates (proven to land 2026-06-26)

The build pipeline is reliable. Full-auto publish HAS landed for real (post confirmed
live in 作品管理 with plays), but the platform side is flaky (upload binding, content
pre-check overload) — every step must verify, and every failure must be reported
honestly. ALWAYS confirm against 作品管理.

When auto-publishing (via **content-publishing** on the logged-in Camofox session):
`browser_navigate` the creator upload page →
`browser_upload(file_paths=[mp4], selector="input[type=file]", verify_text=["上传中","转码中","重新上传"])`
→ **trust the returned `bound` flag**: `bound:false` = the video did NOT register —
re-navigate to a fresh upload page and retry ONCE with `drop=true` (same `verify_text`);
never fill the form on an unbound upload → **wait for the upload to FINISH**
(no 上传中/转码中/百分比, 发布 button enabled) → fill title/description/hashtags with
`browser_type` → **`browser_douyin_publish(title="<the exact title>")`** → it waits out
the content pre-check (auto-clicks 重新检测, retries through 「检测人数过多」 busy toasts)
and confirms the post in 作品管理, returning published / needsVerify / unconfirmed(+reason).
`reason:"detection_busy"` → the draft is safe: `sleep 420` in the terminal, call it ONCE
more, then report honestly — **max 2 publish calls total**. NO QR, NO sandbox,
NO throwaway scripts.

⚠️ **作品管理 is the only proof of 已发布.** A 发布成功 toast / editor-URL rename is NOT
proof (it caused false 已发布 before). Only `published:true` (server saw it in 作品管理)
= 已发布; `unconfirmed:true` = 未确认发布.

⚠️ **风控 caveats:** 抖音 may demand an SMS code on 发布 — the agent canNOT bypass it;
report `未确认发布:需短信验证` + screenshot, never loop or fake 已发布. Repeated
auto-publishing also risks a 风控 logout; if a verify shows logged out, report it
honestly (a QR re-login then needs the user).

## Verification (before reporting done)

`OUT` = the exact `--out` path `make_rich_video.py` printed.

1. **Duration + audio:** `ffprobe -v error -show_entries format=duration:stream=codec_type -of default=nw=1 "$OUT"` → ~narration length, both a video and an audio stream.
2. **Resolution / fps:** 1080x1920, 30fps.
3. **Looks rich, not bare:** extract 2-3 frames
   (`ffmpeg -y -ss 3 -i "$OUT" -vframes 1 f.png`) across scenes and `vision_analyze`
   them — they must show designed layouts (code card / big number / compare / bullets
   with accent + depth), NOT flat centered text on black. If it looks like the old bare
   slideshow, the spec is too thin — add `code`/`stat`/`compare` scenes.
