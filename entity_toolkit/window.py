"""The Entity Toolkit window: the pages in a window of their own instead of a browser tab (the `window` setting, on by default).

The window is a small separate program (``entity_toolkit window``) started by the toolkit: it shows the same local pages with the web
engine built into Windows (WebView2, the one Edge uses). The first time it opens in the middle of the screen at 75 % of its size (on a second screen when
there is one, so that it does not cover the game), then where you left it. Closing it either keeps the toolkit running in the notification area or quits it: it asks once, and can remember.

Without the `pywebview` package, or if the window cannot start, the pages open in the default browser as before.
"""
import importlib.util
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser

from . import config, paths

TITLE = "Entity Toolkit"
SHARE = 0.75  # of the screen, the first time


def available():
    return importlib.util.find_spec("webview") is not None


def first_geometry(screen):
    """(x, y, width, height): 75 % of the screen, in its middle. `screen` is (x, y, width, height)."""
    sx, sy, sw, sh = screen
    w, h = int(sw * SHARE), int(sh * SHARE)
    return sx + (sw - w) // 2, sy + (sh - h) // 2, w, h


def pick_screen(screens):
    """The screen the window opens on the first time: a second screen when there is one (the game plays on the main one,
    which is the screen holding the point 0, 0), else the only screen."""
    others = [s for s in screens if not (s[0] <= 0 < s[0] + s[2] and s[1] <= 0 < s[1] + s[3])]
    return (others or screens)[0]


def usable(geometry, screens):
    """A remembered place is used again only if it is a real window whose title bar is still on one of the screens
    (a second screen may have been unplugged since)."""
    try:
        x, y, w, h = (int(v) for v in geometry)
    except Exception:
        return False
    if w < 400 or h < 300:
        return False
    return any(sx - 50 <= x <= sx + sw - 150 and sy - 10 <= y <= sy + sh - 80 for sx, sy, sw, sh in screens)


def own_identity():
    """Tells Windows this program is "Entity Toolkit", not "Python": the taskbar then shows the window's own icon (the red E)
    instead of the Python logo, and does not group it with other Python programs."""
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("TauHub.EntityToolkit")
    except Exception:
        pass


def set_icon(hwnd, ico):
    """Puts the .ico on the window, small (title bar) and large (taskbar, Alt+Tab)."""
    try:
        import ctypes
        u = ctypes.windll.user32
        u.LoadImageW.restype = ctypes.c_void_p
        u.SendMessageW.argtypes = [ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p]
        for which, size in ((0, 16), (1, 48)):  # ICON_SMALL, ICON_BIG
            h = u.LoadImageW(None, str(ico), 1, size, size, 0x10)  # IMAGE_ICON, LR_LOADFROMFILE
            if h:
                u.SendMessageW(hwnd, 0x0080, which, h)  # WM_SETICON
    except Exception:
        pass


def _call(base, path, body=None):
    data = None if body is None else json.dumps(body).encode("utf8")
    req = urllib.request.Request(base + path, data=data, headers={"Content-Type": "application/json", "X-Requested-With": "EntityToolkit"})
    with urllib.request.urlopen(req, timeout=3) as r:
        return json.loads(r.read() or b"{}")


class _Api:
    """What the page may ask the window to do (the "close" question shown by the shell)."""

    def __init__(self, state):
        self._state = state

    def close(self, action, remember=False):
        """action: 'tray' (keep the toolkit running, close only the window), 'quit' (stop everything) or 'cancel'."""
        if action not in ("tray", "quit"):
            return False
        if remember:
            cfg = config.load()
            cfg["close_action"] = action
            config.save(cfg)
        self._state["decided"] = action
        threading.Thread(target=self._state["finish"], daemon=True).start()
        return True


def process_alive(pid):
    """Is the process `pid` still running?"""
    import ctypes
    k = ctypes.windll.kernel32
    k.OpenProcess.restype = ctypes.c_void_p
    h = k.OpenProcess(0x00100000, False, int(pid))  # SYNCHRONIZE
    if not h:
        return False
    try:
        return k.WaitForSingleObject(ctypes.c_void_p(h), 0) == 0x102  # WAIT_TIMEOUT: still running
    finally:
        k.CloseHandle(ctypes.c_void_p(h))


def run(page="live.html", owner=0):
    """The window program itself. Returns when the window is closed. `owner`: the toolkit that opened it; the window goes with it
    (a toolkit killed and started again must not leave its window behind: two windows, one of them dead)."""
    import webview
    from . import winapi

    for _ in range(20):  # one window only: an older one is closing (its toolkit is gone), wait for it
        if winapi.single_instance("EntityToolkitWindow"):
            break
        time.sleep(0.5)
    else:
        return 0

    own_identity()
    cfg = config.load()
    base = f"http://127.0.0.1:{cfg['port']}"
    paths.ensure()
    screens = [(s.x, s.y, s.width, s.height) for s in webview.screens] or [(0, 0, 1920, 1080)]
    x, y, w, h = cfg.get("window_geometry") if usable(cfg.get("window_geometry"), screens) else first_geometry(pick_screen(screens))
    state = {"decided": None}
    webview.settings["ALLOW_DOWNLOADS"] = True                 # "Download PNG" on the random-loadout page
    webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True  # GitHub, NightLight...: in your own browser
    win = webview.create_window(TITLE, f"{base}/app.html#{page}", js_api=_Api(state), x=x, y=y, width=w, height=h, min_size=(720, 480),
                                background_color="#0b0e12", text_select=True, zoomable=True)

    def finish():
        if state["decided"] == "quit":
            try:
                _call(base, "/api/quit", {})
            except Exception:
                pass
        win.destroy()

    state["finish"] = finish

    def remember_place():
        try:
            c = config.load()
            c["window_geometry"] = [int(win.x), int(win.y), int(win.width), int(win.height)]
            config.save(c)
        except Exception:
            pass

    def on_closing():
        remember_place()
        if state["decided"]:
            return True
        action = config.load().get("close_action") or "ask"
        if action in ("tray", "quit"):
            state["decided"] = action
            if action == "quit":
                threading.Thread(target=lambda: _call(base, "/api/quit", {}), daemon=True).start()
            return True
        # ask: the window stays, and the page shows the question (answered through _Api.close)
        threading.Thread(target=lambda: win.evaluate_js("window.etShell && window.etShell.askClose()"), daemon=True).start()
        return False

    win.events.closing += on_closing

    def orders():
        """The toolkit can ask the window to come back in front on a page (notification-area icon), or to close (the toolkit stops)."""
        misses = 0
        while True:
            time.sleep(0.5)
            if owner and not process_alive(owner):
                state["decided"] = state["decided"] or "tray"
                win.destroy()
                return
            try:
                o = _call(base, "/api/window")
                misses = 0
            except Exception:
                misses += 1
                if misses >= 6:  # the toolkit is gone: nothing left to show
                    state["decided"] = state["decided"] or "tray"
                    win.destroy()
                    return
                continue
            if o.get("goto"):
                try:
                    win.restore()
                    win.show()
                    win.evaluate_js(f"window.etShell && window.etShell.go({json.dumps(o['goto'])})")
                except Exception:
                    pass

    icon = None
    try:
        from . import tray
        icon = paths.DATA / "entity_toolkit.ico"
        if not icon.exists():
            tray._image().resize((256, 256)).save(icon, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])
    except Exception:
        icon = None
    def started():
        threading.Thread(target=orders, daemon=True).start()
        if icon:
            try:
                import ctypes
                hwnd = int(win.native.Handle.ToInt64()) if getattr(win, "native", None) is not None else ctypes.windll.user32.FindWindowW(None, TITLE)
                set_icon(hwnd, icon)
            except Exception:
                pass

    webview.start(started, private_mode=False, storage_path=str(paths.DATA / "window_profile"),
                  icon=str(icon) if icon else None)
    return 0


class Launcher:
    """Used by the toolkit itself: opens the window (or the browser), knows whether the window is open."""

    def __init__(self, url, hub, log):
        self.url, self.hub, self.log = url, hub, log
        self.proc = None
        self.lock = threading.Lock()

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def open(self, page="live.html"):
        """Shows `page`: in the window when it is turned on and available, in the default browser otherwise."""
        if not config.load().get("window") or not available():
            webbrowser.open(self.url + "app.html#" + page)
            return
        with self.lock:
            if self.alive():
                self.hub.window_goto(page)  # the open window comes back in front on that page
                return
            from . import autostart
            try:
                self.proc = subprocess.Popen(autostart.command() + ["window", "--page", page, "--owner", str(os.getpid())], cwd=str(paths.ROOT))
                threading.Thread(target=self._watch, args=(self.proc, page, time.time()), daemon=True).start()
            except Exception as e:
                self.log(f"The window could not be started ({e}): opening the browser instead")
                webbrowser.open(self.url + "app.html#" + page)

    def _watch(self, proc, page, started):
        code = proc.wait()
        if code not in (0, None) and time.time() - started < 8:  # it died at once: WebView2 missing?
            self.log(f"The window stopped right away (code {code}): opening the browser instead. Turn 'Use the Entity Toolkit window' off in Settings to always use the browser")
            webbrowser.open(self.url + "app.html#" + page)

    def close(self):
        if self.alive():
            try:
                self.proc.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    sys.exit(run())
