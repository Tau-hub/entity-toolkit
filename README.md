# Entity Toolkit

[Version française](README.fr.md)

An **unofficial** companion for *Dead by Daylight* (Windows): see your teammates' perks over the game, send your match scoreboard to NightLight with one key, track your character levels, and browse recommended builds.

> Not affiliated with Behaviour Interactive, NightLight, Otzdarva or the DbD wiki. *Dead by Daylight* and its assets are trademarks / property of Behaviour Interactive Inc. No game asset, rating or description is shipped in this repository: the toolkit downloads them on your PC (see [Data and privacy](#data-and-privacy)).

![The allies' perks drawn over the game's survivor list](docs/images/overlay.jpg)

*Each ally's four perks, drawn in a 2×2 grid next to their portrait in the game's own survivor list (player names blurred for this screenshot).*

## What it does

| | |
|---|---|
| **Allies' perks** (survivor) | Press the capture key on the Tab players menu: the toolkit reads your three allies' perks, character names and player names, shows them on the **Live** page (second screen) and draws them over the game's survivor list, on the right survivor. |
| **Perk text on hover** | When the game frees the mouse (you are hooked or dead), put it on an overlay icon and a small box shows that perk's name, rating and text. It disappears as soon as the mouse leaves the icon. Turn it off on the Setup page. |
| **Map memory** (survivor and killer) | The same key reads and remembers the map from the players menu. |
| **NightLight upload** | Press the same key on the end-of-match scoreboard: it is sent to [NightLight](https://nightlight.gg), the match is reviewed for you ("Me" ticked on your name, everyone else Random, map set from memory, Confirm clicked). |
| **Level tracking** | A page to set how far you got with each killer and survivor, kept up to date automatically from the scoreboard. |
| **Priorities** | Which characters are worth levelling next, from Otzdarva's opinion plus NightLight stats. |
| **Recommended builds** | Killer sheets (builds, add-on tier list, combos) and survivor builds, from Otzdarva and NightLight. |
| **Random loadout** | Roll a random killer (or survivor) loadout: power, add-ons, perks, optional offering, with ratings. Copy or download the poster as an image. |
| **Build creator** | Save your own killer and survivor builds (four perks, a name, the killers it suits). Search perks by name, killer or type: "aura", "gen regression", "healing"… |
| **Sounds** | A soft "ok" or "not ok" sound so you know without looking whether the map and perks were read. |

![Live page](docs/images/live.png)

## How it works, and what it does not do

- It **only looks at pixels**: a screenshot of the monitor the game is on, like OBS does. It does **not** read the game's memory, inject anything, or hook the game.
- Text is read with the **OCR built into Windows**; perk icons are recognised by comparing them with the official icons it downloads.
- The overlay is a **separate transparent window** laid over the game (click-through, never takes focus), not something drawn inside the game.
- **No guarantee about anti-cheat.** It behaves like screen-capture tools and Discord's overlay, but only you decide whether you are comfortable running anything next to an online game. Use it at your own risk.

## Requirements

- Windows 10 or 11, **Python 3.10 or newer**, Microsoft Edge (used for the NightLight review).
- *Dead by Daylight* in **English**, in **borderless or windowed** mode (not exclusive fullscreen).
- An **English language pack** for Windows OCR: Settings → Time & language → Language & region.
- Tested at **2560×1440** for the game and **1920×1080** side screens. Every position is proportional to the game screen's height, but other resolutions have not been tested: see [Troubleshooting](#troubleshooting).

## Install

```bash
git clone https://github.com/Tau-hub/entity-toolkit
cd entity-toolkit
install.bat
run.bat
```

`install.bat` installs the Python packages. `run.bat` starts the toolkit in the background and opens the **Setup** page the first time.

## First launch: the Setup page

![Setup page](docs/images/setup.png)

1. **Requirements.** The page checks that Windows has an English OCR engine.
2. **Update database.** One button downloads perk names, descriptions and icons (DbD wiki), map names, Otzdarva's builds and tier list, and NightLight's stats. The first time takes a few minutes. Run it again after a game patch (new perks, new maps, new ratings). The page shows the patch the game is on (from the Steam announcements) and the patch label of Otzdarva's data, which can lag a few days behind the game; wiki pages are re-downloaded on every update. Each step reports on its own, so one site being down does not block the others. The same thing from a console: `python -m entity_toolkit update-db`. While it runs, the page shows which step it is on, and afterwards what the patch brought (new or removed killers, survivors, perks, add-ons, items, offerings, maps). Once you have done it once, the toolkit refreshes the data by itself every 7 days in the background (change or turn off in *Options*).
3. **You.** Type your in-game name exactly as the scoreboard shows it.
4. **Your levels.** Drop screenshots of the in-game killer and survivor selection screens right on the Setup page and the toolkit reads which characters you have and their levels (you review before saving), or set them by hand on the **Levels** page (see below).
5. **NightLight** (optional). Paste an API token from your NightLight account settings and sign in once in the Edge window the button opens. The toolkit never sees your password.
6. **Options.** Overlay on/off, sounds, dry run (saves the scoreboard but never sends it), and the keys.

Once you press **Finish setup**, the *Setup* button becomes **⚙ Settings** (top right): same page without the requirements, to update the database, change your name, import levels, set the NightLight token and the options. *Reset the setup* at the bottom brings the first-launch checklist back (your data is kept).

## Using it during a match

The default key is **Alt + Numpad 7** (NumLock on). It only reacts while the game is running **and** in front.

| You are on… | Press the key | Result |
|---|---|---|
| The **players menu** (Tab), as survivor | once | Map remembered, allies' perks on the Live page, overlay drawn once you close the menu |
| The **players menu**, as killer | once | Map remembered |
| The game (menu closed), overlay shown | once | Overlay stays (it is only removed by the scoreboard or by Alt + Numpad 8) |
| The game (menu closed), overlay removed | once | Overlay put back with the last perks read |
| The **match scoreboard** | once | Overlay removed, screenshot sent to NightLight, match reviewed and confirmed, your character's level corrected |
| Anything else | once | "Not ok" sound, nothing is sent |

**Alt + Numpad 8** removes the overlay and forgets the perks (handy if you do not want to upload that match). Both keys can be changed on the Setup page.

The toolkit stops by itself when the game closes. To have it start by itself when the game starts: `python -m entity_toolkit autostart install` (undo with `autostart remove`). Only one copy ever runs: if you start it with `run.bat` and the autostart watcher then launches it again when the game starts, the second copy stops by itself, so a key press is handled once.

**Reading a perk:** while the mouse is free (hooked, dead, spectating), hover an icon of the overlay to see its text; move off the icon and it goes away. It only reads the mouse position (no hook, nothing read from the game): nothing at all while the overlay is hidden, twice a second while you play (the game hides and locks the cursor), and a fast check (25 times a second) only when the mouse is free **and** near the icons. During normal play the mouse is locked to the camera, so nothing shows. `data/entity_toolkit.log` records it: `Overlay hover:` lines for every change (mouse locked / free, text shown / hidden) and a summary of the number of checks each minute.

Why the overlay waits: the game's own survivor list is only visible once the Tab menu is closed. After the key press the toolkit watches the screen, reads the names in the game's list and matches each ally to the right row, first by **portrait**, then by **player name** when two allies play the same character or the portraits are too similar. Your own row never moves.

## Levels

![Levels page](docs/images/levels.png)

![Reading levels from screenshots of the in-game selection screens](docs/images/levels-import.png)

*Dropping four screenshots of the killer selection screen: every character recognised, with the five levels that differ from the saved ones ticked for you to apply.*

Levels run from 0 to 3 (0 = not levelled yet, 3 = done). A new user sets them once on the **Levels** page, either by hand or by **dropping screenshots of the in-game killer and survivor selection screens**: the toolkit recognises each character card (SIFT feature matching against the downloaded portraits) and reads its level badge, then shows what it found so you can review and apply it. By hand: **+** and **−** per character, buttons to set every killer or survivor to 0 or 3, **Import / Export JSON** to move your levels between PCs or share them, and a **History** panel. After that the toolkit keeps them current by itself: on the scoreboard it reads the level badge of *your* row and corrects the character you just played. Not everybody owns every character, so each one also has an **Own** checkbox: **I own everything**, **I own only the base game** (then tick what you have), a **Chapters (DLC)** panel that toggles a killer and the survivor from the same chapter together, or one by one. The priorities only rank the characters you own, and playing a character on the scoreboard marks it as owned.

![Priorities page](docs/images/priorities.png)

## Recommended builds

![Killer sheet](docs/images/killer-sheet.png)

The **Killer sheet** page shows Otzdarva's builds, NightLight's most played builds, the add-on tier list and add-on combos for each killer. **Survivor builds** shows the most popular NightLight builds and Otzdarva's survivor builds. ![Survivor builds](docs/images/survivor-builds.png)

Everything comes from the database you downloaded, so it is as fresh as your last update.

## Random loadout

![Random loadout](docs/images/loadout.png)

Pick a killer (or a survivor, or press **Random killer**) and get a random loadout: power, add-ons, four perks and an optional offering, each with its rating. The first visit shows every killer as a portrait; once you have rolled, they move to a column on the left so you can roll another one with a click. Reroll everything or one part, then copy the poster or download it as a PNG.

## Build creator

Choose **Killer builds** or **Survivor builds**, give the build a name, and pick up to four perks. Killer builds can list the killers they suit (shown as small heads on the saved build); a build with none is a general one. Survivor builds apply to any survivor.

To find perks, type a perk name, a killer name or a **type** ("aura", "gen regression", "healing"), or use the drop-down list of all types. A perk can have several types. The types come from the wiki's mechanic tags and from the perk text, so they are a best effort: **✎ Edit types** lets you correct any perk by hand (kept in `data/perk_types.json`). Saved builds are in `data/my_builds.json`.

## Data and privacy

Everything the toolkit stores lives in the git-ignored `data/` folder next to the code (override with the `ENTITY_TOOLKIT_DATA` environment variable):

| File / folder | What |
|---|---|
| `icons/`, `images/`, `loadout_data.json`, `loadout_extra.json`, `patch.json`, `killers.json`, `survivors.json`, `survivor_builds.json`, `maps.json`, `nl_maps.json` | Downloaded by **Update database** |
| `levels.json`, `levels_history.json`, `owned.json` | Your levels, and the characters you do not own |
| `config.json` | Your settings |
| `nightlight_token.txt` | Your NightLight API token. Sent **only** to `api.nightlight.gg` |
| `nightlight_profile/` | The Edge profile holding your NightLight session |
| `uploads/`, `debug/` | The scoreboards sent and the last captures kept to diagnose problems |
| `entity_toolkit.log` | What the toolkit did |

Network use: the game screenshot never leaves your PC except the **scoreboard**, which goes to NightLight when you press the key on it (turn that off with *Dry run* on the Setup page). **Update database** reads from `deadbydaylight.wiki.gg`, `otzdarva-builds.com`, `otzdarva.com`, `otz-addon-tierlist.pages.dev` and `nightlight.gg`. The local web server listens on `127.0.0.1` only and refuses requests from other websites.

## Troubleshooting

- **"Screen not recognised"**: the toolkit looks for the words *PLAYERS / QUESTS* (players menu) or *MATCH SCOREBOARD* at the top left. Check that the game is in English and that you pressed the key on one of those two screens. The capture is saved in `data/debug/` (`*_unknown.jpg`).
- **Nothing happens**: the game must be running and in front. Look at `data/entity_toolkit.log`. Run `python -m entity_toolkit` instead of `run.bat` to see the console.
- **Wrong or missing perks**: perks below 78 % confidence are flagged "to check" on the Live page. Run **Update database** after a patch so the new icons exist.
- **Overlay misplaced**: positions are proportional to the game screen's height and were measured at 2560×1440. Adjust `data/overlay_layout.json` (`x`, `dy`, `rows`, `size`, `gap`, described at the top of `entity_toolkit/overlay.py`) and press the key again. Pull requests with measurements for other resolutions are very welcome.
- **NightLight review fails**: Edge must be installed, and you must have signed in once (Setup → Sign in). The window is visible on purpose: NightLight is behind Cloudflare, which refuses invisible browsers. The toolkit hands focus back to the game while it works.
- **The game's list names are unreadable**: the overlay then falls back to the menu order.

## Command line

```text
python -m entity_toolkit                  start (same as run.bat)
python -m entity_toolkit update-db        download / refresh the data  [--only patch builds perks loadout maps nl_maps] [--refresh]
python -m entity_toolkit login            sign in to NightLight
python -m entity_toolkit autostart install   start by itself when the game starts (autostart remove to undo)
python -m entity_toolkit test-image X.jpg analyse a screenshot as if you had pressed the key (dry run)
python -m entity_toolkit serve --demo     serve the pages with a made-up result, without the game
```

## Development

```bash
python -m unittest discover -s tests
```

| Module | Role |
|---|---|
| `assistant.py` | The key loop: which screen is it, what to do |
| `recognize.py`, `analyzer.py` | Perks, names and map from a players-menu screenshot |
| `overlay.py` | The transparent window and the ally-to-row matching |
| `nightlight.py`, `review.py` | Upload, map memory, automatic review |
| `levels.py` | Levels, history, reading the scoreboard badge |
| `database/` | `update-db`: wiki, Otzdarva and NightLight downloads |
| `server.py`, `web/` | Local pages and JSON API |

Contributions: open an issue first for anything big (see also [AI assistance](#ai-assistance)).

## Credits

Builds, perk values and the add-on tier list come from **Otzdarva** ([otzdarva-builds.com](https://otzdarva-builds.com), [otzdarva.com](https://otzdarva.com)); community statistics and the upload API from **[NightLight](https://nightlight.gg)**; perk and map data from the **[Dead by Daylight wiki](https://deadbydaylight.wiki.gg)**. None of it is redistributed here: it is fetched on your machine, and the ratings and opinions belong to their authors.

## License

[MIT](LICENSE) for the code of this repository. It does not cover the third-party data the toolkit downloads, nor *Dead by Daylight*'s assets.

## AI assistance

Most of the code and documentation of this project was written with Claude (Anthropic) through Claude Code, from the maintainer's requirements. The maintainer chose the features, reviewed the results, and checked the tool on real game screenshots and in matches. As with any AI-assisted code, bugs and unhandled setups are likely: read what the toolkit does before giving it access to your NightLight account. Commits containing AI-written changes carry a `Co-Authored-By: Claude` line. Contributions are welcome; if an AI tool wrote part of yours, mention it in the pull request.
