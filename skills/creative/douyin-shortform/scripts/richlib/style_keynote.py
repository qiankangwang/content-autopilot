#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_keynote — 暗色聚光「发布会舞台」风 (the original look, redesigned).

2026-07-19 visual overhaul (same pass as style_editorial): text cards used to
be small type floating in a void — unfinished-PPT feel. Now the stage itself is
designed (dual spotlights, perspective floor grid, ghost stroked glyph, edge
vignette), type is 15–25%% larger, every card type gets structure (glow bars,
ghost number echoes, glass panels) so no card shows more than ~1/4 screen of
continuous dead space. Subtitle plate and the landscape media canvas are
reskinned to match the stage. No corner branding (user decision 2026-07-18).
"""
from . import base
from .base import Style, esc, rgba, highlight

_ACCENTS = ["#FF2E4D", "#2E7BFF", "#16C784", "#7C5CFF", "#FF7A00", "#FF2E88"]
_COOLS = {"#FF2E4D": "#2E7BFF", "#2E7BFF": "#16C784", "#16C784": "#2E7BFF",
          "#7C5CFF": "#2EE6FF", "#FF7A00": "#2E7BFF", "#FF2E88": "#7C5CFF"}
# ghost stage ornaments: geometric glyphs only (a big number could read as an
# episode count — that's banned branding territory)
_GHOSTS = ["△", "▽", "◎", "◇", "○", "∞"]


def _big_lines(lines, base_fs=152, grad=False):
    """Headline stack; grad=True paints the last line with the accent→cool
    gradient (the keynote 'hero word' treatment)."""
    fs = base.big_fs(lines, base=base_fs)
    n = len(lines)
    out = []
    for j, x in enumerate(lines):
        cls = "big grad" if (grad and j == n - 1) else "big"
        out.append(f'<div class="{cls}" style="--d:{0.10*j:.2f}s;font-size:{fs}px">{esc(x)}</div>')
    return "".join(out)


class KeynoteStyle(Style):
    id = "keynote"
    weight = 0.35          # rare rotation option
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
            "hook": rng.choice(["grad", "bar"]),
            "stat": rng.choice(["left", "center"]),
            "bullets": rng.choice(["index", "beam"]),
            "ghost": rng.choice(_GHOSTS),
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
            "ADIM": rgba(accent, .14), "ASH": rgba(accent, .45),
            "ASTROKE": rgba(accent, .5),
            "CDIM": rgba(cool, .12),
            "STROKE": "rgba(255,255,255,.10)" if dark else "rgba(0,0,0,.12)",
            "VIG": "rgba(3,5,10,.52)" if dark else "rgba(22,25,34,.16)",
            "GLASS": "rgba(255,255,255,.06)" if dark else "rgba(255,255,255,.62)",
            "GLASSBD": "rgba(255,255,255,.16)" if dark else "rgba(0,0,0,.10)",
            "LINE": "rgba(255,255,255,.05)" if dark else "rgba(0,0,0,.05)",
        }
        return _CSS % p

    def background(self, ctx):
        # stage architecture (NOT branding): dual spotlights, perspective floor
        # grid, oversized stroked ghost glyph, edge vignette — the frame reads
        # as a designed keynote slide even behind a short text card.
        ghost = esc(ctx.get("ghost", "△"))
        drift = ('<div class="glow a"></div><div class="glow b"></div>'
                 if ctx.get("glow", True) else "")
        return (f'{drift}'
                '<div class="kn-spot tl"></div><div class="kn-spot br"></div>'
                '<div class="kn-floor"></div><div class="grid"></div>'
                f'<div class="kn-ghost">{ghost}</div>'
                '<div class="kn-vig"></div>')

    def chrome(self, spec, ctx):
        return ""   # no corner branding (user decision 2026-07-18)

    def scene(self, i, sc, ctx):
        t = sc.get("type", "point")
        if t == "hook":
            eb = f'<div class="eyebrow">{esc(sc["eyebrow"])}</div>' if sc.get("eyebrow") else ""
            grad = ctx.get("hook") == "grad"
            return (f'<section class="scene hook" data-i="{i}">{eb}'
                    f'<div class="biglines">{_big_lines(sc.get("lines", []), base_fs=152, grad=grad)}'
                    f'<div class="accentbar"></div></div></section>')
        if t == "stat":
            val, unit = esc(sc.get("value", "")), esc(sc.get("unit", ""))
            cls = "scene stat " + ("center" if ctx.get("stat") == "center" else "left")
            return (f'<section class="{cls}" data-i="{i}">'
                    f'<div class="statghost">{val}</div>'
                    f'<div class="statwrap"><div class="statnum">{val}'
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
                    f'<div class="kn-vs">VS</div>'
                    f'<div class="cmp after"><span class="cmpicon">✓</span>'
                    f'<span class="cmptext">{esc(sc.get("after",""))}</span></div></section>')
        if t == "bullets":
            rows = sc.get("lines", [])
            if ctx.get("bullets") == "index":
                items = "".join(
                    f'<div class="bitem" style="--d:{0.14*j:.2f}s"><span class="bnum">{j+1:02d}</span>'
                    f'<span class="btext">{esc(x)}</span></div>' for j, x in enumerate(rows))
            else:
                items = "".join(
                    f'<div class="bitem" style="--d:{0.14*j:.2f}s"><span class="bbeam"></span>'
                    f'<span class="btext">{esc(x)}</span></div>' for j, x in enumerate(rows))
            head = (f'<div class="bhead">{esc(sc["head"])}</div><div class="hairbar"></div>'
                    if sc.get("head") else "")
            count = f"{len(rows):02d}"
            return (f'<section class="scene bullets" data-i="{i}">'
                    f'<div class="kn-count">{count}</div>'
                    f'{head}<div class="blist">{items}</div></section>')
        if t == "outro":
            return (f'<section class="scene outro" data-i="{i}">'
                    f'<div class="biglines">{_big_lines(sc.get("lines", []), base_fs=140, grad=True)}'
                    f'<div class="accentbar"></div></div></section>')
        return (f'<section class="scene hook" data-i="{i}">'
                f'<div class="biglines">{_big_lines(sc.get("lines", [sc.get("say","")]), base_fs=140)}'
                f'</div></section>')


_CSS = r"""
html,body{background:%(BG)s;font-family:"Noto Sans CJK SC","Source Han Sans SC",sans-serif}
.bar{background:%(ACCENT)s;box-shadow:0 0 18px %(ACCENT)s}
/* ── stage architecture: spotlights + floor grid + ghost glyph + vignette ── */
.glow{position:absolute;border-radius:50%%;filter:blur(120px);opacity:.20;z-index:0}
.glow.a{width:760px;height:760px;background:%(ACCENT)s;top:-160px;right:-180px;animation:floatA 14s ease-in-out infinite alternate}
.glow.b{width:680px;height:680px;background:%(COOL)s;bottom:-200px;left:-160px;animation:floatB 16s ease-in-out infinite alternate}
@keyframes floatA{from{transform:translate(0,0)}to{transform:translate(-60px,80px)}}
@keyframes floatB{from{transform:translate(0,0)}to{transform:translate(70px,-60px)}}
.kn-spot{position:absolute;z-index:0;pointer-events:none}
.kn-spot.tl{left:-340px;top:-380px;width:1240px;height:1240px;
  background:radial-gradient(circle,%(ADIM)s,transparent 62%%)}
.kn-spot.br{right:-360px;bottom:-340px;width:1180px;height:1180px;
  background:radial-gradient(circle,%(CDIM)s,transparent 62%%)}
.kn-floor{position:absolute;left:-22%%;right:-22%%;bottom:-60px;height:780px;z-index:0;opacity:.55;
  background-image:linear-gradient(%(LINE)s 2px,transparent 2px),
    linear-gradient(90deg,%(LINE)s 2px,transparent 2px);
  background-size:118px 118px;transform:perspective(880px) rotateX(60deg);
  transform-origin:50%% 100%%;mask-image:linear-gradient(180deg,transparent 4%%,#000 64%%)}
.grid{position:absolute;inset:0;z-index:0;opacity:.5;background-image:radial-gradient(%(DOT)s 1.5px,transparent 1.6px);
  background-size:46px 46px;mask-image:linear-gradient(180deg,transparent,#000 30%%,#000 70%%,transparent)}
.kn-ghost{position:absolute;top:110px;right:-30px;z-index:0;font-weight:900;font-size:660px;
  line-height:1;color:transparent;-webkit-text-stroke:3px %(STROKE)s;pointer-events:none}
.kn-vig{position:absolute;inset:0;z-index:1;pointer-events:none;
  background:radial-gradient(ellipse 135%% 115%% at 50%% 42%%,transparent 56%%,%(VIG)s)}
/* subtitles: keynote skin — deep glass plate + accent footlight (white text
   + the dark -webkit-text-stroke stay inherited from base) */
.sub{background:rgba(9,12,19,.66);border:1.5px solid rgba(255,255,255,.13);
  border-bottom:7px solid %(ACCENT)s;border-radius:16px;
  backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);
  box-shadow:0 10px 30px rgba(0,0,0,.4),0 16px 44px %(ASH)s}
/* media fit canvas: dark stage + spotlights + vignette (no blurred-black fill) */
.media-canvas{background:
  radial-gradient(860px 720px at 16%% 10%%,%(ADIM)s,transparent 62%%),
  radial-gradient(820px 700px at 86%% 88%%,%(CDIM)s,transparent 62%%),
  radial-gradient(ellipse 140%% 120%% at 50%% 42%%,transparent 55%%,rgba(0,0,0,.5)),
  #0B0E14}
.media-fitpos,.media-fit{border-radius:24px}
/* ── scenes ── */
.scene{padding:0 96px;transform:translateY(18px) scale(.992);transition:opacity .45s ease,transform .45s ease}
.scene.active{transform:none}
.biglines{position:relative}
.eyebrow{color:%(ACCENT)s;font-weight:800;font-size:50px;letter-spacing:4px;margin-bottom:30px;
  text-shadow:0 0 34px %(ASH)s;opacity:0}
.scene.active .eyebrow{animation:rise .6s ease forwards}
.big{color:%(FG)s;font-weight:900;line-height:1.14;letter-spacing:1px;opacity:0;transform:translateY(42px)}
.big.grad{background:linear-gradient(94deg,%(ACCENT)s 8%%,%(COOL)s 92%%);
  -webkit-background-clip:text;background-clip:text;color:transparent}
.scene.active .big{animation:rise .72s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.accentbar{height:14px;width:0;border-radius:8px;margin-top:44px;
  background:linear-gradient(90deg,%(ACCENT)s,%(COOL)s);box-shadow:0 0 32px %(ASH)s}
.scene.active .accentbar{animation:grow .8s cubic-bezier(.2,.7,.2,1) forwards .35s}
/* stat: hero number with glow + a stroked ghost echo filling the stage */
.statghost{position:absolute;left:50%%;top:44%%;transform:translate(-50%%,-50%%);z-index:0;
  font-weight:900;font-size:540px;line-height:1;letter-spacing:-14px;white-space:nowrap;
  color:transparent;-webkit-text-stroke:3px %(ASTROKE)s;opacity:.34;pointer-events:none}
.statwrap{position:relative;text-align:left}
.stat.center .statwrap{text-align:center}
.statnum{color:%(ACCENT)s;font-weight:900;font-size:340px;line-height:.96;letter-spacing:-4px;
  text-shadow:0 0 70px %(ASH)s,0 0 190px %(ADIM)s;opacity:0;transform:translateY(30px) scale(.9)}
.scene.active .statnum{animation:popbig .75s cubic-bezier(.2,.8,.2,1) forwards}
.statunit{font-size:136px}
.statlabel{color:%(FG)s;font-weight:800;font-size:86px;margin-top:26px;opacity:0}
.scene.active .statlabel{animation:rise .6s ease forwards .3s}
/* code window */
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
.codecap{color:%(FG)s;font-weight:800;font-size:66px;margin-top:46px;opacity:0}
.scene.active .codecap{animation:rise .6s ease forwards .5s}
/* compare: two glass panels on the stage + stroked VS divider */
.compare{gap:44px}
.kn-vs{align-self:center;font-weight:900;font-size:92px;letter-spacing:6px;color:transparent;
  -webkit-text-stroke:2.5px %(ASTROKE)s;opacity:0;transform:scale(.7)}
.scene.active .kn-vs{animation:popbig .5s cubic-bezier(.2,.8,.2,1) forwards .14s}
.cmp{display:flex;align-items:center;gap:32px;padding:52px 54px;border-radius:30px;font-weight:800;font-size:76px;opacity:0;
  background:%(GLASS)s;border:1.5px solid %(GLASSBD)s;
  backdrop-filter:blur(20px);-webkit-backdrop-filter:blur(20px);
  box-shadow:0 30px 80px rgba(0,0,0,.35)}
.cmp .cmpicon{width:84px;height:84px;min-width:84px;border-radius:50%%;display:flex;align-items:center;justify-content:center;font-size:50px;color:#fff}
.cmp.before{color:%(SUB)s;transform:translateX(-60px)}
.cmp.before .cmpicon{background:#6B7280}
.cmp.before .cmptext{text-decoration:line-through;text-decoration-color:%(SUB)s}
.cmp.after{color:%(FG)s;transform:translateX(60px);border-color:%(ASTROKE)s;
  background:linear-gradient(135deg,%(ADIM)s,%(GLASS)s);
  box-shadow:0 30px 80px rgba(0,0,0,.35),0 0 60px %(ADIM)s}
.cmp.after .cmpicon{background:%(ACCENT)s;box-shadow:0 0 30px %(ASH)s}
.scene.active .cmp.before{animation:slidex .6s cubic-bezier(.2,.7,.2,1) forwards .05s}
.scene.active .cmp.after{animation:slidex .6s cubic-bezier(.2,.7,.2,1) forwards .22s}
/* bullets: big rows with index strokes / light beams + a stroked count echo */
.kn-count{position:absolute;top:130px;right:20px;z-index:0;font-weight:900;font-size:460px;
  line-height:1;letter-spacing:-10px;color:transparent;-webkit-text-stroke:3px %(ASTROKE)s;
  opacity:.3;pointer-events:none}
.bhead{color:%(FG)s;font-weight:900;font-size:80px;margin-bottom:18px;opacity:0}
.scene.active .bhead{animation:rise .55s ease forwards}
.hairbar{height:10px;width:0;border-radius:6px;margin-bottom:44px;
  background:linear-gradient(90deg,%(ACCENT)s,%(COOL)s);box-shadow:0 0 24px %(ASH)s}
.scene.active .hairbar{animation:growh .7s cubic-bezier(.2,.7,.2,1) forwards .25s}
.blist{display:flex;flex-direction:column}
.bitem{display:flex;align-items:center;gap:36px;padding:32px 0;opacity:0;transform:translateY(26px);
  border-bottom:1px solid %(GLASSBD)s}
.bitem:last-child{border-bottom:0}
.scene.active .bitem{animation:rise .6s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.bnum{font-weight:900;font-size:96px;line-height:1;min-width:128px;color:transparent;-webkit-text-stroke:3px %(ACCENT)s}
.bbeam{width:16px;min-width:16px;height:88px;border-radius:8px;
  background:linear-gradient(180deg,%(ACCENT)s,%(COOL)s);box-shadow:0 0 28px %(ASH)s}
.btext{color:%(FG)s;font-weight:800;font-size:82px;line-height:1.22}
@keyframes rise{from{opacity:0;transform:translateY(34px)}to{opacity:1;transform:none}}
@keyframes grow{to{width:240px}}
@keyframes growh{to{width:220px}}
@keyframes pop{from{opacity:0;transform:translateY(-10px) scale(.96)}to{opacity:1;transform:none}}
@keyframes popbig{from{opacity:0;transform:translateY(30px) scale(.92)}to{opacity:1;transform:none}}
@keyframes slidein{from{opacity:0;transform:translateX(-14px)}to{opacity:1;transform:none}}
@keyframes slidex{to{opacity:1;transform:none}}
/* cover: FIRST scene fully composed, no entrance (contract) */
.scene:first-of-type .eyebrow,.scene:first-of-type .big,.scene:first-of-type .statnum,
.scene:first-of-type .statlabel,.scene:first-of-type .bhead,.scene:first-of-type .bitem,
.scene:first-of-type .cmp,.scene:first-of-type .kn-vs,.scene:first-of-type .win,
.scene:first-of-type .codeline,.scene:first-of-type .codecap{opacity:1;transform:none;animation:none}
.scene:first-of-type .accentbar{width:240px;animation:none}
.scene:first-of-type .hairbar{width:220px;animation:none}
"""
