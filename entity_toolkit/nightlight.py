"""NightLight (nightlight.gg) side of the toolkit: remember the map from the players menu, send the end-of-match scoreboard.

The upload uses NightLight's public upload API (the one ShareX uses) with *your own* API token, read from data/nightlight_token.txt and sent
only to api.nightlight.gg. Get a token in your NightLight account settings.
"""
import io
import json
import time
import webbrowser

import requests

from . import paths, recognize as rc
from .log import log

API = "https://api.nightlight.gg/v1/upload"
JPEG_QUALITY = 95


# ---------- map memory ----------
def remember_map(img):
    """Reads the map shown at the bottom of the screen (OCR). Only saved when it matches a known map: otherwise this is not the players menu."""
    m = rc.recognize_map(img)
    if not m["maps"]:
        return None
    data = {"map": m["maps"][1], "realm": m["realms"][1] if m["realms"] else None, "time": time.strftime("%Y-%m-%d %H:%M:%S"), "ts": time.time()}
    paths.ensure()
    paths.LAST_MATCH.write_text(json.dumps(data, ensure_ascii=False), encoding="utf8")
    return data


def recall_map(max_age_h=4):
    try:
        d = json.loads(paths.LAST_MATCH.read_text(encoding="utf8"))
        return d if time.time() - d["ts"] < max_age_h * 3600 else None
    except Exception:
        return None


def forget_map():
    try:
        paths.LAST_MATCH.unlink()
    except FileNotFoundError:
        pass


# ---------- upload ----------
def have_token():
    return paths.NL_TOKEN.exists() and bool(paths.NL_TOKEN.read_text(encoding="utf8").strip())


def jpeg_bytes(img):
    buf = io.BytesIO()
    img.convert("RGB").save(buf, "JPEG", quality=JPEG_QUALITY)
    return buf.getvalue()


def upload(img, send, open_url=False):
    """Saves the scoreboard in data/uploads/ and, when `send` is true, sends it. Returns a dict with the NightLight url."""
    data = jpeg_bytes(img)
    paths.ensure()
    f = paths.UPLOADS / (time.strftime("%Y%m%d_%H%M%S") + ".jpg")
    f.write_bytes(data)
    mem = recall_map()
    info = {"file": str(f), "size_mb": round(len(data) / 1e6, 2), "resolution": img.size, "remembered_map": mem["map"] if mem else None}
    if not send:
        log(f"DRY RUN (nothing sent): {info}")
        return info
    if not have_token():
        raise RuntimeError("No NightLight API token: paste it on the Setup page (or save it in data/nightlight_token.txt).")
    token = paths.NL_TOKEN.read_text(encoding="utf8").strip()
    r = requests.post(API, headers={"Authorization": "Bearer " + token}, files={"file": ("scoreboard.jpg", data, "image/jpeg")}, timeout=120)
    body = r.json()
    if r.status_code != 200 or body.get("status") != "success":
        raise RuntimeError(f"NightLight refused the upload ({r.status_code}): {body.get('error', {}).get('message')}")
    url = body["data"]["url"]
    log(f"Uploaded: {url}")
    if open_url:
        webbrowser.open(url)
    return {**info, "url": url}
