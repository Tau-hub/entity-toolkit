"""Tells whether a newer Entity Toolkit is on GitHub (once a day, optional: the `check_version` setting).

It only downloads one small public file from the project's repository and reads the version number in it. Nothing is sent.
"""
import re
import threading
import time

from . import __version__, config, paths

URL = "https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/entity_toolkit/__init__.py"
PAGE = "https://github.com/Tau-hub/entity-toolkit" + ("/releases/latest" if paths.FROZEN else "")  # the .exe is replaced by downloading the new release
STATE = {"latest": None, "checked": 0}


def parse(v):
    """'0.2.1' -> (0, 2, 1); anything unreadable -> ()."""
    try:
        return tuple(int(x) for x in re.findall(r"\d+", v or "")[:4])
    except Exception:
        return ()


def newer(latest, current=__version__):
    a, b = parse(latest), parse(current)
    return bool(a) and bool(b) and a > b


def read(text):
    m = re.search(r"__version__\s*=\s*[\"']([^\"']+)[\"']", text or "")
    return m.group(1) if m else None


def check():
    import requests
    STATE["checked"] = int(time.time())
    STATE["latest"] = read(requests.get(URL, timeout=10).text)
    return STATE["latest"]


def info():
    return {"current": __version__, "latest": STATE["latest"], "newer": newer(STATE["latest"]), "page": PAGE, "exe": paths.FROZEN}


def start(log):
    """Background check: shortly after the start, then once a day while the toolkit runs."""
    def loop():
        time.sleep(20)
        while True:
            if config.load().get("check_version"):
                try:
                    latest = check()
                    if newer(latest):
                        log(f"A newer Entity Toolkit is available: {latest} (you have {__version__}) - {PAGE}")
                except Exception as e:
                    log(f"Version check skipped: {e}")
            time.sleep(24 * 3600)
    threading.Thread(target=loop, daemon=True).start()
