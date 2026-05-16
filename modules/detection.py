import re
from pathlib import Path
from config import SYSTEM_MAP, SYSTEM_PRIORITY, AMBIGUOUS_EXTENSIONS, SYSTEM_ROM_TYPES

DISC_REGEX = re.compile(r"(disc|disk|cd)[\s_-]*(\d+)", re.I)

# ========= FOLDER HEURISTICS =========
# Used to disambiguate systems when extensions are shared
FOLDER_HINTS = {
    "ps2": ["ps2", "playstation2", "playstation 2"],
    "psx": ["psx", "playstation1", "playstation", "ps1", "ps-1"],
    "ps3": ["ps3", "playstation3", "playstation 3"],
    "saturn": ["saturn", "sega saturn"],
    "segacd": ["segacd", "sega cd"],
    "dreamcast": ["dreamcast", "dc", "sega dc"],
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


def detect_arcade(path):
    p = str(path).lower()

    for system, keywords in ARCADE_SYSTEM_KEYWORDS.items():
        for keyword in keywords:
            if keyword in p:
                return system

    return None


def detect_system(file_path):
    """
    Detect system from file path using multiple strategies:
    1. Arcade detection by folder keyword
    2. Folder heuristics (if extension is ambiguous)
    3. Extension mapping
    4. SYSTEM_ROM_TYPES validation (confirm extension is valid for system)
    5. SYSTEM_PRIORITY for disambiguation

    Args:
        file_path: Path object or string representing the file

    Returns:
        System ID string (e.g., "ps2", "psx"), or None if not found
    """
    file_path = Path(file_path) if isinstance(file_path, str) else file_path
    suffix = file_path.suffix.lower()
    parent_path = str(file_path.parent).lower()

    # Skip non-file entries
    if not suffix:
        return None

    # Arcade detection by folder keyword
    arcade = detect_arcade(file_path)
    if arcade:
        return arcade

    # Check if this is an ambiguous extension
    if suffix in AMBIGUOUS_EXTENSIONS:
        candidates = AMBIGUOUS_EXTENSIONS[suffix]
    else:
        # Get system from regular SYSTEM_MAP
        sys = SYSTEM_MAP.get(suffix)
        if sys:
            # Validate that extension is in SYSTEM_ROM_TYPES for this system
            if sys in SYSTEM_ROM_TYPES:
                if suffix in SYSTEM_ROM_TYPES[sys]:
                    return sys
            else:
                return sys
        return None

    # Multiple candidates - use folder heuristics first
    for system in candidates:
        if system in FOLDER_HINTS:
            for hint in FOLDER_HINTS[system]:
                if hint in parent_path:
                    # Validate this system actually uses this extension
                    if (
                        system in SYSTEM_ROM_TYPES
                        and suffix in SYSTEM_ROM_TYPES[system]
                    ):
                        return system
                    elif system not in SYSTEM_ROM_TYPES:
                        return system

    # Use SYSTEM_PRIORITY to disambiguate
    for prioritized_system in SYSTEM_PRIORITY:
        if prioritized_system in candidates:
            # Validate this system actually uses this extension
            if prioritized_system in SYSTEM_ROM_TYPES:
                if suffix in SYSTEM_ROM_TYPES[prioritized_system]:
                    return prioritized_system
            else:
                return prioritized_system

    # No priority match - return first valid candidate
    for candidate in candidates:
        if candidate in SYSTEM_ROM_TYPES:
            if suffix in SYSTEM_ROM_TYPES[candidate]:
                return candidate
        else:
            return candidate

    return None
