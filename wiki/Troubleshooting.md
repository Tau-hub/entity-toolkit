[← Home](https://github.com/Tau-hub/entity-toolkit/wiki/Home) · [Français](https://github.com/Tau-hub/entity-toolkit/wiki/Depannage)

## Troubleshooting

- **"Screen not recognised"**: the toolkit looks for the words *PLAYERS / QUESTS* (players menu) or *MATCH SCOREBOARD* at the top left. Check that the game is in English and that you pressed the key on one of those two screens. The capture is saved in `data/debug/` (`*_unknown.jpg`).
- **Nothing happens**: the game must be running and in front. Look at `data/entity_toolkit.log`. Run `python -m entity_toolkit` instead of `run.bat` to see the console.
- **Wrong or missing perks**: perks below 78 % confidence are flagged "to check" on the Live page. Run **Update database** after a patch so the new icons exist.
- **Overlay misplaced**: positions are proportional to the game screen's height and were measured at 2560×1440. Adjust `data/overlay_layout.json` (`x`, `dy`, `rows`, `size`, `gap`, described at the top of `entity_toolkit/overlay.py`) and press the key again. Pull requests with measurements for other resolutions are very welcome.
- **NightLight review fails**: Edge must be installed, and you must have signed in once (Settings → Sign in to NightLight). The window is visible on purpose: NightLight is behind Cloudflare, which refuses invisible browsers. The toolkit hands focus back to the game while it works.
- **The game's list names are unreadable**: the overlay then falls back to the menu order.
