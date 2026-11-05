"""User settings, stored in ``data/config.json`` (created on first run, editable from the setup page)."""
import json

from . import paths

DEFAULTS = {
    "player": "",                 # your in-game name, as shown on the scoreboard (needed to tick "Me" on NightLight)
    "capture_key": "alt+numpad7",  # one key does everything: players menu -> perks + map, scoreboard -> NightLight upload
    "clear_key": "alt+numpad8",    # removes the perk overlay
    "overlay": True,              # draw the allies' perks over the game's survivor list
    "perk_hover": True,           # show a perk's text when the mouse is over its icon (the game frees the cursor when you are hooked or dead)
    "sounds": True,               # small "ok" / "not ok" sounds
    "upload": True,               # send the scoreboard to NightLight when you press the key on it
    "dry_run": False,             # True: save the scoreboard locally but never send it
    "open_browser": True,         # open the live page when the program starts
    "layout": "columns",          # live page layout: "columns" or "list"
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
