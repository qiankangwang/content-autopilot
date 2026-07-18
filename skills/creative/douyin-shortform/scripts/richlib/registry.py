#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""richlib.registry — choose a style per video, with anti-repeat + topic affinity.

select() is the between-videos variation: it weights every style by
weight * affinity(spec), penalizes the styles used in the last couple of runs
(persisted in .style_state.json next to the output), and draws one with a
seeded RNG. An explicit --style or spec['style'] overrides everything.
"""
import json
import os
import random

from . import base
from .style_keynote import KeynoteStyle
from .style_editorial import EditorialStyle
from .style_notebook import NotebookStyle
from .style_terminal import TerminalStyle
from .style_tabloid import TabloidStyle

# Order = nothing special; weights/affinity decide. Keynote is intentionally
# low-weight: kept as a rare option, no longer the default look.
STYLES = [
    EditorialStyle(),
    NotebookStyle(),
    TerminalStyle(),
    TabloidStyle(),
    KeynoteStyle(),
]
BY_ID = {s.id: s for s in STYLES}

_STATE_NAME = ".style_state.json"
_RECENT_KEEP = 4


def _state_path(out_path):
    d = os.path.dirname(os.path.abspath(out_path)) if out_path else "."
    return os.path.join(d, _STATE_NAME)


def _load_recent(out_path):
    try:
        with open(_state_path(out_path), encoding="utf-8") as f:
            return list(json.load(f).get("recent", []))[-_RECENT_KEEP:]
    except Exception:
        return []


def _save_recent(out_path, recent):
    try:
        with open(_state_path(out_path), "w", encoding="utf-8") as f:
            json.dump({"recent": recent[-_RECENT_KEEP:]}, f, ensure_ascii=False)
    except Exception:
        pass


def make_rng(spec, out_path=""):
    return random.Random(base.seed_from(spec, out_path))


def select(spec, rng, out_path="", explicit=None):
    """Return (style, recent_after). Does NOT persist — caller persists once it
    commits to rendering (so a dry inspection doesn't poison rotation)."""
    recent = _load_recent(out_path)

    # explicit override (CLI --style or spec['style'])
    forced = (explicit or spec.get("style") or "").strip().lower()
    if forced in BY_ID:
        return BY_ID[forced], recent

    scores = {}
    for s in STYLES:
        sc = max(0.0001, float(s.weight) * float(s.affinity(spec)))
        if recent[-1:] and s.id == recent[-1]:
            sc *= 0.08          # almost never twice in a row
        elif s.id in recent[-2:]:
            sc *= 0.30
        elif s.id in recent[-_RECENT_KEEP:]:
            sc *= 0.65
        scores[s] = sc

    total = sum(scores.values())
    r = rng.random() * total
    chosen = STYLES[-1]
    for s in STYLES:
        r -= scores[s]
        if r <= 0:
            chosen = s
            break
    return chosen, recent


def commit(out_path, recent, style):
    _save_recent(out_path, (recent + [style.id])[-_RECENT_KEEP:])
