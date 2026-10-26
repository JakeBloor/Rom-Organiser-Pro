"""
EmuMovies artwork packs, kept as a local artwork library.

EmuMovies only offers artwork as whole-system packs ("Sony Playstation
(Boxes-2D)(ReDump)(EM 2.2).part1.rar" ...). For each system in the ROM
folder, the newest official pack of each art type ES-DE uses is downloaded,
unpacked into <library>/<system>/<media type>/, and the downloaded parts are
deleted. Only those local copies are ever deleted: the connection to
EmuMovies is read-only. manifest.json records which pack each folder came
from, so a pack is only downloaded again when EmuMovies publishes a newer one.

Organise runs then copy each game's images out of the library.
"""

import ftplib
import json
import os
import re
import shutil
import time
from pathlib import Path

from config import canonical_system
from modules import esde, settings
from modules.emumovies import OFFICIAL, match_file, set_system_name, system_names
from modules.library import system_folders
from modules.media import IMAGE_SUFFIXES
from modules.organizer import sort_by_priority
from modules.unpack import UnpackError, unpack

ARTWORK = "Artwork"
PART_REGEX = re.compile(r"\.(?:part\d+\.rar|rar|7z(?:\.\d+)?|zip)$", re.IGNORECASE)
PART_NUMBER_REGEX = re.compile(r"\.part(\d+)\.rar$|\.7z\.(\d+)$", re.IGNORECASE)
EM_VERSION_REGEX = re.compile(r"\(EM (\d+(?:\.\d+)*)\)")
# Versions this big are dates ("EM 20160611"), from EmuMovies' older packs
DATE_VERSION = 10000

# A pack's art type, from its first bracket: "(Boxes-2D)", "(2D Boxes)" ...
# Spines, textures, labels, 2.5D, banners and custom marquees aren't used.
PACK_KINDS = (
    (re.compile(r"^(?:boxes-2d|2d boxes)$", re.I), "covers"),
    (re.compile(r"^(?:boxes-3d|3d boxes)$", re.I), "3dboxes"),
    (re.compile(r"^(?:boxes-back|2d boxes-back)$", re.I), "backcovers"),
    (re.compile(r"^(?:snaps-gameplay|gameplay snaps)$", re.I), "screenshots"),
    (re.compile(r"^(?:snaps-title|title snaps)$", re.I), "titlescreens"),
    (re.compile(r"^(?:logos-game|logos|game logos)$", re.I), "marquees"),
    (re.compile(r"^(?:game media-2d|2d carts|discs|2d discs)$", re.I), "physicalmedia"),
    (re.compile(r"^(?:backgrounds-game|backgrounds)$", re.I), "fanart"),
)


def library_root():
    """Where unpacked packs live: set in Settings, else next to ES-DE's media folder."""
    return settings.path("emumovies_artwork_dir") or esde.media_root().parent / "emumovies-artwork"


def pack_name(filename):
    """"Sony Playstation (Boxes-2D)(ReDump)(EM 2.2).part1.rar" -> its pack name, without the part."""
    return PART_REGEX.sub("", filename)


def pack_type(name):
    """The ES-DE media type a pack holds, or None for art types that aren't used."""
    kind = re.search(r"\(([^)]*)\)", name)
    if not kind:
        return None
    return next((media_type for regex, media_type in PACK_KINDS if regex.match(kind.group(1).strip())), None)


def _part_number(filename):
    found = PART_NUMBER_REGEX.search(filename)
    return int(next(group for group in found.groups() if group)) if found else 0


def _rank(name):
    """Sorts packs best first: official EmuMovies packs, for the whole system, newest."""
    version = EM_VERSION_REGEX.search(name)
    numbers = tuple(int(n) for n in version.group(1).split(".")) if version else ()
    if numbers and numbers[0] >= DATE_VERSION:
        numbers = ()
    regional = " - " in name.split("(", 1)[0]
    # Packs without a usable version number come after every numbered one
    return (version is None, regional, not numbers, tuple(-n for n in numbers), name)


def choose_packs(filenames):
    """
    {media type: (pack name, [part file names in order])}: the best pack of
    each art type ES-DE uses, among a system's artwork files.
    """
    packs = {}
    for filename in filenames:
        packs.setdefault(pack_name(filename), []).append(filename)

    chosen = {}
    for name in sorted(packs, key=_rank):
        media_type = pack_type(name)
        if media_type and media_type not in chosen:
            chosen[media_type] = (name, sorted(packs[name], key=_part_number))
    return chosen


class ArtworkLibrary:
    """Unpacked packs: <root>/<system>/<media type>/<image>, and manifest.json naming each folder's pack."""

    def __init__(self, root):
        self.root = Path(root)
        self.manifest_path = self.root / "manifest.json"
        self._files = {}
        try:
            self.manifest = json.loads(self.manifest_path.read_text())
        except (OSError, ValueError):
            self.manifest = {}

    def pack_for(self, system, media_type):
        return self.manifest.get(f"{system}/{media_type}", {}).get("pack")

    def record(self, system, media_type, pack, files):
        self.manifest[f"{system}/{media_type}"] = {"pack": pack, "files": files, "unpacked": time.time()}
        self.root.mkdir(parents=True, exist_ok=True)
        self.manifest_path.write_text(json.dumps(self.manifest, indent=2))
        self._files.pop((system, media_type), None)

    def folder(self, system, media_type):
        return self.root / canonical_system(system) / media_type

    def find(self, game, media_type):
        """The library image for game, or None."""
        key = (canonical_system(game["system"]), media_type)
        if key not in self._files:
            folder = self.folder(*key)
            self._files[key] = sorted(p.name for p in folder.iterdir()) if folder.is_dir() else []
        found = match_file(self._files[key], game)
        return self.folder(*key) / found if found else None


def _artwork_folder(server, system):
    wanted = system_names(system)
    return next(
        (f"{OFFICIAL}/{ARTWORK}/{name}" for name in server.listing(f"{OFFICIAL}/{ARTWORK}")
         if set_system_name(name) in wanted),
        None,
    )


def _is_image(path):
    return path.suffix.lower() in IMAGE_SUFFIXES


def _install_pack(server, library, system, media_type, folder, name, parts, progress):
    """Downloads a pack's parts, unpacks its images into the library, then deletes the parts."""
    downloads = library.root / ".downloads" / name
    staging = library.root / ".unpacking" / system / media_type
    shutil.rmtree(downloads, ignore_errors=True)
    shutil.rmtree(staging, ignore_errors=True)
    downloads.mkdir(parents=True)
    try:
        for index, part in enumerate(parts, start=1):
            remote = f"{folder}/{part}"
            total = server.ftp.size(remote) or 1
            done = 0

            def on_bytes(count, index=index):
                nonlocal done
                done += count
                progress(f"{name}: part {index} of {len(parts)}, {done / 1e6:.0f} of {total / 1e6:.0f} MB")

            server.download(remote, downloads / part, on_bytes)

        progress(f"{name}: unpacking")
        unpack([downloads / part for part in parts], staging, keep=_is_image)

        # The images are kept flat, as ES-DE names them, whatever folders the pack used
        flat = staging.with_name(staging.name + ".flat")
        shutil.rmtree(flat, ignore_errors=True)
        flat.mkdir(parents=True)
        for image in staging.rglob("*"):
            if image.is_file():
                os.replace(image, flat / image.name)
        final = library.folder(system, media_type)
        shutil.rmtree(final, ignore_errors=True)
        final.parent.mkdir(parents=True, exist_ok=True)
        os.replace(flat, final)
        return sum(1 for _ in final.iterdir())
    finally:
        # Only the local downloads and staging folders are deleted, never anything on EmuMovies
        shutil.rmtree(downloads, ignore_errors=True)
        shutil.rmtree(staging, ignore_errors=True)


def download_packs(server, rom_root, library, logger, progress=lambda detail: None, should_stop=lambda: False):
    """
    For each system in the ROM folder, downloads and unpacks the art packs
    the library doesn't have yet (or has an older version of). Returns
    {"installed": n, "up_to_date": n, "failed": n}.
    """
    summary = {"installed": 0, "up_to_date": 0, "failed": 0}
    systems = sort_by_priority({canonical_system(s) for s in system_folders(rom_root)})
    try:
        _download_systems(server, systems, library, logger, progress, should_stop, summary)
    finally:
        # Local working folders only; nothing on EmuMovies is touched
        for working in (".downloads", ".unpacking"):
            shutil.rmtree(library.root / working, ignore_errors=True)
    return summary


def _download_systems(server, systems, library, logger, progress, should_stop, summary):
    for system in systems:
        folder = _artwork_folder(server, system)
        if not folder:
            logger(f"[EMUMOVIES] {system} · No artwork packs on EmuMovies")
            continue

        for media_type, (name, parts) in choose_packs(server.listing(folder)).items():
            if should_stop():
                return
            if library.pack_for(system, media_type) == name:
                summary["up_to_date"] += 1
                continue
            try:
                count = _install_pack(server, library, system, media_type, folder, name, parts, progress)
            except (OSError, UnpackError, ftplib.Error) as e:
                logger(f"[EMUMOVIES ERROR] {system} · {media_type} · {name}: {e}", "WARNING")
                summary["failed"] += 1
                continue
            library.record(system, media_type, name, count)
            logger(f"[EMUMOVIES] {system} · {media_type} · {count} images from {name}")
            summary["installed"] += 1
