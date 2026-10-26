import shutil
import subprocess
from collections import deque
from pathlib import Path

from config import SKYSCRAPER_PLATFORMS, canonical_system
from modules import esde, settings


# Skyscraper's flags for leaving media files already in place alone
SKIP_EXISTING = (
    "skipexistingbackcovers", "skipexistingcovers", "skipexistingfanarts", "skipexistingmanuals",
    "skipexistingmarquees", "skipexistingscreenshots", "skipexistingvideos", "skipexistingwheels",
)


def _platform(system):
    """Skyscraper's name for a system, also for ES-DE's other folder names."""
    canonical = canonical_system(system)
    return SKYSCRAPER_PLATFORMS.get(system) or SKYSCRAPER_PLATFORMS.get(canonical, canonical)


def skyscraper_commands(system, rom_root, skyscraper="Skyscraper"):
    """
    The two Skyscraper runs needed for one system: gather data and media from
    ScreenScraper into Skyscraper's cache, then write an ES-DE gamelist and
    media from that cache.
    """
    base = [
        skyscraper,
        "-p", _platform(system),
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
        # Media already there (from EmuMovies, the first source) is kept
        "--flags", "unattend,videos," + ",".join(SKIP_EXISTING),
    ]

    return [gather, generate]


def _run(command, on_output, should_stop):
    """
    Runs one Skyscraper command, passing each line it prints to on_output so
    a long scrape shows what it's doing. Skyscraper gets no input, so it can
    never sit waiting at a prompt. Returns (exit code, last lines printed), or
    (None, ...) if should_stop said to stop.
    """
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    tail = deque(maxlen=20)

    for line in process.stdout:
        line = line.strip()
        if line:
            tail.append(line)
            if on_output:
                on_output(line)
        if should_stop and should_stop():
            process.terminate()
            process.wait()
            return None, list(tail)

    return process.wait(), list(tail)


def run_skyscraper(system, logger, rom_root=None, on_output=None, should_stop=None):
    """
    Scrape game data and media for one system. Returns True on success, False
    if this system failed, or None when scraping can't run at all (disabled or
    Skyscraper missing) or was stopped, so callers can skip the remaining
    systems. on_output gets each line Skyscraper prints; should_stop is
    checked as it goes.
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
        returncode, output = _run(command, on_output, should_stop)

        if returncode is None:
            logger(f"[STOPPED] Scraping {system} was stopped", "WARNING")
            return None

        if returncode != 0:
            logger(
                f"[SCRAPER ERROR] {system}: Skyscraper exited with {returncode}"
                + (f": {output[-1]}" if output else ""),
                "ERROR",
            )
            return False

    logger(f"[SCRAPER] {system} game data and media written for ES-DE", "SUCCESS")
    return True
