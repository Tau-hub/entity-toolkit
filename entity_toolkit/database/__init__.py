"""`update-db`: downloads everything the toolkit needs from the community sites into the data folder.

Run it once after installing, and again after a game patch (new perks, new maps, new ratings). Each step is independent and
reports success or failure on its own, so one site being down does not block the others.
"""
import json
import threading
import time
import traceback

from .. import config, paths
from ..log import log as _log
from . import changes, verify

STEPS = [
    ("patch", "Current game patch (Steam announcements)"),
    ("builds", "Builds, tier list and ratings (Otzdarva, NightLight)"),
    ("perks", "Perk names, descriptions and icons (DbD wiki)"),
    ("loadout", "Random-loadout data: powers, add-ons, items, offerings (DbD wiki)"),
    ("maps", "Map and realm names, alternate character models (DbD wiki)"),
    ("nl_maps", "NightLight map ids"),
]

STATE = {"running": False, "step": None, "steps": {}, "log": [], "finished": None, "changes": [], "missing": [], "trigger": None, "todo": []}
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
    s["news"] = news()
    s["missing"] = config.load().get("db_missing") or []
    return s


def news():
    """The last update that brought something: {"at", "patch", "lines"} or None. Kept on disk: a later update that finds nothing, or a
    restart, must not hide it."""
    try:
        return json.loads((paths.DATA / "updates.json").read_text(encoding="utf8"))
    except Exception:
        return None


def check_complete():
    """What the patch notes announce and the database does not have yet (see verify.py). Remembered: it is tried again until it is there."""
    from . import patch
    gone = verify.missing((patch.load() or {}).get("new"))
    cfg = config.load()
    cfg["db_missing"], cfg["db_missing_tried"] = gone, int(time.time())
    config.save(cfg)
    return gone


def run(only=None, refresh=False, trigger="manual"):
    """Runs the steps (all of them, or the ones listed in `only`). Returns {step: error or None}."""
    from . import builds, loadout, maps, patch, perks
    todo = [k for k, _ in STEPS if not only or k in only]
    with _lock:
        if STATE["running"]:
            return {}
        STATE.update(running=True, step=None, steps={}, log=[], finished=None, changes=[], missing=[], trigger=trigger, todo=list(todo))
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
        after = changes.snapshot()
        found = changes.describe(changes.diff(before, after)) + changes.describe_reworked(changes.reworked(before, after))
        with _lock:
            STATE.update(running=False, step=None, finished=int(time.time()), changes=found)
        if found:
            _say("What is new since the last update:")
            for line in found:
                _say("  • " + line)
        elif before:
            _say("Nothing changed since the previous update.")
            last = news()
            if last:
                _say(f"The last changes, on {time.strftime('%Y-%m-%d %H:%M', time.localtime(last['at']))}: " + " · ".join(last["lines"]))
        if found:
            try:
                from . import patch
                paths.ensure()
                record = {"at": int(time.time()), "patch": (patch.load() or {}).get("live", ""), "lines": found}
                (paths.DATA / "updates.json").write_text(json.dumps(record, ensure_ascii=False), encoding="utf8")
            except Exception:
                _log(traceback.format_exc())
        try:
            gone = check_complete()
            with _lock:
                STATE["missing"] = gone
            if gone:
                _say("!! Announced in the patch notes but NOT in the database yet: " + ", ".join(gone) + ". The community sites may be late: it is tried again every few hours.")
        except Exception:
            _log(traceback.format_exc())
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


PATCH_EVERY = 3600       # one small request to the Steam announcements: the toolkit can stay in the notification area for days
RETRY_EVERY = 3 * 3600   # while something announced is missing from the database


LOOK_NOW = threading.Event()  # set when the game starts: the patch is looked at without waiting for the next hour


def look_now():
    LOOK_NOW.set()


def next_action(now, cfg, live, stored, is_due):
    """What the background loop has to do now: "patch", "missing", "age" or None. `live` is None when the patch was not asked this time."""
    if live and patch_changed(live, cfg, stored):
        return "patch"
    if cfg.get("update_on_patch") and cfg.get("db_missing") and now - (cfg.get("db_missing_tried") or 0) >= RETRY_EVERY:
        return "missing"
    return "age" if is_due else None


def start_auto_update(log=_log):
    """Background checks, so that nobody has to press "Update database":
     - the very first start downloads everything by itself (the `first_download` setting);
     - at each start, at each game launch and every hour, the Steam announcements tell whether the game got a new patch: if so the database is
       refreshed (the `update_on_patch` setting);
     - when the patch notes announce something the database does not have yet, it is tried again every few hours;
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
        looked_at, checked = 0.0, False
        while True:
            try:
                from . import patch
                cfg = config.load()
                if not nothing_installed() and not STATE["running"]:
                    if not checked and cfg.get("update_on_patch"):  # data from an older version of the toolkit was never verified
                        if (patch.load() or {}).get("new") is None:
                            patch.main(log)
                        check_complete()
                        checked, cfg = True, config.load()
                    live, now = None, time.time()  # wall clock: it also moves while the computer sleeps
                    if cfg.get("update_on_patch") and (LOOK_NOW.is_set() or now - looked_at >= PATCH_EVERY):
                        LOOK_NOW.clear()
                        live, looked_at = patch.latest()[0], now
                    action = next_action(now, cfg, live, patch.load(), due())
                    if action == "patch":
                        log(f"The game is now on patch {live} (the database is for {cfg.get('db_patch') or (patch.load() or {}).get('live')}): refreshing it in the background")
                    elif action == "missing":
                        log("Still missing from the database: " + ", ".join(cfg["db_missing"]) + ". Trying again")
                    elif action == "age":
                        log("Automatic update: the database is older than the chosen delay, refreshing it in the background")
                    if action:
                        run(trigger="automatic")
            except Exception as e:
                log(f"Automatic database check skipped: {e}")
                looked_at = time.time() - PATCH_EVERY + 600  # no network (just woken up?): again in ten minutes
            time.sleep(60)
    threading.Thread(target=loop, daemon=True, name="auto-update").start()
