"""`update-db`: downloads everything the toolkit needs from the community sites into the data folder.

Run it once after installing, and again after a game patch (new perks, new maps, new ratings). Each step is independent and
reports success or failure on its own, so one site being down does not block the others.
"""
import threading
import time
import traceback

from .. import config, paths
from ..log import log as _log
from . import changes

STEPS = [
    ("patch", "Current game patch (Steam announcements)"),
    ("builds", "Builds, tier list and ratings (Otzdarva, NightLight)"),
    ("perks", "Perk names, descriptions and icons (DbD wiki)"),
    ("loadout", "Random-loadout data: powers, add-ons, items, offerings (DbD wiki)"),
    ("maps", "Map and realm names (DbD wiki)"),
    ("nl_maps", "NightLight map ids"),
]

STATE = {"running": False, "step": None, "steps": {}, "log": [], "finished": None, "changes": [], "trigger": None, "todo": []}
ON_FINISH = []  # callbacks run after every update (the running program reloads what it keeps in memory)
_lock = threading.Lock()


def _say(msg):
    _log(msg)
    with _lock:
        STATE["log"] = (STATE["log"] + [f"{time.strftime('%H:%M:%S')} {msg}"])[-200:]


def status():
    """What is installed and what the last run did (for the Setup page)."""
    with _lock:
        s = dict(STATE, steps=dict(STATE["steps"]), log=list(STATE["log"]))
    s["installed"] = {
        "perks": paths.LOADOUT.exists() and paths.ICONS.exists() and any(paths.ICONS.iterdir()),
        "patch": paths.PATCH.exists(),
        "builds": paths.KILLERS.exists() and paths.SURVIVORS.exists(),
        "loadout": paths.LOADOUT_EXTRA.exists(),
        "maps": paths.MAPS.exists(),
        "nl_maps": paths.NL_MAPS.exists(),
    }
    for key in s["installed"]:
        f = {"patch": paths.PATCH, "perks": paths.LOADOUT, "builds": paths.KILLERS, "loadout": paths.LOADOUT_EXTRA, "maps": paths.MAPS, "nl_maps": paths.NL_MAPS}[key]
        s.setdefault("updated", {})[key] = int(f.stat().st_mtime) if f.exists() else None
    return s


def run(only=None, refresh=False, trigger="manual"):
    """Runs the steps (all of them, or the ones listed in `only`). Returns {step: error or None}."""
    from . import builds, loadout, maps, patch, perks
    todo = [k for k, _ in STEPS if not only or k in only]
    with _lock:
        if STATE["running"]:
            return {}
        STATE.update(running=True, step=None, steps={}, log=[], finished=None, changes=[], trigger=trigger, todo=list(todo))
    fns = {
        "patch": lambda: patch.main(_say),
        "builds": lambda: builds.main(_say),
        "perks": lambda: perks.main(_say, refresh=refresh),
        "loadout": lambda: loadout.main(_say, refresh=refresh),
        "maps": lambda: maps.wiki_maps(_say),
        "nl_maps": lambda: maps.nightlight_maps(_say),
    }
    result = {}
    before = changes.snapshot()
    _say(("Automatic update" if trigger == "automatic" else "Update") + f" started: {len(todo)} step{'s' if len(todo) != 1 else ''}. Perks, icons and add-ons are downloaded again; nothing is removed unless the sites dropped it.")
    try:
        for n, key in enumerate(todo, 1):  # builds first: the perk and loadout steps read their ratings / tiers
            with _lock:
                STATE["step"] = key
            _say(f"== [{n}/{len(todo)}] {dict(STEPS)[key]} ==")
            try:
                fns[key]()
                result[key] = None
            except Exception as e:
                result[key] = f"{type(e).__name__}: {e}"
                _say(f"!! {key} failed: {e}")
                _log(traceback.format_exc())
            with _lock:
                STATE["steps"][key] = result[key] or "ok"
    finally:
        found = changes.describe(changes.diff(before, changes.snapshot()))
        with _lock:
            STATE.update(running=False, step=None, finished=int(time.time()), changes=found)
        if found:
            _say("What is new since the last update:")
            for line in found:
                _say("  • " + line)
        elif before:
            _say("Nothing new: no killer, survivor, perk, add-on, item, offering or map was added or removed.")
        ok = not any(result.values())
        if ok and not only:
            cfg = config.load()
            cfg["last_update"] = int(time.time())
            config.save(cfg)
        _say("Update finished." if ok else "Update finished with errors (see above).")
        for cb in ON_FINISH:
            try:
                cb()
            except Exception:
                _log(traceback.format_exc())
    return result


def run_async(only=None, refresh=False, trigger="manual"):
    if STATE["running"]:
        return False
    threading.Thread(target=run, args=(only, refresh, trigger), daemon=True).start()
    return True


def last_update():
    """When the whole database was last refreshed (0 = never). Falls back to the perk file's date for data downloaded before this was recorded."""
    t = config.load().get("last_update") or 0
    if not t and paths.LOADOUT.exists():
        t = int(paths.LOADOUT.stat().st_mtime)
    return t


def due():
    days = config.load().get("auto_update_days") or 0
    t = last_update()
    return bool(days) and bool(t) and time.time() - t > days * 86400  # never before the first manual download


def start_auto_update(log=_log):
    """Background check: refreshes the database by itself when the chosen number of days has passed. Costs one clock comparison every few hours."""
    def loop():
        time.sleep(60)  # let the program start (and a match begin) before doing anything
        while True:
            try:
                if due() and not STATE["running"]:
                    log("Automatic update: the database is older than the chosen delay, refreshing it in the background")
                    run(trigger="automatic")
            except Exception:
                log(traceback.format_exc())
            time.sleep(6 * 3600)
    threading.Thread(target=loop, daemon=True, name="auto-update").start()
