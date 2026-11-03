"""Tiny logger: console (when there is one) and ``data/entity_toolkit.log``."""
import time

from . import paths


def log(msg):
    line = f"{time.strftime('[%H:%M:%S]')} {msg}"
    try:
        print(line, flush=True)
    except Exception:
        pass  # no console (pythonw) or a character the console cannot print
    try:
        paths.ensure()
        with paths.LOG_FILE.open("a", encoding="utf8") as f:
            f.write(line + "\n")
    except Exception:
        pass
