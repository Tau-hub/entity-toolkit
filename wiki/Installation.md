[← Home](https://github.com/Tau-hub/entity-toolkit/wiki/Home) · [Français](https://github.com/Tau-hub/entity-toolkit/wiki/Installer)

## Requirements

- Windows 10 or 11 and Microsoft Edge (used for the NightLight review; its web engine, WebView2, also draws the Entity Toolkit window and is part of Windows 11 and of up-to-date Windows 10). **Python 3.10 or newer** only if you choose the Python install below; the `.exe` needs nothing else.
- *Dead by Daylight* in **English**, in **borderless or windowed** mode (not exclusive fullscreen).
- An **English language pack** for Windows OCR: Settings → Time & language → Language & region.
- Tested at **2560×1440** for the game and **1920×1080** side screens. Every position is proportional to the game screen's height, but other resolutions have not been tested: see [Troubleshooting](https://github.com/Tau-hub/entity-toolkit/wiki/Troubleshooting).

## Install

There are two ways to run the toolkit. They do exactly the same thing: pick the one you are comfortable with.

### Option A: the `.exe` (no Python needed)

1. Open the [latest release](https://github.com/Tau-hub/entity-toolkit/releases/latest) and download `EntityToolkit-<version>-windows.zip`.
2. Check the download (optional but recommended, see below).
3. Unzip it wherever you like, in a folder you can write to (Documents, Desktop, another drive: not `Program Files`). Keep `EntityToolkit.exe` and the `_internal` folder together.
4. Double-click **`EntityToolkit.exe`**. It starts in the background (the red **E** appears in the notification area) and opens its window on the **Setup** page the first time.

Your data goes in a `data` folder next to `EntityToolkit.exe`. To update, download the new release, unzip it and move your `data` folder into it (if *Start automatically with Windows* is on, untick and tick it again from the new folder).

**Checking the download.** Each release comes with `SHA256SUMS.txt`, and its notes show the same fingerprint. In PowerShell, in the folder where the zip is:

```powershell
Get-FileHash .\EntityToolkit-<version>-windows.zip -Algorithm SHA256
```

The value must be the one in `SHA256SUMS.txt`. If it is not, the file is not the one that was published: delete it. The zip is built by GitHub Actions from the tagged source ([release.yml](https://github.com/Tau-hub/entity-toolkit/blob/main/.github/workflows/release.yml)), not on someone's PC, and GitHub signs a statement saying so. With the [GitHub CLI](https://cli.github.com) you can check that statement, which proves the file came out of this repository's workflow:

```bash
gh attestation verify EntityToolkit-<version>-windows.zip --repo Tau-hub/entity-toolkit
```

**Windows warnings.** The `.exe` is not signed with a paid certificate, so Windows SmartScreen may say *"Windows protected your PC"* the first time: **More info → Run anyway**. Programs packaged this way (PyInstaller) are also sometimes flagged by antivirus software by mistake. If you would rather not trust a binary, use option B: it runs the very same code, which you can read.

### Option B: with Python

```bash
git clone https://github.com/Tau-hub/entity-toolkit
cd entity-toolkit
install.bat
run.bat
```

`install.bat` installs the Python packages. `run.bat` starts the toolkit in the background and opens its window on the **Setup** page the first time. Update with `git pull`.
