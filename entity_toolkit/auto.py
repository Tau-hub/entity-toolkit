"""Automatic mode (optional, the `auto` setting): the toolkit presses the capture key for you.

What it does, only while the game is the window in front:
 - when you press Tab, it looks a few times at a thin strip at the top left of the game's monitor; if the players menu is there, it
   does what the capture key does (perks, map, overlay);
 - every 2 seconds it looks at the same strip; when the end-of-match scoreboard is there and every survivor has finished (a status
   icon on each of the four rows), it does what the capture key does on the scoreboard (NightLight upload, overlay removed).

It uses nothing new: the same screenshots of the monitor, the same key-state polling and the same process-list check as the manual key.
Nothing is read from, or sent to, the game's process. The strip is about 1/17 of the screen, and reading it takes about 30 ms, so the
cost is one short look every 2 seconds, and none at all while the game is not in front.
"""
import asyncio
import ctypes
import re
import time
from ctypes import wintypes

import mss
import numpy as np
from PIL import Image

from . import ocr, winapi

STRIP = (0.0, 0.04, 0.45, 0.17)   # left, top, right, bottom of the strip holding both titles, as fractions of the game's monitor
END_EVERY = 2.0                   # seconds between two looks for the scoreboard
TAB_LOOKS = (0.35, 0.9, 1.6)      # after Tab: when to look for the players menu (it takes a moment to open)
REREAD_AFTER = 300                # once the players menu was read, Tab does not read it again for 5 minutes (you reopen it during the match)
RESEND_AFTER = 150                # once a scoreboard was handled, another one is not handled for 2.5 minutes (leaving the page and coming back)
VK_TAB = 0x09


def kind_of(text):
    """'end', 'players' or None from the text of the strip (same rule as the capture key)."""
    text = text.upper()
    if "SCOREBOARD" in text:
        return "end"
    if re.search(r"\bPLAY(ERS)?\b", text) and ("QUESTS" in text or "POWER" in text):
        return "players"
    return None


def _monitor(sct, hwnd):
    r = wintypes.RECT()
    winapi.user32.GetWindowRect(hwnd, ctypes.byref(r))
    cx, cy = (r.left + r.right) // 2, (r.top + r.bottom) // 2
    return next((m for m in sct.monitors[1:] if m["left"] <= cx < m["left"] + m["width"] and m["top"] <= cy < m["top"] + m["height"]), sct.monitors[1])


def strip_of(img):
    w, h = img.size
    return img.crop((int(w * STRIP[0]), int(h * STRIP[1]), int(w * STRIP[2]), int(h * STRIP[3])))


def read_kind(strip):
    return kind_of(" ".join(asyncio.run(ocr._ocr(strip))))


def look(hwnd):
    """Which screen the game shows, from the strip only: 'end', 'players' or None."""
    with mss.mss() as sct:
        m = _monitor(sct, hwnd)
        box = {"left": m["left"] + int(m["width"] * STRIP[0]), "top": m["top"] + int(m["height"] * STRIP[1]),
               "width": int(m["width"] * (STRIP[2] - STRIP[0])), "height": int(m["height"] * (STRIP[3] - STRIP[1]))}
        shot = sct.grab(box)
    return read_kind(Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX"))


def survivors_done(img):
    """For the four survivor rows of the scoreboard: True when the row shows a status icon (escaped, dead, disconnected...) left of the
    name. The icons are white on a dark bar, so a row still without one has almost no bright pixel there."""
    k = img.height / 1440
    out = []
    for i in range(4):
        cx, cy, half = 235 * k, (355 + 160.5 * i) * k, 22 * k
        g = np.asarray(img.crop((int(cx - half), int(cy - half), int(cx + half), int(cy + half))).convert("L"))
        out.append(float((g > 175).mean()) >= 0.06)
    return out


def want_players(players_at, now):
    """Look for the players menu? Not when it was read a moment ago for this match."""
    return players_at is None or now - players_at > REREAD_AFTER


def want_end(end_at, now):
    """Handle a scoreboard? Not when one was handled a moment ago (the same one, seen again)."""
    return end_at is None or now - end_at > RESEND_AFTER


class Watcher:
    """The automatic loop. `press(hwnd, why, img)` does what the capture key does, on the screenshot `img`; `ast` gives the state (busy, players_at, end_at)."""

    def __init__(self, ast, press, enabled, say, log):
        self.ast, self.press, self.enabled, self.say, self.log = ast, press, enabled, say, log
        self.tab_down = False
        self.looks = []        # moments at which to look for the players menu after a Tab press
        self.next_end = 0.0
        self.confirm = 0       # looks in a row that found a finished scoreboard
        self.told = False      # "waiting for the survivors" was said for this scoreboard

    def step(self, now):
        """One turn of the loop; returns how long to sleep."""
        if not self.enabled():
            self.looks, self.confirm = [], 0
            return 0.5
        tab = winapi.combo_down([VK_TAB])
        if tab and not self.tab_down and want_players(self.ast.players_at, now):
            self.looks = [now + d for d in TAB_LOOKS]
        self.tab_down = tab
        after_tab = bool(self.looks) and now >= self.looks[0]
        if not after_tab and now < self.next_end:
            return 0.03
        if after_tab:
            self.looks.pop(0)
        else:
            self.next_end = now + END_EVERY
        hwnd = winapi.game_in_front()
        if not hwnd or self.ast.busy.locked():
            return 0.03
        kind = look(hwnd)
        if kind == "players":
            self.confirm = 0
            if want_players(self.ast.players_at, now):
                # the whole screen is taken at once and checked again: a quick tap on Tab may already have closed the menu,
                # and reading a screen without the menu would only give the "not ok" sound
                img = winapi.grab_game_monitor(hwnd)
                if read_kind(strip_of(img)) == "players":
                    self.looks = []
                    self.press(hwnd, "players menu seen", img)
        elif kind == "end":
            self.looks = []
            if not want_end(self.ast.end_at, now):
                return 0.03
            img = winapi.grab_game_monitor(hwnd)
            done = survivors_done(img)
            if all(done):
                self.confirm += 1
                if self.confirm >= 2:  # seen finished twice in a row: the page has settled
                    self.confirm, self.told = 0, False
                    self.press(hwnd, "scoreboard seen, every survivor has finished", img)
                else:
                    self.next_end = now + 0.7
            else:
                self.confirm = 0
                if not self.told:
                    self.told = True
                    left = done.count(False)
                    self.log(f"Automatic: scoreboard seen, {left} survivor{'s' if left > 1 else ''} still in the trial: waiting")
                    self.say(f"Scoreboard seen: waiting for {left} survivor{'s' if left > 1 else ''} to finish (press the capture key to send it now)")
        else:
            self.confirm, self.told = 0, False
        return 0.03

    def run(self):
        while True:
            try:
                pause = self.step(time.time())
            except Exception as e:
                self.log(f"Automatic mode: {type(e).__name__}: {e}")
                pause = 2.0
            time.sleep(pause)
