"""Automatic review of a NightLight match in a dedicated browser (Edge, persistent profile in data/nightlight_profile).

The browser window is visible: the site is protected by Cloudflare, which refuses windowless browsers. The first time, `login` opens the sign-in
page: you sign in yourself (e-mail or Discord) and the session stays in the profile. No password is ever read or stored here.
"""
import difflib
import json
import re
import threading
import time

from playwright.sync_api import sync_playwright

from . import paths, winapi
from .text import norm


class NotLoggedIn(Exception):
    pass


class ReviewError(Exception):
    pass


def map_id(name):
    """NightLight id of a map from its name (exact name first, then the closest one). None if unknown."""
    if not paths.NL_MAPS.exists():
        return None
    maps = json.loads(paths.NL_MAPS.read_text(encoding="utf8"))
    n = norm(name)
    exact = [int(i) for i, v in maps.items() if norm(v) == n]
    if exact:
        return exact[0]
    best = difflib.get_close_matches(n, [norm(v) for v in maps.values()], n=1, cutoff=0.85)
    return next((int(i) for i, v in maps.items() if best and norm(v) == best[0]), None)


def _give_focus_back(hwnd, stop):
    """Edge activates itself when it opens, even off-screen: while the review runs, focus is handed back to the original window (the game)."""
    while not stop.is_set():
        try:
            exe, cur = winapi.foreground_exe()
            if exe == "msedge.exe" and cur != hwnd:
                winapi.user32.keybd_event(0x12, 0, 0, 0)  # an Alt press allows SetForegroundWindow
                winapi.user32.SetForegroundWindow(hwnd)
                winapi.user32.keybd_event(0x12, 0, 2, 0)
        except Exception:
            pass
        stop.wait(0.15)


def _context(p, minimized=False):
    args = ["--window-position=-32000,-32000"] if minimized else []
    paths.NL_PROFILE.mkdir(parents=True, exist_ok=True)
    return p.chromium.launch_persistent_context(str(paths.NL_PROFILE), channel="msedge", headless=False, viewport={"width": 1400, "height": 1300}, args=args)


def login(log=print):
    """Opens the NightLight sign-in page; waits until you are signed in (10 min max) then closes."""
    with sync_playwright() as p:
        ctx = _context(p)
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto("https://nightlight.gg/account/login")
        log("Sign in to NightLight in the window that just opened (tick 'Remember me')...")
        deadline = time.time() + 600
        while time.time() < deadline:
            if "/account/login" not in page.url and "nightlight.gg" in page.url and "Just a moment" not in page.title() and "instant" not in page.title():
                log("Signed in: session saved in the NightLight profile.")
                time.sleep(2)
                ctx.close()
                return True
            time.sleep(1)
        ctx.close()
        return False


def session_saved():
    """True once a NightLight profile exists (a hint only: whether the session is still valid is known when a review runs)."""
    return paths.NL_PROFILE.exists() and any(paths.NL_PROFILE.iterdir())


def _own_row(page, pseudo):
    """Index (0 = top row) of the player's row: the 'Me' button closest above their name."""
    return page.evaluate(
        """(pseudo) => {
            const norm = s => s.toLowerCase().normalize('NFD').replace(/[^a-z0-9]/g, '');
            const me = [...document.querySelectorAll('label.btn')].filter(l => l.textContent.trim() === 'Me');
            if (!me.length) return -1;
            const top = el => el.getBoundingClientRect().top + window.scrollY;
            const first = top(me[0]) - 5;
            const cands = [...document.querySelectorAll('main *')].filter(e => e.children.length === 0 && norm(e.textContent) === norm(pseudo) && top(e) > first);
            if (!cands.length) return -1;
            const y = top(cands[0]);
            let idx = 0;
            me.forEach((l, i) => { if (top(l) <= y + 5) idx = i; });
            return idx;
        }""",
        pseudo,
    )


def _groups(page):
    """State of the associations: for each player, index of the ticked button (0 Random, 1 Friend, 2 Me) or -1."""
    return page.evaluate(
        """() => { const r = [...document.querySelectorAll('input[type=radio]')]; const out = [];
            for (let i = 0; i + 2 < r.length; i += 3) out.push([r[i], r[i + 1], r[i + 2]].findIndex(x => x.checked)); return out; }"""
    )


def review_match(url, pseudo, map_name=None, log=print, row=None, focus_hwnd=None):
    """Opens the upload page, waits for recognition, ticks 'Me' on your row and everybody else 'Random', sets the map, then 'Confirm'."""
    match_id = re.search(r"/(?:upload|review/one|match)/(\d+)", url).group(1)
    stop = threading.Event()
    if focus_hwnd:
        threading.Thread(target=_give_focus_back, args=(focus_hwnd, stop), daemon=True).start()
    with sync_playwright() as p:
        ctx = _context(p, minimized=True)
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            log(f"Review: opening {url}")
            page.goto(url, timeout=90000)
            for _ in range(60):  # the Cloudflare challenge solves itself in a real browser
                if "Just a moment" not in page.title() and "instant" not in page.title():
                    break
                time.sleep(1)
            if "/account/login" in page.url:
                raise NotLoggedIn("No NightLight session: run `python -m entity_toolkit login` (or use the Setup page).")
            # recognition: wait for the review page or the failure message
            ok = False
            for _ in range(120):
                if "/review/" in page.url and page.locator("label.btn", has_text="Me").count() >= 1:
                    ok = True
                    break
                if page.get_by_text("doesn't appear to be of a scoreboard").count():
                    raise ReviewError("NightLight did not recognise the screenshot as a match scoreboard.")
                time.sleep(1)
            if not ok:
                raise ReviewError("The review page did not appear in time.")
            log(f"Review page ready: {page.url}")
            time.sleep(1.5)
            n = page.locator("label.btn", has_text="Me").count()
            if row is None:
                row = _own_row(page, pseudo)
            log(f"Players: {n} · your row: {row}")
            info = {"match_id": match_id, "player": row, "players": n, "map": None}
            if row >= 0:
                me = page.locator("label.btn", has_text="Me").nth(row)
                if row == n - 1:
                    me.dblclick()  # as killer: puts every survivor on Random
                else:
                    me.click()
            else:
                log(f"'{pseudo}' not found on the page: tick 'Me' by hand.")
            # every player without an association -> Random (the server refuses otherwise)
            for i, g in enumerate(_groups(page)):
                if g == -1:
                    page.locator("label.btn", has_text="Random").nth(i).click()
            log(f"Associations: {_groups(page)}")
            if -1 in _groups(page):
                raise ReviewError("Could not fill in every player.")
            if map_name:
                mid = map_id(map_name)
                if mid:
                    st = page.evaluate(
                        """async ([id, mid]) => { const r = await fetch('/api/v1/match/' + id + '/map', {method: 'PATCH', credentials: 'include',
                            headers: {Accept: 'application/json', 'Content-Type': 'application/json'}, body: JSON.stringify({map_id: mid})}); return r.status; }""",
                        [match_id, mid],
                    )
                    info["map"] = map_name if st in (200, 400) else None  # 400 "No change": the map is already right
                    if st not in (200, 400):
                        log(f"Map not saved (HTTP {st}).")
                else:
                    log(f"Map '{map_name}' unknown to NightLight: choose it by hand.")
            log("Clicking Confirm...")
            with page.expect_response(re.compile(r"/api/v1/match/\d+/verify")) as resp:
                page.get_by_role("button", name="Confirm").click()
            body = resp.value.json()
            log(f"Validation response: {body.get('status')} {body.get('error') or ''}")
            if body.get("status") != "success":
                raise ReviewError(body.get("error", {}).get("message", "Validation refused"))
            info["validated"] = True
            return info
        finally:
            ctx.close()
            stop.set()
