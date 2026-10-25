import os
import re
import shutil
from collections import defaultdict
from pathlib import Path

from config import (
    AMBIGUOUS_EXTENSIONS,
    M3U_SYSTEMS,
    MULTI_FILE_DIR,
    SYSTEM_MAP,
)
from modules import esde, settings
from modules.archives import sheet_tracks
from modules.hashing import hash_rom
from modules.dat_validation import lookup_hashes
from modules.detection import DISC_REGEX, detect_system, clean_name, get_disc_number
from modules.m3u import append_to_m3u

ARCADE_SYSTEMS = {"fbneo", "arcade", "mame"}
SHEET_SUFFIXES = {".cue", ".gdi"}


def _bump(status, key, amount=1):
    status[key] = status.get(key, 0) + amount


def _playlist_title(name):
    """"Final Fantasy VII (USA) (Disc 1)" -> "Final Fantasy VII (USA)"."""
    title = DISC_REGEX.sub("", name)
    title = re.sub(r"\(\s*\)|\[\s*\]", "", title)
    return re.sub(r"\s+", " ", title).strip(" -_")


def _is_rom_candidate(path):
    suffix = path.suffix.lower()
    return suffix in SYSTEM_MAP or suffix in AMBIGUOUS_EXTENSIONS


def _uses_shared_layout(system):
    """Whether a multi-file game for system gets a playlist pointing into MULTI_FILE_DIR."""
    return settings.get("multi_file_layout") == "shared" and system in M3U_SYSTEMS


def _write_playlist(playlist_dir, title, entries, logger, dry_run):
    if dry_run:
        logger(f"[DRY RUN] {playlist_dir / (title + '.m3u')} lists: {', '.join(entries)}")
        return

    # In the shared layout the system folder may not exist yet
    playlist_dir.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        append_to_m3u(playlist_dir, title, entry)


def _place(unit, dest_dir, logger, status, dry_run, planned, playlist=None):
    """
    Move a ROM and the files that belong with it into dest_dir, never
    overwriting. playlist is a new .m3u that must not exist yet either.
    """
    destinations = [dest_dir / f.name for f in unit]

    clash = next(
        (d for d in destinations + [playlist] if d and (d.exists() or d in planned)), None
    )
    if clash is None and dest_dir.exists() and not dest_dir.is_dir():
        clash = dest_dir

    if clash is not None:
        logger(f"[SKIP] {clash} already exists, leaving {unit[0]} in place")
        _bump(status, "skipped")
        return False

    planned.update(destinations)
    if playlist:
        planned.add(playlist)

    for source, destination in zip(unit, destinations):
        if dry_run:
            logger(f"[DRY RUN] {source} -> {destination}")
        else:
            dest_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))
            logger(f"[MOVED] {source} -> {destination}")

    _bump(status, "roms_processed")
    return True


def process_roms(input_folder, logger, status, dry_run=False, rom_root=None):
    """
    Move ROMs from input_folder into the EmuDeck layout under rom_root
    (ES-DE's ROM folder by default). Single-file games go straight into <system>/.
    Games made of several files (a .cue/.gdi with its tracks, or several
    discs) are stored so ES-DE and Steam ROM Manager list each game once:

    - "shared" layout, for M3U_SYSTEMS: the files go into
      <MULTI_FILE_DIR>/<system>/<Game>/ and <system>/<Game>.m3u points at them.
      Neither ES-DE nor Steam ROM Manager looks outside the system folders.
    - "esde" layout: ES-DE folders named like the file inside them,
      <system>/<Game>.cue/ or <system>/<Game>.m3u/ with the playlist inside.
    - other systems in the "shared" layout: files stay in <system>/, one
      entry per disc, since their Steam parsers don't accept playlists.

    A file's system comes from a DAT hash match, then its folder names, then
    its contents. Files that can't be identified without guessing are left in
    place. Existing files are never overwritten. With dry_run nothing is moved
    and the log shows where each file would go.

    Returns a list of placed games: {"system", "title", "path", "names",
    "dat_title"}. path is what ES-DE and Steam list (a file, or a folder ES-DE
    interprets as a file); names are the ROM names to look artwork up by;
    dat_title is the matching DAT's name (also its libretro thumbnail folder).
    """
    rom_root = Path(rom_root) if rom_root else esde.rom_root()
    layout = settings.get("multi_file_layout")
    files = sorted(p for p in Path(input_folder).rglob("*") if p.is_file())

    status["files_total"] = len(files)
    status["files_checked"] = 0

    tracks_by_sheet = {
        f: sheet_tracks(f) for f in files if f.suffix.lower() in SHEET_SUFFIXES
    }
    owned_tracks = {track for tracks in tracks_by_sheet.values() for track in tracks}

    seen_hashes = set()
    planned = set()
    placed = []
    discs_by_game = defaultdict(list)

    for index, file in enumerate(files):
        status["files_checked"] = index
        status["progress"] = int(index * 100 / len(files))
        status["current_file"] = file.name

        # Track files move together with their .cue/.gdi sheet
        if file in owned_tracks or not _is_rom_candidate(file):
            continue

        tracks = tracks_by_sheet.get(file, [])
        # DATs list the track data, not the sheet text
        hashes = hash_rom(tracks[0] if tracks else file)

        if hashes["md5"] in seen_hashes:
            logger(f"[DUPLICATE] {file}")
            _bump(status, "duplicates")
            continue

        seen_hashes.add(hashes["md5"])

        dat_name, dat_system, dat_title = lookup_hashes(hashes)
        system = dat_system or detect_system(file, allow_guess=False)

        if not system:
            logger(
                f"[UNSORTED] {file}: couldn't tell which system this is for. "
                "Put it in a folder named after the system (e.g. ps2/) and run again."
            )
            _bump(status, "unsorted")
            status.setdefault("unsorted_files", []).append(file.name)
            continue

        if dat_name:
            _bump(status, "dat_matches")

        unit = [file] + tracks
        disc = get_disc_number(file.stem) or (dat_name and get_disc_number(dat_name))

        game = {
            "system": system,
            "title": file.stem if system in ARCADE_SYSTEMS else dat_name or clean_name(file.stem),
            "names": [dat_name or file.stem],
            "dat_title": dat_title,
        }

        if disc and system not in ARCADE_SYSTEMS:
            title = _playlist_title(dat_name or file.stem)
            discs_by_game[(system, title)].append((disc, unit, game))
            continue

        playlist = None
        if tracks and _uses_shared_layout(system):
            dest_dir = rom_root / MULTI_FILE_DIR / system / file.stem
            playlist = rom_root / system / f"{file.stem}.m3u"
            launch_path = playlist
        elif tracks and layout == "esde":
            dest_dir = rom_root / system / file.name
            launch_path = dest_dir
        else:
            dest_dir = rom_root / system
            launch_path = dest_dir / file.name

        if _place(unit, dest_dir, logger, status, dry_run, planned, playlist):
            if playlist:
                entry = Path(os.path.relpath(dest_dir / file.name, playlist.parent)).as_posix()
                _write_playlist(playlist.parent, file.stem, [entry], logger, dry_run)
            placed.append({**game, "path": launch_path})

    for (system, title), discs in discs_by_game.items():
        discs.sort(key=lambda d: d[0])

        if _uses_shared_layout(system):
            dest_dir = rom_root / MULTI_FILE_DIR / system / title
            playlist_dir = rom_root / system
            launch_path = playlist_dir / f"{title}.m3u"
        elif layout == "esde":
            dest_dir = playlist_dir = launch_path = rom_root / system / f"{title}.m3u"
        else:
            # The system's Steam parser can't launch playlists: one entry per disc
            for _, unit, game in discs:
                if _place(unit, rom_root / system, logger, status, dry_run, planned):
                    placed.append({**game, "path": rom_root / system / unit[0].name})
            continue

        playlist_entries = [
            Path(os.path.relpath(dest_dir / unit[0].name, playlist_dir)).as_posix()
            for _, unit, _ in discs
            if _place(unit, dest_dir, logger, status, dry_run, planned)
        ]

        if not playlist_entries:
            continue

        _write_playlist(playlist_dir, title, playlist_entries, logger, dry_run)

        first = discs[0][2]
        placed.append(
            {
                **first,
                "title": clean_name(title),
                "names": first["names"] + [title],
                "path": launch_path,
            }
        )

    status["files_checked"] = len(files)
    status["progress"] = 100
    status["current_file"] = ""

    return placed
