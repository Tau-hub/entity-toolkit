"""Reads your character levels from screenshots of the in-game character selection grid (killers or survivors).

For each card of the grid:
  1. find the cards: the near-black rough frame around each card is a dark blob with the card's proportions; the missing cards of the
     regular grid are filled in from the pitch of the ones found;
  2. recognise the character by matching SIFT features of the card with the portraits downloaded by `update-db`;
  3. read the level badge (bottom left): an empty ring is level 0, otherwise the digit is read with Windows OCR.
Only pixels of the screenshot are used. Results are suggestions: the Levels page shows them for review before anything is saved.
"""
import json

import cv2
import numpy as np
from PIL import Image

from . import levels, paths

MIN_MATCHES = 20      # good SIFT matches needed to name a character
MARGIN = 1.35         # the best character must beat the second best by this factor
CARD_SIZE = 300       # cards are resized to this height before matching
_REFS = {}


def _gray_on_black(im):
    im = im.convert("RGBA")
    bg = Image.new("RGBA", im.size, (0, 0, 0, 255))
    bg.alpha_composite(im)
    return cv2.cvtColor(np.asarray(bg.convert("RGB")), cv2.COLOR_RGB2GRAY)


def _sift():
    return cv2.SIFT_create(nfeatures=900)


def references():
    """{kind: [(short name, descriptors)]} for every character that has a portrait. Cached until the data changes."""
    key = (paths.KILLERS.stat().st_mtime if paths.KILLERS.exists() else 0, paths.SURVIVORS.stat().st_mtime if paths.SURVIVORS.exists() else 0)
    if _REFS.get("key") == key:
        return _REFS["refs"]
    sift, refs = _sift(), {k: [] for k in levels.KINDS}
    for kind in levels.KINDS:
        for c in levels.characters(kind):
            f = paths.DATA / c["portrait"] if c.get("portrait") else None
            if not f or not f.exists():
                continue
            g = _gray_on_black(Image.open(f))
            g = cv2.resize(g, (CARD_SIZE, CARD_SIZE), interpolation=cv2.INTER_AREA)
            _, des = sift.detectAndCompute(g, None)
            if des is not None:
                refs[kind].append((c["short"], des))
    _REFS.update(key=key, refs=refs)
    return refs


# ---------- finding the cards ----------
def frames(img):
    """Boxes (x, y, w, h) of the cards whose dark frame is clearly visible."""
    v = np.asarray(img.convert("RGB")).max(axis=2)
    dark = (v < 38).astype(np.uint8) * 255
    dark = cv2.morphologyEx(dark, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    cnts, _ = cv2.findContours(dark, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    W, H = img.size
    out = []
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        if w < W * 0.06 or h < H * 0.06 or w > W * 0.5 or not 0.74 < w / h < 0.95:
            continue
        out.append((x, y, w, h))
    return out


def _cluster(values, tol):
    values = sorted(values)
    groups = [[values[0]]]
    for v in values[1:]:
        if v - groups[-1][-1] <= tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [float(np.median(g)) for g in groups]


def grid(img):
    """All the card boxes of the regular grid, filling in the cards whose frame was not detected. Cards cut by the image edge are skipped."""
    fs = frames(img)
    if not fs:
        return []
    w = int(np.median([f[2] for f in fs]))
    h = int(np.median([f[3] for f in fs]))
    xs, ys = _cluster([f[0] for f in fs], w * 0.25), _cluster([f[1] for f in fs], h * 0.25)
    W, H = img.size

    def axis(pos, size, limit):
        step = float(np.median(np.diff(pos))) if len(pos) > 1 else size * 1.06
        if step < size * 0.9:  # clusters too close: not a real pitch
            step = size * 1.06
        start = pos[0]
        while start - step > -size * 0.06:
            start -= step
        out = []
        p = start
        while p + size <= limit + size * 0.06:
            if p >= -size * 0.06:
                out.append(int(round(p)))
            p += step
        return out

    return [(max(x, 0), max(y, 0), min(w, W - max(x, 0)), min(h, H - max(y, 0))) for y in axis(ys, h, H) for x in axis(xs, w, W)]


# ---------- recognising a card ----------
def identify(card):
    """(kind, short name, good matches, runner-up matches) of the character the card shows, or (None, None, ...) when no portrait stands out."""
    sift = _sift()
    g = cv2.cvtColor(np.asarray(card.convert("RGB")), cv2.COLOR_RGB2GRAY)
    g = g[: int(g.shape[0] * 0.78)]  # leave the level badge out
    g = cv2.resize(g, (int(g.shape[1] * CARD_SIZE / g.shape[0]), CARD_SIZE), interpolation=cv2.INTER_AREA)
    _, des = sift.detectAndCompute(g, None)
    if des is None:
        return None, None, 0, 0
    bf = cv2.BFMatcher(cv2.NORM_L2)
    scores = []
    for kind, refs in references().items():  # killers and survivors together: a card's colour is not a reliable hint
        for name, rdes in refs:
            pairs = bf.knnMatch(rdes, des, k=2)
            good = sum(1 for p in pairs if len(p) == 2 and p[0].distance < 0.75 * p[1].distance)
            scores.append((good, kind, name))
    scores.sort(reverse=True)
    if not scores:
        return None, None, 0, 0
    best, second = scores[0], (scores[1] if len(scores) > 1 else (0, "", ""))
    if best[0] < MIN_MATCHES or best[0] < MARGIN * max(second[0], 1):
        return None, None, best[0], second[0]
    return best[1], best[2], best[0], second[0]


# ---------- reading the level badge ----------
_DIGITS = {}


def _norm_mask(mask):
    """Crops a boolean mask to its bounding box and resizes it to 20x28 (so the digit's size on screen does not matter)."""
    ys, xs = np.where(mask)
    if not len(xs):
        return None
    crop = mask[ys.min(): ys.max() + 1, xs.min(): xs.max() + 1].astype(np.uint8) * 255
    return cv2.resize(crop, (20, 28), interpolation=cv2.INTER_AREA) > 127


def _digit_templates():
    """The digits 1-3 drawn in a bold sans-serif font: the game's badge font is a bold sans too, and the three shapes are very different."""
    if _DIGITS:
        return _DIGITS
    from PIL import ImageDraw, ImageFont
    font = None
    for name in ("arialbd.ttf", "segoeuib.ttf", "DejaVuSans-Bold.ttf"):
        try:
            font = ImageFont.truetype(name, 90)
            break
        except OSError:
            continue
    for d in "123":
        im = Image.new("L", (140, 140), 0)
        ImageDraw.Draw(im).text((20, 10), d, fill=255, font=font)
        _DIGITS[int(d)] = _norm_mask(np.asarray(im) > 127)
    return _DIGITS


def read_level(card):
    """0 for an empty ring, otherwise the digit (1-3) in the badge at the bottom left; None when unreadable."""
    w, h = card.size
    badge = np.asarray(card.crop((int(w * 0.10), int(h * 0.74), int(w * 0.42), int(h * 0.98))).convert("L"))
    inner = badge[int(badge.shape[0] * 0.10): int(badge.shape[0] * 0.75), int(badge.shape[1] * 0.22): int(badge.shape[1] * 0.78)]
    white = inner > 225
    if white.mean() < 0.02:  # no white digit on the disc: an empty ring
        return 0
    # the digit is one connected blob, tall and near the middle of the disc; stray bright pixels of the portrait are ignored
    n, lab, stats, cents = cv2.connectedComponentsWithStats(white.astype(np.uint8))
    cx, cy = inner.shape[1] / 2, inner.shape[0] / 2
    cands = [i for i in range(1, n) if stats[i, cv2.CC_STAT_HEIGHT] >= inner.shape[0] * 0.35 and stats[i, cv2.CC_STAT_AREA] >= 12]
    if not cands:
        return None
    best_blob = min(cands, key=lambda i: (cents[i][0] - cx) ** 2 + (cents[i][1] - cy) ** 2)
    m = _norm_mask(lab == best_blob)
    if m is None:
        return None
    scores = {d: float((m & t).sum()) / max(float((m | t).sum()), 1.0) for d, t in _digit_templates().items()}
    best = max(scores, key=scores.get)
    return best if scores[best] >= 0.45 else None


def scan(img):
    """Cards found on one screenshot: [{"kind", "name", "level", "matches", "box"}]; name / level are None when not recognised."""
    img = img.convert("RGB")
    out = []
    for x, y, w, h in grid(img):
        card = img.crop((x, y, x + w, y + h))
        kind, name, good, second = identify(card)
        out.append({"kind": kind, "name": name, "level": read_level(card), "matches": good, "runner_up": second, "box": [x, y, w, h]})
    return out


def merge(results):
    """Several screenshots may show the same character: keep one entry per character, the most confident one.
    Returns (entries by (kind, name), unrecognised count)."""
    best, unknown = {}, 0
    for r in results:
        if not r["name"] or r["level"] is None:
            unknown += 1
            continue
        key = (r["kind"], r["name"])
        if key not in best or r["matches"] > best[key]["matches"]:
            best[key] = r
    return best, unknown
