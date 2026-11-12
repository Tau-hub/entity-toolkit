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


def wiki_skins(log=print):
    """The alternate character models of every survivor and killer ("Alternate Character Models" section of each character's wiki page):
    skins that show another name in the game (A2 on Yui Kimura, Jonathan Byers on Steve Harrington...). {"survivors": {character: [names]}, "killers": {...}}."""
    out = {"survivors": {}, "killers": {}}
    for kind, f in (("survivors", paths.SURVIVORS), ("killers", paths.KILLERS)):
        try:
            names = [s["name"] for s in json.loads(f.read_text(encoding="utf8"))["killers"] if s["name"] != "The Troupe"]  # (the "killers" key holds the survivors too)
        except Exception:
            continue
        for n in names:
            try:
                text = api(action="parse", page=n, prop="wikitext", redirects=1)["parse"]["wikitext"]["*"]
            except Exception:
                continue
            m = re.search(r"=== Alternate Character Models ===(.*?)(?:\n== |\Z)", text, re.S)
            skins = re.findall(r"^\* \[\[([^\]|]+)", m.group(1), re.M) if m else []
            if skins:
                out[kind][n] = skins
    if not out["survivors"] and not out["killers"]:
        raise RuntimeError("no alternate character model found (the wiki's layout may have changed)")
    paths.SKINS.write_text(json.dumps(out, ensure_ascii=False), encoding="utf8")
    log(f"Alternate character models: {sum(map(len, out['survivors'].values()))} for survivors, {sum(map(len, out['killers'].values()))} for killers")
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
