"""Keeps the screenshots taken by the capture key (players menu, scoreboard, anything else) in data/captures/, newest 100 only.

Handy to diagnose a wrong reading afterwards, or to illustrate the documentation. They never leave your PC and are git-ignored with the rest of
data/. The count is the `keep_captures` setting (Settings page, 0 = keep nothing); the oldest ones are deleted as new ones arrive.
"""
import time

from . import config, paths


def save(img, kind):
    """Writes one capture as a JPEG named <date>_<time>_<kind>.jpg, then deletes the oldest ones beyond the limit. Never raises."""
    try:
        keep = int(config.load().get("keep_captures") or 0)
        if keep <= 0:
            return None
        paths.CAPTURES.mkdir(parents=True, exist_ok=True)
        f = paths.CAPTURES / f"{time.strftime('%Y%m%d_%H%M%S')}_{kind or 'other'}.jpg"
        img.convert("RGB").save(f, quality=85)
        prune(keep)
        return f
    except Exception:
        return None


def prune(keep):
    files = sorted(paths.CAPTURES.glob("*.jpg"))  # the names start with the date: oldest first
    for f in files[:max(0, len(files) - keep)]:
        try:
            f.unlink()
        except OSError:
            pass
