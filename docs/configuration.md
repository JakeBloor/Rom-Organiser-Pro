# Configuration

Change settings on the **Settings** page: click **⚙️ Settings** at the top of the home page, or go to `http://127.0.0.1:8181/settings`. Click **Save settings** to store them.

Settings are saved in `settings.json` in the app folder. Most apply straight away. Server settings are marked **Applies after restart**, and the page tells you when a restart is needed.

`settings.json` is tracked in git, and it includes your API key and ScreenScraper password. Anyone who can see the repository can read and use them. On disk, it's saved with owner-only permissions (`600`).

If the file is missing, every setting uses its default. If the file is broken, the Settings page and the startup log say so and the defaults are used.

## Folders

| Setting | Default | What it does |
|---|---|---|
| ES-DE folder | `~/ES-DE` | ES-DE's own folder. The app reads `settings/es_settings.xml` here to find your ROM and media folders, which EmuDeck sets, including when ROMs are on an SD card. |
| Default ROM folder | `~/Emulation/roms` | Used when ES-DE's settings don't name a ROM folder. You can also type a different ROM folder on the home page for each run. |
| Steam artwork folder | blank | Where Steam artwork is saved. Leave it blank for a `steam-artwork` folder next to ES-DE's media folder. |
| Steam ROM Manager settings file | `~/.config/steam-rom-manager/userData/userConfigurations.json` | The file the **Use this app's artwork in Steam ROM Manager** button updates. |
| Multi-file game layout | Shared | How games with several files are stored. See [How games are stored](how-games-are-stored.md). |

`~` stands for your home folder.

Two folders are fixed, relative to the app folder: DAT files go in `dats/` and log files in `logs/`. ES-DE's game lists are in `gamelists/` inside the ES-DE folder.

## Artwork

| Setting | Default | What it does |
|---|---|---|
| Download libretro thumbnails | on | Covers, screenshots and title screens. No account needed. |
| Download from SteamGridDB | on | Steam artwork, plus ES-DE marquees and fan art. |
| SteamGridDB API key | not set | Get one free at [steamgriddb.com/profile/preferences/api](https://www.steamgriddb.com/profile/preferences/api). |

## Game data

| Setting | Default | What it does |
|---|---|---|
| Scrape game data with Skyscraper | on | Runs Skyscraper after organising. It only runs when Skyscraper is installed. |
| ScreenScraper user name and password | not set | Your [ScreenScraper](https://www.screenscraper.fr) account, passed to Skyscraper. |
| Preferred region | `us` | For box art and data, such as `us`, `eu`, `jp` or `wor`. |
| Preferred language | `en` | For descriptions, such as `en`, `fr` or `de`. |
| Download threads | `4` | From 1 to 32. ScreenScraper limits threads by account level. |

## Passwords and keys

The page never shows a saved password or API key; it only says whether one is saved.

- **To keep one,** leave its box empty.
- **To change it,** type the new one.
- **To delete it,** tick **Remove the saved …** under the box.

## Server

These apply the next time the app starts.

| Setting | Default | What it does |
|---|---|---|
| Listen address | `127.0.0.1` | `127.0.0.1` means only this device can open the page. `0.0.0.0` lets other devices on your network open it. |
| Port | `8181` | The web server's port. |
| Debug mode | off | Flask's debug mode and reloader, for development. It can only be turned on with a `127.0.0.1` listen address, because the debugger lets anyone who can open the page run code. |

## Fixed tables in config.py

`config.py` holds the tables the app works from. You don't normally need to change them. To add a system, see [Development](development.md#adding-a-system).

| Table | Meaning |
|---|---|
| `SYSTEM_ROM_TYPES` | Every system folder and the file extensions it accepts. |
| `SYSTEM_MAP` | Extensions that belong to a single system. |
| `AMBIGUOUS_EXTENSIONS` | Extensions shared by several systems, decided by folder name or contents. See [How systems are detected](detection.md). |
| `SYSTEM_PRIORITY` | Order used when a library scan has to guess. The organiser never guesses. |
| `DAT_SYSTEM_IDS` | DAT names mapped to system folders. They are also libretro thumbnail folder names. |
| `M3U_SYSTEMS` | Systems that get the shared playlist layout. |
| `SKYSCRAPER_PLATFORMS` | Skyscraper's names for systems whose folder name differs, such as `genesis` → `megadrive`. |
