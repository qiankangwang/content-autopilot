# Douyin Shortform V3 — "Dark Matter" Framework Design

Status: authoritative design contract for the V3 rebuild (2026-07-24).
Diagnosis it answers: prior output criticized as low-res materials, weak copy,
PPT-like layouts, no visual taste (tabloid hazard stripes, dead black hooks,
6-node whiteboard diagrams, webpage screenshots panned as footage).

## 1. Visual system: "Dark Matter" (single flagship system, replaces 5-skin rotation)

The look: a precision instrument in the dark — data gets measured, lit, proven.
Reference points: 回形针 evidence density, Vox highlight blocks, oscilloscope /
terminal restraint. NOT cyberpunk decoration: color only ever encodes meaning.

### Palette (semantic, not decorative)
- bg `#0A0E14` (deep space, never pure black) / card `#131920`
- text `#E8ECEF` / secondary `#7A8794` / grid-line `#1E2630` (1px)
- accent `#3DDC97` (measurement green — progress, confirmation, highlights)
- data `#4FC3F7` (signal blue — charts, numbers, tracks)
- warn `#FF5D5D` — ONLY on genuinely negative data. Never as decoration.
- Evidence-card sub-language (light): paper `#F4F5F3`, ink `#131920`.
- Per-video hue rotation allowed on accent (green→amber→violet) to avoid
  sameness across days; semantics stay fixed.

### Type (all free-commercial; bundle in scripts/assets/fonts)
- H1 headlines: 得意黑 Smiley Sans Oblique — 96-128px, lh 1.15, tight tracking
- H2 / labels: Noto Sans CJK SC Bold — 56-64px
- Body / captions: Noto Sans CJK SC Medium — 42-46px, lh 1.5
- Hero digits: Noto Sans CJK SC Black 160-220px, tabular; latin digits may use
  JetBrains Mono for instrument feel
- Source tags: 26-28px Regular, letter-spaced
- ensure_fonts() must install Smiley Sans and VERIFY presence of Noto CJK,
  warn loudly if missing.

### Grid & safe area (1080×1920)
- Margins 72px; content column x:72-1008
- Douyin UI no-go: top y<200; bottom y>1550; right rail x>930 below y≈1150
- Headlines land at y 250-900, left-aligned by default (log-feel, anti-PPT)
- Captions (subtitles) at y≈1380-1540, never below 1550

### Media treatment ("no naked low-res, no naked screenshots")
- Full-bleed video: allowed only if short side ≥900px source. Subtle 4%
  scanline overlay optional for "recorded" feel.
- Webpage/article/paper screenshots: NEVER panned full-bleed. Always the
  Evidence Card: light card, 32px padding, 1px accent border, cropped to the
  single relevant region, source tag bottom-right (`来源: 新华社` style), may
  zoom slowly INTO the highlighted line (Ken Burns limited to 1.06x).
- Low-res images (<720 short side): contained ≤75% width on blur-fill backdrop
  (40px blur of the image's own colors), never stretched past 110%.
- AI-gen clips: normalize to 30fps; keep h264, no second vp9 pass.

### Data viz (kills the PPT diagram)
- Flow/process = "track line": one glowing rail across the canvas, nodes as
  8px lit dots (accent, 6px glow), labels floating by the rail, progress =
  highlight sweeping along the rail synced to voiceover. Max 4 nodes.
- Numbers = hero digits with roll-up count (600-900ms ease-out, 4px overshoot
  settle), unit small at lower-right, one context line underneath.
- Comparison = two solid bars (no gradient), digits outside the bar.
- No boxes-with-arrows. No full-screen white panels. A diagram scene must
  never be >40% empty.

### Motion vocabulary (all CSS-implementable, frame-stepped renderer)
- Entrance: blur-focus `filter:blur(8px)→0` + `translateY(24px)→0`, 320ms,
  cubic-bezier(.16,1,.3,1) — "coming into measurement"
- Emphasis: highlighter sweep `clip-path inset` left→right 200ms linear on key
  words; number roll-ups; NO bounce-ins on text cards
- Transitions between scenes: hard cut default; rail-sweep wipe 180ms for
  chapter changes. Kill the random rise/slide/zoom/drop pool.
- Ambient: grid drift ≤6% opacity, 8-12s loop. Kill `sceneLive` breathing wobble
  on text scenes (keep gentle 1.02-1.05 drift only on full-bleed media).

## 2. Scene grammar V2

Types: `hook` `media` `evidence` `stat` `diagram` `compare` `kinetic` `outro`
(`code` `bullets` retained but discouraged).

Hard rules (validate_spec):
- hook MUST have a visual layer (media background or kinetic type over animated
  bg). A dead-black text-only hook is a validation error.
- Any text card: ≤2 lines × ≤9 chars headline, or 1 headline + 1 sub. Paragraph
  cards (>28 chars body) are a validation error — copy must be translated into
  numbers/rails/cards, not pasted.
- diagram: ≤4 nodes, node label ≤8 chars + sub ≤12 chars.
- ≥55% of scenes carry real media (video/image/evidence); text-only scenes never
  adjacent (existing rule kept).
- Every scene's `say` = one concrete fact in spoken Chinese, 12-22 chars;
  banned: 空话 ("非常厉害", "引发热议" without a number/subject).
- Total voiceover 130-170 chars for a 35-50s cut.

## 3. Render chain quality (make_rich_video.py)

- Render at device_scale_factor=2 (2160×3840), screenshot PNG (lossless),
  downscale to 1080×1920 with lanczos in ffmpeg. Fallback to DPR 1.5 if frame
  time explodes.
- Encode: libx264, crf 17, preset slow (medium fallback), maxrate 12M,
  bufsize 24M, yuv420p, 30fps. Target ≥8Mbps per Douyin upload guidance.
- Remove the noise() grain filter and heavy vignette from the finishing chain
  (clarity > fake film feel). Keep a very subtle eq contrast trim only.
- Audio: TTS stays 24kHz mono at source; mix bus upsampled to 44.1kHz stereo,
  BGM kept stereo, output aac 192k 44.1k stereo.
- Materials: record_page_clip viewport 1080×1920; fetch_web_clip max-height
  1080; all intermediate transcodes leave `-deadline realtime` for
  `-deadline good -cpu-used 2` (or h264 crf 18 passthrough where chromium can
  decode); gen clips fps-normalized to 30.

## 4. Copy engine

Script writing (order → spec) rules live in SKILL.md v3. Model routing:
kimi-k3 (reasoning, high-taste) drafts hook + say-lines; deepseek executes
mechanical assembly. Copy acceptance gate: hook concrete in ≤2s speech, every
line survivable alone as a caption, zero filler adjectives.

## 5. QC gates

1. validate_spec (grammar above) — pre-render, hard fail.
2. verify_media (vision) — existing, plus: reject any webpage screenshot not
   routed to Evidence Card; reject media short side <720 for full-bleed use.
3. Post-render frame audit: sample 6 frames → vision model checks text
   overflow, contrast, dead space >45%, caption legibility. Fail = fix + rerun.

## 6. File ownership (V3 rebuild)

- make_rich_video.py + fetch/gen scripts + fonts: render-chain owner
- richlib/ (base.py additions, style_obsidian.py, registry): visual engine owner
- SKILL.md v3: production-spec owner
- Old styles remain on disk for rollback; registry defaults to obsidian.
