# PyInstaller recipe for the Windows build:  python packaging/build.py
#
# One folder (EntityToolkit.exe + _internal/), not one self-extracting file: a single file would unpack about 300 MB to a temporary
# folder at every start (so each time the game launches), and is flagged more often by antivirus software.
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH).parent
sys.path.insert(0, str(root))
from entity_toolkit import __version__, tray  # noqa: E402

build = root / "build"
build.mkdir(exist_ok=True)
icon = build / "entity_toolkit.ico"
tray._image().resize((256, 256)).save(icon, sizes=[(16, 16), (32, 32), (48, 48), (256, 256)])

datas = [(str(root / "web"), "web"), (str(root / "sounds" / "ok.wav"), "sounds"), (str(root / "sounds" / "ko.wav"), "sounds"), (str(root / "LICENSE"), ".")]
if (root / "seed" / "seed.json").exists():  # the database shipped with the toolkit
    datas.append((str(root / "seed"), "seed"))
binaries, hidden = [], ["pystray._win32", "clr"]
for pkg in ("winrt", "playwright", "webview", "clr_loader", "pythonnet"):  # Windows OCR bindings, the browser driver and the window (WebView2 through .NET) are loaded in ways PyInstaller cannot guess
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hidden += h

a = Analysis([str(root / "packaging" / "entity_toolkit_exe.py")], pathex=[str(root)], binaries=binaries, datas=datas, hiddenimports=hidden,
             excludes=["matplotlib", "pandas", "scipy", "IPython", "pytest", "PyQt5", "PyQt6", "PySide2", "PySide6"])
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name="EntityToolkit", console=False, icon=str(icon), upx=False)
COLLECT(exe, a.binaries, a.datas, name="EntityToolkit", upx=False)
