"""This week's Shrine of Secrets, and which of its four perks are worth your shards (optional: the `shrine` setting).

The list comes from NightLight's public API (one small request when the week changes, nothing is sent, no token). Each perk is then
compared with your levels: a perk whose character you have not levelled yet is one you do not have, and the Shrine is the cheap way to get it.
"""
import calendar
import json
import threading
import time

from . import config, levels, paths

URL = "https://api.nightlight.gg/v1/shrine"
GOOD = 60  # rating (out of 100) from which a perk you do not have is called out
_lock = threading.Lock()
_last_try = 0


def _utc(text):
    """'2026-11-17T14:59:59' (UTC) -> epoch seconds; 0 when unreadable."""
    try:
        return calendar.timegm(time.strptime(str(text)[:19], "%Y-%m-%dT%H:%M:%S"))
    except Exception:
        return 0


def cached():
    try:
        return json.loads(paths.SHRINE.read_text(encoding="utf8"))
    except Exception:
        return None


def fetch():
    import requests
    d = requests.get(URL, timeout=10, headers={"User-Agent": "entity-toolkit"}).json()["data"]
    out = {"week": d.get("week"), "start": _utc(d.get("start")), "end": _utc(d.get("end")),
           "perks": [{"name": p["name"], "shards": p.get("shards"), "character": p.get("character") or ""} for p in d["perks"]]}
    paths.ensure()
    paths.SHRINE.write_text(json.dumps(out, ensure_ascii=False), encoding="utf8")
    return out


def current(now=None):
    """The saved Shrine while its week is still running, else a fresh one (at most one attempt every 10 minutes); None when unknown."""
    global _last_try
    now = now or time.time()
    c = cached()
    if c and c.get("end", 0) > now:
        return c
    if not config.load().get("shrine"):
        return None
    with _lock:
        if now - _last_try < 600:
            return None
        _last_try = now
    try:
        return fetch()
    except Exception:
        return None


def _key(name):
    return "".join(ch for ch in str(name).lower() if ch.isalnum())


def describe(shrine, perks, lv):
    """Adds what the toolkit knows to each Shrine perk: side, icon, rating, its character and your level on that character.

    `perks` is {"K": [...], "S": [...]} from the perk database, `lv` is {"killers": {name: level}, "survivors": {...}}.
    `have` is True when the character is levelled (the perk is already in your bloodwebs), `worth` when you do not have it and it rates well.
    """
    index = {_key(p["name"]): (side, p) for side in ("K", "S") for p in perks.get(side, [])}
    out = []
    for s in shrine["perks"]:
        side, p = index.get(_key(s["name"]), (None, {}))
        kind = {"K": "killers", "S": "survivors"}.get(side)
        owner = p.get("owner") or ""
        level = int((lv.get(kind) or {}).get(owner, 0) or 0) if kind and owner else 0
        have = bool(side) and (not owner or level >= 1)
        note = p.get("note")
        out.append({"name": p.get("name") or s["name"], "side": side, "icon": p.get("icon"), "desc": p.get("desc", ""), "note": note, "shards": s.get("shards"),
                    "owner": owner or s.get("character", ""), "level": level, "have": have, "worth": bool(side) and not have and (note or 0) >= GOOD})
    return out


def info():
    """For the pages: {"week", "end", "perks": [...], "worth": n} or None when the Shrine is off or could not be read."""
    if not config.load().get("shrine"):
        return None
    s = current()
    if not s:
        return None
    try:
        perks = json.loads(paths.LOADOUT.read_text(encoding="utf8"))["perks"]
    except Exception:
        perks = {}
    rows = describe(s, perks, levels.load())
    return {"week": s["week"], "end": s["end"], "perks": rows, "worth": sum(r["worth"] for r in rows)}


def summary():
    """The little the navigation bar needs, from the saved file only (never waits for the network)."""
    c = cached()
    if not c or c.get("end", 0) <= time.time() or not config.load().get("shrine"):
        return None
    i = info()
    return i and {"week": i["week"], "worth": {side: [r["name"] for r in i["perks"] if r["worth"] and r["side"] == side] for side in ("K", "S")}}


def start(log):
    """Background: reads the Shrine shortly after the start, then looks every hour whether the week changed."""
    def loop():
        time.sleep(30)
        while True:
            try:
                before = (cached() or {}).get("week")
                s = current()
                if s and s["week"] != before:
                    i = info()
                    good = [r["name"] for r in i["perks"] if r["worth"]] if i else []
                    log("Shrine of Secrets: " + ", ".join(p["name"] for p in s["perks"]) + (f" - worth a look: {', '.join(good)}" if good else ""))
            except Exception as e:
                log(f"Shrine check skipped: {e}")
            time.sleep(3600)
    threading.Thread(target=loop, daemon=True, name="shrine").start()
