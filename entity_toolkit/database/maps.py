"""Map and realm names (wiki) and NightLight's map ids (read from the site's own front-end bundle)."""
import json
import re
import urllib.request

from .. import paths
from .perks import BROWSER_UA, api

NL = "https://nightlight.gg"


def wiki_maps(log=print):
    out = {}
    for key, cat in (("maps", "Category:Maps"), ("realms", "Category:Realms")):
        r = api(action="query", list="categorymembers", cmtitle=cat, cmlimit=500)
        out[key] = [x["title"] for x in r["query"]["categorymembers"]]
    paths.ensure()
    paths.MAPS.write_text(json.dumps(out, ensure_ascii=False), encoding="utf8")
    log(f"Maps: {len(out['maps'])} maps, {len(out['realms'])} realms")
    return out


def _get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": BROWSER_UA}), timeout=60).read().decode("utf8", "replace")


def nightlight_maps(log=print):
    """{id: name} of NightLight's maps, found in the JavaScript of its /maps page (entries look like {id:67,n:`Trickster's Delusion`,r:`Sleepless District`...)."""
    page = _get(NL + "/maps")
    found = {}
    for js in sorted(set(re.findall(r"/assets/[\w\-.]+\.js", page))):
        try:
            txt = _get(NL + js)
        except Exception:
            continue
        for mid, name in re.findall(r"\{id:(\d+),n:`([^`]+)`,r:`[^`]*`", txt):
            found[mid] = name
        if len(found) >= 30:
            break
    if not found:
        raise RuntimeError("NightLight map ids not found (the site's layout may have changed)")
    paths.NL_MAPS.write_text(json.dumps(found, ensure_ascii=False, indent=0), encoding="utf8")
    log(f"NightLight maps: {len(found)} ids")
    return found
