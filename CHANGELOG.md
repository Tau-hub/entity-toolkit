# Changelog

All notable changes to Entity Toolkit are written here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows [Semantic Versioning](https://semver.org/) (0.x: the minor number can bring changes of behaviour).

Releases are made only when they are worth it for the people using the `.exe`: between two releases, changes pile up under *Unreleased*.

## [Unreleased]

### Added
- The new content announced by the patch notes (killer, survivor, map) is checked after every update; what is missing is shown in Settings and tried again every few hours.
- Updates report the perks whose text or numbers changed, and the last news stays visible after a later update that finds nothing.
- A perk without any rating shows the average of its side, marked as an average.
- Setting *When the game is closed*: the window closes and the toolkit stays in the notification area (default), the toolkit quits, or everything is left as it is.

### Fixed
- Database: a killer just released was left out when Otzdarva had no build for them yet (The Terrifier).
- Database: a new game patch is now noticed while the toolkit keeps running (it was only looked for at start).
- Players menu: an ally with fewer than four perks (empty slots, dark or purple) no longer gets made-up perks in the empty slots; they are left out.
- Players menu: with bots in the match the rows are no longer where the toolkit looked for them, so a human ally could be taken for an empty row and their perks were missing. The height of each row is now found from the row itself (up to three bots), and a player name that is not read is read again brightened.

- Players menu: an ally who brought no perk at all (four empty slots) no longer makes the whole menu look like the killer's view, which left every other ally without perks; they are kept as an ally with no perk, so the overlay is still shown for the others.

### Changed
- Dependencies: minimum versions raised for Pillow (13), pywebview (6.2.1), beautifulsoup4 (4.15) and the `winrt` packages (4.x, with Windows.Media.Ocr 10.0.28000); GitHub Actions `setup-python` 7. A clean install of `requirements.txt` (OpenCV 5.0, NumPy 2.4.6) was checked on real screenshots: menu, scoreboard and OCR read as before.

### Project
- Conventional Commits for every commit; contributing guide, code of conduct, security policy, issue and pull request templates, third-party notices.

## [0.4.3] - 2026-11-14

### Added
- **Perk tier list** page: every survivor or killer perk in tiers S to D, on a score out of 100 (S 80 and more, A 65-79, B 50-64, C 25-49, D 0-24), based on the combined rating, Otzdarva's opinion, or NightLight's pick rate and escape / kill rate. Filters by kind of perk, search, only the perks you have. Last page of the navigation, also in the notification-area menu.

### Fixed
- The scoreboard is never sent with the game's perk tooltip over it (mouse on a perk): the toolkit waits for a clean picture and shows a small message asking you to move the mouse off the perks.

### Changed
- The toolkit now writes in its log why it stops (window, notification-area menu, update, game closed) and any crash.

## [0.4.2] - 2026-11-14

### Fixed
- Automatic mode: a scoreboard that was already handled is never sent again, however long you were away from it (it used to be sent a second time after 2.5 minutes).

## [0.4.1] - 2026-11-12

### Added
- Scoreboard upload: a short blip and a small "Uploading..." box at the top left of the game as soon as the picture is good, so you can leave the scoreboard at once (setting in Settings).
- Skins that rename a character (A2 for Yui Kimura...): read from the wiki's "Alternate Character Models", so the players menu knows every such name.

### Changed
- Shorter sounds; quicker second look at the end scoreboard.
- GitHub Actions run on Node 24.

### Fixed
- Only one Entity Toolkit window can exist, and it goes away with the toolkit that opened it (a killed and restarted toolkit left a dead window behind).
- Players menu: extra screenshots that change nothing are no longer read over and over.

## [0.4.0] - 2026-11-12

### Added
- The Entity Toolkit window: its own window instead of a browser tab (75 % of the screen, remembered place, close to the notification area or quit).
- The database ships with the toolkit (`seed/`): it works right after installing; targeted database updates after a game patch.
- Self-update from the releases (ask / install by itself / only tell), checked with SHA-256.
- Credits to Dead by Daylight, the DbD Wiki (CC BY-NC-SA 4.0), Otzdarva and NightLight.

### Fixed
- Automatic mode: a scoreboard covered by another window is never sent; bots and players without perks count as a revealed scoreboard.

## [0.3.3] - 2026-11-11

### Changed
- Automatic mode is the default (hotkey mode stays one click away in Settings).

## [0.3.2] - 2026-11-11

### Added
- Step-by-step setup wizard.

### Changed
- Smarter automatic mode: several screenshots put together after Tab, quick taps handled, nothing sent when NightLight is not in use.

## [0.3.1] - 2026-11-11

### Added
- Automatic mode (Hotkey or Automatic in Settings): Tab reads the players menu, the scoreboard is sent by itself.

### Changed
- Settings are saved as you change them; the overlay is removed before the automatic capture.

## [0.3.0] - 2026-11-11

### Added
- Shrine of Secrets alert, loadout filters, daily challenge.
- Windows `.exe` release with a SHA-256 checksum, built by GitHub Actions.
- Wiki (EN + FR); the README keeps the essentials.

## [0.2.0] - 2026-11-11

### Added
- Notification-area icon, update dot on Settings, new-version check, GitHub Actions tests.

### Fixed
- Character names with a few letters misread as lower case.

## [0.1.0] - 2026-11-04

### Added
- First version: perk overlay on the game's survivor list, NightLight upload, level tracking, priorities, killer sheet, survivor builds, random loadout.

[Unreleased]: https://github.com/Tau-hub/entity-toolkit/compare/v0.4.3...HEAD
[0.4.3]: https://github.com/Tau-hub/entity-toolkit/compare/v0.4.2...v0.4.3
[0.4.2]: https://github.com/Tau-hub/entity-toolkit/compare/v0.4.1...v0.4.2
[0.4.1]: https://github.com/Tau-hub/entity-toolkit/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/Tau-hub/entity-toolkit/compare/v0.3.3...v0.4.0
[0.3.3]: https://github.com/Tau-hub/entity-toolkit/compare/v0.3.2...v0.3.3
[0.3.2]: https://github.com/Tau-hub/entity-toolkit/compare/v0.3.1...v0.3.2
[0.3.1]: https://github.com/Tau-hub/entity-toolkit/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/Tau-hub/entity-toolkit/releases/tag/v0.3.0
