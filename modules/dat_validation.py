import re
import xml.etree.ElementTree as ET
from config import DAT_DIR
from modules.dat_fetcher import DATFetcher

DAT_DB = {}


def _load_clrmamepro_dat(dat, logger):
    try:
        text = dat.read_text(errors="ignore")
        entries = 0

        for game_start in re.finditer(r"game\s*\(", text, re.IGNORECASE):
            idx = game_start.end()
            depth = 1
            while idx < len(text) and depth > 0:
                ch = text[idx]
                if ch == '"':
                    idx += 1
                    while idx < len(text) and text[idx] != '"':
                        if text[idx] == "\\":
                            idx += 1
                        idx += 1
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                idx += 1

            game_block = text[game_start.end() : idx - 1]
            name_match = re.search(r'name\s+"([^"]+)"', game_block)
            if not name_match:
                continue

            game_name = name_match.group(1)

            for rom_match in re.finditer(
                r"rom\s*\((.*?)\)", game_block, re.DOTALL | re.IGNORECASE
            ):
                rom_block = rom_match.group(1)
                md5_match = re.search(r"md5\s+([0-9A-Fa-f]+)", rom_block)
                sha1_match = re.search(r"sha1\s+([0-9A-Fa-f]+)", rom_block)
                crc_match = re.search(r"crc\s+([0-9A-Fa-f]+)", rom_block)

                if not (md5_match or sha1_match or crc_match):
                    continue

                if md5_match:
                    DAT_DB[md5_match.group(1).lower()] = game_name
                if sha1_match:
                    DAT_DB[sha1_match.group(1).lower()] = game_name
                if crc_match:
                    DAT_DB[crc_match.group(1).lower()] = game_name

                entries += 1

        if entries:
            logger(f"[DAT] Loaded {entries} entries from {dat.name} (clrmamepro)")
            return True

    except Exception as e:
        logger(f"[DAT ERROR] {dat.name} clrmamepro parse failed: {e}")

    return False


def load_dat_files(logger):
    DAT_DB.clear()

    for dat in DAT_DIR.rglob("*.dat"):
        try:
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
                continue
            except Exception:
                pass

            if _load_clrmamepro_dat(dat, logger):
                continue

            logger(f"[DAT WARN] Skipped unsupported or invalid DAT: {dat.name}")

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

    # First try libretro database (fast, single archive).
    try:
        logger("Attempting to fetch DATs from libretro database...", "INFO")
        lr_results = fetcher.fetch_libretro_dats()
        if lr_results.get("libretro"):
            logger("Successfully fetched DATs from libretro repository.", "SUCCESS")
            # Load newly fetched DATs into memory
            load_dat_files(logger)
            return {"libretro": True}
        else:
            logger(
                "Libretro fetch returned no DATs, falling back to DAT-o-MATIC.",
                "WARNING",
            )
    except Exception as e:
        logger(f"Libretro fetch failed: {e}", "ERROR")

    # Fallback to DAT-o-MATIC guidance
    logger(
        "⚠️  DAT-o-MATIC may require manual download; attempting scripted fetch where possible.",
        "WARNING",
    )
    logger(
        "If scripted fetch fails, download DATs manually from https://datomatic.no-intro.org and place them in dats/.",
        "INFO",
    )

    try:
        results = fetcher.fetch_no_intro_dats(systems)
        # If any success, load dats
        if any(results.values()):
            load_dat_files(logger)
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
