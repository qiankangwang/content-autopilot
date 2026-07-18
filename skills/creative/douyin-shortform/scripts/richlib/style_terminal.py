#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_terminal — C · 终端/IDE (GitHub-dark, mono, code blocks, command line).

On-brand for an AI-coding account: editor windows with traffic-lights + filename
tabs + line numbers, a $ prompt with a blinking caret, diffs, a status bar.
variant() rotates the accent, filename, and a layout per scene type.
"""
from .base import Style, esc, big_fs, highlight, blob, scene_types

_ACCENTS = ["#7ee787", "#79c0ff", "#d2a8ff", "#ffa657", "#56d4dd"]
_FILES = ["openai_chips.ts", "today.py", "ai_news.md", "notes.rs", "ship.go"]


def _fill(css, m):
    for k, v in m.items():
        css = css.replace(k, str(v))
    return css


class TerminalStyle(Style):
    id = "terminal"
    weight = 1.0
    label = "终端"

    def affinity(self, spec):
        b = blob(spec)
        techy = any(k in b for k in ("代码", "编程", "开发", "bug", "重构", "命令", "终端",
                                     "脚本", "api", "框架", "报错", "调试", "部署", "agent",
                                     "模型", "芯片", "算法", "程序员", "开源"))
        score = 1.0
        if "code" in scene_types(spec):
            score *= 2.2
        if techy:
            score *= 1.6
        else:
            # `$ prompt` chrome on a life/society topic reads as gibberish to a
            # lay audience (2026-07-15: a typhoon-tape video shipped full of
            # `$ measure` / `diff` cards) — hard-gate this style to tech topics.
            score *= 0.01
        if "游戏" in b and "code" not in scene_types(spec):
            score *= 0.6
        return score

    def variant(self, rng):
        return {
            "accent": rng.choice(_ACCENTS),
            "file": rng.choice(_FILES),
            "hook": rng.choice(["prompt", "comment", "tab"]),
            "stat": rng.choice(["diff", "stdout", "neon"]),
            "bullets": rng.choice(["checklist", "stdout"]),
        }

    def css(self, ctx):
        return _fill(_CSS, {"__ACCENT__": ctx["accent"]})

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
        return f'<section class="scene tm" data-i="{i}"><div class="tm-cmt">// {body}</div></section>'

    def _hook(self, i, sc, ctx):
        lines = sc.get("lines", []) or [sc.get("say", "")]
        fs = big_fs(lines, base=104)
        head = "".join(f'<div class="tm-h" style="--d:{0.10*j:.2f}s;font-size:{fs}px">{esc(x)}</div>' for j, x in enumerate(lines))
        mode = ctx["hook"]
        if mode == "comment":
            top = f'<div class="tm-banner">/* {esc(sc.get("eyebrow","")) or "今日头条"} */</div>'
        elif mode == "tab":
            top = (f'<div class="tm-tabbar"><span class="d r"></span><span class="d y"></span><span class="d g"></span>'
                   f'<span class="tm-tab">{esc(ctx["file"])}</span></div>')
        else:
            top = f'<div class="tm-prompt">$ ai-news --why<span class="cur"></span></div>'
        return f'<section class="scene tm hook" data-i="{i}">{top}<div class="tm-head">{head}</div></section>'

    def _outro(self, i, sc, ctx):
        lines = sc.get("lines", []) or [sc.get("say", "")]
        fs = big_fs(lines, base=96)
        head = "".join(f'<div class="tm-h" style="--d:{0.10*j:.2f}s;font-size:{fs}px">{esc(x)}</div>' for j, x in enumerate(lines))
        return (f'<section class="scene tm outro" data-i="{i}"><div class="tm-prompt">$ git commit -m<span class="cur"></span></div>'
                f'<div class="tm-head">{head}</div></section>')

    def _stat(self, i, sc, ctx):
        val, unit, label = esc(sc.get("value", "")), esc(sc.get("unit", "")), esc(sc.get("label", ""))
        m = ctx["stat"]
        if m == "diff":
            return (f'<section class="scene tm stat" data-i="{i}"><div class="tm-difflines">'
                    f'<div class="tm-d minus">- 老办法</div>'
                    f'<div class="tm-d plus">+ {label} <span class="tm-big">{val}{unit}</span></div></div></section>')
        if m == "stdout":
            return (f'<section class="scene tm stat" data-i="{i}"><div class="tm-prompt">$ measure<span class="cur"></span></div>'
                    f'<div class="tm-out">&gt;&gt; {label}: <span class="tm-big">{val}{unit}</span></div></section>')
        return (f'<section class="scene tm stat neon" data-i="{i}"><div class="tm-neon">{val}<span class="su">{unit}</span></div>'
                f'<div class="tm-cmt">// {label}</div></section>')

    def _code(self, i, sc, ctx):
        lines = highlight(sc.get("code", ""), sc.get("lang", "python"))
        body = "".join(f'<div class="tm-cl" style="--d:{0.08*j:.2f}s"><span class="tm-ln">{j+1}</span><span class="tm-ct">{ln}</span></div>'
                       for j, ln in enumerate(lines))
        cap = f'<div class="tm-codecap"># {esc(sc["caption"])}</div>' if sc.get("caption") else ""
        return (f'<section class="scene tm code" data-i="{i}"><div class="tm-win">'
                f'<div class="tm-winbar"><span class="d r"></span><span class="d y"></span><span class="d g"></span>'
                f'<span class="tm-tab">{esc(ctx["file"])}</span><span class="tm-lang">{esc(sc.get("lang","code"))}</span></div>'
                f'<div class="tm-codebody">{body}</div></div>{cap}</section>')

    def _compare(self, i, sc, ctx):
        return (f'<section class="scene tm cmp" data-i="{i}"><div class="tm-win">'
                f'<div class="tm-winbar"><span class="d r"></span><span class="d y"></span><span class="d g"></span>'
                f'<span class="tm-tab">diff</span></div>'
                f'<div class="tm-codebody"><div class="tm-cl minus"><span class="tm-ln">-</span><span class="tm-ct">{esc(sc.get("before",""))}</span></div>'
                f'<div class="tm-cl plus"><span class="tm-ln">+</span><span class="tm-ct">{esc(sc.get("after",""))}</span></div></div></div></section>')

    def _bullets(self, i, sc, ctx):
        head = f'<div class="tm-bhead"># {esc(sc["head"])}</div>' if sc.get("head") else ""
        rows = sc.get("lines", [])
        if ctx["bullets"] == "checklist":
            items = "".join(f'<div class="tm-li" style="--d:{0.12*j:.2f}s"><span class="tm-box">[<span class="tm-x">x</span>]</span>'
                            f'<span class="tm-lt">{esc(x)}</span></div>' for j, x in enumerate(rows))
        else:
            items = "".join(f'<div class="tm-li" style="--d:{0.12*j:.2f}s"><span class="tm-box">&gt;</span>'
                            f'<span class="tm-lt">{esc(x)}</span></div>' for j, x in enumerate(rows))
        return f'<section class="scene tm bul" data-i="{i}">{head}<div class="tm-list">{items}</div></section>'


_CSS = r"""
html,body{background:#0b0f17;font-family:"Noto Sans Mono CJK SC","DejaVu Sans Mono",monospace;color:#c9d1d9}
.bar{background:__ACCENT__;height:8px;box-shadow:0 0 16px __ACCENT__}
.scene.tm{padding:0 60px}
.d{width:18px;height:18px;border-radius:50%;display:inline-block}.r{background:#ff5f56}.y{background:#ffbd2e}.g{background:#27c93f}
.tm-status{position:absolute;bottom:84px;left:60px;right:60px;z-index:6;font-size:26px;color:#8b949e;display:flex;align-items:center;gap:14px}
.tm-on{color:__ACCENT__}.tm-sep{color:#3d444d}.tm-br{margin-left:auto;color:__ACCENT__;opacity:.8}
/* hook */
.tm-prompt{font-size:40px;color:#e6edf3;margin-bottom:30px}
.cur{display:inline-block;width:20px;height:38px;background:__ACCENT__;vertical-align:-6px;margin-left:8px;animation:bl 1s steps(1) infinite}
.tm-banner{font-size:38px;color:#8b949e;font-style:italic;margin-bottom:26px}
.tm-tabbar{display:inline-flex;align-items:center;gap:11px;background:#161b22;border:1px solid #20262f;border-bottom:none;
  border-radius:12px 12px 0 0;padding:16px 26px;margin-bottom:0}
.tm-tabbar .tm-tab{margin-left:14px;color:#e6edf3;font-size:30px}
.tm-head{}
.tm-h{font-family:"Noto Sans CJK SC",sans-serif;font-weight:900;line-height:1.1;color:#e6edf3;opacity:0;transform:translateY(20px)}
.scene.active .tm-h{animation:tmrise .6s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.tm-h:last-of-type{color:__ACCENT__}
/* stat */
.tm-difflines{font-size:64px;font-weight:700}
.tm-d{padding:18px 30px;border-radius:10px;opacity:0;transform:translateX(-26px)}
.scene.active .tm-d{animation:tmslide .55s cubic-bezier(.2,.7,.2,1) forwards}
.tm-d.minus{color:#8b949e;background:rgba(248,81,73,.10);text-decoration:line-through}
.tm-d.plus{color:#7ee787;background:rgba(63,185,80,.12);margin-top:18px}.scene.active .tm-d.plus{animation-delay:.2s}
.tm-big{font-weight:900}
.tm-out{font-size:60px;color:#c9d1d9;margin-top:10px}.tm-out .tm-big{color:__ACCENT__;font-weight:900;font-size:88px}
.tm-neon{font-family:"Noto Sans CJK SC",sans-serif;font-weight:900;font-size:320px;line-height:.92;color:__ACCENT__;
  text-shadow:0 0 50px __ACCENT__;opacity:0;transform:translateY(24px)}
.scene.active .tm-neon{animation:tmrise .8s cubic-bezier(.2,.8,.2,1) forwards}
.tm-neon .su{font-size:140px}
.tm-cmt{font-size:48px;color:#8b949e;line-height:1.6;max-width:920px;margin-top:14px}
/* code window (shared by code + compare) */
.tm-win{border:1px solid #20262f;border-radius:16px;background:#0d1117;overflow:hidden;box-shadow:0 36px 90px rgba(0,0,0,.6);
  opacity:0;transform:translateY(26px) scale(.97)}
.scene.active .tm-win{animation:tmpop .6s cubic-bezier(.2,.8,.2,1) forwards}
.tm-winbar{display:flex;align-items:center;gap:11px;padding:22px 26px;background:#161b22;border-bottom:1px solid #20262f}
.tm-winbar .tm-tab{margin-left:16px;color:#e6edf3;font-size:30px}.tm-lang{margin-left:auto;color:#8b949e;font-size:26px}
.tm-codebody{padding:34px 30px;font-size:44px;line-height:1.55}
.tm-cl{white-space:pre;display:flex;gap:20px;opacity:0;transform:translateX(-10px)}
.scene.active .tm-cl{animation:tmf .4s ease forwards;animation-delay:var(--d)}
.tm-ln{color:#3d444d;min-width:48px;text-align:right;user-select:none}
.tm-ct{flex:1;white-space:pre}
.tm-cl.minus{background:rgba(248,81,73,.12)}.tm-cl.minus .tm-ln,.tm-cl.minus .tm-ct{color:#f8a39d}
.tm-cl.plus{background:rgba(63,185,80,.14)}.tm-cl.plus .tm-ln,.tm-cl.plus .tm-ct{color:#7ee787}
.t-kw{color:#ff7b72}.t-str{color:#a5d6ff}.t-cmt{color:#8b949e;font-style:italic}.t-num{color:#79c0ff}.t-fn{color:#d2a8ff}.t-dec{color:#e3b341}
.tm-codecap{font-size:42px;color:#8b949e;margin-top:28px;opacity:0}.scene.active .tm-codecap{animation:tmf .5s ease forwards .4s}
/* bullets */
.tm-bhead{font-size:50px;color:#8b949e;margin-bottom:40px;opacity:0}.scene.active .tm-bhead{animation:tmf .5s ease forwards}
.tm-list{display:flex;flex-direction:column;gap:34px}
.tm-li{display:flex;align-items:center;gap:24px;font-size:60px;opacity:0;transform:translateX(-20px)}
.scene.active .tm-li{animation:tmslide .5s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.tm-box{color:#8b949e;font-weight:700}.tm-x{color:__ACCENT__}.tm-lt{color:#e6edf3}
@keyframes tmf{to{opacity:1;transform:none}}
@keyframes tmrise{to{opacity:1;transform:none}}
@keyframes tmslide{to{opacity:1;transform:none}}
@keyframes tmpop{to{opacity:1;transform:none}}
@keyframes bl{50%{opacity:0}}
/* cover: first scene fully composed */
.scene.tm:first-of-type .tm-h{opacity:1;transform:none;animation:none}
.scene.tm:first-of-type .tm-win,.scene.tm:first-of-type .tm-neon{opacity:1;transform:none;animation:none}
"""
