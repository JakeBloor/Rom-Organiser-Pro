import re
from pathlib import Path
from config import SYSTEM_MAP, SYSTEM_PRIORITY, AMBIGUOUS_EXTENSIONS, SYSTEM_ROM_TYPES
from modules.archives import sniff_disc_system, zip_rom_member

DISC_REGEX = re.compile(r"(disc|disk|cd)[\s_-]*(\d+)", re.I)

# Extensions whose header can be sniffed when the folder doesn't say the system
SNIFFABLE_DISC_SUFFIXES = {".iso", ".bin", ".img"}

# ========= FOLDER HEURISTICS =========
# Used to disambiguate systems when extensions are shared
FOLDER_HINTS = {
    "ps2": ["ps2", "playstation2", "playstation 2"],
    "psx": ["psx", "playstation1", "playstation", "ps1", "ps-1"],
    "ps3": ["ps3", "playstation3", "playstation 3"],
    "ps4": ["ps4", "playstation4", "playstation 4"],
    "ps5": ["ps5", "playstation5", "playstation 5"],
    "psp": ["psp", "playstationportable", "playstation portable"],
    "saturn": ["saturn", "sega saturn"],
    "segacd": ["segacd", "sega cd"],
    "dreamcast": ["dreamcast", "dc", "sega dc"],
    "xboxone": ["xboxone", "xbox one"],
    "xboxseriesx": ["xboxseriesx", "xbox series x", "xbox series", "xboxseries"],
    "atarijaguarcd": ["atarijaguarcd", "jaguarcd", "jaguar cd"],
    "dos": ["dos", "msdos"],
    "gc": ["gamecube", "gc"],
    "wii": ["wii"],
    "wiiu": ["wiiu", "wii u"],
    "xbox360": ["xbox360", "xbox 360"],
    "switch": ["switch", "nintendo switch"],
    "mame": ["mame"],
    "fbneo": ["fbneo", "neo geo", "neogeo"],
    "pcenginecd": ["pcenginecd", "tg16cd", "turbografxcd"],
    "genesis": ["genesis", "megadrive"],
}

ARCADE_SYSTEM_KEYWORDS = {
    "fbneo": ["fbneo", "neo geo", "neogeo"],
    "mame": ["mame"],
    "arcade": ["arcade"],
}


def clean_name(name):
    name = DISC_REGEX.sub("", name)
    name = re.sub(r"\(.*?\)|\[.*?\]", "", name)
    name = re.sub(r"\s+", " ", name)
    return name.strip()


def get_disc_number(name):
    m = DISC_REGEX.search(name)
    return int(m.group(2)) if m else None


def _normalise(name):
    """Lowercase and drop separators, so "PlayStation 2" matches "playstation2"."""
    return re.sub(r"[^a-z0-9]", "", name.lower())


NORMALISED_FOLDER_HINTS = {
    system: {_normalise(hint) for hint in hints} for system, hints in FOLDER_HINTS.items()
}
NORMALISED_ARCADE_KEYWORDS = {
    system: {_normalise(keyword) for keyword in keywords}
    for system, keywords in ARCADE_SYSTEM_KEYWORDS.items()
}


def _folder_names(file_path):
    """Normalised parent folder names, nearest folder first."""
    names = (_normalise(part) for part in reversed(file_path.parent.parts))
    return [name for name in names if name]


def _accepts(system, suffix):
    """True if suffix is a ROM type for system (systems without a type list accept anything)."""
    return system not in SYSTEM_ROM_TYPES or suffix in SYSTEM_ROM_TYPES[system]


def detect_arcade(path):
    path = Path(path)
    suffix = path.suffix.lower()

    for folder in _folder_names(path):
        for system, keywords in NORMALISED_ARCADE_KEYWORDS.items():
            if folder not in keywords:
                continue
            # e.g. a .chd in an "arcade" folder goes to the first arcade
            # system that supports CHDs
            for arcade_system in [system, *NORMALISED_ARCADE_KEYWORDS]:
                if _accepts(arcade_system, suffix):
                    return arcade_system

    return None


def detect_system(file_path, allow_guess=True):
    """
    Detect system from file path using multiple strategies:
    1. Arcade detection by folder name
    2. Extension mapping, validated against SYSTEM_ROM_TYPES
    3. For ambiguous extensions: folder names (nearest first), matched whole
       against FOLDER_HINTS and system IDs
    4. For files that exist: the single ROM inside a .zip, or the header of a
       disc image
    5. SYSTEM_PRIORITY for disambiguation (skipped when allow_guess is False,
       so callers that move files never act on a guess)

    Folder names are compared whole (after normalising case and separators), so
    "snes" never matches "nes" and "gba" never matches "gb".

    Args:
        file_path: Path object or string representing the file
        allow_guess: Fall back to SYSTEM_PRIORITY when nothing else decides

    Returns:
        System ID string (e.g., "ps2", "psx"), or None if not found
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    # Skip non-file entries
    if not suffix:
        return None

    # Arcade detection by folder name
    arcade = detect_arcade(file_path)
    if arcade:
        return arcade

    # Check if this is an ambiguous extension
    if suffix in AMBIGUOUS_EXTENSIONS:
        candidates = AMBIGUOUS_EXTENSIONS[suffix]
    else:
        # Get system from regular SYSTEM_MAP
        sys = SYSTEM_MAP.get(suffix)
        if sys and _accepts(sys, suffix):
            return sys
        return None

    # Multiple candidates - check folder names across ALL known systems, nearest
    # folder first. Archives (zip/7z) and other ambiguous files inherit the
    # system of a folder named after it (e.g. "snes"), even if SYSTEM_ROM_TYPES
    # doesn't list the extension. Arcade folders were handled above.
    for folder in _folder_names(file_path):
        for system, hints in NORMALISED_FOLDER_HINTS.items():
            if folder in hints and _accepts(system, suffix):
                return system

        if folder in SYSTEM_ROM_TYPES and folder not in ARCADE_SYSTEM_KEYWORDS:
            return folder

    # Nothing in the folder names: look inside the file
    if file_path.is_file():
        if suffix == ".zip":
            member = zip_rom_member(file_path)
            inner_suffix = Path(member).suffix.lower() if member else ""
            if inner_suffix and inner_suffix not in AMBIGUOUS_EXTENSIONS:
                inner = SYSTEM_MAP.get(inner_suffix)
                if inner and _accepts(inner, inner_suffix):
                    return inner

        if suffix in SNIFFABLE_DISC_SUFFIXES:
            sniffed = sniff_disc_system(file_path)
            if sniffed:
                return sniffed

    if not allow_guess:
        return None

    # Guess: SYSTEM_PRIORITY order first, then the candidates' own order
    ordered = [s for s in SYSTEM_PRIORITY if s in candidates] + list(candidates)
    return next((s for s in ordered if _accepts(s, suffix)), None)
