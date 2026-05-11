import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
import zipfile
import io
import gzip

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
        Fetch a single DAT file from URL with proper redirect handling and compression support.
        Handles DAT-o-MATIC's form-based downloads.

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

            # First request to get potential form/selection page
            response = requests.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()

            content = response.content

            # If we got an HTML selection page from DAT-o-MATIC, submit the form
            if (
                content.startswith(b"<!DOCTYPE") or content.startswith(b"<html")
            ) and "datomatic" in url.lower():
                self.logger(
                    f"Got selection page, submitting download request...", "INFO"
                )

                # Extract the system ID from the URL
                system_id_match = re.search(r"&s=(\d+)", url)
                if system_id_match:
                    system_id = system_id_match.group(1)

                    # Try to submit a download request with form data
                    form_url = "https://datomatic.no-intro.org/index.php"
                    form_data = {
                        "page": "download",
                        "s": system_id,
                        "op": "dat",
                        "download": "1",
                    }

                    response = requests.post(
                        form_url, data=form_data, timeout=30, allow_redirects=True
                    )
                    response.raise_for_status()
                    content = response.content

                    # If still HTML, extract checkbox select list and try again
                    if content.startswith(b"<!DOCTYPE") or content.startswith(b"<html"):
                        html_str = content.decode("utf-8", errors="ignore")
                        # Look for checkboxes in the form
                        checkbox_matches = re.findall(
                            r'<input[^>]*name="([^"]*)"[^>]*value="(\d+)"', html_str
                        )
                        if checkbox_matches:
                            # Select the first checkbox (usually the standard DAT)
                            select_data = {
                                "page": "download",
                                "s": system_id,
                                "op": "dat",
                                checkbox_matches[0][0]: checkbox_matches[0][1],
                            }
                            response = requests.post(
                                form_url,
                                data=select_data,
                                timeout=30,
                                allow_redirects=True,
                            )
                            response.raise_for_status()
                            content = response.content

            # Check if we got HTML instead of a DAT file
            if content.startswith(b"<!DOCTYPE") or content.startswith(b"<html"):
                # Try to extract download link from HTML
                html_str = content.decode("utf-8", errors="ignore")

                # Look for common download link patterns
                download_patterns = [
                    r'href=["\']([^"\']*\.zip[^"\']*)["\']',
                    r'href=["\']([^"\']*\.gz[^"\']*)["\']',
                    r'href=["\']([^"\']*download[^"\']*)["\']',
                ]

                found_url = None
                for pattern in download_patterns:
                    matches = re.findall(pattern, html_str)
                    if matches:
                        found_url = matches[0]
                        break

                if found_url:
                    # Try the extracted URL
                    if not found_url.startswith("http"):
                        # Make it absolute
                        base_domain = "https://datomatic.no-intro.org"
                        if found_url.startswith("/"):
                            found_url = base_domain + found_url
                        else:
                            found_url = base_domain + "/" + found_url

                    self.logger(f"Following download link: {found_url}", "INFO")
                    response = requests.get(found_url, timeout=30, allow_redirects=True)
                    response.raise_for_status()
                    content = response.content
                else:
                    self.logger(
                        f"✗ Got HTML page instead of DAT file: {filename}", "ERROR"
                    )
                    return False

            # Handle ZIP files (DAT-o-MATIC may return ZIP archives)
            if content.startswith(b"PK"):  # ZIP magic number
                try:
                    self.logger(f"Extracting DAT from ZIP...", "INFO")
                    with zipfile.ZipFile(io.BytesIO(content)) as zf:
                        # Find the first .dat file in the ZIP
                        dat_files = [
                            f for f in zf.namelist() if f.lower().endswith(".dat")
                        ]
                        if dat_files:
                            content = zf.read(dat_files[0])
                        else:
                            self.logger(f"No .dat file found in ZIP", "ERROR")
                            return False
                except Exception as e:
                    self.logger(f"Failed to extract ZIP: {e}", "ERROR")
                    return False

            # Handle GZIP files
            elif content.startswith(b"\x1f\x8b"):  # GZIP magic number
                try:
                    self.logger(f"Decompressing GZIP...", "INFO")
                    content = gzip.decompress(content)
                except Exception as e:
                    self.logger(f"Failed to decompress GZIP: {e}", "ERROR")
                    return False

            with open(file_path, "wb") as f:
                f.write(content)

            # Validate the DAT file
            if self._validate_dat_file(file_path):
                self.logger(f"✓ Successfully downloaded: {filename}", "SUCCESS")
                return True
            else:
                self.logger(f"✗ Invalid DAT file (not valid XML): {filename}", "ERROR")
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
        """Return the DAT download URL for a No-Intro system from DAT-o-MATIC.

        DAT-o-MATIC doesn't serve direct download links, so we need to:
        1. Search for the system
        2. Get the system ID (s=...)
        3. Return a direct POST-able endpoint for the DAT file
        """
        try:
            query = quote(display_name, safe="")
            page_url = f"{self.DAT_SOURCES['datomatic']}{query}"
            response = requests.get(page_url, timeout=30)
            response.raise_for_status()

            html = response.text

            # Extract the system ID (s=XX) from the page
            system_id_match = re.search(r"\?page=download&s=(\d+)&op=dat", html)
            if not system_id_match:
                # Try alternate pattern
                system_id_match = re.search(r"&s=(\d+)[^0-9]", html)

            if system_id_match:
                system_id = system_id_match.group(1)
                # Return URL with op=dat which should initiate download or show selection
                return f"https://datomatic.no-intro.org/index.php?page=download&s={system_id}&op=dat"

            return None

        except Exception as e:
            self.logger(f"Error extracting DAT URL for {display_name}: {e}", "ERROR")
            return None

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
