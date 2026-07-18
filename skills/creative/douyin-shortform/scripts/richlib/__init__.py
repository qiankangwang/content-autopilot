"""richlib — pluggable visual-style engine for the rich 抖音 video builder.

The old pipeline had ONE hardcoded look (dark keynote + accent). This package
breaks the look into swappable *style modules* plus a rotation+variation engine
so consecutive videos rarely share a style AND two same-style videos still differ
(see registry.select / Style.variant). Narration/timing/mux are unchanged and
still live in make_rich_video.py.
"""
