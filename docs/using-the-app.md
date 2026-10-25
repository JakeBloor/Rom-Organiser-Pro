# Using the app

The **Logs** and **⚙️ Settings** buttons at the top open the full log and the [settings](configuration.md).

The page has three parts: the **library panel** at the top, the **organise form**, and the **progress and run report** below it. It follows your device's light or dark setting.

## Library panel

This shows what's already in your ROM folder:

- **Totals:** games, systems detected, and games in the ROM folder still to organise.
- **Library report:** three charts.
  - **Games by system.** The 12 biggest systems are shown; the rest are grouped as "Other".
  - **ES-DE media.** The share of games that have each image type ES-DE uses: covers, screenshots, marquees, videos and so on.
  - **Steam artwork.** The share of games that have each of Steam's five image types.
- **API connections:** whether SteamGridDB and ScreenScraper are set up.
- **Use this app's artwork in Steam ROM Manager:** see [Steam ROM Manager](artwork.md#steam-rom-manager).
- **Last scanned:** when the library was last scanned, and whether it covered all systems or only some.

Each chart shows exact numbers when you hover over or tab to a bar. **Show as table** lists the same numbers as a table.

## Scanning

Scanning counts the games in your ROM folder and checks which images they have. It never moves or changes files. The app also scans when it starts and after each real organise run.

Under the **Scan Games** button, choose what to scan:

- **All systems** (the default).
- **Only the systems I pick.** Shows a checkbox for each system folder in your ROM folder, with **Select all** and **Clear** buttons. Only the ticked systems are scanned, and the library report then covers only those. On a large library this is much quicker.

Only games in the system folders count, because that's all ES-DE shows. Games you've dropped elsewhere in the ROM folder appear in the **New games** panel instead.

## Organising

| Field | Meaning |
|---|---|
| **ROM folder** | Your games, one folder per system, and where you drop new ones. Read from ES-DE's settings. |
| **Dry run** | When on, nothing moves and nothing is downloaded. The log and report show what *would* happen. The button reads **Preview (dry run)** or **Organise** to match. |

Only one run can go at a time. The form locks while a run is going.

### New games

Drop new games into their system folder, such as `roms/snes/`. Games dropped loose in the ROM folder, or in a folder of their own, work too. The **New games** panel shows:

- **New games to organise:**
  - games in a system folder that the app hasn't organised yet, or that have changed since
  - games outside the system folders
  - multi-file games that need storing differently, such as the discs of a PlayStation game or a `.cue` with its tracks; see [How games are stored](how-games-are-stored.md)
- **Games that need you:** ones an earlier run left where they were, with why:
  - **unsorted:** the app couldn't tell which system it's for
  - **skipped:** a game with that name is already in place
  - **duplicate:** the same game is already in your library

The panel checks every 30 seconds while the page is open, and after every run. Click **Check now** to check straight away. Organising only touches the games listed, and a game already in the right system folder stays where it is.

The first time, every game already in your library is new, so the first run works through the whole library once. After that, only games you add show up.

Games the app has already examined and left in place aren't hashed again on the next run, unless the file has changed. See [Cache](#cache).

A real run has four steps. The systems listed under **Systems to organise first** in Settings go first in each step (by default `psx, ps2, ps3, psp, gc, n64, xbox`).

1. **Finding new games** in the ROM folder.
2. **Organising.** Each game is identified and moved, or organised where it is. See [How games are stored](how-games-are-stored.md).
3. **Scraping.** If Skyscraper is installed, it downloads game data and extra media for each system that got new games. If it isn't installed, the app logs a warning and skips this step.
4. **Artwork.** Images are downloaded from libretro and SteamGridDB, for four games at a time. See [Game data and artwork](artwork.md).

A dry run stops after step 2.

## Progress

While a run is going you'll see:

- the step, and the current file or system, with a progress bar
- what's happening right now, such as "checking 1.2 GB of 4.3 GB" or Skyscraper's latest line
- how long the run has been going
- a warning if nothing has moved for a minute. That usually means one very big file or a slow scrape, not a stuck run.
- counters for organised games, DAT matches, duplicates, unsorted and skipped files, and images downloaded
- the live log, which keeps the most recent 500 lines; `/logs` shows the full log

### Stopping a run

Click **Stop** next to Progress. The run finishes the file, system or game it's on, then stops; nothing is left half moved. Games it didn't reach are still listed as new, so the next run picks up where it left off.

## Run report

When a run finishes, the run report shows:

- **What happened to each file:** organised, unsorted, skipped (the destination already existed) or duplicate (the same ROM appeared twice).
- **Games organised by system.**
- **ES-DE and Steam image coverage** for the games this run organised. A dry run says that images are only downloaded on a real run.
- **Files left where you dropped them,** with what to do about them.

## Cache

The app keeps notes about files in `cache/files.json` in the app folder:

- **Checksums:** a game left in place, or one already organised, isn't hashed again. Hashing a large disc image can take a while.
- **The last result for games left in place:** this is how the New games panel knows which ones need you.
- **The games it has organised:** this is how it tells games you've just dropped into a system folder from ones it has already handled. A game you drop in a second time, even under another name, is caught as a duplicate instead of being added twice.

Notes are only trusted while a file's size and modification time are unchanged, so editing or replacing a file makes the app look at it again. The cache isn't in git, and deleting it is always safe: every game shows as new again, and the next run works through the library once more without moving anything already in place.
