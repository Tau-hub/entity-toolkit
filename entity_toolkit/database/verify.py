"""Is the database complete? The game's own patch notes say what is new ("New Killer: ...", "New Survivor: ...", "New Map: ..."); each of
these names must be in the data after an update. The community sites can be days late, and a site can change its layout: without this
check, an update that missed a whole character would still say that everything went well.
"""
import json
import re

from .. import paths
from ..text import norm

ANNOUNCED = re.compile(r"\bNew (Killer|Survivor|Map)\s*:\s*([^\[\]\r\n<]{3,60})")


def announced(items, version):
    """[[kind, name]] announced as new by the live patch notes of this chapter (all the notes of the same major.minor version, PTB left out)."""
    chapter = ".".join(version.split(".")[:2]) + "."
    out = []
    for n in items:
        title = n.get("title", "").strip()
        if not title.startswith(chapter) or "PTB" in title.upper():
            continue
        for kind, name in ANNOUNCED.findall(n.get("contents", "")):
            pair = [kind, name.strip(" .*_")]
            if pair[1] and pair not in out:
                out.append(pair)
    return out


def _load(f):
    try:
        return json.loads(f.read_text(encoding="utf8"))
    except Exception:
        return {}


def _same(wanted, names):
    key = lambda s: norm(re.sub(r"^the\s+", "", s.strip(), flags=re.I))
    return any(key(wanted) == key(n) for n in names if n)


def missing(new):
    """Plain sentences for what the patch notes announce and the data does not hold (completely). [] when all is there."""
    killers = _load(paths.KILLERS).get("killers", [])
    survivors = _load(paths.SURVIVORS).get("killers", [])  # (the "killers" key holds the survivors too)
    powers = _load(paths.LOADOUT_EXTRA).get("powers", [])
    maps = _load(paths.MAPS).get("maps", [])
    out = []
    for kind, name in new or []:
        if kind == "Map":
            if not _same(name, maps):
                out.append(f"map {name}")
            continue
        found = next((c for c in (killers if kind == "Killer" else survivors) if _same(name, [c.get("name"), c.get("short")])), None)
        if not found:
            out.append(f"{kind.lower()} {name}")
            continue
        if len(found.get("teachables", [])) < 3:
            out.append(f"the perks of {name}")
        if kind == "Killer" and not any(_same(name, [p.get("killer"), *p.get("names", [])]) for p in powers):
            out.append(f"the power and add-ons of {name}")
    return out
