"""The database shipped with the toolkit (the ``seed/`` folder): perks, icons, maps, builds and ratings as they were on a given day.

It makes the toolkit usable right after installing, without a first download. It only holds what is the same for everyone: nothing
personal (no levels, no settings, no token, no screenshots). At start it is copied into your data folder when you have no database yet,
or when the shipped one is more recent than yours (after installing a newer version of the toolkit). The automatic updates then keep it
current between two releases: a new game patch does not need a new release of the toolkit.

``python packaging/make_seed.py`` rebuilds the folder from the maintainer's data folder before a release.
"""
import json
import shutil
import time

from .. import config, paths

FILES = ["loadout_data.json", "loadout_extra.json", "killers.json", "survivors.json", "survivor_builds.json", "maps.json", "nl_maps.json", "patch.json"]
FOLDERS = ["icons", "images"]


def info(folder=None):
    """{"date": epoch seconds, "patch": game patch, "toolkit": version} of the shipped database; None when none is shipped."""
    try:
        return json.loads(((folder or paths.SEED) / "seed.json").read_text(encoding="utf8"))
    except Exception:
        return None


def wanted(seed, last_update, have_database):
    """Copy the shipped database? Yes when there is none yet, or when the shipped one is more recent than the last full update."""
    if not seed:
        return False
    return not have_database or int(seed.get("date") or 0) > int(last_update or 0)


def install(log=print, source=None, target=None):
    """Copies the shipped database into the data folder when `wanted`. Returns True when it did."""
    source, target = source or paths.SEED, target or paths.DATA
    seed = info(source)
    cfg = config.load()
    have = (target / "loadout_data.json").exists() and (target / "icons").exists()
    if not wanted(seed, cfg.get("last_update"), have):
        return False
    t0 = time.time()
    target.mkdir(parents=True, exist_ok=True)
    for name in FILES:
        if (source / name).exists():
            shutil.copy2(source / name, target / name)
    for name in FOLDERS:
        if (source / name).is_dir():
            shutil.copytree(source / name, target / name, dirs_exist_ok=True)
    cfg["last_update"] = int(seed.get("date") or time.time())
    cfg["db_patch"] = seed.get("patch") or cfg.get("db_patch") or ""
    config.save(cfg)
    log(f"Database shipped with the toolkit installed: data of {time.strftime('%Y-%m-%d', time.localtime(cfg['last_update']))}, game patch {cfg['db_patch'] or '?'} ({time.time() - t0:.1f} s)")
    return True


def build(source, target, toolkit_version):
    """Maintainer side: writes the seed folder from a data folder (only the shared files). Returns the seed information."""
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    for name in FILES:
        shutil.copy2(source / name, target / name)
    for name in FOLDERS:
        shutil.copytree(source / name, target / name)
    patch = json.loads((source / "patch.json").read_text(encoding="utf8")).get("live", "")
    cfg = json.loads((source / "config.json").read_text(encoding="utf8")) if (source / "config.json").exists() else {}
    meta = {"date": int(cfg.get("last_update") or (source / "loadout_data.json").stat().st_mtime), "patch": patch, "toolkit": toolkit_version}
    (target / "seed.json").write_text(json.dumps(meta), encoding="utf8")
    return meta
