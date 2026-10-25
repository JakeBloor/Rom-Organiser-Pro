# Troubleshooting

## A file was left in the import folder ("unsorted")

The app couldn't tell its system for certain. This usually happens with shared extensions like `.iso`, `.chd`, `.bin` or `.zip`. Move the file into a folder named after its system, for example `ps2/Game.iso` or `saturn/Game.chd`, and run again. [How systems are detected](detection.md) lists the folder names that work.

## A file was "skipped"

A file or playlist with the same name already exists in the ROM folder, or another file in the same run was going to the same place. The app never overwrites. If the existing copy is the one you want, delete the new file. Otherwise, remove the old one and run again.

## "Duplicate" files

Two files in the import folder are the same ROM. Only the first one is moved; the duplicate stays in the import folder.

## Few games match a DAT

- **The first start has to download the DAT files.** Check the startup log for a libretro download error.
- **Hacks, translations, homebrew and bad dumps aren't in the DATs.** They're still organised by extension and folder name, but artwork lookups use the file name, so matches are less likely.
- **For more coverage,** add the latest No-Intro or Redump DATs by hand. See [Where the DAT files come from](detection.md#where-the-dat-files-come-from).

## Settings don't seem to apply

Server settings (listen address, port and debug mode) only apply after a restart. Everything else applies straight away.

If the Settings page says `settings.json` couldn't be read, fix the file or delete it to go back to the defaults. Deleting it also removes your saved API key and ScreenScraper login. Because the file is tracked in git, `git checkout settings.json` brings back the last committed version.

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

## "An organise run is already in progress"

Only one run can go at a time. Wait for it to finish; the progress section shows how far it has got.
