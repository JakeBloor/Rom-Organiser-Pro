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
STEAMGRIDDB_API = os.getenv("STEAMGRIDDB_API", "")

# ScreenScraper
SCREENSCRAPER_USER = os.getenv("SCREENSCRAPER_USER", "")
SCREENSCRAPER_PASSWORD = os.getenv("SCREENSCRAPER_PASSWORD", "")

# IGDB / Twitch API
TWITCH_CLIENT_ID = os.getenv("TWITCH_CLIENT_ID", "")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_CLIENT_SECRET", "")

# RetroAchievements
RETROACHIEVEMENTS_USER = os.getenv("RETROACHIEVEMENTS_USER", "")
RETROACHIEVEMENTS_API_KEY = os.getenv("RETROACHIEVEMENTS_API_KEY", "")

# LaunchBox Games Database
LAUNCHBOX_API_KEY = os.getenv("LAUNCHBOX_API_KEY", "")

# GiantBomb API
GIANTBOMB_API_KEY = os.getenv("GIANTBOMB_API_KEY", "")

# RAWG API
RAWG_API_KEY = os.getenv("RAWG_API_KEY", "")

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

# ========= SYSTEM MAP =========

SYSTEM_MAP = {
    ".cue": "psx",
    ".bin": "psx",
    ".chd": "psx",
    ".pbp": "psx",

    ".iso": "ps2",
    ".cso": "psp",

    ".nes": "nes",
    ".sfc": "snes",
    ".smc": "snes",
    ".gba": "gba",
    ".nds": "nds",
    ".3ds": "n3ds",

    ".gcm": "gc",
    ".rvz": "gc",

    ".wbfs": "wii",

    ".xci": "switch",
    ".nsp": "switch",

    ".gen": "genesis",
    ".md": "genesis",
    ".gg": "gamegear",

    ".gdi": "dreamcast",
    ".cdi": "dreamcast",

    ".zip": "fbneo",
    ".7z": "fbneo"
}