#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_terminal — C · 终端/IDE (GitHub-dark, mono, code blocks, command line).

On-brand for an AI-coding account: the WHOLE frame is one live terminal window
(titlebar + line-number gutter + scanlines + status bar), every text card is
framed as command output (a dim pseudo-prompt above it), and oversized ghost
ASCII glyphs / stroked ghost numbers fill what used to be dead space.
variant() rotates the accent, filename, pseudo path, and a layout per type.
"""
from .base import Style, esc, big_fs, highlight, blob, scene_types, rgba

_ACCENTS = ["#7ee787", "#79c0ff", "#d2a8ff", "#ffa657", "#56d4dd"]
_FILES = ["openai_chips.ts", "today.py", "ai_news.md", "notes.rs", "ship.go"]
# neutral pseudo paths for the window titlebar — no usernames, no branding
_PATHS = ["~/notes/today", "~/dev/scratch", "~/work/draft.md", "~/inbox/read.md"]


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
        # per-type layout pools — every text-card type has >=3 visibly
        # different compositions, all chosen from the per-video rng
        return {
            "accent": rng.choice(_ACCENTS),
            "file": rng.choice(_FILES),
            "path": rng.choice(_PATHS),
            "hook": rng.choice(["prompt", "comment", "tab", "man", "boot"]),
            "stat": rng.choice(["diff", "stdout", "neon", "bar"]),
            "bullets": rng.choice(["checklist", "stdout", "tree", "panes"]),
            "compare": rng.choice(["diff", "cols", "exit"]),
            "outro": rng.choice(["commit", "shutdown", "pass"]),
        }

    def css(self, ctx):
        return _fill(_CSS, {
            "__ACCENT__": ctx["accent"],
            "__GLOW__": rgba(ctx["accent"], 0.12),
            "__GHOST__": rgba(ctx["accent"], 0.07),
            "__GSTROKE__": rgba(ctx["accent"], 0.16),
        })

    def background(self, ctx):
        # structural terminal-window furniture (NOT branding): titlebar with
        # traffic lights + a neutral pseudo path, a dim line-number gutter,
        # faint scanlines, and a neutral status bar. Fills the dead space that
        # made text cards read as unfinished PPT (2026-07-19 review).
        nums = "".join(f"<span>{n}</span>" for n in range(1, 41))
        return ('<div class="tm-bg">'
                '<div class="tm-scan"></div>'
                '<div class="tm-titlebar">'
                '<span class="d r"></span><span class="d y"></span><span class="d g"></span>'
                f'<span class="tm-path">{esc(ctx.get("path", "~/notes/today"))}</span>'
                '<span class="tm-winlab">bash</span></div>'
                f'<div class="tm-gutter">{nums}</div>'
                '<div class="tm-statusbar"><span class="tm-mode">-- INSERT --</span>'
                '<span class="tm-sep">·</span><span>UTF-8</span>'
                '<span class="tm-sep">·</span><span>LF</span>'
                '<span class="tm-fillsp"></span><span>ln 12, col 3</span></div>'
                '</div>')

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
        return (f'<section class="scene tm" data-i="{i}">'
                f'<div class="tm-ghost">&gt;</div>'
                f'<div class="tm-pp">$ echo</div><div class="tm-cmt">// {body}</div></section>')

    def _hook(self, i, sc, ctx):
        lines = sc.get("lines", []) or [sc.get("say", "")]
        fs = big_fs(lines, base=148)
        head = "".join(f'<div class="tm-h" style="--d:{0.10*j:.2f}s;font-size:{fs}px">{esc(x)}</div>'
                       for j, x in enumerate(lines))
        eb = esc(sc.get("eyebrow", "")) or "今日头条"
        mode = ctx["hook"]
        if mode == "man":
            # man-page composition: NAME/SYNOPSIS structure, headline indented
            return (f'<section class="scene tm hook man" data-i="{i}">'
                    f'<div class="tm-ghost">&gt;</div>'
                    f'<div class="tm-manrow"><span>TODAY(1)</span>'
                    f'<span>User Commands</span><span>TODAY(1)</span></div>'
                    f'<div class="tm-mansec">NAME</div>'
                    f'<div class="tm-manname">today — {eb}</div>'
                    f'<div class="tm-mansec">SYNOPSIS</div>'
                    f'<div class="tm-head man-ind">{head}</div>'
                    f'<div class="tm-mansec">SEE ALSO</div>'
                    f'<div class="tm-manname">watch(1), read(2)</div></section>')
        if mode == "boot":
            # boot-splash composition: framed headline box + [ OK ] boot lines
            return (f'<section class="scene tm hook boot" data-i="{i}">'
                    f'<div class="tm-ghost">&gt;</div>'
                    f'<div class="tm-bootbox"><div class="tm-bootlab">{eb}</div>'
                    f'<div class="tm-head">{head}</div></div>'
                    f'<div class="tm-bootseq">'
                    f'<div class="tm-bootline" style="--d:.15s">[ <span class="ok">OK</span> ] mounted /topic</div>'
                    f'<div class="tm-bootline" style="--d:.32s">[ <span class="ok">OK</span> ] loaded 3 modules</div>'
                    f'<div class="tm-bootver">tty1 · boot v2.6 · press any key to continue</div>'
                    f'</div></section>')
        if mode == "comment":
            top = (f'<div class="tm-pp">$ cat hook.md</div>'
                   f'<div class="tm-banner">/* {eb} */</div>')
        elif mode == "tab":
            top = (f'<div class="tm-tabbar"><span class="d r"></span><span class="d y"></span><span class="d g"></span>'
                   f'<span class="tm-tab">{esc(ctx["file"])}</span></div>'
                   f'<div class="tm-eb"># {eb}</div>')
        else:
            top = (f'<div class="tm-prompt">$ cat hook.md<span class="cur"></span></div>'
                   f'<div class="tm-eb"># {eb}</div>')
        return (f'<section class="scene tm hook" data-i="{i}">'
                f'<div class="tm-ghost">&gt;</div>'
                f'{top}<div class="tm-head">{head}</div></section>')

    def _outro(self, i, sc, ctx):
        lines = sc.get("lines", []) or [sc.get("say", "")]
        fs = big_fs(lines, base=118)
        head = "".join(f'<div class="tm-h" style="--d:{0.10*j:.2f}s;font-size:{fs}px">{esc(x)}</div>'
                       for j, x in enumerate(lines))
        mode = ctx["outro"]
        if mode == "shutdown":
            # logout sequence: headline, then the session winds down line by line
            return (f'<section class="scene tm outro" data-i="{i}">'
                    f'<div class="tm-ghost bottom">_</div>'
                    f'<div class="tm-prompt">$ logout<span class="cur"></span></div>'
                    f'<div class="tm-head">{head}</div>'
                    f'<div class="tm-shseq">'
                    f'<div class="tm-shline" style="--d:.25s">Saving session... done</div>'
                    f'<div class="tm-shline" style="--d:.50s">Connection closed.</div>'
                    f'<div class="tm-shline" style="--d:.75s">[ process completed ]</div>'
                    f'</div></section>')
        if mode == "pass":
            # test-suite-all-green composition: dots, headline, PASSED rule
            return (f'<section class="scene tm outro" data-i="{i}">'
                    f'<div class="tm-ghost bottom">✓</div>'
                    f'<div class="tm-pp">$ pytest -q</div>'
                    f'<div class="tm-passdots">.........</div>'
                    f'<div class="tm-head">{head}</div>'
                    f'<div class="tm-passbar">═════ all checks PASSED ═════</div></section>')
        return (f'<section class="scene tm outro" data-i="{i}">'
                f'<div class="tm-ghost bottom">_</div>'
                f'<div class="tm-prompt">$ git commit -m<span class="cur"></span></div>'
                f'<div class="tm-head">{head}</div></section>')

    def _stat(self, i, sc, ctx):
        val, unit, label = esc(sc.get("value", "")), esc(sc.get("unit", "")), esc(sc.get("label", ""))
        m = ctx["stat"]
        ghost = f'<div class="tm-ghostnum">{val}</div>'
        if m == "diff":
            return (f'<section class="scene tm stat" data-i="{i}">{ghost}'
                    f'<div class="tm-pp">$ git diff --stat</div>'
                    f'<div class="tm-difflines">'
                    f'<div class="tm-d minus">- 老办法</div>'
                    f'<div class="tm-d plus">+ {label} <span class="tm-big">{val}{unit}</span></div></div></section>')
        if m == "bar":
            # htop/meter composition: label + big value + ASCII progress bar
            raw = str(sc.get("value", ""))
            num = "".join(ch for ch in raw if ch.isdigit() or ch == ".")
            try:
                v = float(num)
            except ValueError:
                v = 70.0
            frac = v / 100.0 if (("%" in raw or "％" in raw) and 0 < v <= 100) else 0.72
            cells = 18
            fill = max(1, min(cells, round(frac * cells)))
            bar = ('<span class="bf">' + "█" * fill + '</span>'
                   '<span class="be">' + "░" * (cells - fill) + '</span>')
            return (f'<section class="scene tm stat" data-i="{i}">{ghost}'
                    f'<div class="tm-pp">$ top -n 1</div>'
                    f'<div class="tm-meter"><div class="tm-mlab">{label}</div>'
                    f'<div class="tm-mval">{val}<span class="su">{unit}</span></div>'
                    f'<div class="tm-mbar">[{bar}]</div></div></section>')
        if m == "stdout":
            return (f'<section class="scene tm stat" data-i="{i}">{ghost}'
                    f'<div class="tm-prompt">$ cat stats.log<span class="cur"></span></div>'
                    f'<div class="tm-out">&gt;&gt; {label}: <span class="tm-big">{val}{unit}</span></div></section>')
        return (f'<section class="scene tm stat neon" data-i="{i}">{ghost}'
                f'<div class="tm-pp">$ echo $RESULT</div>'
                f'<div class="tm-neon">{val}<span class="su">{unit}</span></div>'
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
        before, after = esc(sc.get("before", "")), esc(sc.get("after", ""))
        mode = ctx["compare"]
        if mode == "cols":
            # diff -u two-panel composition: red old panel vs green new panel
            return (f'<section class="scene tm cmp" data-i="{i}">'
                    f'<div class="tm-ghost">$</div>'
                    f'<div class="tm-pp">$ diff -u old new</div>'
                    f'<div class="tm-cols">'
                    f'<div class="tm-col minusc"><div class="tm-colhead">--- a/old</div>'
                    f'<div class="tm-coltext">{before}</div></div>'
                    f'<div class="tm-col plusc"><div class="tm-colhead">+++ b/new</div>'
                    f'<div class="tm-coltext">{after}</div></div></div></section>')
        if mode == "exit":
            # exit-code composition: red error block -> green pass block
            return (f'<section class="scene tm cmp" data-i="{i}">'
                    f'<div class="tm-ghost">!</div>'
                    f'<div class="tm-pp">$ ./run.sh</div>'
                    f'<div class="tm-ex bad"><div class="tm-exhead">✗ 报错</div>'
                    f'<div class="tm-extext">{before}</div>'
                    f'<div class="tm-excode">exit 1</div></div>'
                    f'<div class="tm-exarr">↓ 修复</div>'
                    f'<div class="tm-ex good"><div class="tm-exhead">✓ 通过</div>'
                    f'<div class="tm-extext">{after}</div>'
                    f'<div class="tm-excode">exit 0</div></div></section>')
        return (f'<section class="scene tm cmp" data-i="{i}">'
                f'<div class="tm-ghost">$</div>'
                f'<div class="tm-pp">$ git diff</div>'
                f'<div class="tm-win">'
                f'<div class="tm-winbar"><span class="d r"></span><span class="d y"></span><span class="d g"></span>'
                f'<span class="tm-tab">diff</span></div>'
                f'<div class="tm-codebody"><div class="tm-cl minus"><span class="tm-ln">-</span><span class="tm-ct">{esc(sc.get("before",""))}</span></div>'
                f'<div class="tm-cl plus"><span class="tm-ln">+</span><span class="tm-ct">{esc(sc.get("after",""))}</span></div></div></div></section>')

    def _bullets(self, i, sc, ctx):
        head = f'<div class="tm-bhead"># {esc(sc["head"])}</div>' if sc.get("head") else ""
        rows = sc.get("lines", [])
        mode = ctx["bullets"]
        if mode == "tree":
            # tree-command composition: head is the root dir, items branch off
            root = esc(sc.get("head", "")) or "notes/"
            items = "".join(
                f'<div class="tm-li" style="--d:{0.12*j:.2f}s">'
                f'<span class="tm-treepre">{"└── " if j == len(rows) - 1 else "├── "}</span>'
                f'<span class="tm-lt">{esc(x)}</span></div>' for j, x in enumerate(rows))
            return (f'<section class="scene tm bul" data-i="{i}">'
                    f'<div class="tm-ghost">#</div>'
                    f'<div class="tm-pp">$ tree . -L 1</div>'
                    f'<div class="tm-troot">{root}</div>'
                    f'<div class="tm-list tree">{items}</div></section>')
        if mode == "panes":
            # tmux-split composition: every item lives in its own pane frame
            panes = "".join(
                f'<div class="tm-pane" style="--d:{0.14*j:.2f}s">'
                f'<span class="tm-panetag">{j}</span>'
                f'<span class="tm-lt">{esc(x)}</span></div>' for j, x in enumerate(rows))
            return (f'<section class="scene tm bul" data-i="{i}">'
                    f'<div class="tm-ghost">#</div>'
                    f'<div class="tm-pp">$ tmux attach</div>'
                    f'{head}<div class="tm-panes">{panes}</div></section>')
        if mode == "checklist":
            pp = '<div class="tm-pp">$ cat todo.md</div>'
            items = "".join(f'<div class="tm-li" style="--d:{0.12*j:.2f}s"><span class="tm-box">[<span class="tm-x">x</span>]</span>'
                            f'<span class="tm-lt">{esc(x)}</span></div>' for j, x in enumerate(rows))
        else:
            pp = '<div class="tm-pp">$ ls -1 notes/</div>'
            items = "".join(f'<div class="tm-li" style="--d:{0.12*j:.2f}s"><span class="tm-box">&gt;</span>'
                            f'<span class="tm-lt">{esc(x)}</span></div>' for j, x in enumerate(rows))
        return (f'<section class="scene tm bul" data-i="{i}">'
                f'<div class="tm-ghost">#</div>'
                f'{pp}{head}<div class="tm-list">{items}</div></section>')


_CSS = r"""
html,body{background:#0b0f17;font-family:"Noto Sans Mono CJK SC","DejaVu Sans Mono",monospace;color:#c9d1d9}
.bar{background:__ACCENT__;height:8px;box-shadow:0 0 16px __ACCENT__}
.scene.tm{padding:0 78px 0 104px}
.d{width:18px;height:18px;border-radius:50%;display:inline-block}.r{background:#ff5f56}.y{background:#ffbd2e}.g{background:#27c93f}
/* full-frame terminal window furniture (background layer, every scene) */
.tm-bg{position:absolute;inset:0;z-index:0;pointer-events:none}
.tm-scan{position:absolute;inset:0;
  background:repeating-linear-gradient(0deg,rgba(255,255,255,.016) 0 2px,transparent 2px 6px)}
.tm-titlebar{position:absolute;top:0;left:0;right:0;height:88px;display:flex;align-items:center;
  gap:11px;padding:0 34px;background:#10151d;border-bottom:1px solid #20262f}
.tm-path{margin-left:18px;color:#8b949e;font-size:30px}
.tm-winlab{margin-left:auto;color:#3d444d;font-size:26px}
.tm-gutter{position:absolute;top:112px;bottom:160px;left:20px;width:52px;overflow:hidden;
  font-size:24px;line-height:46px;text-align:right;color:#252c37}
.tm-gutter span{display:block}
.tm-statusbar{position:absolute;left:0;right:0;bottom:8px;height:56px;display:flex;align-items:center;
  gap:18px;padding:0 34px;background:#10151d;border-top:1px solid #20262f;font-size:26px;color:#57606a}
.tm-mode{color:__ACCENT__;opacity:.85}.tm-sep{color:#3d444d}.tm-fillsp{margin-left:auto}
/* ghost glyphs: oversized ASCII ornaments that fill the dead space */
.tm-ghost{position:absolute;top:100px;right:6px;font-size:820px;line-height:1;font-weight:700;
  color:__GHOST__;pointer-events:none}
.tm-ghost.bottom{top:auto;bottom:30px}
.tm-ghostnum{position:absolute;top:170px;right:30px;font-family:"Noto Sans CJK SC",sans-serif;
  font-size:500px;line-height:1;font-weight:900;color:transparent;
  -webkit-text-stroke:3px __GSTROKE__;letter-spacing:-10px;pointer-events:none}
/* subtitles: terminal skin (deep plate + accent left bar; white+stroke from base) */
.sub{background:rgba(13,17,23,.9);border-radius:8px;
  border-left:12px solid __ACCENT__;padding:6px 30px 10px 26px}
/* media fit canvas: dark base + faint scanlines + accent glow instead of black blur */
.media-canvas{background:
  repeating-linear-gradient(0deg,rgba(255,255,255,.014) 0 2px,transparent 2px 6px),
  radial-gradient(90% 60% at 50% 34%,__GLOW__,transparent 70%),
  linear-gradient(180deg,#0d1117,#0b0f17)}
.media-fit,.media-fitpos{border-radius:14px}
/* pseudo-prompt: dim command line that frames each card as terminal output */
.tm-pp{font-size:34px;color:#7d8590;opacity:.8;margin-bottom:26px}
.tm-eb{font-size:36px;color:__ACCENT__;opacity:.85;letter-spacing:3px;margin-bottom:24px}
/* hook */
.tm-prompt{font-size:46px;color:#e6edf3;margin-bottom:30px}
.cur{display:inline-block;width:20px;height:38px;background:__ACCENT__;vertical-align:-6px;margin-left:8px;animation:bl 1s steps(1) infinite}
.tm-banner{font-size:42px;color:#8b949e;font-style:italic;margin-bottom:26px}
.tm-tabbar{display:inline-flex;align-items:center;gap:11px;background:#161b22;border:1px solid #20262f;
  border-radius:12px;padding:16px 26px;margin-bottom:26px;align-self:flex-start}
.tm-tabbar .tm-tab{margin-left:14px;color:#e6edf3;font-size:30px}
.tm-head{position:relative}
.tm-h{font-family:"Noto Sans CJK SC",sans-serif;font-weight:900;line-height:1.12;color:#e6edf3;opacity:0;transform:translateY(20px)}
.scene.active .tm-h{animation:tmrise .6s cubic-bezier(.2,.7,.2,1) forwards;animation-delay:var(--d)}
.tm-h:last-of-type{color:__ACCENT__}
/* hook: man-page layout */
.tm-manrow{display:flex;justify-content:space-between;font-size:32px;color:#57606a;margin-bottom:36px;opacity:0}
.scene.active .tm-manrow{animation:tmf .5s ease forwards}
.tm-mansec{font-size:34px;letter-spacing:6px;color:__ACCENT__;margin:32px 0 14px;opacity:0}
.scene.active .tm-mansec{animation:tmf .5s ease forwards .1s}
.tm-manname{font-size:44px;color:#8b949e;padding-left:48px;opacity:0}
.scene.active .tm-manname{animation:tmf .5s ease forwards .18s}
.tm-head.man-ind{padding-left:48px;margin-top:8px}
/* hook: boot-splash layout */
.tm-bootbox{position:relative;border:3px solid #30363d;border-radius:18px;padding:60px 46px 50px;
  box-shadow:inset 0 0 70px rgba(0,0,0,.4);opacity:0;transform:translateY(20px)}
.scene.active .tm-bootbox{animation:tmrise .6s cubic-bezier(.2,.7,.2,1) forwards}
.tm-bootlab{position:absolute;top:-26px;left:38px;background:#0b0f17;padding:0 18px;
  font-size:34px;color:__ACCENT__;letter-spacing:4px}
.tm-bootseq{margin-top:46px;font-size:34px;line-height:1.9;color:#57606a}
.tm-bootline{opacity:0}.scene.active .tm-bootline{animation:tmf .4s ease forwards;animation-delay:var(--d)}
.tm-bootline .ok{color:#7ee787}
.tm-bootver{margin-top:12px;font-size:28px;color:#3d444d;opacity:0}
.scene.active .tm-bootver{animation:tmf .4s ease forwards .55s}
/* stat */
.tm-difflines{font-size:78px;font-weight:700}
.tm-d{padding:20px 32px;border-radius:10px;opacity:0;transform:translateX(-26px)}
.scene.active .tm-d{animation:tmslide .55s cubic-bezier(.2,.7,.2,1) forwards}
.tm-d.minus{color:#8b949e;background:rgba(248,81,73,.10);text-decoration:line-through}
.tm-d.plus{color:#7ee787;background:rgba(63,185,80,.12);margin-top:20px}.scene.active .tm-d.plus{animation-delay:.2s}
.tm-big{font-weight:900}
.tm-out{font-size:72px;color:#c9d1d9;margin-top:10px}.tm-out .tm-big{color:__ACCENT__;font-weight:900;font-size:112px}
.tm-neon{font-family:"Noto Sans CJK SC",sans-serif;font-weight:900;font-size:360px;line-height:.92;color:__ACCENT__;
  text-shadow:0 0 50px __ACCENT__;opacity:0;transform:translateY(24px)}
.scene.active .tm-neon{animation:tmrise .8s cubic-bezier(.2,.8,.2,1) forwards}
.tm-neon .su{font-size:150px}
.tm-cmt{font-size:56px;color:#8b949e;line-height:1.55;max-width:920px;margin-top:16px}
/* stat: htop/meter layout */
.tm-meter{opacity:0;transform:translateY(22px)}
.scene.active .tm-meter{animation:tmrise .6s cubic-bezier(.2,.7,.2,1) forwards}
.tm-mlab{font-size:56px;color:#8b949e;margin-bottom:10px}
.tm-mval{font-family:"Noto Sans CJK SC",sans-serif;font-weight:900;font-size:220px;line-height:1;color:__ACCENT__}
.tm-mval .su{font-size:96px}
.tm-mbar{font-size:58px;margin-top:28px;color:#3d444d;letter-spacing:2px}
.tm-mbar .bf{color:__ACCENT__;text-shadow:0 0 24px __GLOW__}
.tm-mbar .be{color:#242b36}
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
/* compare rows read as a headline diff, not source code */
.cmp .tm-codebody{font-size:64px;line-height:1.4}
.cmp .tm-cl{white-space:normal;padding:16px 8px}.cmp .tm-ct{white-space:normal}
/* compare: diff -u two-panel layout */
.tm-cols{display:grid;grid-template-columns:1fr 1fr;gap:30px}
.tm-col{border-radius:16px;padding:38px 32px;min-height:420px;opacity:0}
.tm-col.minusc{background:rgba(248,81,73,.10);border:2px solid rgba(248,81,73,.45);transform:translateX(-30px)}
.tm-col.plusc{background:rgba(63,185,80,.10);border:2px solid rgba(63,185,80,.45);transform:translateX(30px)}
.scene.active .tm-col{animation:tmslide .55s cubic-bezier(.2,.7,.2,1) forwards}
.scene.active .tm-col.plusc{animation-delay:.18s}
.tm-colhead{font-size:36px;margin-bottom:28px}
.minusc .tm-colhead{color:#f8a39d}.plusc .tm-colhead{color:#7ee787}
.tm-coltext{font-family:"Noto Sans CJK SC",sans-serif;font-size:56px;line-height:1.5;color:#e6edf3;font-weight:700}
/* compare: exit-code layout (error block -> pass block) */
.tm-ex{border-radius:18px;padding:40px 44px;opacity:0;transform:translateY(22px)}
.scene.active .tm-ex{animation:tmrise .55s cubic-bezier(.2,.7,.2,1) forwards}
.tm-ex.bad{background:rgba(248,81,73,.12);border-left:12px solid #f85149}
.tm-ex.good{background:rgba(63,185,80,.12);border-left:12px solid #3fb950}
.scene.active .tm-ex.good{animation-delay:.35s}
.tm-exhead{font-size:40px;font-weight:700;margin-bottom:18px}
.bad .tm-exhead{color:#f8a39d}.good .tm-exhead{color:#7ee787}
.tm-extext{font-family:"Noto Sans CJK SC",sans-serif;font-size:60px;font-weight:700;line-height:1.45;color:#e6edf3}
.tm-excode{margin-top:20px;font-size:32px;color:#57606a;text-align:right}
.tm-exarr{font-size:44px;color:__ACCENT__;margin:26px 0 26px 20px;opacity:0}
.scene.active .tm-exarr{animation:tmf .4s ease forwards .22s}
/* bullets */
.tm-bhead{font-size:62px;color:#e6edf3;font-weight:700;margin-bottom:44px;opacity:0}.scene.active .tm-bhead{animation:tmf .5s ease forwards}
.tm-list{display:flex;flex-direction:column;gap:40px}
.tm-li{display:flex;align-items:center;gap:26px;font-size:74px;opacity:0;transform:translateX(-20px)}
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
