# Troubleshooting

## A game stays where I dropped it ("unsorted")

The app couldn't tell its system for certain. This usually happens with shared extensions like `.iso`, `.chd`, `.bin` or `.zip`. Move the file into a folder named after its system, for example `ps2/Game.iso` or `saturn/Game.chd`, and run again. [How systems are detected](detection.md) lists the folder names that work.

## A file was "skipped"

A file or playlist with the same name already exists in the ROM folder, or another file in the same run was going to the same place. The app never overwrites. If the existing copy is the one you want, delete the new file. Otherwise, remove the old one and run again.

## "Duplicate" files

The same game is already in your library, maybe under another name, or you dropped it in twice. Only one copy is organised; the duplicate stays where you dropped it. Delete it if you don't need it.

## A game I fixed still shows as needing me

The New games panel remembers why a game was left in place until the file changes or a run tries it again. Click **Organise** to try it again, or delete `cache/files.json` to clear everything the app has remembered.

## Few games match a DAT

- **The first start has to download the DAT files.** Check the startup log for a libretro download error.
- **Hacks, translations, homebrew and bad dumps aren't in the DATs.** They're still organised by extension and folder name, but artwork lookups use the file name, so matches are less likely.
- **For more coverage,** add the latest No-Intro or Redump DATs, TOSEC DATs for computers, or a MAME DAT. See [Where the DAT files come from](detection.md#where-the-dat-files-come-from).
- **The run report's DAT matches chart** shows why games didn't match. "Compressed image" games are named differently from the DATs and have no readable serial: rename them to their No-Intro or Redump names, or use uncompressed images.
- **Games organised before this update** aren't checked again. Turn on **Re-organise everything** for one run.

## Settings don't seem to apply

Server settings (listen address, port and debug mode) only apply after a restart. Everything else applies straight away.

If the Settings page says a settings file couldn't be read, fix that file or delete it:

- **`settings.json`:** run `git checkout settings.json` to get back the last committed version. Deleting it puts every setting back to its default.
- **`settings.local.json`:** deleting it removes your saved API key and ScreenScraper login, so enter them again on the Settings page.

## No game data, videos or manuals

These come from Skyscraper. If the log says "Skyscraper isn't installed", install [Skyscraper](https://github.com/Gemba/skyscraper) and make sure `Skyscraper` is on your `PATH`, or scrape from inside ES-DE (Main menu > Scraper). Make sure your ScreenScraper account is set on the Settings page.

## No Steam artwork, marquees or fan art

These need a SteamGridDB API key, set on the Settings page. The **API connections** line on the page shows whether one is set. If the log says "No results for …", SteamGridDB doesn't know the game under that name.

## Images are downloaded but ES-DE doesn't show them

- **Check the media folder.** In ES-DE, go to Main menu > Other settings > Game media directory. The app reads this setting from ES-DE's settings file, so the two should match. Also check that **ES-DE folder** on the Settings page points at the right ES-DE folder.
- **Restart ES-DE** or reload its game lists after adding media.

## Steam shows a game more than once

The game was probably stored with the **ES-DE folders** layout, or by hand inside a `Game.m3u/` folder. EmuDeck's Steam ROM Manager parsers add every file they find. Use the default `shared` layout for games you add to Steam. See [How games are stored](how-games-are-stored.md).

## A multi-disc game won't launch from its playlist

The playlist uses paths such as `../.multifile/psx/<game>/<disc>`. These work in RetroArch, DuckStation and other emulators that read paths relative to the playlist. Check that the files are still in `roms/.multifile/<system>/<game>/`, and open the `.m3u` in a text editor to see what it points at.

## Steam ROM Manager setup fails

The page shows an error if SRM's settings file is missing or broken. Open Steam ROM Manager once so it creates its settings, or set **Steam ROM Manager settings file** on the Settings page to the right file. To undo the app's changes, copy `userConfigurations.json.rom-organiser.bak` back over `userConfigurations.json`.

## The page won't open

- **Check the address.** It's `http://127.0.0.1:8181` by default, not port 8080.
- **To open it from another device,** set **Listen address** to `0.0.0.0` on the Settings page, restart the app, and use the Deck's IP address.
- **If port 8181 is taken,** choose another **Port** on the Settings page and restart. If the app can't start at all, edit `"port"` in `settings.json`, or delete `settings.json` to go back to the defaults.
- **If you changed the listen address or port,** the new values only apply after a restart.

## A run takes ages, or seems stuck

- **Look at the line under the progress bar.** It shows what the run is doing right now, such as "checking 2.1 GB of 4.3 GB" or Skyscraper's latest line, and how long since progress last moved. A minute of quiet usually means one big file or a slow scrape.
- **Big disc images:** files over **Largest file to check against DATs** (1 GB by default) are only fingerprinted. If you raised that setting, the first run reads every image in full, which takes about a minute per 4 GB from an SD card.
- **Your first run** works through your whole library once. Click **Stop** at any time; the next run carries on with the games that are left.
- **Skyscraper** can take a long time for a big system, especially without a ScreenScraper account. Turn off **Scrape game data with Skyscraper** in Settings to skip it, and scrape from ES-DE later.

## "An organise run is already in progress"

Only one run can go at a time. Wait for it to finish; the progress section shows how far it has got.
