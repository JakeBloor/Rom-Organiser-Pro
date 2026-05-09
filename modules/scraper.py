import subprocess
from pathlib import Path

from config import (
    EMUDECK_ROOT,
    SCREENSCRAPER_USER,
    SCREENSCRAPER_PASSWORD,
    SCRAPER_THREADS,
    SCRAPER_LANGUAGE,
    SCRAPER_REGION,
    ENABLE_SCREENSCRAPER
)

def needs_scraping(system_path):
    return not (system_path / "gamelist.xml").exists()

def run_skyscraper(system, logger):
    if not ENABLE_SCREENSCRAPER:
        logger("[SCRAPER] Disabled")
        return

    system_path = EMUDECK_ROOT / system

    if not needs_scraping(system_path):
        logger(f"[SCRAPER] Skipping {system}")
        return

    logger(f"[SCRAPER] Running {system}")

    command = [
        "Skyscraper",
        "-p", system,
        "-s", "screenscraper",
        "-i", str(system_path),
        "--flags", "unattend,onlymissing",
        "--threads", str(SCRAPER_THREADS),
        "--lang", SCRAPER_LANGUAGE,
        "--region", SCRAPER_REGION
    ]

    if SCREENSCRAPER_USER:
        command.extend([
            "--user", SCREENSCRAPER_USER
        ])

    if SCREENSCRAPER_PASSWORD:
        command.extend([
            "--password", SCREENSCRAPER_PASSWORD
        ])

    subprocess.run(command)