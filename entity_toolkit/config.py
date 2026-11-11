"""User settings, stored in ``data/config.json`` (created on first run, editable from the setup page)."""
import json

from . import paths

DEFAULTS = {
    "player": "",                 # your in-game name, as shown on the scoreboard (needed to tick "Me" on NightLight)
    "capture_key": "alt+numpad7",  # one key does everything: players menu -> perks + map, scoreboard -> NightLight upload
    "clear_key": "alt+numpad8",    # removes the perk overlay
    "auto": False,                # automatic mode: Tab reads the players menu and the scoreboard is sent by itself, without the capture key (which keeps working)
    "overlay": True,              # draw the allies' perks over the game's survivor list
    "perk_hover": True,           # show a perk's text when the mouse is over its icon (the game frees the cursor when you are hooked or dead)
    "sounds": True,               # small "ok" / "not ok" sounds
    "upload": True,               # send the scoreboard to NightLight when you press the key on it
    "dry_run": False,             # True: save the scoreboard locally but never send it
    "open_browser": True,         # open the Live page in your default browser when the toolkit starts (so: when the game starts, with autostart)
    "layout": "columns",          # live page layout: "columns" or "list"
    "auto_update_days": 7,        # refresh the database by itself every N days (0 = never)
    "last_update": 0,             # when the whole database was last refreshed (set by the update)
    "setup_done": None,           # first-launch setup finished (None = decide from the data: database present and name set)
    "keep_captures": 100,         # keep the last N screenshots taken with the key (0 = none), the oldest are deleted
    "tray": True,                 # icon in the Windows notification area while the toolkit runs (open the pages, quit)
    "check_version": True,        # once a day, look on GitHub whether a newer Entity Toolkit exists (reads one public file, sends nothing)
    "shrine": True,               # show this week's Shrine of Secrets and flag the perks you do not have (reads NightLight's public list, sends nothing)
    "port": 8765,
}


def load():
    try:
        return {**DEFAULTS, **json.loads(paths.CONFIG.read_text(encoding="utf8"))}
    except Exception:
        return dict(DEFAULTS)


def save(cfg):
    paths.ensure()
    clean = {k: v for k, v in cfg.items() if k in DEFAULTS}
    paths.CONFIG.write_text(json.dumps(clean, indent=1, ensure_ascii=False), encoding="utf8")
    return clean
