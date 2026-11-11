[← Home](https://github.com/Tau-hub/entity-toolkit/wiki/Home) · [Français](https://github.com/Tau-hub/entity-toolkit/wiki/Donnees-et-vie-privee)

## Data and privacy

Everything the toolkit stores lives in the git-ignored `data/` folder next to the code (override with the `ENTITY_TOOLKIT_DATA` environment variable):

| File / folder | What |
|---|---|
| `icons/`, `images/`, `loadout_data.json`, `loadout_extra.json`, `patch.json`, `killers.json`, `survivors.json`, `survivor_builds.json`, `maps.json`, `nl_maps.json` | Downloaded by **Update database** |
| `levels.json`, `levels_history.json`, `levels_backups.json`, `owned.json` | Your levels, their history, the states kept before bulk changes, and the characters you do not own |
| `my_builds.json`, `perk_types.json` | Your Build creator builds, and your corrections of the perk types |
| `captures/` | The last 100 screenshots taken with the capture key (a rotation: the oldest is deleted; the number is in Settings, 0 = none) |
| `config.json` | Your settings (including the automatic update delay) |
| `nightlight_token.txt` | Your NightLight API token. Sent **only** to `api.nightlight.gg` |
| `nightlight_profile/` | The Edge profile holding your NightLight session |
| `uploads/`, `debug/` | The scoreboards sent and the last captures kept to diagnose problems |
| `entity_toolkit.log` | What the toolkit did |

Network use: the game screenshot never leaves your PC except the **scoreboard**, which goes to NightLight when you press the key on it (turn that off with *Dry run* on the Settings page). **Update database** reads from `deadbydaylight.wiki.gg`, `otzdarva-builds.com`, `otzdarva.com`, `otz-addon-tierlist.pages.dev` and `nightlight.gg`. Once a day it also reads one public file on `raw.githubusercontent.com` to tell you when a newer Entity Toolkit exists (nothing is sent; turn it off in Settings), and once a week NightLight's public Shrine of Secrets list on `api.nightlight.gg` (nothing is sent, no token; turn it off in Settings). The local web server listens on `127.0.0.1` only and refuses requests from other websites.
