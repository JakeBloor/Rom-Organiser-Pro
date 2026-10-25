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

1. Drag and drop new games into their system folder in your ROM folder, for example `~/Emulation/roms/snes/` or `~/Emulation/roms/psx/`. Games dropped loose in the ROM folder, or in a folder of their own, work too: the app works out their system.
2. Check the **ROM folder** on the page. It's filled in from ES-DE's settings.
3. The **New games** panel lists what's waiting to be organised. It checks the folder every 30 seconds, or click **Check now**.
4. Leave **Dry run** on and click **Preview (dry run)**. Nothing moves. The log shows where each file would go, and the run report shows what would happen.
5. If the preview looks right, turn **Dry run** off and click the button again to organise for real. The app moves the games into place, removes the folders it emptied, and then downloads game data and artwork.
6. Open ES-DE to see the games. To add them to Steam as well, see [Steam ROM Manager](artwork.md#steam-rom-manager).

The first time, every game already in your library shows as new, because the app hasn't organised any of them yet. The first real run works through them all once: it checks each against the DATs, looks for duplicates and fetches missing artwork, without moving games that are already in the right place. Hashing large disc images makes this run slow on a big library. After that, only games you add show as new.

Games the app couldn't identify stay where you dropped them, and the New games panel lists them as needing you. Move each one into a folder named after its system (for example `ps2/`) and run again. See [How systems are detected](detection.md).

## Next steps

- [Using the app](using-the-app.md): every part of the page.
- [Configuration](configuration.md): add your SteamGridDB and ScreenScraper accounts on the Settings page, change the port, and more.
