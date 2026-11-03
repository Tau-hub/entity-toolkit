"""Recognises the survivors' perks and the map on a screenshot of the in-game players menu (Tab).

Each perk icon on the screenshot is compared (normalised correlation, several scales) with the survivor perk icons
downloaded by ``update-db``. Only the pixels of the screenshot are used.
"""
import difflib
import json
import re
import time

import cv2
import numpy as np
from PIL import Image

from . import ocr, paths
from .text import norm

# Layout measured on a 2000x1125 screenshot (proportional to the screen height)
REF_H = 1125
ROWS_Y = [265, 384, 503, 621]
PERKS_X = [775, 831, 888, 944]
BOX = 28    # half side of the crop (px at REF_H)
GLYPH = 50  # side of the icon on the screenshot (px at REF_H), found by calibration (correlation peak)
MAP_BOX = (560, 880, 1440, 975)  # where the map name is, at the bottom of the screen (px at REF_H)


def cx_of(img, x):
    """x of the 2000 px wide reference screenshot, moved to the image's centre: the game's UI is centred."""
    return img.width / 2 + (x - 1000) * img.height / REF_H


def map_lists():
    """Map and realm names from the wiki, saved by ``update-db``."""
    if not paths.MAPS.exists():
        raise FileNotFoundError("Map names are missing: run `python -m entity_toolkit update-db` first.")
    return json.loads(paths.MAPS.read_text(encoding="utf8"))


def recognize_map(img):
    """Reads the text at the bottom of the screen (Windows OCR) and matches it with the known maps / realms."""
    s = img.height / REF_H
    x0, y0, x1, y1 = MAP_BOX
    lines = ocr.read_lines(img.crop((int(cx_of(img, x0)), int(y0 * s), int(cx_of(img, x1)), int(y1 * s))))
    known = map_lists()

    # the wiki uses British spelling (Theatre) while the game shows Theater: fuzzy matching absorbs the gap
    def best(names, text):
        t = norm(text)
        sc = sorted(((difflib.SequenceMatcher(None, t, norm(n)).ratio(), n) for n in names), reverse=True)
        return sc[0] if sc and sc[0][0] >= 0.75 else None

    found = {"maps": None, "realms": None, "ocr": lines}
    for ln in lines:
        for part in re.split(r"\s[-–—]\s", ln):
            for key in ("maps", "realms"):
                cand = best(known[key], part)
                if cand and (found[key] is None or cand[0] > found[key][0]):
                    found[key] = cand
    return found


def whiteness(rgb):
    """Light/grey pixels (the white glyph) high, the purple / dark background low."""
    return rgb.min(axis=2).astype(np.float32)


def load_refs(data):
    refs = []
    for p in data["perks"]["S"]:
        a = np.array(Image.open(paths.ICONS / p["icon"]).convert("RGBA"))[:, :, 3].astype(np.float32)
        refs.append((p["name"], a))
    return refs


def prepare(refs, sizes):
    """Resizes every reference icon once per size (the expensive part otherwise)."""
    return [(n, [cv2.resize(a, (s, s), interpolation=cv2.INTER_AREA) for s in sizes]) for n, a in refs]


def best_score(crop, templates):
    return max(float(cv2.matchTemplate(crop, t, cv2.TM_CCOEFF_NORMED).max()) for t in templates)


def recognize(img, refs, top=3, rows=None):
    """rows: indices of the rows to analyse (0 = local player, at the top); None = all 4 rows."""
    scale = img.height / REF_H
    out = []
    t0 = time.time()
    prepared = prepare(refs, [GLYPH - 2, GLYPH, GLYPH + 2])
    for ri, y in enumerate(ROWS_Y):
        if rows is not None and ri not in rows:
            out.append(None)
            continue
        row = []
        for x in PERKS_X:
            b = int(BOX * scale)
            px = int(cx_of(img, x))
            crop = img.crop((px - b, int(y * scale) - b, px + b, int(y * scale) + b)).resize((2 * BOX, 2 * BOX), Image.LANCZOS)
            c = whiteness(np.array(crop))
            c[:19, 33:] = 0  # tier pips at the top right
            scores = sorted(((best_score(c, ts), n) for n, ts in prepared), reverse=True)[:top]
            row.append(scores)
        out.append(row)
    return out, time.time() - t0
