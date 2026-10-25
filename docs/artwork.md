# Game data and artwork

After a real organise run, the app gets images for each new game from up to three sources. It only downloads the image types a game doesn't have yet, so running again never replaces images you already have.

## What goes where

| Shown in | Image type | Folder | Source |
|---|---|---|---|
| ES-DE | Covers | `covers` | libretro, then SteamGridDB |
| ES-DE | Screenshots | `screenshots` | libretro |
| ES-DE | Title screens | `titlescreens` | libretro |
| ES-DE | Marquees (logos) | `marquees` | SteamGridDB |
| ES-DE | Fan art | `fanart` | SteamGridDB |
| ES-DE | Back covers, 3D boxes, physical media | `backcovers`, `3dboxes`, `physicalmedia` | Skyscraper |
| ES-DE | Videos, manuals | `videos`, `manuals` | Skyscraper |
| ES-DE | Miximages | `miximages` | ES-DE makes these itself from the other images |
| Steam | Library capsule (600×900) | `tall` | SteamGridDB |
| Steam | Wide capsule (920×430) | `long` | SteamGridDB |
| Steam | Hero banner | `hero` | SteamGridDB |
| Steam | Logo | `logo` | SteamGridDB |
| Steam | Icon | `icon` | SteamGridDB |

### ES-DE media

ES-DE images go into ES-DE's media folder, read from ES-DE's settings (usually `~/ES-DE/downloaded_media`):

```
downloaded_media/<system>/<type>/<game>.png
downloaded_media/snes/covers/Chrono Trigger (USA).png
```

The image is named after the game file without its extension. The exception is a folder ES-DE treats as a game (see [ES-DE layout](how-games-are-stored.md#es-de-layout)). Its images keep the folder's "extension", for example `Crash Bandicoot (USA).cue.png`.

### Steam artwork

Steam images go into a `steam-artwork` folder next to ES-DE's media folder, unless you choose another **Steam artwork folder** on the Settings page:

```
steam-artwork/<system>/<type>/<ROM file name>.png
steam-artwork/psx/tall/Final Fantasy VII (USA).png
```

## Sources

### libretro thumbnails

[thumbnails.libretro.com](https://thumbnails.libretro.com) has box art, screenshots and title screens, named after the games in the DAT files. It needs no account.

When a game matched a DAT, the app looks it up under that DAT's name, so matches are exact. Otherwise it uses the system's libretro folder and tries the game's other names, such as the playlist title for a multi-disc game. Characters libretro can't use in file names (`& * / : \` < > ? \ |`) are replaced with `_`, as libretro does.

### SteamGridDB

[SteamGridDB](https://www.steamgriddb.com) has Steam-style artwork for most games. It needs a free API key, set on the Settings page; see [Configuration](configuration.md#artwork). The app searches for the game once, then fetches each image type it's missing. PNG and JPEG files keep their real extension.

SteamGridDB also fills the ES-DE cover (when libretro has none), the marquee and the fan art.

### Skyscraper and ScreenScraper

[Skyscraper](https://github.com/Gemba/skyscraper) downloads game data from [ScreenScraper](https://www.screenscraper.fr): descriptions, release dates, genres and ratings. It also gets the media types the other sources don't have: back covers, 3D boxes, physical media, fan art, manuals and videos.

When Skyscraper is installed and on your `PATH`, the app runs it for each system that got new games, in two steps:

1. **Gather:** download data and media from ScreenScraper into Skyscraper's cache. Only games that are missing data are fetched.
2. **Generate:** write ES-DE's `gamelist.xml` for the system, and copy the media into ES-DE's media folder.

A ScreenScraper account makes scraping faster and more reliable; set it on the Settings page. If Skyscraper isn't installed, the app says so and skips this step. You can scrape from inside ES-DE instead (Main menu > Scraper).

## Steam ROM Manager

Steam ROM Manager (SRM) adds your ROMs to Steam as shortcuts. EmuDeck sets SRM up with one "parser" per emulator. SRM's own artwork search may not find older games, so the app can point SRM at the artwork it has downloaded.

Click **Use this app's artwork in Steam ROM Manager** on the page. The app then:

1. **Backs up SRM's settings.** It copies `~/.config/steam-rom-manager/userData/userConfigurations.json` to `userConfigurations.json.rom-organiser.bak`, the first time only. Later clicks keep that first backup.
2. **Fills in local image paths.** For each parser that launches games from a system folder, it sets the local image paths for all five Steam types, for example `<steam-artwork>/psx/tall/${fileName}.@(png|jpg)`.
3. **Leaves your own settings alone.** Image paths you've already set are kept. Parsers for apps or tools, rather than ROM folders, aren't touched.

Afterwards, open Steam ROM Manager and choose **Parse**, then **Save to Steam**. Close Steam first if SRM asks you to.

To undo it, copy the `.rom-organiser.bak` file back over `userConfigurations.json`.
