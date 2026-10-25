# Getting started

## What you need

- **Python 3.12 or newer.**
- **EmuDeck.** The app works without it, but it's built for EmuDeck's folder layout and ES-DE.
- **Internet access** for the first run, to download the game lists (DAT files) and artwork.
- **Optional:** [Skyscraper](https://github.com/Gemba/skyscraper), for game descriptions, videos, manuals and extra image types. See [Game data and artwork](artwork.md).
- **Optional:** [Steam ROM Manager](https://github.com/SteamGridDB/steam-rom-manager), to add your games to Steam. EmuDeck installs it.

## Install

```bash
git clone <this repository>
cd RomOrganiser
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
source .venv/bin/activate
python app.py
```

Then open **http://127.0.0.1:8181** in a browser on the same machine.

Before your first real run, open **⚙️ Settings** and add your SteamGridDB API key. Add a ScreenScraper account too if you use Skyscraper. Without them, the app still organises games, but downloads less artwork.

### What happens on the first start

1. **Game lists download.** The app fetches the libretro database's DAT files, the lists of known good ROMs with their checksums, into `dats/libretro/`. Later starts skip this while those files are still on disk.
2. **The DAT files load.**
3. **Your library is scanned.** The app scans the ROM folder ES-DE uses, so the page opens showing what you already have.

Startup messages appear in the terminal and on the page's log.

## Organise your first ROMs

1. Put the new ROMs in a folder of their own, for example `~/Downloads/NewROMs`. Sub-folders are fine.
2. On the page, enter that folder as the **ROM Import Folder**.
3. Check the **EmuDeck ROM Folder**. It's filled in from ES-DE's settings, usually `~/Emulation/roms`.
4. Leave **Dry run** on and click **Preview (dry run)**. Nothing moves. The log shows where each file would go, and the run report shows what would happen.
5. If the preview looks right, turn **Dry run** off and click the button again to organise for real. The app moves the files and then downloads game data and artwork.
6. Open ES-DE to see the games. To add them to Steam as well, see [Steam ROM Manager](artwork.md#steam-rom-manager).

Files the app couldn't identify stay in the import folder. The run report lists them. Put each one in a folder named after its system (for example `ps2/`) and run again. See [How systems are detected](detection.md).

## Next steps

- [Using the app](using-the-app.md): every part of the page.
- [Configuration](configuration.md): add your SteamGridDB and ScreenScraper accounts on the Settings page, change the port, and more.
