"""Windows helpers: is the game running / in front, screenshot of its monitor, global hotkeys.

Everything here only reads the process list and the screen's pixels (like OBS does). Nothing is opened, read or injected
in the game's own process.
"""
import ctypes
from ctypes import wintypes

import mss
from PIL import Image

GAME_EXE = "DeadByDaylight-Win64-Shipping.exe"

user32, kernel32 = ctypes.windll.user32, ctypes.windll.kernel32
kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)  # real pixel coordinates (mixed 1080p / 1440p screens)
except Exception:
    pass


class PROCESSENTRY32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                ("th32DefaultHeapID", ctypes.c_void_p), ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                ("szExeFile", ctypes.c_char * 260)]


def game_pids():
    """Process ids of the game, from a snapshot of the process list (the game process itself is never touched)."""
    snap = kernel32.CreateToolhelp32Snapshot(0x2, 0)
    pids = set()
    try:
        e = PROCESSENTRY32()
        e.dwSize = ctypes.sizeof(e)
        ok = kernel32.Process32First(snap, ctypes.byref(e))
        while ok:
            if e.szExeFile.decode("mbcs", "ignore").lower() == GAME_EXE.lower():
                pids.add(e.th32ProcessID)
            ok = kernel32.Process32Next(snap, ctypes.byref(e))
        return pids
    finally:
        kernel32.CloseHandle(snap)


def game_running():
    return bool(game_pids())


def foreground_exe():
    """(executable name, window) in front. For the game we only compare the window's process id with the process list:
    no handle is opened on the game's process (no read, no query)."""
    hwnd = user32.GetForegroundWindow()
    pid = wintypes.DWORD()
    user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if pid.value in game_pids():
        return GAME_EXE.lower(), hwnd
    h = kernel32.OpenProcess(0x1000, False, pid.value)  # not the game: its name can be read
    if not h:
        return "", hwnd
    try:
        buf = ctypes.create_unicode_buffer(520)
        n = wintypes.DWORD(520)
        kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n))
        return buf.value.rsplit("\\", 1)[-1].lower(), hwnd
    finally:
        kernel32.CloseHandle(h)


def game_in_front():
    exe, hwnd = foreground_exe()
    return (hwnd if exe == GAME_EXE.lower() else None)


def grab_game_monitor(hwnd):
    """Screenshot of the monitor the game window is on."""
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    cx, cy = (r.left + r.right) // 2, (r.top + r.bottom) // 2
    with mss.mss() as sct:
        mon = next((m for m in sct.monitors[1:] if m["left"] <= cx < m["left"] + m["width"] and m["top"] <= cy < m["top"] + m["height"]), sct.monitors[1])
        shot = sct.grab(mon)
        return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")


# ---------- hotkeys ----------
MODIFIERS = {"ctrl": 0x11, "shift": 0x10, "alt": 0x12}
KEYS = {"tab": 0x09, "esc": 0x1B, "space": 0x20,
        **{f"f{i}": 0x6F + i for i in range(1, 13)},
        **{f"numpad{i}": 0x60 + i for i in range(10)}}


def parse_combo(s):
    """'alt+numpad7' -> [VK_ALT, VK_NUMPAD7]."""
    vks = []
    for part in s.lower().replace(" ", "").split("+"):
        if part in MODIFIERS:
            vks.append(MODIFIERS[part])
        elif part in KEYS:
            vks.append(KEYS[part])
        elif len(part) == 1 and part.isalnum():
            vks.append(ord(part.upper()))
        else:
            raise ValueError(f"Unknown key in shortcut: {part!r}")
    return vks


def combo_down(vks):
    """True while every key of the combination is held. Several virtual keys for one slot are not needed here."""
    return all(user32.GetAsyncKeyState(vk) & 0x8000 for vk in vks)


def combo_label(s):
    return "+".join(p.capitalize() if len(p) > 1 else p.upper() for p in s.split("+")).replace("Numpad", "Numpad ")
