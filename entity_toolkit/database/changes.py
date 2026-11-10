"""What an update brought: new (or removed) killers, survivors, perks, add-ons, items, offerings, maps.

`snapshot()` lists what the data folder holds right now; the update takes one before and one after, and `describe()` turns the difference into
plain sentences for the Setup page and the log. On a first install (nothing before) it says nothing: everything would be "new".
"""
import json

from .. import paths


def _load(f):
    try:
        return json.loads(f.read_text(encoding="utf8"))
    except Exception:
        return None


def snapshot():
    snap = {}
    for key, f in (("Killer", paths.KILLERS), ("Survivor", paths.SURVIVORS)):
        d = _load(f)
        if d:
            snap[key] = sorted({c.get("short") or c["name"] for c in d.get("killers", [])})
    d = _load(paths.LOADOUT)
    if d:
        snap["Killer perk"] = sorted(p["name"] for p in d["perks"]["K"])
        snap["Survivor perk"] = sorted(p["name"] for p in d["perks"]["S"])
    d = _load(paths.LOADOUT_EXTRA)
    if d:
        snap["Add-on"] = sorted({f'{a["name"]} ({p["killer"]})' for p in d["powers"] for a in p["addons"]})
        snap["Item"] = sorted(i["name"] for i in d["items"])
        snap["Offering"] = sorted({o["name"] for side in d["offerings"].values() for o in side})
    d = _load(paths.MAPS)
    if d:
        snap["Map"] = sorted(d.get("maps", []))
        snap["Realm"] = sorted(d.get("realms", []))
    return snap


def diff(before, after):
    """[(kind, added names, removed names)] for what changed."""
    out = []
    for kind, names in after.items():
        old = before.get(kind)
        if old is None:
            continue  # nothing there before (first download): not a change
        add, gone = sorted(set(names) - set(old)), sorted(set(old) - set(names))
        if add or gone:
            out.append((kind, add, gone))
    return out


def describe(changes, limit=8):
    """One sentence per kind: "New killer: X" / "3 new add-ons: A, B, C…"."""
    lines = []
    for kind, add, gone in changes:
        plural = lambda n: kind.lower() + ("s" if n != 1 else "")
        if add:
            shown = ", ".join(add[:limit]) + ("…" if len(add) > limit else "")
            lines.append(f"New {kind.lower()}: {shown}" if len(add) == 1 else f"{len(add)} new {plural(len(add))}: {shown}")
        if gone:
            shown = ", ".join(gone[:limit]) + ("…" if len(gone) > limit else "")
            lines.append(f"Removed {kind.lower()}: {shown}" if len(gone) == 1 else f"{len(gone)} {plural(len(gone))} removed: {shown}")
    return lines
