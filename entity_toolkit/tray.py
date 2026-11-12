"""A small icon in the Windows notification area while the toolkit runs: open the pages, the settings, or quit.

Optional: needs the `pystray` package (in requirements.txt). Without it, or with the `tray` setting off, the toolkit runs exactly as before.
"""
import webbrowser

from . import __version__


# Same pages, same order as the navigation bar (web/nav.js). A double click on the icon opens the first one.
PAGES = [
    ("live.html", "Live"),
    ("levels.html", "Levels"),
    ("priorities.html?kind=killers", "Killer priorities"),
    ("priorities.html?kind=survivors", "Survivor priorities"),
    ("killer.html", "Killer sheet"),
    ("survivor_builds.html", "Survivor builds"),
    ("loadout.html", "Random loadout"),
    ("buildmaker.html", "Build creator"),
]


def _opener(address):
    return lambda: webbrowser.open(address)


def _image():
    from PIL import Image, ImageDraw
    im = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((2, 2, 62, 62), fill=(18, 20, 26, 255), outline=(209, 36, 58, 255), width=5)
    d.rectangle((21, 19, 27, 45), fill=(240, 240, 240, 255))  # an "E"
    for y, x1 in ((19, 43), (29, 38), (40, 43)):
        d.rectangle((23, y, x1, y + 5), fill=(240, 240, 240, 255))
    return im


def start(url, hub, log, open_page=None):
    """Shows the icon; returns it (call .stop() when leaving) or None when it cannot be shown.
    `open_page(page)` shows a page (the Entity Toolkit window, or the browser); without it the browser is used."""
    show = open_page or (lambda page: webbrowser.open(url + "app.html#" + page))
    go = lambda page: (lambda: show(page))
    try:
        import pystray
    except Exception:
        log("No tray icon: the pystray package is not installed (pip install pystray)")
        return None
    try:
        item = pystray.MenuItem
        icon = pystray.Icon("entity_toolkit", _image(), f"Entity Toolkit {__version__}", pystray.Menu(
            *[item(label, go(page), default=page == "live.html") for page, label in PAGES],
            pystray.Menu.SEPARATOR,
            item("Today's killer challenge", go("loadout.html?daily=K")),
            item("Today's survivor challenge", go("loadout.html?daily=S")),
            pystray.Menu.SEPARATOR,
            item("Settings", go("setup.html")),
            pystray.Menu.SEPARATOR,
            item("Quit Entity Toolkit", lambda: hub.quit()),
        ))
        icon.run_detached()
        return icon
    except Exception as e:
        log(f"No tray icon: {e}")
        return None
