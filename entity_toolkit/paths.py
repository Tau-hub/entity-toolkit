"""Where things live. Everything the user generates or owns goes in one git-ignored folder (``data/`` by default)."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("ENTITY_TOOLKIT_DATA", ROOT / "data"))
WEB = ROOT / "web"
SOUNDS = ROOT / "sounds"

ICONS = DATA / "icons"                      # perk icons downloaded from the DbD wiki by `update-db`
LOADOUT = DATA / "loadout_data.json"        # perks (name, icon, description, rating) used for recognition
LOADOUT_EXTRA = DATA / "loadout_extra.json"  # killer powers, add-ons, items, offerings (random loadout page)
KILLERS = DATA / "killers.json"             # killer builds / add-on tiers
SURVIVORS = DATA / "survivors.json"         # survivor perk ratings
SURVIVOR_BUILDS = DATA / "survivor_builds.json"
PATCH = DATA / "patch.json"                 # the game's current live patch (Steam news)
MAPS = DATA / "maps.json"                   # map and realm names (wiki)
NL_MAPS = DATA / "nl_maps.json"             # NightLight map ids
LEVELS = DATA / "levels.json"               # character levels {"killers": {...}, "survivors": {...}}
LEVELS_HISTORY = DATA / "levels_history.json"
PERK_TYPES = DATA / "perk_types.json"       # your corrections of the automatic perk types {"Perk": ["type id", ...]}
MYBUILDS = DATA / "my_builds.json"           # the builds you saved in the Build creator
OWNED = DATA / "owned.json"                 # characters you do NOT own: {"killers": [...], "survivors": [...]} (everything is owned by default)
CONFIG = DATA / "config.json"
OVERLAY_LAYOUT = DATA / "overlay_layout.json"
LAST_MATCH = DATA / "last_match.json"       # map remembered between the players menu and the scoreboard
LOG_FILE = DATA / "entity_toolkit.log"
DEBUG = DATA / "debug"                      # last captures kept to diagnose recognition problems
UPLOADS = DATA / "uploads"                  # scoreboards sent to NightLight
NL_PROFILE = DATA / "nightlight_profile"    # Edge profile holding your NightLight session
NL_TOKEN = DATA / "nightlight_token.txt"    # your NightLight API token (never leaves this folder, sent only to api.nightlight.gg)


def ensure():
    for p in (DATA, DEBUG, UPLOADS):
        p.mkdir(parents=True, exist_ok=True)
