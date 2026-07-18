#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_keynote — the ORIGINAL look, ported into the Style contract.

Kept as a rare rotation option (low weight) so nothing that worked is lost, and
as the reference implementation of the contract for the other style modules.
Dark/light + accent + drifting glows + dot grid; one layout per scene type.
"""
from . import base
from .base import Style, esc, rgba, highlight

_ACCENTS = ["#FF2E4D", "#2E7BFF", "#16C784", "#7C5CFF", "#FF7A00", "#FF2E88"]
_COOLS = {"#FF2E4D": "#2E7BFF", "#2E7BFF": "#16C784", "#16C784": "#2E7BFF",
          "#7C5CFF": "#2EE6FF", "#FF7A00": "#2E7BFF", "#FF2E88": "#7C5CFF"}


def _big_lines(lines, base_fs=128):
    fs = base.big_fs(lines, base=base_fs)
    return "".join(
        f'<div class="big" style="--d:{0.10*j:.2f}s;font-size:{fs}px">{esc(x)}</div>'
        for j, x in enumerate(lines)
    )


class KeynoteStyle(Style):
    id = "keynote"
    weight = 0.35          # rare: the look the user got tired of
    label = "聚光"

    def affinity(self, spec):
        return 1.0

    def variant(self, rng):
        accent = rng.choice(_ACCENTS)
        return {
            "accent": accent,
            "cool": _COOLS.get(accent, "#2E7BFF"),
            "theme": "dark" if rng.random() < 0.72 else "light",
            "glow": rng.random() < 0.85,
        }

    def css(self, ctx):
        dark = ctx.get("theme", "dark") != "light"
        accent, cool = ctx["accent"], ctx.get("cool", "#2E7BFF")
        p = {
            "ACCENT": accent, "COOL": cool,
            "BG": "#0B0E14" if dark else "#F5F4F0",
            "FG": "#FFFFFF" if dark else "#14161C",
            "SUB": "#9AA3B2" if dark else "#5B616E",
            "DOT": "rgba(255,255,255,.07)" if dark else "rgba(0,0,0,.06)",
            "CARD": "#11151F" if dark else "#FFFFFF",
            "CARDBAR": "#161B27" if dark else "#ECEAE4",
            "CARDBD": "rgba(255,255,255,.09)" if dark else "rgba(0,0,0,.10)",
            "CODEFG": "#C8D3F5" if dark else "#2A2E3A",
            "DIMCARD": "rgba(255,255,255,.05)" if dark else "rgba(0,0,0,.05)",
            "ADIM": rgba(accent, .14), "ASH": rgba(accent, .45),
        }
        return _CSS % p

    def background(self, ctx):
        if not ctx.get("glow", True):
            return '<div class="grid"></div>'
        return '<div class="glow a"></div><div class="glow b"></div><div class="grid"></div>'

    def chrome(self, spec, ctx):
        return ""   # no corner branding (user decision 2026-07-18)

    def scene(self, i, sc, ctx):
        t = sc.get("type", "point")
        if t == "hook":
            eb = f'<div class="eyebrow">{esc(sc["eyebrow"])}</div>' if sc.get("eyebrow") else ""
            return (f'<section class="scene hook" data-i="{i}">{eb}'
                    f'<div class="biglines">{_big_lines(sc.get("lines", []))}'
                    f'<div class="accentbar"></div></div></section>')
        if t == "stat":
            unit = esc(sc.get("unit", ""))
            return (f'<section class="scene stat" data-i="{i}">'
                    f'<div class="statwrap"><div class="statnum">{esc(sc.get("value",""))}'
                    f'<span class="statunit">{unit}</span></div>'
                    f'<div class="statlabel">{esc(sc.get("label",""))}</div></div></section>')
        if t == "code":
            lines = highlight(sc.get("code", ""), sc.get("lang", "python"))
            body = "".join(
                f'<div class="codeline" style="--d:{0.09*j:.2f}s">{ln}</div>'
                for j, ln in enumerate(lines))
            cap = f'<div class="codecap">{esc(sc["caption"])}</div>' if sc.get("caption") else ""
            lang = esc(sc.get("lang", "python"))
            return (f'<section class="scene code" data-i="{i}"><div class="win">'
                    f'<div class="winbar"><span class="dot d1"></span><span class="dot d2"></span>'
                    f'<span class="dot d3"></span><span class="winlang">{lang}</span></div>'
                    f'<div class="wincode">{body}</div></div>{cap}</section>')
        if t == "compare":
            return (f'<section class="scene compare" data-i="{i}">'
                    f'<div class="cmp before"><span class="cmpicon">✕</span>'
                    f'<span class="cmptext">{esc(sc.get("before",""))}</span></div>'
                    f'<div class="cmp after"><span class="cmpicon">✓</span>'
                    f'<span class="cmptext">{esc(sc.get("after",""))}</span></div></section>')
        if t == "bullets":
            items = "".join(
                f'<div class="bitem" style="--d:{0.14*j:.2f}s"><span class="bdash"></span>'
                f'<span class="btext">{esc(x)}</span></div>'
                for j, x in enumerate(sc.get("lines", [])))
            head = f'<div class="bhead">{esc(sc["head"])}</div>' if sc.get("head") else ""
            return f'<section class="scene bullets" data-i="{i}">{head}<div class="blist">{items}</div></section>'
        if t == "outro":
            return (f'<section class="scene outro" data-i="{i}">'
                    f'<div class="biglines">{_big_lines(sc.get("lines", []))}</div></section>')
        return (f'<section class="scene hook" data-i="{i}">'
                f'<div class="biglines">{_big_lines(sc.get("lines", [sc.get("say","")]))}</div></section>')


_CSS = r"""
html,body{background:%(BG)s;font-family:"Noto Sans CJK SC","Source Han Sans SC",sans-serif}
.bar{background:%(ACCENT)s;box-shadow:0 0 18px %(ACCENT)s}
.glow{position:absolute;border-radius:50%%;filter:blur(120px);opacity:.22;z-index:0}
.glow.a{width:760px;height:760px;background:%(ACCENT)s;top:-160px;right:-180px;animation:floatA 14s ease-in-out infinite alternate}
.glow.b{width:680px;height:680px;background:%(COOL)s;bottom:-200px;left:-160px;animation:floatB 16s ease-in-out infinite alternate}
@keyframes floatA{from{transform:translate(0,0)}to{transform:translate(-60px,80px)}}
@keyframes floatB{from{transform:translate(0,0)}to{transform:translate(70px,-60px)}}
.grid{position:absolute;inset:0;z-index:0;opacity:.5;background-image:radial-gradient(%(DOT)s 1.5px,transparent 1.6px);
  background-size:46px 46px;mask-image:linear-gradient(180deg,transparent,#000 30%%,#000 70%%,transparent)}
.tag{position:absolute;top:150px;left:96px;z-index:6;color:#fff;background:%(ACCENT)s;font-weight:800;font-size:40px;
  padding:13px 30px;border-radius:40px;letter-spacing:1px;box-shadow:0 10px 30px %(ASH)s;opacity:0;animation:pop .6s ease forwards .15s}
.handle{position:absolute;bottom:104px;left:96px;z-index:6;color:%(SUB)s;font-weight:700;font-size:34px;opacity:.85}
.scene{padding:0 96px;transform:translateY(18px) scale(.992);transition:opacity .45s ease,transform .45s ease}
.scene.active{transform:none}
.biglines{position:relative}
.eyebrow{color:%(ACCENT)s;font-weight:800;font-size:46px;letter-spacing:3px;margin-bottom:26px;opacity:0}
.scene.active .eyebrow{animation:rise .6s ease forwards}
.big{color:%(FG)s;font-weight:900;font-size:128px;line-height:1.16;letter-spacing:1px;opacity:0;transform:translateY(42px)}
.scene.active .big{animation:rise .72s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.accentbar{height:14px;width:0;background:%(ACCENT)s;border-radius:8px;margin-top:42px}
.scene.active .accentbar{animation:grow .8s cubic-bezier(.2,.7,.2,1) forwards .35s}
.statwrap{text-align:left}
.statnum{color:%(ACCENT)s;font-weight:900;font-size:300px;line-height:.96;letter-spacing:-4px;opacity:0;transform:translateY(30px) scale(.9)}
.scene.active .statnum{animation:popbig .75s cubic-bezier(.2,.8,.2,1) forwards}
.statunit{font-size:120px}
.statlabel{color:%(FG)s;font-weight:800;font-size:74px;margin-top:24px;opacity:0}
.scene.active .statlabel{animation:rise .6s ease forwards .3s}
.win{background:%(CARD)s;border:1.5px solid %(CARDBD)s;border-radius:30px;overflow:hidden;box-shadow:0 40px 90px rgba(0,0,0,.45);opacity:0;transform:translateY(34px) scale(.96)}
.scene.active .win{animation:popbig .6s cubic-bezier(.2,.8,.2,1) forwards}
.winbar{display:flex;align-items:center;gap:14px;padding:24px 30px;background:%(CARDBAR)s;border-bottom:1.5px solid %(CARDBD)s}
.dot{width:22px;height:22px;border-radius:50%%}.dot.d1{background:#FF5F57}.dot.d2{background:#FEBC2E}.dot.d3{background:#28C840}
.winlang{margin-left:auto;color:%(SUB)s;font-weight:700;font-size:32px;letter-spacing:1px}
.wincode{padding:34px 38px;font-family:"Noto Sans Mono CJK SC","JetBrains Mono","DejaVu Sans Mono",monospace;font-size:46px;line-height:1.5}
.codeline{color:%(CODEFG)s;white-space:pre;opacity:0;transform:translateX(-14px);overflow:hidden;text-overflow:ellipsis}
.scene.active .codeline{animation:slidein .5s ease forwards;animation-delay:var(--d)}
.t-kw{color:#FF7AB6;font-weight:700}.t-str{color:#9ECE6A}.t-cmt{color:#6B7689;font-style:italic}
.t-num{color:#FF9E64}.t-fn{color:#7AA2F7}.t-dec{color:#E0AF68}
.codecap{color:%(FG)s;font-weight:800;font-size:60px;margin-top:46px;opacity:0}
.scene.active .codecap{animation:rise .6s ease forwards .5s}
.compare{gap:42px}
.cmp{display:flex;align-items:center;gap:30px;padding:46px 50px;border-radius:26px;font-weight:800;font-size:64px;opacity:0}
.cmp .cmpicon{width:74px;height:74px;min-width:74px;border-radius:50%%;display:flex;align-items:center;justify-content:center;font-size:46px;color:#fff}
.cmp.before{background:%(DIMCARD)s;color:%(SUB)s;transform:translateX(-60px)}
.cmp.before .cmpicon{background:#6B7280}.cmp.before .cmptext{text-decoration:line-through;text-decoration-color:%(SUB)s}
.cmp.after{background:%(ADIM)s;color:%(FG)s;transform:translateX(60px)}.cmp.after .cmpicon{background:%(ACCENT)s}
.scene.active .cmp.before{animation:slidex .6s cubic-bezier(.2,.7,.2,1) forwards .05s}
.scene.active .cmp.after{animation:slidex .6s cubic-bezier(.2,.7,.2,1) forwards .22s}
.bhead{color:%(ACCENT)s;font-weight:800;font-size:56px;margin-bottom:40px;opacity:0}
.scene.active .bhead{animation:rise .55s ease forwards}
.blist{display:flex;flex-direction:column;gap:42px}
.bitem{display:flex;align-items:center;gap:30px;opacity:0;transform:translateY(26px)}
.scene.active .bitem{animation:rise .6s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.bdash{width:54px;height:14px;min-width:54px;border-radius:8px;background:%(ACCENT)s}
.btext{color:%(FG)s;font-weight:800;font-size:76px;line-height:1.2}
@keyframes rise{from{opacity:0;transform:translateY(34px)}to{opacity:1;transform:none}}
@keyframes grow{to{width:240px}}
@keyframes pop{from{opacity:0;transform:translateY(-10px) scale(.96)}to{opacity:1;transform:none}}
@keyframes popbig{from{opacity:0;transform:translateY(30px) scale(.92)}to{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-14px)}to{opacity:1;transform:none}}
@keyframes slidex{to{opacity:1;transform:none}}
.scene.hook .eyebrow,.scene.hook .big{opacity:1;transform:none;animation:none}
.scene.hook .accentbar{width:240px;animation:none}
"""
