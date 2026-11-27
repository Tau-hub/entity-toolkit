"""Is the database complete? The game's own patch notes say what is new ("New Killer: ...", "New Survivor: ...", "New Map: ..."); each of
these names must be in the data after an update. The community sites can be days late, and a site can change its layout: without this
check, an update that missed a whole character would still say that everything went well.
"""
import json
import re

from .. import paths
from ..text import norm

ANNOUNCED = re.compile(r"\bNew (Killer|Survivor|Map)\s*:\s*([^\[\]\r\n<]{3,60})")


PERKS = re.compile(r"New (Killer|Survivor) Perks\s*:(.*?)(?=\[h[23]\]|$)", re.S)
# a perk: a list item that is only a name ("Name:", in bold or not) followed by its own list
PERK = re.compile(r"\[\*\]\s*\[p\]\s*(?:\[b\]\s*)*([^\[\]\r\n:]{3,40}?)\s*(?:\[/b\]\s*)*:?\s*(?:\[/b\]\s*)*\[/p\]\s*\[list\]")
SMALL = {"a", "an", "and", "as", "at", "for", "from", "in", "of", "on", "or", "the", "to", "with"}
CHAPTER = re.compile(r"^\s*(\d+)\.(\d+)\.")


def _is_name(s):
    """"Best Gift Ever", not "Whenever you take a hit": a short title, every important word capitalised."""
    words = s.split()
    return 0 < len(words) <= 6 and all(w[0].isupper() or w[0].isdigit() or w.lower() in SMALL or ":" in w for w in words)


def _new_in(text):
    out = [[kind, name.strip(" .*_")] for kind, name in ANNOUNCED.findall(text)]
    for side, block in PERKS.findall(text):
        out += [[f"{side} perk", name.strip()] for name in PERK.findall(block) if _is_name(name.strip())]
    return [p for p in out if p[1]]


def upcoming(items, version):
    """[[kind, name]] shown on a PTB (test server) of a later chapter than the live one: the community sites add them early, and they
    must stay out of the database until they are in the game."""
    live = tuple(map(int, CHAPTER.match(version).groups()))
    released, out = announced(items, version), []
    for n in items:
        title = n.get("title", "")
        m = CHAPTER.match(title)
        if not m or "PTB" not in title.upper() or tuple(map(int, m.groups())) <= live:
            continue
        out += [p for p in _new_in(n.get("contents", "")) if p not in out and p not in released]
    return out


def not_released(name, *kinds):
    """Is this name (of one of these kinds) only on the PTB for now? Reads what the patch step stored."""
    try:
        later = json.loads(paths.PATCH.read_text(encoding="utf8")).get("upcoming") or []
    except Exception:
        return False
    return any(kind in kinds and _same(name, [n]) for kind, n in later)


def announced(items, version):
    """[[kind, name]] announced as new by the live patch notes of this chapter (all the notes of the same major.minor version, PTB left out)."""
    chapter = ".".join(version.split(".")[:2]) + "."
    out = []
    for n in items:
        title = n.get("title", "").strip()
        if not title.startswith(chapter) or "PTB" in title.upper():
            continue
        for p in _new_in(n.get("contents", "")):
            if p not in out:
                out.append(p)
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
    sides = _load(paths.LOADOUT).get("perks", {})
    perks = {kind: [p["name"] for p in sides.get(side, [])] for kind, side in (("Killer perk", "K"), ("Survivor perk", "S"))}
    out = []
    if killers and not _load(paths.KILLERS).get("nlPeriod"):  # the site did not answer, or changed: the ratings are Otzdarva's alone
        out.append("NightLight's perk statistics")
    for kind, name in new or []:
        if kind in perks:
            if not _same(name, perks[kind]):
                out.append(f"{kind.lower()} {name}")
            continue
        if kind == "Map":
            if not _same(name, maps):
                out.append(f"map {name}")
            continue
        found = next((c for c in (killers if kind == "Killer" else survivors) if _same(name, [c.get("name"), c.get("short")])
                      or str(c.get("name", "")).lower().startswith(name.lower() + " ")), None)  # the notes may give the first name only
        if not found:
            out.append(f"{kind.lower()} {name}")
            continue
        if len(found.get("teachables", [])) < 3:
            out.append(f"the perks of {name}")
        if kind == "Killer" and not any(_same(name, [p.get("killer"), *p.get("names", [])]) for p in powers):
            out.append(f"the power and add-ons of {name}")
    return out
