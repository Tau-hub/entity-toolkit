"""Rebuilds ``seed/``, the database shipped with the toolkit, from your data folder: ``python packaging/make_seed.py``.

Run **Update database** first so the data is current. Only the shared files are copied (perks, icons, maps, builds, ratings):
never your levels, settings, NightLight token, screenshots or builds.
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from entity_toolkit import __version__, paths  # noqa: E402
from entity_toolkit.database import seed  # noqa: E402

if __name__ == "__main__":
    meta = seed.build(paths.DATA, ROOT / "seed", __version__)
    files = [f for f in (ROOT / "seed").rglob("*") if f.is_file()]
    print(f"seed/: {len(files)} files, {sum(f.stat().st_size for f in files) / 1e6:.0f} MB, data of {time.strftime('%Y-%m-%d', time.localtime(meta['date']))}, game patch {meta['patch']}")
