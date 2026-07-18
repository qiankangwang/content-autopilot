#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Rich motion-graphics 抖音 builder (1080x1920) — ONE command, INSIDE the container.

This is the canonical 抖音 video pipeline. Visuals are information-dense animated
"keynote" graphics — syntax-highlighted code cards, before/after compares,
big-number stats, kinetic bullet beats — NOT a static gradient slideshow (a flat
text-on-gradient slideshow read by a robotic TTS voice looks low-effort and
obviously AI-made). Narration is a natural neural voice (豆包/火山 **vivi**) via
volc_tts.py. Audio and slides are auto-synced: each scene is voiced separately so
its on-screen duration matches its real spoken length.

Pipeline (all automatic):
  spec.json  ->  per-scene vivi TTS (volc_tts.py)  ->  per-scene duration
             ->  HTML/CSS motion graphics rendered via Playwright (Chromium)
             ->  ffmpeg: transcode + mux voice  ->  1080x1920 H.264/AAC mp4

spec JSON:
{
  "tag": "AI编程",                 # accent pill, top-left (optional)
  "theme": "dark",                  # "dark" | "light"
  "accent": "#FF2E4D",              # accent color
  "handle": "@yourhandle",          # bottom-left handle (default @yourhandle)
  "scenes": [
    # every scene SHOULD carry "say" = the spoken narration for that beat.
    {"type": "hook",   "say": "...", "eyebrow": "AI编程", "lines": ["写完功能","最烦写测试"]},
    {"type": "stat",   "say": "...", "value": "70%", "label": "测试初稿 AI 来写"},
    {"type": "code",   "say": "...", "lang": "python", "caption": "3秒出骨架",
                        "code": "def test_pay():\n    assert pay(100) == 100  # 正常"},
    {"type": "compare","say": "...", "before": "手写测试 · 1.5天", "after": "AI起草 · 10分钟"},
    {"type": "bullets","say": "...", "lines": ["读 AI 漏的边界","补真实 case","改断言"]},
    {"type": "outro",  "say": "...", "lines": ["省下的时间","拿去啃硬逻辑"]}   # content-only close, NO 关注/点赞 CTA
  ]
}

Usage (inside the agent container):
  python make_rich_video.py --spec spec.json --out /root/hermes-content/douyin/<date>-<topic>.mp4
  # voice creds come from /root/.config/volc_tts.json (volc_tts.py handles it)
  # override voice:  --voice zh_female_vv_uranus_bigtts   (default = vivi)
"""
import argparse
import glob
import html
import json
import os
import re
import subprocess
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))

W, H = 1080, 1920
PAD = 0.28          # silence/breath appended after each scene (s)
MIN_DUR = 1.8       # floor for a scene with no/short audio
DEFAULT_VOICE = os.getenv("VOLC_TTS_VOICE", "zh_female_vv_uranus_bigtts")
COVER_HOLD = 0.35   # s to hold a clean cover frame over the recorder's broken first frames

# follow/like/收藏 CTAs — design choice: content-only close, never a 关注 CTA
# (a hard-sell "follow me / like / 三连" close reads as spam and hurts retention)
_CTA_RE = re.compile(
    r"(关注我|关注一下|点关注|求关注|关注\s*[@＠]|一键三连|三连|点赞|点个赞|求赞|"
    r"记得收藏|收藏一下|转发一下|订阅一下|订阅频道|follow\s*me|please\s*subscribe|hit\s*subscribe)",
    re.I,
)


def _scrub_cta(say):
    """Drop whole sentences that are follow/like/三连 CTAs, keep the real content."""
    if not say:
        return say
    parts = re.split(r"(?<=[。！？!?\n])", say)
    kept = [p for p in parts if p.strip() and not _CTA_RE.search(p)]
    return "".join(kept).strip()


# ----------------------------------------------------------------------------- TTS + timing
def _ffprobe_dur(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", path],
        capture_output=True, text=True,
    )
    try:
        return float(out.stdout.strip())
    except (TypeError, ValueError):
        return 0.0


def _tts_scene(say, out_mp3, voice, speed, provider="volc", fish_model="s1"):
    """Synthesize one scene's narration (volc/vivi or Fish Audio). Returns ok bool."""
    say = (say or "").strip()
    if not say:
        return False
    if provider == "fish":
        cmd = [sys.executable, os.path.join(_HERE, "fish_tts.py"),
               "--text", say, "--out", out_mp3, "--model", fish_model, "--speed", str(speed)]
        if voice:
            cmd += ["--voice", voice]
    else:
        cmd = [sys.executable, os.path.join(_HERE, "volc_tts.py"),
               "--text", say, "--out", out_mp3, "--voice", voice, "--speed", str(speed)]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0 or not os.path.exists(out_mp3):
        sys.stderr.write(f"[rich] {provider}_tts failed for scene: {r.stderr[:300]}\n")
        return False
    return True


def _silence(out_mp3, seconds):
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
         "-t", f"{seconds:.3f}", "-c:a", "libmp3lame", "-q:a", "6", out_mp3],
        capture_output=True, text=True, check=True,
    )


def build_audio(scenes, workdir, voice, speed, provider="volc", fish_model="s1"):
    """Voice each scene; return (concat_mp3_path, [per_scene_duration_incl_pad])."""
    parts, durs = [], []
    sil = os.path.join(workdir, "_sil.mp3")
    _silence(sil, PAD)
    for i, sc in enumerate(scenes):
        seg = os.path.join(workdir, f"_a{i}.mp3")
        if _tts_scene(_scrub_cta(sc.get("say", "")), seg, voice, speed, provider, fish_model):
            d = _ffprobe_dur(seg)
            parts.append(seg)
        else:                                   # no narration -> hold on a silent beat
            d = max(MIN_DUR - PAD, 0.6)
            seg2 = os.path.join(workdir, f"_a{i}.mp3")
            _silence(seg2, d)
            parts.append(seg2)
        parts.append(sil)
        durs.append(round(d + PAD, 3))
    # concat (re-encode for clean timestamps)
    listf = os.path.join(workdir, "_concat.txt")
    with open(listf, "w", encoding="utf-8") as f:
        for p in parts:
            f.write(f"file '{p}'\n")
    voice_mp3 = os.path.join(workdir, "_voice.mp3")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", listf,
         "-c:a", "libmp3lame", "-q:a", "4", voice_mp3],
        capture_output=True, text=True, check=True,
    )
    return voice_mp3, durs


# ----------------------------------------------------------------------------- code highlighter
_KW = {
    "python": r"\b(def|return|if|elif|else|for|while|in|not|and|or|is|None|True|False|"
              r"import|from|as|class|with|try|except|finally|raise|assert|lambda|yield|async|await|pass)\b",
    "js": r"\b(const|let|var|function|return|if|else|for|while|of|in|new|class|extends|"
          r"async|await|try|catch|finally|throw|import|from|export|default|null|true|false|this)\b",
    "ts": r"\b(const|let|var|function|return|if|else|for|while|of|in|new|class|extends|interface|type|"
          r"async|await|try|catch|finally|throw|import|from|export|default|null|true|false|this)\b",
    "bash": r"\b(if|then|else|fi|for|in|do|done|while|case|esac|function|echo|export|cd|return)\b",
}


def highlight(code, lang):
    lang = (lang or "python").lower()
    kw = _KW.get(lang, _KW["python"])
    cmt = "#" if lang in ("python", "bash") else "//"
    out_lines = []
    for raw in code.split("\n"):
        # split off a trailing line comment (naive but fine for short snippets)
        comment = ""
        ci = raw.find(cmt)
        # avoid matching # inside a string crudely: only treat as comment if not within quotes
        if ci != -1 and raw.count("'", 0, ci) % 2 == 0 and raw.count('"', 0, ci) % 2 == 0:
            comment = raw[ci:]
            raw = raw[:ci]
        toks = []
        pattern = re.compile(
            r"(?P<str>'[^']*'|\"[^\"]*\")"
            r"|(?P<dec>@[\w.]+)"
            r"|(?P<kw>" + kw + r")"
            r"|(?P<fn>[A-Za-z_]\w*)(?=\s*\()"
            r"|(?P<num>\b\d+\.?\d*\b)"
            r"|(?P<id>[A-Za-z_一-鿿]\w*)"
            r"|(?P<ws>\s+)"
            r"|(?P<other>.)"
        )
        for m in pattern.finditer(raw):
            kind = m.lastgroup
            text = html.escape(m.group())
            if kind in ("ws", "other", "id"):
                toks.append(text)
            else:
                toks.append(f'<span class="t-{kind}">{text}</span>')
        if comment:
            toks.append(f'<span class="t-cmt">{html.escape(comment)}</span>')
        out_lines.append("".join(toks) if toks else "&nbsp;")
    return out_lines


# ----------------------------------------------------------------------------- HTML scenes
def esc(s):
    return html.escape(str(s))


def _big_fs(lines):
    """Responsive font-size for big kinetic text so long CJK lines don't wrap ugly.
    Content width ~888px; ~font-size px per CJK glyph at weight 900."""
    m = max((len(str(x)) for x in lines if x), default=4)
    if m <= 5:
        return 128
    return {6: 118, 7: 104, 8: 92, 9: 82, 10: 74}.get(m, 66)


def _big_lines(lines):
    fs = _big_fs(lines)
    return "".join(
        f'<div class="big" style="--d:{0.10*j:.2f}s;font-size:{fs}px">{esc(x)}</div>'
        for j, x in enumerate(lines)
    )


def scene_html(i, sc):
    t = sc.get("type", "point")
    if t == "hook":
        eb = f'<div class="eyebrow">{esc(sc["eyebrow"])}</div>' if sc.get("eyebrow") else ""
        lines = _big_lines(sc.get("lines", []))
        return f'<section class="scene hook" data-i="{i}">{eb}<div class="biglines">{lines}<div class="accentbar"></div></div></section>'

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
            for j, ln in enumerate(lines)
        )
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
            for j, x in enumerate(sc.get("lines", []))
        )
        head = f'<div class="bhead">{esc(sc["head"])}</div>' if sc.get("head") else ""
        return f'<section class="scene bullets" data-i="{i}">{head}<div class="blist">{items}</div></section>'

    if t == "outro":
        # content-only close — never render a 关注/点赞 CTA pill
        lines = _big_lines(sc.get("lines", []))
        return f'<section class="scene outro" data-i="{i}"><div class="biglines">{lines}</div></section>'

    # fallback: plain big text
    lines = _big_lines(sc.get("lines", [sc.get("say", "")]))
    return f'<section class="scene hook" data-i="{i}"><div class="biglines">{lines}</div></section>'


CSS = r"""
* { margin:0; padding:0; box-sizing:border-box; }
html,body { width:__W__px; height:__H__px; overflow:hidden; background:__BG__;
  font-family:"Noto Sans CJK SC","Source Han Sans SC","Noto Sans CJK",sans-serif;
  -webkit-font-smoothing:antialiased; }
.stage { position:relative; width:__W__px; height:__H__px; overflow:hidden; }
/* depth: drifting accent glows + faint dot grid (kills flat-black) */
.glow { position:absolute; border-radius:50%; filter:blur(120px); opacity:.22; z-index:0; }
.glow.a { width:760px; height:760px; background:__ACCENT__; top:-160px; right:-180px;
  animation:floatA 14s ease-in-out infinite alternate; }
.glow.b { width:680px; height:680px; background:__COOL__; bottom:-200px; left:-160px;
  animation:floatB 16s ease-in-out infinite alternate; }
@keyframes floatA { from{transform:translate(0,0)} to{transform:translate(-60px,80px)} }
@keyframes floatB { from{transform:translate(0,0)} to{transform:translate(70px,-60px)} }
.grid { position:absolute; inset:0; z-index:0; opacity:.5;
  background-image:radial-gradient(__DOT__ 1.5px, transparent 1.6px);
  background-size:46px 46px; mask-image:linear-gradient(180deg,transparent,#000 30%,#000 70%,transparent); }
.tag { position:absolute; top:150px; left:96px; z-index:6; color:#fff; background:__ACCENT__;
  font-weight:800; font-size:40px; padding:13px 30px; border-radius:40px; letter-spacing:1px;
  box-shadow:0 10px 30px __ACCENTSH__; opacity:0; animation:pop .6s ease forwards .15s; }
.handle { position:absolute; bottom:104px; left:96px; z-index:6; color:__SUB__;
  font-weight:700; font-size:34px; opacity:.85; letter-spacing:.5px; }
.bar { position:absolute; left:0; bottom:0; height:9px; width:0; background:__ACCENT__; z-index:7;
  box-shadow:0 0 18px __ACCENT__; }
.scene { position:absolute; inset:0; z-index:3; display:flex; flex-direction:column;
  justify-content:center; padding:0 96px; opacity:0; transform:translateY(18px) scale(.992);
  transition:opacity .45s ease, transform .45s ease; pointer-events:none; }
.scene.active { opacity:1; transform:none; }
/* big kinetic text (hook / outro / fallback) */
.biglines { position:relative; }
.eyebrow { color:__ACCENT__; font-weight:800; font-size:46px; letter-spacing:3px;
  margin-bottom:26px; opacity:0; }
.scene.active .eyebrow { animation:rise .6s ease forwards; }
.big { color:__FG__; font-weight:900; font-size:128px; line-height:1.16; letter-spacing:1px;
  opacity:0; transform:translateY(42px); }
.scene.active .big { animation:rise .72s cubic-bezier(.2,.7,.2,1) forwards; animation-delay:var(--d); }
.accentbar { height:14px; width:0; background:__ACCENT__; border-radius:8px; margin-top:42px; }
.scene.active .accentbar { animation:grow .8s cubic-bezier(.2,.7,.2,1) forwards .35s; }
/* stat */
.statwrap { text-align:left; }
.statnum { color:__ACCENT__; font-weight:900; font-size:300px; line-height:.96; letter-spacing:-4px;
  opacity:0; transform:translateY(30px) scale(.9); }
.scene.active .statnum { animation:popbig .75s cubic-bezier(.2,.8,.2,1) forwards; }
.statunit { font-size:120px; }
.statlabel { color:__FG__; font-weight:800; font-size:74px; margin-top:24px; opacity:0; }
.scene.active .statlabel { animation:rise .6s ease forwards .3s; }
/* code window */
.win { background:__CARD__; border:1.5px solid __CARDBD__; border-radius:30px; overflow:hidden;
  box-shadow:0 40px 90px rgba(0,0,0,.45); opacity:0; transform:translateY(34px) scale(.96); }
.scene.active .win { animation:popbig .6s cubic-bezier(.2,.8,.2,1) forwards; }
.winbar { display:flex; align-items:center; gap:14px; padding:24px 30px;
  background:__CARDBAR__; border-bottom:1.5px solid __CARDBD__; }
.dot { width:22px; height:22px; border-radius:50%; }
.dot.d1{background:#FF5F57} .dot.d2{background:#FEBC2E} .dot.d3{background:#28C840}
.winlang { margin-left:auto; color:__SUB__; font-weight:700; font-size:32px; letter-spacing:1px; }
.wincode { padding:34px 38px; font-family:"Noto Sans Mono CJK SC","JetBrains Mono","DejaVu Sans Mono","Noto Sans CJK SC",monospace;
  font-size:46px; line-height:1.5; }
.codeline { color:__CODEFG__; white-space:pre; opacity:0; transform:translateX(-14px);
  overflow:hidden; text-overflow:ellipsis; }
.scene.active .codeline { animation:slidein .5s ease forwards; animation-delay:var(--d); }
.t-kw{color:#FF7AB6;font-weight:700} .t-str{color:#9ECE6A} .t-cmt{color:#6B7689;font-style:italic}
.t-num{color:#FF9E64} .t-fn{color:#7AA2F7} .t-dec{color:#E0AF68}
.codecap { color:__FG__; font-weight:800; font-size:60px; margin-top:46px; opacity:0; }
.scene.active .codecap { animation:rise .6s ease forwards .5s; }
/* compare */
.compare { gap:42px; }
.cmp { display:flex; align-items:center; gap:30px; padding:46px 50px; border-radius:26px;
  font-weight:800; font-size:64px; opacity:0; }
.cmp .cmpicon { width:74px; height:74px; min-width:74px; border-radius:50%; display:flex;
  align-items:center; justify-content:center; font-size:46px; color:#fff; }
.cmp.before { background:__DIMCARD__; color:__SUB__; transform:translateX(-60px); }
.cmp.before .cmpicon { background:#6B7280; }
.cmp.before .cmptext { text-decoration:line-through; text-decoration-color:__SUB__; }
.cmp.after { background:__ACCENTDIM__; color:__FG__; transform:translateX(60px); }
.cmp.after .cmpicon { background:__ACCENT__; }
.scene.active .cmp.before { animation:slidex .6s cubic-bezier(.2,.7,.2,1) forwards .05s; }
.scene.active .cmp.after { animation:slidex .6s cubic-bezier(.2,.7,.2,1) forwards .22s; }
/* bullets */
.bhead { color:__ACCENT__; font-weight:800; font-size:56px; margin-bottom:40px; opacity:0; }
.scene.active .bhead { animation:rise .55s ease forwards; }
.blist { display:flex; flex-direction:column; gap:42px; }
.bitem { display:flex; align-items:center; gap:30px; opacity:0; transform:translateY(26px); }
.scene.active .bitem { animation:rise .6s cubic-bezier(.2,.7,.2,1) forwards; animation-delay:var(--d); }
.bdash { width:54px; height:14px; min-width:54px; border-radius:8px; background:__ACCENT__; }
.btext { color:__FG__; font-weight:800; font-size:76px; line-height:1.2; }
/* outro cta */
.cta { margin-top:54px; align-self:flex-start; color:#fff; background:__ACCENT__; font-weight:800;
  font-size:52px; padding:22px 44px; border-radius:50px; box-shadow:0 14px 40px __ACCENTSH__;
  opacity:0; }
.scene.active .cta { animation:pop .6s ease forwards .5s; }
/* keyframes */
@keyframes rise { from{opacity:0;transform:translateY(34px)} to{opacity:1;transform:none} }
@keyframes grow { to{width:240px} }
@keyframes pop { from{opacity:0;transform:translateY(-10px) scale(.96)} to{opacity:1;transform:none} }
@keyframes popbig { from{opacity:0;transform:translateY(30px) scale(.92)} to{opacity:1;transform:none} }
@keyframes slidein { from{opacity:0;transform:translateX(-14px)} to{opacity:1;transform:none} }
@keyframes slidex { to{opacity:1;transform:none} }
/* hook = instant-on: the opening (and the video cover = frame 0) shows the fully
   composed punch immediately instead of mid-entrance — bolder hook + clean cover. */
.scene.hook .eyebrow, .scene.hook .big { opacity:1; transform:none; animation:none; }
.scene.hook .accentbar { width:240px; animation:none; }
"""


def build_html(spec, durs):
    theme = spec.get("theme", "dark")
    dark = theme != "light"
    accent = spec.get("accent", "#FF2E4D")
    cool = spec.get("cool", "#2E7BFF")
    pal = {
        "__W__": str(W), "__H__": str(H), "__ACCENT__": accent, "__COOL__": cool,
        "__BG__": "#0B0E14" if dark else "#F5F4F0",
        "__FG__": "#FFFFFF" if dark else "#14161C",
        "__SUB__": "#9AA3B2" if dark else "#5B616E",
        "__DOT__": "rgba(255,255,255,.07)" if dark else "rgba(0,0,0,.06)",
        "__CARD__": "#11151F" if dark else "#FFFFFF",
        "__CARDBAR__": "#161B27" if dark else "#ECEAE4",
        "__CARDBD__": "rgba(255,255,255,.09)" if dark else "rgba(0,0,0,.10)",
        "__CODEFG__": "#C8D3F5" if dark else "#2A2E3A",
        "__DIMCARD__": "rgba(255,255,255,.05)" if dark else "rgba(0,0,0,.05)",
        "__ACCENTDIM__": _rgba(accent, .14),
        "__ACCENTSH__": _rgba(accent, .45),
    }
    css = CSS
    for k, v in pal.items():
        css = css.replace(k, v)

    scenes = spec.get("scenes", [])
    scenes_html = "\n".join(scene_html(i, sc) for i, sc in enumerate(scenes))
    tag = spec.get("tag", "")
    tag_html = f'<div class="tag">{esc(tag)}</div>' if tag else ""
    handle = spec.get("handle", "@yourhandle")
    total = sum(durs) if durs else len(scenes) * 2.8

    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{css}</style></head>
<body><div class="stage">
<div class="glow a"></div><div class="glow b"></div><div class="grid"></div>
{tag_html}
{scenes_html}
<div class="handle">{esc(handle)}</div>
<div class="bar" id="bar"></div>
</div>
<script>
const durs = {json.dumps(durs)};
const total = {total};
const scenes = [...document.querySelectorAll('.scene')];
const bar = document.getElementById('bar');
bar.style.transition = 'width ' + total + 's linear';
function show(i){{ scenes.forEach((s,k)=>s.classList.toggle('active', k===i)); }}
window.__done = false;
function run(i){{
  if(i>=scenes.length){{ window.__done = true; return; }}
  show(i);
  setTimeout(()=>run(i+1), (durs[i]||2.8)*1000);
}}
requestAnimationFrame(()=>{{ bar.style.width='100%'; run(0); }});
</script></body></html>"""


def _rgba(hexc, a):
    hexc = hexc.lstrip("#")
    if len(hexc) == 3:
        hexc = "".join(c * 2 for c in hexc)
    try:
        r, g, b = int(hexc[0:2], 16), int(hexc[2:4], 16), int(hexc[4:6], 16)
    except ValueError:
        r, g, b = 255, 46, 77
    return f"rgba({r},{g},{b},{a})"


# ----------------------------------------------------------------------------- render
def record(html_path, total_s):
    from playwright.sync_api import sync_playwright
    rec_dir = tempfile.mkdtemp(prefix="richrec-")
    with sync_playwright() as p:
        browser = p.chromium.launch(args=["--no-sandbox", "--disable-dev-shm-usage"])
        ctx = browser.new_context(
            viewport={"width": W, "height": H}, device_scale_factor=1,
            record_video_dir=rec_dir, record_video_size={"width": W, "height": H},
        )
        page = ctx.new_page()
        page.goto("file://" + html_path)
        page.wait_for_timeout(int(total_s * 1000) + 1000)
        page.close()
        ctx.close()
        browser.close()
    vids = glob.glob(os.path.join(rec_dir, "*.webm"))
    if not vids:
        raise RuntimeError("Playwright produced no video")
    return vids[0]


def main():
    ap = argparse.ArgumentParser(description="Build a rich motion-graphics 9:16 抖音 video.")
    ap.add_argument("--spec", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--voice", default=DEFAULT_VOICE,
                    help="volc voice_type, OR Fish Audio reference_id when --tts fish")
    ap.add_argument("--tts", choices=["volc", "fish"], default="volc",
                    help="TTS provider: volc (火山/vivi) or fish (Fish Audio, e.g. 赛马娘)")
    ap.add_argument("--fish-model", default="s1", help="Fish Audio backbone: s1 or s2-pro")
    ap.add_argument("--speed", default="1.0")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--no-audio", action="store_true", help="render silent (debug)")
    args = ap.parse_args()

    with open(args.spec, encoding="utf-8") as f:
        spec = json.load(f)
    scenes = spec.get("scenes", [])
    if not scenes:
        print("ERROR: spec has no scenes", file=sys.stderr)
        return 2

    workdir = tempfile.mkdtemp(prefix="rich-")
    if args.no_audio:
        durs = [max(MIN_DUR, 2.6) for _ in scenes]
        voice_mp3 = None
    else:
        # with Fish Audio the volc default voice_type is meaningless — clear it so
        # fish_tts.py resolves the reference_id from --voice or its creds file.
        voice = args.voice
        if args.tts == "fish" and voice == DEFAULT_VOICE:
            voice = ""
        print(f"[rich] 1/3 {args.tts} voice per scene ({len(scenes)} scenes, voice={voice or '(creds)'})...")
        voice_mp3, durs = build_audio(scenes, workdir, voice, float(args.speed),
                                      provider=args.tts, fish_model=args.fish_model)

    print(f"[rich] 2/3 render motion graphics ({sum(durs):.1f}s)...")
    html_doc = build_html(spec, durs)
    hf = tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8")
    hf.write(html_doc); hf.close()
    webm = record(hf.name, sum(durs))

    print("[rich] 3/3 smooth-interpolate + cover + mux...")
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)

    # Clean cover: the recorder's first frame is a partial-paint frame (squished /
    # gray) — 抖音 uses frame 0 as the thumbnail, so the cover looks broken. Grab a
    # settled hook frame and overlay it over the first COVER_HOLD s so frame 0 is clean.
    cover_t = max(0.4, min(1.0, (durs[0] - 0.2) if durs else 1.0))
    cover_png = os.path.join(workdir, "_cover.png")
    cov = subprocess.run(
        ["ffmpeg", "-y", "-ss", f"{cover_t:.3f}", "-i", webm,
         "-frames:v", "1", "-q:v", "2", cover_png],
        capture_output=True, text=True,
    )
    have_cover = cov.returncode == 0 and os.path.exists(cover_png)

    # Smoother 30fps via blend interpolation: fast (no motion-estimation) and clean for
    # our gentle fades/slides — it removes the old 25->30 dup-frame judder and fills the
    # in-between frames. NOTE: do NOT prepend mpdecimate here — with blend mode the large
    # time-gaps mpdecimate creates (static holds) turn into slow cross-dissolves. The
    # mci/bidir variant looked great but was ~25x slower (minutes) — too slow for the
    # daily cron, so blend it is.
    smooth = f"minterpolate=fps={args.fps}:mi_mode=blend,scale={W}:{H},format=yuv420p"

    cmd = ["ffmpeg", "-y", "-i", webm]
    if voice_mp3:
        cmd += ["-i", voice_mp3]
    if have_cover:
        cmd += ["-loop", "1", "-i", cover_png]
        cov_idx = 2 if voice_mp3 else 1
        fc = (f"[0:v]{smooth}[v0];"
              f"[{cov_idx}:v]scale={W}:{H},setsar=1,format=yuv420p[cov];"
              f"[v0][cov]overlay=enable='lte(t,{COVER_HOLD})':eof_action=pass[v]")
        cmd += ["-filter_complex", fc, "-map", "[v]"]
    else:
        cmd += ["-vf", smooth, "-map", "0:v"]
    if voice_mp3:
        cmd += ["-map", "1:a", "-c:a", "aac", "-b:a", "192k", "-shortest"]
    else:
        cmd += ["-an"]
    cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "19", args.out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write("[rich] ffmpeg failed:\n" + r.stderr[-1200:] + "\n")
        return 1

    abs_out = os.path.abspath(args.out)
    dur = _ffprobe_dur(abs_out)
    print(f"[rich] DONE -> {abs_out}  ({dur:.1f}s, 1080x1920, smooth {args.fps}fps + clean cover)")
    print(f"[rich] NEXT: browser_upload(file_paths=['{abs_out}'], selector='input[type=file]')  -- exact path")
    for f in (hf.name, webm, cover_png):
        try:
            os.remove(f)
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
