[← Home](https://github.com/Tau-hub/entity-toolkit/wiki/Home) · [Français](https://github.com/Tau-hub/entity-toolkit/wiki/Donnees-et-vie-privee)

## Data and privacy

**Whose data it is.** *Dead by Daylight* and everything that comes from the game belong to **Behaviour Interactive Inc.** The perks, icons, maps and texts the toolkit ships and downloads were collected from the [Dead by Daylight Wiki](https://deadbydaylight.wiki.gg) and its contributors, the builds and ratings come from Otzdarva, and the statistics from NightLight: they are credited in the [README](https://github.com/Tau-hub/entity-toolkit#credits) and in the `seed/` folder, and removed on request.

Everything the toolkit stores lives in the `data/` folder next to the code, or next to `EntityToolkit.exe` (git-ignored; override with the `ENTITY_TOOLKIT_DATA` environment variable):

| File / folder | What |
|---|---|
| `icons/`, `images/`, `loadout_data.json`, `loadout_extra.json`, `patch.json`, `killers.json`, `survivors.json`, `survivor_builds.json`, `maps.json`, `nl_maps.json` | The database: shipped with the toolkit (the `seed/` folder), then kept current by the updates |
| `levels.json`, `levels_history.json`, `levels_backups.json`, `owned.json` | Your levels, their history, the states kept before bulk changes, and the characters you do not own |
| `my_builds.json`, `perk_types.json` | Your Build creator builds, and your corrections of the perk types |
| `captures/` | The last 100 screenshots the toolkit read, taken with your capture key or by the automatic mode, including the extra players-menu screenshots (a rotation: the oldest is deleted; the number is in Settings, 0 = none) |
| `config.json` | Your settings (hotkey or automatic mode, your keys, the automatic update delay…) |
| `shrine.json` | This week's Shrine of Secrets, as read from NightLight's public list |
| `nightlight_token.txt` | Your NightLight API token. Sent **only** to `api.nightlight.gg` |
| `nightlight_profile/` | The Edge profile holding your NightLight session |
| `window_profile/`, `entity_toolkit.ico` | What the Entity Toolkit window remembers (your filters, your daily-challenge streak…) and its icon |
| `uploads/`, `debug/` | The scoreboards sent and the last captures kept to diagnose problems |
| `entity_toolkit.log` | What the toolkit did |

Network use: the game screenshot never leaves your PC except the **scoreboard**, which goes to NightLight when you press your capture key on it, or by itself at the end of the match in automatic mode. That only happens if you saved a NightLight token; turn it off with *Dry run* or by unticking the sending on the Settings page. A database update (by itself after a game patch, every 7 days, or with **Update database**) reads from `deadbydaylight.wiki.gg`, `otzdarva-builds.com`, `otzdarva.com`, `otz-addon-tierlist.pages.dev` and `nightlight.gg`. At each start it also asks `api.steampowered.com` which patch the game is on, and `api.github.com` whether a newer Entity Toolkit exists; installing one downloads it from `github.com` (nothing is sent; each can be turned off in Settings), and once a week NightLight's public Shrine of Secrets list on `api.nightlight.gg` (nothing is sent, no token; turn it off in Settings). The local web server listens on `127.0.0.1` only and refuses requests from other websites.
