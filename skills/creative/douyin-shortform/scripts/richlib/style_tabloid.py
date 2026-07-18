#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_tabloid — D · 大字快报 (black + acid, huge mixed type, tilt, sticker).

Maximum 抖音 stop-power, but art-directed — real hierarchy inside the chaos.
variant() rotates a 2-color scheme, skew, and a layout per scene type.
"""
from .base import Style, esc, big_fs, highlight, blob, scene_types

_SCHEMES = [  # (bg, accent, second)
    ("#111111", "#e6ff00", "#ff2e5b"),   # black / acid-green / hot-pink
    ("#0d1030", "#00e5ff", "#ff2e5b"),   # navy / cyan / pink
    ("#111111", "#ff2e5b", "#e6ff00"),   # black / pink / acid
    ("#161106", "#ff7a00", "#00e5ff"),   # near-black / orange / cyan
    ("#1a0a14", "#ff2e88", "#ffe14d"),   # plum / magenta / yellow
]


def _fill(css, m):
    for k, v in m.items():
        css = css.replace(k, str(v))
    return css


class TabloidStyle(Style):
    id = "tabloid"
    weight = 1.0
    label = "快报"

    def affinity(self, spec):
        b = blob(spec)
        score = 1.0
        if any(k in b for k in ("突发", "发布", "官宣", "重磅", "刚刚", "首发", "震惊", "爆", "炸", "上线", "曝光", "颠覆", "王炸")):
            score *= 1.9
        if "stat" in scene_types(spec):
            score *= 1.3
        return score

    def variant(self, rng):
        bg, accent, second = rng.choice(_SCHEMES)
        return {
            "accent": accent, "second": second, "bg": bg,
            "skew": rng.choice([-6, -4, 0, 4]),
            "hook": rng.choice(["skew", "box", "outline"]),
            "stat": rng.choice(["sticker", "split"]),
            "tilt": rng.choice([-3, 2, 3, 4]),
        }

    def css(self, ctx):
        return _fill(_CSS, {
            "__BG__": ctx["bg"], "__ACCENT__": ctx["accent"],
            "__SECOND__": ctx["second"], "__SKEW__": ctx["skew"], "__TILT__": ctx["tilt"],
        })

    def chrome(self, spec, ctx):
        return ""   # no corner branding (user decision 2026-07-18)

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
        return f'<section class="scene tb" data-i="{i}"><div class="tb-card">{body}</div></section>'

    def _headline(self, i, sc, ctx, outro=False):
        lines = sc.get("lines", []) or [sc.get("say", "")]
        big_i = len(lines) - 1 if len(lines) <= 2 else len(lines) // 2
        mode = "box" if outro else ctx["hook"]
        out = []
        for j, x in enumerate(lines):
            if j == big_i:
                fs = big_fs([x], base=168)
                cls = "tb-l2 " + mode
                out.append(f'<div class="{cls}" style="--d:{0.10*j:.2f}s;font-size:{fs}px"><span class="tb-tx">{esc(x)}</span></div>')
            else:
                fs = big_fs([x], base=82)
                out.append(f'<div class="tb-l1" style="--d:{0.10*j:.2f}s;font-size:{fs}px">{esc(x)}</div>')
        return f'<section class="scene tb hl" data-i="{i}">{"".join(out)}</section>'

    def _stat(self, i, sc, ctx):
        val, unit, label = esc(sc.get("value", "")), esc(sc.get("unit", "")), esc(sc.get("label", ""))
        if ctx["stat"] == "split":
            digits = "".join(f'<span class="tb-dg" style="--d:{0.07*k:.2f}s">{esc(c)}</span>' for k, c in enumerate(str(sc.get("value", ""))))
            return (f'<section class="scene tb stat" data-i="{i}"><div class="tb-split">{digits}<span class="tb-su">{unit}</span></div>'
                    f'<div class="tb-sticker">{label}</div></section>')
        return (f'<section class="scene tb stat" data-i="{i}"><div class="tb-mega">{val}<span class="tb-su">{unit}</span></div>'
                f'<div class="tb-sticker">{label}</div></section>')

    def _code(self, i, sc, ctx):
        lines = highlight(sc.get("code", ""), sc.get("lang", "python"))
        body = "".join(f'<div class="tb-cl" style="--d:{0.07*j:.2f}s">{ln}</div>' for j, ln in enumerate(lines))
        cap = f'<div class="tb-callout">▶ {esc(sc["caption"])}</div>' if sc.get("caption") else ""
        return (f'<section class="scene tb code" data-i="{i}"><div class="tb-shot"><div class="tb-shotbar">CODE</div>'
                f'<div class="tb-code">{body}</div></div>{cap}</section>')

    def _compare(self, i, sc, ctx):
        return (f'<section class="scene tb cmp" data-i="{i}">'
                f'<div class="tb-blk old"><span class="tb-tx">{esc(sc.get("before",""))}</span></div>'
                f'<div class="tb-vs">VS</div>'
                f'<div class="tb-blk new"><span class="tb-tx">{esc(sc.get("after",""))}</span></div></section>')

    def _bullets(self, i, sc, ctx):
        head = f'<div class="tb-bhead">{esc(sc["head"])}</div>' if sc.get("head") else ""
        chips = "".join(f'<div class="tb-chip c{j%3}" style="--d:{0.12*j:.2f}s">{esc(x)}</div>' for j, x in enumerate(sc.get("lines", [])))
        return f'<section class="scene tb bul" data-i="{i}">{head}<div class="tb-chips">{chips}</div></section>'


_CSS = r"""
html,body{background:__BG__;font-family:"Noto Sans CJK SC",sans-serif;font-weight:900;color:#fff}
.bar{background:__ACCENT__;height:10px}
.scene.tb{padding:0 56px}
.tb-top{position:absolute;top:0;left:0;right:0;z-index:6;background:__ACCENT__;color:#111;font-size:30px;font-weight:900;
  letter-spacing:4px;padding:18px 56px;display:flex;justify-content:space-between}
.tb-no{letter-spacing:2px}
.tb-handle{position:absolute;bottom:64px;right:56px;z-index:6;background:#fff;color:#111;font-size:30px;font-weight:900;
  padding:8px 22px;transform:rotate(-2deg)}
/* headline */
.tb-l1{font-size:82px;line-height:1.04;margin-bottom:18px;opacity:0;transform:translateY(22px)}
.scene.active .tb-l1{animation:tbrise .5s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:var(--d)}
.tb-l2{line-height:1.0;margin:6px 0 14px;opacity:0;transform:translateY(26px);width:max-content;max-width:980px}
.scene.active .tb-l2{animation:tbpop .55s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:calc(var(--d) + .06s)}
.tb-l2.skew{color:__ACCENT__;transform:skewX(__SKEW__deg) translateY(26px);text-shadow:7px 7px 0 __SECOND__}
.scene.active .tb-l2.skew{animation:tbskew .55s cubic-bezier(.2,.8,.2,1) forwards .06s}
.tb-l2.box .tb-tx{background:__ACCENT__;color:#111;padding:4px 20px;box-decoration-break:clone}
.tb-l2.outline{color:transparent;-webkit-text-stroke:4px __ACCENT__}
/* stat */
.tb-mega{font-size:440px;line-height:.86;color:__ACCENT__;letter-spacing:-10px;text-shadow:9px 9px 0 __SECOND__;
  opacity:0;transform:translateY(24px)}
.scene.active .tb-mega{animation:tbpop .6s cubic-bezier(.2,.8,.2,1) forwards}
.tb-mega .tb-su,.tb-split .tb-su{font-size:170px;-webkit-text-stroke:0}
.tb-split{display:flex;align-items:flex-end;gap:6px}
.tb-dg{font-size:380px;line-height:.86;color:__ACCENT__;text-shadow:8px 8px 0 __SECOND__;opacity:0;transform:translateY(30px) rotate(-4deg)}
.scene.active .tb-dg{animation:tbpop .5s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:var(--d)}
.tb-sticker{align-self:flex-start;margin-top:30px;background:#fff;color:#111;font-size:56px;font-weight:900;padding:14px 30px;
  transform:rotate(__TILT__deg);box-shadow:0 14px 36px rgba(0,0,0,.5);opacity:0}
.scene.active .tb-sticker{animation:tbpop .5s ease forwards .3s}
/* code screenshot card */
.tb-shot{background:#16181c;border:4px solid __ACCENT__;border-radius:14px;overflow:hidden;transform:rotate(__TILT__deg);
  box-shadow:0 24px 50px rgba(0,0,0,.55);opacity:0}
.scene.active .tb-shot{animation:tbpop .55s cubic-bezier(.2,.8,.2,1) forwards}
.tb-shotbar{background:__ACCENT__;color:#111;font-size:26px;font-weight:900;letter-spacing:4px;padding:10px 24px}
.tb-code{font-family:"Noto Sans Mono CJK SC","DejaVu Sans Mono",monospace;font-weight:400;font-size:42px;line-height:1.5;padding:32px 30px;color:#e8edf2}
.tb-cl{white-space:pre;opacity:0}.scene.active .tb-cl{animation:tbf .4s ease forwards;animation-delay:var(--d)}
.t-kw{color:__ACCENT__;font-weight:700}.t-str{color:#9ece6a}.t-cmt{color:#7d8590;font-style:italic}.t-num{color:__SECOND__}.t-fn{color:#7aa2f7}.t-dec{color:#e0af68}
.tb-callout{margin-top:28px;color:__ACCENT__;font-size:52px;font-weight:900;transform:rotate(-1deg);opacity:0}
.scene.active .tb-callout{animation:tbrise .5s ease forwards .35s}
/* compare */
.scene.tb.cmp{gap:18px}
.tb-blk{font-size:84px;font-weight:900;padding:26px 34px;opacity:0;transform:translateX(-30px);align-self:flex-start;max-width:920px}
.scene.active .tb-blk{animation:tbslide .5s cubic-bezier(.2,.8,.2,1) forwards}
.tb-blk.old{color:#8a8a8a}.tb-blk.old .tb-tx{text-decoration:line-through;text-decoration-color:__SECOND__;text-decoration-thickness:8px}
.tb-blk.new{background:__ACCENT__;color:#111;align-self:flex-end;transform:translateX(30px)}.scene.active .tb-blk.new{animation-delay:.24s}
.tb-vs{font-size:64px;color:__SECOND__;font-weight:900;align-self:center;transform:rotate(-6deg);opacity:0}
.scene.active .tb-vs{animation:tbpop .4s ease forwards .15s}
/* bullets as chips */
.tb-bhead{font-size:64px;font-weight:900;margin-bottom:38px;opacity:0}.scene.active .tb-bhead{animation:tbrise .5s ease forwards}
.tb-chips{display:flex;flex-direction:column;gap:26px;align-items:flex-start}
.tb-chip{font-size:64px;font-weight:900;padding:16px 32px;opacity:0;transform:translateX(-26px) rotate(-1deg)}
.scene.active .tb-chip{animation:tbslide .5s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:var(--d)}
.tb-chip.c0{background:__ACCENT__;color:#111}.tb-chip.c1{background:__SECOND__;color:#111}.tb-chip.c2{background:#fff;color:#111}
.tb-card{background:#1c1c1c;border:3px solid __ACCENT__;padding:30px 34px;font-size:56px;font-weight:800;line-height:1.4;
  align-self:flex-start;transform:rotate(__TILT__deg);max-width:900px}
@keyframes tbf{to{opacity:1;transform:none}}
@keyframes tbrise{to{opacity:1;transform:none}}
@keyframes tbslide{to{opacity:1;transform:none}}
@keyframes tbpop{to{opacity:1;transform:none}}
@keyframes tbskew{to{opacity:1;transform:skewX(__SKEW__deg)}}
/* cover: first scene fully composed */
.scene.tb:first-of-type .tb-l1,.scene.tb:first-of-type .tb-l2{opacity:1;transform:none;animation:none}
.scene.tb:first-of-type .tb-l2.skew{transform:skewX(__SKEW__deg);animation:none}
"""
