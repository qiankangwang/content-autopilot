# assets/fonts/

Fonts used by the V3 **obsidian** (Dark Matter) headlines and the legacy
**notebook** style. Not committed — download and drop the ttf files here:

**Smiley Sans (得意黑, SIL OFL 1.1)** — obsidian H1 headlines:
<https://github.com/atelier-anchor/smiley-sans/releases>

- `SmileySans-Oblique.ttf`

Handwriting font used by the **notebook** style (`richlib/style_notebook.py`).
Not committed — download **LXGW WenKai** (霞鹜文楷, SIL OFL 1.1) from
<https://github.com/lxgw/LxgwWenKai> and place the ttf files here, e.g.:

- `LXGWWenKai-Regular.ttf`
- `LXGWWenKai-Medium.ttf`

`make_rich_video.py` auto-installs anything in this directory into `~/.fonts`
(and refreshes fontconfig) on each run. Without a handwriting font the notebook
style falls back to the system sans CJK font.
