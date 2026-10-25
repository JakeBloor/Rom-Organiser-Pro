# How systems are detected

To move a file, the app has to know for certain which system it's for. It checks these in order and stops at the first one that answers.

## 1. DAT match

The app works out the file's MD5 and SHA-1 checksums and looks them up in the loaded DAT files. When the file matches:

- the DAT's name gives the system ("Nintendo - Super Nintendo Entertainment System" → `snes`)
- the matching entry gives the official game name, which is used to look up artwork

For a `.zip` holding a single ROM, the ROM inside is checked. For a `.cue` or `.gdi`, the first track is checked, because DATs list track checksums, not the sheet.

### Where the DAT files come from

When the app starts, it downloads a fixed version of the [libretro database](https://github.com/libretro/libretro-database). It extracts three parts into `dats/libretro/`:

- `dat/`: libretro's own DATs
- `metadat/no-intro/`: cartridge systems
- `metadat/redump/`: disc systems

The download is skipped while the files for that version are already on disk. A failed download never deletes the DATs you already have.

To add DATs yourself, download them from [DAT-o-MATIC](https://datomatic.no-intro.org) (cartridge systems) or [redump.org](http://redump.org/downloads/) (disc systems). Put them in `dats/metadat/no-intro/` or `dats/metadat/redump/` and restart the app. Both XML and clrmamepro DATs work.

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

`SYSTEM_ROM_TYPES` in `config.py` is the full list, with each system's accepted extensions.
