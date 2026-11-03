"""Two discreet sounds: ``ok`` and ``ko`` (see sounds/gen_sounds.py, synthesised, no third-party audio)."""
from . import config, paths


def beep(ok):
    if not config.load()["sounds"]:
        return
    try:
        import winsound
        winsound.PlaySound(str(paths.SOUNDS / ("ok.wav" if ok else "ko.wav")), winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass
