#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_editorial — A · 杂志/编辑排版 (cream paper, serif, refined, asymmetric).

Reads like a premium tech-magazine spread: tracked kicker + rule, big serif
headlines, hairlines, a folio line, drop-caps and pull-quotes. Calm, credible —
the opposite of a content farm. variant() rotates palette + per-scene layout.
"""
import re
from .base import Style, esc, big_fs, highlight, blob, scene_types

_PALETTES = [  # (paper, ink, accent, sub)
    ("#f1ece1", "#1c1a17", "#a8341f", "#7a7163"),   # cream / ink-red
    ("#f3f0e8", "#161616", "#1f5fae", "#76798a"),   # cream / ink-blue
    ("#eee9df", "#1a1c18", "#2f6b4f", "#74786c"),   # cream / forest
    ("#f3efe6", "#181612", "#b06a12", "#857a66"),   # cream / ochre
    ("#efe9e6", "#1a1413", "#8a2f4f", "#867074"),   # blush / wine
]


def _fill(css, m):
    for k, v in m.items():
        css = css.replace(k, str(v))
    return css


def _latin_lead(s):
    """Return (lead_char, rest) if the line starts with a latin letter, else (None, s)."""
    s = str(s)
    if s and re.match(r"[A-Za-z]", s):
        return s[0], s[1:]
    return None, s


class EditorialStyle(Style):
    id = "editorial"
    weight = 1.0
    label = "杂志"

    def affinity(self, spec):
        b = blob(spec)
        score = 1.0
        if any(k in b for k in ("为什么", "趋势", "观点", "深度", "其实", "意味", "格局", "本质", "复盘", "分析", "信号", "时代")):
            score *= 1.8
        if "code" in scene_types(spec):
            score *= 0.5
        return score

    def variant(self, rng):
        paper, ink, accent, sub = rng.choice(_PALETTES)
        return {
            "accent": accent, "paper": paper, "ink": ink, "sub": sub,
            "hook": rng.choice(["dropcap", "kicker", "pull"]),
            "stat": rng.choice(["left", "center"]),
            "bullets": rng.choice(["numbered", "ruled"]),
            "issue": rng.choice(["第 014 期", "VOL.07", "No.21", "本期特写"]),
        }

    def css(self, ctx):
        return _fill(_CSS, {
            "__PAPER__": ctx["paper"], "__INK__": ctx["ink"],
            "__ACCENT__": ctx["accent"], "__SUB__": ctx["sub"],
        })

    def chrome(self, spec, ctx):
        return ""   # no corner branding (user decision 2026-07-18)

    def scene(self, i, sc, ctx):
        t = sc.get("type", "point")
        if t == "hook":
            return self._hook(i, sc, ctx)
        if t == "outro":
            return self._outro(i, sc, ctx)
        if t == "stat":
            return self._stat(i, sc, ctx)
        if t == "code":
            return self._code(i, sc, ctx)
        if t == "compare":
            return self._compare(i, sc, ctx)
        if t == "bullets":
            return self._bullets(i, sc, ctx)
        body = esc(sc.get("caption") or sc.get("say", ""))
        return f'<section class="scene ed" data-i="{i}"><p class="ed-body">{body}</p></section>'

    def _hook(self, i, sc, ctx):
        lines = sc.get("lines", []) or [sc.get("say", "")]
        fs = big_fs(lines, base=124)
        eb = esc(sc.get("eyebrow", "")) or "特写"
        mode = ctx["hook"]
        if mode == "pull":
            body = "".join(f'<div class="ed-pl" style="--d:{0.10*j:.2f}s;font-size:{int(fs*0.86)}px">{esc(x)}</div>' for j, x in enumerate(lines))
            return f'<section class="scene ed hook pull" data-i="{i}"><div class="ed-quote">“</div><div class="ed-pullwrap">{body}</div></section>'
        head = []
        for j, x in enumerate(lines):
            cls = "ed-h1"
            inner = esc(x)
            if mode == "dropcap" and j == 0:
                lead, rest = _latin_lead(x)
                if lead:
                    inner = f'<span class="ed-drop">{esc(lead)}</span>{esc(rest)}'
            head.append(f'<div class="{cls}" style="--d:{0.10*j:.2f}s;font-size:{fs}px">{inner}</div>')
        kicker = f'<div class="ed-eyebrow">{eb}</div>' if mode == "kicker" else ""
        return f'<section class="scene ed hook" data-i="{i}">{kicker}<div class="ed-hwrap">{"".join(head)}<div class="ed-rule"></div></div></section>'

    def _outro(self, i, sc, ctx):
        lines = sc.get("lines", []) or [sc.get("say", "")]
        fs = big_fs(lines, base=104)
        body = "".join(f'<div class="ed-h1" style="--d:{0.10*j:.2f}s;font-size:{fs}px">{esc(x)}</div>' for j, x in enumerate(lines))
        return f'<section class="scene ed outro" data-i="{i}"><div class="ed-endmark">—</div><div class="ed-hwrap">{body}</div></section>'

    def _stat(self, i, sc, ctx):
        val, unit, label = esc(sc.get("value", "")), esc(sc.get("unit", "")), esc(sc.get("label", ""))
        cls = "ed-stat " + ctx["stat"]
        return (f'<section class="scene {cls}" data-i="{i}"><div class="ed-statwrap">'
                f'<div class="ed-num">{val}<span class="ed-unit">{unit}</span></div>'
                f'<div class="ed-hair"></div><div class="ed-cap">{label}</div></div></section>')

    def _code(self, i, sc, ctx):
        lines = highlight(sc.get("code", ""), sc.get("lang", "python"))
        body = "".join(f'<div class="ed-cl" style="--d:{0.07*j:.2f}s">{ln}</div>' for j, ln in enumerate(lines))
        cap = f'<div class="ed-figcap">— {esc(sc["caption"])}</div>' if sc.get("caption") else ""
        lang = esc(sc.get("lang", "code"))
        return (f'<section class="scene ed code" data-i="{i}"><div class="ed-figtag">CODE · {lang}</div>'
                f'<div class="ed-codeframe"><div class="ed-code">{body}</div></div>{cap}</section>')

    def _compare(self, i, sc, ctx):
        return (f'<section class="scene ed cmp" data-i="{i}"><div class="ed-cmpwrap">'
                f'<div class="ed-cmprow before"><span class="ed-cmplab">之前</span><span class="ed-cmptxt">{esc(sc.get("before",""))}</span></div>'
                f'<div class="ed-hair"></div>'
                f'<div class="ed-cmprow after"><span class="ed-cmplab">之后</span><span class="ed-cmptxt">{esc(sc.get("after",""))}</span></div>'
                f'</div></section>')

    def _bullets(self, i, sc, ctx):
        head = f'<div class="ed-bhead">{esc(sc["head"])}</div>' if sc.get("head") else ""
        rows = sc.get("lines", [])
        if ctx["bullets"] == "numbered":
            items = "".join(
                f'<div class="ed-li num" style="--d:{0.12*j:.2f}s"><span class="ed-n">{j+1:02d}</span>'
                f'<span class="ed-lt">{esc(x)}</span></div>' for j, x in enumerate(rows))
        else:
            items = "".join(
                f'<div class="ed-li ruled" style="--d:{0.12*j:.2f}s"><span class="ed-lt">{esc(x)}</span></div>'
                for j, x in enumerate(rows))
        return f'<section class="scene ed bul" data-i="{i}">{head}<div class="ed-list">{items}</div></section>'


_CSS = r"""
html,body{background:__PAPER__;font-family:"Noto Serif CJK SC","Source Han Serif SC",serif;color:__INK__}
.bar{background:__ACCENT__;height:6px}
.scene.ed{padding:0 84px}
.ed-top{position:absolute;top:84px;left:84px;right:84px;z-index:6;display:flex;justify-content:space-between;align-items:baseline;
  font-family:"Noto Sans CJK SC",sans-serif;border-bottom:2px solid __INK__;padding-bottom:18px}
.ed-k{font-weight:800;font-size:30px;letter-spacing:7px;color:__ACCENT__}
.ed-issue{font-size:24px;letter-spacing:3px;color:__SUB__}
.ed-folio{position:absolute;bottom:80px;left:84px;right:84px;z-index:6;display:flex;justify-content:space-between;
  font-family:"Noto Sans CJK SC",sans-serif;font-size:24px;color:__SUB__;border-top:1px solid __SUB__;padding-top:16px}
.ed-folio .ed-h{color:__INK__;font-weight:700}
/* headline */
.ed-hwrap{position:relative}
.ed-eyebrow{font-family:"Noto Sans CJK SC",sans-serif;font-weight:800;font-size:34px;letter-spacing:6px;color:__ACCENT__;
  text-transform:uppercase;margin-bottom:30px;opacity:0}
.scene.active .ed-eyebrow{animation:edf .6s ease forwards}
.ed-h1{font-weight:700;line-height:1.1;letter-spacing:1px;opacity:0;transform:translateY(22px)}
.scene.active .ed-h1{animation:edrise .75s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.ed-h1:last-of-type{color:__ACCENT__}
.ed-drop{font-size:1.5em;line-height:.8;float:left;margin:0 .06em -.06em 0;color:__ACCENT__}
.ed-rule{height:3px;width:0;background:__INK__;margin-top:40px}
.scene.active .ed-rule{animation:edgrow .8s cubic-bezier(.2,.7,.2,1) forwards .35s}
.ed-quote{font-size:240px;line-height:.6;color:__ACCENT__;height:120px;opacity:0}
.scene.active .ed-quote{animation:edf .5s ease forwards}
.ed-pl{font-style:italic;font-weight:600;line-height:1.32;opacity:0;transform:translateY(18px)}
.scene.active .ed-pl{animation:edrise .7s ease forwards;animation-delay:var(--d)}
/* outro */
.ed-endmark{font-size:80px;color:__ACCENT__;margin-bottom:20px;opacity:0}.scene.active .ed-endmark{animation:edf .6s ease forwards}
/* stat */
.ed-statwrap{max-width:880px}
.ed-stat.center .ed-statwrap{text-align:center;margin:0 auto}
.ed-num{font-weight:700;font-size:330px;line-height:.92;color:__ACCENT__;letter-spacing:-4px;opacity:0;transform:translateY(24px)}
.scene.active .ed-num{animation:edrise .8s cubic-bezier(.2,.8,.2,1) forwards}
.ed-unit{font-size:140px}
.ed-hair{height:2px;background:__SUB__;margin:30px 0;opacity:0}.scene.active .ed-hair{animation:edf .6s ease forwards .3s}
.ed-stat.center .ed-hair{width:240px;margin:30px auto}
.ed-cap{font-size:56px;color:__INK__;opacity:0}.scene.active .ed-cap{animation:edrise .6s ease forwards .4s}
/* code */
.ed-figtag{font-family:"Noto Sans CJK SC",sans-serif;font-weight:800;font-size:26px;letter-spacing:4px;color:__SUB__;margin-bottom:24px;opacity:0}
.scene.active .ed-figtag{animation:edf .5s ease forwards}
.ed-codeframe{border-top:2px solid __INK__;border-bottom:2px solid __INK__;padding:38px 6px;opacity:0;transform:translateY(20px)}
.scene.active .ed-codeframe{animation:edrise .6s ease forwards .1s}
.ed-code{font-family:"Noto Sans Mono CJK SC","DejaVu Sans Mono",monospace;font-size:44px;line-height:1.55;color:__INK__}
.ed-cl{white-space:pre;opacity:0}.scene.active .ed-cl{animation:edf .4s ease forwards;animation-delay:var(--d)}
.t-kw{color:__ACCENT__;font-weight:700}.t-str{color:#2f6b4f}.t-cmt{color:__SUB__;font-style:italic}.t-num{color:#8a2f4f}.t-fn{color:__INK__;font-weight:700}.t-dec{color:#b06a12}
.ed-figcap{font-style:italic;font-size:42px;color:__SUB__;margin-top:26px;opacity:0}.scene.active .ed-figcap{animation:edf .5s ease forwards .4s}
/* compare */
.ed-cmpwrap{max-width:900px}
.ed-cmprow{display:flex;align-items:baseline;gap:28px;padding:14px 0;font-size:62px;opacity:0;transform:translateX(-24px)}
.scene.active .ed-cmprow{animation:edslide .6s cubic-bezier(.2,.7,.2,1) forwards}
.scene.active .ed-cmprow.after{animation-delay:.22s}
.ed-cmplab{font-family:"Noto Sans CJK SC",sans-serif;font-weight:800;font-size:30px;letter-spacing:4px;min-width:120px}
.ed-cmprow.before{color:__SUB__}.ed-cmprow.before .ed-cmptxt{text-decoration:line-through;text-decoration-thickness:2px}
.ed-cmprow.after .ed-cmplab{color:__ACCENT__}
/* bullets */
.ed-bhead{font-family:"Noto Serif CJK SC",serif;font-weight:700;font-size:64px;color:__INK__;margin-bottom:44px;opacity:0}
.scene.active .ed-bhead{animation:edrise .6s ease forwards}
.ed-list{display:flex;flex-direction:column}
.ed-li{display:flex;align-items:baseline;gap:30px;padding:26px 0;opacity:0;transform:translateY(18px)}
.scene.active .ed-li{animation:edrise .6s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.ed-li.ruled{border-bottom:1px solid __SUB__}
.ed-n{font-weight:700;font-size:54px;color:__ACCENT__;min-width:96px}
.ed-lt{font-size:62px;line-height:1.3}
.ed-body{font-size:58px;line-height:1.7;max-width:880px}
@keyframes edf{to{opacity:1;transform:none}}
@keyframes edrise{to{opacity:1;transform:none}}
@keyframes edslide{to{opacity:1;transform:none}}
@keyframes edgrow{to{width:260px}}
/* cover: first scene fully composed */
.scene.ed:first-of-type .ed-h1,.scene.ed:first-of-type .ed-eyebrow,.scene.ed:first-of-type .ed-pl,
.scene.ed:first-of-type .ed-quote{opacity:1;transform:none;animation:none}
.scene.ed:first-of-type .ed-rule{width:260px;animation:none}
"""
