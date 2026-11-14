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


def row_offsets(img):
    """How far each of the four rows really is from ROWS_Y (px at REF_H). The rows keep their usual place when four humans play, but are
    shorter or taller when bots are in the match (a bot row has no player icon), so the later rows move up or down by up to ~20 px.
    Found on the purple diamond of each row's first perk. When no row is more than 8 px off, all give 0 (noise)."""
    s = img.height / REF_H
    y0 = 170
    x = cx_of(img, PERKS_X[0])
    b = int(22 * s)
    band = np.asarray(img.convert("RGB").crop((int(x - b), int(y0 * s), int(x + b), int(720 * s))), dtype=int)
    purple = ((band[:, :, 2] - band[:, :, 1]) > 30) & ((band[:, :, 0] - band[:, :, 1]) > 8)
    k = max(3, int(34 * s))
    sm = np.convolve(purple.sum(axis=1).astype(float), np.ones(k) / k, mode="same")
    out = []
    for y in ROWS_Y:
        lo, hi = max(0, int((y - y0 - 40) * s)), int((y - y0 + 40) * s)  # up to three bots: the last row can be ~25 px higher
        seg = sm[lo:hi]
        d = round((lo + float(np.flatnonzero(seg >= 0.98 * seg.max()).mean())) / s + y0 - y) if len(seg) and seg.max() > 3 else 0  # middle of the top plateau
        out.append(d)
    return out if any(abs(d) > 8 for d in out) else [0, 0, 0, 0]  # all the offsets or none: small ones alone are noise


def recognize(img, refs, top=3, rows=None, dys=None):
    """rows: indices of the rows to analyse (0 = local player, at the top); None = all 4 rows. dys: vertical offset of each row (see row_offsets)."""
    scale = img.height / REF_H
    out = []
    t0 = time.time()
    prepared = prepare(refs, [GLYPH - 2, GLYPH, GLYPH + 2])
    b = int(BOX * scale)

    def icon_scores(x, yy):
        px = int(cx_of(img, x))
        crop = img.crop((px - b, yy - b, px + b, yy + b)).resize((2 * BOX, 2 * BOX), Image.LANCZOS)
        c = whiteness(np.array(crop))
        c[:19, 33:] = 0  # tier pips at the top right
        return sorted(((best_score(c, ts), n) for n, ts in prepared), reverse=True)[:top]

    for ri, y in enumerate(ROWS_Y):
        if rows is not None and ri not in rows:
            out.append(None)
            continue
        d = dys[ri] if dys else 0
        if dys and any(dys):  # rows moved (bots in the match): the offset found is within a few px, the best one is the one where the first icon matches best
            d = max((d - 6, d, d + 6), key=lambda c: icon_scores(PERKS_X[0], int((y + c) * scale))[0][0])
        if dys:
            dys[ri] = d  # (the refined offset goes back to the caller: the names are read at the same height)
        yy = int((y + d) * scale)
        out.append([icon_scores(x, yy) for x in PERKS_X])
    return out, time.time() - t0
