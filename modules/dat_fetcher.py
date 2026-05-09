import requests
import xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime
import os

from config import DAT_DIR


class DATFetcher:
    """Fetches and manages DAT files from various sources"""

    # Popular DAT sources
    DAT_SOURCES = {
        'no-intro': 'https://datomatic.no-intro.org/index.php?page=download&file=',
        'redump': 'http://redump.org/datfiles/',
        # Add more sources as needed
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
                filename = url.split('/')[-1]

            if not filename.endswith('.dat'):
                filename += '.dat'

            file_path = DAT_DIR / filename

            self.logger(f"Fetching DAT: {filename}", 'INFO')
            response = requests.get(url, timeout=30)
            response.raise_for_status()

            with open(file_path, 'wb') as f:
                f.write(response.content)

            # Validate the DAT file
            if self._validate_dat_file(file_path):
                self.logger(f"✓ Successfully downloaded: {filename}", 'SUCCESS')
                return True
            else:
                self.logger(f"✗ Invalid DAT file: {filename}", 'ERROR')
                file_path.unlink()  # Delete invalid file
                return False

        except requests.exceptions.RequestException as e:
            self.logger(f"✗ Failed to fetch {filename}: {str(e)}", 'ERROR')
            return False
        except Exception as e:
            self.logger(f"✗ Error processing {filename}: {str(e)}", 'ERROR')
            return False

    def _validate_dat_file(self, file_path):
        """Check if DAT file is valid XML"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            return root.tag in ('datafile', 'mame')
        except Exception:
            return False

    def fetch_no_intro_dats(self, systems=None):
        """
        Fetch No-Intro DAT files

        Args:
            systems (list): List of systems to fetch (e.g., ['nes', 'snes', 'psx'])
                          If None, fetches all available

        Returns:
            dict: Success/failure results for each system
        """
        results = {}

        # Map of common system names to No-Intro DAT identifiers
        system_map = {
            'nes': 'Nintendo - NES',
            'snes': 'Nintendo - SNES',
            'gba': 'Nintendo - Game Boy Advance',
            'nds': 'Nintendo - Nintendo DS',
            'n3ds': 'Nintendo - Nintendo 3DS',
            'gc': 'Nintendo - GameCube',
            'wii': 'Nintendo - Wii',
            'switch': 'Nintendo - Switch',
            'psx': 'Sony - PlayStation',
            'ps2': 'Sony - PlayStation 2',
            'psp': 'Sony - PSP',
            'genesis': 'Sega - Genesis',
            'gg': 'Sega - Game Gear',
            'dreamcast': 'Sega - Dreamcast',
        }

        target_systems = systems or system_map.keys()

        self.logger(f"Starting No-Intro DAT fetch for: {', '.join(target_systems)}", 'INFO')

        for system in target_systems:
            if system not in system_map:
                self.logger(f"⚠️  Unknown system: {system}", 'WARNING')
                results[system] = False
                continue

            dat_name = system_map[system]
            # Format: "Nintendo - NES (20240101).dat"
            url = f"{self.DAT_SOURCES['no-intro']}{dat_name}"
            results[system] = self.fetch_dat(url, f"{system}.dat")

        return results

    def list_local_dats(self):
        """List all locally stored DAT files"""
        if not DAT_DIR.exists():
            return []

        dats = list(DAT_DIR.glob('*.dat'))
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
            games = root.findall('.//game')

            return {
                'filename': dat_filename,
                'size_mb': round(stat.st_size / (1024 * 1024), 2),
                'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                'games': len(games)
            }
        except Exception as e:
            self.logger(f"Error reading DAT info for {dat_filename}: {e}", 'ERROR')
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
        for dat_file in DAT_DIR.glob('*.dat'):
            system = dat_file.stem.split('_')[0]
            if system not in dats_by_system:
                dats_by_system[system] = []
            dats_by_system[system].append(dat_file)

        # Delete old files, keeping only the newest
        for system, dats in dats_by_system.items():
            sorted_dats = sorted(dats, key=lambda x: x.stat().st_mtime, reverse=True)
            for old_dat in sorted_dats[keep_count:]:
                try:
                    old_dat.unlink()
                    self.logger(f"Deleted old DAT: {old_dat.name}", 'DEBUG')
                except Exception as e:
                    self.logger(f"Failed to delete {old_dat.name}: {e}", 'ERROR')