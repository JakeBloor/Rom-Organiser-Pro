# How systems are detected

To move a file, the app has to know for certain which system it's for. It checks these in order and stops at the first one that answers.

## 1. DAT match

The app works out the file's MD5 and SHA-1 checksums and looks them up in the loaded DAT files. When the file matches:

- the DAT's name gives the system ("Nintendo - Super Nintendo Entertainment System" → `snes`)
- the matching entry gives the official game name, which is used to look up artwork

A few files need special handling:

- **Zips:** for a `.zip` holding a single ROM, the ROM inside is checked.
- **Cue and gdi sheets:** the first track is checked, because DATs list track checksums, not the sheet.
- **SNES copier headers:** an SNES dump with a 512-byte copier header is checked without it, as the DATs are.
- **CHDs:** a `.chd` isn't read in full. Its header records a SHA-1 of the original data, and for DVD-based games (PS2, PSP) that matches the Redump DAT directly.

Other compressed images (`.rvz`, `.cso`, `.wbfs`, `.7z` and others), and files over **Largest file to check against DATs** in Settings, are only fingerprinted. DATs list checksums of uncompressed images, so a compressed one can never match.

### Matching by serial

When the checksum doesn't match, the app reads the game's serial from the start of the file and looks it up in the DATs. Only a few kilobytes are read, so this works for big and compressed images too:

| Format | Serial from |
|---|---|
| GameCube and Wii: `.iso`, `.gcm`, `.ciso`, `.wbfs`, `.rvz`, `.wia` | The disc's game ID, e.g. `GM8E01` |
| PS1 and PS2: `.iso`, `.bin`, `.img` | The boot file named in `SYSTEM.CNF`, e.g. `SLUS_203.12` |
| PSP: `.iso` | `UMD_DATA.BIN`, e.g. `ULUS-10041` |
| PSP and PS1: `.pbp` | Its `PARAM.SFO` |
| PS3 game folders | `PARAM.SFO`, e.g. `BLUS30443` |

Serials come from the Redump DATs and from libretro's GameTDB-based DATs, about 90,000 of them. `.chd`, `.cso` and `.gcz` files compress their headers too, so they rely on the CHD checksum or the name instead.

### Matching by name

When neither the checksum nor the serial matches, the app looks the file's name up in the DATs instead. Most ROM sets are named exactly as in No-Intro and Redump, for example `Chrono Trigger (USA).sfc`. Names are compared ignoring capitals, underscores and extra spaces.

- **The folder's system decides:** a game in a system folder only matches that system's DAT names.
- **Outside the system folders,** a name must belong to just one system to count.
- **A plain name** also matches the release the DAT lists with more tags. For example, `Gran Turismo 4 (USA)` matches `Gran Turismo 4 (USA) (v2.00)`, the latest released version. Betas, prototypes and demos aren't used.

The run report shows how many games matched by checksum, how many by name, and why the rest matched nothing:

- **compressed:** a compressed image whose name isn't in the DATs
- **too big:** a file too big to check, whose name isn't in the DATs
- **not in the DATs:** usually a renamed or patched dump, a hack, or homebrew

### Where the DAT files come from

When the app starts, it downloads a fixed version of the [libretro database](https://github.com/libretro/libretro-database), currently from 25 October 2026. It extracts three parts into `dats/libretro/`:

- `dat/`: libretro's own DATs
- `metadat/no-intro/`: cartridge systems
- `metadat/redump/`: disc systems

The download is skipped while the files for that version are already on disk. A failed download never deletes the DATs you already have.

Some of libretro's DATs, such as those for GameCube, Wii and PS3, list serial numbers instead of checksums. The app uses them for serial and name matching.

The app also downloads [FinalBurn Neo](https://github.com/libretro/FBNeo/tree/master/dats)'s arcade and Neo Geo DATs, free on GitHub, into `dats/fbneo/`. Arcade sets are zips named by set (`sf2.zip`), so these match each zip to its game. That gives the full title, such as "Street Fighter II: The World Warrior", for artwork. They cover the `arcade`, `fbneo`, `mame` and `neogeo` folders.

To add DATs yourself, download them from [DAT-o-MATIC](https://datomatic.no-intro.org) (cartridge systems) or [redump.org](http://redump.org/downloads/) (disc systems). Put them in `dats/metadat/no-intro/` or `dats/metadat/redump/` and restart the app. Both XML and clrmamepro DATs work.

Any other DAT goes in `dats/extra/`:

- **[TOSEC](https://www.tosecdev.org/downloads)** (free) for computers. DATs named `Commodore Amiga - ...`, `Commodore C64 - ...`, `Atari ST - ...`, `Sinclair ZX Spectrum - ...`, `MSX MSX - ...`, `Amstrad CPC - ...` and similar are linked to their system folders.
- **A MAME DAT** (named `MAME <version>.dat`, free from [progettoSNAPS](https://www.progettosnaps.net/dats/MAME/)) for the `mame` folder.
- **Newer No-Intro or Redump DATs** named the libretro way, e.g. `Nintendo - Game Boy.dat`.

## 2. Arcade folders

A file inside a folder named `mame`, `fbneo` or `arcade` is treated as an arcade game for that system. A `neogeo` or `Neo Geo` folder counts as `fbneo`.

## 3. Extension

Many extensions belong to only one system, such as `.sfc` (SNES), `.gba` (Game Boy Advance) and `.nds` (Nintendo DS). These are decided by the extension alone.

## 4. Folder names

Some extensions are shared between systems: `.iso`, `.chd`, `.cue`, `.bin`, `.zip`, `.pkg` and others. For these, the app looks at the names of the folders the file sits in, starting with the nearest.

Folder names must match exactly, ignoring capitals, spaces, dashes and underscores. `snes` never matches `nes`, and `gba` never matches `gb`. Common alternative names work too: `PlayStation 2` or `ps2`, `GameCube` or `gc`, `Mega Drive` or `genesis`, and so on.

This is the easiest fix for an unsorted file: put it in a folder named after its system and run again.

## 5. File contents

Without a helpful folder name, the app looks inside the file:

- **Zip archives** holding a single ROM are judged by that ROM's extension.
- **Disc images** (`.iso`, `.bin`, `.img`) are recognised from their header: GameCube and Wii discs, Sega discs (Saturn, Sega CD, Dreamcast) and PlayStation discs. PS1 and PS2 are told apart by the disc's boot file.

## Unsorted files

If none of these settles it, the file stays where you dropped it and is reported as **unsorted**. The organiser never falls back to a best guess.

Scanning your library is different, because it moves nothing. When counting a file outside the system folders, the scan may go with the most likely system.

## Supported systems

The app knows 66 system folders, including:

- **Nintendo:** NES, Famicom Disk System, SNES, N64, GameCube, Wii, Wii U, Switch, Game Boy, Game Boy Color, Game Boy Advance, DS, 3DS and Virtual Boy
- **Sony:** PlayStation 1 to 5, PSP and PS Vita
- **Sega:** Master System, Genesis/Mega Drive, Sega CD, 32X, Saturn, Dreamcast and Game Gear
- **Atari:** 2600, 5200, 7800, 800, Lynx, Jaguar, Jaguar CD and ST
- **Microsoft:** Xbox, Xbox 360, Xbox One and Xbox Series X
- **Computers and others:** Amiga, Amstrad CPC, C64, VIC-20, DOS, MSX, X68000, ZX Spectrum, PC Engine and PC Engine CD, Neo Geo Pocket, WonderSwan, and arcade (MAME, FBNeo, Neo Geo)
- **Engines and fantasy consoles:** ScummVM, OpenBOR, PICO-8, TIC-80, Solarus, EasyRPG, Lutro, and ports

ES-DE's other folder names for these systems work too, for example `megadrive`, `megacd`, `famicom`, `sfc`, `tg16`, `tg-cd`, `sgb`, `msx1` and `cps1`. A game in one of them matches the DATs, artwork and Skyscraper platform of the system it stands for (`SYSTEM_ALIASES` in `config.py`).

Smaller systems with No-Intro DATs are supported too: Arduboy, Arcadia 2001, Channel F, Super Cassette Vision, Videopac+, CreatiVision, Game.com, Supervision, Game Master, PV-1000, Super A'Can, Sufami Turbo, ZX81, X1, Plus/4, V.Smile, PC-98, Atomiswave, Uzebox, J2ME, Palm OS, WASM-4 and LowRes NX.

`SYSTEM_ROM_TYPES` in `config.py` is the full list, with each system's accepted extensions.
