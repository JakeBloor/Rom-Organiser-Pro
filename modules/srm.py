"""
Point EmuDeck's Steam ROM Manager parsers at the app's Steam artwork, so the
images show up in Steam next time SRM adds the games.
"""

import json
import re
import shutil
from pathlib import Path

from config import DAT_SYSTEM_IDS, M3U_SYSTEMS, SYSTEM_ROM_TYPES
from modules import settings
from modules.media import STEAM_IMAGE_TYPES

KNOWN_SYSTEMS = set(SYSTEM_ROM_TYPES) | set(DAT_SYSTEM_IDS.values()) | M3U_SYSTEMS
BACKUP_SUFFIX = ".rom-organiser.bak"

# Characters with a meaning in SRM's globs, escaped with a backslash in paths
GLOB_SPECIAL = re.compile(r"([\[\]{}()*?!+@])")


def parser_system(parser):
    """
    The ES-DE system an SRM parser reads, from its ROM folder ("${romsdirglobal}/psx")
    or, for parsers rooted at the ROM folder, the start of its glob ("{snes/**,...}/...").
    """
    folder = parser.get("romDirectory", "").rstrip("/").rsplit("/", 1)[-1]
    if folder in KNOWN_SYSTEMS:
        return folder

    match = re.match(r"[{@(]*([a-z0-9-]+)", parser.get("parserInputs", {}).get("glob", ""))
    if match and match.group(1) in KNOWN_SYSTEMS:
        return match.group(1)

    return None


def local_image_globs(steam_root, system):
    root = GLOB_SPECIAL.sub(r"\\\1", Path(steam_root).as_posix())
    return {
        kind: f"{root}/{system}/{kind}/${{fileName}}.@(png|jpg)" for kind in STEAM_IMAGE_TYPES
    }


def configure_srm(steam_root, logger, config_path=None):
    """
    Fill each parser's empty local image globs. Images a user already set up
    are left alone, and the original config is backed up once beside it.

    Returns {"updated": [parser titles], "backup": path}, or {"error": message}.
    """
    config_path = Path(config_path or settings.path("srm_config"))

    try:
        parsers = json.loads(config_path.read_text())
    except (OSError, ValueError) as e:
        logger(f"[STEAM] Couldn't read Steam ROM Manager's parsers at {config_path}: {e}", "ERROR")
        return {"error": f"Couldn't read {config_path}"}

    backup = config_path.with_name(config_path.name + BACKUP_SUFFIX)
    if not backup.exists():
        shutil.copy2(config_path, backup)

    updated = []

    for parser in parsers:
        system = parser_system(parser)
        if not system:
            continue

        images = parser.setdefault("localImages", {})
        missing = {
            kind: glob for kind, glob in local_image_globs(steam_root, system).items()
            if not images.get(kind)
        }
        if missing:
            images.update(missing)
            updated.append(parser.get("configTitle", system))

    config_path.write_text(json.dumps(parsers, indent=2))
    logger(
        f"[STEAM] Steam ROM Manager will use local artwork for {len(updated)} parsers. "
        "Run it again (Parse, then Save to Steam) to apply it.",
        "SUCCESS",
    )
    return {"updated": updated, "backup": str(backup)}
