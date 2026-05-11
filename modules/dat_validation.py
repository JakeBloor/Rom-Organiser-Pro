import xml.etree.ElementTree as ET
from config import DAT_DIR
from modules.dat_fetcher import DATFetcher

DAT_DB = {}


def load_dat_files(logger):
    for dat in DAT_DIR.glob("*.dat"):
        try:
            tree = ET.parse(dat)
            root = tree.getroot()

            count = 0

            for game in root.findall(".//game"):
                name = game.attrib.get("name")

                for rom in game.findall("rom"):
                    md5 = rom.attrib.get("md5")
                    sha1 = rom.attrib.get("sha1")
                    crc = rom.attrib.get("crc")

                    if md5:
                        DAT_DB[md5.lower()] = name
                    if sha1:
                        DAT_DB[sha1.lower()] = name
                    if crc:
                        DAT_DB[crc.lower()] = name

                    count += 1

            logger(f"[DAT] Loaded {count} entries from {dat.name}")

        except Exception as e:
            logger(f"[DAT ERROR] {dat.name}: {e}")


def fetch_latest_dats(logger, systems=None):
    """
    Fetch latest DAT files automatically

    Args:
        logger: Logger instance
        systems (list): Systems to fetch (e.g., ['nes', 'snes', 'psx'])

    Returns:
        dict: Fetch results
    """
    fetcher = DATFetcher(logger)

    logger(
        "⚠️  Note: DAT-o-MATIC requires manual download due to JavaScript form handling.",
        "WARNING",
    )
    logger(
        "Visit https://datomatic.no-intro.org and download DAT files manually.", "INFO"
    )
    logger("Place DAT files in the 'dats/' directory for ROM validation.", "INFO")

    try:
        results = fetcher.fetch_no_intro_dats(systems)
        return results
    except Exception as e:
        logger(f"DAT fetch error: {e}", "ERROR")
        logger(
            "As a workaround, manually download and place DAT files in dats/ folder",
            "WARNING",
        )
        return {}


def validate_hashes(hashes):
    for h in hashes.values():
        if h.lower() in DAT_DB:
            return DAT_DB[h.lower()]

    return None
