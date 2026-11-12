[← Home](https://github.com/Tau-hub/entity-toolkit/wiki/Home) · [Français](https://github.com/Tau-hub/entity-toolkit/wiki/Ligne-de-commande-et-developpement)

## Command line

With the `.exe`, replace `python -m entity_toolkit` with `EntityToolkit.exe` (it has no console, so look at `data\entity_toolkit.log` for what it did).

```text
python -m entity_toolkit                  start (same as run.bat)
python -m entity_toolkit update-db        download / refresh the data  [--only patch builds perks loadout maps nl_maps] [--refresh]
python -m entity_toolkit login            sign in to NightLight
python -m entity_toolkit autostart install   start by itself when the game starts (autostart remove to undo)
python -m entity_toolkit test-image X.jpg analyse a screenshot as if you had pressed your capture key on it (dry run)
python -m entity_toolkit serve --demo     serve the pages with a made-up result, without the game
```

## Development

```bash
python -m unittest discover -s tests
```

| Module | Role |
|---|---|
| `assistant.py` | The capture key, and what to do on each screen (players menu, scoreboard) |
| `auto.py` | Automatic mode: seeing the players menu and the finished scoreboard without a key |
| `recognize.py`, `analyzer.py` | Perks, names and map from a players-menu screenshot |
| `overlay.py` | The transparent window and the ally-to-row matching |
| `nightlight.py`, `review.py` | Upload, map memory, automatic review |
| `levels.py` | Levels, history, backups, reading the scoreboard badge |
| `perk_types.py`, `mybuilds.py` | Build creator: what a perk does (several types per perk), saved builds |
| `shrine.py`, `version.py`, `tray.py` | This week's Shrine, new versions (check and install), the notification-area icon |
| `database/seed.py`, `seed/` | The database shipped with the toolkit, and its installation at the first start |
| `packaging/` | The `.exe`: PyInstaller recipe and `build.py` (zip + SHA-256) |
| `database/` | `update-db`: wiki, Otzdarva and NightLight downloads, what changed (`changes.py`), automatic refresh |
| `server.py`, `web/` | Local pages and JSON API |
| `window.py` | The Entity Toolkit window (pywebview / WebView2) showing those pages, and its launcher |

**Releasing.** Refresh the shipped database (`Update database`, then `python packaging/make_seed.py`). Change `__version__` in `entity_toolkit/__init__.py`, commit, then push a tag with the same number (`git tag v0.3.0`, `git push origin v0.3.0`). The [release workflow](https://github.com/Tau-hub/entity-toolkit/blob/main/.github/workflows/release.yml) runs the tests, builds the `.exe` on a clean Windows machine, attests it and creates a **draft** release with the zip, `SHA256SUMS.txt` and the install notes: read it, then press *Publish*. The manual lives in the `wiki/` folder: after changing it, `python packaging/publish_wiki.py` copies it to the wiki. To build locally: `pip install pyinstaller`, then `python packaging/build.py` (result in `dist/`).

Contributions: open an issue first for anything big (see also [AI assistance](https://github.com/Tau-hub/entity-toolkit#ai-assistance)).
