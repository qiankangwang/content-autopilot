#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_obsidian — V3 「Dark Matter」旗舰视觉系统 (DESIGN-V3, 2026-07-24).

一台在暗处工作的精密仪器：数据被测量、被点亮、被证明。取代旧 5-皮肤轮换。
色彩永远只编码语义（accent=确认/高亮, data=信号/数字/轨道, warn=真负向数据）。

════════════════════════════════════════════════════════════════════════════
ENGINE CONTRACT — spec 字段契约 (主线程按此接线 make_rich_video.build_html)
════════════════════════════════════════════════════════════════════════════
build_html 目前只拦截 type=="media" / type=="diagram" 交给 base.*_scene；其余
类型 (hook/stat/compare/outro/code/bullets/evidence/kinetic) 都会自然落到
style.scene(i, sc, ctx)。因此本 style 需要引擎侧做且仅做两件事：

  1. 【必须】obsidian 激活时，type=="diagram" 不要再走 base.diagram_scene，
     改路由到 style.scene() —— 本 style 用「轨道线」范式重写了 diagram，
     base 的方框箭头版（浅色面板）在深色画布上会视觉打架。
  2. 【建议】把新类型 "evidence" / "kinetic" 加进 validate_spec 的合法 type
     白名单（它们已经会落到 style.scene，无需额外 dispatch）。

media 仍由 base.media_scene 渲染，本 style 只用 CSS 皮肤化 .media-* 类；
evidence 是本 style 自渲染的「浅色证据卡」，专用于网页/论文截图（不要走 media）。

── 各 type 消费的 spec 字段 ────────────────────────────────────────────────
hook      { type, say, lines:[≤2 行,每行≤9字], eyebrow?, image?|video? 可选底图 }
kinetic   { type, say, lines:[短词/短句], accent_line? int=高亮第几行(默认末行),
            sub? }                                        # 新类型：大字动感排版
stat      { type, say, value:"89"|"3.7亿"|"1200"(数字滚动只滚前导整数),
            unit?, label:上下文一句, warn? bool=负向数据用红 }
diagram   { type, say, title?, nodes:[≤4 个 {label:≤8字, sub?:≤12字}] }
                                                          # 轨道线，非方框箭头
compare   { type, say,
            a:{label, value, unit?, pct:0-100}, b:{...}, # 双实心条(数字在条外)
            或 before:"文字", after:"文字" }              # 退化为状态对比双行
evidence  { type, say, image:截图路径, source?:"来源: 新华社",
            highlight?:证据卡上浮一句高亮 }               # 新类型：浅色证据卡
code      { type, say, code, lang?, caption? }
bullets   { type, say, head?, lines:[...] }               # 保留但不鼓励
outro     { type, say, lines:[...] }

ctx (variant 产出) 关键字段：accent(每日绿/琥珀/紫三选一,语义不变), data(信号蓝),
warn(负向红), paper/ink(证据卡浅色子语言)。
"""
import re
from .base import Style, esc, rgba, mix, big_fs, highlight, blob, scene_types

# ── 每日色相轮换：仅 accent 变，语义固定 (green→amber→violet) ─────────────────
_HUES = ["green", "amber", "violet"]
_ACCENT = {"green": "#3DDC97", "amber": "#F2B45C", "violet": "#B58CFF"}
_DATA = "#4FC3F7"   # 信号蓝 — 图表/数字/轨道 (不随色相变)
_WARN = "#FF5D5D"   # 负向数据专用 (不随色相变)
_PAPER = "#F4F5F3"  # 证据卡纸白
_INK = "#131920"    # 证据卡墨色

_FONT_H1 = '"Smiley Sans Oblique","Smiley Sans","得意黑","Noto Sans CJK SC",sans-serif'
_FONT = '"Noto Sans CJK SC","Source Han Sans SC",sans-serif'
_FONT_MONO = '"JetBrains Mono","Noto Sans Mono CJK SC","DejaVu Sans Mono",monospace'


def _fill(css, m):
    for k, v in m.items():
        css = css.replace(k, str(v))
    return css


def _blur_lines(lines, base_fs, accent, accent_last=True, font=_FONT_H1):
    """Headline stack, each line a blur-focus entrance (staggered). Last line
    optionally painted in accent. Digits/latin stay tabular for instrument feel."""
    fs = big_fs(lines, base=base_fs)
    n = len(lines)
    out = []
    for j, x in enumerate(lines):
        col = f"color:{accent}" if (accent_last and j == n - 1) else ""
        out.append(
            f'<div class="om-h1 om-in" style="--d:{0.09 * j:.2f}s;font-size:{fs}px;'
            f'font-family:{font};{col}">{esc(x)}</div>')
    return "".join(out)


class ObsidianStyle(Style):
    id = "obsidian"
    weight = 6.0            # flagship default (old 5 styles kept low as fallback)
    label = "暗物质"
    own_transitions = True  # hard cuts + in-scene blur-focus; engine entry pool skipped
    OWN_TYPES = ("diagram",)  # engine routes these to scene() instead of base.*_scene

    def affinity(self, spec):
        return 1.0          # handles every topic — it is the house system

    def variant(self, rng):
        # hue is drawn from the seeded rng (seed folds in spec tag/title/topic →
        # per-video rotation, semantics unchanged). Per-type layout picks add
        # within-style variety so a run of videos never looks stamped.
        hue = rng.choice(_HUES)
        accent = _ACCENT[hue]
        return {
            "accent": accent,
            "hue": hue,
            "data": _DATA,
            "warn": _WARN,
            "paper": _PAPER,
            "ink": _INK,
            "hook": rng.choice(["stack", "backdrop"]),
            "compare": rng.choice(["bars", "state"]),
            "diagram_side": rng.choice(["right", "alt"]),
        }

    def css(self, ctx):
        a = ctx["accent"]
        d = ctx["data"]
        return _fill(_CSS, {
            "__BG__": "#0A0E14",
            "__CARD__": "#131920",
            "__FG__": "#E8ECEF",
            "__SUB__": "#7A8794",
            "__GRID__": "#1E2630",
            "__ACCENT__": a,
            "__DATA__": d,
            "__WARN__": ctx["warn"],
            "__PAPER__": ctx["paper"],
            "__INK__": ctx["ink"],
            "__A08__": rgba(a, .08),
            "__A14__": rgba(a, .14),
            "__A22__": rgba(a, .22),
            "__A45__": rgba(a, .45),
            "__A70__": rgba(a, .70),
            "__D14__": rgba(d, .14),
            "__D45__": rgba(d, .45),
            "__ADARK__": mix(a, "#0A0E14", .74),
        })

    def background(self, ctx):
        # ambient dark-matter field: a drifting measurement grid (≤6% opacity),
        # one faint accent nebula (low), a soft edge vignette. Guarantees a hook
        # is NEVER a dead-black text card, without ever competing with content.
        return ('<div class="om-grid"></div>'
                '<div class="om-neb"></div>'
                '<div class="om-vig"></div>')

    def chrome(self, spec, ctx):
        return ""   # no corner branding (user decision 2026-07-18)

    # ── dispatch ────────────────────────────────────────────────────────────
    def scene(self, i, sc, ctx):
        t = sc.get("type", "hook")
        fn = {
            "hook": self._hook, "kinetic": self._kinetic, "stat": self._stat,
            "diagram": self._diagram, "compare": self._compare,
            "evidence": self._evidence, "code": self._code,
            "bullets": self._bullets, "outro": self._outro,
        }.get(t)
        if fn:
            return fn(i, sc, ctx)
        # sane fallback: treat unknown as a kinetic headline (never a blank card)
        return self._kinetic(i, sc, ctx)

    # ── hook: kinetic headline over the drift field, optional dimmed backdrop ──
    def _hook(self, i, sc, ctx):
        accent = ctx["accent"]
        lines = sc.get("lines") or [sc.get("say", "")]
        eb = (f'<div class="om-eyebrow om-in">{esc(sc["eyebrow"])}</div>'
              if sc.get("eyebrow") else "")
        backdrop = self._backdrop(sc)
        body = _blur_lines(lines, 128, accent, accent_last=True)
        cls = "scene om-scene hook" + (" has-bg" if backdrop else "")
        return (f'<section class="{cls}" data-i="{i}">{backdrop}'
                f'<div class="om-wrap">{eb}<div class="om-heads">{body}</div>'
                f'<div class="om-rail-mini om-grow"></div></div></section>')

    # ── kinetic: big staggered typography, one line swept in accent ───────────
    def _kinetic(self, i, sc, ctx):
        accent = ctx["accent"]
        lines = sc.get("lines") or [sc.get("say", "")]
        hi = sc.get("accent_line")
        hi = (len(lines) - 1) if hi is None else int(hi)
        fs = big_fs(lines, base=138)
        out = []
        for j, x in enumerate(lines):
            if j == hi:
                out.append(
                    f'<div class="om-k1" style="--d:{0.11 * j:.2f}s;font-size:{fs}px">'
                    f'<span class="om-sweep" style="color:{accent}">{esc(x)}</span></div>')
            else:
                out.append(
                    f'<div class="om-k1 om-in" style="--d:{0.11 * j:.2f}s;'
                    f'font-size:{fs}px">{esc(x)}</div>')
        sub = (f'<div class="om-ksub om-in" style="--d:{0.11 * len(lines):.2f}s">'
               f'{esc(sc["sub"])}</div>' if sc.get("sub") else "")
        return (f'<section class="scene om-scene kinetic" data-i="{i}">'
                f'<div class="om-wrap">{"".join(out)}{sub}</div></section>')

    # ── stat: hero digit with a pure-CSS roll-up counter (no JS RAF) ──────────
    def _stat(self, i, sc, ctx):
        num_col = ctx["warn"] if sc.get("warn") else ctx["data"]
        raw = str(sc.get("value", ""))
        unit = esc(sc.get("unit", ""))
        label = esc(sc.get("label", ""))
        m = re.match(r"^\s*(-?)([0-9][0-9,]*)(.*)$", raw)
        cover_final = ""  # scene-0 freeze needs the counter parked at target
        if m and m.group(2):
            sign = esc(m.group(1))
            intval = int(m.group(2).replace(",", ""))
            suffix = esc(m.group(3))
            pn = f"--rn{i}"
            kf = f"omRoll{i}"
            unit_html = f'<span class="om-unit">{unit}</span>' if unit else ""
            num_html = (
                f'<div class="om-num" style="color:{num_col}">'
                f'<span class="om-sign">{sign}</span>'
                f'<span class="om-roll om-roll{i}"></span>'
                f'<span class="om-sfx">{suffix}</span>{unit_html}</div>')
            # per-scene @property + keyframes + counter wiring, data-i scoped.
            inj = (
                f'<style>'
                f'@property {pn}{{syntax:"<integer>";initial-value:0;inherits:false}}'
                f'@keyframes {kf}{{from{{{pn}:0}}to{{{pn}:{intval}}}}}'
                f'.om-roll{i}{{counter-reset:r{i} var({pn})}}'
                f'.om-roll{i}::after{{content:counter(r{i})}}'
                f'.scene[data-i="{i}"].active .om-roll{i}{{'
                f'animation:{kf} .82s cubic-bezier(.16,1,.3,1) forwards;{pn}:{intval}}}'
                # scene-0 is the cover / frame-0 screenshot — park at target, no roll
                f'.scene[data-i="{i}"]:first-of-type .om-roll{i}{{'
                f'{pn}:{intval};animation:none}}'
                f'</style>')
        else:
            # non-numeric value → static blur-focus number, no counter
            num_html = (f'<div class="om-num om-in" style="color:{num_col}">'
                        f'{esc(raw)}<span class="om-unit">{unit}</span></div>')
            inj = ""
        return (f'<section class="scene om-scene stat" data-i="{i}">{inj}'
                f'<div class="om-wrap"><div class="om-statset om-settle">{num_html}'
                f'<div class="om-statlabel om-in" style="--d:.34s">{label}</div>'
                f'</div></div></section>')

    # ── diagram: TRACK LINE — one glowing rail, ≤4 lit nodes, labels by rail ──
    def _diagram(self, i, sc, ctx):
        accent = ctx["accent"]
        nodes = sc.get("nodes") or []
        nodes = nodes[:4]
        n = len(nodes)
        if n == 0:
            return self._kinetic(i, sc, ctx)
        title = (f'<div class="om-dgtitle om-in">{esc(sc["title"])}</div>'
                 if sc.get("title") else "")
        parts = []
        for idx, nd in enumerate(nodes):
            if isinstance(nd, str):
                nd = {"label": nd}
            top = 12.0 + (idx * (76.0 / (n - 1)) if n > 1 else 38.0)
            delay = 0.35 + idx * 0.34   # 错峰点亮, synced past the rail draw
            # labels always float to the RIGHT of the rail (portrait-safe: a
            # left label would overflow the 72px margin on long node text)
            sub = (f'<span class="om-nsub">{esc(nd.get("sub"))}</span>'
                   if nd.get("sub") else "")
            parts.append(
                f'<div class="om-node r" style="top:{top:.1f}%;--d:{delay:.2f}s">'
                f'<span class="om-dot"></span>'
                f'<span class="om-nlabel">{esc(nd.get("label", ""))}{sub}</span>'
                f'</div>')
        return (f'<section class="scene om-scene diagram" data-i="{i}">{title}'
                f'<div class="om-rail">'
                f'<div class="om-line om-draw"></div>'
                f'<div class="om-sweepdot"></div>'
                f'{"".join(parts)}</div></section>')

    # ── compare: two solid bars (digits outside) OR state contrast ────────────
    def _compare(self, i, sc, ctx):
        accent, data, warn = ctx["accent"], ctx["data"], ctx["warn"]
        a, b = sc.get("a"), sc.get("b")
        if a and b and ("pct" in a or "value" in b):
            def bar(side, item, col, delay):
                pct = max(0.0, min(100.0, float(item.get("pct", 0) or 0)))
                val = esc(str(item.get("value", "")))
                unit = esc(str(item.get("unit", "")))
                lab = esc(str(item.get("label", "")))
                return (
                    f'<div class="om-barrow">'
                    f'<div class="om-barlab">{lab}</div>'
                    f'<div class="om-bartrack">'
                    f'<div class="om-bar {side} om-fill" '
                    f'style="--w:{pct:.1f}%;background:{col};--d:{delay:.2f}s"></div>'
                    f'<div class="om-barval om-in" style="--d:{delay + 0.3:.2f}s">'
                    f'{val}<span class="om-barunit">{unit}</span></div></div></div>')
            body = (bar("a", a, warn if a.get("worse") else _mix_dim(data), 0.15)
                    + bar("b", b, accent, 0.35))
            return (f'<section class="scene om-scene compare bars" data-i="{i}">'
                    f'<div class="om-wrap">{body}</div></section>')
        # state contrast: old recedes (dim, struck), new comes forward (lit)
        before, after = esc(sc.get("before", "")), esc(sc.get("after", ""))
        return (f'<section class="scene om-scene compare state" data-i="{i}">'
                f'<div class="om-wrap">'
                f'<div class="om-cmp old om-in" style="--d:.05s">'
                f'<span class="om-cmptag">之前</span>'
                f'<span class="om-cmptxt">{before}</span></div>'
                f'<div class="om-cmp new om-in" style="--d:.24s">'
                f'<span class="om-cmptag" style="color:{accent}">之后</span>'
                f'<span class="om-cmptxt">{after}</span></div></div></section>')

    # ── evidence: light paper card framing a webpage/paper screenshot ─────────
    def _evidence(self, i, sc, ctx):
        accent = ctx["accent"]
        img = esc(str(sc.get("image", "")))
        src = sc.get("source") or ""
        src_html = (f'<div class="om-evsrc">{esc(src)}</div>' if src else "")
        hi = (f'<div class="om-evhi om-in" style="--d:.4s;border-color:{accent}">'
              f'{esc(sc["highlight"])}</div>' if sc.get("highlight") else "")
        return (f'<section class="scene om-scene evidence" data-i="{i}">'
                f'<div class="om-evcard om-in" style="border-color:{rgba(accent, .9)}">'
                f'<div class="om-evframe">'
                f'<img class="om-evimg" src="file://{img}">'
                f'</div>{src_html}</div>{hi}</section>')

    # ── code: dark instrument card, syntax-lit, per-line blur-focus ───────────
    def _code(self, i, sc, ctx):
        lines = highlight(sc.get("code", ""), sc.get("lang", "python"))
        body = "".join(
            f'<div class="om-cl om-in" style="--d:{0.06 * j:.2f}s">{ln}</div>'
            for j, ln in enumerate(lines))
        cap = (f'<div class="om-codecap om-in" style="--d:.5s">{esc(sc["caption"])}</div>'
               if sc.get("caption") else "")
        lang = esc(sc.get("lang", "python"))
        return (f'<section class="scene om-scene code" data-i="{i}">'
                f'<div class="om-win om-in"><div class="om-winbar">'
                f'<span class="om-wtrace"></span><span class="om-wlang">{lang}</span>'
                f'</div><div class="om-wcode">{body}</div></div>{cap}</section>')

    # ── bullets: rail spine + lit nodes (retained, discouraged) ───────────────
    def _bullets(self, i, sc, ctx):
        rows = sc.get("lines", []) or []
        head = (f'<div class="om-bhead om-in">{esc(sc["head"])}</div>'
                if sc.get("head") else "")
        items = "".join(
            f'<div class="om-brow om-in" style="--d:{0.13 * j:.2f}s">'
            f'<span class="om-bdot"></span>'
            f'<span class="om-btxt">{esc(x)}</span></div>'
            for j, x in enumerate(rows))
        return (f'<section class="scene om-scene bullets" data-i="{i}">'
                f'<div class="om-wrap">{head}'
                f'<div class="om-blist"><span class="om-bspine om-draw"></span>'
                f'{items}</div></div></section>')

    # ── outro: kinetic close + a rail sweep ───────────────────────────────────
    def _outro(self, i, sc, ctx):
        accent = ctx["accent"]
        lines = sc.get("lines") or [sc.get("say", "")]
        body = _blur_lines(lines, 118, accent, accent_last=True)
        backdrop = self._backdrop(sc)   # brand-image bookend with the hook
        cls = "scene om-scene outro" + (" has-bg" if backdrop else "")
        return (f'<section class="{cls}" data-i="{i}">{backdrop}'
                f'<div class="om-wrap"><div class="om-heads">{body}</div>'
                f'<div class="om-rail-mini om-grow"></div></div></section>')

    # ── shared: dimmed full-bleed backdrop for a hook (image or video) ────────
    def _backdrop(self, sc):
        vid = str(sc.get("video", ""))
        img = str(sc.get("image", ""))
        if vid:
            return (f'<div class="om-bd"><video class="om-bdmedia" '
                    f'src="file://{esc(vid)}" muted preload="auto"></video>'
                    f'<div class="om-bdscrim"></div></div>')
        if img:
            return (f'<div class="om-bd"><img class="om-bdmedia" '
                    f'src="file://{esc(img)}"><div class="om-bdscrim"></div></div>')
        return ""


def _mix_dim(hexc):
    # the "not-worse" comparison bar: signal blue softened so accent-b wins focus
    return mix(hexc, "#0A0E14", .28)


_CSS = r"""
html,body{background:__BG__;font-family:__FONT__;color:__FG__}
.bar{background:__ACCENT__;box-shadow:0 0 16px __A45__;height:6px}

/* ══ ambient dark-matter field (background layer, every scene) ══════════════ */
.om-grid{position:absolute;inset:-4%;z-index:0;pointer-events:none;opacity:.055;
  background-image:linear-gradient(__GRID__ 1px,transparent 1px),
    linear-gradient(90deg,__GRID__ 1px,transparent 1px);
  background-size:96px 96px;animation:omDrift 11s linear infinite}
@keyframes omDrift{from{transform:translate(0,0)}to{transform:translate(96px,96px)}}
.om-neb{position:absolute;z-index:0;pointer-events:none;width:1200px;height:1200px;
  left:-260px;top:-320px;border-radius:50%;filter:blur(140px);opacity:.16;
  background:radial-gradient(circle,__ACCENT__,transparent 62%)}
.om-vig{position:absolute;inset:0;z-index:1;pointer-events:none;
  background:radial-gradient(ellipse 130% 110% at 50% 40%,transparent 58%,rgba(3,5,9,.6))}

/* ══ motion: kill base wobble + engine entry pool on TEXT scenes ════════════
   (DESIGN-V3: entrances are per-child blur-focus, not the rise/slide pool;
   only full-bleed media keeps a gentle 1.0→1.04 drift). ═══════════════════ */
.scene.active,
.scene.active.tr-rise,.scene.active.tr-slidel,.scene.active.tr-slider,
.scene.active.tr-zoom,.scene.active.tr-drop{animation:none}
.scene.media-scene.active,
.scene.media-scene.active.tr-rise,.scene.media-scene.active.tr-slidel,
.scene.media-scene.active.tr-slider,.scene.media-scene.active.tr-zoom,
.scene.media-scene.active.tr-drop{animation:omMediaDrift 16s linear forwards}
@keyframes omMediaDrift{0%{transform:scale(1.0)}100%{transform:scale(1.04)}}

/* entrance vocabulary */
@keyframes omBlur{0%{opacity:0;filter:blur(8px);transform:translateY(24px)}
  100%{opacity:1;filter:blur(0);transform:translateY(0)}}
@keyframes omSweep{0%{clip-path:inset(0 100% 0 0)}100%{clip-path:inset(0 0 0 0)}}
@keyframes omGrow{0%{width:0}100%{width:180px}}
@keyframes omDraw{0%{transform:scaleY(0)}100%{transform:scaleY(1)}}
@keyframes omSettle{0%{transform:translateY(10px)}70%{transform:translateY(-4px)}
  100%{transform:translateY(0)}}
@keyframes omNode{0%{opacity:0;transform:scale(.4)}
  60%{opacity:1;transform:scale(1.18)}100%{opacity:1;transform:scale(1)}}
@keyframes omSweepDot{0%{top:-8%;opacity:0}8%{opacity:1}92%{opacity:1}
  100%{top:100%;opacity:0}}
@keyframes omFill{0%{width:0}100%{width:var(--w)}}
@keyframes omKB{0%{transform:scale(1.0)}100%{transform:scale(1.06)}}

.scene.active .om-in{animation:omBlur .32s cubic-bezier(.16,1,.3,1) both;
  animation-delay:var(--d,0s)}
.scene.active .om-sweep{animation:omSweep .2s linear both .12s}
.scene.active .om-grow{animation:omGrow .5s cubic-bezier(.16,1,.3,1) both .3s}
.scene.active .om-settle{animation:omSettle .82s cubic-bezier(.16,1,.3,1) both}

/* ══ layout scaffold ═══════════════════════════════════════════════════════ */
.om-scene{padding:0 72px;justify-content:center;align-items:flex-start;text-align:left}
.om-wrap{position:relative;z-index:3;width:100%;max-width:936px}
.om-eyebrow{font-family:__FONT__;font-weight:700;font-size:34px;letter-spacing:6px;
  color:__ACCENT__;margin-bottom:26px;text-transform:uppercase}
.om-heads{position:relative}
.om-h1{font-weight:900;line-height:1.14;letter-spacing:1px;margin-bottom:6px}
.om-rail-mini{height:8px;width:0;border-radius:5px;margin-top:40px;
  background:linear-gradient(90deg,__ACCENT__,transparent);box-shadow:0 0 20px __A45__}

/* hook backdrop (dimmed full-bleed media under kinetic type) */
.om-bd{position:absolute;inset:0;z-index:0;overflow:hidden}
.om-bdmedia{width:100%;height:100%;object-fit:cover;opacity:.42;filter:saturate(.9)}
.scene.active .om-bdmedia{animation:omMediaDrift 16s linear forwards}
.om-bdscrim{position:absolute;inset:0;
  background:linear-gradient(180deg,rgba(10,14,20,.55),rgba(10,14,20,.86))}
.hook.has-bg .om-wrap{max-width:960px}

/* ══ kinetic ═══════════════════════════════════════════════════════════════ */
.kinetic .om-wrap{max-width:960px}
.om-k1{font-family:__FONT_H1__;font-weight:900;line-height:1.12;letter-spacing:1px;
  margin-bottom:8px}
.om-sweep{display:inline-block;font-family:__FONT_H1__}
.om-ksub{font-family:__FONT__;font-weight:500;font-size:46px;color:__SUB__;
  margin-top:26px;line-height:1.5}

/* ══ stat: hero digit + roll-up counter ════════════════════════════════════ */
.stat .om-wrap{max-width:960px}
.om-statset{position:relative}
.om-num{font-family:__FONT__;font-weight:900;font-size:300px;line-height:.92;
  letter-spacing:-6px;font-variant-numeric:tabular-nums;
  font-feature-settings:"tnum";display:flex;align-items:baseline;
  text-shadow:0 0 60px __D45__}
.om-num .om-sign{font-size:.7em}
.om-unit{font-size:.34em;font-weight:700;color:__SUB__;margin-left:14px;
  align-self:flex-end;letter-spacing:0}
.om-sfx{font-size:.9em}
.om-statlabel{font-family:__FONT__;font-weight:600;font-size:56px;color:__FG__;
  margin-top:24px;line-height:1.35;max-width:900px}

/* ══ diagram: track line ═══════════════════════════════════════════════════ */
.diagram{padding:0 64px}
.om-dgtitle{position:absolute;top:210px;left:64px;font-family:__FONT__;font-weight:900;
  font-size:60px;letter-spacing:1px;color:__FG__;z-index:4}
.om-rail{position:absolute;left:300px;top:330px;bottom:430px;width:2px;z-index:3}
.om-line{position:absolute;left:0;top:0;bottom:0;width:3px;border-radius:2px;
  transform-origin:top;background:linear-gradient(180deg,__ACCENT__,__D45__);
  box-shadow:0 0 18px __A45__}
.scene.active .om-draw{animation:omDraw .5s cubic-bezier(.16,1,.3,1) both}
.om-sweepdot{position:absolute;left:-7px;width:16px;height:16px;border-radius:50%;
  background:__ACCENT__;box-shadow:0 0 24px 6px __A70__;opacity:0}
.scene.active .om-sweepdot{animation:omSweepDot 2.6s linear both .5s}
.om-node{position:absolute;left:0;transform:translateY(-50%);display:flex;
  align-items:center;opacity:0}
.scene.active .om-node{animation:omNode .5s cubic-bezier(.16,1,.3,1) both;
  animation-delay:var(--d,0s)}
.om-dot{width:16px;height:16px;min-width:16px;border-radius:50%;margin-left:-7px;
  background:__ACCENT__;box-shadow:0 0 6px 2px __A70__,0 0 0 6px __A14__}
.om-node.r .om-nlabel{margin-left:34px}
.om-node.l{flex-direction:row-reverse}
.om-node.l .om-nlabel{margin-right:34px;text-align:right}
.om-nlabel{font-family:__FONT__;font-weight:700;font-size:52px;color:__FG__;
  line-height:1.1;white-space:nowrap}
.om-nsub{display:block;font-size:30px;font-weight:400;color:__SUB__;margin-top:6px}

/* ══ compare: bars / state ═════════════════════════════════════════════════ */
.compare .om-wrap{max-width:936px}
.om-barrow{margin:38px 0}
.om-barlab{font-family:__FONT__;font-weight:700;font-size:46px;color:__FG__;
  margin-bottom:16px}
.om-bartrack{position:relative;display:flex;align-items:center;height:78px}
.om-bar{height:78px;border-radius:10px;width:0}
.scene.active .om-fill{animation:omFill .7s cubic-bezier(.16,1,.3,1) both;
  animation-delay:var(--d,0s)}
.om-barval{font-family:__FONT__;font-weight:900;font-size:70px;margin-left:26px;
  color:__FG__;font-variant-numeric:tabular-nums;white-space:nowrap}
.om-barunit{font-size:.5em;font-weight:700;color:__SUB__;margin-left:8px}
.om-cmp{display:flex;align-items:center;gap:30px;padding:34px 40px;border-radius:18px;
  margin:18px 0;font-family:__FONT__;font-weight:800;font-size:64px}
.om-cmp.old{color:__SUB__;background:rgba(255,255,255,.03);
  border:1px solid __GRID__}
.om-cmp.old .om-cmptxt{text-decoration:line-through;text-decoration-color:__SUB__}
.om-cmp.new{color:__FG__;background:__A08__;border:1px solid __A45__;
  box-shadow:0 0 40px __A14__}
.om-cmptag{font-size:34px;font-weight:800;letter-spacing:4px;min-width:120px}

/* ══ evidence: light paper card ════════════════════════════════════════════ */
.evidence{justify-content:center;align-items:center;padding:0 84px}
.om-evcard{position:relative;z-index:3;width:100%;max-width:912px;
  background:__PAPER__;border:1px solid __ACCENT__;border-radius:14px;padding:32px;
  box-shadow:0 40px 120px rgba(0,0,0,.55)}
.om-evframe{overflow:hidden;border-radius:6px;background:#fff;max-height:1080px}
.om-evimg{width:100%;display:block;object-fit:cover}
.scene.active .om-evimg{animation:omKB 6s linear both}
.om-evsrc{position:absolute;right:24px;bottom:18px;font-family:__FONT__;font-weight:500;
  font-size:26px;letter-spacing:2px;color:__INK__;opacity:.62}
.om-evhi{position:absolute;left:96px;right:96px;bottom:250px;z-index:4;
  font-family:__FONT__;font-weight:800;font-size:46px;color:__FG__;line-height:1.4;
  background:rgba(10,14,20,.9);border-left:4px solid;padding:20px 26px;border-radius:10px}

/* ══ code ══════════════════════════════════════════════════════════════════ */
.code{justify-content:center;align-items:stretch;padding:0 64px}
.om-win{background:__CARD__;border:1px solid __GRID__;border-radius:18px;overflow:hidden;
  box-shadow:0 30px 80px rgba(0,0,0,.5)}
.om-winbar{display:flex;align-items:center;gap:16px;padding:20px 28px;
  background:rgba(255,255,255,.02);border-bottom:1px solid __GRID__}
.om-wtrace{width:56px;height:6px;border-radius:3px;background:__ACCENT__;
  box-shadow:0 0 12px __A45__}
.om-wlang{margin-left:auto;font-family:__FONT_MONO__;font-size:30px;color:__SUB__;
  letter-spacing:1px}
.om-wcode{padding:34px 38px;font-family:__FONT_MONO__;font-size:44px;line-height:1.5}
.om-cl{color:#C8D3F5;white-space:pre;overflow:hidden;text-overflow:ellipsis}
.t-kw{color:__ACCENT__;font-weight:700}.t-str{color:#9ECE6A}
.t-cmt{color:__SUB__;font-style:italic}.t-num{color:#FF9E64}
.t-fn{color:__DATA__}.t-dec{color:#E0AF68}
.om-codecap{font-family:__FONT__;font-weight:700;font-size:52px;color:__FG__;
  margin-top:34px}

/* ══ bullets ═══════════════════════════════════════════════════════════════ */
.bullets .om-wrap{max-width:936px}
.om-bhead{font-family:__FONT__;font-weight:900;font-size:72px;color:__FG__;
  margin-bottom:38px}
.om-blist{position:relative;padding-left:52px}
.om-bspine{position:absolute;left:14px;top:14px;bottom:14px;width:3px;border-radius:2px;
  transform-origin:top;background:linear-gradient(180deg,__ACCENT__,__D45__);
  box-shadow:0 0 16px __A45__}
.om-brow{display:flex;align-items:center;gap:30px;padding:26px 0}
.om-bdot{width:16px;height:16px;min-width:16px;border-radius:50%;margin-left:-46px;
  background:__ACCENT__;box-shadow:0 0 6px 2px __A70__,0 0 0 6px __A14__}
.om-btxt{font-family:__FONT__;font-weight:700;font-size:60px;color:__FG__;line-height:1.28}

/* ══ subtitles: DESIGN-V3 override (44px Noto Medium, white+deep stroke) ═════
   base emits inline font-size/weight → we win with !important. Lifted to
   y≈1428-1548 (never below 1550). Keyword accent kept from base inline color. */
.subs{bottom:372px}
.sub{font-family:__FONT__!important;font-weight:500!important;font-size:44px!important;
  color:#fff;background:rgba(8,11,16,.72);border:1px solid __GRID__;
  border-bottom:3px solid __A70__;border-radius:12px;
  -webkit-text-stroke:4px rgba(6,9,14,.92);paint-order:stroke fill;
  padding:8px 26px 12px;letter-spacing:1px;
  box-shadow:0 10px 30px rgba(0,0,0,.4)}
.sub .kw{font-weight:700}

/* ══ media skin (base renders media/diagram fallback; we reskin the classes) ═ */
.media-scrim{background:linear-gradient(transparent,rgba(6,9,14,.7))}
.media-canvas{background:
  radial-gradient(900px 760px at 16% 8%,__A14__,transparent 60%),
  radial-gradient(820px 700px at 86% 90%,__D14__,transparent 60%),
  radial-gradient(ellipse 140% 120% at 50% 42%,transparent 55%,rgba(3,5,9,.6)),
  __BG__}
.media-fit,.media-fitpos{border-radius:16px}
.media-cap{font-family:__FONT__;font-weight:700;background:__A70__;color:#06090e}
.media-ovl{background:rgba(10,14,20,.94);border-right:6px solid __ACCENT__}

/* ══ cover freeze: FIRST scene fully composed, no entrance (base contract) ══ */
.scene:first-of-type .om-in,.scene:first-of-type .om-sweep,
.scene:first-of-type .om-node,.scene:first-of-type .om-settle{
  animation:none;opacity:1;filter:none;transform:none;clip-path:none}
.scene:first-of-type .om-draw{animation:none;transform:scaleY(1)}
.scene:first-of-type .om-grow{animation:none;width:180px}
.scene:first-of-type .om-fill{animation:none;width:var(--w)}
.scene:first-of-type .om-sweepdot{animation:none;opacity:0}
"""

_CSS = _fill(_CSS, {
    "__FONT_H1__": _FONT_H1, "__FONT_MONO__": _FONT_MONO, "__FONT__": _FONT,
})
