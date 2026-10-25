"""
Fixed tables the app works from: systems, extensions, DAT names and layout
rules. Settings you can change (folders, accounts, server) live in
settings.json and are edited on the Settings page; see modules/settings.py.
"""

from pathlib import Path

# ========= PATHS =========

DAT_DIR = Path("./dats")
CACHE_DIR = Path("./cache")
LOG_DIR = Path("./logs")
MEDIA_DIR = Path("./media")

# ========= SCRAPING =========

# Skyscraper platform names that differ from the ES-DE/EmuDeck folder names
SKYSCRAPER_PLATFORMS = {
    "genesis": "megadrive",
    "n3ds": "3ds",
    "fbneo": "arcade",
    "dos": "pc",
}

# ========= LAYOUT =========
# How games made of several files (a .cue/.gdi with tracks, or several discs)
# are stored, chosen on the Settings page:
#
# "shared" (default) suits both ES-DE and Steam ROM Manager. The files go in
#   <roms>/.multifile/<system>/<game>/ and a <game>.m3u playlist in the
#   system folder points at them, so each game is listed exactly once. Only
#   used for M3U_SYSTEMS; other systems keep their files in the system folder.
# "esde" uses ES-DE's "directories interpreted as files" folders
#   (<system>/<game>.m3u/). Tidiest in ES-DE, but EmuDeck's Steam ROM Manager
#   parsers add the folder and every disc inside it as separate shortcuts.

MULTI_FILE_DIR = ".multifile"

# Systems whose EmuDeck Steam ROM Manager parser accepts .m3u playlists
M3U_SYSTEMS = {
    "amiga",
    "amiga1200",
    "amiga600",
    "amigacd32",
    "c16",
    "c64",
    "dreamcast",
    "gc",
    "pcfx",
    "psx",
    "saturn",
    "segacd",
    "vic20",
    "wii",
    "x68000",
}

# ========= DAT SYSTEMS =========
# Maps DAT names (No-Intro / Redump / libretro, matched case-insensitively,
# with any trailing "(Digital)"-style suffix removed) to ES-DE system folders,
# so a hash match tells the organiser which system a file belongs to. The
# names are libretro's exactly, as they double as libretro thumbnail folders.

DAT_SYSTEM_IDS = {
    "Nintendo - Nintendo Entertainment System": "nes",
    "Nintendo - Family Computer Disk System": "fds",
    "Nintendo - Super Nintendo Entertainment System": "snes",
    "Nintendo - Satellaview": "satellaview",
    "Nintendo - Nintendo 64": "n64",
    "Nintendo - Nintendo 64DD": "n64dd",
    "Nintendo - Game Boy": "gb",
    "Nintendo - Game Boy Color": "gbc",
    "Nintendo - Game Boy Advance": "gba",
    "Nintendo - Nintendo DS": "nds",
    "Nintendo - Nintendo DSi": "nds",
    "Nintendo - Nintendo 3DS": "n3ds",
    "Nintendo - New Nintendo 3DS": "n3ds",
    "Nintendo - Virtual Boy": "virtualboy",
    "Nintendo - Pokemon Mini": "pokemini",
    "Nintendo - GameCube": "gc",
    "Nintendo - Wii": "wii",
    "Nintendo - Wii U": "wiiu",
    "Sega - Master System - Mark III": "mastersystem",
    "Sega - Game Gear": "gamegear",
    "Sega - Mega Drive - Genesis": "genesis",
    "Sega - 32X": "sega32x",
    "Sega - SG-1000": "sg-1000",
    "Sega - Mega-CD - Sega CD": "segacd",
    "Sega - Saturn": "saturn",
    "Sega - Dreamcast": "dreamcast",
    "Sega - Naomi": "naomi",
    "Sega - Naomi 2": "naomi2",
    "Sony - PlayStation": "psx",
    "Sony - PlayStation 2": "ps2",
    "Sony - PlayStation 3": "ps3",
    "Sony - PlayStation Portable": "psp",
    "Sony - PlayStation Vita": "psvita",
    "NEC - PC Engine - TurboGrafx 16": "pcengine",
    "NEC - PC Engine SuperGrafx": "supergrafx",
    "NEC - PC Engine CD - TurboGrafx-CD": "pcenginecd",
    "NEC - PC-FX": "pcfx",
    "SNK - Neo Geo Pocket": "ngp",
    "SNK - Neo Geo Pocket Color": "ngpc",
    "SNK - Neo Geo CD": "neogeocd",
    "Bandai - WonderSwan": "wonderswan",
    "Bandai - WonderSwan Color": "wonderswancolor",
    "Atari - 2600": "atari2600",
    "Atari - 5200": "atari5200",
    "Atari - 7800": "atari7800",
    "Atari - Lynx": "atarilynx",
    "Atari - Jaguar": "atarijaguar",
    "Atari - Jaguar CD": "atarijaguarcd",
    "Atari - ST": "atarist",
    "Atari - 8-bit": "atari800",
    "Commodore - 64": "c64",
    "Commodore - Amiga": "amiga",
    "Commodore - VIC-20": "vic20",
    "Commodore - CD32": "amigacd32",
    "Commodore - CDTV": "cdtv",
    "Microsoft - MSX": "msx",
    "Microsoft - MSX2": "msx2",
    "Microsoft - Xbox": "xbox",
    "Microsoft - Xbox 360": "xbox360",
    "Coleco - ColecoVision": "colecovision",
    "Mattel - Intellivision": "intellivision",
    "GCE - Vectrex": "vectrex",
    "Magnavox - Odyssey2": "odyssey2",
    "The 3DO Company - 3DO": "3do",
    "Philips - CD-i": "cdimono1",
    "Sinclair - ZX Spectrum": "zxspectrum",
    "Amstrad - CPC": "amstradcpc",
    "Sharp - X68000": "x68000",
    "DOS": "dos",
    "ScummVM": "scummvm",
    "PICO-8": "pico8",
    "TIC-80": "tic80",
    # Smaller systems with No-Intro DATs
    "Arduboy Inc - Arduboy": "arduboy",
    "Emerson - Arcadia 2001": "arcadia",
    "Fairchild - Channel F": "channelf",
    "Epoch - Super Cassette Vision": "scv",
    "Philips - Videopac+": "videopac",
    "VTech - CreatiVision": "crvision",
    "Tiger - Game.com": "gamecom",
    "Watara - Supervision": "supervision",
    "Hartung - Game Master": "gmaster",
    "Casio - PV-1000": "pv1000",
    "Funtech - Super Acan": "supracan",
    "Nintendo - Sufami Turbo": "sufami",
    "Sinclair - ZX 81": "zx81",
    "Sharp - X1": "x1",
    "Commodore - Plus-4": "plus4",
    "VTech - V.Smile": "vsmile",
    "NEC - PC-98": "pc98",
    "Atomiswave": "atomiswave",
    "Uzebox": "uzebox",
    "Mobile - J2ME": "j2me",
    "Mobile - Palm OS": "palm",
    "WASM-4": "wasm4",
    "LowRes NX": "lowresnx",
}

# Other names ES-DE uses for a system's folder, e.g. "megadrive" for the
# Genesis. Games there take the same file types, match the same DATs and
# get the same artwork as the system they stand for.
SYSTEM_ALIASES = {
    "famicom": "nes",
    "sfc": "snes",
    "megadrive": "genesis",
    "megadrivejp": "genesis",
    "megacd": "segacd",
    "megacdjp": "segacd",
    "tg16": "pcengine",
    "tg-cd": "pcenginecd",
    "sgb": "gb",
    "msx1": "msx",
    "amiga600": "amiga",
    "amiga1200": "amiga",
    "saturnjp": "saturn",
    "sega32xjp": "sega32x",
    "sega32xna": "sega32x",
    "snesna": "snes",
    "cps": "arcade",
    "cps1": "arcade",
    "cps2": "arcade",
    "cps3": "arcade",
}


def canonical_system(system):
    """The system an ES-DE folder name stands for: "megadrive" -> "genesis"."""
    return SYSTEM_ALIASES.get(system, system)

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
    "atarijaguarcd",
]

# ========= AMBIGUOUS EXTENSION MAPPING =========
# Extensions that map to multiple systems
# These require folder hints or SYSTEM_PRIORITY to resolve
# Order matters: systems listed first are checked in SYSTEM_PRIORITY order

AMBIGUOUS_EXTENSIONS = {
    # ISO can be many disc-based systems
    ".iso": [
        "ps2",
        "ps3",
        "ps4",
        "ps5",
        "psx",
        "segacd",
        "dreamcast",
        "gc",
        "wii",
        "wiiu",
        "xbox360",
        "xboxone",
        "xboxseriesx",
        "psp",
        "pcenginecd",
        "atarijaguarcd",
        "dos",
        "saturn",
        "xbox",
    ],
    # PKG files can be PS3, PS4, PS5 or Vita packages
    ".pkg": ["ps3", "ps4", "ps5", "psvita"],
    # CUE files (cue/bin pairs)
    ".cue": ["psx", "segacd", "dreamcast", "pcenginecd", "atarijaguarcd", "dos"],
    ".bin": ["psx", "segacd", "dreamcast"],
    # CHD compressed format (multi-system; the usual format for PS1/PS2/Dreamcast on EmuDeck)
    ".chd": [
        "psx",
        "ps2",
        "dreamcast",
        "saturn",
        "segacd",
        "pcenginecd",
        "pcengine",
        "psp",
        "gc",
        "wii",
        "wiiu",
        "fbneo",
        "mame",
        "arcade",
    ],
    # Compressed and EBOOT disc images shared by PlayStation systems
    ".cso": ["ps2", "psp"],
    ".pbp": ["psx", "psp"],
    # IMG format (also multi-system)
    ".img": ["psx", "saturn", "dreamcast"],
    # ZIP archives (can be arcade or other)
    ".zip": ["fbneo", "mame", "arcade", "neogeo"],
    ".7z": ["fbneo", "mame", "arcade", "neogeo"],
    # Home computer disk and tape images
    ".dsk": ["amstradcpc", "zxspectrum", "msx"],
    ".tap": ["zxspectrum", "c64"],
    ".prg": ["c64", "vic20"],
    ".t64": ["c64", "vic20"],
    ".rom": ["msx", "atarijaguar"],
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
    "gc": [".gcm", ".gcz", ".rvz", ".tgc", ".iso", ".chd"],
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
    "psx": [".pbp", ".cue", ".bin", ".ecm", ".img", ".iso", ".chd"],
    "ps2": [".iso", ".isz", ".cso", ".chd"],
    "ps3": [".iso", ".pkg", ".ps3"],
    "ps4": [".iso", ".pkg"],
    "ps5": [".iso", ".pkg"],
    "psp": [".iso", ".cso", ".pbp", ".chd"],
    "psvita": [".vpk", ".pkg"],
    # Sega
    "mastersystem": [".sms"],
    "gamegear": [".gg"],
    "genesis": [".gen", ".md", ".smd"],
    "sega32x": [".32x"],
    "saturn": [".iso", ".ccd", ".chd", ".img"],
    "segacd": [".iso", ".cue", ".bin", ".chd"],
    "dreamcast": [".iso", ".cdi", ".cue", ".bin", ".gdi", ".chd"],
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
    "atarijaguar": [".j64", ".jag", ".abs", ".rom"],
    "atarijaguarcd": [".iso", ".cue"],
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
    # Smaller systems
    "arduboy": [".hex", ".arduboy", ".zip"],
    "arcadia": [".bin", ".zip"],
    "channelf": [".bin", ".chf", ".zip"],
    "scv": [".bin", ".0", ".zip"],
    "videopac": [".bin", ".zip"],
    "crvision": [".bin", ".rom", ".zip"],
    "gamecom": [".bin", ".zip"],
    "supervision": [".sv", ".bin", ".zip"],
    "gmaster": [".bin", ".zip"],
    "pv1000": [".bin", ".zip"],
    "supracan": [".bin", ".zip"],
    "sufami": [".st", ".bs", ".sfc", ".smc", ".zip"],
    "zx81": [".p", ".t81", ".tzx", ".zip"],
    "x1": [".2d", ".2hd", ".d88", ".88d", ".hdm", ".xdf", ".dx1", ".tap", ".zip"],
    "plus4": [".d64", ".prg", ".t64", ".tap", ".crt", ".zip"],
    "vsmile": [".bin", ".zip"],
    "pc98": [".d98", ".98d", ".fdi", ".hdi", ".nfd", ".hdd", ".d88", ".88d", ".fdd", ".hdm", ".cue", ".zip"],
    "atomiswave": [".bin", ".lst", ".zip", ".7z"],
    "uzebox": [".uze"],
    "j2me": [".jar"],
    "palm": [".prc", ".pqa", ".pdb"],
    "wasm4": [".wasm"],
    "lowresnx": [".nx"],
}

# Alternative folder names take the file types of the system they stand for
for _alias, _system in SYSTEM_ALIASES.items():
    SYSTEM_ROM_TYPES.setdefault(_alias, list(SYSTEM_ROM_TYPES[_system]))

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
    ".j64": "atarijaguar",
    ".jag": "atarijaguar",
    ".abs": "atarijaguar",
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
    # =====================================================
    # SMALLER SYSTEMS (extensions only they use)
    # =====================================================
    ".arduboy": "arduboy",
    ".chf": "channelf",
    ".sv": "supervision",
    ".t81": "zx81",
    ".uze": "uzebox",
    ".jar": "j2me",
    ".prc": "palm",
    ".wasm": "wasm4",
    ".nx": "lowresnx",
}
