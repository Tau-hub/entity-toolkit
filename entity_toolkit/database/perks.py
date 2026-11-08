"""Perk database from the Dead by Daylight wiki (deadbydaylight.wiki.gg): names, descriptions and icons.

Writes data/loadout_data.json (killer and survivor perks) and downloads the perk icons into data/icons/. The survivor icons are what the
recognition compares screenshots with. When killers.json / survivors.json exist, each perk also gets its rating (note /100, stars, NightLight stats).
"""
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor

from bs4 import BeautifulSoup, NavigableString

from .. import paths
from ..text import norm

BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
WIKI = "https://deadbydaylight.wiki.gg"
CACHE = paths.DATA / "wiki_cache"


def get(url, binary=False, data=None, tries=8):
    """GET/POST that backs off when the wiki answers 403/429 (rate limit)."""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=data, headers={"User-Agent": BROWSER_UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                raw = r.read()
            return raw if binary else raw.decode("utf8", "replace")
        except urllib.error.HTTPError as e:
            if e.code not in (403, 429) or i == tries - 1:
                raise
            time.sleep(5 + i * 5)


def api(**p):
    return json.loads(get(f"{WIKI}/api.php", data=urllib.parse.urlencode({**p, "format": "json"}).encode()))


def page_html(title, refresh):
    f = CACHE / f"page_{title}.html"
    if refresh or not f.exists() or time.time() - f.stat().st_mtime > 600:  # an update must not reuse pages from an earlier run
        CACHE.mkdir(parents=True, exist_ok=True)
        f.write_text(api(action="parse", page=title, prop="text", disablelimitreport=1)["parse"]["text"]["*"], encoding="utf8")
    return f.read_text(encoding="utf8")


def clean_desc(td, strip_lead=False):
    """Useful text only: no flavour sentence, bullet lists, clean line breaks."""
    for span in td.select("span.clr9"):  # flavour quote of perks / offerings (beige)
        (span.find_parent("i") or span).decompose()
    ul = td.find("ul")
    if strip_lead and ul and ul.parent is td:  # add-ons: the flavour text comes before the list of effects
        for node in list(ul.previous_siblings):
            if isinstance(node, NavigableString) or node.name == "br":
                node.extract()
    for br in td.find_all("br"):
        br.replace_with("\n")
    for li in td.find_all("li"):
        li.insert_before("\n• ")
    for blk in td.find_all(["p", "ul"]):
        blk.insert_before("\n")
        blk.insert_after("\n")
    txt = td.get_text("")
    txt = re.sub(r"[ \t\xa0]+", " ", txt)
    txt = re.sub(r"\s*\n\s*", "\n", txt).strip()
    txt = re.sub(r"\s+([.,:;!?%)])", r"\1", txt).replace("( ", "(")
    lines = [ln for ln in txt.split("\n") if ln.startswith("•") or not re.fullmatch(r'["“].*["”]( [—–-].*)?|[—–-] ?.*', ln.strip())]
    return "\n".join(lines).strip()


def wiki_rows(title, refresh=False, strip_lead=False):
    """Rendered wiki page: {normalised name: (name, icon file, description)} (first occurrence wins)."""
    soup = BeautifulSoup(page_html(title, refresh), "html.parser")
    for t in soup.select(".tooltiptext, style, script, sup"):
        t.decompose()
    out = {}
    for tr in soup.find_all("tr"):
        tds = tr.find_all("td", recursive=False)
        if not tds:
            continue
        icon = name = None
        for th in tr.find_all("th", recursive=False):
            img = th.find("img", src=re.compile(r"/images/"))
            if img and not icon:
                path = urllib.parse.unquote(img["src"].split("?")[0].split("/images/")[1])
                icon = path.split("/")[1] if path.startswith("thumb/") else path
            elif th.get_text(strip=True) and not name:
                name = th.get_text(strip=True)
        if not (name and icon):
            continue
        out.setdefault(norm(name), (name, icon, clean_desc(tds[0], strip_lead)))
    return out


def resolve_urls(files):
    """file -> real url, in batches of 50; files already in the cache are skipped."""
    urls = {f: "" for f in files if (paths.ICONS / f).exists() and (paths.ICONS / f).stat().st_size > 200}
    files = sorted(f for f in files if f not in urls)

    def batch(chunk):
        """A file name can trip the wiki's firewall (403): split the batch to isolate it."""
        try:
            r = json.loads(get(f"{WIKI}/api.php", tries=2, data=urllib.parse.urlencode(
                {"action": "query", "titles": "|".join("File:" + f for f in chunk), "prop": "imageinfo", "iiprop": "url", "format": "json"}).encode()))
        except urllib.error.HTTPError:
            if len(chunk) == 1:
                return
            batch(chunk[:len(chunk) // 2])
            batch(chunk[len(chunk) // 2:])
            return
        back = {n["to"]: n["from"] for n in r["query"].get("normalized", [])}
        for pg in r["query"]["pages"].values():
            if "imageinfo" in pg:
                urls[back.get(pg["title"], pg["title"])[5:].replace(" ", "_")] = pg["imageinfo"][0]["url"]
        time.sleep(0.5)

    for i in range(0, len(files), 50):
        batch(files[i:i + 50])
    return urls


def fetch_icon(args):
    filename, url = args
    paths.ICONS.mkdir(parents=True, exist_ok=True)
    f = paths.ICONS / filename
    try:
        if not (f.exists() and f.stat().st_size > 200):
            f.write_bytes(get(url, binary=True))
            time.sleep(0.15)
        return True
    except Exception:
        return False


def parse_perks(lua, char_type):
    """[(name, wiki tags)] of one side ('K' or 'S') from the wiki's Lua datatable, skipping unused / retired perks.
    The wiki tags every perk with the mechanics it touches (Auras, Regression, Healing, Exposed...): the Build creator builds its types on them."""
    start = lua.index("p.perks = {")
    end = lua.index("p.perksCount", start)
    out = []
    for line in lua[start:end].splitlines():
        m = re.match(r'\s*\["(.+?)"\]\s*=\s*\{(.*)\}\s*,?\s*$', line)
        if not m:
            continue
        body = m.group(2)
        tags = re.findall(r'"([^"]+)"', (re.search(r"tags\s*=\s*\{([^}]*)\}", body) or [None, ""])[1])
        f = {k: v.strip("\"'") for k, v in re.findall(r"(\w+)\s*=\s*(\"[^\"]*\"|'[^']*'|[\w.+-]+)", re.sub(r"tags\s*=\s*\{[^}]*\}", "", body))}
        if any(f.get(k) for k in ("unused", "deprecated", "retired")) or f.get("charType") != char_type:
            continue
        out.append((m.group(1), tags))
    return out


def enrich(data):
    """Adds the ratings stored in killers.json / survivors.json: note /100, Otz stars, NightLight pick / win rates, owner character."""
    rate = {"K": {}, "S": {}}
    for key, f in (("K", paths.KILLERS), ("S", paths.SURVIVORS)):
        if not f.exists():
            continue
        src = json.loads(f.read_text(encoding="utf8"))
        for ch in src["killers"]:
            for t in ch["teachables"]:
                nl = t.get("nl") or {}
                alt = " ".join(dict.fromkeys([ch["name"], ch.get("short", ""), *ch.get("aliases", [])]))
                rate[key][norm(t["name"])] = {"owner": ch.get("short") or ch["name"], "ownerAlt": alt,
                                              "note": round(t["score"] / 10), "stars": t.get("stars"), "otz": t.get("value"),
                                              "pick": nl.get("pick"), "nlRate": nl.get("rate")}
    for key in ("K", "S"):
        for d in data["perks"][key]:
            d.update(rate[key].get(norm(d["name"]), {}))
    n = sum("note" in d for key in ("K", "S") for d in data["perks"][key])
    return n


def main(log=print, refresh=False):
    paths.ensure()
    log("Reading the wiki's perk tables...")
    lua = get(f"{WIKI}/index.php?title=Module:Datatable/Loadout&action=raw")
    rows = {"K": wiki_rows("Killer_Perks", refresh), "S": wiki_rows("Survivor_Perks", refresh)}
    perks = {"K": [], "S": []}
    for side in ("K", "S"):
        for n, tags in parse_perks(lua, side):
            row = rows[side].get(norm(n)) or rows[side].get(norm(re.sub(r"\s*\(.*?\)\s*$", "", n)))
            if row:
                perks[side].append({"name": n, "icon": row[1], "desc": row[2], "tags": tags})
    files = {d["icon"] for side in perks.values() for d in side}
    log(f"{len(perks['K'])} killer perks, {len(perks['S'])} survivor perks, {len(files)} icons to check...")
    urls = resolve_urls(files)
    todo = sorted(urls)
    with ThreadPoolExecutor(3) as ex:
        ok = {f for f, r in zip(todo, ex.map(fetch_icon, [(f, urls[f]) for f in todo])) if r}
    log(f"{len(ok)} icons OK, {len(files) - len(ok)} missing")
    data = {"perks": {side: [d for d in lst if d["icon"] in ok] for side, lst in perks.items()}}
    rated = enrich(data)
    paths.LOADOUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
    log(f"Perk database done: {len(data['perks']['K'])} killer + {len(data['perks']['S'])} survivor perks, {rated} with a rating")
    return data
