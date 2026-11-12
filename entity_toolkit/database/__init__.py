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
    ("maps", "Map and realm names, alternate character models (DbD wiki)"),
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
        "maps": lambda: (maps.wiki_maps(_say), maps.wiki_skins(_say)),
        "nl_maps": lambda: maps.nightlight_maps(_say),
    }
    result = {}
    before = changes.snapshot()
    _say(("Automatic update" if trigger == "automatic" else "Update") + f" started: {len(todo)} step{'s' if len(todo) != 1 else ''}. The lists and texts are read again; only the icons and pictures you do not have yet are downloaded. Nothing is removed unless the sites dropped it.")
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
            try:
                from . import patch
                cfg["db_patch"] = (patch.load() or {}).get("live") or cfg.get("db_patch") or ""
            except Exception:
                pass
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


def nothing_installed():
    return not (paths.LOADOUT.exists() or paths.KILLERS.exists() or paths.MAPS.exists())


def patch_changed(live, cfg, stored):
    """Did the game move to another patch than the one the database was refreshed for? `stored` is the saved patch.json (or None).
    False when either side is unknown: an update is never started on a guess."""
    base = cfg.get("db_patch") or (stored or {}).get("live")
    return bool(live) and bool(base) and live != base


def start_auto_update(log=_log):
    """Background checks, so that nobody has to press "Update database":
     - the very first start downloads everything by itself (the `first_download` setting);
     - at each start, one request to the Steam announcements tells whether the game got a new patch: if so the database is
       refreshed (the `update_on_patch` setting);
     - and it is refreshed anyway when it is older than the chosen number of days (`auto_update_days`)."""
    def loop():
        time.sleep(4)
        try:
            if nothing_installed() and config.load().get("first_download") and not STATE["running"]:
                log("First start: downloading the database in the background (perks, icons, maps, builds)")
                run(trigger="automatic")
        except Exception:
            log(traceback.format_exc())
        time.sleep(56)  # let the program start (and a match begin) before doing anything else
        first = True
        while True:
            try:
                cfg = config.load()
                if first and cfg.get("update_on_patch") and not nothing_installed() and not STATE["running"]:
                    from . import patch
                    live = patch.latest()[0]
                    if patch_changed(live, cfg, patch.load()):
                        log(f"The game is now on patch {live} (the database is for {cfg.get('db_patch') or (patch.load() or {}).get('live')}): refreshing it in the background")
                        run(trigger="automatic")
                if due() and not STATE["running"]:
                    log("Automatic update: the database is older than the chosen delay, refreshing it in the background")
                    run(trigger="automatic")
            except Exception as e:
                log(f"Automatic database check skipped: {e}")
            first = False
            time.sleep(6 * 3600)
    threading.Thread(target=loop, daemon=True, name="auto-update").start()
