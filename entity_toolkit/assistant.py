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

from . import analyzer as an, auto, captures, config, levels, nightlight, ocr, paths, review, sounds, winapi
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


def still_this_match(known, seen):
    """Automatic mode, players menu seen again: are the allies already shown (`known`, survivor names) the ones on screen (`seen`)?
    Two names in common are enough (one when a single name is known: three allies playing the same survivor)."""
    known, seen = {norm(n) for n in known if n}, {norm(n) for n in seen}
    return bool(known) and len(known & seen) >= min(2, len(known))


def read_complete(allies, known):
    """A players-menu reading is complete when it found three allies and recognised the survivor each of them plays.
    It is not when something covered part of the menu (the game's own tooltip when the mouse is on an item or a perk)."""
    known = {norm(n) for n in known}
    return len(allies) >= 3 and all(norm(a.get("survivor") or "") in known for a in allies)


def merge_readings(readings, known):
    """The best of several readings of the same players menu, ally by ally: a recognised survivor wins over an unreadable one, a player
    name over none, and each of the four perks keeps its most confident reading. A row hidden on one screenshot (the game's tooltip
    under the mouse) is taken from another one."""
    known = {norm(n) for n in known}
    ok = lambda a: norm(a.get("survivor") or "") in known
    rows = {}
    for res in readings:
        for a in res["allies"]:
            b = rows.get(a["row"])
            if b is None:
                rows[a["row"]] = dict(a, perks=list(a["perks"]))
                continue
            if ok(a) and not ok(b):
                b["survivor"], b["player"] = a["survivor"], a["player"] or b["player"]
            elif ok(a) == ok(b) and a["player"] and not b["player"]:
                b["player"] = a["player"]
            b["perks"] = [x if x["score"] >= y["score"] else y for x, y in zip(b["perks"], a["perks"])]
    out = dict(readings[0], allies=[rows[r] for r in sorted(rows)])
    for key in ("map", "realm"):
        out[key] = next((r[key] for r in readings if r.get(key)), None)
    return out


class Burst:
    """A few more screenshots of the players menu, taken in the background while the first one is being read. They are only looked at
    when that first reading is incomplete (an ally missing, a name unreadable): the mouse may have moved off the icon by then."""

    def __init__(self, hwnd, delays=(0.15, 0.35, 0.6, 0.9, 1.3, 1.8)):  # close together: the menu is often open for a second or two only
        self.frames = []
        self.thread = threading.Thread(target=self._run, args=(hwnd, delays), daemon=True)
        self.thread.start()

    def _run(self, hwnd, delays):
        t0 = time.time()
        for d in delays:
            time.sleep(max(0.0, t0 + d - time.time()))
            try:
                img = winapi.grab_game_monitor(hwnd)
                if auto.read_kind(auto.strip_of(img)) != "players":
                    log(f"Extra screenshots: the menu was no longer on screen {d} s after the first one ({len(self.frames)} kept)")
                    return  # the menu was closed (or it was not the menu at all): nothing more to take
                self.frames.append(img)
                captures.save(img.copy(), f"players-extra{len(self.frames)}")  # kept with the other captures, to see afterwards what was read
            except Exception as e:
                log(f"Extra screenshots stopped: {type(e).__name__}: {e}")
                return
        log(f"Extra screenshots: {len(self.frames)} kept")

    def get(self):
        self.thread.join(4)
        return list(self.frames)


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
        self.players_at = None  # when the players menu was last read for the current match (automatic mode does not read it again right away)
        self.end_at = None      # when a scoreboard was last handled (automatic mode does not handle the same one twice)
        self.complete = False   # the last players-menu reading found the three allies and their survivors
        self.burst = None       # the extra screenshots being taken for the press in progress
        self.partial = None     # (incomplete reading, time): completed by the next reading of the same menu
        self.retries = 0        # automatic mode: readings done again because the last one was incomplete (at most 2 per match)

    @property
    def cfg(self):
        return {**config.load(), **self.override}

    def say(self, msg):
        self.hub.status(msg)

    # ----- dispatch -----
    def handle(self, img, quiet=False):
        """`quiet` (automatic mode): a screen that is neither the menu nor the scoreboard is simply ignored, without a sound."""
        kind = classify(img)
        log(f"Screen recognised: {kind or 'none'}")
        if quiet and kind is None:  # automatic mode: the screen changed in the meantime, nothing to do and nothing to say
            if self.overlay_was_on and self.overlay and self.cfg["overlay"] and self.last_menu:
                allies, me, menu, _ = self.last_menu
                log("Automatic: nothing to read after all: the overlay is put back")
                self.overlay.watch(allies, me, lambda: winapi.grab_game_monitor(self.hwnd), self.hwnd, menu)
            return
        if quiet and kind == "players" and self.complete and self.last_menu and time.time() - self.last_menu[3] < 45 * 60:
            # automatic mode, menu opened again during the match: when the same allies are on screen, the perks already shown stay as they are
            if still_this_match([a["survivor"] for a in self.last_menu[0]], names_on_screen(img)):
                log("Automatic: players menu seen again, same match: the perks already shown are kept")
                self.players_at = time.time()
                return
        if quiet and kind == "end" and not all(auto.rows_revealed(img)):
            # automatic mode: between seeing the finished scoreboard and taking the picture to send, something came over it
            # (another window, a page change). An incomplete picture is never sent: the scoreboard is looked at again.
            log(f"Automatic: the scoreboard picture is not complete any more (rows {auto.rows_revealed(img)}): nothing sent, looking again")
            threading.Thread(target=captures.save, args=(img.copy(), "end-covered"), daemon=True).start()
            return
        threading.Thread(target=captures.save, args=(img.copy(), kind or "other"), daemon=True).start()  # rotation of the last captures, off the critical path
        if kind == "players":
            self.players_at = time.time()
            self.on_players(img)
            self.complete = bool(self.last_menu) and read_complete(self.last_menu[0], an.survivor_names())
            if quiet and self.last_menu and not self.complete and self.retries < 2:
                # automatic mode: part of the menu was hidden (a tooltip under the mouse?) or still opening. It is read again
                # as long as the menu stays open, or at the next Tab, twice at most.
                self.retries += 1
                self.players_at = None
                log(f"Automatic: incomplete reading ({len(self.last_menu[0])} allies, some survivors not recognised): the menu will be read again (retry {self.retries} of 2)")
            elif self.complete:
                self.retries = 0
        elif kind == "end":
            self.end_at, self.players_at = time.time(), None
            self.complete, self.retries = False, 0
            self.last_menu = None  # the match is over: its perks must never come back (not as an overlay, not as mouse checks)
            self.on_end(img, quiet)
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
            known = an.survivor_names()
            sure = lambda r: read_complete(r["allies"], known) and not any(p["uncertain"] for a in r["allies"] for p in a["perks"])
            if not sure(res):  # an ally is missing, or a perk is doubtful (something over it): use the other screenshots taken meanwhile, then what the previous try had read
                for n, frame in enumerate(reversed(self.burst.get() if self.burst else []), 1):  # the latest first: the most likely to differ
                    log(f"Reading not sure ({len(res['allies'])} allies, {sum(p['uncertain'] for a in res['allies'] for p in a['perks'])} doubtful perks): reading another screenshot of the menu ({n})")
                    before = [(a["row"], a["survivor"], a["player"], [p.get("name") for p in a["perks"]]) for a in res["allies"]]
                    res = merge_readings([res, self.analyzer.analyze(frame)], known)
                    if sure(res):
                        break
                    if n >= 2 and before == [(a["row"], a["survivor"], a["player"], [p.get("name") for p in a["perks"]]) for a in res["allies"]]:
                        break  # another screenshot changed nothing: the others will not either (a survivor the database does not know, say)
                if not read_complete(res["allies"], known) and self.partial and time.time() - self.partial[1] < 120:
                    res = merge_readings([res, self.partial[0]], known)
                log(f"After putting the readings together: {[(a['row'], a['survivor']) for a in res['allies']]}")
            self.partial = None if read_complete(res["allies"], known) else (res, time.time())
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
    def on_end(self, img, quiet=False):
        cfg = self.cfg
        if quiet and not cfg["dry_run"] and not (cfg["upload"] and nightlight.have_token()):
            # automatic mode, and NightLight is not in use (sending turned off, or no token): the end of the match only removes the
            # overlay and updates your level. Nothing is saved or sent, and no "not ok" sound.
            log("Match over · NightLight is not in use (upload off or no token): nothing is sent")
            try:
                levels.sync_from_scoreboard(img, own_row(img, cfg["player"]), self.analyzer, log=log, dry=False)
            except Exception as e:
                log(f"Level update failed: {e}")
            nightlight.forget_map()
            self.say("Match over: perks removed (NightLight upload is off)")
            return
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

    def on_press(hwnd, why=None, img=None, clean=True):
        """`img` + `clean=False` (automatic mode, players menu): read that very screenshot and leave the overlay alone."""
        if not ast.busy.acquire(blocking=False):
            log("Press ignored: a job is already running")
            return
        try:
            log(f"Automatic: {why} (game window {hwnd})" if why else f"{label} pressed (game window {hwnd})")
            t0 = time.time()
            ast.overlay_was_on = False
            if img is None or clean:
                ast.overlay_was_on = ast.overlay.hide() if ast.overlay else False  # removed before the capture: it must not get in the way of reading, nor end up in the scoreboard sent to NightLight
                if ast.overlay_was_on:
                    log("Overlay removed")
            if img is None or ast.overlay_was_on:  # automatic mode hands over its own screenshot: it is only used when the overlay was not drawn on it
                time.sleep(0.25)
                t0 = time.time()
                seen = img  # automatic mode: the picture on which the finished scoreboard was seen
                img = winapi.grab_game_monitor(hwnd)
                log(f"Game screen captured: {img.size[0]}x{img.size[1]} in {time.time() - t0:.2f} s")
                if why and seen is not None:
                    # the picture to send must be the scoreboard that was seen, with nothing over it (another window, a page change):
                    # several are taken, a moment apart, and the first clean one is used
                    for n in range(4):
                        if winapi.game_in_front() == hwnd and auto.same_board(seen, img):
                            break
                        log(f"Automatic: something is over the scoreboard on that picture: taking another one ({n + 1})")
                        threading.Thread(target=captures.save, args=(img.copy(), "end-covered"), daemon=True).start()
                        time.sleep(0.4)
                        img = winapi.grab_game_monitor(hwnd)
                    else:
                        log("Automatic: no clean picture of the scoreboard (another window in front?): nothing sent, looking again")
                        return
            ast.hwnd = hwnd
            ast.burst = Burst(hwnd)  # a few more screenshots while this one is read (they stop by themselves when it is not the players menu)
            ast.handle(img, quiet=bool(why))
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
        ast.players_at = None  # automatic mode: the next Tab reads the menu again
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
            elif seen and stop_with_game and not hub.window_open():  # the game is closed, and so is the window: nothing left to do
                missing += 1
                if missing >= 2:
                    log("Game closed: stopping")
                    deadline = time.time() + 240  # lets an upload / review in progress finish
                    while ast.busy.locked() and time.time() < deadline:
                        time.sleep(1)
                    hub.quit()
                    return
            time.sleep(3)

    state = {"on": False, "at": 0.0}

    def auto_on():  # the setting is read again every 2 seconds, so ticking it on the Settings page works without a restart
        if time.time() - state["at"] > 2:
            on = bool(config.load().get("auto"))
            if on != state["on"]:
                log("Automatic mode on: Tab reads the players menu, the scoreboard is sent by itself" if on else "Automatic mode off")
            state.update(on=on, at=time.time())
        return state["on"]

    watcher = auto.Watcher(ast, lambda hwnd, why, img, clean: threading.Thread(target=on_press, args=(hwnd, why, img, clean), daemon=True).start(), auto_on, hub.status, log)
    threading.Thread(target=watcher.run, daemon=True, name="auto").start()
    threading.Thread(target=keys, daemon=True).start()
    threading.Thread(target=watch_game, daemon=True).start()
    return label
