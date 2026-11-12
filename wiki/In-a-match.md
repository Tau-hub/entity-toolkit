[← Home](https://github.com/Tau-hub/entity-toolkit/wiki/Home) · [Français](https://github.com/Tau-hub/entity-toolkit/wiki/En-match)

## How it works, step by step

The toolkit acts at **two moments** of a match: at the start, on the players menu (Tab), and at the end, on the scoreboard. You choose in **Settings** how these two moments are triggered:

| Mode | At the start | At the end |
|---|---|---|
| **Automatic** (the default) | Open the players menu (Tab) and keep it open about one second | Nothing: the scoreboard is sent by itself |
| **Hotkey** | Open the players menu (Tab) and press **your capture key** | Press **your capture key** on the scoreboard |

**Your capture key** is the one set in Settings. It is **Alt + Numpad 7** until you change it (NumLock on), and any combination works: `f9`, `ctrl+shift+n`… The second key, the **clear key** (Alt + Numpad 8 until you change it), removes the overlay.

**1. At the start: the players menu is read.** The toolkit takes a screenshot of the game, reads the map name at the bottom, then for each ally the character, the player name and the four perks (icons compared with the downloaded ones). A short "ok" sound tells you it worked; the result also shows on the **Live** page.

- *Automatic:* open the menu with Tab and keep it open about one second.
- *Hotkey:* open the menu with Tab and press your capture key.

![The Tab players menu, as it is read (player names blurred)](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/players-menu.jpg)

**2. Close the menu: the perks appear next to your allies.** The game's own survivor list (top left of the screen) is only visible once the menu is closed. The toolkit watches it, recognises each ally by portrait (then by player name when two allies play the same character) and draws their four perks in a 2×2 grid beside them. They stay until the end of the match. Same thing in both modes.

![Back in the game: each ally's four perks drawn on the left survivor list (player names blurred)](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/ingame.jpg)

**3. At the end: the scoreboard is read.** The overlay is removed and the scoreboard screenshot is read: the players, their perks, add-ons, offerings, the points, and your character's level badge (your level is corrected on the Levels page).

- *Hotkey:* press your capture key on the scoreboard, once the match is over for everyone (while some players' perks are still hidden, the match is not finished and NightLight would get an incomplete scoreboard).
- *Automatic:* nothing to press. The toolkit waits by itself until every player's perks are revealed.

![The end-of-match scoreboard sent to NightLight (player names and chat blurred)](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/scoreboard.jpg)

**4. The match is uploaded to NightLight by itself** (if you set NightLight up). As soon as the scoreboard picture is good, a short blip sounds and a small *Uploading...* box appears at the top left of the game: **you can leave the scoreboard right away**, everything after that works on the picture already taken, and a last message tells you when the match is confirmed. It is sent with the map read in step 1, "Me" ticked on your name, everyone else set to Random, and confirmed, with no click from you. The match then appears in your NightLight history like any other upload. Same thing in both modes.

![The result on NightLight: map filled in, you ticked as "Me", everyone else Random (player names blurred)](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/nightlight.jpg)

If you do not want a match uploaded, press your clear key before the scoreboard (it removes the overlay and forgets the perks), or turn on *Dry run* in Settings. Without a NightLight token, nothing is ever sent.

## Hotkey mode

Choose **Hotkey** in Settings → *Hotkey or automatic* if you would rather decide yourself when the toolkit reads the screen: nothing is then looked at until you press your capture key. Your capture key only reacts while the game is running **and** in front. What it does depends on the screen:

| You are on… | Your capture key does this |
|---|---|
| The **players menu** (Tab), as survivor | Map remembered, allies' perks on the Live page, overlay drawn once you close the menu |
| The **players menu**, as killer | Map remembered |
| The game (menu closed), overlay shown | Nothing changes: the overlay stays (only the scoreboard or your clear key removes it) |
| The game (menu closed), overlay removed | Overlay put back with the last perks read |
| The **match scoreboard** | Overlay removed, screenshot sent to NightLight, match reviewed and confirmed, your character's level corrected |
| Anything else | "Not ok" sound, nothing is sent |

Both keys are changed in Settings → *Hotkey or automatic*; a new shortcut takes effect the next time the toolkit starts.

## Automatic mode

This is the mode the toolkit starts in (Settings → *Hotkey or automatic*; a change applies within a few seconds, no restart). You press no key at all:

1. **At the start of the match, press Tab and keep the menu open about one second.** The toolkit sees the players menu, reads the perks and the map, and draws the overlay. A tap shorter than half a second can be missed: nothing happens then, just press Tab again a little longer.
2. **Play.** Opening Tab again changes nothing: the toolkit sees the same allies and keeps the perks already shown.
3. **At the end, stay on the scoreboard a couple of seconds.** The scoreboard is sent to NightLight, and the overlay removed, only when the match is over for everyone: the game then reveals every player's perks, and the toolkit waits until the four survivors and the killer all show theirs. If you die first, or come back from spectating, the scoreboard you see still hides some perks: the toolkit waits.

Your capture key and your clear key keep working in automatic mode, for instance to send a scoreboard before everyone has finished.

**It only does what you set up.** If NightLight is not in use (no token, or sending turned off in Settings), the end of the match sends nothing and makes no sound: the toolkit just removes the overlay and updates your level.

**If the first reading is incomplete** (the mouse was on an item or a perk, so the game's own tooltip covered an ally or a perk), the toolkit uses the extra screenshots it takes right after the first one (up to six in two seconds, the first after 0.15 s) and puts the readings together, ally by ally and perk by perk. If that is still not enough, it reads the menu again at your next Tab. The same happens in hotkey mode.

**What it costs.** While the game is the window in front, the toolkit looks at a thin strip at the top left of the screen (where *PLAYERS* and *MATCH SCOREBOARD* are written) every 2 seconds, and nine times in the 1.6 seconds after a Tab press. One look takes about 30 ms. When the game is not in front, it looks at nothing.

**What it touches.** Nothing new compared with the capture key: a screenshot of the monitor, the state of the Tab key, and the list of running programs to know the game is in front. The game's memory and files are never read, and nothing is sent to the game. As always, there is no guarantee about anti-cheat: see the README.

**Limits.** A scoreboard is sent only when all five rows show their loadout. A bot, or a player who brought no perk at all, still shows the empty outlines of its perk slots and add-on squares, which counts; a row that is blank is a loadout the game still hides (the match is not over). A custom match with fewer than five players is not sent by itself: use your capture key. After one scoreboard, the next one is not sent by itself for 2.5 minutes (so leaving the page and coming back does not send it twice). If you leave a match without seeing the scoreboard, the overlay stays until your next Tab or your clear key.

## In both modes

**Removing the overlay.** Your clear key removes the overlay and forgets the perks (handy if you do not want to upload that match).

**Reading a perk.** While the mouse is free (hooked, dead, spectating), hover an icon of the overlay to see its text; move off the icon and it goes away. It only reads the mouse position (no hook, nothing read from the game): nothing at all while the overlay is hidden, twice a second while you play (the game hides and locks the cursor), and a fast check (25 times a second) only when the mouse is free **and** near the icons. During normal play the mouse is locked to the camera, so nothing shows. `data/entity_toolkit.log` records it: `Overlay hover:` lines for every change (mouse locked / free, text shown / hidden) and a summary of the number of checks each minute.

**Why the overlay waits.** The game's own survivor list is only visible once the Tab menu is closed. After the menu is read, the toolkit watches the screen, reads the names in the game's list and matches each ally to the right row, first by **portrait**, then by **player name** when two allies play the same character or the portraits are too similar. Your own row never moves.

**Starting and stopping.** The toolkit stops by itself when the game closes. To have it start by itself when the game starts, tick *Start automatically with Windows* in Settings (or run `python -m entity_toolkit autostart install`, undone with `autostart remove`). Only one copy ever runs: if you start it by hand and the autostart watcher then launches it again when the game starts, the second copy stops by itself, so nothing is handled twice.
