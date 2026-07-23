---
name: douyin-shortform
description: Make human-quality vertical short videos for 抖音 — one "Dark Matter" precision-instrument look, natural male voice, evidence-dense motion graphics.
version: 3.0.0
platforms: [linux, macos, windows]
prerequisites:
  commands: [ffmpeg, ffprobe]
metadata:
  hermes:
    tags: [creative, video, douyin, shortform, motion-graphics, captions, dark-matter]
    related_skills: [humanizer, content-publishing]
    category: creative
    requires_toolsets: [terminal]
pinned: true
---

# Douyin Short-Form Video — "Dark Matter" (v3)

> This file is an **operations manual for a night-time automation agent**, not a
> whitepaper. Read it top to bottom, do the steps, keep the command-line examples.

⛔ **The PLUMBING is canonical — voice + render + mux are verified working.** The
voice is 豆包/火山 **北京小爷** (NOT Kokoro, NOT edge-tts). The output is **evidence-
dense animated motion graphics** (NOT a static gradient slideshow, NOT AI-photo Ken
Burns). Do not revert those.

🎨 **The LOOK is now ONE flagship system: "Dark Matter."** As of 2026-07-24 the old
5-skin rotation (editorial / notebook / terminal / tabloid / keynote) is **retired as
the primary look**. Every render uses the single `obsidian` visual language: a
precision instrument in the dark where data gets measured, lit, and proven (回形针
evidence density, Vox highlight blocks, oscilloscope/terminal restraint). Color only
ever **encodes meaning**, never decorates. The old style names still exist on disk
and are reachable via `--style <name>` **for rollback only** if an obsidian render
breaks — they are not part of normal operation. **You still don't hand-author the
palette or layout — you write CONTENT; the engine dresses it in Dark Matter.**

This is what replaced the two old failures:

- ❌ **bare text-on-gradient slideshow + edge-tts/Kokoro** — rejected as "不像真人".
  BANNED.
- ❌ **CogView AI photos + Ken Burns** (old `make_video.py`) — plastic "AI图" look. Gone.
- ✅ **Dark Matter motion graphics + 北京小爷 natural voice** (this skill) — approved.

> Do NOT confuse "kinetic motion graphics" (good) with "static gradient slides"
> (banned). The difference is real animation, real evidence (screenshots-as-evidence-
> cards / stat roll-ups / track-line diagrams), and the natural voice.

## HARD RULES (read first)

1. **One command:** `scripts/make_rich_video.py --spec spec.json --out <path>`. It
   voices each phrase with 北京小爷 (prosody-paced), times slides to the real audio,
   renders the Dark Matter motion graphics, mixes low-volume **background music**
   under the voice (bundled public-domain tracks, auto-rotated; bare narration reads
   as AI-made), and muxes → a finished 1080x1920 H.264/AAC mp4. Disable bgm only if
   the content demands it (`--bgm off` or `"bgm":"off"`).
2. **Voice = 北京小爷** (`zh_male_beijingxiaoye_moon_bigtts`, user-approved; 豆包/火山
   via `scripts/volc_tts.py`, creds at `/root/.config/volc_tts.json`). It is the
   ENGINE DEFAULT — do **NOT** pass `--voice` (passing vivi once shipped a wrong
   female-voice video). NEVER edge-tts, NEVER Kokoro, NEVER faster-whisper.
3. **TTS is FAIL-LOUD — silence is NEVER shipped.** If any phrase fails to synth,
   the build MUST abort loudly (non-zero exit, clear error). A silent/muted segment
   is a shipped defect (this caused the 07-18 无声片 incident). Never "paper over" a
   TTS failure with a silent gap, a beep, or a re-used clip — stop and report.
4. **You write CONTENT; the engine owns the LOOK.** Do NOT set `theme`/`accent`/
   `style` (ignored — obsidian is fixed). Scene types are a *vocabulary*: carry REAL
   information (the number, the evidence, the comparison) and sequence them by a
   chosen narrative structure — not the same fixed march every time.
5. **Don't hand-edit the engine per video** (`make_rich_video.py`, `volc_tts.py`,
   `richlib/`). If a build fails, fix your **SPEC** (text / scene fields), not the
   script.
6. **No 关注/点赞/三连/收藏 CTA** — in 口播 *and* 画面. The outro lands the **content**
   point; never add a `cta` field, never say "关注我 / 点赞 / 一键三连". (The script
   strips these as a safety net, but don't author them.)

## How to Run

Work inside `/root/hermes-content/douyin/`. Write a `spec.json`, then one command:

```bash
SKILL_DIR="$(dirname "$(find ~/.hermes/skills -path '*/douyin-shortform/SKILL.md' | head -1)")"
python "$SKILL_DIR/scripts/make_rich_video.py" \
  --spec /root/hermes-content/douyin/<date>-<topic>/spec.json \
  --out  /root/hermes-content/douyin/<date>-<topic>.mp4
# On success it prints:  [rich] DONE -> <path> (Ns, 1080x1920)
```

Default look = **obsidian (Dark Matter)** — do NOT pass `--style`. Add
`--style editorial|notebook|terminal|tabloid|keynote` **only** to force an old skin
for rollback if obsidian breaks. Do NOT pass `--voice` (engine default = 北京小爷).
Use container paths (`/root/...`), never host paths (`D:\...`). The script runs in
the container.

## Visual system: "Dark Matter" (what the engine renders — do NOT author it)

You never write colors/coords; this is here so your spec *fits* the look and your QC
knows what "correct" is.

- **Palette (semantic):** bg `#0A0E14` (deep space, never pure black) / card
  `#131920`; text `#E8ECEF` / secondary `#7A8794` / grid-line `#1E2630`. Accent
  `#3DDC97` (measurement green = progress/confirmation/highlight); data `#4FC3F7`
  (signal blue = charts/numbers/tracks); warn `#FF5D5D` **only on genuinely negative
  data**, never decoration. Evidence cards use a light sub-palette (paper `#F4F5F3`,
  ink `#131920`). A per-video accent hue rotation (green→amber→violet) avoids
  day-to-day sameness; semantics stay fixed.
- **Type:** H1 得意黑 Smiley Sans Oblique (96-128px); H2/labels Noto Sans CJK SC Bold
  (56-64px); body/captions Noto Sans CJK SC Medium (42-46px); hero digits Noto Sans
  CJK SC Black (160-220px, tabular; latin digits may use JetBrains Mono). All
  free-commercial, bundled in `scripts/assets/fonts`; the engine's `ensure_fonts()`
  installs Smiley Sans and warns loudly if Noto CJK is missing.
- **Grid & safe area (1080×1920):** 72px margins; content column x:72-1008.
  Douyin UI no-go zones: top y<200, bottom y>1550, right rail x>930 below y≈1150.
  Headlines land left-aligned (log-feel, anti-PPT); captions sit y≈1380-1540, never
  below 1550. The engine enforces this — but keep hooks/outros short so they fit.
- **Motion:** entrance = blur-focus (`blur 8px→0` + `translateY 24px→0`, 320ms) —
  "coming into measurement"; emphasis = highlighter sweep on key words + number
  roll-ups (NO bounce-ins on text cards); transitions = **hard cut by default**,
  rail-sweep wipe only on chapter changes. The old random rise/slide/zoom/drop pool
  and the `sceneLive` breathing wobble on text scenes are **gone**; only gentle
  1.02-1.05 drift remains on full-bleed media.

## Spec format & Scene grammar V2

`spec.json` is **content only**. Global keys: `tag` (small label, optional), `handle`
(default `@yourhandle`), `title` (the topic — recommended; seeds the engine), optional
`style` (rollback only). Then `scenes: [...]`. **Every scene MUST have `say`** = the
spoken narration for that beat (audio AND per-scene duration come from it). Do NOT
set `theme`/`accent`.

Scene types (a **vocabulary**, not a fixed running order):

| type | fields | use for |
| --- | --- | --- |
| `media` | `image` OR `video` (container path), `caption?`, `overlay?` | **the backbone** — a REAL photo or **video clip** of the thing. Images get a limited Ken Burns; clips play muted under the voice (looped if short). |
| `evidence` | `image` (container path), `source` (e.g. `新华社`), `caption?`, `highlight?` | **webpage / article / paper / screenshot content** — renders as a light Evidence Card (32px padding, 1px accent border), cropped to the ONE relevant region, source tag bottom-right, slow zoom (≤1.06x) into the highlighted line. **All page/screenshot material MUST use this type — never full-bleed `media`.** |
| `kinetic` | `lines` (1-2, ≤9 chars), `eyebrow?`, plus optional `image`/`video` bg | animated text over a live background — use for hooks and punch beats that have no single photo but still need a visual layer |
| `hook` | `lines` (1-2, ≤9 chars each), `eyebrow?`, **must carry a visual layer**: either a `media`/`evidence` background OR be authored as `kinetic` over the animated bg | the opening punch (first ~2s). **A dead-black text-only hook is a validation error.** |
| `stat` | `value` (e.g. "70%"), `label`, `unit?` | one big hero number, roll-up count-in |
| `diagram` | `title?`, `nodes` (**≤4**: `{label(≤8 chars), sub?(≤12 chars)}`), `edges` (labels between consecutive nodes) | 架构/流程/链路 — renders as a glowing **track line** (rail + lit dots), highlight sweeps along it synced to voice. **NOT boxes-with-arrows, NOT a whiteboard.** |
| `compare` | `before`, `after` | 之前 ❌ vs 现在 ✅ — two solid bars, digits outside the bar (one short line each) |
| `outro` | `lines` (1-2) | the close — land the point itself, **NO 关注/点赞 CTA** |
| `code` | `code` (`\n`), `lang`, `caption?` | **discouraged** — only genuine code stories; ≤6 lines |
| `bullets` | `lines` (2-4 short), `head?` | **discouraged** — prefer stat/diagram/evidence; a styled list is a PPT smell |

**Grammar hard rules (the engine's `validate_spec` fails the build if violated):**

- **hook MUST have a visual layer** (media/evidence bg or `kinetic` over animated bg).
- **Any text card ≤2 lines** — either ≤2 lines × ≤9 chars headline, or 1 headline +
  1 sub. A paragraph card (>28 chars of body) is a validation error: translate the
  copy into a number / rail / evidence card, don't paste prose.
- **diagram ≤4 nodes**, node label ≤8 chars + sub ≤12 chars.
- **≥55% of scenes carry real media** (video / image / evidence). Text-only scenes
  are **never adjacent** (no two card-only scenes back-to-back).
- **Each `say` = ONE concrete fact in spoken Chinese, 12-22 chars.** Banned as `say`:
  空话 with no number/subject ("非常厉害", "引发热议", "值得关注").
- **Total voiceover 130-170 chars** for a **35-50s** cut. (This supersedes v2's
  25-35s / 90-130 chars — v3 runs a touch longer to carry evidence.)

**Speech-synced subtitles are automatic** — every scene's `say` is rendered as
big captions (y≈1380-1540, numbers auto-highlighted), phrase by phrase in sync with
the voice. Don't put the narration on the slides; the subs carry it.

### Assembly — content decides the mix (NOT a template)

Scene types are LEGO bricks: real footage, evidence cards, track-line diagrams, data
overlays ON footage, hero-number punches. **Compose what THIS story needs, never the
same assembly twice in a row.** Two forms to pick from before writing scenes:

- **Footage-flow** (events / society / lifestyle / macro): nearly every spoken line
  rides a MOVING real shot (news clip / stock footage, cut every 2-5s), media ≥70%,
  text cards limited to the hook + at most one stat punch; mechanism beats use
  `diagram`. The subtitle layer carries the words.
- **Card-mix** (code / data / mechanism-heavy tech): mixed assembly, media ≥55%.

The one test for every scene: *is this the most informative thing the screen could
show while the voice says this line?* If real footage wins, use it; if the point
needs footage AND a number, put an `overlay` on the media scene.

**`overlay` on media scenes** — footage + data on screen together:
`{"type":"media","video":"clip.webm","caption":"实录 · 发布会","overlay":{"value":"29/32","label":"小组赛命中"}}`
(`value` = big accent number; `label`/`text` = one short line under it.)

### Example spec (Dark Matter, grammar-clean)

```json
{
  "tag": "AI编程", "handle": "@yourhandle", "title": "AI 帮我写测试",
  "scenes": [
    {"type":"kinetic","say":"写完功能最烦的就是补测试。","eyebrow":"AI 编程","lines":["写完功能","最烦补测试"]},
    {"type":"compare","say":"以前手写要磨一天半,现在起草只要十分钟。","before":"手写 · 1.5 天","after":"AI 起草 · 10 分钟"},
    {"type":"evidence","say":"我把函数丢进去,三秒就出一份测试骨架。","image":"/root/.../shot1.png","source":"本地终端","caption":"3 秒出骨架"},
    {"type":"stat","say":"现在七成的测试初稿都让它先起草。","value":"70%","label":"测试初稿 AI 先写"},
    {"type":"diagram","say":"我只做三步:读漏的边界,补真实用例,收紧断言。","title":"我做的三步","nodes":[{"label":"读边界"},{"label":"补用例"},{"label":"收断言"}],"edges":["",""]},
    {"type":"outro","say":"省下的时间,拿去啃真正难的逻辑。","lines":["省下的时间","啃难逻辑"]}
  ]
}
```

## Materials (evidence, not decoration)

**Hard material rules (also enforced by `verify_media`):**

- **Webpage / article / paper / any screenshot → `evidence` type ONLY.** NEVER pan a
  page screenshot full-bleed as "footage" (a top-3 complaint about old output). Crop
  to the single relevant region; the engine frames it as an Evidence Card with source
  tag.
- **Full-bleed video/photo requires short side ≥900px source.** Below that it can't
  go full-bleed.
- **Short side <720px → contained (≤75% width) on a 40px blur-fill of the image's own
  colors**, never stretched past ~110%. No naked low-res.
- **AI-gen clips are normalized to 30fps** (h264, no second vp9 pass).

**Getting material:**

0. **Stock footage (first choice for atmosphere/setting).** Portrait HD, free
   commercial license:
   `python "$SKILL_DIR/scripts/fetch_stock_clip.py" --query "<english keywords>" --out <dir>/clipN.mp4`
   — keywords ENGLISH, 2-3 concrete nouns ("data center aisle", "chip factory
   macro"); `--index 1` picks the next candidate. Event-specific imagery still needs
   real news footage (`fetch_web_clip`); stock covers the LOOK, not the news.
1. **Page-scroll VIDEO clip (real motion from the actual page):**
   `python "$SKILL_DIR/scripts/record_page_clip.py" --url <page> --out /root/hermes-content/douyin/<dir>/clip1.webm --seconds 6`
   → slow-scrolling phone-viewport capture (viewport 1080×1920; load lead-in
   auto-trimmed). `--no-scroll` for a static hold; mp4 sources auto-transcoded. A
   scrolling **page** clip still reads as a page — prefer it for atmosphere, and route
   any single readable region through `evidence` instead.
2. **Screenshots via the browser** (for `evidence` content): `browser_navigate` →
   `browser_screenshot` → file lands in `/root/.hermes/cache/screenshots/`. Copy the
   newest into your work dir:
   `cp "$(ls -t /root/.hermes/cache/screenshots/*.png | head -1)" /root/hermes-content/douyin/<date>-<topic>/shot1.png`
   then reference it as an `evidence` scene.
3. **Direct image download** (`curl -o`) when an article has a key figure. For
   abstract/mechanism beats with NO real footage, generate an **AI motion b-roll clip**
   (documentary-style vertical):
   `python "$SKILL_DIR/scripts/gen_scene_video.py" --desc "<画面内容一句话>" --out <dir>/genN.mp4`
   → scene `video`. **Hard cap 4 per video (2-3 recommended)**; 1-4 min/clip — poll
   patiently. A STATIC AI illustration (`gen_scene_image.py`, cap **1** per video) is
   the last resort. Real material always outranks both. Both scripts write `.ai`
   sidecars the engine uses to enforce caps; `gen_scene_image` auto-crops CogView's
   「AI生成」watermark strip.
4. **Look at each image before using it** (`vision_analyze`) — confirm it shows what
   you'll say over it, isn't a cookie banner / 404 / blank page / **a full-page wall of
   article text** (unreadable on a phone; use the article's own figure, an `evidence`
   crop, or a `diagram` instead).

## Copy engine (this is where quality comes from)

**Model routing:** the high-taste reasoning pass — **hook + `say` lines** — is
drafted by **kimi-k3** (env `KIMI_CN` / `K3` key). **deepseek** does the mechanical
assembly (splitting the approved script into scene fields, filling captions/labels,
JSON shaping). Draft with kimi-k3, execute with deepseek.

**Copy acceptance gate (all three MUST pass):**
1. **The hook is concrete within ≤2s of speech** — a specific image + a number or a
   conflict in the first spoken line. No windup, no background.
2. **Every `say` line survives alone as a caption** — read any single line cold; if it
   says nothing without its neighbors, rewrite it.
3. **Zero filler adjectives / no-subject hype** — see禁语 below.

**How to write the hook:** front-load a concrete image plus a number or a conflict in
the first ~2 seconds. "一辆车三年掉价一半" beats "今天聊聊汽车保值率". The hook scene
MUST carry a visual layer (media/evidence bg or `kinetic`).

**每句可独立成字幕 standard:** each `say` is 12-22 chars, one concrete fact, readable
standalone. If a line needs the previous line to make sense, it's not a caption — split
or rewrite.

**禁语 (banned in 口播 AND 画面):**
- Empty adjectives / no-subject hype: 「非常厉害」「引发热议」「值得关注」「相当不错」
  「令人震惊」 with no number or subject behind them.
- AI tells: 「你有没有想过」「在这个 AI 时代」「众所周知」「今天给大家分享」「话不多说」
  「随着…的发展」「不得不说」「家人们」「绝绝子」.
- News-anchor filler: 「据报道」「近日」「值得注意的是」 and any 新闻联播 phrasing.
- Any 关注/点赞/三连/收藏.
- Run the final script through the **humanizer** skill regardless.

## Structure & voice (vary the shape too)

One look does not mean one rhythm. Vary the **narrative shape** and **spoken register**
or it still reads as AI slop.

**Pick a structure** (fit the topic; don't repeat the last video's):
悬念式 (反常钩子→为什么→证据→转折→收) / 故事式 (一个场景「我…」→经过→发现→普适点) /
暴论式 (反共识断言→大家为什么想错→论据→让步→立场) / 拆解式 (一个结果→步骤 1/2/3→收) /
辟谣式 (「都说 X」→其实不是→真相) / 对比式 (A vs B→各自→结论).

**Pick a voice** (vary it): 老友闲聊 / 冷静解读 / 开发者唠嗑 / 热血快评.

**Tempo variance (anti-conveyor-belt, user feedback 2026-07-24).** A cut where every
scene runs the same 3-5s reads as a slideshow on a belt. Two levers, both mandatory:
- Write at least one FAST beat (short punchy `say`, 8-12 chars, on a media/kinetic
  scene) and at least one HELD beat (a media scene whose `say` is the longest line,
  or a data scene the engine will hold for reading).
- The engine enforces a **reading-time floor** per card scene (~4.5 chars/s on big
  type + orientation beats) by extending the scene past the voiceover with BGM-only
  tail — so never cram a dense card onto a short spoken line expecting it to flash
  past; the engine will hold it. Budget the pacing in the spec instead.

## Authoring tips

0. **Homework before writing (depth is a HARD requirement).** Read 2-3 sources first.
   The script must contain **≥3 specific facts** (exact numbers / names / timeline /
   causal chain), **1 judgment of your own** (not a restatement), and **1 detail most
   people don't know**. Go DEEP on one point, don't skim three. Self-check: "would
   someone who knows this field learn something?" If not, rewrite.
1. **Script first, then split into scenes.** Write the spoken narration (**35-50s,
   130-170 chars**, hook in the first ~2s), run it through the **humanizer** skill,
   THEN cut it into scene `say` lines (each 12-22 chars).
2. **Write like a 抖音 up主, not a news anchor.** Short spoken sentences, opinions and
   attitude, rhetorical turns (「结果呢?」「离谱的是」「你猜怎么着」), a new hook-point
   every ~8s (new fact / reversal / number punch). Open with conflict or conclusion —
   ZERO background windup. End on a take that invites comments, not a summary.
3. **通俗易懂 is a HARD requirement.** Write for someone who knows NOTHING about the
   field; translate every term into daily language: 「渗透率60%」→「每卖10辆新车,6辆是
   电车」;「平均车龄8.2年」→「一辆油车平均开到孩子小学毕业」. Numbers need a reference an
   ordinary person can feel. Self-check: would your 完全不懂行的朋友 follow every
   sentence?
4. **Pace like an editor.** Most scenes 2-4s; let ONE scene breathe at 5-6s max. Never
   the same layout two scenes in a row. Match type to content: a number → `stat`, a
   flow → `diagram` (track line), a before/after → `compare`, evidence → `evidence`.
5. **`say` is what's HEARD; on-screen text is the emphasis, not a transcript.** Keep
   them aligned, but the slide shows the punch, the voice carries the sentence.

## Identity gate (HARD)

Never put 学校 / 城市 / 年级 / 职位 in the video or narration. Self-label "技术博主" /
"AI工具玩家". De-identify any personal experience. Full self-check before building.

## QC gates (three, all must pass before "done")

`OUT` = the exact `--out` path `make_rich_video.py` printed.

**Gate 1 — `validate_spec` (pre-render, hard fail).** Runs inside the engine before
render: enforces Scene-grammar V2 (hook visual layer, ≤2-line cards / ≤28-char body,
diagram ≤4 nodes, ≥55% media, no adjacent text-only, `say` 12-22 chars, VO 130-170
chars). A violation aborts the build — fix the spec, don't touch the script.

**Gate 2 — `verify_media` (vision, pre/at render).** Rejects: any webpage screenshot
NOT routed to an `evidence` card; any media with short side <720 used full-bleed;
cookie banners / 404s / blank pages / full-page text walls. Fix the offending material
or re-route to `evidence`/`diagram`.

**Gate 3 — Post-render frame audit (NEW in v3).** One command — it samples 6
mid-segment frames and runs the vision checklist (text cut off / contrast /
dead space >45% / layout accidents) automatically:

```bash
python $SKILL_DIR/scripts/qc_frames.py --video "$OUT"
# exit 0 = PASS; exit 6 = failures printed per-timestamp — fix the SPEC and RE-RENDER
```

**Any failure → fix the SPEC and RE-RENDER** (tighten copy, add a bg layer, split an
overflowing card, swap a dead diagram for stat/evidence). Do not ship a frame that fails.

Also still confirm the basics:
- **Duration + streams:** `ffprobe -v error -show_entries format=duration:stream=codec_type -of default=nw=1 "$OUT"` → ~narration length (35-50s), both a video and an audio stream.
- **Resolution / fps:** 1080x1920, 30fps.
- **Rich, not bare:** frames show designed Dark Matter layouts (hero number / track-line
  diagram / evidence card / compare bars), NOT flat centered text on black.

## Render chain (engine behavior — described, not authored)

`make_rich_video.py` implements the following; you don't set these, but QC against them:

- **Sampling:** render at device_scale_factor 2 (2160×3840), screenshot PNG (lossless),
  downscale to 1080×1920 with **lanczos** in ffmpeg. Falls back to DPR 1.5 if frame
  time explodes.
- **Encode:** libx264, **crf 17, preset slow** (medium fallback), maxrate 12M, bufsize
  24M, yuv420p, 30fps — **target ≥8 Mbps** per Douyin upload guidance.
- **No fake film:** the noise/grain filter and heavy vignette are **removed** (clarity >
  film feel); only a very subtle eq contrast trim remains. (`--no-grade` still available
  for A/B.)
- **Audio:** TTS stays 24kHz mono at source; the mix bus is upsampled to **44.1kHz
  stereo**, BGM stereo, output **aac 192k 44.1k stereo**.
- **Material transcodes:** `record_page_clip` viewport 1080×1920; `fetch_web_clip`
  max-height 1080; intermediate transcodes use quality settings (not
  `-deadline realtime`); gen clips fps-normalized to 30.

## Publishing 抖音 = full-auto with honesty gates

The build pipeline is reliable. Full-auto publish HAS landed for real, but the platform
side is flaky (upload binding, content pre-check overload) — every step must verify, and
every failure must be reported honestly. ALWAYS confirm against **作品管理**.

When auto-publishing (via **content-publishing** on the logged-in Camofox session):
`browser_navigate` the creator upload page →
`browser_upload(file_paths=[mp4], selector="input[type=file]", verify_text=["上传中","转码中","重新上传"])`
→ **trust the returned `bound` flag**: `bound:false` = the video did NOT register —
re-navigate to a fresh upload page and retry ONCE with `drop=true` (same `verify_text`);
never fill the form on an unbound upload → **wait for the upload to FINISH** (no
上传中/转码中/百分比, 发布 button enabled) → fill **title / description / topic tags** with
`browser_type` → **`browser_douyin_publish(title="<the exact title>")`** → it waits out
the content pre-check (auto-clicks 重新检测, retries through 「检测人数过多」 busy toasts)
and confirms the post in 作品管理, returning published / needsVerify / unconfirmed(+reason).
`reason:"detection_busy"` → draft is safe: `sleep 420`, call it ONCE more, then report
honestly — **max 2 publish calls total**. NO QR, NO sandbox, NO throwaway scripts.

**Topic tags (话题):** add 3-5 relevant 抖音 hashtags in the description, mixing one broad
tag (e.g. `#科技`) with specific topical ones drawn from the actual content (`#AI编程`
`#新能源车`). No 关注/点赞/三连 phrasing in the tags either. Cover = **auto-generated by the
engine** (a clean strong frame) — do NOT hand-author a cover.

⚠️ **作品管理 is the only proof of 已发布.** A 发布成功 toast / editor-URL rename is NOT
proof (it caused false 已发布 before). Only `published:true` (server saw it in 作品管理)
= 已发布; `unconfirmed:true` = 未确认发布.

⚠️ **风控 caveats:** 抖音 may demand an SMS code on 发布 — the agent canNOT bypass it;
report `未确认发布:需短信验证` + screenshot, never loop or fake 已发布. Repeated
auto-publishing also risks a 风控 logout; if a verify shows logged out, report it
honestly (a QR re-login then needs the user).

## 留档 (retention)

Keep the finished mp4 **≥14 days** (the `Douyin_Retention` task prunes older files) so
a failed/unconfirmed publish can be retried or hand-uploaded without re-rendering.
Leave the `<date>-<topic>.mp4` and its work dir in `/root/hermes-content/douyin/`; do
not delete on success.
