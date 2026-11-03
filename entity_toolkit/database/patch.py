"""The game's current live patch, from the Steam announcements of Dead by Daylight (public feed, no key needed).

Otzdarva's ratings and builds are for the patch his site was last updated for, which can lag the game by a few days: this step tells you
which patch the game is on, so the pages can show both.
"""
import json
import re
import time
import urllib.request

from .. import paths

FEED = "https://api.steampowered.com/ISteamNews/GetNewsForApp/v2/?appid=381210&count=60&maxlength=0"
VERSION = re.compile(r"^\s*(\d+\.\d+\.\d+[a-z]?)(?![A-Za-z0-9])")


def pick(items):
    """(version, title, date) of the newest live patch announcement: a title that starts with a version number and is not a PTB."""
    best = None
    for n in items:
        m = VERSION.match(n["title"])
        if m and "PTB" not in n["title"].upper() and (best is None or n["date"] > best[2]):
            best = (m.group(1), n["title"].strip(), n["date"])
    if not best:
        raise RuntimeError("no live patch found in the Steam announcements")
    return best


def latest():
    req = urllib.request.Request(FEED, headers={"User-Agent": "Mozilla/5.0"})
    return pick(json.loads(urllib.request.urlopen(req, timeout=30).read().decode("utf8", "replace"))["appnews"]["newsitems"])


def main(log=print):
    version, title, date = latest()
    paths.ensure()
    paths.PATCH.write_text(json.dumps({"live": version, "title": title, "date": date, "fetched": int(time.time())}), encoding="utf8")
    log(f"Game patch: {version} ({title}, {time.strftime('%Y-%m-%d', time.localtime(date))})")
    return version


def load():
    try:
        return json.loads(paths.PATCH.read_text(encoding="utf8"))
    except Exception:
        return None
