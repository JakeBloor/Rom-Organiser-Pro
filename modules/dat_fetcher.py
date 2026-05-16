import re
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import quote
import zipfile
import io
import gzip
from pathlib import Path

from config import DAT_DIR


class DATFetcher:
    """Fetches and manages DAT files from various sources"""

    # DAT-o-MATIC base URL for No-Intro downloads
    DAT_SOURCES = {
        "datomatic": "https://datomatic.no-intro.org/index.php?page=download&file=",
    }

    # Libretro database commit to fetch from
    DEFAULT_LIBRETRO_COMMIT = "559696d00979f4f3c593a1ee2c7aef0ed4c47695"

    def __init__(self, logger):
        self.logger = logger
        DAT_DIR.mkdir(parents=True, exist_ok=True)

    def fetch_dat(self, url, filename=None, subfolder=None):
        """
        Fetch a single DAT file from URL with proper redirect handling
        and compression support.

        Args:
            url (str): URL to fetch DAT from
            filename (str): Optional filename to save as
            subfolder (str): Optional subfolder inside DAT_DIR

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if filename is None:
                filename = url.split("/")[-1]

            if not filename.endswith(".dat"):
                filename += ".dat"

            # Support nested folders
            target_dir = DAT_DIR / subfolder if subfolder else DAT_DIR
            target_dir.mkdir(parents=True, exist_ok=True)

            file_path = target_dir / filename

            self.logger(f"Fetching DAT: {file_path}", "INFO")

            # First request to get potential form/selection page
            response = requests.get(url, timeout=30, allow_redirects=True)
            response.raise_for_status()

            content = response.content

            # Handle DAT-o-MATIC HTML response
            if (
                content.startswith(b"<!DOCTYPE") or content.startswith(b"<html")
            ) and "datomatic" in url.lower():

                self.logger(
                    "Got selection page, submitting download request...",
                    "INFO",
                )

                system_id_match = re.search(r"&s=(\d+)", url)

                if system_id_match:
                    system_id = system_id_match.group(1)

                    form_url = "https://datomatic.no-intro.org/index.php"

                    form_data = {
                        "page": "download",
                        "s": system_id,
                        "op": "dat",
                        "download": "1",
                    }

                    response = requests.post(
                        form_url,
                        data=form_data,
                        timeout=30,
                        allow_redirects=True,
                    )

                    response.raise_for_status()
                    content = response.content

                    # Handle selection forms
                    if content.startswith(b"<!DOCTYPE") or content.startswith(b"<html"):
                        html_str = content.decode(
                            "utf-8",
                            errors="ignore",
                        )

                        checkbox_matches = re.findall(
                            r'<input[^>]*name="([^"]*)"[^>]*value="(\d+)"',
                            html_str,
                        )

                        if checkbox_matches:
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

            # Handle unexpected HTML
            if content.startswith(b"<!DOCTYPE") or content.startswith(b"<html"):
                html_str = content.decode("utf-8", errors="ignore")

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
                    if not found_url.startswith("http"):
                        base_domain = "https://datomatic.no-intro.org"

                        if found_url.startswith("/"):
                            found_url = base_domain + found_url
                        else:
                            found_url = base_domain + "/" + found_url

                    self.logger(
                        f"Following download link: {found_url}",
                        "INFO",
                    )

                    response = requests.get(
                        found_url,
                        timeout=30,
                        allow_redirects=True,
                    )

                    response.raise_for_status()
                    content = response.content

                else:
                    self.logger(
                        f"✗ Got HTML page instead of DAT file: {filename}",
                        "ERROR",
                    )
                    return False

            # Handle ZIP archives
            if content.startswith(b"PK"):
                try:
                    self.logger("Extracting DAT from ZIP...", "INFO")

                    with zipfile.ZipFile(io.BytesIO(content)) as zf:
                        dat_files = [
                            f for f in zf.namelist() if f.lower().endswith(".dat")
                        ]

                        if dat_files:
                            content = zf.read(dat_files[0])
                        else:
                            self.logger(
                                "No .dat file found in ZIP",
                                "ERROR",
                            )
                            return False

                except Exception as e:
                    self.logger(
                        f"Failed to extract ZIP: {e}",
                        "ERROR",
                    )
                    return False

            # Handle GZIP
            elif content.startswith(b"\x1f\x8b"):
                try:
                    self.logger("Decompressing GZIP...", "INFO")
                    content = gzip.decompress(content)

                except Exception as e:
                    self.logger(
                        f"Failed to decompress GZIP: {e}",
                        "ERROR",
                    )
                    return False

            with open(file_path, "wb") as f:
                f.write(content)

            # Validate DAT
            if self._validate_dat_file(file_path):
                self.logger(
                    f"✓ Successfully downloaded: {file_path}",
                    "SUCCESS",
                )
                return True

            self.logger(
                f"✗ Invalid DAT file (not valid XML): {filename}",
                "ERROR",
            )

            file_path.unlink(missing_ok=True)
            return False

        except requests.exceptions.RequestException as e:
            self.logger(
                f"✗ Failed to fetch {filename}: {str(e)}",
                "ERROR",
            )
            return False

        except Exception as e:
            self.logger(
                f"✗ Error processing {filename}: {str(e)}",
                "ERROR",
            )
            return False

    def _validate_dat_file(self, file_path):
        """
        Check if DAT file is valid XML.

        Many DAT formats use different root tags,
        so we only verify that the XML parses.
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()

            # Any valid XML root is acceptable
            return root is not None

        except Exception as e:
            self.logger(
                f"Invalid DAT/XML file {file_path}: {e}",
                "ERROR",
            )
            return False

    def _get_datomatic_dat_url(self, display_name):
        """
        Return the DAT download URL for a No-Intro system
        from DAT-o-MATIC.
        """
        try:
            query = quote(display_name, safe="")
            page_url = f"{self.DAT_SOURCES['datomatic']}{query}"

            response = requests.get(page_url, timeout=30)
            response.raise_for_status()

            html = response.text

            system_id_match = re.search(
                r"\?page=download&s=(\d+)&op=dat",
                html,
            )

            if not system_id_match:
                system_id_match = re.search(
                    r"&s=(\d+)[^0-9]",
                    html,
                )

            if system_id_match:
                system_id = system_id_match.group(1)

                return (
                    "https://datomatic.no-intro.org/"
                    f"index.php?page=download&s={system_id}&op=dat"
                )

            return None

        except Exception as e:
            self.logger(
                f"Error extracting DAT URL for {display_name}: {e}",
                "ERROR",
            )
            return None

    def fetch_no_intro_dats(self, systems=None):
        """
        Fetch DAT files from DAT-o-MATIC via No-Intro.
        """
        results = {}

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

        self.logger(
            f"Starting DAT fetch for: {', '.join(target_systems)}",
            "INFO",
        )

        for system in target_systems:
            if system not in system_map:
                self.logger(
                    f"⚠️ Unknown system: {system}",
                    "WARNING",
                )
                results[system] = False
                continue

            display_name = system_map[system]

            url = self._get_datomatic_dat_url(display_name)

            if not url:
                self.logger(
                    f"✗ Unable to locate DAT download for {display_name}",
                    "ERROR",
                )
                results[system] = False
                continue

            # Save in subfolders by system
            results[system] = self.fetch_dat(
                url,
                f"{system}.dat",
                subfolder=system,
            )

        return results

    def list_local_dats(self):
        """
        List all locally stored DAT files,
        including subfolders.
        """
        if not DAT_DIR.exists():
            return []

        dats = list(DAT_DIR.rglob("*.dat"))

        return sorted([str(d.relative_to(DAT_DIR)) for d in dats])

    def get_dat_info(self, dat_filename):
        """
        Get info about a DAT file.
        Supports nested paths.
        """
        file_path = DAT_DIR / dat_filename

        if not file_path.exists():
            return None

        try:
            stat = file_path.stat()

            tree = ET.parse(file_path)
            root = tree.getroot()

            games = root.findall(".//game")

            return {
                "filename": str(dat_filename),
                "size_mb": round(
                    stat.st_size / (1024 * 1024),
                    2,
                ),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),
                "games": len(games),
            }

        except Exception as e:
            self.logger(
                f"Error reading DAT info for {dat_filename}: {e}",
                "ERROR",
            )
            return None

    def cleanup_old_dats(self, keep_count=3):
        """
        Keep only the most recent N DAT files,
        including subfolders.
        """
        if not DAT_DIR.exists():
            return

        dats_by_system = {}

        # Recursive DAT search
        for dat_file in DAT_DIR.rglob("*.dat"):
            system = dat_file.stem.split("_")[0]

            if system not in dats_by_system:
                dats_by_system[system] = []

            dats_by_system[system].append(dat_file)

        for system, dats in dats_by_system.items():
            sorted_dats = sorted(
                dats,
                key=lambda x: x.stat().st_mtime,
                reverse=True,
            )

            for old_dat in sorted_dats[keep_count:]:
                try:
                    old_dat.unlink()

                    self.logger(
                        f"Deleted old DAT: {old_dat}",
                        "DEBUG",
                    )

                except Exception as e:
                    self.logger(
                        f"Failed to delete {old_dat}: {e}",
                        "ERROR",
                    )

    def fetch_libretro_repo(self, commit_hash=None):
        """
        Download libretro-database archive
        and extract DAT files.
        """
        try:
            commit = commit_hash or self.DEFAULT_LIBRETRO_COMMIT

            zip_url = (
                "https://github.com/libretro/" f"libretro-database/archive/{commit}.zip"
            )

            self.logger(
                f"Fetching libretro database archive: {zip_url}",
                "INFO",
            )

            response = requests.get(
                zip_url,
                timeout=60,
                stream=True,
            )

            response.raise_for_status()

            content = response.content

            if content.startswith(b"PK"):
                with zipfile.ZipFile(io.BytesIO(content)) as zf:
                    dat_names = [n for n in zf.namelist() if n.lower().endswith(".dat")]

                    if not dat_names:
                        self.logger(
                            "No .dat files found in libretro archive",
                            "WARNING",
                        )
                        return False

                    extracted = 0

                    for name in dat_names:
                        try:
                            data = zf.read(name)

                            # Preserve subfolder structure
                            relative_path = Path(name)

                            # Remove top-level archive folder
                            relative_parts = relative_path.parts[1:]

                            if not relative_parts:
                                continue

                            dest = DAT_DIR.joinpath(*relative_parts)

                            dest.parent.mkdir(
                                parents=True,
                                exist_ok=True,
                            )

                            with open(dest, "wb") as f:
                                f.write(data)

                            if self._validate_dat_file(dest):
                                extracted += 1

                                self.logger(
                                    f"Extracted DAT: {dest}",
                                    "SUCCESS",
                                )
                            else:
                                self.logger(
                                    f"Rejected invalid DAT: {dest}",
                                    "WARNING",
                                )

                        except Exception as e:
                            self.logger(
                                f"Failed to extract {name}: {e}",
                                "ERROR",
                            )

                    return extracted > 0

            self.logger(
                "Downloaded libretro archive is not a ZIP file",
                "ERROR",
            )

            return False

        except requests.exceptions.RequestException as e:
            self.logger(
                f"Failed to download libretro archive: {e}",
                "ERROR",
            )
            return False

        except Exception as e:
            self.logger(
                f"Error extracting libretro archive: {e}",
                "ERROR",
            )
            return False

    def fetch_libretro_dats(self, commit_hash=None):
        """
        High-level convenience wrapper.
        """
        success = self.fetch_libretro_repo(commit_hash)

        return {"libretro": bool(success)}
