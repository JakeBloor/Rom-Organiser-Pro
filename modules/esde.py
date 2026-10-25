"""
Locations ES-DE (EmuDeck's frontend) reads ROMs, game lists and media from.

EmuDeck writes its own folders into ES-DE's settings file (for example ROMs on
the SD card), so that file is checked before falling back to the defaults.
"""

import re
from pathlib import Path

from modules import settings

SETTING_REGEX = r'<string\s+name="{name}"\s+value="([^"]*)"'


def _setting(name):
    settings_file = esde_home() / "settings" / "es_settings.xml"

    try:
        text = settings_file.read_text(errors="ignore")
    except OSError:
        return None

    match = re.search(SETTING_REGEX.format(name=name), text)
    value = match.group(1).strip() if match else ""
    return Path(value).expanduser() if value else None


def esde_home():
    return settings.path("esde_home")


def rom_root():
    """Folder holding one sub-folder per system, e.g. ~/Emulation/roms."""
    return _setting("ROMDirectory") or settings.path("default_rom_folder")


def media_root():
    """Folder ES-DE reads scraped media from: <media>/<system>/covers/<game>.png."""
    return _setting("MediaDirectory") or esde_home() / "downloaded_media"


def gamelists_root():
    """Folder holding <system>/gamelist.xml with scraped game data."""
    return esde_home() / "gamelists"
