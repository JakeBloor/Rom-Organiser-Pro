"""
Look inside ROM files without unpacking them: the single ROM in a .zip, the
header of a disc image, so files with shared extensions can be identified,
and the title of a PS3 game folder.
"""

import re
import struct
import zipfile
from pathlib import Path

# Files often bundled next to a ROM in a zip that don't count as the ROM
JUNK_SUFFIXES = {".txt", ".nfo", ".diz", ".url", ".htm", ".html", ".pdf"}

# Bytes read from the start of a disc image when sniffing it. PS1/PS2 discs
# keep SYSTEM.CNF near the start, so this also covers the BOOT/BOOT2 check.
SNIFF_BYTES = 4 * 1024 * 1024

ISO_PVD_OFFSET = 0x8000  # Primary volume descriptor, 2048-byte sectors
RAW_PVD_OFFSET = 16 * 2352 + 24  # Same descriptor in a raw 2352-byte .bin

# .cue: FILE "<name>" BINARY
CUE_FILE_REGEX = re.compile(r'^[ \t]*FILE[ \t]+(?:"([^"]+)"|(\S+))', re.IGNORECASE | re.MULTILINE)
# .gdi track lines: <number> <lba> <type> <sector size> <file> <offset>, the
# file optionally quoted. The first line is the track count, so matches must
# not run across lines.
GDI_TRACK_REGEX = re.compile(
    r'^[ \t]*\d+[ \t]+\d+[ \t]+\d+[ \t]+\d+[ \t]+(?:"([^"]+)"|(\S+))', re.MULTILINE
)


def zip_rom_member(path):
    """Name of the only ROM file inside a zip, or None (not a zip, or several files)."""
    try:
        with zipfile.ZipFile(path) as zf:
            members = [
                info.filename
                for info in zf.infolist()
                if not info.is_dir()
                and Path(info.filename).suffix.lower() not in JUNK_SUFFIXES
            ]
    except (OSError, zipfile.BadZipFile):
        return None

    return members[0] if len(members) == 1 else None


def sheet_tracks(sheet):
    """
    Track files a .cue or .gdi sheet points at that exist next to it, in sheet
    order. These have to stay in the same folder as the sheet.
    """
    try:
        text = Path(sheet).read_text(errors="ignore")
    except OSError:
        return []

    regex = GDI_TRACK_REGEX if Path(sheet).suffix.lower() == ".gdi" else CUE_FILE_REGEX
    names = [m.group(1) or m.group(2) for m in regex.finditer(text)]

    tracks = []
    for name in names:
        track = Path(sheet).parent / Path(name).name
        if track.is_file() and track not in tracks:
            tracks.append(track)

    return tracks


def _pvd_system_id(data, offset):
    if data[offset + 1 : offset + 6] != b"CD001":
        return ""
    # Padded with spaces on pressed discs, sometimes NULs on homebrew images
    return data[offset + 8 : offset + 40].decode("ascii", "ignore").strip(" \x00")


def sniff_disc_system(path):
    """
    Identify a disc image or Genesis .bin from its header bytes.

    Returns an ES-DE system ID, or None when the header isn't recognised.
    """
    try:
        with open(path, "rb") as f:
            data = f.read(SNIFF_BYTES)
    except OSError:
        return None

    # Nintendo disc magic words
    if data[0x1C:0x20] == bytes.fromhex("C2339F3D"):
        return "gc"
    if data[0x18:0x1C] == bytes.fromhex("5D1C9EA3"):
        return "wii"

    # Sega headers sit at 0 in a .iso and after the 16-byte sync header in a raw .bin
    head = data[:0x20]
    if b"SEGA SEGASATURN" in head:
        return "saturn"
    if b"SEGADISCSYSTEM" in head:
        return "segacd"
    if b"SEGA SEGAKATANA" in head:
        return "dreamcast"
    if data[0x100:0x104] in (b"SEGA", b" SEG"):
        return "genesis"

    system_id = _pvd_system_id(data, ISO_PVD_OFFSET) or _pvd_system_id(
        data, RAW_PVD_OFFSET
    )
    if system_id == "PSP GAME":
        return "psp"
    if system_id == "PLAYSTATION":
        # SYSTEM.CNF says BOOT2 on PS2 discs and BOOT on PS1 discs
        if re.search(rb"BOOT2\s*=", data):
            return "ps2"
        if re.search(rb"BOOT\s*=", data):
            return "psx"

    return None


# What's inside a PS3 game folder, however it's named
PS3_FOLDER_MARKERS = ("PS3_GAME", "PS3_DISC.SFB")


def is_ps3_folder(folder):
    """A PS3 game: a "Game.ps3" folder, or a disc or installed game folder."""
    folder = Path(folder)
    return folder.suffix.lower() == ".ps3" or any(
        (folder / marker).exists() for marker in PS3_FOLDER_MARKERS
    )


SFO_MAGIC = b"\0PSF"
SFO_HEADER = struct.Struct("<4sIIII")  # magic, version, key table, data table, entries
SFO_ENTRY = struct.Struct("<HHIII")  # key offset, format, length, max length, data offset


def sfo_title(sfo_path):
    """The TITLE in a PS3 PARAM.SFO (e.g. "Demon's Souls"), or None if it can't be read."""
    try:
        data = Path(sfo_path).read_bytes()
        magic, _, key_table, data_table, entries = SFO_HEADER.unpack_from(data)
        if magic != SFO_MAGIC:
            return None

        for index in range(entries):
            key_offset, _, length, _, data_offset = SFO_ENTRY.unpack_from(
                data, SFO_HEADER.size + index * SFO_ENTRY.size
            )
            key_start = key_table + key_offset
            key = data[key_start:data.index(b"\0", key_start)]
            if key == b"TITLE":
                value = data[data_table + data_offset:data_table + data_offset + length]
                return value.rstrip(b"\0").decode("utf-8", "replace").strip() or None
    except (OSError, struct.error, ValueError):
        return None

    return None


def ps3_title(folder):
    """A PS3 game folder's title from its PARAM.SFO, for disc and installed layouts."""
    for sfo in ("PS3_GAME/PARAM.SFO", "PARAM.SFO"):
        title = sfo_title(Path(folder) / sfo)
        if title:
            return title
    return None
