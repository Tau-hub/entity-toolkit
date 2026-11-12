"""Automatic mode (optional, the `auto` setting): the toolkit presses the capture key for you.

What it does, only while the game is the window in front:
 - when you press Tab, it looks a few times at a thin strip at the top left of the game's monitor; if the players menu is there, it
   does what the capture key does (perks, map, overlay);
 - every 2 seconds it looks at the same strip; when the end-of-match scoreboard is there and every player's perks are revealed (the match is over
   for everyone), it does what the capture key does on the scoreboard (NightLight upload, overlay removed).

It uses nothing new: the same screenshots of the monitor, the same key-state polling and the same process-list check as the manual key.
Nothing is read from, or sent to, the game's process. The strip is about 1/17 of the screen, and reading it takes about 30 ms, so the
cost is one short look every 2 seconds, and none at all while the game is not in front.
"""
import asyncio
import base64
import ctypes
import re
import time
from ctypes import wintypes

import mss
import numpy as np
from PIL import Image, ImageFilter

from . import ocr, winapi

STRIP = (0.0, 0.04, 0.45, 0.17)   # left, top, right, bottom of the strip holding both titles, as fractions of the game's monitor
END_EVERY = 2.0                   # seconds between two looks for the scoreboard
TAB_LOOKS = (0.1, 0.2, 0.3, 0.42, 0.55, 0.7, 0.9, 1.2, 1.6)  # after Tab: when to look for the players menu. Close together: a quick tap shows it for half a second
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


PERKS_X = (239, 318, 397, 476)   # centres of the four perk diamonds of a scoreboard row (px on a 1440-high screen)
ROW_Y, ROW_STEP = 433, 160.5     # centre of the first row's perks, distance between two rows
FILLED = 15                      # a drawn perk is a busy little picture: its grey levels vary this much (standard deviation)
EMPTY_MATCH = 0.5                # how much a slot must look like an empty diamond (1 = identical) to count as one
# What an EMPTY perk diamond looks like once the smooth background is removed (30x30, whole-number levels). Taken from the four bot rows of
# a 2560x1440 scoreboard, where every perk slot is empty. A player without perks, or a bot, shows these outlines; a row whose loadout is still
# hidden shows nothing at all.
_EMPTY_DIAMOND = np.frombuffer(base64.b64decode(
    "AP4CBQACAQEDBxgxTmkLwdPGSF49Hw0GAwD/AAAC/v4CBAQFAgEECiFAUgS+2dO5swpNLhgMBAAB/wME/Pn+AQMC/v4KGDdL"
    "4qbN1tjVxsowTikYDwQCAQT//vz//f8CAg0WLETgocDK8QjQ073HIEMwIAwCAf76/wIBAAYOGiM0ROiYusLnJTMA38K0m/xP"
    "LhoLBP/9/QIA/AUUJjJA35K6utInJxohENPSra0qRDEbDwQAAv///xIeOUX/przK4hklExETHAXZxq6qKkoqHwsIAQEEEiA3"
    "QOClwMzhER0aFg0MEhkKxrqguFJPLiMZAwUOIDVP8JjGzOQaHgsHBwMBBQ8b+cavnrQxXD0uCw8dL0oFpsXA6RsiDggEAQL+"
    "AQcOJ/21rZKiN1tGICY2RuSZr8PeEyAMAgMBAgH+BAYLEiDvq6aTr0JwKTxD+KiswekWGAsB/f8A/v7+AwQEDyEv+6qimbVE"
    "TVj/qcO73RETB/z7+v7+//38AAECCQsfOQGurq3UYQSnycrfDRIFAv39/f3+//z2+gAA/gYQIDX4usS6/6jL3OwcGQIDAwEB"
    "Af7+/Pj4+wICAQUMEREqFczPtb/S9CAkDQQDAgL/AQEAAQQA/wUC/f7+BhIhMCTtus7cHisbCAMCAgEA/vz+AQQBAQMC////"
    "CRglOVACvb3R4A4cDAb///8DBAIBAgH8/wIDBgIDChouMfPIKci5y9gMGAoBAf8ABgICAgH5+/8EAwIHDRwf37u/ZjOys73R"
    "CiMPBf7/BQECAvv8/QECBQUNJBrErK+4OVYivaS22BghFgoCBwMDAf0CAgIFCBMeIM+tsqI1HitSKq6pudEEGhoOBgMDAgMF"
    "BQQMGycVzqmlkQJ7ESAqTx2qoLS49y0TEggC+/0DBAoSJBrYs6SS71JKAw4YLEUqpIGsrgMxHQ4F//4ABhIiHMqopIUUXDwu"
    "/wQLGSpMKsKbpbkDJRsLAv0CDh0Wz6irlu9hNyYaAQQHCRchTVOunaOtAiITCQ8RGxfqsKen4l45KxsQ/P4FAQcVJ04qqp66"
    "wgMjGxofIPnArZkWYzckFAoC/f4B/QAMHjlWMK+gyuEZMysz/8i1luxWQiQTCAcEAwEBAgIJER04aDS0vdPcGTwU5sSw9F9K"
    "JhQE/v4BBgcDBwQEChMvQnJNzcjl7vvWzrrKal01IAgCAf8C"
), dtype=np.int8).reshape(30, 30).astype(float)


def _flat(img, cx, cy):
    """The 60x60 patch (at 1440p) centred on (cx, cy), in grey levels."""
    k = img.height / 1440
    return img.crop((int((cx - 30) * k), int((cy - 30) * k), int((cx + 30) * k), int((cy + 30) * k))).convert("L").resize((60, 60), Image.BICUBIC)


def diamond_match(img, cx, cy):
    """How much the slot centred on (cx, cy) looks like an empty perk diamond: 1 = the same outline, about 0 = flat or something else."""
    p = _flat(img, cx, cy)
    a = np.asarray(p, dtype=float) - np.asarray(p.filter(ImageFilter.GaussianBlur(4)), dtype=float)
    a = a.reshape(30, 2, 30, 2).mean(axis=(1, 3))
    a, b = a - a.mean(), _EMPTY_DIAMOND - _EMPTY_DIAMOND.mean()
    d = float(np.sqrt((a * a).sum() * (b * b).sum()))
    return float((a * b).sum() / d) if d > 1e-6 else 0.0


def row_state(img, i):
    """'perks' (at least one perk drawn), 'empty' (the four slots are drawn but empty: a bot, or a player without perks) or 'hidden'."""
    k = img.height / 1440
    cy = ROW_Y + ROW_STEP * i
    half = 26 * k
    for x in PERKS_X:
        g = np.asarray(img.crop((int(x * k - half), int((cy - 26) * k), int(x * k + half), int((cy + 26) * k))).convert("L"), dtype=float)
        if float(g.std()) >= FILLED:
            return "perks"
    if sum(diamond_match(img, x, cy) >= EMPTY_MATCH for x in PERKS_X) >= 2:
        return "empty"
    return "hidden"


def rows_revealed(img):
    """For the five rows of the scoreboard (four survivors, then the killer): True when the row shows its loadout.

    The game hides a player's loadout until the match is really over for everyone: a scoreboard seen earlier (you died first, or you came
    back from spectating) has rows with nothing drawn on them. Once it is over, a row shows its perk diamonds: filled, or, for a bot or a
    player who brought no perk at all, empty outlines (and the squares of the add-ons). Both count as revealed; only a blank row does not.
    """
    return [row_state(img, i) != "hidden" for i in range(5)]


def same_board(a, b):
    """Do two screenshots show the same scoreboard? The rows (left half of the screen, without the far left where the overlay is drawn)
    do not move, so two pictures of the same scoreboard are almost identical there; a window that came over it makes them differ."""
    def rows(img):
        w, h = img.size
        return np.asarray(img.crop((int(w * 0.06), int(h * 0.22), int(w * 0.55), int(h * 0.80))).convert("L").resize((160, 96)), dtype=float)
    return float(np.abs(rows(a) - rows(b)).mean()) < 6.0


def want_players(players_at, now):
    """Look for the players menu? Not when it was read a moment ago for this match."""
    return players_at is None or now - players_at > REREAD_AFTER


def want_end(end_at, now):
    """Handle a scoreboard? Not when one was handled a moment ago (the same one, seen again)."""
    return end_at is None or now - end_at > RESEND_AFTER


class Watcher:
    """The automatic loop. `press(hwnd, why, img, clean)` does what the capture key does, on the screenshot `img` (`clean`: remove the overlay first); `ast` gives the state (busy, players_at, end_at)."""

    def __init__(self, ast, press, enabled, say, log):
        self.ast, self.press, self.enabled, self.say, self.log = ast, press, enabled, say, log
        self.tab_down = False
        self.looks = []        # moments at which to look for the players menu after a Tab press
        self.next_end = 0.0
        self.confirm = 0       # looks in a row that found a finished scoreboard
        self.told = False      # "waiting for the end of the match" was said for this scoreboard

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
        if after_tab:
            # right after Tab the whole screen is taken at once, so that the picture read is the very one that showed the menu
            # (a quick tap closes it within half a second)
            img = winapi.grab_game_monitor(hwnd)
            if read_kind(strip_of(img)) == "players":
                self.looks = []
                self.press(hwnd, "players menu seen", img, False)  # the overlay stays: it is not on the part of the screen that is read
            elif not self.looks:
                self.log("Automatic: Tab pressed but the players menu was not seen (closed too fast?): press Tab again, a little longer")
            return 0.02
        kind = look(hwnd)
        if kind == "players":
            self.confirm = 0
            if want_players(self.ast.players_at, now):
                # the whole screen is taken at once and checked again: the menu may have been closed in the meantime,
                # and reading a screen without the menu would only give the "not ok" sound
                img = winapi.grab_game_monitor(hwnd)
                if read_kind(strip_of(img)) == "players":
                    self.looks = []
                    self.press(hwnd, "players menu seen", img, False)  # the overlay stays: it is not on the part of the screen that is read
        elif kind == "end":
            self.looks = []
            if not want_end(self.ast.end_at, now):
                return 0.03
            img = winapi.grab_game_monitor(hwnd)
            done = rows_revealed(img)
            if all(done):
                self.confirm += 1
                if self.confirm >= 2:  # seen complete twice in a row: the page has settled
                    self.confirm, self.told = 0, False
                    self.press(hwnd, "scoreboard seen, every player's perks are revealed", img, True)  # the overlay is removed and the screen taken again: it must not be on the picture sent
                else:
                    self.next_end = now + 0.7
            else:
                self.confirm = 0
                if not self.told:
                    self.told = True
                    left = done.count(False)
                    self.log(f"Automatic: scoreboard seen, the perks of {left} player{'s' if left > 1 else ''} are still hidden (rows {done}): waiting")
                    self.say(f"Scoreboard seen: waiting for the end of the match ({left} player{'s' if left > 1 else ''} with hidden perks). Press the capture key to send it now")
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
