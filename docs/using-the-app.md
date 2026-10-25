# Using the app

The **Logs** and **⚙️ Settings** buttons at the top open the full log and the [settings](configuration.md).

The page has three parts: the **library panel** at the top, the **organise form**, and the **progress and run report** below it. It follows your device's light or dark setting.

## Library panel

This shows what's already in your ROM folder:

- **Totals:** games, systems detected and files the app couldn't identify.
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

A game outside the system folders, for example in `roms/Downloads/`, still counts towards a system you picked. Files the app can't identify are only counted when you scan all systems.

## Organising

| Field | Meaning |
|---|---|
| **ROM Import Folder** | The folder of new ROMs to sort. Sub-folders are included. |
| **EmuDeck ROM Folder** | Where the games go, one folder per system. Read from ES-DE's settings. |
| **Dry run** | When on, nothing moves and nothing is downloaded. The log and report show what *would* happen. The button reads **Preview (dry run)** or **Organise** to match. |

Only one run can go at a time. The form locks while a run is going.

A real run has three phases:

1. **Organising.** Each file is identified and moved. See [How games are stored](how-games-are-stored.md).
2. **Scraping.** If Skyscraper is installed, it downloads game data and extra media for each system that got new games. If it isn't installed, the app logs a warning and skips this phase.
3. **Artwork.** Images are downloaded from libretro and SteamGridDB for each new game. See [Game data and artwork](artwork.md).

## Progress

While a run is going you'll see:

- the current phase and file, with a progress bar
- counters for organised games, DAT matches, duplicates, unsorted and skipped files, and images downloaded
- the live log, which keeps the most recent 500 lines; `/logs` shows the full log

## Run report

When a run finishes, the run report shows:

- **What happened to each file:** organised, unsorted, skipped (the destination already existed) or duplicate (the same ROM appeared twice).
- **Games organised by system.**
- **ES-DE and Steam image coverage** for the games this run organised. A dry run says that images are only downloaded on a real run.
- **Files left in the import folder,** with what to do about them.
