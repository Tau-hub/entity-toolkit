# Third-party notices

Entity Toolkit's own code is under the [MIT licence](LICENSE). It uses the open-source libraries below, which keep their own licences, and the Windows `.exe` bundles them (made with PyInstaller). Versions are those of the build; see `requirements.txt`.

| Library | Used for | Licence |
|---|---|---|
| [Pillow](https://python-pillow.org/) | Image handling | MIT-CMU (HPND) |
| [NumPy](https://numpy.org/) | Image maths | BSD-3-Clause |
| [opencv-python](https://github.com/opencv/opencv-python) | Recognising perk icons and portraits | Apache-2.0 (OpenCV), with the licences of the libraries it bundles |
| [mss](https://github.com/BoboTiG/python-mss) | Screen capture | MIT |
| [Requests](https://requests.readthedocs.io/) | Downloads, NightLight upload | Apache-2.0 |
| [Beautiful Soup 4](https://www.crummy.com/software/BeautifulSoup/) | Reading wiki pages | MIT |
| [Playwright for Python](https://playwright.dev/python/) | Reviewing an upload on NightLight in a browser | Apache-2.0 |
| [pystray](https://github.com/moses-palmer/pystray) | Notification-area icon | **LGPL-3.0** |
| [pywebview](https://pywebview.flowrl.com/) | The Entity Toolkit window (WebView2) | BSD-3-Clause |
| [winrt](https://github.com/pywinrt/pywinrt) (Windows.Media.Ocr and friends) | Reading text on screen with Windows OCR | MIT |
| [PyInstaller](https://pyinstaller.org/) | Building the `.exe` (build time only) | GPL-2.0-or-later with the bootloader exception |

**pystray (LGPL-3.0).** It is used as an unmodified library, imported by the Python code. Its source is at the link above; in the `.exe` it sits as separate files in the `_internal` folder, so it can be replaced by another version of the same library.

**Not covered by the MIT licence:** the game data in `seed/` (names, descriptions, icons, portraits, builds, statistics) belongs to Behaviour Interactive and to the community sources credited in the [README](README.md#credits) and in [seed/README.md](seed/README.md).
