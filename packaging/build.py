"""Builds the Windows release: ``python packaging/build.py`` (needs ``pip install pyinstaller``).

Result, in ``dist/``:
  EntityToolkit-<version>-windows.zip   the folder to unzip anywhere: EntityToolkit.exe + _internal/
  SHA256SUMS.txt                        the zip's SHA-256, to check a download:  Get-FileHash EntityToolkit-<version>-windows.zip

The GitHub workflow ``.github/workflows/release.yml`` runs this on a clean machine when a version tag is pushed.
"""
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from entity_toolkit import __version__  # noqa: E402


NOTES = """## Two ways to use it

**With the `.exe` (no Python needed).** Download `{name}` below, unzip it in a folder you can write to (not `Program Files`), keep `EntityToolkit.exe` and `_internal` together, and double-click `EntityToolkit.exe`.

**With Python.** Clone the repository (or download *Source code* below), then run `install.bat` and `run.bat`. It is the very same code, which you can read.

Both are described in the [README](https://github.com/Tau-hub/entity-toolkit#install).

## Check your download

SHA-256 of `{name}`:

```
{digest}
```

In PowerShell, in the folder where the zip is, this must print the same value (it is also in `SHA256SUMS.txt`):

```powershell
Get-FileHash .\\{name} -Algorithm SHA256
```

The zip was built by this repository's GitHub Actions workflow from this tag, and GitHub signed a statement saying so. To check it with the [GitHub CLI](https://cli.github.com):

```
gh attestation verify {name} --repo Tau-hub/entity-toolkit
```

The `.exe` is not signed with a paid certificate: Windows SmartScreen may warn the first time (**More info → Run anyway**), and antivirus software sometimes flags PyInstaller programs by mistake. If you would rather not run a binary, use the Python way.
"""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    dist = ROOT / "dist"
    subprocess.check_call([sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", str(dist), "--workpath", str(ROOT / "build"),
                           str(ROOT / "packaging" / "entity_toolkit.spec")], cwd=str(ROOT))
    folder = dist / "EntityToolkit"
    name = f"EntityToolkit-{__version__}-windows.zip"
    with zipfile.ZipFile(dist / name, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sorted(folder.rglob("*")):
            if f.is_file():
                z.write(f, Path("EntityToolkit") / f.relative_to(folder))
    digest = sha256(dist / name)
    (dist / "SHA256SUMS.txt").write_text(f"{digest}  {name}\n", encoding="utf8", newline="\n")
    (dist / "RELEASE_NOTES.md").write_text(NOTES.format(name=name, digest=digest), encoding="utf8", newline="\n")
    print(f"{name}:{(dist / name).stat().st_size / 1e6:.0f} MB\nSHA-256: {digest}")


if __name__ == "__main__":
    main()
