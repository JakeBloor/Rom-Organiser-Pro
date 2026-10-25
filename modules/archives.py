"""
Look inside ROM files without unpacking them: the single ROM in a .zip, the
header of a disc image, so files with shared extensions can be identified,
and the title of a PS3 game folder.
"""

import os
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


def _sheet_regex(sheet):
    return GDI_TRACK_REGEX if Path(sheet).suffix.lower() == ".gdi" else CUE_FILE_REGEX


def _resolve_track(folder, name):
    """
    The file a sheet's track name means: the path as written (it may lead
    into another folder), else that name next to the sheet, in any
    capitalisation, since sheets made on Windows rarely match a Linux SD card.
    """
    name = name.replace("\\", "/")
    for candidate in (Path(os.path.normpath(folder / name)), folder / Path(name).name):
        found = _named_as_on_disk(candidate)
        if found:
            return found
    return None


def _named_as_on_disk(path):
    """
    path as it's actually spelled on disk, matching capitals loosely, or None.
    macOS would also open a wrongly capitalised name, so the folder is read
    to get the real one: two spellings of one file must not look like two files.
    """
    try:
        entries = sorted(path.parent.iterdir())
    except OSError:
        return None
    exact = next((entry for entry in entries if entry.name == path.name), None)
    loose = exact or next((entry for entry in entries if entry.name.lower() == path.name.lower()), None)
    return loose if loose and loose.is_file() else None


def sheet_tracks(sheet):
    """Track files a .cue or .gdi sheet points at that exist, in sheet order."""
    sheet = Path(sheet)
    try:
        text = sheet.read_text(errors="ignore")
    except OSError:
        return []

    tracks = []
    for match in _sheet_regex(sheet).finditer(text):
        track = _resolve_track(sheet.parent, match.group(1) or match.group(2))
        if track and track not in tracks:
            tracks.append(track)

    return tracks


def rewrite_sheet(sheet, moved):
    """
    Points a sheet's track lines at their new places. moved maps each track's
    file name (in any capitalisation) to its new path; paths are written
    relative to the sheet.
    """
    sheet = Path(sheet)
    text = sheet.read_text(errors="ignore")
    gdi = sheet.suffix.lower() == ".gdi"
    moved = {name.lower(): path for name, path in moved.items()}

    def replace(match):
        group = 1 if match.group(1) is not None else 2
        new = moved.get(Path(match.group(group).replace("\\", "/")).name.lower())
        if new is None:
            return match.group(0)
        relative = Path(os.path.relpath(new, sheet.parent)).as_posix()
        quoted = f'"{relative}"' if not gdi or " " in relative else relative
        # Replace the name together with its quotes, if it had them
        start, end = match.span(group)
        if group == 1:
            start, end = start - 1, end + 1
        whole, offset = match.group(0), match.start()
        return whole[:start - offset] + quoted + whole[end - offset:]

    sheet.write_text(_sheet_regex(sheet).sub(replace, text))


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


def sfo_values(data):
    """The text values in a PARAM.SFO's bytes, e.g. {"TITLE": ..., "TITLE_ID": ...}."""
    try:
        magic, _, key_table, data_table, entries = SFO_HEADER.unpack_from(data)
        if magic != SFO_MAGIC:
            return {}

        values = {}
        for index in range(entries):
            key_offset, _, length, _, data_offset = SFO_ENTRY.unpack_from(
                data, SFO_HEADER.size + index * SFO_ENTRY.size
            )
            key_start = key_table + key_offset
            key = data[key_start:data.index(b"\0", key_start)].decode("ascii", "replace")
            value = data[data_table + data_offset:data_table + data_offset + length]
            values[key] = value.rstrip(b"\0").decode("utf-8", "replace").strip()
        return values
    except (struct.error, ValueError):
        return {}


def sfo_title(sfo_path):
    """The TITLE in a PS3 PARAM.SFO (e.g. "Demon's Souls"), or None if it can't be read."""
    try:
        data = Path(sfo_path).read_bytes()
    except OSError:
        return None
    return sfo_values(data).get("TITLE") or None


def ps3_title(folder):
    """A PS3 game folder's title from its PARAM.SFO, for disc and installed layouts."""
    for sfo in ("PS3_GAME/PARAM.SFO", "PARAM.SFO"):
        title = sfo_title(Path(folder) / sfo)
        if title:
            return title
    return None


def ps3_serial(folder):
    """A PS3 game folder's serial (TITLE_ID, e.g. "BLUS30443") from its PARAM.SFO."""
    for sfo in ("PS3_GAME/PARAM.SFO", "PARAM.SFO"):
        try:
            serial = sfo_values((Path(folder) / sfo).read_bytes()).get("TITLE_ID")
        except OSError:
            continue
        if serial:
            return serial
    return None


# Where a GameCube or Wii disc's 6-character game ID sits in each format
NINTENDO_ID_OFFSETS = {
    ".iso": 0, ".gcm": 0, ".ciso": 0x8000, ".wbfs": 0x200, ".rvz": 0x58, ".wia": 0x58,
}
NINTENDO_DISC_MAGIC = ((0x1C, bytes.fromhex("C2339F3D")), (0x18, bytes.fromhex("5D1C9EA3")))
# PS1/PS2 discs name their boot file in SYSTEM.CNF, e.g. "BOOT2 = cdrom0:\\SLUS_203.12;1"
PLAYSTATION_BOOT_REGEX = re.compile(rb"BOOT2?\s*=\s*cdrom0?:\\?([A-Z]{4})[_-](\d{3})\.(\d{2})")
# PSP discs start UMD_DATA.BIN with their serial, e.g. "ULUS-10041|..."
PSP_UMD_REGEX = re.compile(rb"\b(U[CL][A-Z]{2})-(\d{5})\|")
# How far into a disc image to look for SYSTEM.CNF or UMD_DATA.BIN
SERIAL_SEARCH_BYTES = 16 * 1024 * 1024
PBP_MAGIC = b"\0PBP"


def _nintendo_id(path, offset):
    with open(path, "rb") as f:
        f.seek(offset)
        header = f.read(0x20)
    disc_id = header[:6]
    has_magic = any(header[at:at + 4] == magic for at, magic in NINTENDO_DISC_MAGIC)
    if has_magic and disc_id.isalnum():
        return disc_id.decode("ascii")
    return None


def _playstation_serial(path):
    with open(path, "rb") as f:
        data = f.read(SERIAL_SEARCH_BYTES)
    boot = PLAYSTATION_BOOT_REGEX.search(data)
    if boot:
        return (boot.group(1) + boot.group(2) + boot.group(3)).decode("ascii")
    umd = PSP_UMD_REGEX.search(data)
    if umd:
        return (umd.group(1) + umd.group(2)).decode("ascii")
    return None


def _pbp_serial(path):
    """A PSP or PS1 EBOOT.PBP's DISC_ID, from the PARAM.SFO at its start."""
    with open(path, "rb") as f:
        header = f.read(0x28)
        if header[:4] != PBP_MAGIC:
            return None
        sfo_start, icon_start = struct.unpack_from("<II", header, 0x08)
        f.seek(sfo_start)
        sfo = f.read(max(0, icon_start - sfo_start))
    return sfo_values(sfo).get("DISC_ID") or None


def disc_serial(path):
    """
    A disc game's serial, read from just its header, so it works on large and
    compressed images: the game ID of a GameCube or Wii disc (.iso, .gcm,
    .ciso, .wbfs, .rvz, .wia), the boot file of a PS1/PS2 image, a PSP
    disc's UMD_DATA.BIN, or a .pbp's PARAM.SFO. None if there isn't one.
    """
    path = Path(path)
    suffix = path.suffix.lower()
    try:
        if suffix == ".pbp":
            return _pbp_serial(path)
        if suffix in NINTENDO_ID_OFFSETS:
            found = _nintendo_id(path, NINTENDO_ID_OFFSETS[suffix])
            if found or suffix != ".iso":
                return found
        if suffix in (".iso", ".bin", ".img"):
            return _playstation_serial(path)
    except (OSError, struct.error):
        return None
    return None
