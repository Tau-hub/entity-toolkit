"""Builds the recommended-builds / priorities data (killers.json, survivors.json, survivor_builds.json).

Sources, fetched on *your* machine when you run `update-db` (nothing from them is shipped in this repository):
  - otzdarva-builds.com and otzdarva.com : Otzdarva's builds, perk values and character info
  - otz-addon-tierlist.pages.dev        : Otzdarva's killer add-on tier list
  - nightlight.gg                       : community perk / build statistics (last 28 days)
Credit for the opinions and ratings belongs to Otzdarva and to the NightLight team.
"""
import difflib
import hashlib
import html
import json
import re
import unicodedata
import urllib.parse
import urllib.request
from .. import paths

HERE = paths.DATA
IMAGES = paths.DATA / "images"
UA = {"User-Agent": "Mozilla/5.0"}
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"
TIER_SITE = "https://otz-addon-tierlist.pages.dev"

# name (add-ons site) -> name (builds site / otzdarva.com)
ALIASES = {
    "myers": "The Shape", "leatherface": "The Cannibal", "freddy": "The Nightmare",
    "pyramid head": "The Executioner", "pinhead": "The Cenobite", "onryo": "The Onryō",
    "wesker": "The Mastermind", "chucky": "The Good Guy", "vecna": "The Lich",
    "dracula": "The Dark Lord", "springtrap": "The Animatronic", "jason": "The Slasher",
    "judgement": "The Judgment", "ghostface": "The Ghost Face", "pig": "The Pig",
}


def get(url, ua=None):
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": ua} if ua else UA), timeout=60) as r:
        return r.read().decode("utf8")


def loc(url):
    """Local image (data/images/) if present, downloaded when needed; otherwise the Fandom CDN."""
    if "wiki.gg/images/" not in url:
        return url
    name = urllib.parse.unquote(url.split("/images/")[1].split("?")[0])
    f = IMAGES / name
    if not (f.exists() and f.stat().st_size > 500):
        try:
            req = urllib.request.Request(url.split("?")[0], headers={"User-Agent": BROWSER_UA, "Accept": "image/png,image/*,*/*;q=0.8"})
            data = urllib.request.urlopen(req, timeout=30).read()
            if len(data) > 500:
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_bytes(data)
        except Exception:
            return fandom(url)
    return "images/" + urllib.parse.quote(name)


def fandom(url):
    """wiki.gg blocks hotlinking; the Fandom CDN hosts the same files (path = md5 of the name)."""
    if "wiki.gg/images/" not in url:
        return url
    f = urllib.parse.unquote(url.split("/images/")[1].split("?")[0])
    h = hashlib.md5(f.encode()).hexdigest()
    return f"https://static.wikia.nocookie.net/deadbydaylight_gamepedia_en/images/{h[0]}/{h[:2]}/{urllib.parse.quote(f)}"


def perk_desc(s):
    """A perk's description: the effect only, without the flavour text."""
    s = re.sub(r'<i><span class="luaClr clr clr9"[^>]*>.*?</span></i>', "", s, flags=re.S)
    return strip(s)


def addon_desc(raw):
    """An add-on's description: the effect only (no flavour sentence before the list, no quotes)."""
    raw = re.sub(r'<i><span class="luaClr clr clr9"[^>]*>.*?</span></i>', "", raw, flags=re.S)
    m = re.search(r"<p[ >]|<ul", raw)
    i = m.start() if m else 0
    if i > 0:
        # plain text before the first paragraph / the list: flavour lines, except the sentence that introduces an effect ("... :")
        lines = [strip(x) for x in re.split(r"<br\s*/?>|\n", raw[:i])]
        lines = [x for x in lines if x]
        keep = [j for j, x in enumerate(lines) if x.endswith(":")]
        raw = ("\n".join(lines[keep[-1]:]) + "\n" if keep else "") + raw[i:]
    # flavour paragraph right before the list (a sentence that does not introduce an effect: no ":")
    m = re.match(r"\s*<p[^>]*>(.*?)</p>\s*(?=<ul)", raw, flags=re.S)
    if m and not strip(m.group(1)).endswith(":"):
        raw = raw[m.end():]
    return strip(raw)


def strip(s):
    s = re.sub(r"<br\s*/?>|</p>|</li>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = html.unescape(s).replace("\xa0", " ")
    return re.sub(r"\n\s*\n+", "\n", s).strip()


def nname(name):
    name = unicodedata.normalize("NFD", name.lower()).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]", "", name.replace("hex:", "").replace("scourge hook:", ""))


def lookup_n(d, name):
    """Lookup by normalised name, then approximate (e.g. "Chili" / "Chilli")."""
    k = nname(name)
    if k in d:
        return d[k]
    m = difflib.get_close_matches(k, d.keys(), n=1, cutoff=0.85)
    return d[m[0]] if m else None


def canon(name):
    return re.sub(r"[^a-z]", "", name.lower().replace("the ", "", 1) if name.lower().startswith("the ") else name.lower())


def parse_difficulty(page):
    out = {}
    for chunk in page.split('_createdAt:"')[1:]:
        if '_type:"killer"' not in chunk:
            continue
        g = lambda k: (re.search(k + r':"((?:[^"\\]|\\.)*)"', chunk) or [None, ""])[1].replace('\\"', '"')
        name = g("name")
        comment = "\n".join(
            t.replace('\\"', '"') for t in re.findall(r'text:"((?:[^"\\]|\\.)*)"', chunk) if t != "---"
        )
        out[canon(name)] = {
            "order": int((re.search(r"inGameOrder:(\d+)", chunk) or [0, 0])[1]),
            "unlockPriority": int((re.search(r"unlockPriority:(\d+)", chunk) or [0, 0])[1]),
            "perkRefs": re.findall(r'_ref:"([^"]+)"', chunk.split("perks:[", 1)[1].split("]", 1)[0]) if "perks:[" in chunk else [],
            "difficulty": g("difficulty"), "speed": g("speed"), "terrorRadius": g("terrorRadius"),
            "availableIn": g("availableIn"), "icon": g("iconUrl"), "comment": comment,
            "guide": g("mostRecentGuideUrl"),
        }
    return out


def parse_perk_docs(page):
    docs = {}
    for chunk in page.split('_createdAt:"')[1:]:
        if '_type:"perk"' not in chunk:
            continue
        g = lambda k: (re.search(k + r':"((?:[^"\\]|\\.)*)"', chunk) or [None, ""])[1]
        v = re.search(r"value:(\d+)", chunk)
        docs[g("_id")] = {"name": g("name").replace('\\"', '"'), "value": int(v.group(1)) if v else 0, "belongsTo": g("belongsTo"), "iconUrl": g("iconUrl")}
    return docs


def parse_survivors(page):
    out = []
    for chunk in page.split('_createdAt:"')[1:]:
        if '_type:"survivor"' not in chunk:
            continue
        g = lambda k: (re.search(k + r':"((?:[^"\\]|\\.)*)"', chunk) or [None, ""])[1]
        refs = re.findall(r'_ref:"([^"]+)"', chunk.split("perks:[", 1)[1].split("]", 1)[0]) if "perks:[" in chunk else []
        out.append({"name": g("name"), "icon": g("iconUrl"), "perkRefs": refs, "availableIn": g("availableIn").replace('\\"', '"'),
                    "order": int((re.search(r"inGameOrder:(\d+)", chunk) or [0, 0])[1])})
    return out


NL = "https://nightlight.gg"


def fetch_nightlight():
    """NightLight community stats (last 28 days): {role: {normalised name: stats}}, period."""
    kp = json.loads(get(NL + "/api/v1/stats/global/killer-perks", BROWSER_UA))["data"]
    sp = json.loads(get(NL + "/api/v1/stats/global/survivor-perks", BROWSER_UA))["data"]
    viewer = get(NL + "/perks/viewer", BROWSER_UA)
    names = {}
    for js in sorted(set(re.findall(r"/assets/[\w\-.]+\.js", viewer))):
        try:
            txt = get(NL + js, BROWSER_UA)
        except Exception:
            continue
        if "Pain Resonance" not in txt:
            continue
        for pid, n, slug, r, tier, rank in re.findall(r'"(\d+)":\{"n":"([^"]+)","i":"([^"]*)","u":"[^"]*","r":(\d),"c":\d+,"t":"(\w+)","p":(\d+)', txt):
            names[int(pid)] = (n, int(r), tier, int(rank), slug)
        break
    glob = json.loads(get(NL + "/api/v1/stats/global/perks_and_builds", BROWSER_UA))["data"]
    out = {}
    for role, data, rate_key in ((2, kp, "kill_rate"), (1, sp, "escape_rate")):
        rows = data["perks"]
        tot = sum(x["count"] for x in rows) or 1
        avg = sum(x[rate_key] * x["count"] for x in rows) / tot
        by_pct = sorted(rows, key=lambda x: -x["pct"])
        n = max(len(by_pct) - 1, 1)
        pool = {}
        for i, x in enumerate(by_pct):
            if x["id"] not in names:
                continue
            pool[nname(names[x["id"]][0])] = {
                "pick": x["pct"], "rate": x[rate_key], "games": x["count"], "avgRate": round(avg, 1),
                "tier": names[x["id"]][2], "usage": 1 - i / n,
                "perf": 0.5 if x["count"] < 150 else max(0.0, min(1.0, 0.5 + (x[rate_key] - avg) / 20)),
            }
        out[role] = pool
    return out, f'{kp["start"][:10]} → {kp["end"][:10]}', names, glob


def cdn_local(url):
    """Downloads an icon from the NightLight CDN into data/images/ (name prefixed nl_); returns the relative path."""
    name = "nl_" + url.rsplit("/", 1)[-1]
    f = IMAGES / name
    if not (f.exists() and f.stat().st_size > 200):
        try:
            data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": BROWSER_UA}), timeout=30).read()
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
        except Exception:
            return url
    return "images/" + urllib.parse.quote(name)


def fetch_nl_killer_builds(k, icon_of, kind="killers", limit=8, cands=None):
    """A character's most played builds on NightLight (no empty slot, no "Adept" build)."""
    html_page = ""
    for cand in cands or ([k["short"]] + k["aliases"]):
        try:
            html_page = get(NL + f"/{kind}/" + urllib.parse.quote(cand.replace(" ", "_")), BROWSER_UA)
        except Exception:
            continue
        if "Most Used Builds" in html_page:
            break
    if "Most Used Builds" not in html_page:
        return []
    seg = html_page[html_page.index("Most Used Builds"):]
    own = {nname(t["name"]) for t in k["teachables"]}
    out = []
    for cell, usage, rate, wins, games in re.findall(
        r"<tr><td></td><td>(.*?)</td><td>([\d.]+)%</td><td>([\d.]+)<!-- -->%<small[^>]*>(\d+)<!-- -->/<!-- -->(\d+)</small></td></tr>", seg
    ):
        imgs = re.findall(r'src="([^"]+)"[^>]*?title="([^"]*)"', cell)
        if len(imgs) < 4 or any("none-85" in src for src, _ in imgs):
            continue  # empty slot
        names_ = [html.unescape(t) for _, t in imgs]
        if sum(nname(n) in own for n in names_) >= 3:
            continue  # the "Adept" achievement build
        out.append({
            "perks": [dict(zip(("icon", "icon2", "desc"), icon_of(n, src))) | {"name": n} for (src, _), n in zip(imgs, names_)],
            "usage": float(usage), "rate": float(rate), "wins": int(wins), "games": int(games),
        })
        if len(out) >= limit:
            break
    return out


def nl_lookup(pool, name):
    k = nname(name)
    if k in pool:
        return pool[k]
    m = difflib.get_close_matches(k, pool.keys(), n=1, cutoff=0.85)
    return pool[m[0]] if m else None


def blend(otz_value, nl):
    """Rating 0-1000: 50 % Otz's opinion, 35 % NightLight popularity (rank), 15 % NightLight performance."""
    if not nl:  # perk missing from the NightLight stats: keep Otz's value alone
        return min(otz_value, 999)
    usage, perf = nl["usage"], nl["perf"]
    return round(1000 * (0.5 * min(otz_value, 999) / 999 + 0.35 * usage + 0.15 * perf))


def stars(v):
    return 0 if v <= 0 else 1 if v <= 333 else 2 if v <= 666 else 3


def parse_tierlist(page):
    groups = page.split('<div class="killerGroup">')[1:]
    out = {}
    for grp in groups:
        file = re.search(r'src="\./public/killers/([^"]+?)\.png"', grp).group(1)
        file = urllib.parse.unquote(file)
        portrait = f"{TIER_SITE}/public/killers/{urllib.parse.quote(file)}.png"
        addons = []
        for m in re.finditer(
            r'class="addon-back ([\w-]+)">\s*<div class="addon"\s*data-comment="([^"]*)">.*?src="\./public/addons/([^"]+)"\s*alt="([^"]*)".*?class="addon-desc" data-comment="([^"]*)"',
            grp, re.S,
        ):
            tier, comment, img, alt, desc = m.groups()
            comment = strip(html.unescape(comment))
            comment = re.sub(r"^.*?:\s", "", comment, count=1) if ":" in comment[:60] else comment
            addons.append({
                "name": html.unescape(alt).strip(), "tier": tier,
                "img": f"{TIER_SITE}/public/addons/{urllib.parse.quote(urllib.parse.unquote(img))}",
                "comment": comment, "desc": addon_desc(urllib.parse.unquote(desc)),
            })
        combos = {}
        for key in ("best", "solid", "good", "fun"):
            cm = re.search(rf'class="{key}-combo text-combo" data-comment="([^"]*)"', grp)
            idx = [int(x) for x in re.findall(r"\d+", cm.group(1))] if cm else []
            combos[key] = [i - 1 for i in idx if 0 < i <= len(addons)]
        out[file] = {"portrait": portrait, "addons": addons, "combos": combos}
    return out


def chapter_label(available_in):
    """'"Old Wounds" DLC Pack' -> 'Old Wounds'; 'Base Game' stays. Killer and survivor of the same chapter get the same label."""
    s = re.sub(r"\s*(DLC Pack|DLC|Chapter)\s*$", "", available_in.replace('"', "").strip(), flags=re.I).strip()
    s = re.sub(r"\s*Chapter\s*$", "", s).strip()
    return s or "Unknown"


def canon_chapters(labels):
    """Fixes typos in the source ('Madenning Darkness') by snapping each label to the most frequent close one."""
    counts = {}
    for l in labels:
        counts[l] = counts.get(l, 0) + 1
    ranked = sorted(counts, key=lambda l: -counts[l])
    out = {}
    for l in labels:
        close = difflib.get_close_matches(l, [r for r in ranked if counts[r] > counts[l]], n=1, cutoff=0.88)
        out[l] = close[0] if close else l
    return out


def tier_key_to_name(file):
    return ALIASES.get(file.lower(), "The " + file.title())


def main(log=print):
    """Downloads everything and writes killers.json, survivors.json and survivor_builds.json in the data folder."""
    paths.ensure()
    IMAGES.mkdir(exist_ok=True)
    log("Downloading Otzdarva's builds and tier list...")
    builds = json.loads(get("https://otzdarva-builds.com/data/builds.json"))
    scrape = json.loads(get("https://otzdarva-builds.com/data/scrape.json"))
    tiers = parse_tierlist(get(TIER_SITE + "/"))
    ci_page = get("https://otzdarva.com/dbd/character-info")
    diffs = parse_difficulty(ci_page)
    perk_docs = parse_perk_docs(ci_page)
    try:
        nl_stats, nl_period, nl_names, nl_glob = fetch_nightlight()
        log(f"NightLight: {len(nl_stats[2])} killer perks, {len(nl_stats[1])} survivor perks ({nl_period})")
    except Exception as e:
        log(f"  ! NightLight unavailable: {e}")
        nl_stats, nl_period, nl_names, nl_glob = {1: {}, 2: {}}, "", {}, {}

    perks = {p["name"]: {"icon": loc(p["iconUrl"]), "icon2": fandom(p["iconUrl"]), "desc": perk_desc(p["description"])} for p in scrape["killers"]["perks"]}
    portraits = {canon(c["name"]): c["portraitUrl"] for c in scrape["killers"]["characters"]}
    meta = scrape.get("other", {})

    perks_n = {nname(k): v for k, v in perks.items()}

    def perk(p):
        info = perks.get(p["name"]) or lookup_n(perks_n, p["name"]) or (
            {"icon": loc(p["iconUrl"]), "icon2": fandom(p["iconUrl"]), "desc": ""} if p.get("iconUrl") else {})
        return {"name": p["name"], "icon": info.get("icon", ""), "icon2": info.get("icon2", ""), "desc": info.get("desc", "")}

    def build(b):
        return {
            "name": b["name"], "notes": b["notes"],
            "perks": [dict(perk(p), alts=[perk(a) for a in p["alts"]]) for p in b["perks"]],
        }

    killers, universal = [], None
    tier_by_canon = {canon(tier_key_to_name(f)): (f, t) for f, t in tiers.items()}
    for k in builds["killers"]:
        if k["name"] == "Universal Builds":
            universal = [build(b) for b in k["builds"]]
            continue
        c = canon(k["name"])
        f, t = tier_by_canon.get(c, (None, {"portrait": "", "addons": [], "combos": {}}))
        d = diffs.get(c, {})
        killers.append({
            "name": k["name"], "short": k["name"].replace("The ", "", 1), "slug": c,
            "aliases": [f] if f else [],
            "portrait": loc(portraits.get(c) or t["portrait"] or d.get("icon", "")),
            "portrait2": fandom(portraits.get(c) or ""),
            "difficulty": d.get("difficulty", "?"), "speed": d.get("speed", ""),
            "terrorRadius": d.get("terrorRadius", ""), "availableIn": d.get("availableIn", ""),
            "otzComment": d.get("comment", ""), "guide": d.get("guide", ""),
            "order": d.get("order", 0), "unlockPriority": d.get("unlockPriority", 0),
            "teachables": [
                {"name": perk_docs[r]["name"], "value": perk_docs[r]["value"], "stars": stars(perk_docs[r]["value"]),
                 "nl": nl_lookup(nl_stats[2], perk_docs[r]["name"]),
                 "score": blend(perk_docs[r]["value"], nl_lookup(nl_stats[2], perk_docs[r]["name"])),
                 "icon": perk(perk_docs[r])["icon"], "icon2": perk(perk_docs[r])["icon2"], "desc": perk(perk_docs[r])["desc"]}
                for r in d.get("perkRefs", []) if r in perk_docs
            ],
            "builds": [build(b) for b in k["builds"]],
            "addons": t["addons"], "combos": t["combos"],
        })
        if not t["addons"]:
            log(f"  ! no add-ons for {k['name']}")
        if not d:
            log(f"  ! no difficulty info for {k['name']}")

    data = {"patch": meta.get("patchNumber", ""), "nlPeriod": nl_period, "nlRate": "kills", "killers": killers, "universal": universal or []}
    # ---- survivors ----
    sperks = {p["name"]: {"icon": loc(p["iconUrl"]), "icon2": fandom(p["iconUrl"]), "desc": perk_desc(p["description"])}
              for p in scrape["survivors"]["perks"]}
    sperks_n = {nname(k): v for k, v in sperks.items()}
    sport = {c["name"]: c["portraitUrl"] for c in scrape["survivors"]["characters"]}
    survivors = []
    for sv in sorted(parse_survivors(ci_page), key=lambda x: x["order"]):
        tl = []
        for r in sv["perkRefs"]:
            if r not in perk_docs:
                continue
            pd = perk_docs[r]
            info = sperks.get(pd["name"]) or lookup_n(sperks_n, pd["name"]) or (
                {"icon": loc(pd["iconUrl"]), "icon2": fandom(pd["iconUrl"]), "desc": ""} if pd.get("iconUrl") else {})
            nl = nl_lookup(nl_stats[1], pd["name"])
            tl.append({"name": pd["name"], "value": pd["value"], "stars": stars(pd["value"]), "nl": nl,
                       "score": blend(pd["value"], nl), "icon": info.get("icon", ""),
                       "icon2": info.get("icon2", ""), "desc": info.get("desc", "")})
        raw = sport.get(sv["name"]) or sv["icon"]
        survivors.append({"name": sv["name"], "short": sv["name"], "slug": nname(sv["name"]), "portrait": loc(raw), "portrait2": fandom(raw),
                          "availableIn": sv["availableIn"], "teachables": tl, "nlBuilds": []})
    sdata = {"patch": meta.get("patchNumber", ""), "nlPeriod": nl_period, "nlRate": "escapes", "killers": survivors, "universal": []}
    log(f"Survivors: {len(survivors)}")
    # chapter label of every character (killer + survivor of the same DLC share it), typos in the source snapped together
    raw_labels = [chapter_label(c.get("availableIn", "")) for c in killers + survivors]
    fixed = canon_chapters(raw_labels)
    for c, l in zip(killers + survivors, raw_labels):
        c["chapter"] = fixed[l]

    # ---- NightLight builds (killers + survivors) ----
    all_n = {**sperks_n, **perks_n}

    def icon_of(name, cdn_src):
        info = lookup_n(all_n, name)
        return (info["icon"], info["icon2"], info["desc"]) if info else (cdn_local(cdn_src), cdn_src, "")

    for k in killers:
        k["nlBuilds"] = fetch_nl_killer_builds(k, icon_of)
    log(f"NightLight killer builds: {sum(len(k['nlBuilds']) for k in killers)} ({sum(1 for k in killers if not k['nlBuilds'])} killers without a build)")
    paths.KILLERS.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf8")

    # survivor builds: group the full builds (4 perks, no "Adept" build) of all the survivors' pages
    agg = {}
    for sv_ in survivors:
        rows = fetch_nl_killer_builds(sv_, icon_of, kind="survivors", limit=40, cands=[sv_["name"], sv_["name"].title()])
        for r in rows:
            key = tuple(sorted(nname(p["name"]) for p in r["perks"]))
            a = agg.setdefault(key, {"perks": r["perks"], "wins": 0, "games": 0})
            a["wins"] += r["wins"]
            a["games"] += r["games"]
    paths.SURVIVORS.write_text(json.dumps(sdata, ensure_ascii=False, indent=1), encoding="utf8")
    tot_games = sum(a["games"] for a in agg.values()) or 1
    s_nl = [{"perks": a["perks"], "usage": round(100 * a["games"] / tot_games, 2),
             "rate": round(100 * a["wins"] / max(a["games"], 1), 2), "wins": a["wins"], "games": a["games"]}
            for a in sorted(agg.values(), key=lambda a: -a["games"])]

    def sperk(p):
        info = lookup_n(all_n, p["name"]) or {}
        return {"name": p["name"], "icon": info.get("icon", ""), "icon2": info.get("icon2", ""), "desc": info.get("desc", "")}

    def sbuild(b):
        return {"name": b["name"], "notes": b["notes"], "perks": [dict(sperk(p), alts=[sperk(a) for a in p["alts"]]) for p in b["perks"]]}

    s_otz = [{"name": g["name"], "builds": [sbuild(b) for b in g["builds"]]} for g in builds["survivors"]]
    sb = {"patch": meta.get("patchNumber", ""), "nlPeriod": nl_period, "nl": s_nl[:12], "otz": s_otz}
    paths.SURVIVOR_BUILDS.write_text(json.dumps(sb, ensure_ascii=False, indent=1), encoding="utf8")
    log(f"NightLight survivor builds: {len(sb['nl'])}")
    log(f"Builds data done: {len(killers)} killers, {sum(len(k['addons']) for k in killers)} add-ons, patch {data['patch']}")
