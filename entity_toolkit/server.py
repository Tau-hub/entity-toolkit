"""Local web server (127.0.0.1 only): the live page, the setup / levels / priorities pages and the JSON API behind them.

Only the site's own files are served (web/, the downloaded perk icons and images): never the NightLight token, the browser profile or the logs.
State-changing requests need a custom header that other websites cannot send cross-origin, so a web page you visit cannot drive the toolkit.
"""
import json
import threading
from urllib.parse import quote
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import unquote, urlparse

from . import autostart, config, database, levels, mybuilds, nightlight, paths, perk_types, shrine, version, winapi
from .database import patch as patch_info

MIME = {".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8",
        ".png": "image/png", ".webp": "image/webp", ".jpg": "image/jpeg", ".svg": "image/svg+xml", ".ico": "image/x-icon"}
DATA_PAGES = {"killer.html": paths.KILLERS, "survivor_builds.html": paths.SURVIVOR_BUILDS}  # pages whose data is injected into the HTML
EMPTY = {"killer.html": {"patch": "", "nlPeriod": "", "nlRate": "", "killers": [], "universal": []},
         "survivor_builds.html": {"patch": "", "nlPeriod": "", "nl": [], "otz": []}}


def loadout_data():
    """Everything the random-loadout page rolls from, with icon paths the browser can load (same origin, so the poster canvas can be saved)."""
    try:
        base = json.loads(paths.LOADOUT.read_text(encoding="utf8"))
        extra = json.loads(paths.LOADOUT_EXTRA.read_text(encoding="utf8"))
    except Exception:
        return {"perks": {"K": [], "S": []}, "items": [], "itemPools": {}, "poolNames": {}, "powers": [], "offerings": {"K": [], "S": [], "B": []}}
    icon = lambda f: "icons/" + quote(f)
    emb = lambda d: {**d, "icon": icon(d["icon"])}
    portrait = lambda p: "images/" + quote(p["portrait"]) if p.get("portrait") else None
    return {
        "perks": {k: [emb(d) for d in v] for k, v in base["perks"].items()},
        "items": [emb(i) for i in extra["items"]],
        "itemPools": {k: [emb(a) for a in v] for k, v in extra["itemPools"].items()},
        "poolNames": extra["poolNames"],
        "powers": [{**p, "icon": icon(p["icon"]) if p["icon"] else portrait(p), "portraitUri": portrait(p), "addons": [emb(a) for a in p["addons"]]} for p in extra["powers"]],
        "offerings": {k: [emb(d) for d in v] for k, v in extra["offerings"].items()},
    }


def loadout_page_data():
    """The random-loadout data plus what its filters need: each perk's types, whether you have it (its character is levelled, or it is a
    general perk), the killers you own, and the perk types of each side."""
    data = loadout_data()
    over = perk_types.overrides()
    lv = levels.load()
    data["types"] = {}
    for side, kind in (("K", "killers"), ("S", "survivors")):
        src = perk_types.resolve_copies(data["perks"][side])
        types = {p["name"]: perk_types.perk_types(p, side, over) for p in src}
        for p in data["perks"][side]:
            p["types"] = types.get(p["name"], [])
            p["have"] = not p.get("owner") or int(lv[kind].get(p["owner"], 0) or 0) >= 1
        used = {t for ts in types.values() for t in ts}
        data["types"][side] = [{"id": t[0], "label": t[1], "group": t[2]} for t in perk_types.TYPES if side in t[3] and t[0] in used]
    data["ownedKillers"] = [c["name"] for c in levels.characters("killers") if c["owned"]] + [c["short"] for c in levels.characters("killers") if c["owned"]]
    return data


def buildmaker_data():
    """Everything the Build creator needs: perks of both sides with their types, the type lists, the killers (small heads), the saved builds."""
    data = loadout_data()
    over = perk_types.overrides()
    perks, catalogs = {}, {}
    for side in ("K", "S"):
        src = perk_types.resolve_copies(data["perks"][side])
        perks[side] = [{"name": p["name"], "icon": p["icon"], "desc": p.get("desc", ""), "owner": p.get("owner", ""), "ownerAlt": p.get("ownerAlt", ""),
                        "types": perk_types.perk_types(p, side, over), "custom": p["name"] in over} for p in src]
        catalogs[side] = perk_types.catalog(side, src, over)
    killers = sorted(({"kid": p["kid"], "name": p["killer"], "short": p["names"][1] if len(p["names"]) > 1 else p["killer"], "names": p["names"], "portrait": p.get("portraitUri")}
                      for p in data["powers"]), key=lambda k: k["kid"])
    return {"perks": perks, "types": catalogs, "allTypes": [{"id": t[0], "label": t[1], "group": t[2], "sides": t[3], "alias": perk_types.ALIASES.get(t[0], "")} for t in perk_types.TYPES],
            "killers": killers, "builds": mybuilds.load()}


def with_patch(data):
    """Adds the game's live patch (when known) next to the patch Otzdarva's data is for."""
    live = patch_info.load()
    if isinstance(data, dict) and live:
        data["livePatch"] = live["live"]
    return data


def setup_done():
    """The first-launch setup is over: your own choice (Finish / Reset on the Setup page), else guessed from the data for older installs."""
    cfg = config.load()
    if cfg.get("setup_done") is not None:
        return bool(cfg["setup_done"])
    return db_ready() and bool(cfg.get("player"))


def db_ready():
    return paths.LOADOUT.exists() and paths.ICONS.exists() and any(paths.ICONS.iterdir())


class Hub:
    """Shared state between the assistant (writes) and the web pages (read)."""

    def __init__(self):
        self.lock = threading.Lock()
        self.state = {"version": 0, "status": "Waiting for the capture key", "result": None}
        self.stop = threading.Event()
        self.goto = None                 # page the open window is asked to show (taken by the window, once)
        self.window_open = lambda: False  # replaced by the launcher: is the Entity Toolkit window open?
        self.opener = None               # replaced by the launcher: shows a page (window or browser)

    def window_goto(self, page):
        with self.lock:
            self.goto = page

    def take_goto(self):
        with self.lock:
            page, self.goto = self.goto, None
        return page

    def _set(self, **kw):
        with self.lock:
            self.state.update(kw)
            self.state["version"] += 1

    def status(self, msg):
        self._set(status=msg)

    def result(self, res):
        self._set(result=res, status=None)

    def snapshot(self):
        with self.lock:
            s = dict(self.state)
        cfg = config.load()
        s.update(ready=db_ready(), key=winapi.combo_label(cfg["capture_key"]), auto=bool(cfg.get("auto")))
        return s

    def quit(self):
        self.stop.set()

    def wait(self):
        self.stop.wait()


def _token_saved():
    return nightlight.have_token()


def _ocr_available():
    try:
        from winrt.windows.media.ocr import OcrEngine
        return OcrEngine.try_create_from_user_profile_languages() is not None
    except Exception:
        return False


def make_handler(hub):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        # ---------- helpers ----------
        def _send(self, code, body, ctype, cache="no-store"):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", cache)
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def _json(self, obj, code=200):
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf8"), "application/json; charset=utf-8")

        def _host_ok(self):
            return self.headers.get("Host", "").split(":")[0] in ("127.0.0.1", "localhost")  # against DNS rebinding

        # ---------- GET ----------
        def do_GET(self):
            if not self._host_ok():
                return self._send(403, b"forbidden", "text/plain")
            path = unquote(urlparse(self.path).path)
            if path in ("/", ""):
                self.send_response(302)
                self.send_header("Location", "/app.html#live.html" if db_ready() and setup_done() else "/app.html#setup.html")
                self.end_headers()
                return
            if path.startswith("/api/"):
                return self._api_get(path)
            rel = path.lstrip("/")
            if rel == "loadout.html":
                html = (paths.WEB / rel).read_text(encoding="utf8").replace("/*DATA*/null", json.dumps(loadout_page_data(), ensure_ascii=False).replace("</", "<\/"))
                return self._send(200, html.encode("utf8"), MIME[".html"])
            if rel in DATA_PAGES:
                return self._data_page(rel)
            for prefix, root in (("icons/", paths.ICONS), ("images/", paths.DATA / "images")):
                if rel.startswith(prefix):
                    return self._file(root, rel[len(prefix):], cache="max-age=3600")
            return self._file(paths.WEB, rel)

        def _file(self, root, rel, cache="no-store"):
            f = (root / rel).resolve()
            root = root.resolve()
            if not (root in f.parents and f.suffix.lower() in MIME and f.is_file()):
                return self._send(404, b"not found", "text/plain")
            self._send(200, f.read_bytes(), MIME[f.suffix.lower()], cache=cache)

        def _data_page(self, rel):
            """Pages built from a template: the downloaded data is injected where the page expects it."""
            try:
                data = json.loads(DATA_PAGES[rel].read_text(encoding="utf8"))
            except Exception:
                data = EMPTY[rel]
            html = (paths.WEB / rel).read_text(encoding="utf8").replace("/*__DATA__*/null", json.dumps(with_patch(data), ensure_ascii=False).replace("</", "<\\/"))
            self._send(200, html.encode("utf8"), MIME[".html"])

        def _api_get(self, path):
            if path == "/api/live":
                return self._json(hub.snapshot())
            if path == "/api/shell":
                st = database.STATE
                return self._json({"setup_done": setup_done(), "version": version.info(), "shrine": shrine.summary(),
                                   "update": {"running": st["running"], "finished": st["finished"], "changes": len(st["changes"])}})
            if path == "/api/setup":
                lv = levels.load()
                return self._json({"ocr": _ocr_available(), "token": _token_saved(), "session": _session_saved(), "config": config.load(),
                                   "db": database.status(), "patch": patch_info.load(), "ratings_patch": _ratings_patch(), "setup_done": setup_done(), "autostart": autostart.installed(), "last_update": database.last_update(), "version": version.info(), "levels_set": sum(1 for k in lv.values() for v in k.values() if v)})
            if path == "/api/levels":
                chars = {k: levels.characters(k) for k in levels.KINDS}
                return self._json({"ready": any(chars.values()), "characters": chars, "levels": levels.load(), "history": levels.history(), "chapters": levels.chapters(), "backups": levels.backups()})
            if path == "/api/window":
                return self._json({"goto": hub.take_goto()})
            if path == "/api/shrine":
                return self._json({"shrine": shrine.info()})
            if path == "/api/buildmaker":
                return self._json(buildmaker_data())
            if path in ("/api/builds/killers", "/api/builds/survivors"):
                f = paths.KILLERS if path.endswith("killers") else paths.SURVIVORS
                data = json.loads(f.read_text(encoding="utf8")) if f.exists() else {}
                return self._json(with_patch(data))
            return self._send(404, b"not found", "text/plain")

        # ---------- POST ----------
        def do_POST(self):
            if not self._host_ok() or self.headers.get("X-Requested-With") != "EntityToolkit":
                return self._send(403, b"forbidden", "text/plain")
            origin = self.headers.get("Origin")
            if origin and urlparse(origin).hostname not in ("127.0.0.1", "localhost"):
                return self._send(403, b"forbidden", "text/plain")
            try:
                n = int(self.headers.get("Content-Length") or 0)
                limit = 120_000_000 if urlparse(self.path).path == "/api/levels/scan" else 2_000_000  # screenshots are big
                if n > limit:
                    return self._json({"error": "request too large"}, 413)
                body = json.loads(self.rfile.read(n) or b"{}")
                self._json(self._api_post(urlparse(self.path).path, body))
            except Exception as e:
                self._json({"error": f"{type(e).__name__}: {e}"}, 400)

        def _api_post(self, path, body):
            if path == "/api/config":
                cfg = config.load()
                for key in ("capture_key", "clear_key"):
                    if key in body:
                        winapi.parse_combo(body[key])  # raises on an unknown key
                cfg.update({k: v for k, v in body.items() if k in config.DEFAULTS})
                config.save(cfg)
                return {"ok": True}
            if path == "/api/quit":  # the window was closed with "quit Entity Toolkit"
                hub.quit()
                return {"ok": True}
            if path == "/api/window/show":  # a second launch of the program: show what is already running
                if hub.opener:
                    hub.opener(str(body.get("page") or "live.html"))
                return {"ok": bool(hub.opener)}
            if path == "/api/setup/done":
                cfg = config.load()
                cfg["setup_done"] = bool(body.get("done"))
                config.save(cfg)
                return {"setup_done": cfg["setup_done"]}
            if path == "/api/token":
                paths.ensure()
                paths.NL_TOKEN.write_text(str(body.get("token", "")).strip(), encoding="utf8")
                return {"ok": True}
            if path == "/api/login":
                def go():
                    from . import review
                    review.login()
                threading.Thread(target=go, daemon=True).start()
                return {"started": True}
            if path == "/api/autostart":
                if body.get("enabled"):
                    autostart.install()
                else:
                    autostart.remove()
                return {"enabled": autostart.installed()}
            if path == "/api/update-db":
                return {"started": database.run_async(refresh=bool(body.get("refresh")))}
            if path == "/api/levels/set":
                return {"changed": levels.set_level(body["kind"], body["name"], body["level"])}
            if path == "/api/levels/scan":
                return {"cards": _scan_image(body["image"]), "ok": True}
            if path == "/api/levels/restore":
                return {"ok": levels.restore(int(body["t"]))}
            if path == "/api/levels/apply":
                if len(body["entries"]) > 5:
                    levels.snapshot("Before importing levels from screenshots")
                n = 0
                for e in body["entries"]:
                    n += bool(levels.set_level(e["kind"], e["name"], e["level"], src="screenshot"))
                    levels.set_owned(e["kind"], e["name"], True)  # it showed on your character screen with a level: you own it
                return {"changed": n}
            if path == "/api/levels/set-all":
                levels.snapshot(f"Before setting every owned {body['kind'][:-1]} to level {body['level']}")
                names = [c["short"] for c in levels.characters(body["kind"]) if c["owned"]]
                return {"changed": levels.set_many(body["kind"], {n: body["level"] for n in names}, src="manual")}
            if path == "/api/owned/set":
                return {"changed": levels.set_owned(body["kind"], body["name"], bool(body["owned"]))}
            if path == "/api/owned/chapter":
                levels.snapshot("Before changing a chapter")
                return {"changed": levels.set_chapter_owned(body["label"], bool(body["owned"]))}
            if path == "/api/owned/all":
                levels.snapshot("Before " + ("owning everything" if body["owned"] else "keeping only the base game"))
                return {"changed": levels.set_all_owned(bool(body["owned"]))}
            if path == "/api/levels/reset":
                levels.snapshot("Before resetting the levels")
                levels.reset()
                return {"ok": True}
            if path == "/api/mybuilds/save":
                return {"build": mybuilds.save(body)}
            if path == "/api/mybuilds/delete":
                return {"deleted": mybuilds.delete(body["id"])}
            if path == "/api/perktypes/set":
                perk_types.save_override(body["name"], body.get("types"))
                return {"ok": True}
            if path == "/api/levels/import":
                levels.snapshot("Before importing a JSON file")
                return {"changed": levels.import_json(body["text"])}
            return {"error": "unknown endpoint"}

    return Handler


def _ratings_patch():
    try:
        return json.loads(paths.KILLERS.read_text(encoding="utf8")).get("patch") or None
    except Exception:
        return None


def _scan_image(data_b64):
    """Reads the character cards of one screenshot (base64 of a PNG / JPEG / WebP file)."""
    import base64
    import io

    from PIL import Image

    from . import roster_scan
    img = Image.open(io.BytesIO(base64.b64decode(data_b64)))
    cur = levels.load()
    out = []
    for c in roster_scan.scan(img):
        if c["name"]:
            c["current"] = cur[c["kind"]].get(c["name"], 0)
            ch = next((x for x in levels.characters(c["kind"]) if x["short"] == c["name"]), None)
            c["portrait"] = ch["portrait"] if ch else None
            c["portrait2"] = ch["portrait2"] if ch else None
        out.append(c)
    return out


def _session_saved():
    try:
        from . import review
        return review.session_saved()
    except Exception:
        return paths.NL_PROFILE.exists()


class _Server(ThreadingHTTPServer):
    allow_reuse_address = False  # on Windows the default would let two copies listen on the same port


def start(hub, port=None):
    port = port or config.load()["port"]
    srv = _Server(("127.0.0.1", port), make_handler(hub))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{port}/"
