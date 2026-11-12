"""New versions of Entity Toolkit: knowing one exists, and installing it when you say so.

Checking (the `check_version` setting): at each start, then once a day, the toolkit reads the latest published release of the project on
GitHub (one public request, nothing is sent). Installing (the `update_install` setting: "ask", "auto" or "never"):

 - the packaged program (EntityToolkit.exe): the release's zip is downloaded into the data folder, its SHA-256 is compared with the
   release's SHA256SUMS.txt, it is unpacked, the toolkit stops, a small script replaces EntityToolkit.exe and _internal (never your
   data folder) and starts the toolkit again;
 - the Python version from a git clone: ``git pull`` then ``pip install -r requirements.txt``, and the toolkit starts again;
 - anything else (the source downloaded as a zip): it cannot be done for you, the release page is opened.
"""
import hashlib
import re
import shutil
import subprocess
import sys
import threading
import time
import zipfile

from . import __version__, config, paths

API = "https://api.github.com/repos/Tau-hub/entity-toolkit/releases/latest"
PAGE = "https://github.com/Tau-hub/entity-toolkit/releases/latest"
STATE = {"latest": None, "checked": 0, "page": PAGE, "zip": None, "sums": None, "notes": "",
         "installing": False, "step": "", "error": None}
_lock = threading.Lock()


def parse(v):
    """'0.2.1' or 'v0.2.1' -> (0, 2, 1); anything unreadable -> ()."""
    try:
        return tuple(int(x) for x in re.findall(r"\d+", v or "")[:4])
    except Exception:
        return ()


def newer(latest, current=__version__):
    a, b = parse(latest), parse(current)
    return bool(a) and bool(b) and a > b


def read(text):
    m = re.search(r"__version__\s*=\s*[\"']([^\"']+)[\"']", text or "")
    return m.group(1) if m else None


def read_release(data):
    """What is needed from GitHub's "latest release" answer: version, page, the Windows zip and the checksum file."""
    assets = {a.get("name", ""): a.get("browser_download_url") for a in data.get("assets") or []}
    zip_name = next((n for n in assets if n.lower().endswith("-windows.zip")), None)
    return {"latest": (data.get("tag_name") or "").lstrip("vV") or None, "page": data.get("html_url") or PAGE,
            "zip": assets.get(zip_name) if zip_name else None, "zip_name": zip_name, "sums": assets.get("SHA256SUMS.txt"),
            "notes": (data.get("body") or "")[:4000]}


def expected_hash(sums_text, name):
    """The SHA-256 written for `name` in a SHA256SUMS.txt ("<hash>  <file>" per line); None when it is not listed."""
    for line in (sums_text or "").splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[-1].lstrip("*") == name and re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            return parts[0].lower()
    return None


def check():
    import requests
    r = requests.get(API, timeout=15, headers={"Accept": "application/vnd.github+json", "User-Agent": "entity-toolkit"})
    r.raise_for_status()
    info = read_release(r.json())
    with _lock:
        STATE.update(info, checked=int(time.time()))
    return info["latest"]


def kind():
    """How this copy can be updated: 'exe', 'git' or 'manual'."""
    if paths.FROZEN:
        return "exe"
    return "git" if (paths.ROOT / ".git").exists() and shutil.which("git") else "manual"


def info():
    with _lock:
        s = dict(STATE)
    k = kind()
    return {"current": __version__, "latest": s["latest"], "newer": newer(s["latest"]), "page": s["page"], "exe": paths.FROZEN,
            "kind": k, "can_install": k == "git" or (k == "exe" and bool(s["zip"]) and bool(s["sums"])),
            "mode": config.load().get("update_install") or "ask", "installing": s["installing"], "step": s["step"], "error": s["error"]}


def _say(log, step):
    with _lock:
        STATE["step"] = step
    log("Update: " + step)


def apply_script(root, new, exe="EntityToolkit.exe", watcher=None):
    """The script that swaps the program once it has stopped: waits for it, replaces the .exe and _internal, starts it again.
    `data` is never touched. Plain commands only (tasklist, robocopy, copy), so that it can be read."""
    lines = [
        "@echo off",
        "setlocal",
        f'set "ROOT={root}"',
        f'set "NEW={new}"',
        "set /a n=0",
        ":wait",
        f'tasklist /FI "IMAGENAME eq {exe}" 2>nul | find /I "{exe}" >nul',
        "if errorlevel 1 goto swap",
        "set /a n+=1",
        f"if %n% GEQ 10 taskkill /F /IM {exe} >nul 2>&1",
        "if %n% GEQ 40 goto fail",
        "ping -n 2 127.0.0.1 >nul",
        "goto wait",
        ":swap",
        'robocopy "%NEW%\\_internal" "%ROOT%\\_internal" /MIR /R:3 /W:1 >nul',
        "if errorlevel 8 goto fail",
        f'copy /Y "%NEW%\\{exe}" "%ROOT%\\{exe}" >nul',
        "if errorlevel 1 goto fail",
        'echo ok> "%~dp0result.txt"',
        'rmdir /S /Q "%NEW%\\.." >nul 2>&1',
        "goto restart",
        ":fail",
        'echo failed> "%~dp0result.txt"',
        ":restart",
    ]
    if watcher:
        lines.append(f'if exist "{watcher}" wscript "{watcher}"')
    lines += [f'start "" "%ROOT%\\{exe}" run', "exit /b 0", ""]
    return "\r\n".join(lines)


def _install_exe(log):
    import requests
    with _lock:
        url, sums_url, latest = STATE["zip"], STATE["sums"], STATE["latest"]
    if not (url and sums_url):
        raise RuntimeError("this release has no Windows zip or no SHA256SUMS.txt")
    work = paths.DATA / "update"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True, exist_ok=True)
    name = url.rsplit("/", 1)[-1]
    target = work / name
    _say(log, f"downloading {name}")
    h = hashlib.sha256()
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": "entity-toolkit"}) as r:
        r.raise_for_status()
        total, done = int(r.headers.get("Content-Length") or 0), 0
        with open(target, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
                h.update(chunk)
                done += len(chunk)
                if total:
                    with _lock:
                        STATE["step"] = f"downloading {name}: {done * 100 // total} %"
    _say(log, "checking the download (SHA-256)")
    want = expected_hash(requests.get(sums_url, timeout=30, headers={"User-Agent": "entity-toolkit"}).text, name)
    if not want or want != h.hexdigest():
        target.unlink(missing_ok=True)
        raise RuntimeError("the downloaded file does not match the release's SHA-256: nothing was installed")
    _say(log, "unpacking")
    new = work / "new"
    with zipfile.ZipFile(target) as z:
        z.extractall(new)
    folder = new / "EntityToolkit"
    if not ((folder / "EntityToolkit.exe").exists() and (folder / "_internal").is_dir()):
        raise RuntimeError("the zip does not look like Entity Toolkit: nothing was installed")
    target.unlink(missing_ok=True)
    from . import autostart
    watcher = autostart.startup_dir() / autostart.LAUNCHER
    bat = work / "apply.bat"
    bat.write_text(apply_script(paths.ROOT, folder, watcher=watcher if watcher.exists() else None), encoding="mbcs")
    _say(log, f"installing {latest}: the toolkit restarts")
    subprocess.Popen(["cmd", "/c", str(bat)], cwd=str(work), creationflags=0x08000000 | 0x00000008, close_fds=True)  # no window, detached


def _install_git(log):
    def run(cmd):
        p = subprocess.run(cmd, cwd=str(paths.ROOT), capture_output=True, text=True, timeout=600, creationflags=0x08000000)
        if p.returncode:
            raise RuntimeError(f"{' '.join(cmd[:3])} failed: {(p.stderr or p.stdout).strip()[-300:]}")
        return p.stdout.strip()
    _say(log, "git pull")
    out = run(["git", "pull", "--ff-only"])
    log("Update: " + (out.splitlines()[-1] if out else "done"))
    _say(log, "installing the Python packages")
    run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"])
    from . import autostart
    _say(log, "restarting")
    cmd = " ".join(f'"{c}"' if " " in c else c for c in autostart.command() + ["run"])
    subprocess.Popen(["cmd", "/c", f"ping -n 4 127.0.0.1 >nul & start \"\" {cmd}"], cwd=str(paths.ROOT), creationflags=0x08000000 | 0x00000008, close_fds=True)


def install(log, quit_toolkit):
    """Installs the latest release in the background; `quit_toolkit()` stops the running toolkit once the new one is ready to take over.
    Returns False when an installation is already running or cannot be done for this copy."""
    k = kind()
    with _lock:
        if STATE["installing"] or k == "manual":
            return False
        STATE.update(installing=True, error=None, step="starting")

    def work():
        try:
            (_install_exe if k == "exe" else _install_git)(log)
            time.sleep(1)
            quit_toolkit()
        except Exception as e:
            log(f"Update failed: {e}")
            with _lock:
                STATE.update(installing=False, error=str(e), step="")
    threading.Thread(target=work, daemon=True, name="update").start()
    return True


def start(log, quit_toolkit=None, idle=lambda: True):
    """Background check: shortly after each start, then once a day. In "auto" mode a new version is installed by itself when `idle()`
    says nothing is going on (the game is not running)."""
    def loop():
        time.sleep(8)
        while True:
            cfg = config.load()
            if cfg.get("check_version"):
                try:
                    latest = check()
                    if newer(latest):
                        log(f"A newer Entity Toolkit is available: {latest} (you have {__version__}) - {PAGE}")
                except Exception as e:
                    log(f"Version check skipped: {e}")
            for _ in range(24 * 60):  # a day, looking every minute whether an automatic installation can start
                time.sleep(60)
                if quit_toolkit and config.load().get("update_install") == "auto" and info()["newer"] and info()["can_install"] and not STATE["error"] and idle():
                    install(log, quit_toolkit)
    threading.Thread(target=loop, daemon=True).start()
