"""Where things live. Everything the user generates or owns goes in one git-ignored folder (``data/`` by default)."""
import os
import sys
from pathlib import Path

FROZEN = bool(getattr(sys, "frozen", False))  # True in the packaged EntityToolkit.exe (see packaging/), False when run with Python
if FROZEN:
    ROOT = Path(sys.executable).resolve().parent  # the folder holding EntityToolkit.exe: data/ is created next to it
    BUNDLE = Path(getattr(sys, "_MEIPASS", ROOT))  # where the packaged pages and sounds are
else:
    ROOT = BUNDLE = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("ENTITY_TOOLKIT_DATA", ROOT / "data"))
WEB = BUNDLE / "web"
SOUNDS = BUNDLE / "sounds"
SEED = BUNDLE / "seed"  # the database shipped with the toolkit (see database/seed.py)

ICONS = DATA / "icons"                      # perk icons downloaded from the DbD wiki by `update-db`
LOADOUT = DATA / "loadout_data.json"        # perks (name, icon, description, rating) used for recognition
LOADOUT_EXTRA = DATA / "loadout_extra.json"  # killer powers, add-ons, items, offerings (random loadout page)
KILLERS = DATA / "killers.json"             # killer builds / add-on tiers
SURVIVORS = DATA / "survivors.json"         # survivor perk ratings
SURVIVOR_BUILDS = DATA / "survivor_builds.json"
PATCH = DATA / "patch.json"                 # the game's current live patch (Steam news)
MAPS = DATA / "maps.json"                   # map and realm names (wiki)
NL_MAPS = DATA / "nl_maps.json"             # NightLight map ids
SKINS = DATA / "skins.json"                 # names of the alternate character models (skins that rename a character, e.g. A2 for Yui Kimura)
LEVELS = DATA / "levels.json"               # character levels {"killers": {...}, "survivors": {...}}
LEVELS_HISTORY = DATA / "levels_history.json"
LEVELS_BACKUPS = DATA / "levels_backups.json"  # states kept before every bulk change, so a mistake can be undone
PERK_TYPES = DATA / "perk_types.json"       # your corrections of the automatic perk types {"Perk": ["type id", ...]}
MYBUILDS = DATA / "my_builds.json"           # the builds you saved in the Build creator
OWNED = DATA / "owned.json"                 # characters you do NOT own: {"killers": [...], "survivors": [...]} (everything is owned by default)
SHRINE = DATA / "shrine.json"               # this week's Shrine of Secrets (NightLight's public list)
CONFIG = DATA / "config.json"
OVERLAY_LAYOUT = DATA / "overlay_layout.json"
LAST_MATCH = DATA / "last_match.json"       # map remembered between the players menu and the scoreboard
LOG_FILE = DATA / "entity_toolkit.log"
CAPTURES = DATA / "captures"              # the last screenshots taken with the capture key (a rotation, see captures.py)
DEBUG = DATA / "debug"                      # last captures kept to diagnose recognition problems
UPLOADS = DATA / "uploads"                  # scoreboards sent to NightLight
NL_PROFILE = DATA / "nightlight_profile"    # Edge profile holding your NightLight session
NL_TOKEN = DATA / "nightlight_token.txt"    # your NightLight API token (never leaves this folder, sent only to api.nightlight.gg)


def ensure():
    for p in (DATA, DEBUG, UPLOADS):
        p.mkdir(parents=True, exist_ok=True)
