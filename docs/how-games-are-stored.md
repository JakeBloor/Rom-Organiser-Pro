# How games are stored

Games go into one folder per system inside the ROM folder, named the way ES-DE and EmuDeck expect: `snes/`, `psx/`, `ps2/`, `gc/` and so on. ES-DE only shows games inside these folders.

Drop new games into their system folder, or anywhere else in the ROM folder. Organising moves each one into place, then removes any folder it emptied. System folders are never removed.

PS3 games are folders, either a `Game.ps3/` folder or a disc folder holding `PS3_GAME/`. Each is treated as one game and never looked inside. Its name comes from its `PARAM.SFO`, because the folder is often just a title ID like `BLUS30443`. A PS3 folder dropped anywhere else in the ROM folder is recognised and moved into `ps3/`.

A game in a system folder keeps that system as long as the system can run its file type, even if a DAT match suggests another one. A `.gba` file dropped into `snes/` is moved to `gba/`, because the SNES can't run it.

## Single-file games

Most games are one file and go straight into the system folder:

```
roms/snes/Chrono Trigger (USA).sfc
roms/gba/Advance Wars (USA).gba
```

If the game matched a DAT, it keeps the file name it already had. Arcade ROMs are never renamed, because emulators look them up by exact file name.

## Games made of several files

Some games are more than one file:

- a `.cue` or `.gdi` sheet with its track files, or
- several discs, such as `(Disc 1)` and `(Disc 2)`.

Stored carelessly, these show up several times. ES-DE would list every track file, and Steam ROM Manager adds a shortcut for every file it finds. So the app stores them in one of two layouts. Choose one with **Multi-file game layout** on the Settings page.

### Shared layout (default)

The files go in a hidden `.multifile` folder, and an `.m3u` playlist in the system folder points at them:

```
roms/psx/Final Fantasy VII (USA).m3u                    ← listed once in ES-DE and Steam
roms/.multifile/psx/Final Fantasy VII (USA)/
    Final Fantasy VII (USA) (Disc 1).chd
    Final Fantasy VII (USA) (Disc 2).chd
    Final Fantasy VII (USA) (Disc 3).chd
```

The playlist holds relative paths such as `../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd`. ES-DE skips hidden folders, and Steam ROM Manager only looks inside the system folders, so each game appears exactly once in both.

A single disc with a cue sheet is stored the same way: a one-line playlist, with the `.cue` and its tracks in `.multifile`.

The shared layout is only used for systems whose EmuDeck Steam ROM Manager parser accepts `.m3u` files: Amiga (all models), C16, C64, Dreamcast, GameCube, PC-FX, PlayStation, Saturn, Sega CD, VIC-20, Wii and X68000. Multi-file games for other systems stay in the system folder. A multi-disc game then gets one entry per disc, because those systems' Steam parsers can't launch a playlist.

### ES-DE layout

ES-DE can treat a folder whose name ends in an extension as a single game:

```
roms/psx/Final Fantasy VII (USA).m3u/
    Final Fantasy VII (USA).m3u
    Final Fantasy VII (USA) (Disc 1).chd
    ...
roms/psx/Crash Bandicoot (USA).cue/
    Crash Bandicoot (USA).cue
    Crash Bandicoot (USA).bin
```

This looks tidiest in ES-DE. It doesn't suit Steam, though: EmuDeck's Steam ROM Manager parsers add the folder and every disc inside it as separate shortcuts. Use this layout only if you don't add games to Steam.

## Safety rules

- **Nothing is overwritten.** If a destination file or playlist already exists, or another file in the same run is heading for the same place, the file stays where it was and is counted as **skipped**.
- **Duplicates stay put.** A file with the same checksum as one already handled in this run is counted as a **duplicate**.
- **No guessing.** A file whose system can't be determined for certain stays where you dropped it as **unsorted**. See [How systems are detected](detection.md).
- **Non-ROM files are ignored.** Files whose extension no system uses, like `.txt` or `.nfo`, are left alone.
- **Dry run** logs every move and playlist the run would make, and changes nothing.
