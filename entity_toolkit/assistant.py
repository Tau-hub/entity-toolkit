"""The assistant: one key does everything during and after a match.

Pressing the capture key (default Alt + Numpad 7, only when the game is running AND in front) makes the toolkit look at which screen is shown
(text at the top left):
 - players menu ("PLAYERS" / "QUESTS"): the map is read and remembered (survivor or killer); as survivor the allies' perks are shown on the
   live page and drawn over the game's survivor list;
 - end-of-match scoreboard ("MATCH SCOREBOARD"): the screenshot is sent to NightLight, then "Me" is ticked on your name, the others are set to
   Random, the remembered map is set and the review is confirmed;
 - any other screen: the "not ok" sound; nothing is sent.
The key never removes the overlay during a match: only the scoreboard (match over) or the clear key (default Alt + Numpad 8) does; a new players-menu press replaces it.
"""
import difflib
import json
import re
import threading
import time

from . import analyzer as an, captures, config, levels, nightlight, ocr, paths, review, sounds, winapi
from .log import log
from .text import norm

COOLDOWN = 0  # seconds between two uploads (0 = off)


def classify(img):
    """'end' (scoreboard), 'players' (in-game players menu) or None, from the text at the top left."""
    w, h = img.size
    text = " ".join(ocr.read_lines(img.crop((0, 0, int(w * 0.45), int(h * 0.24))))).upper()
    log(f"Screen {w}x{h} · text at the top left: {text!r}")
    if "SCOREBOARD" in text:
        return "end"
    if re.search(r"\bPLAY(ERS)?\b", text) and ("QUESTS" in text or "POWER" in text):  # "PLAY": truncated reading of PLAYERS
        return "players"
    return None


def _survivor_surnames():
    return [(n, norm(n.split()[-1])) for n in an.survivor_names()]


def names_on_screen(img):
    """Survivors whose surname is readable on screen (players menu or scoreboard): used to tell whether it is the same match."""
    w, h = img.size
    words = set()
    for ln in ocr.read_lines(img.crop((0, int(h * 0.12), w, int(h * 0.97)))):
        words.update(norm(t) for t in ln.split())
    found = set()
    for name, sur in _survivor_surnames():
        if len(sur) >= 4 and any(difflib.SequenceMatcher(None, sur, t).ratio() >= 0.85 for t in words if len(t) >= 3):
            found.add(name)
    return found


def same_match(mem_names, now_names):
    """True / False when the survivors read before and after tell it is the same match (or not), None when there is too little to decide."""
    a, b = set(mem_names), set(now_names)
    common = len(a & b)
    if common >= 2:
        return True
    if common == 0 and a and len(b) >= 3:
        return False  # readable survivors on both sides and none in common
    if common == 1 and len(a) >= 3 and len(b) >= 3:
        return False
    return None


def own_row(img, pseudo):
    """Rank (0 = top row, 4 = bottom row) of your name on the scoreboard, read by OCR; None if not found."""
    w, h = img.size
    top = int(h * 0.2)
    k = h / 1440
    n = norm(pseudo)
    if not n:
        return None
    for ln in ocr.read_words(img.crop((0, top, int(w * 0.6), h))):
        for t, x, y, bw, bh in ln:
            if norm(t) == n or difflib.SequenceMatcher(None, norm(t), n).ratio() >= 0.8:
                idx = round((y + top - 344 * k) / (160.5 * k))
                return idx if 0 <= idx <= 4 else None
    return None


class Assistant:
    def __init__(self, hub, analyzer=None, overlay=None, override=None):
        self.hub = hub
        self.override = override or {}  # settings forced for this run (used by test-image)
        self.analyzer = analyzer
        self.overlay = overlay
        self.hwnd = None
        self.busy = threading.Lock()
        self.last_upload = 0.0
        self.overlay_was_on = False  # this press has just removed the overlay
        self.last_menu = None  # (allies, your row, menu screenshot, time) of the last press in the players menu

    @property
    def cfg(self):
        return {**config.load(), **self.override}

    def say(self, msg):
        self.hub.status(msg)

    # ----- dispatch -----
    def handle(self, img):
        kind = classify(img)
        log(f"Screen recognised: {kind or 'none'}")
        threading.Thread(target=captures.save, args=(img.copy(), kind or "other"), daemon=True).start()  # rotation of the last captures, off the critical path
        if kind == "players":
            self.on_players(img)
        elif kind == "end":
            self.last_menu = None  # the match is over: its perks must never come back (not as an overlay, not as mouse checks)
            self.on_end(img)
        elif self.overlay and self.cfg["overlay"] and self.last_menu and time.time() - self.last_menu[3] < 45 * 60:
            allies, me, menu, _ = self.last_menu
            log("Press outside the menu: overlay put back with the perks of the last players-menu press")
            self.overlay.watch(allies, me, lambda: winapi.grab_game_monitor(self.hwnd), self.hwnd, menu)
            self.say("Perk overlay shown")
        else:
            sounds.beep(False)
            self.say("Screen not recognised (neither the players menu nor the scoreboard)")
            paths.DEBUG.mkdir(parents=True, exist_ok=True)
            f = paths.DEBUG / (time.strftime("%Y%m%d_%H%M%S") + "_unknown.jpg")
            img.convert("RGB").save(f, quality=85)
            log(f"Unrecognised screenshot kept for diagnosis: {f}")

    # ----- players menu -----
    def on_players(self, img):
        mem = nightlight.remember_map(img)
        allies = []
        paths.DEBUG.mkdir(parents=True, exist_ok=True)
        img.convert("RGB").save(paths.DEBUG / "last_players_menu.jpg", quality=85)  # last players-menu screenshot, to diagnose name reading
        if self.analyzer is None:
            self.analyzer = an.Analyzer()
        survivor_view = self.analyzer.menu_visible(img)
        if survivor_view:  # survivor layout: the allies' perks are readable
            res = self.analyzer.analyze(img)
            for _ in range(2):  # menu still opening: the names come out empty, so look again a moment later
                if not res["allies"] or any(a["survivor"] for a in res["allies"]):
                    break
                log("No survivor name read (menu still opening?): looking again in 1 s")
                time.sleep(1.0)
                img = winapi.grab_game_monitor(self.hwnd)
                res = self.analyzer.analyze(img)
            allies = [a["survivor"] for a in res["allies"] if a["survivor"]]
            if not allies and self.last_menu and self.overlay and self.cfg["overlay"] and time.time() - self.last_menu[3] < 45 * 60:
                prev, me, menu, _ = self.last_menu  # unreadable this time: same match, so the overlay already known stays
                log("Names unreadable on this press: the overlay of the same match is kept")
                self.overlay.watch(prev, me, lambda: winapi.grab_game_monitor(self.hwnd), self.hwnd, menu)
                sounds.beep(False)
                return
            self.hub.result(res)
            self.last_menu = (res["allies"], res.get("me_row", 0), img, time.time())
            if self.overlay and self.cfg["overlay"] and res["allies"]:  # a press on the players menu always reads again and shows (to remove: press outside the menu, or the clear key)
                self.overlay.watch(res["allies"], res.get("me_row", 0), lambda: winapi.grab_game_monitor(self.hwnd), self.hwnd, img)
            log(f"Map: {mem['map'] if mem else 'not read'} · {len(res['allies'])} allies shown")
        else:
            self.say(f"Map remembered: {mem['map']}" if mem else "Map not read")
            log(f"Map: {mem['map'] if mem else 'not read'} (perks not shown: killer view)")
            self.last_menu = None  # killer: no overlay, no mouse checks, and no perks left over from an earlier survivor match
            if self.overlay:
                self.overlay.hide()
        if mem:
            canon = {n.upper(): n for n, _ in _survivor_surnames()}
            names = sorted(names_on_screen(img) | {canon[a] for a in allies if a in canon})
            mem["names"] = names
            paths.LAST_MATCH.write_text(json.dumps(mem, ensure_ascii=False), encoding="utf8")
            log(f"Survivors spotted to recognise the match: {names}")
        sounds.beep(bool(mem) and (bool(allies) or not survivor_view))  # survivor: map + allies read; killer: map read

    # ----- end scoreboard -----
    def on_end(self, img):
        cfg = self.cfg
        if COOLDOWN and time.time() - self.last_upload < COOLDOWN:
            log(f"Scoreboard ignored: last upload {time.time() - self.last_upload:.0f} s ago (< {COOLDOWN} s)")
            sounds.beep(False)
            self.say("Scoreboard already sent less than 2 minutes ago")
            return
        mem = nightlight.recall_map()
        map_name = mem["map"] if mem else None
        if mem:
            now = names_on_screen(img)
            same = same_match(mem.get("names", []), now)
            log(f"Survivors on the scoreboard: {sorted(now)} · remembered: {mem.get('names', [])} · same match: {same}")
            if same is False or (same is None and time.time() - mem["ts"] > 20 * 60):
                log("The remembered map comes from another match (or is too old to check): upload without a map")
                self.say("Remembered map is from another match: uploading without a map")
                map_name = None
        dry = cfg["dry_run"] or not cfg["upload"]
        log(f"Scoreboard · remembered map: {map_name or 'none'} · mode: {'dry run' if dry else 'real upload'}")
        row = own_row(img, cfg["player"])
        log(f"Your row on the scoreboard: {row}")
        try:  # level of the character you played: levels.json is corrected from the badge on your row
            levels.sync_from_scoreboard(img, row, self.analyzer, log=log, dry=dry)
        except Exception as e:
            log(f"Level update failed: {e}")
        if dry:
            info = nightlight.upload(img, send=False)
            self.say(f"DRY RUN: scoreboard saved, map {map_name or 'unknown'}")
            log(f"DRY RUN: {info}")
            return
        if not nightlight.have_token():
            sounds.beep(False)
            self.say("No NightLight API token: open the Setup page")
            log("No NightLight API token (data/nightlight_token.txt)")
            return
        self.say("Sending to NightLight...")
        info = nightlight.upload(img, send=True)
        self.last_upload = time.time()
        log(f"Upload OK: {info['url']}")
        self.say("Reviewing the match on NightLight...")
        try:
            r = review.review_match(info["url"], cfg["player"], map_name, log=log, row=row, focus_hwnd=self.hwnd)
        except review.NotLoggedIn as e:
            log(f"NightLight session missing: {e}")
            sounds.beep(False)
            self.say(str(e))
            return
        except Exception as e:
            import traceback
            log("Review failed:\n" + traceback.format_exc())
            sounds.beep(False)
            self.say(f"Uploaded, but finish the review by hand: {e}  ({info['url']})")
            return
        nightlight.forget_map()  # the map must not be reused for the next match
        sounds.beep(True)
        self.say(f"Match confirmed on NightLight · map: {r['map'] or 'not set'}")
        log(f"Match confirmed: {r}")


def run(hub, ast, stop_with_game=True):
    """Watches the keys and the game's presence; called in threads."""
    cfg = config.load()
    capture, clear = winapi.parse_combo(cfg["capture_key"]), winapi.parse_combo(cfg["clear_key"])
    label = winapi.combo_label(cfg["capture_key"])

    def on_press(hwnd):
        if not ast.busy.acquire(blocking=False):
            log("Press ignored: a job is already running")
            return
        try:
            log(f"{label} pressed (game window {hwnd})")
            ast.overlay_was_on = ast.overlay.hide() if ast.overlay else False  # removed before the capture: it must not get in the way of reading
            if ast.overlay_was_on:
                log("Overlay removed")
            time.sleep(0.25)
            t0 = time.time()
            img = winapi.grab_game_monitor(hwnd)
            log(f"Game screen captured: {img.size[0]}x{img.size[1]} in {time.time() - t0:.2f} s")
            ast.hwnd = hwnd
            ast.handle(img)
            log(f"Done in {time.time() - t0:.1f} s")
        except Exception as e:
            import traceback
            log("ERROR:\n" + traceback.format_exc())
            sounds.beep(False)
            hub.status(f"Error: {e}")
        finally:
            ast.busy.release()

    def clear_overlay():
        was = ast.overlay.hide() if ast.overlay else False  # removes the drawing or cancels a wait in progress
        ast.last_menu = None  # a press outside the menu no longer puts it back
        log("Overlay removed" if was else "No overlay to remove (perk memory cleared)")

    def keys():
        down = down_clear = False
        while True:
            pressed = winapi.combo_down(capture)
            pressed_clear = winapi.combo_down(clear)
            hwnd = None
            if (pressed and not down) or (pressed_clear and not down_clear):
                hwnd = winapi.game_in_front()
                if not hwnd:
                    log(f"Shortcut detected but the game is not in front (in front: {winapi.foreground_exe()[0]})")
            if hwnd and pressed and not down:
                threading.Thread(target=on_press, args=(hwnd,), daemon=True).start()
            elif hwnd and pressed_clear and not down_clear:
                clear_overlay()
            down, down_clear = pressed, pressed_clear
            time.sleep(0.03)

    def watch_game():
        seen, missing = False, 0
        while True:
            if winapi.game_running():
                if not seen:
                    log("Game detected")
                seen, missing = True, 0
            elif seen and stop_with_game:
                missing += 1
                if missing >= 2:
                    log("Game closed: stopping")
                    deadline = time.time() + 240  # lets an upload / review in progress finish
                    while ast.busy.locked() and time.time() < deadline:
                        time.sleep(1)
                    hub.quit()
                    return
            time.sleep(3)

    threading.Thread(target=keys, daemon=True).start()
    threading.Thread(target=watch_game, daemon=True).start()
    return label
