"""Random-loadout data from the Dead by Daylight wiki: killer powers, add-ons, items and offerings (perks come from perks.py).

Writes data/loadout_extra.json and downloads the icons into data/icons/. Run after `builds` and `perks` (it reads killers.json for add-on tiers and killer aliases).
"""
import difflib
import json
import re
import time
import urllib.parse
from concurrent.futures import ThreadPoolExecutor

from .. import paths
from ..text import norm
from .perks import api, fetch_icon, get, resolve_urls, wiki_rows, WIKI

POOLS = {"1": "Keys", "2": "Firecrackers", "3": "Flashlights", "4": "Limited", "5": "Maps", "6": "Med-Kits", "7": "Toolboxes", "8": "Fog Vials"}


def parse_table(lua, name):
    """[(name, {simple fields}, section)] for p.<name> = { ... } of the wiki's Lua module."""
    start = lua.index(f"p.{name} = {{")
    end = lua.index(f"p.{name}Count", start)
    rows, section = [], ""
    for line in lua[start:end].splitlines():
        s = line.strip()
        m = re.match(r"--\s*(.+?)\s*-*$", s)
        if m and not s.startswith('["'):
            section = m.group(1)
            continue
        m = re.match(r'\["(.+?)"\]\s*=\s*\{(.*)\}\s*,?\s*$', s)
        if not m:
            continue
        body = re.sub(r"tags\s*=\s*\{[^}]*\}", "", m.group(2))
        f = {k: v.strip("\"'") for k, v in re.findall(r"(\w+)\s*=\s*(\"[^\"]*\"|'[^']*'|[\w.+-]+)", body)}
        rows.append((m.group(1), f, section))
    return rows


def lookup(rows, name):
    return rows.get(norm(name)) or rows.get(norm(re.sub(r"\s*\(.*?\)\s*$", "", name)))


def power_extracts(names):
    out = {}
    for i in range(0, len(names), 20):
        r = api(action="query", prop="extracts", exintro=1, explaintext=1, exlimit=20, titles="|".join(names[i:i + 20]))
        for pg in r.get("query", {}).get("pages", {}).values():
            if pg.get("extract"):
                out[pg["title"]] = re.sub(r"\n{2,}", "\n", pg["extract"]).strip()
        time.sleep(0.5)
    return out


def power_icons():
    names, cont = [], None
    while True:
        p = {"action": "query", "list": "allimages", "aiprefix": "IconPowers_", "ailimit": 500}
        if cont:
            p["aicontinue"] = cont
        r = api(**p)
        names += [x["name"] for x in r["query"]["allimages"]]
        cont = r.get("continue", {}).get("aicontinue")
        if not cont:
            return {norm(n[len("IconPowers_"):].rsplit(".", 1)[0]): n for n in names}


def portraits():
    """{killer id: portrait file} from the K<id>_..._Portrait.png images the builds step downloaded."""
    out = {}
    for p in (paths.DATA / "images").glob("K*_Portrait.png"):
        m = re.match(r"K(\d+)_", p.name)
        if m:
            out[int(m.group(1))] = p.name
    return out


def enrich(data):
    """Adds the Otzdarva add-on tiers and the searchable names (aliases) of each killer, from killers.json. Idempotent."""
    if not paths.KILLERS.exists():
        return
    kj = json.loads(paths.KILLERS.read_text(encoding="utf8"))
    by_kid = {}
    for k in kj["killers"]:
        m = re.search(r"/K(\d+)_", k.get("portrait", ""))
        if m:
            by_kid[int(m.group(1))] = k
    for p in data["powers"]:
        k = by_kid.get(p["kid"])
        if k:
            p["killer"] = k["name"]  # the wiki's add-on section titles are sometimes odd ("Special HB/CB Add-ons"): use the killer's real name
        p["names"] = sorted({p["killer"], re.sub(r"^The\s+", "", p["killer"]), *([k["name"], k["short"], *k.get("aliases", [])] if k else [])})
        if not k:
            continue
        ads = {norm(a["name"]): a for a in k["addons"]}
        for a in p["addons"]:
            src = ads.get(norm(a["name"]))
            if not src:
                close = difflib.get_close_matches(norm(a["name"]), list(ads), n=1, cutoff=0.85)
                src = ads[close[0]] if close else None
            if src:
                a["tier"] = src["tier"]
                a["comment"] = re.sub(r"\s+", " ", src.get("comment", "")).strip()[:450]
    for key, lst in data["offerings"].items():  # mobile-only / retired offerings cannot be rolled any more
        data["offerings"][key] = [o for o in lst if not re.search(r"DBD MOBILE|NO LONGER|RETIRED", o.get("desc", "").upper())]


def main(log=print, refresh=False):
    paths.ensure()
    log("Reading the wiki's item, add-on, power and offering tables...")
    lua = get(f"{WIKI}/index.php?title=Module:Datatable/Loadout&action=raw")
    off_rows, add_rows = wiki_rows("Offerings", refresh), wiki_rows("Add-ons", refresh, strip_lead=True)
    item_rows = wiki_rows("Items", refresh)
    pw_icons = power_icons()
    ports = portraits()

    killers = {}  # id -> name (sections of the add-ons table)
    for n, f, sec in parse_table(lua, "addons"):
        if f.get("killer", "0") != "0":
            killers.setdefault(int(f["killer"]), re.sub(r"^K\d+\s*-\s*", "", sec).strip())

    addons_by_item, addons_by_killer = {}, {}
    for n, f, _ in parse_table(lua, "addons"):
        if any(f.get(k) for k in ("unused", "unusedVisible", "decom", "notAvailable", "deprecated", "retired")):
            continue
        row = lookup(add_rows, n)
        if not row or "NO LONGER AVAILABLE" in row[2].upper():
            continue
        d = {"name": n, "icon": row[1], "desc": row[2], "rarity": int(f.get("rarity", 1))}
        if f.get("itemsCategory", "0") != "0":
            addons_by_item.setdefault(f["itemsCategory"], []).append(d)
        elif f.get("killer", "0") != "0":
            addons_by_killer.setdefault(int(f["killer"]), []).append(d)

    items = []
    for n, f, _ in parse_table(lua, "items"):
        if any(f.get(k) for k in ("unused", "deprecated")) or f.get("rarity") in (None, "0"):
            continue
        row = lookup(item_rows, n)
        ads = addons_by_item.get(f.get("category", "0"), [])
        if row and "NO LONGER" not in row[2].upper() and len(ads) >= 2:
            items.append({"name": n, "icon": row[1], "desc": row[2], "rarity": int(f["rarity"]), "pool": f.get("category", "0")})

    prows = parse_table(lua, "powers")
    extracts = power_extracts([n for n, f, _ in prows if int(f["killer"]) in addons_by_killer])
    powers = []
    for n, f, _ in prows:
        kid = int(f["killer"])
        if len(addons_by_killer.get(kid, [])) < 2:
            continue
        ic = pw_icons.get(norm(n))
        if not ic:
            close = difflib.get_close_matches(norm(n), list(pw_icons), n=1, cutoff=0.8)
            ic = pw_icons[close[0]] if close else None
        powers.append({"name": n, "icon": ic, "killer": killers.get(kid, f"K{kid}"), "kid": kid,
                       "desc": extracts.get(n, ""), "portrait": ports.get(kid), "addons": addons_by_killer[kid]})

    offerings = {"K": [], "S": [], "B": []}
    for n, f, _ in parse_table(lua, "offerings"):
        if any(f.get(k) for k in ("retired", "deprecated", "unused", "notAvailable")):
            continue
        row = lookup(off_rows, n)
        if row:
            offerings[f.get("charType", "B")].append({"name": n, "icon": row[1], "desc": row[2], "rarity": int(f.get("rarity", 1))})

    files = {d["icon"] for k in offerings.values() for d in k}
    pools = {i["pool"]: addons_by_item[i["pool"]] for i in items}
    files |= {i["icon"] for i in items}
    for ads in pools.values():
        files |= {a["icon"] for a in ads}
    for p in powers:
        files |= {a["icon"] for a in p["addons"]} | ({p["icon"]} if p["icon"] else set())
    log(f"{len(files)} icons to check...")
    urls = resolve_urls(files)
    todo = sorted(urls)
    with ThreadPoolExecutor(3) as ex:
        ok = {f for f, r in zip(todo, ex.map(fetch_icon, [(f, urls[f]) for f in todo])) if r}
    log(f"{len(ok)} icons OK, {len(files) - len(ok)} missing")

    def keep(lst):
        return [d for d in lst if d["icon"] in ok]

    for p in powers:
        p["addons"] = keep(p["addons"])
        if p["icon"] not in ok:
            p["icon"] = None  # no power icon: the killer's portrait is used
    data = {
        "items": [i for i in keep(items) if len(keep(pools[i["pool"]])) >= 2],
        "itemPools": {k: keep(v) for k, v in pools.items()},
        "poolNames": POOLS,
        "powers": [p for p in powers if len(p["addons"]) >= 2 and (p["icon"] or p["portrait"])],
        "offerings": {k: keep(v) for k, v in offerings.items()},
    }
    enrich(data)
    paths.LOADOUT_EXTRA.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
    log(f"Random-loadout data done: {len(data['powers'])} killers, {len(data['items'])} items, "
        f"{sum(len(v) for v in data['offerings'].values())} offerings")
    return data
