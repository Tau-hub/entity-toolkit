[← Home](https://github.com/Tau-hub/entity-toolkit/wiki/Home) · [Français](https://github.com/Tau-hub/entity-toolkit/wiki/Configuration)

## First launch: the Setup page

![Setup page, first launch](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/setup.png)

On the first launch, the Setup goes **one page at a time**, with **Next** and **Back**. Nothing blocks you: you can skip a page and come back, and everything is found again later in **⚙ Settings**.

1. **Requirements.** The page checks that Windows has an English OCR engine.
2. **Update database.** One button downloads perk names, descriptions and icons (DbD wiki), map names, Otzdarva's builds and tier list, and NightLight's stats. The first time takes a few minutes. Run it again after a game patch (new perks, new maps, new ratings). The page shows the patch the game is on (from the Steam announcements) and the patch label of Otzdarva's data, which can lag a few days behind the game; wiki pages are re-downloaded on every update. Each step reports on its own, so one site being down does not block the others. The same thing from a console: `python -m entity_toolkit update-db`. While it runs, the page shows which step it is on, and afterwards what the patch brought (new or removed killers, survivors, perks, add-ons, items, offerings, maps). Once you have done it once, the toolkit refreshes the data by itself every 7 days in the background (change or turn off in *Options*). Press the button, then **Next**: the download goes on in the background while you fill in the rest (and **Next** starts it for you if you forgot).
3. **Hotkey or automatic.** Choose how the toolkit is triggered: with the capture key (which you can change here), or in automatic mode, where you only keep the Tab menu open about one second at the start of the match (see [In a match](https://github.com/Tau-hub/entity-toolkit/wiki/In-a-match#automatic-mode)).
4. **Your in-game name.** Type your in-game name exactly as the scoreboard shows it.
5. **NightLight** (optional). The link on the page goes to [nightlight.gg/account/api](https://nightlight.gg/account/api), where you create your API token; paste it, then sign in once in the Edge window the button opens. The toolkit never sees your password. You do not use NightLight? Press **Next**: without a token nothing is ever sent, even in automatic mode.
6. **Your character levels** (optional). Drop screenshots of the in-game killer and survivor selection screens right on the Setup page and the toolkit reads which characters you have and their levels (you review before saving), or set them by hand on the **Levels** page (see below).
7. **Options.** The defaults suit most players. Overlay on/off, sounds, the notification-area icon, the new-version check, opening the Live page in your browser when the toolkit starts (on by default: with the automatic start, the page opens each time you launch the game), dry run (saves the scoreboard but never sends it), and the keys.
8. **Done.** A summary of what is ready and what you skipped, then **Finish setup**, which opens the Live page.

Every change on the page is saved as soon as you make it (a small *Saved ✓* note appears at the bottom right): there is no save button.

Once you press **Finish setup**, the *Setup* button becomes **⚙ Settings** (top right): same page without the requirements, to update the database, change your name, import levels, set the NightLight token and the options. *Reset the setup* at the bottom brings the first-launch checklist back (your data is kept).

![Settings page](https://raw.githubusercontent.com/Tau-hub/entity-toolkit/main/docs/images/settings.png)

### The notification-area icon

While the toolkit runs, a small red **E** sits in the Windows notification area (bottom right of the taskbar, behind the **^** arrow if Windows hides it). It tells you the toolkit is on, and it is the quickest way back to the pages when the browser tab is closed:

- **Double-click**: opens the Live page.
- **Right-click**: a menu with every page (Live, Levels, Killer priorities, Survivor priorities, Killer sheet, Survivor builds, Random loadout, Build creator), today's two daily challenges, **Settings**, then **Quit Entity Toolkit**, which stops the hotkeys, the overlay and the local pages.

You can turn the icon off in the options; the toolkit works the same without it.
