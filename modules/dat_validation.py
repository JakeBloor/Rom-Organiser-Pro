import re
import xml.etree.ElementTree as ET
from bisect import bisect_left
from config import DAT_DIR, DAT_SYSTEM_IDS, canonical_system
from modules.dat_fetcher import DATFetcher

# md5/sha1 (lowercase hex) -> (game name, ES-DE system or None, DAT title)
# The DAT title, e.g. "Nintendo - Game Boy", is also the game's libretro
# thumbnail folder.
DAT_DB = {}
# Game name key -> {ES-DE system: (game name, system, DAT title)}, for files
# whose checksum can't match: compressed images, renamed or patched dumps.
# Only DATs tied to a system are indexed, so a name match names its system.
DAT_NAMES = {}
# Serial key -> {ES-DE system: entry}, read from a disc's header so even
# compressed images match: "SLUS20312", "GW7E01", "BLUS30443"
DAT_SERIALS = {}
SERIAL_REGEX = re.compile(r'\bserial\s+"([^"]+)"', re.IGNORECASE)
# Redump's GameCube/Wii serials hold the 4-character game code: "DL-DOL-GW7E-USA"
NINTENDO_SERIAL_REGEX = re.compile(r"\b(?:DOL|RVL)-([A-Z0-9]{4})\b")

# DAT_NAMES' keys in order, for finding the releases that start with a name
DAT_NAME_KEYS = []
# Releases a plain name shouldn't stand for
UNRELEASED_REGEX = re.compile(
    r"\((?:beta|proto|prototype|demo|sample|kiosk|preview|taikenban|debug|alpha)\b[^)]*\)"
)
IGNORED_DAT_DIRS = {"dat", "metadat", "rdb"}

# Folders of DATs besides libretro's: FinalBurn Neo's (downloaded) and any
# you add yourself, such as TOSEC or MAME
FBNEO_DIR_NAME = "fbneo"
EXTRA_DIR_NAME = "extra"

# Which arcade folders FinalBurn Neo's DATs cover, and their libretro thumbnail folder
FBNEO_DAT_SYSTEMS = {
    "Arcade only": ("arcade", "fbneo", "mame"),
    "Neogeo only": ("neogeo", "arcade", "fbneo", "mame"),
}
ARCADE_THUMBNAILS = "FBNeo - Arcade Games"
# Arcade sets are named by zip ("sf2"); their DATs give the real title as a description
ARCADE_FAMILY = {"arcade", "fbneo", "mame", "neogeo"}

# TOSEC names DATs "<maker> <system> - <kind> - ...": the system part, and its folder
TOSEC_SYSTEMS = {
    "Commodore Amiga": "amiga",
    "Commodore C64": "c64",
    "Commodore VIC20": "vic20",
    "Commodore Plus-4": "plus4",
    "Atari ST": "atarist",
    "Atari 8bit": "atari800",
    "Amstrad CPC": "amstradcpc",
    "MSX MSX": "msx",
    "MSX MSX2": "msx",
    "Sinclair ZX Spectrum": "zxspectrum",
    "Sinclair ZX81": "zx81",
    "Sharp X68000": "x68000",
    "Sharp X1": "x1",
    "NEC PC-98": "pc98",
    "IBM PC Compatibles": "dos",
}

# Arcade DATs are named by emulator and version ("MAME 0.270.dat")
ARCADE_DAT_PREFIXES = {"MAME": "mame", "FinalBurn Neo": "fbneo", "FBNeo": "fbneo"}

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
    for name in METADAT_DAT_DIRS + (FBNEO_DIR_NAME, EXTRA_DIR_NAME):
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
    """
    ES-DE system for a DAT: "Nintendo - Wii (Digital).dat" -> "wii", or by
    TOSEC's naming, "Commodore Amiga - Games - [ADF] (TOSEC-...).dat" -> "amiga".
    """
    return (
        DAT_SYSTEMS_BY_NAME.get(dat_path.stem.lower())
        or DAT_SYSTEMS_BY_NAME.get(dat_title(dat_path).lower())
        or TOSEC_SYSTEMS.get(dat_path.stem.split(" - ")[0])
        or next(
            (system for prefix, system in ARCADE_DAT_PREFIXES.items()
             if dat_path.stem.startswith(prefix + " ")),
            None,
        )
    )


def name_key(name):
    """Game names compared ignoring case, underscores and repeated spaces."""
    return " ".join(name.replace("_", " ").lower().split())


def _add_name(entry, key_name=None):
    """Indexes entry by its game name, or by key_name (an arcade set's zip name)."""
    name, system, _ = entry
    name = key_name or name
    if name and system:
        # Later DATs win, as for checksums: No-Intro and Redump load after libretro's own
        DAT_NAMES.setdefault(name_key(name), {})[system] = entry


def serial_key(serial):
    return re.sub(r"[^A-Z0-9]", "", serial.upper())


def _add_serials(entry, text):
    for field in SERIAL_REGEX.findall(text):
        for serial in re.split(r"[,;]", field):
            keys = {serial_key(serial)} | set(NINTENDO_SERIAL_REGEX.findall(serial.upper()))
            for key in keys - {""}:
                DAT_SERIALS.setdefault(key, {})[entry[1]] = entry


def lookup_serial(serial, system=None):
    """
    (game name, system, DAT title) for a disc serial such as "SLUS20312" or
    a GameCube/Wii game ID such as "GW7E69" (also tried as its 4-character
    code). Same system rules as lookup_name. Else (None, None, None).
    """
    key = serial_key(serial)
    for candidate in (key, key[:4] if len(key) == 6 else None):
        found = candidate and _entry_for(DAT_SERIALS.get(candidate, {}), system)
        if found:
            return found
    return None, None, None


def lookup_name(name, system=None):
    """
    (game name, system, DAT title) for a game named like a DAT entry, e.g.
    "Chrono Trigger (USA)". With system, only that system's entry counts;
    without, the name must belong to just one system. Else (None, None, None).
    """
    key = name_key(name)
    found = _entry_for(DAT_NAMES.get(key, {}), system) or _release_of(key, system)
    return found or (None, None, None)


def _entry_for(by_system, system):
    if system:
        return by_system.get(system)
    if len(by_system) == 1:
        return next(iter(by_system.values()))
    return None


def _release_of(key, system):
    """
    The DAT entry a plain name stands for when the DAT only lists it with
    more tags, e.g. "Gran Turismo 4 (USA)" -> "Gran Turismo 4 (USA) (v2.00)":
    the last released version, leaving out betas, demos and the like.
    """
    prefix = key + " ("
    index = bisect_left(DAT_NAME_KEYS, prefix)
    found = None
    while index < len(DAT_NAME_KEYS) and DAT_NAME_KEYS[index].startswith(prefix):
        candidate = DAT_NAME_KEYS[index]
        entry = _entry_for(DAT_NAMES[candidate], system)
        if entry and not UNRELEASED_REGEX.search(candidate[len(key):]):
            found = entry
        index += 1
    return found


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

    yield from _sorted_dats(DAT_DIR / FBNEO_DIR_NAME)
    yield from _sorted_dats(DAT_DIR / EXTRA_DIR_NAME)


def _load_clrmamepro_dat(dat, logger, system, title):
    try:
        text = dat.read_text(errors="ignore")
        entries = 0
        names = 0

        starts = [m.end() for m in GAME_BLOCK_REGEX.finditer(text)]

        for start, end in zip(starts, starts[1:] + [len(text)]):
            game_block = text[start:end]
            name_match = re.search(r'name\s+"([^"]+)"', game_block)
            if not name_match:
                continue

            entry = (name_match.group(1), system, title)
            if system:
                _add_name(entry)
                _add_serials(entry, game_block)
                names += 1

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
        if names:
            # e.g. libretro's GameCube and Wii DATs list serials, not checksums
            logger(f"[DAT] Loaded {names} game names from {dat.name} (no checksums)")
            return True

    except OSError as e:
        logger(f"[DAT ERROR] {dat.name} clrmamepro parse failed: {e}", "ERROR")

    return False


def _dat_targets(dat):
    """
    The systems a DAT's games are indexed for, and its libretro thumbnail
    folder: FinalBurn Neo's cover every arcade folder; a TOSEC DAT has no
    thumbnail folder, since libretro's thumbnails use other names.
    """
    collection = _dat_collection(dat)
    if collection == FBNEO_DIR_NAME:
        marker = next((m for m in FBNEO_DAT_SYSTEMS if m in dat.name), None)
        return (FBNEO_DAT_SYSTEMS[marker] if marker else (None,)), ARCADE_THUMBNAILS

    system = dat_system(dat)
    title = dat_title(dat)
    if collection == EXTRA_DIR_NAME and title.lower() not in DAT_SYSTEMS_BY_NAME:
        title = None
    return (system,), title


def load_dat_files(logger):
    DAT_DB.clear()
    DAT_NAMES.clear()
    DAT_NAME_KEYS.clear()
    DAT_SERIALS.clear()

    # No-Intro and libretro both ship e.g. "Nintendo - Super Nintendo
    # Entertainment System.dat", so names only need to be unique per collection
    seen = set()

    for dat in _iter_dat_files():
        key = (_dat_collection(dat), dat.name)
        if key in seen:
            continue

        seen.add(key)
        systems, title = _dat_targets(dat)
        system = systems[0]

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
        games = 0
        root = tree.getroot()
        arcade = any(canonical_system(s) in ARCADE_FAMILY for s in systems if s)

        for game in root.findall(".//game") + root.findall(".//machine"):
            name = game.attrib.get("name")
            # Arcade sets go by zip name; the description is the game's real title
            title_name = (game.findtext("description") or name) if arcade else name
            for each in systems:
                _add_name((title_name, each, title), key_name=name)

            entry = (title_name, system, title)
            for rom in game.findall("rom"):
                _add_rom(entry, rom.attrib.get("md5"), rom.attrib.get("sha1"))
                count += 1
            games += 1

        logger(f"[DAT] Loaded {count} entries from {dat.name} ({games} games)")

    DAT_NAME_KEYS.extend(sorted(DAT_NAMES))


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
    # Arcade zip names and titles; their absence only affects arcade games
    fetcher.fetch_fbneo_dats()

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
