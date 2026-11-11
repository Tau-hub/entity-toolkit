"""Command line: ``python -m entity_toolkit [run | update-db | login | test-image PATH | setup]`` (``run`` is the default)."""
import argparse
import sys
import webbrowser


def main(argv=None):
    ap = argparse.ArgumentParser(prog="entity_toolkit", description="Unofficial companion for Dead by Daylight.")
    sub = ap.add_subparsers(dest="cmd")
    run = sub.add_parser("run", help="start the toolkit (default): hotkeys + local web pages; stops by itself when the game closes")
    run.add_argument("--no-open", action="store_true", help="do not open the web page")
    run.add_argument("--keep-running", action="store_true", help="do not stop when the game closes")
    upd = sub.add_parser("update-db", help="download perks, icons, maps, builds and ratings (run once, then after each patch)")
    upd.add_argument("--only", nargs="+", choices=["patch", "builds", "perks", "loadout", "maps", "nl_maps"], help="run only these steps")
    upd.add_argument("--refresh", action="store_true", help="re-download the wiki pages even if cached")
    sub.add_parser("login", help="open NightLight so you can sign in (once)")
    sub.add_parser("setup", help="open the Setup page")
    auto = sub.add_parser("autostart", help="start the toolkit by itself when the game starts (Windows Startup folder)")
    auto.add_argument("action", choices=["install", "remove"])
    sub.add_parser("watch", help="(used by autostart) start the toolkit whenever the game launches")
    serve = sub.add_parser("serve", help="only serve the web pages (no hotkeys, no capture): handy to browse the data without the game")
    serve.add_argument("--demo", action="store_true", help="show a made-up players-menu result on the Live page")
    test = sub.add_parser("test-image", help="analyse a screenshot as if you had pressed the key (dry run, nothing is sent)")
    test.add_argument("image")
    a = ap.parse_args(argv)
    cmd = a.cmd or "run"

    if cmd == "update-db":
        from . import database
        res = database.run(only=a.only, refresh=a.refresh)
        return 1 if any(res.values()) else 0
    if cmd == "login":
        from . import review
        from .log import log
        return 0 if review.login(log) else 1
    if cmd == "test-image":
        return _test_image(a.image)
    if cmd == "autostart":
        from . import autostart
        if a.action == "install":
            print("Installed:", autostart.install(), "- it takes effect at your next Windows sign-in (or run: python -m entity_toolkit watch)")
        else:
            print("Removed." if autostart.remove() else "Nothing to remove.")
        return 0
    if cmd == "watch":
        from . import autostart
        autostart.watch()
        return 0
    if cmd == "serve":
        return _serve(a.demo)
    return _run(open_page=not getattr(a, "no_open", False) and cmd == "run", stop_with_game=not getattr(a, "keep_running", False), setup=cmd == "setup")


def _test_image(path):
    from PIL import Image
    from . import analyzer, assistant

    class Hub:
        def status(self, m): print("[status]", m)
        def result(self, r): print("[perks]", [[p["perks"][0]["name"] for p in al["perks"]] for al in r["allies"]], "map:", r["map"])
        def quit(self): pass

    ast = assistant.Assistant(Hub(), analyzer.Analyzer(), override={"dry_run": True})
    ast.handle(Image.open(path).convert("RGB"))
    return 0


def _serve(demo=False):
    from . import config, server
    from .log import log
    hub = server.Hub()  # no mutex here: `serve` has no hotkeys, so it cannot double-handle a key press; the port check is enough
    try:
        url = server.start(hub, config.load()["port"])
    except OSError:
        log("Port busy: another copy is running")
        return 1
    log(f"Pages only (no hotkeys): {url}")
    if demo:
        from . import demo as demo_mod
        hub.result(demo_mod.result())
    try:
        hub.wait()
    except KeyboardInterrupt:
        pass
    return 0


def _run(open_page, stop_with_game, setup=False):
    from . import analyzer, assistant, config, overlay, paths, server, winapi
    from .log import log
    paths.ensure()
    cfg = config.load()
    if not winapi.single_instance():  # e.g. run.bat, then the autostart watcher launching another copy when the game starts
        log("Entity Toolkit is already running: this second copy stops (one copy only, so a key press is handled once)")
        if setup:
            webbrowser.open(f"http://127.0.0.1:{cfg['port']}/setup.html")
        return 1
    if not paths.CONFIG.exists():
        config.save(cfg)
    hub = server.Hub()
    try:
        url = server.start(hub, cfg["port"])
    except OSError:
        log(f"Entity Toolkit is already running (port {cfg['port']} is busy): stopping this second copy")
        if setup:
            webbrowser.open(f"http://127.0.0.1:{cfg['port']}/setup.html")
        return 1
    log(f"Pages: {url}")
    ready = server.db_ready()
    ana = None
    if ready:
        try:
            ana = analyzer.Analyzer()
        except Exception as e:
            log(f"Perk database could not be loaded: {e}")
            ready = False
    ast = assistant.Assistant(hub, ana, overlay.Overlay(log))
    from . import database

    def reload_recogniser():  # new perks and icons: rebuild the recogniser from the fresh data (swapped in one assignment, never half-built)
        if server.db_ready():
            ast.analyzer = analyzer.Analyzer()
            log("Recogniser reloaded with the updated perk database")
    database.ON_FINISH.append(reload_recogniser)
    database.start_auto_update(log)
    from . import tray, version
    version.start(log)
    icon = tray.start(url, hub, log) if cfg["tray"] else None
    label = assistant.run(hub, ast, stop_with_game=stop_with_game)
    log(f"Entity Toolkit ready: {label} · {'dry run' if cfg['dry_run'] or not cfg['upload'] else 'real upload'}")
    if not ready:
        log("The perk database is missing: open the Setup page and press 'Update database'.")
    if setup or not ready:
        webbrowser.open(url + "setup.html")
    elif open_page and cfg["open_browser"]:
        webbrowser.open(url + "live.html")
    try:
        hub.wait()
    except KeyboardInterrupt:
        pass
    if icon:
        icon.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
