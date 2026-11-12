# The database shipped with Entity Toolkit

This folder is a copy of the data the toolkit otherwise downloads with **Update database**, so that it works right after installing.
`seed.json` says which day it was taken and for which game patch. The toolkit copies it into your `data` folder at the first start and
keeps it current afterwards.

**None of it belongs to this project, and the MIT licence of the code does not cover it.** It is redistributed here, unchanged, for the
convenience of players, with the source of each part:

| What | Files | Source and owner |
|---|---|---|
| Perk, add-on, item, offering and power icons, character portraits | `icons/`, `images/` | *Dead by Daylight* © Behaviour Interactive Inc., as published on the [Dead by Daylight wiki](https://deadbydaylight.wiki.gg) |
| Perk, add-on, item and offering names and descriptions, map and realm names | `loadout_data.json`, `loadout_extra.json`, `maps.json` | The [Dead by Daylight wiki](https://deadbydaylight.wiki.gg) and its contributors (text under the wiki's own licence); the game text is © Behaviour Interactive Inc. |
| Builds, perk values, add-on tier list | `killers.json`, `survivors.json`, `survivor_builds.json` | **Otzdarva** ([otzdarva-builds.com](https://otzdarva-builds.com), [otzdarva.com](https://otzdarva.com)) |
| Community statistics, most played builds, map ids, some icons (`images/nl_*`) | same files, `nl_maps.json` | **[NightLight](https://nightlight.gg)** |
| The game's current patch | `patch.json` | Steam announcements of *Dead by Daylight* |

Entity Toolkit is not affiliated with any of them. If you own some of this content and want it removed from this repository, open an
issue: it will be taken out, and the toolkit will go back to downloading it on each user's PC.

Nothing personal is in here: no levels, no settings, no account, no screenshot. Rebuild it with `python packaging/make_seed.py`.
