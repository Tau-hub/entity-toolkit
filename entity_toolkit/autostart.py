"""Optional: start Entity Toolkit by itself when the game starts.

``python -m entity_toolkit autostart install`` puts a tiny launcher in your Windows Startup folder. It runs a very light watcher (it only
looks at the process list every 5 seconds) that starts the toolkit when Dead by Daylight launches. The toolkit stops itself when the
game closes, and the watcher waits for the next launch. ``autostart remove`` undoes it.
"""
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from . import paths, winapi
from .log import log

LAUNCHER = "EntityToolkitWatcher.vbs"


def startup_dir():
    return Path(os.environ["APPDATA"]) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def pythonw():
    return shutil.which("pythonw") or str(Path(sys.executable).with_name("pythonw.exe"))


def command():
    """How to start this program again: the .exe itself when packaged, else ``pythonw -m entity_toolkit``."""
    return [sys.executable] if paths.FROZEN else [pythonw(), "-m", "entity_toolkit"]


def launcher_text(cmd, folder):
    """The Startup-folder script: runs `cmd` + ``watch`` without a window. In VBScript a quote inside a string is written twice."""
    line = " ".join([f'"{cmd[0]}"'] + cmd[1:] + ["watch"]).replace('"', '""')
    return f'Set sh = CreateObject("WScript.Shell")\nsh.CurrentDirectory = "{folder}"\nsh.Run "{line}", 0, False\n'


def install():
    f = startup_dir() / LAUNCHER
    f.write_text(launcher_text(command(), paths.ROOT), encoding="utf8")
    return f


def remove():
    f = startup_dir() / LAUNCHER
    existed = f.exists()
    f.unlink(missing_ok=True)
    return existed


def installed():
    return (startup_dir() / LAUNCHER).exists()


def watch():
    """Starts the toolkit whenever the game launches."""
    log("Watcher started: waiting for the game")
    while True:
        if winapi.game_running():
            log("Game detected: starting Entity Toolkit")
            code = subprocess.call(command() + ["run"], cwd=str(paths.ROOT))
            log(f"Entity Toolkit stopped (code {code})")
            while winapi.game_running():  # wait for the game to close before re-arming (avoids restarting a copy that just stopped)
                time.sleep(5)
        time.sleep(5)
