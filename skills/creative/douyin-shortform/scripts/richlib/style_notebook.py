#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_notebook — B · 手写笔记 (dot-grid/ruled paper, LXGW WenKai 楷体, marker/circle).

The most human, least-AI look: like a real person jotting notes for a friend.
variant() randomizes paper texture, palette, and a layout per scene type, so two
notebook videos never look the same. Needs LXGW WenKai (base.ensure_fonts ships it).
"""
from .base import Style, esc, big_fs, highlight

_INKS = ["#23262e", "#1d2733", "#2a2320"]
_ACCENTS = ["#e0533b", "#1f6feb", "#d98a00", "#2f8f5b", "#c0398f"]
_HILITES = ["#ffe14d", "#ffd23f", "#bdf0a6", "#a8e0ff", "#ffc6dd"]


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
            "hook": rng.choice(["highlight", "circle", "underline"]),
            "stat": rng.choice(["ring", "arrow"]),
            "bullets": rng.choice(["sticky", "margin"]),
            "tilt": rng.choice([-2, -1, 1, 2]),
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
        })

    def chrome(self, spec, ctx):
        # no corner branding text (user decision 2026-07-18); keep the ruled
        # margin line — it is page decor, not text
        return '<div class="nb-margin"></div>'

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
        fs = big_fs(lines, base=110)
        mode = "underline" if outro else ctx["hook"]
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
        # overflow and collide with the label/arrow doodle
        n = len(raw_val)
        fs = 300 if n <= 3 else (215 if n <= 5 else (155 if n <= 8 else 115))
        num_style = f'style="font-size:{fs}px"'
        if ctx["stat"] == "ring":
            deco = self._circle(ctx)
            return (f'<section class="scene nb stat" data-i="{i}"><div class="nb-statwrap">'
                    f'<div class="nb-statnum" {num_style}><span class="tx">{val}</span><span class="su">{unit}</span>{deco}</div>'
                    f'<div class="nb-statlabel">{label}</div></div></section>')
        # the swoosh arrow only decorates SHORT values — on wide ones it used to
        # land across the digits and the label
        arrow = self._arrow(ctx) if n <= 3 else ""
        return (f'<section class="scene nb stat" data-i="{i}"><div class="nb-statwrap">'
                f'<div class="nb-statnum" {num_style}><span class="tx">{val}</span><span class="su">{unit}</span></div>'
                f'{arrow}<div class="nb-statlabel">{label}</div></div></section>')

    def _code(self, i, sc, ctx):
        lines = highlight(sc.get("code", ""), sc.get("lang", "python"))
        body = "".join(f'<div class="cl" style="--d:{0.08*j:.2f}s">{ln}</div>' for j, ln in enumerate(lines))
        cap = f'<div class="nb-anno">{self._arrow(ctx,"aarrow")}<span>{esc(sc["caption"])}</span></div>' if sc.get("caption") else ""
        return (f'<section class="scene nb code" data-i="{i}"><div class="nb-tape"></div>'
                f'<div class="nb-paper"><div class="nb-code">{body}</div></div>{cap}</section>')

    def _compare(self, i, sc, ctx):
        return (f'<section class="scene nb cmp" data-i="{i}">'
                f'<div class="nb-row bad"><span class="x">✕</span><span>{esc(sc.get("before",""))}</span></div>'
                f'<svg class="nb-div" viewBox="0 0 700 30" preserveAspectRatio="none"><path d="M8,16 C200,6 480,24 692,12" '
                f'fill="none" stroke="{ctx["ink"]}" stroke-width="3" stroke-dasharray="2 12" stroke-linecap="round"/></svg>'
                f'<div class="nb-row good">{self._check(ctx)}<span>{esc(sc.get("after",""))}</span></div></section>')

    def _bullets(self, i, sc, ctx):
        head = f'<div class="nb-bhead">{esc(sc["head"])}</div>' if sc.get("head") else ""
        items = "".join(
            f'<div class="nb-li" style="--d:{0.12*j:.2f}s">{self._check(ctx)}<span>{esc(x)}</span></div>'
            for j, x in enumerate(sc.get("lines", [])))
        wrap = "nb-sticky" if ctx["bullets"] == "sticky" else "nb-list"
        return f'<section class="scene nb bul" data-i="{i}">{head}<div class="{wrap}">{items}</div></section>'


_CSS = r"""
html,body{__PAPER__;font-family:"LXGW WenKai","LXGW WenKai GB","KaiTi","Kaiti SC",serif;color:__INK__}
.bar{background:__ACCENT__;height:10px;opacity:.85}
.scene.nb{padding:0 70px}
.nb-margin{position:absolute;top:0;bottom:0;left:104px;width:3px;background:#f3b0a6;opacity:.5;z-index:1}
.nb-label{position:absolute;top:74px;left:70px;z-index:6;font-weight:700;font-size:38px;color:__ACCENT__;transform:rotate(-2deg)}
.nb-handle{position:absolute;bottom:74px;right:70px;z-index:6;font-weight:700;font-size:34px;color:__INK__;transform:rotate(-3deg)}
.deco{position:absolute;overflow:visible;pointer-events:none}
.nb-stack{position:relative}
.nb-eyebrow{font-size:40px;color:__ACCENT__;font-weight:700;margin-bottom:24px;transform:rotate(-1deg);opacity:0}
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
.nb-statwrap{position:relative}
.nb-statnum{position:relative;font-weight:700;font-size:300px;line-height:.95;color:__ACCENT__;width:max-content;max-width:940px}
.nb-statnum .su{font-size:.44em}
.nb-statnum .tx{position:relative;z-index:2}
.nb-statnum .ring{left:-50px;top:-30px;width:calc(100% + 110px);height:calc(100% + 70px)}
.nb-statnum .ring path{stroke-dasharray:1600;stroke-dashoffset:1600}
.scene.active .nb-statnum .ring path{animation:draw .9s ease forwards .3s}
.nb-statlabel{font-size:60px;margin-top:38px;color:__INK__;position:relative;z-index:3;max-width:940px;line-height:1.35}
.harrow{left:calc(100% - 320px);top:-40px}
/* code: a printout taped into the notebook */
.nb-tape{position:absolute;top:96px;left:50%;width:200px;height:50px;margin-left:-100px;background:rgba(243,214,99,.6);transform:rotate(-3deg);z-index:5}
.nb-paper{background:#fffdf7;border:1px solid #e7e0cf;box-shadow:4px 8px 20px rgba(0,0,0,.12);padding:46px 44px;border-radius:6px;transform:rotate(__TILT__deg);max-width:880px}
.nb-code{font-family:"Noto Sans Mono CJK SC","DejaVu Sans Mono",monospace;font-size:42px;line-height:1.55;color:#2b2f3a}
.cl{white-space:pre;opacity:0;transform:translateX(-8px)}.scene.active .cl{animation:nbf .4s ease forwards;animation-delay:var(--d)}
.t-kw{color:#b5256b;font-weight:700}.t-str{color:#2f8f5b}.t-cmt{color:#9a948a;font-style:italic}.t-num{color:#c0398f}.t-fn{color:#1f6feb}.t-dec{color:#d98a00}
.nb-anno{display:flex;align-items:center;gap:14px;margin-top:30px;color:__ACCENT__;font-size:46px;transform:rotate(-1.5deg)}
.aarrow{width:120px;height:90px}
/* compare */
.scene.nb.cmp{gap:44px}
.nb-row{display:flex;align-items:center;gap:28px;font-size:76px;opacity:0;transform:translateX(-30px)}
.scene.active .nb-row{animation:nbslide .55s cubic-bezier(.2,.7,.2,1) forwards}
.scene.active .nb-row.good{animation-delay:.22s}
.nb-row.bad{color:#9a948a}.nb-row .x{color:#c2553f;font-size:54px}
.nb-row .ck{width:58px;height:58px}
.nb-div{width:100%;height:30px;opacity:0}.scene.active .nb-div{animation:nbf .4s ease forwards .15s}
/* bullets */
.nb-bhead{font-size:54px;color:__ACCENT__;font-weight:700;margin-bottom:40px;transform:rotate(-1deg);opacity:0}
.scene.active .nb-bhead{animation:nbf .5s ease forwards}
.nb-sticky{background:#fff7d2;padding:46px 52px;box-shadow:4px 8px 18px rgba(0,0,0,.14);transform:rotate(-1.5deg);align-self:flex-start;max-width:840px}
.nb-list{display:flex;flex-direction:column;gap:36px}
.nb-li{display:flex;align-items:center;gap:24px;font-size:58px;line-height:1.4;opacity:0;transform:translateY(20px)}
.scene.active .nb-li{animation:nbf .5s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.nb-li .ck{width:56px;height:56px;min-width:56px}
.ck path{stroke-dasharray:80;stroke-dashoffset:80}.scene.active .ck path{animation:draw .45s ease forwards;animation-delay:calc(var(--d) + .15s)}
.nb-note{font-size:56px;line-height:1.7;max-width:880px}
@keyframes nbf{to{opacity:1;transform:none}}
@keyframes nbslide{to{opacity:1;transform:none}}
@keyframes mkgrow{to{width:calc(100% + 22px)}}
@keyframes draw{to{stroke-dashoffset:0}}
/* cover = first scene: fully drawn, no entrance */
.scene.nb:first-of-type .nb-h,.scene.nb:first-of-type .nb-eyebrow{opacity:1;transform:none;animation:none}
.scene.nb:first-of-type .nb-h.mk::before{width:calc(100% + 22px);animation:none}
.scene.nb:first-of-type .deco path{stroke-dashoffset:0;animation:none}
"""
