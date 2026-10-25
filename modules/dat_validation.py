import re
import xml.etree.ElementTree as ET
from config import DAT_DIR, DAT_SYSTEM_IDS
from modules.dat_fetcher import DATFetcher

# md5/sha1 (lowercase hex) -> (game name, ES-DE system or None, DAT title)
# The DAT title, e.g. "Nintendo - Game Boy", is also the game's libretro
# thumbnail folder.
DAT_DB = {}
IGNORED_DAT_DIRS = {"dat", "metadat", "rdb"}

# libretro-database keeps the No-Intro and Redump DATs (the ones with hashes for
# mainstream systems) under metadat/, so these are loaded alongside dat/
METADAT_DAT_DIRS = ("no-intro", "redump")

# Top-level game blocks start at the beginning of a line
GAME_BLOCK_REGEX = re.compile(r"^\s*game\s*\(", re.IGNORECASE | re.MULTILINE)
# Quoted strings are matched whole so a ")" inside a ROM name such as
# "Game (Japan).nes" doesn't end the rom ( ... ) block early
ROM_BLOCK_REGEX = re.compile(r'\brom\s*\(((?:[^()"]|"[^"]*")*)\)', re.IGNORECASE)


def _is_ignored_dat_path(dat_path):
    relative_parts = dat_path.relative_to(DAT_DIR).parts
    return any(part.lower() in IGNORED_DAT_DIRS for part in relative_parts)


def _dat_collection(dat_path):
    parts = [part.lower() for part in dat_path.parts]
    for name in METADAT_DAT_DIRS:
        if name in parts:
            return name
    return "dat"


def _sorted_dats(root):
    if not root.exists():
        return []

    return sorted(
        root.rglob("*.dat"),
        key=lambda p: (
            len(p.relative_to(root).parts),
            p.relative_to(root).as_posix(),
        ),
    )


DAT_SYSTEMS_BY_NAME = {name.lower(): system for name, system in DAT_SYSTEM_IDS.items()}


def dat_title(dat_path):
    """"Nintendo - Wii (Digital).dat" -> "Nintendo - Wii"."""
    return re.sub(r"\s*\([^)]*\)$", "", dat_path.stem)


def dat_system(dat_path):
    """ES-DE system for a DAT, e.g. "Nintendo - Wii (Digital).dat" -> "wii"."""
    return DAT_SYSTEMS_BY_NAME.get(dat_path.stem.lower()) or DAT_SYSTEMS_BY_NAME.get(
        dat_title(dat_path).lower()
    )


def _add_rom(entry, md5, sha1):
    # CRCs aren't stored: lookups only use md5/sha1, and CRC32 collides too
    # easily across a million entries to identify a game on its own
    if md5:
        DAT_DB[md5.lower()] = entry
    if sha1:
        DAT_DB[sha1.lower()] = entry


def _iter_dat_files():
    libretro_dir = DAT_DIR / "libretro"

    if libretro_dir.exists() and any(libretro_dir.rglob("*.dat")):
        yield from _sorted_dats(libretro_dir)
    else:
        for dat in _sorted_dats(DAT_DIR):
            if not _is_ignored_dat_path(dat):
                yield dat

    for name in METADAT_DAT_DIRS:
        yield from _sorted_dats(DAT_DIR / "metadat" / name)


def _load_clrmamepro_dat(dat, logger, system, title):
    try:
        text = dat.read_text(errors="ignore")
        entries = 0

        starts = [m.end() for m in GAME_BLOCK_REGEX.finditer(text)]

        for start, end in zip(starts, starts[1:] + [len(text)]):
            game_block = text[start:end]
            name_match = re.search(r'name\s+"([^"]+)"', game_block)
            if not name_match:
                continue

            entry = (name_match.group(1), system, title)

            for rom_match in ROM_BLOCK_REGEX.finditer(game_block):
                rom_block = rom_match.group(1)
                md5_match = re.search(r"\bmd5\s+([0-9A-Fa-f]+)", rom_block)
                sha1_match = re.search(r"\bsha1\s+([0-9A-Fa-f]+)", rom_block)
                crc_match = re.search(r"\bcrc\s+([0-9A-Fa-f]+)", rom_block)

                if not (md5_match or sha1_match or crc_match):
                    continue

                _add_rom(
                    entry,
                    md5_match and md5_match.group(1),
                    sha1_match and sha1_match.group(1),
                )

                entries += 1

        if entries:
            logger(f"[DAT] Loaded {entries} entries from {dat.name} (clrmamepro)")
            return True

    except OSError as e:
        logger(f"[DAT ERROR] {dat.name} clrmamepro parse failed: {e}", "ERROR")

    return False


def load_dat_files(logger):
    DAT_DB.clear()

    # No-Intro and libretro both ship e.g. "Nintendo - Super Nintendo
    # Entertainment System.dat", so names only need to be unique per collection
    seen = set()

    for dat in _iter_dat_files():
        key = (_dat_collection(dat), dat.name)
        if key in seen:
            continue

        seen.add(key)
        system = dat_system(dat)
        title = dat_title(dat)

        try:
            tree = ET.parse(dat)
        except (ET.ParseError, OSError):
            # Not XML: most libretro DATs are in clrmamepro format
            if not _load_clrmamepro_dat(dat, logger, system, title):
                logger(
                    f"[DAT WARN] Skipped unsupported or invalid DAT: {dat.name}", "WARNING"
                )
            continue

        count = 0

        for game in tree.getroot().findall(".//game"):
            entry = (game.attrib.get("name"), system, title)

            for rom in game.findall("rom"):
                _add_rom(entry, rom.attrib.get("md5"), rom.attrib.get("sha1"))
                count += 1

        logger(f"[DAT] Loaded {count} entries from {dat.name}")


def fetch_latest_dats(logger):
    """
    Fetch the libretro-database DATs. Callers load them with load_dat_files.

    DAT-o-MATIC and Redump only offer downloads through their websites, so if
    libretro can't be reached the user is pointed at those instead.

    Args:
        logger: Logger instance

    Returns:
        dict: {"libretro": bool} fetch result
    """
    fetcher = DATFetcher(logger)

    # fetch_libretro_dats logs and swallows its own errors
    logger("Attempting to fetch DATs from libretro database...", "INFO")
    if fetcher.fetch_libretro_dats().get("libretro"):
        logger("Successfully fetched DATs from libretro repository.", "SUCCESS")
        return {"libretro": True}
    logger("Libretro fetch returned no DATs.", "WARNING")

    logger(
        "No new DATs downloaded; any DATs already on disk will still be used.",
        "WARNING",
    )
    logger(
        "To add DATs manually, download them from https://datomatic.no-intro.org "
        "(cartridge systems) or http://redump.org/downloads/ (disc systems) and put "
        f"them in {DAT_DIR / 'metadat' / 'no-intro'} or {DAT_DIR / 'metadat' / 'redump'}.",
        "WARNING",
    )
    return {"libretro": False}


def lookup_hashes(hashes):
    """
    Return (game name, system, DAT title) for the first hash found in the
    DATs, else (None, None, None).
    """
    for h in hashes.values():
        if h.lower() in DAT_DB:
            return DAT_DB[h.lower()]

    return None, None, None


def validate_hashes(hashes):
    return lookup_hashes(hashes)[0]
