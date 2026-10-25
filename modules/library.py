"""
List the games in a ROM library the way ES-DE lists them, and find the new
files dropped into it that still need organising.
"""

import os
from collections import Counter
from pathlib import Path

from config import AMBIGUOUS_EXTENSIONS, DAT_SYSTEM_IDS, SYSTEM_MAP, SYSTEM_ROM_TYPES, canonical_system
from modules.archives import is_ps3_folder, sheet_tracks
from modules.dat_validation import ARCADE_FAMILY
from modules.detection import get_disc_number
from modules.organizer import SHEET_SUFFIXES, is_rom_candidate, stores_multi_file_games_apart

# Folders ES-DE launches as a single game ("Game.m3u/", "Game.cue/")
FOLDER_GAME_SUFFIXES = {".m3u", ".cue", ".gdi"}
KNOWN_SYSTEMS = set(SYSTEM_ROM_TYPES) | set(DAT_SYSTEM_IDS.values())


def is_game_folder(folder):
    """
    A folder that is one game, never looked inside: ES-DE's "Game.m3u/"-style
    folders, and PS3 games, which are folders of thousands of files.
    """
    folder = Path(folder)
    return folder.suffix.lower() in FOLDER_GAME_SUFFIXES or is_ps3_folder(folder)


def _is_rom_candidate(name):
    suffix = Path(name).suffix.lower()
    return suffix in SYSTEM_MAP or suffix in AMBIGUOUS_EXTENSIONS or suffix == ".m3u"


def system_folders(rom_root):
    """The system folders (e.g. "snes") directly under rom_root, sorted."""
    return sorted(
        entry.name
        for entry in Path(rom_root).iterdir()
        if entry.is_dir() and entry.name in KNOWN_SYSTEMS
    )


def list_library(rom_root, systems=None):
    """
    The games ES-DE lists, as (system, path) pairs: everything in the system
    folders (e.g. "snes/"), with folders ES-DE launches as one game counted
    once and track files left out. ES-DE doesn't look outside the system
    folders, so files there aren't games yet; see pending_games. Hidden
    folders, such as the .multifile store, are skipped. With systems, only
    those system folders are read.
    """
    rom_root = Path(rom_root)
    games = []

    for system in system_folders(rom_root):
        if systems and system not in systems:
            continue

        for dirpath, dirnames, filenames in os.walk(rom_root / system):
            here = Path(dirpath)

            # Hidden folders are skipped by ES-DE too
            dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))

            for folder_game in [d for d in dirnames if is_game_folder(here / d)]:
                dirnames.remove(folder_game)
                games.append((system, here / folder_game))

            roms = sorted(f for f in filenames if not f.startswith(".") and _is_rom_candidate(f))
            tracks = {
                track.name
                for f in roms
                if Path(f).suffix.lower() in SHEET_SUFFIXES
                for track in sheet_tracks(here / f)
            }
            games.extend((system, here / name) for name in roms if name not in tracks)

    return games


def scan_library(rom_root, systems=None):
    """Returns {system: number of games}, most games first."""
    return dict(Counter(system for system, _ in list_library(rom_root, systems)).most_common())


def _organised(path, cache):
    entry = cache.get(path) if cache else None
    return bool(entry) and entry.get("outcome") == "organised"


def pending_games(rom_root, cache=None):
    """
    The games in rom_root that still need organising, as {file: [its track
    files]}. New games are dropped into their system folder (or anywhere in
    the ROM folder), so this lists:

    - games in a system folder that the cache hasn't recorded as organised,
      or that have changed since (without a cache, every game)
    - a .cue/.gdi whose track files sit next to it, which ES-DE and Steam
      would list as extra games
    - a disc of a multi-disc game the current layout stores behind a playlist
    - every ROM outside the system folders (loose, or in a folder of its own)
    - PS3 game folders the cache hasn't recorded as organised, wherever they are

    Nothing inside a folder that is one game (ES-DE's "Game.m3u/" folders and
    PS3 games) is listed, and hidden folders such as the .multifile store and
    files that aren't ROMs are left alone.
    """
    rom_root = Path(rom_root)
    pending = {}

    for dirpath, dirnames, filenames in os.walk(rom_root):
        here = Path(dirpath)
        relative = here.relative_to(rom_root).parts
        folder_system = relative[0] if relative and relative[0] in KNOWN_SYSTEMS else None

        visible = sorted(d for d in dirnames if not d.startswith("."))
        for name in visible:
            if is_ps3_folder(here / name) and not _organised(here / name, cache):
                pending[here / name] = []
        dirnames[:] = [d for d in visible if not is_game_folder(here / d)]

        names = sorted(f for f in filenames if not f.startswith(".") and is_rom_candidate(here / f))
        sheets = {
            here / name: sheet_tracks(here / name)
            for name in names
            if Path(name).suffix.lower() in SHEET_SUFFIXES
        }
        owned = {track for tracks in sheets.values() for track in tracks}

        for name in names:
            path = here / name
            if path in owned:
                continue
            tracks = sheets.get(path, [])
            # Track files ES-DE and Steam would list next to their sheet
            loose_tracks = any(track.parent == here for track in tracks)
            if (
                folder_system is None
                or not _organised(path, cache)
                or (loose_tracks and canonical_system(folder_system) not in ARCADE_FAMILY)
                or (get_disc_number(path.stem) and stores_multi_file_games_apart(folder_system))
            ):
                pending[path] = tracks

    return pending
