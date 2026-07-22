#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_tabloid — D · 大字快报 (black + acid, huge mixed type, tilt, sticker).

Maximum 抖音 stop-power, but art-directed — real hierarchy inside the chaos.
variant() rotates a 2-color scheme, skew, and a layout per scene type.
2026-07-19 whitespace-kill pass (same playbook as style_editorial): structural
street-poster furniture in background(), bigger type, every text card packed
into blocks/bars so no card shows more than ~1/4 screen of flat empty color.
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
            # per-type LAYOUT pools — compositionally distinct, not cosmetic
            # (2026-07-22 「卡片单一」 feedback)
            "hook": rng.choice(["skew", "box", "outline", "banner"]),
            "stat": rng.choice(["sticker", "split", "tag"]),
            "bullets": rng.choice(["bars", "torn", "scatter"]),
            "compare": rng.choice(["slam", "ring", "frontpage"]),
            "outro": rng.choice(["box", "stamp", "tail"]),
            "tilt": rng.choice([-3, 2, 3, 4]),
            "ghost": rng.choice(["!", "?", "!!"]),
            "gtilt": rng.choice([-12, -8, 8, 12]),
        }

    def css(self, ctx):
        return _fill(_CSS, {
            "__BG__": ctx["bg"], "__ACCENT__": ctx["accent"],
            "__SECOND__": ctx["second"], "__SKEW__": ctx["skew"], "__TILT__": ctx["tilt"],
            "__GTILT__": ctx["gtilt"],
        })

    def background(self, ctx):
        # structural street-poster furniture (NOT branding): hazard stripes top
        # + bottom, halftone dot blocks, one giant rotated ghost glyph, a rough
        # frame. Fills the dead space that made text cards read as unfinished
        # PPT (2026-07-19 review) — 满版, like a pasted-up 号外.
        g = esc(ctx.get("ghost", "!"))
        return ('<div class="tb-bg">'
                '<div class="tb-stripe top"></div><div class="tb-stripe bot"></div>'
                '<div class="tb-dots tl"></div><div class="tb-dots br"></div>'
                f'<div class="tb-bigghost">{g}</div>'
                '<div class="tb-frame"></div>'
                '</div>')

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
        eb = sc.get("eyebrow", "")
        if outro:
            omode = ctx.get("outro", "box")
            if omode == "stamp":
                # 盖章式: lines + a huge rotated 「完」 stamp slammed over them
                body = "".join(f'<div class="tb-l2 box" style="--d:{0.10*j:.2f}s;font-size:{big_fs([x],base=176)}px">'
                               f'<span class="tb-tx">{esc(x)}</span></div>' for j, x in enumerate(lines))
                return (f'<section class="scene tb hl ostamp" data-i="{i}">{body}'
                        f'<div class="tb-stamp">完</div></section>')
            if omode == "tail":
                # 尾版式: thick full-width frame around the closing line, big
                body = "".join(f'<div class="tb-taill" style="--d:{0.10*j:.2f}s;font-size:{big_fs([x],base=150)}px">'
                               f'{esc(x)}</div>' for j, x in enumerate(lines))
                return (f'<section class="scene tb hl otail" data-i="{i}">'
                        f'<div class="tb-tailbox">{body}</div></section>')
            mode = "box"
        elif ctx["hook"] == "banner":
            # 头版通栏: full-bleed accent banner strip carrying the big line,
            # kicker reversed above it
            out = []
            if eb:
                out.append(f'<div class="tb-eyebrow">{esc(eb)}</div>')
            for j, x in enumerate(lines):
                if j == big_i:
                    out.append(f'<div class="tb-banner" style="--d:{0.10*j:.2f}s;font-size:{big_fs([x],base=168)}px">'
                               f'<span class="tb-tx">{esc(x)}</span></div>')
                else:
                    out.append(f'<div class="tb-l1" style="--d:{0.10*j:.2f}s;font-size:{big_fs([x],base=96)}px">'
                               f'<span class="tb-tx">{esc(x)}</span></div>')
            return f'<section class="scene tb hl banner" data-i="{i}">{"".join(out)}</section>'
        else:
            mode = ctx["hook"]
        out = []
        if eb:
            out.append(f'<div class="tb-eyebrow">{esc(eb)}</div>')
        for j, x in enumerate(lines):
            if j == big_i:
                # 176 is the ceiling that still fits 5 CJK chars in the 912px
                # column — 198 wrapped 5-char lines mid-word (2026-07-19 QA)
                fs = big_fs([x], base=176)
                cls = "tb-l2 " + mode
                out.append(f'<div class="{cls}" style="--d:{0.10*j:.2f}s;font-size:{fs}px"><span class="tb-tx">{esc(x)}</span></div>')
            else:
                fs = big_fs([x], base=96)
                out.append(f'<div class="tb-l1" style="--d:{0.10*j:.2f}s;font-size:{fs}px"><span class="tb-tx">{esc(x)}</span></div>')
        out.append('<div class="tb-hrule"></div>')
        return f'<section class="scene tb hl" data-i="{i}">{"".join(out)}</section>'

    def _stat(self, i, sc, ctx):
        val, unit, label = esc(sc.get("value", "")), esc(sc.get("unit", "")), esc(sc.get("label", ""))
        # ghost number echo + burst block kill the dead space around the figure
        ghost = f'<div class="tb-gnum">{val}</div>'
        boom = '<div class="tb-boom"></div>'
        sticker = (f'<div class="tb-sticker"><span class="tb-tape l"></span>'
                   f'<span class="tb-tape r"></span>{label}</div>')
        if ctx["stat"] == "tag":
            # 价格吊牌式: mega figure hung on a giant price tag with a punch hole
            # + dashed tear line, label on the tag body
            return (f'<section class="scene tb stat tag" data-i="{i}">{ghost}'
                    f'<div class="tb-tagcard"><span class="tb-hole"></span>'
                    f'<div class="tb-tagnum">{val}<span class="tb-su">{unit}</span></div>'
                    f'<div class="tb-tagtear"></div>'
                    f'<div class="tb-taglabel">{label}</div></div></section>')
        if ctx["stat"] == "split":
            digits = "".join(f'<span class="tb-dg" style="--d:{0.07*k:.2f}s">{esc(c)}</span>' for k, c in enumerate(str(sc.get("value", ""))))
            return (f'<section class="scene tb stat" data-i="{i}">{ghost}{boom}'
                    f'<div class="tb-split">{digits}<span class="tb-su">{unit}</span></div>{sticker}</section>')
        return (f'<section class="scene tb stat" data-i="{i}">{ghost}{boom}'
                f'<div class="tb-mega">{val}<span class="tb-su">{unit}</span></div>{sticker}</section>')

    def _code(self, i, sc, ctx):
        lines = highlight(sc.get("code", ""), sc.get("lang", "python"))
        body = "".join(f'<div class="tb-cl" style="--d:{0.07*j:.2f}s">{ln}</div>' for j, ln in enumerate(lines))
        cap = f'<div class="tb-callout">▶ {esc(sc["caption"])}</div>' if sc.get("caption") else ""
        return (f'<section class="scene tb code" data-i="{i}"><div class="tb-shot"><div class="tb-shotbar">CODE</div>'
                f'<div class="tb-code">{body}</div></div>{cap}</section>')

    def _compare(self, i, sc, ctx):
        before, after = esc(sc.get("before", "")), esc(sc.get("after", ""))
        mode = ctx.get("compare", "slam")
        if mode == "ring":
            # 擂台式: left/right colored corners with a lightning VS seam
            return (f'<section class="scene tb cmp ring" data-i="{i}">'
                    f'<div class="tb-corner l"><span class="tb-blab">之前</span>'
                    f'<span class="tb-ctx">{before}</span></div>'
                    f'<div class="tb-bolt">VS</div>'
                    f'<div class="tb-corner r"><span class="tb-blab">之后</span>'
                    f'<span class="tb-ctx">{after}</span></div></section>')
        if mode == "frontpage":
            # 头版对比: 昨天/今天 two stacked newspaper strips
            return (f'<section class="scene tb cmp fp" data-i="{i}">'
                    f'<div class="tb-fp old"><span class="tb-fptag">昨天</span>'
                    f'<span class="tb-tx">{before}</span></div>'
                    f'<div class="tb-fp new"><span class="tb-fptag">今天</span>'
                    f'<span class="tb-tx">{after}</span></div></section>')
        # slam (default): two thick-framed slabs slamming together
        return (f'<section class="scene tb cmp" data-i="{i}">'
                f'<div class="tb-blk old"><span class="tb-blab">之前</span>'
                f'<span class="tb-tx">{before}</span></div>'
                f'<div class="tb-vs">VS</div>'
                f'<div class="tb-blk new"><span class="tb-blab">之后</span>'
                f'<span class="tb-tx">{after}</span></div></section>')

    def _bullets(self, i, sc, ctx):
        head = f'<div class="tb-bhead"><span class="tb-tx">{esc(sc["head"])}</span></div>' if sc.get("head") else ""
        lines = sc.get("lines", [])
        mode = ctx.get("bullets", "bars")
        if mode == "torn":
            # 撕纸清单: each item on a torn-edge paper strip
            rows = "".join(
                f'<div class="tb-torn" style="--d:{0.12*j:.2f}s"><span class="tb-tn">{j+1}</span>'
                f'<span class="tb-tt">{esc(x)}</span></div>' for j, x in enumerate(lines))
            return f'<section class="scene tb bul" data-i="{i}">{head}<div class="tb-tornwrap">{rows}</div></section>'
        if mode == "scatter":
            # 冲击标签墙: sticker labels at varied sizes/tilts
            tilts = [-4, 3, -2, 5, -3]
            rows = "".join(
                f'<div class="tb-sticklbl s{j%3}" style="--d:{0.12*j:.2f}s;--rot:{tilts[j%len(tilts)]}deg">'
                f'<span class="tb-sn">{j+1}</span>{esc(x)}</div>' for j, x in enumerate(lines))
            return f'<section class="scene tb bul scatter" data-i="{i}">{head}<div class="tb-scatter">{rows}</div></section>'
        # bars (default): full-width numbered bars, alternating fills
        chips = "".join(
            f'<div class="tb-chip c{j%3}" style="--d:{0.12*j:.2f}s">'
            f'<span class="tb-cn">{j+1}</span><span class="tb-ct">{esc(x)}</span></div>'
            for j, x in enumerate(lines))
        return f'<section class="scene tb bul" data-i="{i}">{head}<div class="tb-chips">{chips}</div></section>'


_CSS = r"""
html,body{background:__BG__;font-family:"Noto Sans CJK SC",sans-serif;font-weight:900;color:#fff}
.bar{background:__ACCENT__;height:10px}
.scene.tb{padding:0 56px}
/* structural street-poster furniture (background layer, every scene) */
.tb-bg{position:absolute;inset:0;z-index:0;overflow:hidden}
.tb-stripe{position:absolute;left:-60px;right:-60px;height:56px;
  background:repeating-linear-gradient(-45deg,__ACCENT__ 0 34px,#0a0a0a 34px 68px)}
.tb-stripe.top{top:0}
.tb-stripe.bot{bottom:0;background:repeating-linear-gradient(45deg,__ACCENT__ 0 34px,#0a0a0a 34px 68px)}
.tb-dots{position:absolute;width:470px;height:470px;opacity:.42;pointer-events:none;
  background-image:radial-gradient(__SECOND__ 3px,transparent 3.6px);background-size:30px 30px}
.tb-dots.tl{top:100px;left:-70px}
.tb-dots.br{bottom:120px;right:-70px}
.tb-bigghost{position:absolute;top:50%;right:-90px;line-height:.9;pointer-events:none;
  font-size:1150px;font-weight:900;color:transparent;-webkit-text-stroke:7px __ACCENT__;
  opacity:.13;transform:translateY(-50%) rotate(__GTILT__deg)}
.tb-frame{position:absolute;top:88px;bottom:88px;left:26px;right:26px;
  border:5px solid rgba(255,255,255,.14)}
/* subtitles: tabloid skin — solid ink slab, slanted ends, accent base bar
   (keeps base's white fill + dark -webkit-text-stroke) */
.sub{background:rgba(8,8,10,.96);border-radius:0;padding:10px 44px 16px;
  clip-path:polygon(18px 0,100% 0,calc(100% - 18px) 100%,0 100%);
  box-shadow:inset 0 -8px 0 __ACCENT__}
/* media fit canvas: dark wash + hazard corner stripes + halftone, no black blur */
.media-canvas{background:
  radial-gradient(rgba(255,255,255,.08) 2.4px,transparent 3px) 0 0/28px 28px,
  linear-gradient(180deg,rgba(5,5,8,.5),rgba(5,5,8,.12) 26%,rgba(5,5,8,.12) 64%,rgba(5,5,8,.58))}
.media-canvas::before,.media-canvas::after{content:"";position:absolute;width:360px;height:60px;
  background:repeating-linear-gradient(-45deg,__ACCENT__ 0 24px,transparent 24px 48px);opacity:.85}
.media-canvas::before{top:76px;left:0}
.media-canvas::after{bottom:88px;right:0;transform:scaleX(-1)}
.media-fit,.media-fitpos{border-radius:10px}
/* headline — masthead bars, huge center line, hazard rule */
.tb-eyebrow{width:max-content;background:__SECOND__;color:#111;font-size:42px;font-weight:900;
  letter-spacing:4px;padding:10px 28px;border:4px solid #000;margin-bottom:38px;
  opacity:0;transform:rotate(-2deg) translateY(18px)}
.scene.active .tb-eyebrow{animation:tbeb .5s cubic-bezier(.2,.8,.2,1) forwards}
@keyframes tbeb{to{opacity:1;transform:rotate(-2deg)}}
.tb-l1{line-height:1.18;margin-bottom:34px;opacity:0;transform:translateY(22px);
  width:max-content;max-width:968px}
.scene.active .tb-l1{animation:tbrise .5s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:var(--d)}
.tb-l1 .tb-tx{background:#fff;color:#111;padding:6px 24px;box-decoration-break:clone;
  -webkit-box-decoration-break:clone}
.tb-l2{line-height:1.14;margin:26px 0 18px;opacity:0;transform:translateY(26px);width:max-content;max-width:980px}
.scene.active .tb-l2{animation:tbpop .55s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:calc(var(--d) + .06s)}
.tb-l2.skew{color:__ACCENT__;transform:skewX(__SKEW__deg) translateY(26px);text-shadow:8px 8px 0 __SECOND__}
.scene.active .tb-l2.skew{animation:tbskew .55s cubic-bezier(.2,.8,.2,1) forwards .06s}
.tb-l2.box .tb-tx{background:__ACCENT__;color:#111;padding:6px 24px;box-decoration-break:clone;
  -webkit-box-decoration-break:clone;box-shadow:10px 10px 0 rgba(0,0,0,.55)}
.tb-l2.outline{color:transparent;-webkit-text-stroke:5px __ACCENT__;text-shadow:9px 9px 0 rgba(0,0,0,.6)}
.tb-hrule{height:16px;width:0;margin-top:42px;
  background:repeating-linear-gradient(-45deg,__ACCENT__ 0 22px,#0a0a0a 22px 44px)}
.scene.active .tb-hrule{animation:tbgrow .7s cubic-bezier(.2,.8,.2,1) forwards .35s}
@keyframes tbgrow{to{width:560px}}
/* stat — mega figure + ghost echo + burst + taped sticker */
.tb-gnum{position:absolute;top:130px;right:-40px;font-size:520px;line-height:1;font-weight:900;
  color:transparent;-webkit-text-stroke:5px __ACCENT__;opacity:.15;letter-spacing:-8px;
  transform:rotate(__GTILT__deg);pointer-events:none}
.tb-boom{position:absolute;top:420px;left:600px;width:330px;height:330px;background:__SECOND__;
  opacity:.85;transform:rotate(-12deg);pointer-events:none;
  clip-path:polygon(50% 0,61% 35%,98% 35%,68% 57%,79% 91%,50% 70%,21% 91%,32% 57%,2% 35%,39% 35%)}
.tb-mega{position:relative;font-size:440px;line-height:.86;color:__ACCENT__;letter-spacing:-10px;
  text-shadow:9px 9px 0 __SECOND__;opacity:0;transform:translateY(24px)}
.scene.active .tb-mega{animation:tbpop .6s cubic-bezier(.2,.8,.2,1) forwards}
.tb-mega .tb-su,.tb-split .tb-su{font-size:170px;-webkit-text-stroke:0}
.tb-split{position:relative;display:flex;align-items:flex-end;gap:6px}
.tb-dg{font-size:380px;line-height:.86;color:__ACCENT__;text-shadow:8px 8px 0 __SECOND__;opacity:0;transform:translateY(30px) rotate(-4deg)}
.scene.active .tb-dg{animation:tbpop .5s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:var(--d)}
.tb-sticker{position:relative;align-self:flex-start;margin-top:44px;background:#fff;color:#111;
  font-size:70px;font-weight:900;padding:20px 40px;border:5px solid #000;
  transform:rotate(__TILT__deg);box-shadow:12px 12px 0 rgba(0,0,0,.55);opacity:0}
.scene.active .tb-sticker{animation:tbpop .5s ease forwards .3s}
.tb-tape{position:absolute;width:160px;height:46px;background:__ACCENT__;opacity:.8}
.tb-tape.l{left:-46px;top:-24px;transform:rotate(-18deg)}
.tb-tape.r{right:-46px;bottom:-24px;transform:rotate(-14deg)}
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
/* compare — two thick-framed slabs slamming together */
.scene.tb.cmp{gap:26px;padding:0 64px}
.tb-blk{width:100%;font-size:96px;font-weight:900;padding:38px 44px;opacity:0;transform:translateX(-30px)}
.scene.active .tb-blk{animation:tbslide .5s cubic-bezier(.2,.8,.2,1) forwards}
.tb-blab{display:block;font-size:34px;letter-spacing:8px;margin-bottom:14px}
.tb-blk.old{color:#a6a6a6;background:rgba(255,255,255,.06);border:6px solid rgba(255,255,255,.55)}
.tb-blk.old .tb-blab{color:__SECOND__}
.tb-blk.old .tb-tx{text-decoration:line-through;text-decoration-color:__SECOND__;text-decoration-thickness:9px}
.tb-blk.new{background:__ACCENT__;color:#111;border:6px solid #000;
  box-shadow:14px 14px 0 __SECOND__;transform:translateX(30px)}
.scene.active .tb-blk.new{animation-delay:.24s}
.tb-vs{width:max-content;background:__SECOND__;color:#111;font-size:66px;font-weight:900;
  padding:12px 30px;border:5px solid #000;align-self:center;transform:rotate(-7deg);opacity:0}
.scene.active .tb-vs{animation:tbpop .4s ease forwards .15s}
/* bullets — full-width numbered bars, alternating fills */
.tb-bhead{font-size:92px;font-weight:900;margin-bottom:44px;width:max-content;opacity:0}
.tb-bhead .tb-tx{background:#fff;color:#111;padding:6px 26px;box-shadow:10px 10px 0 __SECOND__}
.scene.active .tb-bhead{animation:tbrise .5s ease forwards}
.tb-chips{display:flex;flex-direction:column;gap:32px;align-items:stretch}
.tb-chip{display:flex;align-items:center;gap:30px;font-size:76px;font-weight:900;
  padding:24px 36px;border:5px solid #000;box-shadow:9px 9px 0 rgba(0,0,0,.55);
  opacity:0;transform:translateX(-26px)}
.tb-chip.c0{background:__ACCENT__;color:#111;transform:translateX(-26px) rotate(-.8deg)}
.tb-chip.c1{background:#fff;color:#111;transform:translateX(-26px) rotate(.7deg)}
.tb-chip.c2{background:__SECOND__;color:#111;transform:translateX(-26px) rotate(-.5deg)}
.scene.active .tb-chip{animation:tbchip .5s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:var(--d)}
@keyframes tbchip{to{opacity:1;transform:translateX(0)}}
.tb-cn{flex:none;background:#111;color:#fff;font-size:50px;min-width:78px;height:78px;
  display:flex;align-items:center;justify-content:center}
.tb-ct{line-height:1.16}
.tb-card{background:#1c1c1c;border:4px solid __ACCENT__;padding:38px 42px;font-size:66px;font-weight:800;line-height:1.4;
  align-self:flex-start;transform:rotate(__TILT__deg);max-width:940px;box-shadow:12px 12px 0 rgba(0,0,0,.55)}
/* hook · banner: full-bleed accent strip carrying the big line */
.tb-banner{width:calc(100% + 112px);margin-left:-56px;background:__ACCENT__;color:#111;
  padding:22px 56px;line-height:1.12;box-shadow:0 14px 0 rgba(0,0,0,.55);
  opacity:0;transform:translateX(-40px)}
.scene.active .tb-banner{animation:tbslide .55s cubic-bezier(.2,.8,.2,1) forwards .06s}
.tb-banner .tb-tx{text-shadow:6px 6px 0 rgba(0,0,0,.35)}
/* stat · tag: price-tag hang */
.scene.tb.stat.tag{align-items:center}
.tb-tagcard{position:relative;background:#fff;color:#111;border:6px solid #000;padding:70px 90px 60px;
  transform:rotate(-3deg);box-shadow:16px 16px 0 __SECOND__;opacity:0}
.scene.active .tb-tagcard{animation:tbpop .55s cubic-bezier(.2,.8,.2,1) forwards}
.tb-hole{position:absolute;top:34px;left:50%;width:46px;height:46px;margin-left:-23px;
  border:6px solid #000;border-radius:50%;background:__BG__}
.tb-tagnum{font-size:340px;line-height:.9;font-weight:900;color:__ACCENT__;
  -webkit-text-stroke:5px #000;letter-spacing:-8px;margin-top:30px}
.tb-tagnum .tb-su{font-size:130px;-webkit-text-stroke:3px #000}
.tb-tagtear{height:0;border-top:7px dashed #000;margin:22px -90px 24px}
.tb-taglabel{font-size:66px;font-weight:900;letter-spacing:2px}
/* compare · ring: boxing corners + lightning VS */
.scene.tb.cmp.ring{flex-direction:row;align-items:stretch;gap:0;padding:0 56px}
.tb-corner{flex:1;display:flex;flex-direction:column;justify-content:center;padding:60px 46px;
  font-size:84px;font-weight:900;opacity:0}
.tb-corner.l{background:rgba(255,255,255,.07);border:6px solid rgba(255,255,255,.5);color:#bdbdbd;
  transform:translateX(-30px)}
.tb-corner.l .tb-blab{color:__SECOND__}
.tb-corner.r{background:__ACCENT__;color:#111;border:6px solid #000;transform:translateX(30px)}
.scene.active .tb-corner.l{animation:tbslide .5s cubic-bezier(.2,.8,.2,1) forwards}
.scene.active .tb-corner.r{animation:tbslideR .5s cubic-bezier(.2,.8,.2,1) forwards .2s}
.tb-corner .tb-blab{font-size:34px;letter-spacing:8px;margin-bottom:16px}
.tb-corner .tb-ctx{line-height:1.18}
.tb-bolt{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%) rotate(-8deg);
  background:__SECOND__;color:#111;font-size:72px;font-weight:900;padding:14px 30px;
  border:6px solid #000;z-index:4;opacity:0}
.scene.active .tb-bolt{animation:tbpop .4s ease forwards .18s}
/* compare · frontpage: 昨天/今天 stacked strips */
.scene.tb.cmp.fp{gap:30px;padding:0 60px}
.tb-fp{width:100%;font-size:88px;font-weight:900;padding:40px 46px;border:6px solid #000;
  display:flex;align-items:baseline;gap:28px;opacity:0;transform:translateY(24px)}
.tb-fp .tb-fptag{font-size:40px;letter-spacing:6px;padding:8px 20px;flex:none}
.tb-fp.old{background:rgba(255,255,255,.06);color:#a6a6a6;border-color:rgba(255,255,255,.5)}
.tb-fp.old .tb-fptag{background:#555;color:#fff}
.tb-fp.old .tb-tx{text-decoration:line-through;text-decoration-color:__SECOND__;text-decoration-thickness:7px}
.tb-fp.new{background:__ACCENT__;color:#111;box-shadow:12px 12px 0 __SECOND__}
.tb-fp.new .tb-fptag{background:#000;color:#fff}
.scene.active .tb-fp{animation:tbrise .5s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:var(--d,0s)}
.scene.active .tb-fp.new{animation-delay:.22s}
/* bullets · torn: torn-paper strips */
.tb-tornwrap{display:flex;flex-direction:column;gap:26px}
.tb-torn{display:flex;align-items:center;gap:28px;background:#fff;color:#111;font-size:74px;font-weight:900;
  padding:26px 40px;opacity:0;transform:translateX(-26px);
  clip-path:polygon(0 6%,4% 0,12% 7%,22% 1%,34% 8%,48% 2%,62% 9%,76% 2%,88% 8%,96% 1%,100% 7%,100% 94%,95% 100%,84% 93%,72% 100%,58% 92%,44% 100%,30% 93%,18% 100%,8% 93%,0 99%)}
.scene.active .tb-torn{animation:tbslide .5s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:var(--d)}
.tb-torn .tb-tn{flex:none;background:__ACCENT__;color:#111;font-size:48px;min-width:70px;height:70px;
  display:flex;align-items:center;justify-content:center;border:4px solid #000}
.tb-torn .tb-tt{line-height:1.16}
/* bullets · scatter: sticker labels, varied size + tilt */
.scene.tb.bul.scatter{justify-content:center}
.tb-scatter{display:flex;flex-wrap:wrap;gap:30px 26px;align-content:center;max-width:960px}
.tb-sticklbl{display:flex;align-items:center;gap:20px;font-size:70px;font-weight:900;color:#111;
  padding:22px 38px;border:5px solid #000;box-shadow:9px 9px 0 rgba(0,0,0,.5);
  transform:rotate(var(--rot)) scale(.9);opacity:0}
.tb-sticklbl.s0{background:__ACCENT__}.tb-sticklbl.s1{background:#fff}.tb-sticklbl.s2{background:__SECOND__}
.scene.active .tb-sticklbl{animation:tbpop .5s cubic-bezier(.2,.8,.4,1.3) forwards;animation-delay:var(--d)}
.tb-sticklbl .tb-sn{background:#000;color:#fff;font-size:44px;min-width:62px;height:62px;
  display:flex;align-items:center;justify-content:center}
/* outro · stamp: 完 stamp slammed over the lines */
.tb-stamp{position:absolute;top:52%;left:50%;transform:translate(-50%,-50%) rotate(-16deg);
  font-size:420px;font-weight:900;color:transparent;-webkit-text-stroke:14px __SECOND__;
  opacity:0;z-index:5}
.scene.active .tb-stamp{animation:tbstamp .5s cubic-bezier(.4,1.6,.5,1) forwards .35s}
@keyframes tbstamp{0%{opacity:0;transform:translate(-50%,-50%) rotate(-16deg) scale(2.4)}
  100%{opacity:.92;transform:translate(-50%,-50%) rotate(-16deg) scale(1)}}
/* outro · tail: thick framed closing */
.tb-tailbox{border:12px solid __ACCENT__;padding:70px 60px;box-shadow:16px 16px 0 rgba(0,0,0,.55);
  background:rgba(0,0,0,.35)}
.tb-taill{font-weight:900;line-height:1.12;color:#fff;margin:8px 0;opacity:0;transform:translateY(22px)}
.scene.active .tb-taill{animation:tbrise .5s cubic-bezier(.2,.8,.2,1) forwards;animation-delay:var(--d)}
@keyframes tbslideR{to{opacity:1;transform:none}}
@keyframes tbf{to{opacity:1;transform:none}}
@keyframes tbrise{to{opacity:1;transform:none}}
@keyframes tbslide{to{opacity:1;transform:none}}
@keyframes tbpop{to{opacity:1;transform:none}}
@keyframes tbskew{to{opacity:1;transform:skewX(__SKEW__deg)}}
/* cover: first scene fully composed */
.scene.tb:first-of-type .tb-l1,.scene.tb:first-of-type .tb-l2,
.scene.tb:first-of-type .tb-banner,.scene.tb:first-of-type .tb-taill{opacity:1;transform:none;animation:none}
.scene.tb:first-of-type .tb-l2.skew{transform:skewX(__SKEW__deg);animation:none}
.scene.tb:first-of-type .tb-eyebrow{opacity:1;transform:rotate(-2deg);animation:none}
.scene.tb:first-of-type .tb-hrule{width:560px;animation:none}
.scene.tb:first-of-type .tb-stamp{opacity:.92;transform:translate(-50%,-50%) rotate(-16deg);animation:none}
"""
