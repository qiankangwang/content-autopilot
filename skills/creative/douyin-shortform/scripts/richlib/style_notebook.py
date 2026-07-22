#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_notebook — B · 手写笔记 (dot-grid/ruled paper, LXGW WenKai 楷体, marker/circle).

The most human, least-AI look: like a real person jotting notes for a friend.
variant() randomizes paper texture, palette, and a layout per scene type, so two
notebook videos never look the same. Needs LXGW WenKai (base.ensure_fonts ships it).

2026-07-19 anti-PPT pass (mirrors style_editorial): full-page notebook furniture
in background() (margin red line + washi tape corners + huge faint doodles),
15-25% bigger type on every text card, hand-drawn dashed frames on bullets/
compare, a ghost outlined numeral behind stats, and notebook skins for the base
.sub subtitle plate and .media-canvas fit backdrop (no more black blur / grey
pill). No corner branding of any kind (user decision 2026-07-18).
"""
from .base import Style, esc, big_fs, highlight, rgba

_INKS = ["#23262e", "#1d2733", "#2a2320"]
_ACCENTS = ["#e0533b", "#1f6feb", "#d98a00", "#2f8f5b", "#c0398f"]
_HILITES = ["#ffe14d", "#ffd23f", "#bdf0a6", "#a8e0ff", "#ffc6dd"]
_DOODLES = ["✗", "◯", "→", "☆", "?", "△"]


def _fill(css, m):
    for k, v in m.items():
        css = css.replace(k, str(v))
    return css


class NotebookStyle(Style):
    id = "notebook"
    weight = 1.1
    label = "手写"

    def affinity(self, spec):
        from .base import blob
        b = blob(spec)
        score = 1.15
        if any(k in b for k in ("我", "经验", "踩坑", "心得", "教程", "科普", "手把手", "聊聊", "说说", "其实", "笔记")):
            score *= 1.4
        return score

    def variant(self, rng):
        return {
            "accent": rng.choice(_ACCENTS),
            "ink": rng.choice(_INKS),
            "hilite": rng.choice(_HILITES),
            "paper": rng.choice(["dot", "ruled", "grid"]),
            # per-type LAYOUT pools — each is a compositionally distinct page,
            # not a cosmetic tweak (2026-07-22 「卡片单一」 feedback)
            "hook": rng.choice(["highlight", "circle", "underline"]),
            "stat": rng.choice(["ring", "arrow", "boxed"]),
            "bullets": rng.choice(["sticky", "margin", "numbered"]),
            "compare": rng.choice(["framed", "pages", "correction"]),
            "outro": rng.choice(["underline", "tape", "highlight"]),
            "tilt": rng.choice([-2, -1, 1, 2]),
            # page furniture randomness: which doodles haunt the margins, and
            # how the corner tape leans — same style, never the same page
            "doodles": rng.sample(_DOODLES, 3),
            "tape_tilt": rng.choice([-42, -36, 34, 40]),
        }

    def css(self, ctx):
        paper = {
            "dot": "background-color:#fcfbf6;background-image:radial-gradient(#c9d2dd 2.2px,transparent 2.3px);"
                   "background-size:40px 40px;background-position:20px 20px",
            "ruled": "background-color:#fcfbf6;background-image:repeating-linear-gradient("
                     "180deg,transparent 0 71px,#cdd6e0 71px 73px)",
            "grid": "background-color:#fcfbf6;background-image:linear-gradient(#dde4ec 1px,transparent 1px),"
                    "linear-gradient(90deg,#dde4ec 1px,transparent 1px);background-size:54px 54px",
        }[ctx["paper"]]
        return _fill(_CSS, {
            "__PAPER__": paper, "__INK__": ctx["ink"], "__ACCENT__": ctx["accent"],
            "__HILITE__": ctx["hilite"], "__TILT__": ctx["tilt"],
            "__TAPE__": rgba(ctx["hilite"], 0.5),
            "__TAPE_TILT__": ctx["tape_tilt"],
            "__INK_SOFT__": rgba(ctx["ink"], 0.4),
            "__INK_GHOST__": rgba(ctx["ink"], 0.09),
            "__WASH__": rgba(ctx["accent"], 0.10),
            "__WASH2__": rgba(ctx["accent"], 0.16),
        })

    def background(self, ctx):
        # full-page notebook furniture (decor, NOT branding): the ruled margin
        # red line, washi-tape corner stickers, and oversized barely-there
        # doodles. Fills the dead paper that made text cards read as an
        # unfinished PPT (2026-07-19 review).
        d0, d1, d2 = (esc(x) for x in ctx["doodles"])
        return ('<div class="nb-bg">'
                '<div class="nb-mline"></div><div class="nb-topline"></div>'
                '<div class="nb-tapecorner ta"></div><div class="nb-tapecorner tb"></div>'
                f'<div class="nb-doodle d0">{d0}</div>'
                f'<div class="nb-doodle d1">{d1}</div>'
                f'<div class="nb-doodle d2">{d2}</div>'
                '</div>')

    def chrome(self, spec, ctx):
        # no corner branding text (user decision 2026-07-18); the margin line
        # moved into background() with the rest of the page furniture
        return ''

    # ── decorations (inline SVG, accent-stroked) ──────────────────────────
    def _circle(self, ctx):
        a = ctx["accent"]
        return (f'<svg class="deco ring" viewBox="0 0 520 230" preserveAspectRatio="none">'
                f'<path d="M40,150 C10,40 180,16 320,22 C470,28 510,120 470,175 '
                f'C420,235 120,232 60,180 C44,165 40,158 40,150 Z" fill="none" '
                f'stroke="{a}" stroke-width="6" stroke-linecap="round"/></svg>')

    def _underline(self, ctx):
        a = ctx["accent"]
        return (f'<svg class="deco uline" viewBox="0 0 600 40" preserveAspectRatio="none">'
                f'<path d="M6,26 C140,10 300,34 420,18 C500,8 560,22 594,16" fill="none" '
                f'stroke="{a}" stroke-width="7" stroke-linecap="round"/></svg>')

    def _arrow(self, ctx, cls="harrow"):
        a = ctx["accent"]
        return (f'<svg class="deco {cls}" viewBox="0 0 180 140">'
                f'<path d="M12,16 C84,40 56,96 150,108" fill="none" stroke="{a}" stroke-width="6" stroke-linecap="round"/>'
                f'<path d="M150,108 l-30,-3 m30,3 l-9,-28" fill="none" stroke="{a}" stroke-width="6" stroke-linecap="round"/></svg>')

    def _check(self, ctx):
        a = ctx["accent"]
        return (f'<svg class="ck" viewBox="0 0 40 40"><path d="M7,22 L17,32 L34,8" fill="none" '
                f'stroke="{a}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>')

    def _box(self, ctx):
        # a wobbly hand-drawn rectangle (two overlapping strokes, marker-like)
        a = ctx["accent"]
        return (f'<svg class="deco boxd" viewBox="0 0 560 300" preserveAspectRatio="none">'
                f'<path d="M22,26 C180,14 400,20 540,24 C544,120 540,220 536,278 '
                f'C360,286 160,282 24,276 C18,180 20,90 22,26 Z" fill="none" '
                f'stroke="{a}" stroke-width="6" stroke-linecap="round"/></svg>')

    def scene(self, i, sc, ctx):
        t = sc.get("type", "point")
        if t in ("hook", "outro"):
            return self._headline(i, sc, ctx, outro=(t == "outro"))
        if t == "stat":
            return self._stat(i, sc, ctx)
        if t == "code":
            return self._code(i, sc, ctx)
        if t == "compare":
            return self._compare(i, sc, ctx)
        if t == "bullets":
            return self._bullets(i, sc, ctx)
        body = esc(sc.get("caption") or sc.get("say", ""))
        return f'<section class="scene nb" data-i="{i}"><div class="nb-note">{body}</div></section>'

    def _headline(self, i, sc, ctx, outro=False):
        lines = sc.get("lines", []) or [sc.get("say", "")]
        # 140 base (was 110): headlines must OWN the page, not float in it
        fs = big_fs(lines, base=140)
        if outro and ctx.get("outro") == "tape":
            # 合上笔记本式: big lines + a washi-tape seal slapped diagonally
            # across, like closing the notebook on the point
            body = "".join(f'<div class="nb-h" style="--d:{0.10*j:.2f}s;font-size:{fs}px">'
                           f'<span class="tx">{esc(ln)}</span></div>' for j, ln in enumerate(lines))
            return (f'<section class="scene nb hl otape" data-i="{i}">'
                    f'<div class="nb-stack">{body}</div>'
                    f'<div class="nb-seal"></div><div class="nb-seal s2"></div></section>')
        if outro:
            mode = "highlight" if ctx.get("outro") == "highlight" else "underline"
        else:
            mode = ctx["hook"]
        out = []
        for j, ln in enumerate(lines):
            last = (j == len(lines) - 1)
            deco = ""
            cls = "nb-h"
            if last:
                if mode == "highlight":
                    cls += " mk"
                elif mode == "circle":
                    deco = self._circle(ctx)
                    cls += " circled"
                elif mode == "underline":
                    deco = self._underline(ctx)
                    cls += " ul"
            out.append(f'<div class="{cls}" style="--d:{0.10*j:.2f}s;font-size:{fs}px">'
                       f'<span class="tx">{esc(ln)}</span>{deco}</div>')
        eb = f'<div class="nb-eyebrow">{esc(sc["eyebrow"])}</div>' if sc.get("eyebrow") else ""
        return f'<section class="scene nb hl" data-i="{i}">{eb}<div class="nb-stack">{"".join(out)}</div></section>'

    def _stat(self, i, sc, ctx):
        raw_val = str(sc.get("value", ""))
        val, unit = esc(raw_val), esc(sc.get("unit", ""))
        label = esc(sc.get("label", ""))
        # size follows the value's length — a fixed 300px wide "9 vs 5" used to
        # overflow and collide with the label/arrow doodle. +15% pass 2026-07-19.
        n = len(raw_val)
        fs = 340 if n <= 3 else (248 if n <= 5 else (178 if n <= 8 else 132))
        num_style = f'style="font-size:{fs}px"'
        # ghost numeral: the same value, huge and outline-only, pencilled into
        # the empty top of the page (kills the blank-card look)
        gfs = 620 if n <= 3 else (430 if n <= 5 else 300)
        ghost = f'<div class="nb-ghostnum" style="font-size:{gfs}px">{val}</div>'
        if ctx["stat"] == "boxed":
            # number pencilled inside a wobbly hand-drawn box, label beneath as
            # a margin annotation
            deco = self._box(ctx)
            return (f'<section class="scene nb stat" data-i="{i}">{ghost}<div class="nb-statwrap">'
                    f'<div class="nb-statnum boxed" {num_style}><span class="tx">{val}</span><span class="su">{unit}</span>{deco}</div>'
                    f'<div class="nb-statlabel anno">{label}</div></div></section>')
        if ctx["stat"] == "ring":
            deco = self._circle(ctx)
            return (f'<section class="scene nb stat" data-i="{i}">{ghost}<div class="nb-statwrap">'
                    f'<div class="nb-statnum" {num_style}><span class="tx">{val}</span><span class="su">{unit}</span>{deco}</div>'
                    f'<div class="nb-statlabel">{label}</div></div></section>')
        # the swoosh arrow only decorates SHORT values — on wide ones it used to
        # land across the digits and the label
        arrow = self._arrow(ctx) if n <= 3 else ""
        return (f'<section class="scene nb stat" data-i="{i}">{ghost}<div class="nb-statwrap">'
                f'<div class="nb-statnum" {num_style}><span class="tx">{val}</span><span class="su">{unit}</span></div>'
                f'{arrow}<div class="nb-statlabel">{label}</div></div></section>')

    def _code(self, i, sc, ctx):
        lines = highlight(sc.get("code", ""), sc.get("lang", "python"))
        body = "".join(f'<div class="cl" style="--d:{0.08*j:.2f}s">{ln}</div>' for j, ln in enumerate(lines))
        cap = f'<div class="nb-anno">{self._arrow(ctx,"aarrow")}<span>{esc(sc["caption"])}</span></div>' if sc.get("caption") else ""
        return (f'<section class="scene nb code" data-i="{i}"><div class="nb-tape"></div>'
                f'<div class="nb-paper"><div class="nb-code">{body}</div></div>{cap}</section>')

    def _compare(self, i, sc, ctx):
        before, after = esc(sc.get("before", "")), esc(sc.get("after", ""))
        mode = ctx.get("compare", "framed")
        if mode == "pages":
            # 左右分页: two half-pages with a spiral-binding seam down the middle
            binding = "".join(f'<span class="nb-ring"></span>' for _ in range(7))
            return (f'<section class="scene nb cmp pages" data-i="{i}">'
                    f'<div class="nb-page left"><div class="nb-ptag bad">之前</div>'
                    f'<div class="nb-ptxt">{before}</div></div>'
                    f'<div class="nb-binding">{binding}</div>'
                    f'<div class="nb-page right"><div class="nb-ptag good">之后</div>'
                    f'<div class="nb-ptxt">{after}</div></div></section>')
        if mode == "correction":
            # 订正式: the old value struck out, the new one written above in accent
            return (f'<section class="scene nb cmp corr" data-i="{i}"><div class="nb-corrwrap">'
                    f'<div class="nb-corr-new">{self._check(ctx)}<span>{after}</span></div>'
                    f'<div class="nb-corr-old"><span>{before}</span>'
                    f'<svg class="nb-strike" viewBox="0 0 700 30" preserveAspectRatio="none">'
                    f'<path d="M6,18 C200,10 480,24 694,12" fill="none" stroke="#c2553f" '
                    f'stroke-width="7" stroke-linecap="round"/></svg></div></div></section>')
        # framed (default): rows inside a hand-drawn dashed frame — a taped-in注记框
        return (f'<section class="scene nb cmp" data-i="{i}"><div class="nb-cmpbox">'
                f'<div class="nb-row bad"><span class="x">✕</span><span>{before}</span></div>'
                f'<svg class="nb-div" viewBox="0 0 700 30" preserveAspectRatio="none"><path d="M8,16 C200,6 480,24 692,12" '
                f'fill="none" stroke="{ctx["ink"]}" stroke-width="3" stroke-dasharray="2 12" stroke-linecap="round"/></svg>'
                f'<div class="nb-row good">{self._check(ctx)}<span>{after}</span></div></div></section>')

    def _bullets(self, i, sc, ctx):
        head = (f'<div class="nb-bhead"><span class="tx">{esc(sc["head"])}</span>{self._underline(ctx)}</div>'
                if sc.get("head") else "")
        if ctx["bullets"] == "numbered":
            # 编号清单: hand-circled numerals instead of checkmarks
            items = "".join(
                f'<div class="nb-li num" style="--d:{0.12*j:.2f}s">'
                f'<span class="nb-num">{j+1}</span><span>{esc(x)}</span></div>'
                for j, x in enumerate(sc.get("lines", [])))
            return f'<section class="scene nb bul" data-i="{i}">{head}<div class="nb-list numbered">{items}</div></section>'
        items = "".join(
            f'<div class="nb-li" style="--d:{0.12*j:.2f}s">{self._check(ctx)}<span>{esc(x)}</span></div>'
            for j, x in enumerate(sc.get("lines", [])))
        wrap = "nb-sticky" if ctx["bullets"] == "sticky" else "nb-list"
        return f'<section class="scene nb bul" data-i="{i}">{head}<div class="{wrap}">{items}</div></section>'


_CSS = r"""
html,body{__PAPER__;font-family:"LXGW WenKai","LXGW WenKai GB","KaiTi","Kaiti SC",serif;color:__INK__}
.bar{background:__ACCENT__;height:10px;opacity:.85}
.scene.nb{padding:0 70px}
/* ── page furniture (background layer, behind every scene) ── */
.nb-bg{position:absolute;inset:0;z-index:0;pointer-events:none}
.nb-mline{position:absolute;top:0;bottom:0;left:104px;width:3px;background:#f3b0a6;opacity:.55}
.nb-topline{position:absolute;left:0;right:0;top:150px;height:2px;background:#f3b0a6;opacity:.35}
.nb-tapecorner{position:absolute;width:280px;height:60px;background:__TAPE__;
  box-shadow:0 3px 10px rgba(0,0,0,.08)}
.nb-tapecorner.ta{top:64px;left:-70px;transform:rotate(__TAPE_TILT__deg)}
.nb-tapecorner.tb{bottom:210px;right:-76px;transform:rotate(calc(__TAPE_TILT__deg * -1))}
.nb-doodle{position:absolute;font-weight:700;line-height:1;color:rgba(0,0,0,.045)}
.nb-doodle.d0{top:96px;right:-40px;font-size:560px;transform:rotate(12deg)}
.nb-doodle.d1{top:44%;left:-90px;font-size:420px;transform:rotate(-14deg)}
.nb-doodle.d2{bottom:120px;right:60px;font-size:340px;transform:rotate(8deg)}
/* ── base-layer skins ── */
/* subtitles: deep-ink plate + washi-tape accent base (keeps base white fill +
   dark text-stroke for readability; kills the disconnected grey pill) */
.sub{background:rgba(24,26,33,.92);border-radius:14px;
  border-bottom:8px solid __TAPE__}
/* media fit canvas: the notebook paper shows through with a soft accent wash —
   no more blurred-black fill */
.media-canvas{background:linear-gradient(180deg,__WASH__,transparent 26%,
  transparent 66%,__WASH2__)}
.media-fit,.media-fitpos{border-radius:10px}
.deco{position:absolute;overflow:visible;pointer-events:none}
.nb-stack{position:relative}
.nb-eyebrow{font-size:48px;color:__ACCENT__;font-weight:700;margin-bottom:26px;transform:rotate(-1deg);opacity:0}
.scene.active .nb-eyebrow{animation:nbf .5s ease forwards}
.nb-h{position:relative;font-weight:700;line-height:1.2;letter-spacing:1px;opacity:0;transform:translateY(16px);display:block;width:max-content;max-width:940px}
.nb-h .tx{position:relative;z-index:2}
.scene.active .nb-h{animation:nbf .55s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.nb-h.mk .tx{box-decoration-break:clone}
.nb-h.mk::before{content:"";position:absolute;left:-10px;right:-12px;bottom:6px;height:42%;background:__HILITE__;z-index:1;transform:rotate(-1deg);width:0}
.scene.active .nb-h.mk::before{animation:mkgrow .55s ease forwards .25s}
.nb-h.circled .ring{left:-44px;top:-26px;width:calc(100% + 96px);height:calc(100% + 60px)}
.nb-h.circled .ring path{stroke-dasharray:1500;stroke-dashoffset:1500}
.scene.active .nb-h.circled .ring path{animation:draw .8s ease forwards .25s}
.nb-h.ul .uline{left:-6px;bottom:-30px;width:108%;height:36px}
.nb-h.ul .uline path{stroke-dasharray:1300;stroke-dashoffset:1300}
.scene.active .nb-h.ul .uline path{animation:draw .7s ease forwards .25s}
/* stat */
.nb-ghostnum{position:absolute;top:110px;right:26px;font-weight:700;line-height:1;
  color:transparent;-webkit-text-stroke:3px __INK_GHOST__;letter-spacing:-6px;
  pointer-events:none;z-index:0}
.nb-statwrap{position:relative;z-index:2}
.nb-statnum{position:relative;font-weight:700;font-size:340px;line-height:.95;color:__ACCENT__;width:max-content;max-width:940px}
.nb-statnum .su{font-size:.44em}
.nb-statnum .tx{position:relative;z-index:2}
.nb-statnum .ring{left:-50px;top:-30px;width:calc(100% + 110px);height:calc(100% + 70px)}
.nb-statnum .ring path{stroke-dasharray:1600;stroke-dashoffset:1600}
.scene.active .nb-statnum .ring path{animation:draw .9s ease forwards .3s}
.nb-statlabel{font-size:70px;margin-top:38px;color:__INK__;position:relative;z-index:3;max-width:940px;line-height:1.35}
.harrow{left:calc(100% - 320px);top:-40px}
/* code: a printout taped into the notebook */
.nb-tape{position:absolute;top:96px;left:50%;width:200px;height:50px;margin-left:-100px;background:rgba(243,214,99,.6);transform:rotate(-3deg);z-index:5}
.nb-paper{background:#fffdf7;border:1px solid #e7e0cf;box-shadow:4px 8px 20px rgba(0,0,0,.12);padding:46px 44px;border-radius:6px;transform:rotate(__TILT__deg);max-width:880px}
.nb-code{font-family:"Noto Sans Mono CJK SC","DejaVu Sans Mono",monospace;font-size:42px;line-height:1.55;color:#2b2f3a}
.cl{white-space:pre;opacity:0;transform:translateX(-8px)}.scene.active .cl{animation:nbf .4s ease forwards;animation-delay:var(--d)}
.t-kw{color:#b5256b;font-weight:700}.t-str{color:#2f8f5b}.t-cmt{color:#9a948a;font-style:italic}.t-num{color:#c0398f}.t-fn{color:#1f6feb}.t-dec{color:#d98a00}
.nb-anno{display:flex;align-items:center;gap:14px;margin-top:30px;color:__ACCENT__;font-size:46px;transform:rotate(-1.5deg)}
.aarrow{width:120px;height:90px}
/* compare: rows inside a hand-drawn dashed frame */
.nb-cmpbox{display:flex;flex-direction:column;gap:44px;border:3px dashed __INK_SOFT__;
  border-radius:22px;padding:66px 58px;margin:0 4px;transform:rotate(-.6deg);
  background:rgba(255,255,255,.45)}
.nb-row{display:flex;align-items:center;gap:28px;font-size:88px;opacity:0;transform:translateX(-30px)}
.scene.active .nb-row{animation:nbslide .55s cubic-bezier(.2,.7,.2,1) forwards}
.scene.active .nb-row.good{animation-delay:.22s}
.nb-row.bad{color:#9a948a}.nb-row .x{color:#c2553f;font-size:62px}
.nb-row .ck{width:66px;height:66px}
.nb-div{width:100%;height:30px;opacity:0}.scene.active .nb-div{animation:nbf .4s ease forwards .15s}
/* bullets */
.nb-bhead{position:relative;font-size:88px;color:__ACCENT__;font-weight:700;margin-bottom:52px;transform:rotate(-1deg);opacity:0;width:max-content;max-width:940px}
.nb-bhead .tx{position:relative;z-index:2}
.nb-bhead .uline{left:-4px;bottom:-20px;width:104%;height:30px}
.nb-bhead .uline path{stroke-dasharray:1300;stroke-dashoffset:1300}
.scene.active .nb-bhead .uline path{animation:draw .7s ease forwards .3s}
.scene.active .nb-bhead{animation:nbf .5s ease forwards}
.nb-sticky{background:#fff7d2;padding:56px 58px;box-shadow:4px 8px 18px rgba(0,0,0,.14);transform:rotate(-1.5deg);align-self:flex-start;max-width:900px;
  display:flex;flex-direction:column;gap:40px}
.nb-list{display:flex;flex-direction:column;gap:40px;border:3px dashed __INK_SOFT__;
  border-radius:18px;padding:52px 48px;transform:rotate(-.4deg)}
.nb-li{display:flex;align-items:center;gap:26px;font-size:72px;line-height:1.35;opacity:0;transform:translateY(20px)}
.scene.active .nb-li{animation:nbf .5s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.nb-li .ck{width:64px;height:64px;min-width:64px}
.ck path{stroke-dasharray:80;stroke-dashoffset:80}.scene.active .ck path{animation:draw .45s ease forwards;animation-delay:calc(var(--d) + .15s)}
.nb-note{font-size:66px;line-height:1.65;max-width:900px}
/* stat · boxed: number inside a wobbly hand-drawn rectangle */
.nb-statnum.boxed{padding:44px 66px}
.nb-statnum .boxd{left:-10px;top:-8px;width:calc(100% + 20px);height:calc(100% + 16px)}
.nb-statnum .boxd path{stroke-dasharray:1900;stroke-dashoffset:1900}
.scene.active .nb-statnum.boxed .boxd path{animation:draw 1s ease forwards .3s}
.nb-statlabel.anno{transform:rotate(-1.2deg)}
/* bullets · numbered: hand-circled numerals */
.nb-list.numbered{gap:44px}
.nb-li.num{align-items:center}
.nb-num{display:inline-flex;align-items:center;justify-content:center;min-width:74px;height:74px;
  border:4px solid __ACCENT__;border-radius:50% 48% 52% 47%;color:__ACCENT__;font-weight:700;
  font-size:48px;transform:rotate(-3deg)}
/* compare · pages: two half-pages + spiral binding */
.scene.nb.cmp.pages{flex-direction:row;align-items:stretch;gap:0;padding:0 60px}
.nb-page{flex:1;display:flex;flex-direction:column;justify-content:center;padding:60px 44px;opacity:0}
.nb-page.left{transform:translateX(-24px)}.nb-page.right{transform:translateX(24px)}
.scene.active .nb-page.left{animation:nbslide .55s cubic-bezier(.2,.7,.2,1) forwards}
.scene.active .nb-page.right{animation:nbslideR .55s cubic-bezier(.2,.7,.2,1) forwards .18s}
.nb-ptag{font-size:44px;font-weight:700;margin-bottom:26px;transform:rotate(-1.5deg)}
.nb-ptag.bad{color:#9a948a}.nb-ptag.good{color:__ACCENT__}
.nb-ptxt{font-size:78px;line-height:1.3}.nb-page.left .nb-ptxt{color:#9a948a}
.nb-binding{display:flex;flex-direction:column;justify-content:center;gap:38px;padding:0 10px}
.nb-ring{width:34px;height:14px;border:3px solid __INK_SOFT__;border-radius:50%;transform:rotate(-8deg)}
/* compare · correction: struck-out old + accent new above */
.nb-corrwrap{display:flex;flex-direction:column;gap:52px;padding:40px 54px}
.nb-corr-new{display:flex;align-items:center;gap:24px;font-size:92px;font-weight:700;color:__ACCENT__;
  opacity:0;transform:translateY(-16px)}
.scene.active .nb-corr-new{animation:nbf .5s ease forwards .25s}
.nb-corr-new .ck{width:70px;height:70px}
.nb-corr-old{position:relative;font-size:80px;color:#9a948a;width:max-content;max-width:900px;opacity:0}
.scene.active .nb-corr-old{animation:nbf .5s ease forwards}
.nb-strike{position:absolute;left:-8px;top:44%;width:104%;height:30px}
.nb-strike path{stroke-dasharray:1400;stroke-dashoffset:1400}
.scene.active .nb-corr-old .nb-strike path{animation:draw .55s ease forwards .5s}
/* outro · tape: washi-tape seal slapped across the closing lines */
.nb-seal{position:absolute;left:-40px;top:46%;width:640px;height:96px;background:__TAPE__;
  transform:rotate(-8deg);box-shadow:0 4px 14px rgba(0,0,0,.1);opacity:0}
.nb-seal.s2{left:auto;right:-60px;top:60%;width:420px;height:76px;transform:rotate(6deg)}
.scene.active .nb-seal{animation:nbf .5s ease forwards .35s}
.scene.active .nb-seal.s2{animation:nbf .5s ease forwards .5s}
@keyframes nbslideR{to{opacity:1;transform:none}}
@keyframes nbf{to{opacity:1;transform:none}}
@keyframes nbslide{to{opacity:1;transform:none}}
@keyframes mkgrow{to{width:calc(100% + 22px)}}
@keyframes draw{to{stroke-dashoffset:0}}
/* cover = first scene: fully drawn, no entrance */
.scene.nb:first-of-type .nb-h,.scene.nb:first-of-type .nb-eyebrow,
.scene.nb:first-of-type .nb-bhead,.scene.nb:first-of-type .nb-li,
.scene.nb:first-of-type .nb-row,.scene.nb:first-of-type .nb-div,
.scene.nb:first-of-type .nb-page,.scene.nb:first-of-type .nb-corr-new,
.scene.nb:first-of-type .nb-corr-old,.scene.nb:first-of-type .nb-seal{opacity:1;transform:none;animation:none}
.scene.nb:first-of-type .nb-h.mk::before{width:calc(100% + 22px);animation:none}
.scene.nb:first-of-type .deco path,.scene.nb:first-of-type .ck path,
.scene.nb:first-of-type .nb-strike path{stroke-dashoffset:0;animation:none}
"""
