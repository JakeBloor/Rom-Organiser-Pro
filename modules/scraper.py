import shutil
import subprocess
from pathlib import Path

from config import SKYSCRAPER_PLATFORMS
from modules import esde, settings


def skyscraper_commands(system, rom_root, skyscraper="Skyscraper"):
    """
    The two Skyscraper runs needed for one system: gather data and media from
    ScreenScraper into Skyscraper's cache, then write an ES-DE gamelist and
    media from that cache.
    """
    base = [
        skyscraper,
        "-p", SKYSCRAPER_PLATFORMS.get(system, system),
        "-i", str(Path(rom_root) / system),
    ]

    # ES-DE output includes back covers, fan art and manuals whenever they're
    # cached; videos also need the flag when generating
    gather = base + [
        "-s", "screenscraper",
        "--flags", "unattend,onlymissing,backcovers,fanarts,manuals,videos",
        "-t", str(settings.get("scraper_threads")),
        "--lang", settings.get("scraper_language"),
        "--region", settings.get("scraper_region"),
    ]

    user = settings.get("screenscraper_user")
    password = settings.get("screenscraper_password")
    if user and password:
        gather.extend(["-u", f"{user}:{password}"])

    generate = base + [
        "-f", "esde",
        "-g", str(esde.gamelists_root() / system),
        "-o", str(esde.media_root() / system),
        "--flags", "unattend,videos",
    ]

    return [gather, generate]


def run_skyscraper(system, logger, rom_root=None):
    """
    Scrape game data and media for one system. Returns True on success, False
    if this system failed, or None when scraping can't run at all (disabled or
    Skyscraper missing), so callers can skip the remaining systems.
    """
    if not settings.get("enable_screenscraper"):
        logger("[SCRAPER] Disabled")
        return None

    skyscraper = shutil.which("Skyscraper")

    if not skyscraper:
        logger(
            "[SCRAPER] Skyscraper isn't installed, so game data wasn't downloaded. "
            "Install it, or scrape from ES-DE instead (Main menu > Scraper).",
            "WARNING",
        )
        return None

    rom_root = Path(rom_root) if rom_root else esde.rom_root()
    logger(f"[SCRAPER] Running {system}")

    for command in skyscraper_commands(system, rom_root, skyscraper):
        result = subprocess.run(command, capture_output=True, text=True, check=False)

        if result.returncode != 0:
            output = (result.stderr or result.stdout).strip().splitlines()
            logger(
                f"[SCRAPER ERROR] {system}: Skyscraper exited with {result.returncode}"
                + (f": {output[-1]}" if output else ""),
                "ERROR",
            )
            return False

    logger(f"[SCRAPER] {system} game data and media written for ES-DE", "SUCCESS")
    return True
