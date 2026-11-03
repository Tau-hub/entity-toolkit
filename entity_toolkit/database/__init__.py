"""`update-db`: downloads everything the toolkit needs from the community sites into the data folder.

Run it once after installing, and again after a game patch (new perks, new maps, new ratings). Each step is independent and
reports success or failure on its own, so one site being down does not block the others.
"""
import threading
import time
import traceback

from .. import paths
from ..log import log as _log

STEPS = [
    ("patch", "Current game patch (Steam announcements)"),
    ("builds", "Builds, tier list and ratings (Otzdarva, NightLight)"),
    ("perks", "Perk names, descriptions and icons (DbD wiki)"),
    ("loadout", "Random-loadout data: powers, add-ons, items, offerings (DbD wiki)"),
    ("maps", "Map and realm names (DbD wiki)"),
    ("nl_maps", "NightLight map ids"),
]

STATE = {"running": False, "step": None, "steps": {}, "log": [], "finished": None}
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


def run(only=None, refresh=False):
    """Runs the steps (all of them, or the ones listed in `only`). Returns {step: error or None}."""
    from . import builds, loadout, maps, patch, perks
    todo = [k for k, _ in STEPS if not only or k in only]
    with _lock:
        if STATE["running"]:
            return {}
        STATE.update(running=True, step=None, steps={}, log=[], finished=None)
    fns = {
        "patch": lambda: patch.main(_say),
        "builds": lambda: builds.main(_say),
        "perks": lambda: perks.main(_say, refresh=refresh),
        "loadout": lambda: loadout.main(_say, refresh=refresh),
        "maps": lambda: maps.wiki_maps(_say),
        "nl_maps": lambda: maps.nightlight_maps(_say),
    }
    result = {}
    try:
        for key in todo:  # builds first: the perk and loadout steps read their ratings / tiers
            with _lock:
                STATE["step"] = key
            _say(f"== {dict(STEPS)[key]} ==")
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
        with _lock:
            STATE.update(running=False, step=None, finished=int(time.time()))
        _say("Update finished." if not any(result.values()) else "Update finished with errors (see above).")
    return result


def run_async(only=None, refresh=False):
    if STATE["running"]:
        return False
    threading.Thread(target=run, args=(only, refresh), daemon=True).start()
    return True
