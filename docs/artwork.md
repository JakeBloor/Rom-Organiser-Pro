# Game data and artwork

After a real organise run, the app gets media for each new game from up to four sources, in this order:

1. **EmuMovies**, for supporters: every media type, videos and manuals included.
2. **Skyscraper**, with ScreenScraper: game data, plus any media EmuMovies didn't have.
3. **libretro** thumbnails.
4. **SteamGridDB**: Steam artwork, and anything still missing.

It only downloads the media types a game doesn't have yet. So the first source with a type wins, and running again never replaces media you already have.

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

### EmuMovies

[EmuMovies](https://emumovies.com) is the first source asked, for supporters. It provides:

- **Videos and manuals,** downloaded per game from EmuMovies' file server during each organise run.
- **Artwork,** which EmuMovies only offers as whole-system packs. Click **Download EmuMovies artwork** on the home page to fetch them once into a local library. Organise runs then copy each game's images from it.

The connection to EmuMovies is read-only. It can list folders and download files, and every other FTP command is refused before it reaches the server. Nothing on EmuMovies is ever changed or deleted. Audio isn't downloaded, since neither ES-DE nor Steam uses it.

**Setting up.** Sign in at emumovies.com and open **FTP Login**, which shows your FTP server (and a backup server), user name and password. Enter them in the **EmuMovies** section of Settings and turn on **Download from EmuMovies**. You can also choose the video quality (HD 1080p, HQ 480p or SQ 240p), and whether to download videos and manuals.

**Videos and manuals.** Games are matched by their DAT name, then their file name, then their title without tags, preferring your region. If a video isn't available in your chosen quality, the next quality is used. Folder listings are kept for a day in `cache/emumovies.json`, and downloads use one connection at a time.

**Artwork packs.** For each system in your ROM folder, the newest official pack of each art type is chosen. Where EmuMovies has no official pack for a type, the best community pack is used instead.

| Pack | ES-DE folder |
|---|---|
| Boxes-2D | covers |
| Boxes-3D | 3dboxes |
| Boxes-Back | backcovers |
| Gameplay snaps | screenshots |
| Title snaps | titlescreens |
| Logos | marquees |
| Game media, carts, discs | physicalmedia |
| Backgrounds | fanart |

Each pack is downloaded and unpacked into `<library>/<system>/<type>/`, then the downloaded archive is deleted. The library is the `emumovies-artwork` folder next to ES-DE's media folder unless you set another in Settings. `manifest.json` there records each pack's version, so a pack is only downloaded again when EmuMovies publishes a newer one. Images go into ES-DE's media folders as hard links when the library is on the same drive, so they take no extra space; otherwise they're copied.

Packs are large: about 1 to 10 GB per system for all eight types, around 37 GB for twelve popular systems. Archives are unpacked with libarchive, which is built into SteamOS and macOS, including `.rar` and `.7z` packs split into parts.

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
