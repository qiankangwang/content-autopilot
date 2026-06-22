#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate 小红书-style cover + carousel cards — bold CJK text on clean, designed
backgrounds (3:4, 1080x1440). 小红书 is a COVER-DRIVEN platform: a raw AI image is a
weak cover; a designed cover with the hook text + clean content cards reads as 干货
and gets far more engagement.

ANTI-同质化: every post should NOT look identical. This generator picks one of several
cohesive color themes + a couple of layout variants, SEEDED by the topic (title) so the
same topic is reproducible but different topics look visually distinct. 小红书 flags
batch/同质 content (identical template every day) → 限流. Pass --seed to override, or
put "theme":"mint" (or "accent"/"bg") in the spec to pin a look.

Runs INSIDE the agent container (fonts-noto-cjk present). Feed it a JSON spec:
  {
    "title": "三行字的强钩子",          # cover big title (the hook)
    "subtitle": "一句副标题(可选)",
    "tag": "AI干货",                    # small pill on the cover
    "cards": [                          # 0-6 carousel content cards
      {"heading": "卡片小标题", "body": "正文,\\n可多行"}
    ],
    "bg": "/root/.hermes/cache/images/x.png",  # optional cover background photo
    "theme": "mint",                    # optional: pin a theme (else seeded by title)
    "handle": "@yourhandle"             # optional: override the footer handle
  }

Output: <outdir>/01-cover.png, 02-*.png ... (upload these to 小红书 with drop=true).
Usage:
  python make_xhs_cards.py --spec spec.json --outdir /root/hermes-content/小红书/<date>-<topic>
"""
import argparse, hashlib, json, os, random, sys
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1440
MARGIN = 96
DEFAULT_HANDLE = "@yourhandle"

# Cohesive themes — each a clean, 小红书-appropriate palette. `dark` covers use light
# text. Keeping the set tasteful (no garish combos) so any pick still looks designed.
THEMES = {
    "coral":  {"accent": (255, 90, 95),  "cover": ((255, 249, 243), (255, 230, 214)),
               "card": ((252, 250, 247), (246, 243, 238)), "ink": (30, 28, 30), "dark": False},
    "mint":   {"accent": (32, 168, 150),  "cover": ((240, 250, 248), (212, 238, 231)),
               "card": ((248, 252, 251), (237, 246, 243)), "ink": (24, 42, 39), "dark": False},
    "indigo": {"accent": (92, 88, 214),   "cover": ((244, 244, 255), (221, 221, 246)),
               "card": ((250, 250, 253), (239, 239, 248)), "ink": (28, 28, 46), "dark": False},
    "amber":  {"accent": (236, 158, 28),  "cover": ((255, 250, 238), (252, 234, 203)),
               "card": ((253, 250, 243), (247, 242, 232)), "ink": (46, 36, 18), "dark": False},
    "ocean":  {"accent": (30, 142, 200),  "cover": ((238, 248, 253), (205, 231, 246)),
               "card": ((247, 251, 253), (235, 244, 249)), "ink": (18, 38, 50), "dark": False},
    "night":  {"accent": (255, 96, 122),  "cover": ((28, 27, 33), (46, 40, 54)),
               "card": ((250, 249, 251), (240, 238, 244)), "ink": (26, 24, 30), "dark": True},
}
THEME_KEYS = list(THEMES.keys())


def _find_font(bold):
    names = (["NotoSansCJKsc-Bold.otf", "NotoSansCJK-Bold.ttc", "NotoSansSC-Bold.otf",
              "NotoSerifCJKsc-Bold.otf"] if bold else
             ["NotoSansCJKsc-Regular.otf", "NotoSansCJK-Regular.ttc", "NotoSansSC-Regular.otf"])
    roots = ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts")]
    for d in roots:
        for root, _, files in os.walk(d):
            for n in names:
                if n in files:
                    return os.path.join(root, n)
    for d in roots:
        for root, _, files in os.walk(d):
            for f in files:
                if ("CJK" in f or "SC" in f or "Hei" in f) and f.lower().endswith((".otf", ".ttc", ".ttf")):
                    return os.path.join(root, f)
    raise RuntimeError("No CJK font found (install fonts-noto-cjk)")


_FB = _find_font(True)
_FR = _find_font(False)


def font(size, bold=True):
    return ImageFont.truetype(_FB if bold else _FR, size)


def _pick_theme(spec, rng):
    name = spec.get("theme")
    if name in THEMES:
        return name, THEMES[name]
    name = rng.choice(THEME_KEYS)
    th = dict(THEMES[name])
    # optional spec override of just the accent
    if spec.get("accent") and isinstance(spec["accent"], (list, tuple)) and len(spec["accent"]) == 3:
        th["accent"] = tuple(spec["accent"])
    return name, th


def _wrap(draw, text, fnt, max_w):
    """Wrap CJK/mixed text to max_w pixels (char by char)."""
    lines, cur = [], ""
    for ch in text:
        if ch == "\n":
            lines.append(cur); cur = ""; continue
        if draw.textlength(cur + ch, font=fnt) <= max_w:
            cur += ch
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines


def _vgrad(top, bot):
    img = Image.new("RGB", (W, H), top)
    px = img.load()
    for y in range(H):
        t = y / H
        px_row = tuple(int(top[i] + (bot[i] - top[i]) * t) for i in range(3))
        for x in range(W):
            px[x, y] = px_row
    return img


def _cover_bg(bg_path, theme):
    if bg_path and os.path.exists(bg_path):
        im = Image.open(bg_path).convert("RGB")
        r = max(W / im.width, H / im.height)
        im = im.resize((int(im.width * r), int(im.height * r)))
        x = (im.width - W) // 2; y = (im.height - H) // 2
        im = im.crop((x, y, x + W, y + H))
        ov = Image.new("RGB", (W, H), (0, 0, 0)); m = Image.new("L", (W, H))
        mp = m.load()
        for yy in range(H):
            a = int(150 - 90 * (yy / H))
            for xx in range(W):
                mp[xx, yy] = max(a, 40)
        return Image.composite(ov, im, m)
    return _vgrad(*theme["cover"])


def make_cover(spec, out, theme, layout, handle):
    photo = bool(spec.get("bg") and os.path.exists(spec["bg"]))
    light_text = photo or theme["dark"]
    img = _cover_bg(spec.get("bg"), theme)
    d = ImageDraw.Draw(img)
    accent = theme["accent"]
    title_color = (255, 255, 255) if light_text else theme["ink"]
    sub_color = (235, 235, 235) if light_text else (118, 118, 126)

    # tag pill (radius varies by layout for subtle variety)
    tag = spec.get("tag", "干货")
    tf = font(40, True)
    tw = d.textlength(tag, font=tf)
    radius = 40 if layout == 0 else 18
    d.rounded_rectangle([MARGIN, 150, MARGIN + tw + 56, 232], radius=radius, fill=accent)
    d.text((MARGIN + 28, 166), tag, font=tf, fill=(255, 255, 255))

    title = spec.get("title", "")
    tfont = font(96, True)
    tlines = _wrap(d, title, tfont, W - 2 * MARGIN)[:4]
    sub = spec.get("subtitle", "")
    sfont = font(46, False)
    slines = _wrap(d, sub, sfont, W - 2 * MARGIN)[:3] if sub else []
    block_h = len(tlines) * 122 + ((40 + len(slines) * 64) if slines else 0)
    # layout 0: vertically centered block; layout 1: anchored to lower third
    if layout == 0:
        y = max(330, (H - block_h) // 2 - 30)
    else:
        y = max(330, H - 300 - block_h)
        # accent rule above the title for the lower-anchored variant
        d.rectangle([MARGIN, y - 44, MARGIN + 96, y - 32], fill=accent)
    for ln in tlines:
        d.text((MARGIN, y), ln, font=tfont, fill=title_color)
        y += 122
    if slines:
        y += 40
        for ln in slines:
            d.text((MARGIN, y), ln, font=sfont, fill=sub_color)
            y += 64

    hf = font(36, False)
    d.text((MARGIN, H - 110), handle, font=hf, fill=(255, 255, 255) if light_text else (140, 140, 148))
    img.save(out, "PNG")
    return out


def make_card(card, idx, total, out, theme, layout, handle):
    accent = theme["accent"]
    ink = theme["ink"]
    gray = (120, 120, 128)
    img = _vgrad(*theme["card"])
    d = ImageDraw.Draw(img)
    # page number
    d.text((MARGIN, 120), f"{idx:02d}", font=font(96, True), fill=accent)
    d.text((W - MARGIN - d.textlength(f"/{total:02d}", font=font(40, True)), 175),
           f"/{total:02d}", font=font(40, True), fill=gray)
    # accent mark: layout 0 = short underline rule; layout 1 = tall left bar by the heading
    if layout == 0:
        d.rectangle([MARGIN, 250, MARGIN + 90, 260], fill=accent)
        hx, y = MARGIN, 300
    else:
        y = 300
        d.rectangle([MARGIN, y + 6, MARGIN + 12, y + 6 + 84 * min(2, 1) + 30], fill=accent)
        hx = MARGIN + 36
    for ln in _wrap(d, card.get("heading", ""), font(60, True), W - 2 * MARGIN - (hx - MARGIN))[:3]:
        d.text((hx, y), ln, font=font(60, True), fill=ink); y += 84
    y += 30
    bfont = font(44, False)
    for ln in _wrap(d, card.get("body", ""), bfont, W - 2 * MARGIN)[:16]:
        d.text((MARGIN, y), ln, font=bfont, fill=(62, 62, 66)); y += 66
    d.text((MARGIN, H - 100), handle, font=font(34, False), fill=gray)
    img.save(out, "PNG")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="JSON spec path")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--seed", help="Override the per-topic style seed (else derived from title)")
    args = ap.parse_args()
    spec = json.load(open(args.spec, encoding="utf-8"))
    os.makedirs(args.outdir, exist_ok=True)

    # Deterministic-but-varied styling: seed from --seed, else title + the dated outdir
    # name (so consecutive days vary even if topics rhyme). hashlib (not the salted
    # built-in hash()) so it's stable across processes.
    seed_src = args.seed or ((spec.get("title", "") or "xhs") + "|" +
                             os.path.basename(os.path.normpath(args.outdir)))
    rng = random.Random(int(hashlib.md5(seed_src.encode("utf-8")).hexdigest(), 16))
    theme_name, theme = _pick_theme(spec, rng)
    layout = rng.randint(0, 1)
    handle = spec.get("handle", DEFAULT_HANDLE)

    outs = [make_cover(spec, os.path.join(args.outdir, "01-cover.png"), theme, layout, handle)]
    cards = spec.get("cards", [])
    for i, c in enumerate(cards, start=2):
        outs.append(make_card(c, i - 1, len(cards),
                              os.path.join(args.outdir, f"{i:02d}-card.png"), theme, layout, handle))
    print(f"[make_xhs_cards] theme={theme_name} layout={layout}")
    print("[make_xhs_cards] generated:")
    for o in outs:
        print("  " + o)
    print(f"[make_xhs_cards] NEXT: upload these {len(outs)} images to 小红书 with browser_upload(drop=true)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
