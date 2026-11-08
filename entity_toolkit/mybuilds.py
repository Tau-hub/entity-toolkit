"""The builds you save in the Build creator: a name, four perks, and (killer builds) the killers it suits. Stored in data/my_builds.json."""
import json
import time
import uuid

from . import paths


def load():
    try:
        return json.loads(paths.MYBUILDS.read_text(encoding="utf8"))
    except Exception:
        return []


def _write(builds):
    paths.ensure()
    paths.MYBUILDS.write_text(json.dumps(builds, ensure_ascii=False, indent=1), encoding="utf8")


def save(b):
    """Adds a build, or replaces the one with the same id. Returns the stored build."""
    side = "S" if b.get("side") == "S" else "K"
    perks = [str(p) for p in (b.get("perks") or []) if p][:4]
    if not perks:
        raise ValueError("a build needs at least one perk")
    build = {"id": b.get("id") or uuid.uuid4().hex[:10], "name": (str(b.get("name") or "").strip() or "Untitled build")[:60], "side": side,
             "perks": perks, "killers": [str(k) for k in (b.get("killers") or [])] if side == "K" else [], "updated": int(time.time())}
    builds = [x for x in load() if x["id"] != build["id"]]
    builds.insert(0, build)
    _write(builds)
    return build


def delete(build_id):
    builds = load()
    kept = [x for x in builds if x["id"] != build_id]
    _write(kept)
    return len(builds) - len(kept)
