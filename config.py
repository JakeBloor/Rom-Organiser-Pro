import os
from pathlib import Path

# ========= PATHS =========

EMUDECK_ROOT = Path.home() / "Emulation" / "roms"
DAT_DIR = Path("./dats")
CACHE_DIR = Path("./cache")
LOG_DIR = Path("./logs")
MEDIA_DIR = Path("./media")

# ========= API CONFIG =========

# SteamGridDB
STEAMGRIDDB_API = "58e1ea89a891ec6dde2f818155da4146"

# ScreenScraper
SCREENSCRAPER_USER = "ChibiChan10"
SCREENSCRAPER_PASSWORD = ""

# ========= SCRAPER SETTINGS =========

ENABLE_STEAMGRIDDB = True
ENABLE_SCREENSCRAPER = True
ENABLE_IGDB = False
ENABLE_RETROACHIEVEMENTS = False
ENABLE_VIDEO_SCRAPING = False
ENABLE_SCREENSHOTS = True
ENABLE_BOXART = True
ENABLE_LOGOS = True

SCRAPER_THREADS = 4
SCRAPER_REGION = "us"
SCRAPER_LANGUAGE = "en"

# ========= SYSTEM PRIORITY =========
# Used for ambiguous extensions (e.g., .iso, .cue, .bin, .chd)
# Priority order when multiple systems share extensions
# Higher in list = checked first

SYSTEM_PRIORITY = [
    # Modern consoles
    "switch",
    "ps5",
    "xboxseriesx",
    # Last-gen consoles
    "ps4",
    "xboxone",
    # Previous generation
    "ps3",
    "xbox360",
    # Disc-based systems
    "ps2",
    "psx",
    "gc",
    "wii",
    "wiiu",
    # Sega disc
    "dreamcast",
    "saturn",
    # Arcade/Emulation
    "fbneo",
    "mame",
    # CD-based
    "segacd",
    "pcenginecd",
    "jaguarcd",
]

# ========= AMBIGUOUS EXTENSION MAPPING =========
# Extensions that map to multiple systems
# These require folder hints or SYSTEM_PRIORITY to resolve
# Order matters: systems listed first are checked in SYSTEM_PRIORITY order

AMBIGUOUS_EXTENSIONS = {
    # ISO can be many disc-based systems
    ".iso": ["ps2", "ps3", "ps4", "psx", "segacd", "dreamcast", "gc", "wii", "wiiu"],
    # CUE files (cue/bin pairs)
    ".cue": ["psx", "segacd", "dreamcast", "pcenginecd"],
    ".bin": ["psx", "segacd", "dreamcast"],
    # CHD compressed format (multi-system)
    ".chd": ["saturn", "gc", "wii", "wiiu", "fbneo", "mame", "arcade"],
    # IMG format (also multi-system)
    ".img": ["psx", "saturn", "dreamcast"],
    # ZIP archives (can be arcade or other)
    ".zip": ["fbneo", "mame", "arcade"],
    ".7z": ["fbneo", "mame", "arcade"],
}

# ========= ROM TYPE DEFINITIONS =========
# Defines which ROM extensions belong to each system
# Used for intelligent filtering when same extension shared across systems

SYSTEM_ROM_TYPES = {
    # Nintendo
    "nes": [".nes", ".unf", ".unif"],
    "fds": [".fds"],
    "snes": [".smc", ".sfc", ".fig", ".swc"],
    "n64": [".n64", ".z64", ".v64"],
    "gc": [".gcm", ".gcz", ".rvz", ".tgc", ".chd"],
    "wii": [".wbfs", ".wad", ".wia", ".iso"],
    "wiiu": [".wud", ".wux", ".wua", ".iso"],
    "switch": [".xci", ".nsp", ".nsz"],
    "gb": [".gb"],
    "gbc": [".gbc"],
    "gba": [".gba"],
    "nds": [".nds", ".dsi"],
    "n3ds": [".3ds", ".cia", ".cci"],
    "virtualboy": [".vb"],
    "wonderswan": [".ws"],
    "wonderswancolor": [".wsc"],
    # Sony
    "psx": [".pbp", ".cue", ".bin", ".ecm", ".img", ".iso"],
    "ps2": [".iso", ".isz", ".cso"],
    "ps3": [".iso", ".pkg", ".ps3"],
    "ps4": [".iso", ".pkg"],
    "ps5": [".iso", ".pkg"],
    "psp": [".iso", ".cso", ".pbp"],
    "psvita": [".vpk", ".pkg"],
    # Sega
    "mastersystem": [".sms"],
    "gamegear": [".gg"],
    "genesis": [".gen", ".md", ".smd"],
    "sega32x": [".32x"],
    "saturn": [".iso", ".ccd", ".chd", ".img"],
    "segacd": [".iso", ".cue", ".bin"],
    "dreamcast": [".iso", ".cdi", ".cue", ".bin", ".gdi"],
    # NEC
    "pcengine": [".pce", ".chd"],
    "pcenginecd": [".iso", ".cue", ".chd"],
    # SNK
    "neogeo": [".neo", ".zip", ".7z"],
    "ngp": [".ngp"],
    "ngpc": [".ngc"],
    # Arcade
    "fbneo": [".zip", ".7z", ".chd"],
    "mame": [".zip", ".7z", ".chd"],
    "arcade": [".zip", ".7z"],
    # Microsoft
    "xbox": [".iso", ".xbe"],
    "xbox360": [".iso", ".xex"],
    "xboxone": [".iso"],
    "xboxseriesx": [".iso"],
    # Atari
    "atari2600": [".a26"],
    "atari5200": [".a52"],
    "atari7800": [".a78"],
    "atarilynx": [".lnx"],
    "jaguar": [".j64", ".jag", ".abs", ".rom"],
    "jaguarcd": [".iso", ".cue"],
    "atari800": [".atr", ".xfd", ".atx"],
    "atarist": [".st", ".msa", ".stx"],
    # Commodore
    "amiga": [".adf", ".adz", ".ipf", ".hdf", ".lha"],
    "c64": [".d64", ".t64", ".crt", ".tap", ".prg"],
    "vic20": [".prg", ".t64"],
    # Computers
    "zxspectrum": [".tzx", ".z80", ".sna", ".tap", ".dsk"],
    "amstradcpc": [".dsk", ".cdt"],
    "msx": [".mx1", ".mx2", ".rom", ".dsk"],
    "x68000": [".dim", ".xdf", ".2hd"],
    "dos": [".exe", ".com", ".bat", ".iso", ".cue"],
    # Other
    "scummvm": [".scummvm"],
    "openbor": [".pak"],
    "pico8": [".p8", ".png"],
    "tic80": [".tic"],
    "ports": [".sh"],
    "easyrpg": [".ldb"],
    "lutro": [".lua"],
    "solarus": [".solarus"],
}

# ========= SYSTEM MAP =========
# Comprehensive EmuDeck system mapping
# Ambiguous extensions are defined separately above

SYSTEM_MAP = {
    # =====================================================
    # ATARI
    # =====================================================
    ".a26": "atari2600",
    ".a52": "atari5200",
    ".a78": "atari7800",
    ".lnx": "atarilynx",
    ".j64": "jaguar",
    ".jag": "jaguar",
    ".abs": "jaguar",
    ".atr": "atari800",
    ".xfd": "atari800",
    ".atx": "atari800",
    ".st": "atarist",
    ".msa": "atarist",
    ".stx": "atarist",
    # =====================================================
    # NINTENDO
    # =====================================================
    ".nes": "nes",
    ".fds": "fds",
    ".unf": "nes",
    ".unif": "nes",
    ".smc": "snes",
    ".sfc": "snes",
    ".fig": "snes",
    ".swc": "snes",
    ".n64": "n64",
    ".z64": "n64",
    ".v64": "n64",
    ".gb": "gb",
    ".gbc": "gbc",
    ".gba": "gba",
    ".nds": "nds",
    ".dsi": "nds",
    ".3ds": "n3ds",
    ".cia": "n3ds",
    ".cci": "n3ds",
    ".gcm": "gc",
    ".gcz": "gc",
    ".rvz": "gc",
    ".tgc": "gc",
    ".wbfs": "wii",
    ".wad": "wii",
    ".wia": "wii",
    ".wud": "wiiu",
    ".wux": "wiiu",
    ".wua": "wiiu",
    ".xci": "switch",
    ".nsp": "switch",
    ".nsz": "switch",
    ".vb": "virtualboy",
    ".ws": "wonderswan",
    ".wsc": "wonderswancolor",
    # =====================================================
    # SONY
    # =====================================================
    ".pbp": "psx",
    ".ecm": "psx",
    ".img": "psx",
    ".mdf": "psx",
    ".toc": "psx",
    ".isz": "ps2",
    ".cso": "psp",
    ".pkg": "ps3",
    ".ps3": "ps3",
    ".vpk": "psvita",
    # =====================================================
    # SEGA
    # =====================================================
    ".sms": "mastersystem",
    ".gg": "gamegear",
    ".gen": "genesis",
    ".md": "genesis",
    ".smd": "genesis",
    ".32x": "sega32x",
    ".ccd": "saturn",
    ".gdi": "dreamcast",
    ".cdi": "dreamcast",
    # =====================================================
    # NEC
    # =====================================================
    ".pce": "pcengine",
    ".sgx": "pcengine",
    # =====================================================
    # SNK
    # =====================================================
    ".neo": "neogeo",
    ".ngp": "ngp",
    ".ngc": "ngpc",
    # =====================================================
    # ARCADE
    # =====================================================
    ".zip": "fbneo",
    ".7z": "fbneo",
    # =====================================================
    # MICROSOFT
    # =====================================================
    ".xbe": "xbox",
    ".xex": "xbox360",
    # =====================================================
    # COMMODORE & COMPUTERS
    # =====================================================
    ".adf": "amiga",
    ".adz": "amiga",
    ".ipf": "amiga",
    ".hdf": "amiga",
    ".lha": "amiga",
    ".d64": "c64",
    ".t64": "c64",
    ".crt": "c64",
    ".tap": "c64",
    ".prg": "c64",
    ".d81": "c64",
    ".x64": "c64",
    # =====================================================
    # ZX / AMSTRAD / MSX
    # =====================================================
    ".tzx": "zxspectrum",
    ".z80": "zxspectrum",
    ".sna": "zxspectrum",
    ".tap": "zxspectrum",
    ".dsk": "amstradcpc",
    ".cdt": "amstradcpc",
    ".mx1": "msx",
    ".mx2": "msx",
    ".rom": "msx",
    # =====================================================
    # SHARP
    # =====================================================
    ".dim": "x68000",
    ".xdf": "x68000",
    ".2hd": "x68000",
    # =====================================================
    # DOS / PC
    # =====================================================
    ".dosz": "dos",
    ".exe": "dos",
    ".com": "dos",
    ".bat": "dos",
    # =====================================================
    # SCUMMVM
    # =====================================================
    ".scummvm": "scummvm",
    # =====================================================
    # OPENBOR
    # =====================================================
    ".pak": "openbor",
    # =====================================================
    # LUA / TIC80 / PICO8
    # =====================================================
    ".p8": "pico8",
    ".png": "pico8",
    ".tic": "tic80",
    # =====================================================
    # PORTS
    # =====================================================
    ".sh": "ports",
    # =====================================================
    # EASYRPG
    # =====================================================
    ".ldb": "easyrpg",
    # =====================================================
    # LUTRO
    # =====================================================
    ".lua": "lutro",
    # =====================================================
    # SOLARUS
    # =====================================================
    ".solarus": "solarus",
}
