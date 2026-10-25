"""
List and count the games in a ROM library the way ES-DE lists them.
"""

import os
from collections import Counter
from pathlib import Path

from config import AMBIGUOUS_EXTENSIONS, DAT_SYSTEM_IDS, SYSTEM_MAP, SYSTEM_ROM_TYPES
from modules.archives import sheet_tracks
from modules.detection import detect_system

# Folders ES-DE launches as a single game ("Game.m3u/", "Game.cue/")
FOLDER_GAME_SUFFIXES = {".m3u", ".cue", ".gdi"}
KNOWN_SYSTEMS = set(SYSTEM_ROM_TYPES) | set(DAT_SYSTEM_IDS.values())


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
    Returns (games, undetected_file_names) for everything under rom_root, where
    games is a list of (system, path). A top-level folder named after a system
    (e.g. "snes") decides the system of everything in it; elsewhere the file
    itself is detected. Hidden folders, such as the .multifile store, are skipped.

    With systems, only games for those systems are listed and other system
    folders aren't walked. Undetected files are then left out, since they can't
    be tied to any system.
    """
    rom_root = Path(rom_root)
    systems = set(systems) if systems else None
    games = []
    undetected = []

    for dirpath, dirnames, filenames in os.walk(rom_root):
        here = Path(dirpath)
        relative = here.relative_to(rom_root).parts
        folder_system = relative[0] if relative and relative[0] in KNOWN_SYSTEMS else None

        # Hidden folders are skipped by ES-DE too
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        if systems and not relative:
            dirnames[:] = [d for d in dirnames if d not in KNOWN_SYSTEMS or d in systems]

        for folder_game in [d for d in dirnames if Path(d).suffix.lower() in FOLDER_GAME_SUFFIXES]:
            dirnames.remove(folder_game)
            system = folder_system or detect_system(here / folder_game / folder_game)
            if system:
                games.append((system, here / folder_game))
            elif not systems:
                undetected.append(folder_game)

        roms = sorted(f for f in filenames if not f.startswith(".") and _is_rom_candidate(f))
        tracks = {
            track.name
            for f in roms
            if Path(f).suffix.lower() in (".cue", ".gdi")
            for track in sheet_tracks(here / f)
        }

        for name in roms:
            if name in tracks:
                continue

            system = folder_system or detect_system(here / name)
            if system:
                games.append((system, here / name))
            elif not systems:
                undetected.append(name)

    if systems:
        games = [(system, path) for system, path in games if system in systems]
    return games, undetected


def scan_library(rom_root, systems=None):
    """Returns (games_by_system, undetected_file_names), most games first."""
    games, undetected = list_library(rom_root, systems)
    return dict(Counter(system for system, _ in games).most_common()), undetected
