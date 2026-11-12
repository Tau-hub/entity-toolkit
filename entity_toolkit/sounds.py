"""Two discreet sounds: ``ok`` and ``ko`` (see sounds/gen_sounds.py, synthesised, no third-party audio)."""
from . import config, paths


def beep(ok):
    """ok / not ok; `"go"`: a very short blip, the scoreboard is being sent (you can leave it)."""
    if not config.load()["sounds"]:
        return
    try:
        import winsound
        name = ok if isinstance(ok, str) else ("ok" if ok else "ko")
        winsound.PlaySound(str(paths.SOUNDS / (name + ".wav")), winsound.SND_FILENAME | winsound.SND_ASYNC)
    except Exception:
        pass
