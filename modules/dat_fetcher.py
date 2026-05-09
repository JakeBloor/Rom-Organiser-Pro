import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote

from config import DAT_DIR


class DATFetcher:
    """Fetches and manages DAT files from various sources"""

    # DAT-o-MATIC base URL for No-Intro downloads
    DAT_SOURCES = {
        "datomatic": "https://datomatic.no-intro.org/index.php?page=download&file=",
    }

    def __init__(self, logger):
        self.logger = logger
        DAT_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_dat(self, url, filename=None):
        """
        Fetch a single DAT file from URL

        Args:
            url (str): URL to fetch DAT from
            filename (str): Optional filename to save as

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if filename is None:
                filename = url.split("/")[-1]

            if not filename.endswith(".dat"):
                filename += ".dat"

            file_path = DAT_DIR / filename

            self.logger(f"Fetching DAT: {filename}", "INFO")
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(file_path, "wb") as f:
                f.write(response.content)

            # Validate the DAT file
            if self._validate_dat_file(file_path):
                self.logger(f"✓ Successfully downloaded: {filename}", "SUCCESS")
                return True
            else:
                self.logger(f"✗ Invalid DAT file: {filename}", "ERROR")
                file_path.unlink()  # Delete invalid file
                return False

        except requests.exceptions.RequestException as e:
            self.logger(f"✗ Failed to fetch {filename}: {str(e)}", "ERROR")
            return False
        except Exception as e:
            self.logger(f"✗ Error processing {filename}: {str(e)}", "ERROR")
            return False

    def _validate_dat_file(self, file_path):
        """Check if DAT file is valid XML"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return root.tag in ("datafile", "mame")
        except Exception:
            return False

    def _get_datomatic_dat_url(self, display_name):
        """Return the DAT download URL for a No-Intro system from DAT-o-MATIC."""
        query = quote(display_name, safe="")
        page_url = f"{self.DAT_SOURCES['datomatic']}{query}"
        response = requests.get(page_url, timeout=30)
        response.raise_for_status()

        html = response.text
        rows = re.findall(r"<tr[^>]*>.*?</tr>", html, re.S)

        exact_url = None
        fallback_url = None

        for row in rows:
            if "page=download&op=dat" not in row:
                continue

            name_match = re.search(r"<b>([^<]+)</b>", row)
            link_match = re.search(
                r'href\s*=\s*"(index\.php\?page=download&op=dat&s=\d+)"', row
            )
            if not name_match or not link_match:
                continue

            candidate = " ".join(name_match.group(1).split())
            if candidate == display_name:
                exact_url = link_match.group(1)
                break

            if candidate.startswith(display_name):
                fallback_url = fallback_url or link_match.group(1)

        dat_link = exact_url or fallback_url
        if not dat_link:
            return None

        return f"https://datomatic.no-intro.org/{dat_link}"

    def fetch_no_intro_dats(self, systems=None):
        """
        Fetch DAT files from DAT-o-MATIC via No-Intro.

        Args:
            systems (list): List of systems to fetch (e.g., ['nes', 'snes', 'psx'])
                          If None, fetches all available

        Returns:
            dict: Success/failure results for each system
        """
        results = {}

        # Map of common system names to No-Intro display names
        system_map = {
            "nes": "Nintendo - Nintendo Entertainment System",
            "snes": "Nintendo - Super Nintendo Entertainment System",
            "gba": "Nintendo - Game Boy Advance",
            "nds": "Nintendo - Nintendo DS",
            "n3ds": "Nintendo - Nintendo 3DS",
            "gc": "Non-Redump - Nintendo - Nintendo GameCube",
            "wii": "Non-Redump - Nintendo - Wii",
            "switch": "Nintendo - Switch",
            "psx": "Non-Redump - Sony - PlayStation",
            "ps2": "Non-Redump - Sony - PlayStation 2",
            "psp": "Non-Redump - Sony - PlayStation Portable",
            "genesis": "Sega - Mega Drive - Genesis",
            "gg": "Sega - Game Gear",
            "dreamcast": "Non-Redump - Sega - Dreamcast",
        }

        target_systems = systems or system_map.keys()

        self.logger(f"Starting DAT fetch for: {', '.join(target_systems)}", "INFO")

        for system in target_systems:
            if system not in system_map:
                self.logger(f"⚠️  Unknown system: {system}", "WARNING")
                results[system] = False
                continue

            display_name = system_map[system]
            url = self._get_datomatic_dat_url(display_name)
            if not url:
                self.logger(
                    f"✗ Unable to locate DAT download for {display_name}", "ERROR"
                )
                results[system] = False
                continue

            results[system] = self.fetch_dat(url, f"{system}.dat")

        return results

    def list_local_dats(self):
        """List all locally stored DAT files"""
        if not DAT_DIR.exists():
            return []

        dats = list(DAT_DIR.glob("*.dat"))
        return sorted([d.name for d in dats])

    def get_dat_info(self, dat_filename):
        """Get info about a specific DAT file"""
        file_path = DAT_DIR / dat_filename

        if not file_path.exists():
            return None

        try:
            stat = file_path.stat()
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Count total games
            games = root.findall(".//game")

            return {
                "filename": dat_filename,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "games": len(games),
            }
        except Exception as e:
            self.logger(f"Error reading DAT info for {dat_filename}: {e}", "ERROR")
            return None

    def cleanup_old_dats(self, keep_count=3):
        """
        Keep only the most recent N DAT files, delete older ones

        Args:
            keep_count (int): Number of recent DATs to keep per system
        """
        if not DAT_DIR.exists():
            return

        # Group DATs by system name (before the number)
        dats_by_system = {}
        for dat_file in DAT_DIR.glob("*.dat"):
            system = dat_file.stem.split("_")[0]
            if system not in dats_by_system:
                dats_by_system[system] = []
            dats_by_system[system].append(dat_file)

        # Delete old files, keeping only the newest
        for system, dats in dats_by_system.items():
            sorted_dats = sorted(dats, key=lambda x: x.stat().st_mtime, reverse=True)
            for old_dat in sorted_dats[keep_count:]:
                try:
                    old_dat.unlink()
                    self.logger(f"Deleted old DAT: {old_dat.name}", "DEBUG")
                except Exception as e:
                    self.logger(f"Failed to delete {old_dat.name}: {e}", "ERROR")
