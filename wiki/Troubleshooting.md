[← Home](https://github.com/Tau-hub/entity-toolkit/wiki/Home) · [Français](https://github.com/Tau-hub/entity-toolkit/wiki/Depannage)

## Troubleshooting

`data/entity_toolkit.log` says what the toolkit saw and did, with the time: it is the first place to look. The screenshots it read are in `data/captures/`.

### Nothing happens

- The game must be running **and** be the window in front, in borderless or windowed mode, in English.
- The toolkit must be running: the red **E** is in the notification area.
- **Hotkey mode:** press the capture key set in Settings (Alt + Numpad 7 until you change it). A numpad key needs NumLock on. A new shortcut only takes effect after the toolkit is restarted.
- **Automatic mode:** check that Settings says *Automatic*, and keep the players menu open about one second. After a tap shorter than half a second the log says *"Tab pressed but the players menu was not seen"*: press Tab again, a little longer.

### The window does not open, or I closed it

- Closed with *Keep it running*: double-click the red **E** in the notification area, or start the program again.
- If the window cannot start (the WebView2 engine is missing on an old Windows 10), the toolkit opens your browser instead and says so in the log. Install the *WebView2 Runtime* from Microsoft, or untick *Show the pages in the Entity Toolkit window* in Settings.
- It opened off-screen after unplugging a monitor: it goes back to the middle of a screen at the next start.

### "Screen not recognised" (hotkey mode)

The toolkit looks for the words *PLAYERS / QUESTS* (players menu) or *MATCH SCOREBOARD* at the top left. Check that the game is in English and that you pressed your capture key on one of those two screens. The capture is saved in `data/debug/` (`*_unknown.jpg`). In automatic mode this cannot happen: another screen is simply ignored.

### An ally or a perk is missing or wrong

- The mouse was on an item or a perk when the menu was read: the game's own tooltip covered part of it. The toolkit puts several screenshots together to work around it; if it is not enough, open the menu again with the mouse away from the icons (and press your capture key in hotkey mode).
- Perks below 78 % confidence are flagged "to check" on the Live page.
- After a game patch, run **Update database** so the new icons exist.

### The perks stayed after the match, or disappeared during it

- They are removed when the scoreboard is read. If you left the match without seeing the scoreboard (or without pressing your capture key on it, in hotkey mode), they stay until the next players menu is read, or until you press your clear key.
- They disappear if the toolkit is restarted during a match: read the players menu again.

### Automatic mode: the scoreboard is not sent

- The toolkit waits until the four survivors and the killer all show their loadout (perks, or at least the empty slots): while one row is still hidden, the match is not over. The Live page then says *"waiting for the end of the match"*.
- A bot or a player without perks is fine (their empty perk slots are recognised as a revealed loadout), but a custom match with fewer than five players never fills that condition: press your capture key on the scoreboard.
- NightLight must be set up (a token, and one sign-in). Without it, nothing is sent and nothing is said: that is intended.

### Overlay misplaced

Positions are proportional to the game screen's height and were measured at 2560×1440. Adjust `data/overlay_layout.json` (`x`, `dy`, `rows`, `size`, `gap`, described at the top of `entity_toolkit/overlay.py`) and read the players menu again. Pull requests with measurements for other resolutions are very welcome.

### NightLight review fails

Edge must be installed, and you must have signed in once (Settings → Sign in to NightLight). The window is visible on purpose: NightLight is behind Cloudflare, which refuses invisible browsers. The toolkit hands focus back to the game while it works.

### The names in the game's list are unreadable

Windows only reads the alphabets of the language packs installed (a Cyrillic name is not read with an English pack). The overlay then places the allies by their portrait, and falls back to the menu order when two of them play the same character.
