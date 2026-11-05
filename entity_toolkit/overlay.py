"""Overlay: the allies' perks drawn over the game's own survivor list (survivor view only).

A transparent, borderless, always-on-top window that never takes focus and lets clicks through. It does not touch the game's
process: it is just a window laid over it (like the Discord overlay). Pressing the capture key again, or the clear key, removes it.

Layout in pixels of a 2560x1440 screen, scaled with the game screen's height; override it in data/overlay_layout.json:
  x    : left edge of the 2x2 icon grid (in the margin left of the list's portraits)
  dy   : vertical shift of the grids relative to the row (negative = up); portraits sit a bit above the text
  rows : vertical centre of each row of the list, top to bottom (4 rows; each ally is drawn on the row they have in the players menu, yours is skipped)
  size : icon size; gap: space between two icons
"""
import ctypes
import difflib
import itertools
import json
import queue
import re
import threading
import time
import tkinter as tk
from ctypes import wintypes

import numpy as np
from PIL import Image, ImageDraw, ImageTk

from . import ocr, paths, recognize as rc

REF_H = 1440
DEFAULT = {"x": 6, "rows": [622, 740, 858, 975], "dy": -19, "size": 52, "gap": 3}
KEY = "#010203"  # colour made transparent
user32 = ctypes.windll.user32
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT, WS_EX_NOACTIVATE, WS_EX_TOOLWINDOW, WS_EX_LAYERED = 0x20, 0x08000000, 0x80, 0x80000
PORTRAIT_MARGIN = 0.15  # below this gap the portraits are not decisive enough: use the player names


def layout():
    try:
        return {**DEFAULT, **json.loads(paths.OVERLAY_LAYOUT.read_text(encoding="utf8"))}
    except Exception:
        return dict(DEFAULT)


def _gradient(size, c0, c1):
    """Diagonal gradient, light at the top left like the game's lit perk frame."""
    yy, xx = np.mgrid[0:size, 0:size]
    t = (xx + yy) / (2.0 * max(size - 1, 1))
    arr = np.stack([(c0[i] + (c1[i] - c0[i]) * t).astype(np.uint8) for i in range(3)], axis=-1)
    return Image.fromarray(arr, "RGB")


def _badge(icon, size):
    """Perk icon the way the game draws it: a lit violet frame with a thick dark border and a big glyph. Opaque; the corners use the
    transparent key colour so the badge looks rounded."""
    k = 4  # drawn at 4x then reduced, for smooth edges
    big = size * k
    corner = Image.new("RGB", (big, big), (1, 2, 3))
    mask = Image.new("L", (big, big), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, big - 1, big - 1), radius=9 * k, fill=255)
    base = Image.new("RGB", (big, big), (8, 6, 10))                      # dark border
    inner = Image.new("L", (big, big), 0)
    ImageDraw.Draw(inner).rounded_rectangle((3 * k, 3 * k, big - 1 - 3 * k, big - 1 - 3 * k), radius=7 * k, fill=255)
    base.paste(_gradient(big, (142, 78, 170), (58, 28, 80)), (0, 0), inner)
    ic = Image.open(paths.ICONS / icon).convert("RGBA")
    if ic.getbbox():
        ic = ic.crop(ic.getbbox())
    f = min(big * 0.82 / ic.width, big * 0.82 / ic.height)
    ic = ic.resize((max(1, int(ic.width * f)), max(1, int(ic.height * f))), Image.LANCZOS)
    base.paste(ic, ((big - ic.width) // 2, (big - ic.height) // 2), ic)
    corner.paste(base, (0, 0), mask)
    return corner.resize((size, size), Image.LANCZOS)


def _norm(t):
    return re.sub(r"[^a-z0-9]", "", t.lower())


def hud_names(img):
    """Player names read in the game's left-hand list (one string per row, empty if unreadable)."""
    cfg = layout()
    s = img.height / REF_H
    out = []
    for cy in cfg["rows"]:
        crop = img.crop((int(240 * s), int((cy - 26) * s), int(470 * s), int((cy + 26) * s)))
        try:
            lines = ocr.read_lines(crop.resize((crop.width * 3, crop.height * 3), Image.LANCZOS))
        except Exception:
            lines = []
        out.append(" ".join(lines).strip())
    return out


def _feat(im):
    a = np.asarray(im.resize((24, 24), Image.LANCZOS).convert("RGB"), dtype=float)
    a = a - a.mean(axis=(0, 1))
    return (a / (np.linalg.norm(a) or 1)).ravel()


def menu_portrait(img, ri):
    """Portrait of row ri of the players menu."""
    s = img.height / rc.REF_H
    cx, cy, r = rc.cx_of(img, 676), (rc.ROWS_Y[ri] - 20) * s, 30 * s
    return img.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r)))


def hud_portrait(img, slot):
    """Portrait of row `slot` of the game's left-hand list."""
    s = img.height / REF_H
    cx, cy, r = 170 * s, (layout()["rows"][slot] - 14) * s, 36 * s
    return img.crop((int(cx - r), int(cy - r), int(cx + r), int(cy + r)))


def _scores(allies, free, menu_img, hud_img):
    return {(a["row"], sl): float(_feat(menu_portrait(menu_img, a["row"])) @ _feat(hud_portrait(hud_img, sl))) for a in allies for sl in free}


def _best_assign(allies, free, sc):
    """Best overall assignment (total similarity) and the gap to the 2nd best: a small gap means the portraits are not discriminating."""
    tots = sorted(((sum(sc[(a["row"], sl)] for a, sl in zip(allies, perm)), perm) for perm in itertools.permutations(free, len(allies))), reverse=True)
    if not tots:
        return {}, 0.0
    margin = tots[0][0] - tots[1][0] if len(tots) > 1 else 9.0
    return {a["row"]: sl for a, sl in zip(allies, tots[0][1])}, margin


def _by_pseudo(allies, free, names):
    out = {}
    for a in allies:
        p = _norm(a.get("player") or "")
        best, score = None, 0.6
        for i in free:
            n = _norm(names[i])
            if len(p) >= 3 and len(n) >= 3:
                r = difflib.SequenceMatcher(None, p, n).ratio()
                if r >= score:
                    best, score = i, r
        if best is not None:
            out[a["row"]] = best
            free.remove(best)
    return out


def place(allies, names, me_row, menu_img=None, hud_img=None):
    """Row of the game's left-hand list for each ally (your row stays where it is in the menu).
    Order: 1) portrait, for characters that are not duplicated among the allies; 2) player name, for duplicates (two of the same
    survivor) and when portraits are not decisive; 3) menu order for what is left. Returns None until the list is readable
    (at least 2 names read on the left)."""
    free = [i for i in range(len(names)) if i != me_row]
    if sum(1 for i in free if len(_norm(names[i])) >= 3) < min(2, len(free)):
        return None  # the left-hand list is not visible yet (Tab menu open): keep waiting
    count = {}
    for a in allies:
        count[a.get("survivor")] = count.get(a.get("survivor"), 0) + 1
    dups = [a for a in allies if count[a.get("survivor")] > 1 or not a.get("survivor")]
    uniq = [a for a in allies if a not in dups]
    out = _by_pseudo(dups, free, names)  # duplicates differ only by their player name
    left = list(uniq)
    if left and menu_img is not None and hud_img is not None and len(free) >= len(left):
        try:
            assign, margin = _best_assign(left, free, _scores(left, free, menu_img, hud_img))
            if margin >= PORTRAIT_MARGIN:
                out.update(assign)
                free = [f for f in free if f not in assign.values()]
                left = []
        except Exception:
            pass
    if left:  # portraits not decisive: player name, then portrait for what is left
        got = _by_pseudo(left, free, names)
        out.update(got)
        left = [a for a in left if a["row"] not in got]
        if left and menu_img is not None and hud_img is not None and len(free) >= len(left):
            try:
                out.update(_best_assign(left, free, _scores(left, free, menu_img, hud_img))[0])
            except Exception:
                pass
    rest = iter([f for f in free if f not in out.values()])
    for a in allies:
        if a["row"] not in out:
            out[a["row"]] = next(rest, a["row"])
    return out


class Overlay:
    """Tk lives in its own thread; everything goes through a command queue."""

    def __init__(self, log=print):
        self.log = log
        self.q = queue.Queue()
        self.visible = False
        self.gen = 0  # changes on every removal: stops a wait in progress
        self.pending = False
        threading.Thread(target=self._loop, daemon=True).start()

    def watch(self, allies, me_row, grab, game_hwnd, menu_img=None, timeout=240):
        """Waits for the game's left-hand list to be visible (Tab menu closed), reads the names and puts each grid on the right survivor."""
        self.gen += 1
        gen = self.gen
        self.pending = True
        self.log(f"Overlay: waiting for the game's list (looking for {[a.get('player') for a in allies]}, your row: {me_row})")

        def run():
            t0, tries, names = time.time(), 0, []
            try:
                while gen == self.gen and time.time() - t0 < timeout:
                    hud = grab()
                    names = hud_names(hud)
                    tries += 1
                    mapping = place(allies, names, me_row, menu_img, hud)
                    if tries <= 3 or tries % 10 == 0:
                        self.log(f"Overlay: try {tries} · read on the left: {names} · {'placement ' + str(mapping) if mapping else 'list not visible yet (Tab menu open?)'}")
                    if mapping and gen == self.gen:
                        self.log(f"Game list read: {names} · placement {mapping}")
                        self.show([{**a, "row": mapping[a["row"]]} for a in allies], game_hwnd)
                        return
                    time.sleep(1.2)
                if gen != self.gen:
                    self.log("Overlay: wait cancelled")
                else:
                    self.log(f"Overlay: game list not found after {tries} tries (last read: {names})")
            except Exception as e:
                self.log(f"Overlay: error while waiting: {e}")
            finally:
                if gen == self.gen and not self.visible:
                    self.pending = False

        threading.Thread(target=run, daemon=True).start()

    def show(self, allies, game_hwnd):
        """allies: the analysis result's list; a["row"] is the row (0 to 3, top to bottom) of the game's left-hand list."""
        icons = {a["row"]: [p["icon"] for p in a["perks"]] for a in allies}
        r = wintypes.RECT()
        user32.GetWindowRect(game_hwnd, ctypes.byref(r))
        self.visible = True
        self.q.put(("show", icons, (r.left, r.top, r.right - r.left, r.bottom - r.top)))

    def hide(self):
        was = self.visible or self.pending
        self.visible = self.pending = False
        self.gen += 1
        self.q.put(("hide",))
        return was

    def _loop(self):
        try:
            root = tk.Tk()
            root.withdraw()
            root.overrideredirect(True)
            root.attributes("-topmost", True)
            root.configure(bg=KEY)
            root.attributes("-transparentcolor", KEY)
            canvas = tk.Canvas(root, bg=KEY, highlightthickness=0, bd=0)
            canvas.pack(fill="both", expand=True)
            photos = []

            def style():  # click-through, never focused, absent from the taskbar
                hwnd = user32.GetParent(root.winfo_id()) or root.winfo_id()
                ex = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex | WS_EX_TRANSPARENT | WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW | WS_EX_LAYERED)

            def poll():
                try:
                    while True:
                        cmd = self.q.get_nowait()
                        if cmd[0] == "hide":
                            root.withdraw()
                            canvas.delete("all")
                            photos.clear()
                        else:
                            self._draw(root, canvas, photos, style, cmd[1], cmd[2])
                except queue.Empty:
                    pass
                root.after(50, poll)

            poll()
            root.mainloop()
        except Exception as e:
            self.log(f"Overlay: error {e}")

    def _draw(self, root, canvas, photos, style, icons, rect):
        try:
            cfg = layout()
            left, top, w, h = rect
            s = h / REF_H
            size, gap = int(cfg["size"] * s), int(cfg["gap"] * s)
            rows = [r + cfg["dy"] for r in cfg["rows"]]  # dy only moves the drawing (name / portrait reading keeps the original rows)
            canvas.delete("all")
            photos.clear()
            width = 2 * size + gap + 4
            block = 2 * size + gap  # 2x2 grid centred on each survivor's row
            y0 = int(rows[0] * s) - block // 2
            y1 = int(rows[-1] * s) + block // 2
            icons = {k: v for k, v in icons.items() if k < len(rows)}
            root.geometry(f"{width}x{y1 - y0}+{left + int(cfg['x'] * s)}+{top + y0}")
            canvas.config(width=width, height=y1 - y0)
            for i, row_icons in icons.items():
                cy = int(rows[i] * s) - y0
                for j, ic in enumerate(row_icons[:4]):
                    ph = ImageTk.PhotoImage(_badge(ic, size))
                    photos.append(ph)
                    canvas.create_image(2 + (j % 2) * (size + gap), cy - block // 2 + (j // 2) * (size + gap), image=ph, anchor="nw")
            root.deiconify()
            root.update_idletasks()
            style()
            root.attributes("-topmost", True)
            self.log(f"Overlay shown: {len(icons)} allies")
        except Exception as e:
            self.log(f"Overlay: cannot draw: {e}")
