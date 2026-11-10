"""Character levels (0-3 bloodweb prestige-free "teachable" levels) for every killer and survivor, plus their history.

Stored in data/levels.json as {"killers": {"Trapper": 2, ...}, "survivors": {"Dwight Fairfield": 3, ...}}. Three ways to fill it:
  1. the Levels page (click a character to change its level),
  2. an import / export of that JSON file (new users can paste a friend's file or their own backup),
  3. automatically: on the end-of-match scoreboard the level badge of *your* row is read and the file corrected when it differs.
"""
import difflib
import json
import time

from PIL import Image, ImageOps

from . import ocr, paths
from .text import norm

KINDS = ("killers", "survivors")
SOURCES = {"killers": paths.KILLERS, "survivors": paths.SURVIVORS}
MAX_LEVEL = 3
REF_H = 1125  # reference height of the measurements below
ROW0, PITCH = 320, 125.4  # centre of the scoreboard's first row and gap between rows (at REF_H)


# ---------- storage ----------
def _read(path, default):
    try:
        return json.loads(path.read_text(encoding="utf8"))
    except Exception:
        return default


def load():
    d = _read(paths.LEVELS, {})
    return {k: {n: max(0, min(MAX_LEVEL, int(v))) for n, v in d.get(k, {}).items()} for k in KINDS}


def history():
    return _read(paths.LEVELS_HISTORY, [])


def _save(levels):
    paths.ensure()
    paths.LEVELS.write_text(json.dumps(levels, ensure_ascii=False, indent=1), encoding="utf8")


def _log_history(kind, name, old, new, src):
    h = history()
    h.append({"t": int(time.time() * 1000), "kind": kind, "n": name, "f": old, "to": new, "src": src})
    paths.LEVELS_HISTORY.write_text(json.dumps(h[-500:], ensure_ascii=False, indent=1), encoding="utf8")


BASE_GAME = "Base Game"  # these characters come with the game: always owned


def characters(kind):
    """Characters of one side from the builds data: [{"name", "short", "portrait", "portrait2", "perks": n, "chapter", "owned"}].
    Empty until `update-db` has run."""
    src = _read(SOURCES[kind], {})
    lost = unowned()[kind]
    out = []
    for c in src.get("killers", []):
        if not c.get("teachables"):
            continue
        short = c.get("short") or c["name"]
        chapter = c.get("chapter") or "Unknown"
        out.append({"name": c["name"], "short": short, "portrait": c.get("portrait"), "portrait2": c.get("portrait2"),
                    "perks": len(c["teachables"]), "chapter": chapter, "owned": chapter == BASE_GAME or short not in lost})
    return out


# ---------- ownership ("do I have this character?") ----------
def unowned():
    d = _read(paths.OWNED, {})
    return {k: set(d.get(k, [])) for k in KINDS}


def _save_unowned(u):
    paths.ensure()
    paths.OWNED.write_text(json.dumps({k: sorted(v) for k, v in u.items()}, ensure_ascii=False, indent=1), encoding="utf8")


def set_owned_many(kind, names, owned):
    """Marks characters as owned / not owned. Base-game characters stay owned. Returns how many changed."""
    u = unowned()
    base = {c["short"] for c in characters(kind) if c["chapter"] == BASE_GAME}
    n = 0
    for name in names:
        if name in base:
            continue
        if owned and name in u[kind]:
            u[kind].discard(name)
            n += 1
        elif not owned and name not in u[kind]:
            u[kind].add(name)
            n += 1
    _save_unowned(u)
    return n


def set_owned(kind, name, owned):
    return bool(set_owned_many(kind, [name], owned))


def set_all_owned(owned):
    return sum(set_owned_many(k, [c["short"] for c in characters(k)], owned) for k in KINDS)


def chapters():
    """The DLC chapters, each with the killers and survivors it brought, and whether you own all / none / some of them."""
    groups = {}
    for kind in KINDS:
        for c in characters(kind):
            g = groups.setdefault(c["chapter"], {"label": c["chapter"], "killers": [], "survivors": [], "base": c["chapter"] == BASE_GAME})
            g[kind].append({"name": c["short"], "owned": c["owned"]})
    out = []
    for g in groups.values():
        flags = [c["owned"] for kind in KINDS for c in g[kind]]
        g["owned"] = "all" if all(flags) else "none" if not any(flags) else "some"
        out.append(g)
    return sorted(out, key=lambda g: (not g["base"], g["label"].lower()))


def set_chapter_owned(label, owned):
    n = 0
    for kind in KINDS:
        n += set_owned_many(kind, [c["short"] for c in characters(kind) if c["chapter"] == label], owned)
    return n


# ---------- backups: the state before every bulk change, to undo a mistake ----------
KEEP_BACKUPS = 20


def snapshot(label):
    """Keeps the current levels and ownership before a bulk change (nothing is stored when it is identical to the last backup)."""
    cur = {"levels": load(), "unowned": {k: sorted(v) for k, v in unowned().items()}}
    b = _read(paths.LEVELS_BACKUPS, [])
    if b and b[-1]["levels"] == cur["levels"] and b[-1]["unowned"] == cur["unowned"]:
        return b[-1]["t"]
    t = int(time.time() * 1000)
    b.append({"t": t, "label": label, **cur})
    paths.ensure()
    paths.LEVELS_BACKUPS.write_text(json.dumps(b[-KEEP_BACKUPS:], ensure_ascii=False), encoding="utf8")
    return t


def backups():
    """Newest first: [{"t", "label", "points" (sum of levels), "characters" (with a level), "unowned"}]."""
    out = []
    for e in reversed(_read(paths.LEVELS_BACKUPS, [])):
        lv = [v for k in KINDS for v in e["levels"].get(k, {}).values()]
        out.append({"t": e["t"], "label": e["label"], "points": sum(lv), "characters": sum(1 for v in lv if v), "unowned": sum(len(e["unowned"].get(k, [])) for k in KINDS)})
    return out


def restore(t):
    """Puts levels and ownership back as they were in backup `t` (the current state is kept as a backup first, so a restore can be undone too)."""
    e = next((x for x in _read(paths.LEVELS_BACKUPS, []) if x["t"] == t), None)
    if not e:
        raise ValueError("that backup no longer exists")
    snapshot("Before restoring an earlier state")
    _save({k: e["levels"].get(k, {}) for k in KINDS})
    _save_unowned({k: set(e["unowned"].get(k, [])) for k in KINDS})
    _log_history("all", "", 0, 0, "restore")
    return True


def set_level(kind, name, level, src="manual"):
    levels = load()
    level = max(0, min(MAX_LEVEL, int(level)))
    old = levels[kind].get(name, 0)
    if old == level:
        return False
    levels[kind][name] = level
    _save(levels)
    _log_history(kind, name, old, level, src)
    return True


def set_many(kind, mapping, src="import"):
    """Sets several levels at once (initial setup / import). Returns how many changed."""
    n = 0
    for name, level in mapping.items():
        n += bool(set_level(kind, name, level, src))
    return n


def import_json(text):
    """Accepts our own export ({"killers": {...}, "survivors": {...}}) or a flat {name: level} dict, matched to known characters by name."""
    data = json.loads(text)
    changed = 0
    lost = data.pop("unowned", None) if isinstance(data, dict) else None
    if isinstance(lost, dict):
        for kind in KINDS:
            names = {_match_name(kind, n) for n in lost.get(kind, [])} - {None}
            everyone = [c["short"] for c in characters(kind)]
            changed += set_owned_many(kind, [n for n in everyone if n in names], False) + set_owned_many(kind, [n for n in everyone if n not in names], True)
    if any(k in data for k in KINDS):
        for kind in KINDS:
            changed += set_many(kind, {_match_name(kind, n): v for n, v in data.get(kind, {}).items() if _match_name(kind, n)})
    else:
        for n, v in data.items():
            for kind in KINDS:
                m = _match_name(kind, n)
                if m:
                    changed += bool(set_level(kind, m, v, "import"))
                    break
    return changed


def reset(kind=None):
    levels = load()
    for k in KINDS if kind is None else [kind]:
        levels[k] = {}
    _save(levels)
    _log_history(kind or "all", "", 0, 0, "reset")


def _match_name(kind, name, cutoff=0.8):
    chars = [c["short"] for c in characters(kind)] + [c["name"] for c in characters(kind)]
    n = norm(name)
    best, score = None, 0
    for c in chars:
        r = difflib.SequenceMatcher(None, n, norm(c)).ratio()
        if r > score:
            best, score = c, r
    if best is None or score < cutoff:
        return None
    return next((c["short"] for c in characters(kind) if best in (c["short"], c["name"])), None)


# ---------- reading the scoreboard ----------
def read_badge(img, row):
    """Number in the level badge of scoreboard row `row` (0-4), or None.

    Windows OCR does not read an isolated digit: the digit is isolated in black on white and repeated three times side by side ("333"), and the first third is kept."""
    k = img.height / REF_H
    c = (ROW0 + PITCH * row) * k
    crop = img.crop((int(66 * k), int(c - 16 * k), int(94 * k), int(c + 16 * k)))
    g = ImageOps.autocontrast(crop.convert("L"))
    for thr in (170, 150, 190):
        b = g.point(lambda v, t=thr: 0 if v > t else 255).resize((g.width * 6, g.height * 6), Image.LANCZOS)
        gap = b.width // 3
        canvas = Image.new("L", (3 * b.width + 2 * gap + 120, b.height + 120), 255)
        for i in range(3):
            canvas.paste(b, (60 + i * (b.width + gap), 60))
        s = "".join(w[0] for ln in ocr.read_words(canvas.convert("RGB"), 1) for w in ln if w[0].isdigit())
        if s and len(s) % 3 == 0:
            return int(s[: len(s) // 3])
    return None


def read_name(img, row):
    """Character name of scoreboard row `row` (the upper-case words at the start of the title line), or ''."""
    k = img.height / REF_H
    c = (ROW0 + PITCH * row) * k
    box = (int(200 * k), int(c - 58 * k), int(700 * k), int(c - 18 * k))
    lines = [ln for ln in ocr.read_words(img.crop(box), 3) if ln]
    if not lines:
        return ""
    out = []
    for w in (w[0] for w in lines[0]):
        if w.isupper() or w.rstrip(".").isupper():
            out.append(w)
        else:
            break
    return " ".join(out)


def _closest(name, keys):
    n = norm(name.upper().removeprefix("THE "))
    best, score = None, 0
    for key in keys:
        r = difflib.SequenceMatcher(None, n, norm(key.upper().removeprefix("THE "))).ratio()
        if r > score:
            best, score = key, r
    return best, score


def sync_from_scoreboard(img, row, analyzer=None, log=print, dry=False):
    """Reads the name and level badge of your row and corrects levels.json when it differs. Returns a one-line report or None."""
    if row is None:
        return None
    n = read_badge(img, row)
    name = read_name(img, row)
    log(f"Level read on your row: badge {n} · name '{name}'")
    if n is None or not name:
        return None
    level = min(MAX_LEVEL, n)
    levels = load()
    names = {k: [c["short"] for c in characters(k)] for k in KINDS}
    if not any(names.values()):
        log("Character list is empty (run update-db): level not saved")
        return None
    kk, ks = _closest(name, names["killers"])
    full = analyzer.resolve_survivor(name) if analyzer else name
    sk, ss = _closest(full, names["survivors"]) if full else (None, 0)
    if max(ks, ss) < 0.8:
        log(f"Character '{name}' not found in the character list: level not updated")
        return None
    kind, key = ("killers", kk) if ks >= ss else ("survivors", sk)
    cur = levels[kind].get(key, 0)
    set_owned(kind, key, True) if not dry else None  # you just played it: you own it
    if cur == level:
        log(f"{key} is already at level {level}")
        return None
    msg = f"{key} level corrected: {cur} -> {level} (from the scoreboard)"
    if dry:
        log("DRY RUN: " + msg)
        return None
    set_level(kind, key, level, "capture")
    set_owned(kind, key, True)  # you just played it: you own it
    log(msg)
    return msg
