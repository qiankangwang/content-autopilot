#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""richlib.base — the Style contract + shared helpers + document assembly.

A *style module* (style_editorial.py, style_notebook.py, ...) subclasses `Style`
and implements a small, fixed contract. make_rich_video.py never knows the
concrete style — it asks the registry to pick one, then calls these methods.

────────────────────────────────────────────────────────────────────────────
THE CONTRACT (what every style MUST provide)
────────────────────────────────────────────────────────────────────────────
class MyStyle(Style):
    id      = "editorial"          # unique slug
    weight  = 1.0                  # base rotation weight (keynote is low)
    label   = "杂志"                # human label (logs)

    def affinity(self, spec) -> float:
        # topic-aware multiplier (>1 favored, <1 disfavored). Look at
        # spec['scenes'] types + _blob(spec) keywords. Default 1.0.

    def variant(self, rng) -> dict:
        # WITHIN-STYLE randomness — this is what kills "same template".
        # Return a ctx dict. MUST include 'accent' (hex). Pick palette, a
        # layout-variant id per scene type, background texture, type scale,
        # etc. ALL random choices come from `rng` (seeded once per video).

    def css(self, ctx) -> str:
        # full CSS for THIS style+variant. Style owns its skin; base owns the
        # skeleton (.stage/.scene/.bar reset + the scene scheduler). Set
        # `--bar` color via a `.bar{background:...}` rule if you want a
        # progress bar; omit to hide it.

    def scene(self, i, sc, ctx) -> str:
        # HTML for ONE scene. Handle every type: hook/stat/code/compare/
        # bullets/outro (+ a sane fallback). Use ctx['_layout'][type] (the
        # variant you chose) to render ≥2 visibly different layouts per type.

    def background(self, ctx) -> str:   # optional bg layers (returned BEHIND scenes)
    def chrome(self, spec, ctx) -> str: # optional tag pill + handle (ABOVE scenes)

Animation model: base toggles `.scene.active` on exactly one scene at a time
(by index, on the audio-synced schedule). Your CSS animates children via
`.scene.active .foo { animation: ... }`. The FIRST scene is shown instantly
(it is also the video cover / frame 0) — keep its composed state readable with
no entrance, like the old hook did.
"""
import hashlib
import html
import os
import re
import shutil
import subprocess

W, H = 1080, 1920

# ── shared text helpers ──────────────────────────────────────────────────────
def esc(s):
    return html.escape(str(s))


def rgba(hexc, a):
    hexc = (hexc or "#000").lstrip("#")
    if len(hexc) == 3:
        hexc = "".join(c * 2 for c in hexc)
    try:
        r, g, b = int(hexc[0:2], 16), int(hexc[2:4], 16), int(hexc[4:6], 16)
    except ValueError:
        r, g, b = 0, 0, 0
    return f"rgba({r},{g},{b},{a})"


def mix(hexc, other, t):
    """Linear blend hexc->other by t in [0,1]; returns #rrggbb."""
    def rgb(h):
        h = h.lstrip("#")
        if len(h) == 3:
            h = "".join(c * 2 for c in h)
        return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    a, b = rgb(hexc), rgb(other)
    c = tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))
    return "#%02x%02x%02x" % c


def big_fs(lines, base=128, content_px=888):
    """Responsive font-size so long CJK lines don't wrap ugly (weight 900)."""
    m = max((len(str(x)) for x in lines if x), default=4)
    if m <= 5:
        return base
    table = {6: 118, 7: 104, 8: 92, 9: 82, 10: 74}
    return round(table.get(m, 66) * base / 128)


# ── code syntax highlighter (terminal/keynote styles) ────────────────────────
_KW = {
    "python": r"\b(def|return|if|elif|else|for|while|in|not|and|or|is|None|True|False|"
              r"import|from|as|class|with|try|except|finally|raise|assert|lambda|yield|async|await|pass)\b",
    "js": r"\b(const|let|var|function|return|if|else|for|while|of|in|new|class|extends|"
          r"async|await|try|catch|finally|throw|import|from|export|default|null|true|false|this)\b",
    "ts": r"\b(const|let|var|function|return|if|else|for|while|of|in|new|class|extends|interface|type|"
          r"async|await|try|catch|finally|throw|import|from|export|default|null|true|false|this)\b",
    "bash": r"\b(if|then|else|fi|for|in|do|done|while|case|esac|function|echo|export|cd|return)\b",
}


def highlight(code, lang):
    """Return a list of HTML lines with <span class="t-kw|t-str|t-cmt|t-num|t-fn|t-dec">."""
    lang = (lang or "python").lower()
    kw = _KW.get(lang, _KW["python"])
    cmt = "#" if lang in ("python", "bash") else "//"
    out_lines = []
    for raw in (code or "").split("\n"):
        comment = ""
        ci = raw.find(cmt)
        if ci != -1 and raw.count("'", 0, ci) % 2 == 0 and raw.count('"', 0, ci) % 2 == 0:
            comment = raw[ci:]
            raw = raw[:ci]
        toks = []
        pattern = re.compile(
            r"(?P<str>'[^']*'|\"[^\"]*\")"
            r"|(?P<dec>@[\w.]+)"
            r"|(?P<kw>" + kw + r")"
            r"|(?P<fn>[A-Za-z_]\w*)(?=\s*\()"
            r"|(?P<num>\b\d+\.?\d*\b)"
            r"|(?P<id>[A-Za-z_一-鿿]\w*)"
            r"|(?P<ws>\s+)"
            r"|(?P<other>.)"
        )
        for m in pattern.finditer(raw):
            kind = m.lastgroup
            text = html.escape(m.group())
            if kind in ("ws", "other", "id"):
                toks.append(text)
            else:
                toks.append(f'<span class="t-{kind}">{text}</span>')
        if comment:
            toks.append(f'<span class="t-cmt">{html.escape(comment)}</span>')
        out_lines.append("".join(toks) if toks else "&nbsp;")
    return out_lines


# ── font self-install (durable via the /root bind mount) ─────────────────────
def ensure_fonts():
    """Copy bundled assets/fonts/*.ttf into ~/.fonts and refresh fontconfig.

    The render container ships NO handwriting/楷体 font, so the notebook style
    would fall back to sans. We ship LXGW WenKai (OFL) with the skill; ~/.fonts
    is bind-mounted (/root) so this copy persists and only runs once.
    """
    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "fonts")
    if not os.path.isdir(src):
        return
    dst = os.path.expanduser("~/.fonts")
    try:
        os.makedirs(dst, exist_ok=True)
    except OSError:
        return
    changed = False
    for fn in os.listdir(src):
        if not fn.lower().endswith((".ttf", ".otf", ".ttc")):
            continue
        sp, dp = os.path.join(src, fn), os.path.join(dst, fn)
        try:
            if not os.path.exists(dp) or os.path.getsize(dp) != os.path.getsize(sp):
                shutil.copy2(sp, dp)
                changed = True
        except OSError:
            pass
    if changed:
        try:
            subprocess.run(["fc-cache", "-f", dst], capture_output=True, timeout=90)
        except Exception:
            pass


# ── the Style base class ─────────────────────────────────────────────────────
class Style:
    id = "base"
    weight = 1.0
    label = "base"

    def affinity(self, spec):
        return 1.0

    def variant(self, rng):
        return {"accent": "#FF2E4D"}

    def css(self, ctx):
        return ""

    def scene(self, i, sc, ctx):
        return f'<section class="scene" data-i="{i}"></section>'

    def background(self, ctx):
        return ""

    def chrome(self, spec, ctx):
        # user decision 2026-07-18: no corner branding on screen (no 期数 /
        # tag pill / handle / slogans) — content only
        return ""


def blob(spec):
    """All human text in a spec, lowercased — for keyword affinity scans."""
    bits = [str(spec.get("tag", "")), str(spec.get("title", "")), str(spec.get("_topic", ""))]
    for sc in spec.get("scenes", []):
        for k in ("say", "eyebrow", "label", "caption", "head", "before", "after"):
            if sc.get(k):
                bits.append(str(sc[k]))
        for x in sc.get("lines", []) or []:
            bits.append(str(x))
        if sc.get("code"):
            bits.append(str(sc["code"]))
    return " ".join(bits).lower()


def scene_types(spec):
    return [sc.get("type", "") for sc in spec.get("scenes", [])]


# ── document assembly (skeleton + scheduler; styles bring the skin) ──────────
_BASE_SKELETON = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:%(W)dpx;height:%(H)dpx;overflow:hidden;-webkit-font-smoothing:antialiased;
  text-rendering:geometricPrecision}
.stage{position:relative;width:%(W)dpx;height:%(H)dpx;overflow:hidden}
.scene{position:absolute;inset:0;z-index:3;display:flex;flex-direction:column;
  justify-content:center;opacity:0;pointer-events:none;transition:opacity .55s ease}
/* sceneLive: settle-in, then a slow perpetual drift — a scene is never a frozen
   card (the static-PPT feel). Runs on the whole scene so every style gets it. */
.scene.active{opacity:1;animation:sceneLive 16s linear forwards}
@keyframes sceneLive{
  0%%{transform:scale(1.018) translateY(8px);animation-timing-function:ease-out}
  7%%{transform:scale(1.0) translateY(0);animation-timing-function:linear}
  100%%{transform:scale(1.038) translateY(-14px)}
}
.bar{position:absolute;left:0;bottom:0;height:8px;width:0;z-index:9}

/* ── media scenes: full-bleed real imagery with a Ken Burns move ─────────── */
.media-wrap{position:absolute;inset:0;overflow:hidden;background:#0b0d12}
.media-img{width:100%%;height:100%%;object-fit:cover}
.scene.active .media-img.kb0{animation:kbOut var(--kbd,8s) linear both}
.scene.active .media-img.kb1{animation:kbIn var(--kbd,8s) linear both}
.scene.active .media-img.kb2{animation:kbPanL var(--kbd,8s) linear both}
.scene.active .media-img.kb3{animation:kbPanR var(--kbd,8s) linear both}
@keyframes kbOut{0%%{transform:scale(1.14)}10%%{transform:scale(1.10)}100%%{transform:scale(1.0)}}
@keyframes kbIn{0%%{transform:scale(1.04)}100%%{transform:scale(1.15)}}
@keyframes kbPanL{0%%{transform:scale(1.16) translateX(3%%)}100%%{transform:scale(1.16) translateX(-3%%)}}
@keyframes kbPanR{0%%{transform:scale(1.16) translateX(-3%%)}100%%{transform:scale(1.16) translateX(3%%)}}
.media-scrim{position:absolute;left:0;right:0;bottom:0;height:560px;
  background:linear-gradient(transparent,rgba(4,6,10,.62))}
/* fit mode — landscape/wide material: the sharp image contained on the STYLE
   CANVAS (the style's own background + a light wash show through), instead of
   the old blurred-black fill that wasted 2/3 of the frame */
.media-canvas{position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(0,0,0,.06),transparent 26%%,
    transparent 66%%,rgba(0,0,0,.24))}
.media-fitpos{position:absolute;left:50%%;top:44%%;transform:translate(-50%%,-50%%);
  width:92%%;height:66%%;display:flex;align-items:center;justify-content:center;
  overflow:hidden;border-radius:26px}
.media-fit{width:100%%;height:100%%;object-fit:cover;border-radius:26px;
  box-shadow:0 40px 110px rgba(0,0,0,.5)}
.scene.active .media-fit{animation:kbFit var(--kbd,8s) linear both}
@keyframes kbFit{0%%{transform:scale(1.0)}100%%{transform:scale(1.055)}}
/* video clips reuse .media-img / .media-fit classes; the renderer seeks them
   frame-by-frame (a <video> doesn't follow the animation clock) */
video.media-img,video.media-fit{background:#0b0d12}

/* ── diagram scenes: architecture/flow, elements land one by one ─────────── */
.diag-wrap{position:absolute;left:50%%;top:45%%;
  transform:translate(-50%%,-50%%) scale(var(--dgscale,1));
  width:880px;display:flex;flex-direction:column;align-items:center}
.diag-title{font-family:'Noto Sans CJK SC',sans-serif;font-weight:900;font-size:56px;
  margin-bottom:44px;letter-spacing:2px}
.diag-node{width:640px;padding:30px 40px;border-radius:20px;margin:0;
  font-family:'Noto Sans CJK SC',sans-serif;font-weight:700;font-size:44px;
  text-align:center;opacity:0;box-shadow:0 16px 44px rgba(0,0,0,.28)}
.diag-node .sub2{display:block;font-size:30px;font-weight:400;opacity:.75;margin-top:6px}
.scene.active .diag-node{animation:diagPop .5s cubic-bezier(.2,1.4,.4,1) var(--nd,0s) both}
@keyframes diagPop{0%%{opacity:0;transform:translateY(26px) scale(.92)}
  100%%{opacity:1;transform:translateY(0) scale(1)}}
.diag-arrow{height:64px;display:flex;flex-direction:column;align-items:center;
  justify-content:center;opacity:0;position:relative}
.scene.active .diag-arrow{animation:diagArrow .4s ease-out var(--nd,0s) both}
@keyframes diagArrow{0%%{opacity:0;transform:translateY(-10px)}100%%{opacity:1;transform:translateY(0)}}
.diag-arrow .shaft{width:6px;flex:1;border-radius:3px}
.diag-arrow .head{width:0;height:0;border-left:14px solid transparent;
  border-right:14px solid transparent;border-top:16px solid}
.diag-arrow .elabel{position:absolute;left:calc(50%% + 26px);top:50%%;transform:translateY(-50%%);
  font-family:'Noto Sans CJK SC',sans-serif;font-size:28px;font-weight:700;
  padding:6px 16px;border-radius:999px;white-space:nowrap}
.media-cap{position:absolute;top:148px;left:64px;max-width:820px;padding:14px 28px;
  font-family:'Noto Sans CJK SC',sans-serif;font-weight:700;font-size:40px;line-height:1.3;
  color:#fff;border-radius:14px}
/* overlay: a floating data/point card ON TOP of real footage — footage and the
   number/point on screen together (modular assembly, not either-or) */
.media-ovl{position:absolute;top:300px;right:56px;max-width:calc(100%% - 132px);
  padding:28px 38px;border-radius:22px;background:rgba(9,11,16,.94);color:#fff;
  text-align:right;font-family:'Noto Sans CJK SC',sans-serif;opacity:0;
  border-right:8px solid var(--ovl-accent,#FF2E4D);
  box-shadow:0 24px 70px rgba(0,0,0,.55)}
.scene.active .media-ovl{animation:diagPop .55s cubic-bezier(.2,1.4,.4,1) .5s both}
.media-ovl .ov{font-weight:900;font-size:84px;line-height:1.05;letter-spacing:1px;
  text-shadow:0 4px 18px rgba(0,0,0,.5)}
.media-ovl .ol{font-size:31px;font-weight:700;opacity:.94;margin-top:8px}

/* ── speech-synced subtitles (global layer; the 抖音 watch-muted backbone) ── */
.subs{position:absolute;left:0;right:0;bottom:296px;height:120px;z-index:6;pointer-events:none}
.sub{position:absolute;left:50%%;bottom:0;transform:translateX(-50%%);white-space:nowrap;
  font-family:'Noto Sans CJK SC',sans-serif;font-weight:900;color:#fff;opacity:0;
  -webkit-text-stroke:5px rgba(8,10,14,.9);paint-order:stroke fill;letter-spacing:1px;
  background:rgba(8,10,14,.6);padding:6px 26px 10px;border-radius:16px}
.stage.go .sub{animation:subPop var(--len,2s) linear var(--d,0s) both}
@keyframes subPop{
  0%%{opacity:0;transform:translateX(-50%%) translateY(16px) scale(.96)}
  5%%{opacity:1;transform:translateX(-50%%) translateY(0) scale(1)}
  96%%{opacity:1;transform:translateX(-50%%) translateY(0) scale(1)}
  100%%{opacity:0;transform:translateX(-50%%) translateY(0) scale(1)}
}
/* keyword pulse: numbers/terms flare briefly as the phrase lands */
.sub .kw{display:inline-block}
.stage.go .sub .kw{animation:kwPulse .6s cubic-bezier(.2,1.6,.4,1) var(--d,0s) both}
@keyframes kwPulse{0%%{transform:scale(1)}30%%{transform:scale(1.22)}100%%{transform:scale(1)}}
"""


def compose_document(style_css, background_html, chrome_html, scenes_html, durs, subs_html=""):
    total = sum(durs) if durs else 1.0
    skeleton = _BASE_SKELETON % {"W": W, "H": H}
    return f"""<!doctype html><html><head><meta charset="utf-8">
<style>{skeleton}\n{style_css}</style></head>
<body><div class="stage" id="stage">
{background_html}
{scenes_html}
<div class="subs">{subs_html}</div>
{chrome_html}
<div class="bar" id="bar"></div>
</div>
<script>
const durs = {_json(durs)};
const total = {total};
const scenes = [...document.querySelectorAll('.scene')];
const stage = document.getElementById('stage');
const bar = document.getElementById('bar');
if (bar) bar.style.transition = 'width ' + total + 's linear';
function show(i){{ scenes.forEach((s,k)=>s.classList.toggle('active', k===i)); }}
window.__show = show;
window.__done = false;
function run(i){{
  if(i>=scenes.length){{ window.__done = true; return; }}
  show(i);
  setTimeout(()=>run(i+1), (durs[i]||2.8)*1000);
}}
// Manual mode (#manual): the renderer drives the timeline frame-by-frame —
// no auto-run, no wall-clock timers. It calls __show(i) at scene boundaries,
// __start() once, and steps every animation via __step(ms) per frame.
// The .go class gates the subtitle animations so their delays start counting
// from __start, not from page load.
window.__start = function(){{
  stage.classList.add('go'); if(bar) bar.style.width='100%'; show(0);
  // Freeze everything at t=0 immediately — otherwise animations run on the
  // WALL clock until the first __step pauses them (the frame-0 screenshot
  // takes real time), which put subtitles ~0.5s ahead of the scenes.
  for (const a of document.getAnimations({{subtree:true}})) {{
    try {{ a.pause(); a.currentTime = 0; }} catch(e) {{}}
  }}
}};
window.__step = function(ms){{
  for (const a of document.getAnimations({{subtree:true}})) {{
    try {{ a.pause(); a.currentTime = (a.currentTime || 0) + ms; }} catch(e) {{}}
  }}
}};
// Video clips don't follow the animation clock — the renderer seeks them to the
// scene-local time each frame (loops when the clip is shorter than the scene).
// Returns a Promise that resolves when the seeked frame is decoded.
window.__seekVideos = function(idx, t){{
  const sc = scenes[idx];
  const vids = sc ? sc.querySelectorAll('video') : [];
  const ps = [];
  for (const v of vids) {{
    const d = (isFinite(v.duration) && v.duration > 0.1) ? v.duration : 0;
    const target = d ? (t % d) : t;
    if (Math.abs((v.currentTime || 0) - target) < 0.004) continue;
    ps.push(new Promise((res) => {{
      const done = () => {{ v.removeEventListener('seeked', done); res(1); }};
      v.addEventListener('seeked', done);
      setTimeout(done, 300);   // decode-stall guard
      try {{ v.currentTime = target; }} catch(e) {{ done(); }}
    }}));
  }}
  return Promise.all(ps);
}};
// QA: open with #2 (or #scene=2) to freeze on that scene for a screenshot.
const _manual = location.hash.includes('manual');
const _jump = (location.hash.match(/(\\d+)/) || [])[1];
requestAnimationFrame(()=>{{
  if(_manual) return;
  stage.classList.add('go');
  if(bar) bar.style.width='100%';
  if(_jump !== undefined) show(parseInt(_jump,10)); else run(0);
}});
</script></body></html>"""


def _json(obj):
    import json
    return json.dumps(obj)


# ── media scene (base-rendered; styles never see type=media) ─────────────────
def media_scene(i, sc, ctx, kb_class="kb0", dur=8.0, fit=False, aspect=None):
    """Real imagery — a screenshot/photo OR a video clip — with an optional
    caption chip. This is the anti-PPT workhorse: the screen shows the THING
    being talked about, the subtitle layer carries the words.

    Images get a Ken Burns move. Video clips (sc['video'], webm/vp8|vp9 only —
    headless chromium has no h264) are seeked frame-by-frame by the renderer;
    sc['_poster'] (extracted first frame) feeds the fit-mode blur layer.

    fit=True (landscape/wide material): blurred cover fill behind a contained
    sharp copy — nothing gets cropped away. fit=False (tall material): full-bleed
    cover."""
    accent = ctx.get("accent", "#FF2E4D")
    cap = sc.get("caption")
    cap_html = (f'<div class="media-cap" style="background:{rgba(accent, 0.92)}">{esc(cap)}</div>'
                if cap else "")
    # ── auto-fit the layout to the material's shape ──────────────────────────
    # fit-mode panel: height follows the material's own aspect (fills the panel
    # exactly, no letterbox inside); wide strips sit higher; the overlay card
    # moves BELOW a wide panel instead of floating over blur.
    W_, H_ = 1080, 1920
    panel_style, ovl_style = "", ""
    if fit:
        a = aspect if (aspect and aspect > 0.05) else 1.4
        panel_w = int(W_ * 0.92)
        panel_h = int(min(panel_w / a, H_ * 0.66))
        center_y = 0.38 if a >= 1.3 else 0.44
        panel_top = max(int(H_ * center_y - panel_h / 2), 170)
        panel_style = (f'style="top:{panel_top}px;height:{panel_h}px;'
                       f'transform:translateX(-50%)"')
        if a >= 1.3:
            ovl_style = f'style="top:{panel_top + panel_h + 40}px"'
    ovl = sc.get("overlay") or {}
    ovl_html = ""
    if ovl.get("value") or ovl.get("text"):
        val = (f'<div class="ov" style="color:{accent}">{esc(ovl["value"])}</div>'
               if ovl.get("value") else "")
        lab = (f'<div class="ol">{esc(ovl.get("label") or ovl.get("text"))}</div>'
               if (ovl.get("label") or ovl.get("text")) else "")
        acc_style = f'style="--ovl-accent:{accent}"' if not ovl_style else \
            ovl_style[:-1] + f';--ovl-accent:{accent}"'
        ovl_html = f'<div class="media-ovl" {acc_style}>{val}{lab}</div>'
    vid = esc(str(sc.get("video", "")))
    img = esc(str(sc.get("image", "")))
    # fit mode sits on the style canvas (style background shows through); the
    # panel gets a hairline accent frame so it reads as designed, not floated
    frame = f'border:3px solid {rgba(accent, 0.55)}'
    if fit:
        panel_style = panel_style[:-1] + f';{frame}"' if panel_style \
            else f'style="{frame}"'
    if vid:
        if fit:
            body = (f'<div class="media-canvas"></div>'
                    f'<div class="media-fitpos" {panel_style}>'
                    f'<video class="media-fit" src="file://{vid}" muted preload="auto"></video>'
                    f'</div>')
        else:
            body = (f'<div class="media-wrap">'
                    f'<video class="media-img" src="file://{vid}" muted preload="auto"></video></div>')
    elif fit:
        body = (f'<div class="media-canvas"></div>'
                f'<div class="media-fitpos" {panel_style}><img class="media-fit" src="file://{img}"></div>')
    else:
        body = (f'<div class="media-wrap"><img class="media-img {kb_class}" src="file://{img}"></div>')
    scrim = "" if fit else '<div class="media-scrim"></div>'
    return (f'<section class="scene media-scene" data-i="{i}" style="--kbd:{dur:.2f}s">'
            f'{body}{scrim}{cap_html}{ovl_html}</section>')


def diagram_scene(i, sc, ctx, dur=8.0):
    """Architecture/flow diagram whose elements land step by step, timed to the
    narration (「讲架构的，一个一个走」). Spec:

      {"type":"diagram","say":"...","title":"整体架构",
       "nodes":[{"label":"用户","sub":"App/Web"},{"label":"API 网关"},{"label":"模型服务"}],
       "edges":["请求","转发"]}   # edge i sits between node i and node i+1 (label optional: "" )

    Vertical chain layout (9:16-native). Each arrow lands TOGETHER with the
    node it points to (a lone arrow into blank space read as broken — shipped
    2026-07-17/18), and the whole build-out finishes inside the first ~50% of
    the scene. The backdrop panel hugs the chain instead of covering the whole
    frame (a full-screen near-empty white card was the #1 「烂尾卡」 complaint):
    short chains scale UP to fill it, long chains scale down to protect the
    subtitle band."""
    accent = ctx.get("accent", "#FF2E4D")
    nodes = sc.get("nodes") or []
    edges = sc.get("edges") or []
    n = len(nodes)
    if n == 0:
        return f'<section class="scene" data-i="{i}"></section>'
    # one step per node; the arrow into node k shares node k's timeslot
    span = max(min(dur * 0.5, n * 0.9), 1.0)
    slot = span / max(n, 1)
    dark = "#10131a"
    parts = []
    title = sc.get("title")
    title_html = (f'<div class="diag-title" style="color:{dark}">{esc(title)}</div>'
                  if title else "")
    for idx, nd in enumerate(nodes):
        if isinstance(nd, str):
            nd = {"label": nd}
        t = idx * slot
        if idx > 0:
            label = edges[idx - 1] if idx - 1 < len(edges) else ""
            elabel = (f'<span class="elabel" style="background:{rgba(accent, 0.12)};'
                      f'color:{dark};border:2px solid {rgba(accent, 0.5)}">{esc(label)}</span>'
                      if label else "")
            parts.append(
                f'<div class="diag-arrow" style="--nd:{t:.2f}s">'
                f'<div class="shaft" style="background:{rgba(accent, 0.8)}"></div>'
                f'<div class="head" style="border-top-color:{rgba(accent, 0.9)}"></div>'
                f'{elabel}</div>')
        sub = f'<span class="sub2">{esc(nd.get("sub"))}</span>' if nd.get("sub") else ""
        bg = rgba(accent, 0.14) if idx % 2 == 0 else "rgba(255,255,255,.92)"
        border = f"3px solid {rgba(accent, 0.85)}"
        parts.append(
            f'<div class="diag-node" style="--nd:{t:.2f}s;background:{bg};'
            f'border:{border};color:{dark}">{esc(nd.get("label", ""))}{sub}</div>')
    # Size the panel to the CONTENT. Short chains scale up (fill the panel,
    # no dead space); long chains scale down so they never spill into the
    # subtitle band (bottom ~420px; 2026-07-15 user report).
    est_h = (156 if title else 0) + n * 134 + max(n - 1, 0) * 64
    max_h = 1240.0                      # room between header band and subs
    upscale = 1.35 if n <= 3 else 1.15
    scale = min(upscale, max_h / max(est_h, 1))
    panel_h = int(est_h * scale + 150)
    center_y = 820                      # visual center between chrome and subs
    panel_top = max(center_y - panel_h // 2, 130)
    return (f'<section class="scene diagram-scene" data-i="{i}">'
            f'<div style="position:absolute;left:52px;right:52px;'
            f'top:{panel_top}px;height:{panel_h}px;'
            f'background:rgba(250,250,252,.94);border-radius:34px;'
            f'box-shadow:0 40px 110px rgba(0,0,0,.35)"></div>'
            f'<div class="diag-wrap" style="--dgscale:{scale:.3f};'
            f'top:{panel_top + panel_h // 2}px">'
            f'{title_html}{"".join(parts)}</div></section>')


# ── speech-synced subtitles ──────────────────────────────────────────────────
# CJK punctuation always splits; western ,.!?;: split only when they touch a
# CJK char (protects "GPT-5.5" / "v2.0" but catches 「64队了,因凡蒂诺」).
_SUB_SPLIT = re.compile(
    r"[，。！？；、：\s]+|……|…|——"
    r"|[,.!?;:]+(?=[一-鿿])|(?<=[一-鿿])[,.!?;:]+")
_SUB_STRIP = " ，。！？；、：,.!?;:…—"
_SUB_NUM = re.compile(r"(\d+(?:\.\d+)?[%％]?(?:[万亿千百倍块元年月日号])?|[A-Za-z][A-Za-z0-9.\-]{1,14})")


# natural break points inside an unpunctuated clause: AFTER a particle/aux
# (的了着过就都也还才是在把被让给跟和与或), or BEFORE a connective (但因所如果
# 虽然). Splitting anywhere else risks slicing a word in half (「就暴|露了」
# shipped in a published video 2026-07-17).
_SUB_BREAK_AFTER = "的了着过就都也还才是在把被让给跟和与或"
_SUB_BREAK_BEFORE_RE = re.compile(r"[但因所若虽]|如果|但是|所以|因为|虽然|然后|结果|不过|而且")
_SUB_TOKEN_RE = re.compile(r"\d+(?:\.\d+)?[%％]?|[A-Za-z][A-Za-z0-9.\-]*")


def _split_points(p):
    """Candidate split indices for clause p, best-first is NOT implied — the
    caller picks the one closest to its target. Points never fall inside a
    number/latin token."""
    banned = set()
    for m in _SUB_TOKEN_RE.finditer(p):
        banned.update(range(m.start() + 1, m.end()))
    pts = set()
    for i, ch in enumerate(p[:-1]):
        if ch in _SUB_BREAK_AFTER and (i + 1) not in banned:
            pts.add(i + 1)
    for m in _SUB_BREAK_BEFORE_RE.finditer(p):
        if m.start() > 0 and m.start() not in banned:
            pts.add(m.start())
    # a number/latin token starts a new visual unit — breaking right before it
    # beats slicing the CJK word that precedes it
    for m in _SUB_TOKEN_RE.finditer(p):
        if m.start() > 0:
            pts.add(m.start())
    return pts


def _split_clause(p, max_len):
    """Split an over-long unpunctuated clause at natural boundaries. Pieces
    stay balanced (no 14+3 orphans): each cut targets the midpoint of what
    remains, snapping to the nearest natural break; falls back to the plain
    balanced cut only when no break point is anywhere near."""
    out = []
    while len(p) > max_len:
        pieces = -(-len(p) // max_len)          # ceil
        target = -(-len(p) // pieces)           # balanced piece length
        pts = _split_points(p)
        # nearest natural break within ±4 of the target (may overshoot max_len
        # by 2 — the subtitle font auto-shrinks), else balanced cut; never
        # leave a fragment shorter than 3 chars on either side. A cut whose
        # NEXT char is a trailing particle strands it (「花在|了你…」shipped
        # in QA) — deprioritize those.
        cands = [i for i in pts if abs(i - target) <= 4 and 3 <= i <= len(p) - 3
                 and i <= max_len + 2]
        cut = min(cands, key=lambda i: (p[i] in _SUB_BREAK_AFTER, abs(i - target))) \
            if cands else target
        out.append(p[:cut])
        p = p[cut:]
    if p:
        out.append(p)
    return out


def _sub_chunks(say, max_len=15):
    """Split narration into subtitle-sized phrase chunks (CJK ≤max_len each).
    Punctuation splits first; over-long clauses split at natural word
    boundaries (particles/connectives), balanced, never inside numbers or
    latin tokens."""
    parts = [p.strip(_SUB_STRIP) for p in _SUB_SPLIT.split(str(say or "")) if p]
    chunks = []
    for p in parts:
        if not p:
            continue
        if len(p) <= max_len:
            chunks.append(p)
            continue
        chunks.extend(_split_clause(p, max_len))
    return [c for c in chunks if c]


def _sub_div(text, t, dur, accent):
    fs = 62 if len(text) <= 10 else (54 if len(text) <= 13 else 48)
    body, last = [], 0
    for m in _SUB_NUM.finditer(text):
        body.append(esc(text[last:m.start()]))
        body.append(f'<span class="kw" style="color:{accent}">{esc(m.group(1))}</span>')
        last = m.end()
    body.append(esc(text[last:]))
    return (f'<div class="sub" style="--d:{t:.2f}s;--len:{dur:.2f}s;font-size:{fs}px">'
            f'{"".join(body)}</div>')


def build_subs_html(scenes, durs, accent, timings=None, pad=0.28):
    """One .sub div per phrase. When the audio builder supplies real per-phrase
    timings (start, end, text — scene-local), subtitles sync EXACTLY to the
    voice; otherwise fall back to char-proportional estimates."""
    out, t0 = [], 0.0
    for idx, (sc, d) in enumerate(zip(scenes, durs)):
        sc_t = timings[idx] if (timings and idx < len(timings)) else None
        if sc_t:
            for (s, e, text) in sc_t:
                out.append(_sub_div(text, t0 + s, max(e - s, 0.3), accent))
        else:
            chunks = _sub_chunks(sc.get("say", ""))
            speech = max(d - pad, 0.4)
            total_chars = sum(len(c) for c in chunks) or 1
            t = t0
            for c in chunks:
                cd = speech * len(c) / total_chars
                out.append(_sub_div(c, t, cd, accent))
                t += cd
        t0 += d
    return "".join(out)


def seed_from(spec, out_path=""):
    """Stable-ish per-video seed: topic/title + out filename. Differs per video,
    reproducible for a given (topic, filename)."""
    key = (str(spec.get("title", "")) + str(spec.get("tag", "")) +
           str(spec.get("_topic", "")) + os.path.basename(out_path or "") +
           (spec.get("scenes", [{}])[0].get("say", "") if spec.get("scenes") else ""))
    if not key.strip():
        key = "richlib"
    return int(hashlib.md5(key.encode("utf-8")).hexdigest()[:12], 16)
