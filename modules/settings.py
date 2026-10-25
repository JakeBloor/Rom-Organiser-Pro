"""
User settings, kept in settings.json in the app folder and edited on the
Settings page. Modules read them when they need them (settings.get(...)), so
changes apply straight away; server settings apply on the next start.

settings.json is tracked in git, account details included.
"""

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

SETTINGS_FILE = Path(__file__).resolve().parent.parent / "settings.json"

LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}


@dataclass(frozen=True)
class Field:
    key: str
    label: str
    kind: str  # "text", "path", "secret", "bool", "int" or "choice"
    default: object
    group: str
    help: str = ""
    choices: tuple = ()
    minimum: int = 0
    maximum: int = 0
    restart: bool = False


FIELDS = (
    Field("esde_home", "ES-DE folder", "path", "~/ES-DE", "Folders",
          "ES-DE's own folder. Its settings say where your ROMs and media are."),
    Field("default_rom_folder", "Default ROM folder", "path", "~/Emulation/roms", "Folders",
          "Used when ES-DE's settings don't name a ROM folder."),
    Field("steam_artwork_dir", "Steam artwork folder", "path", "", "Folders",
          "Leave blank for a steam-artwork folder next to ES-DE's media folder."),
    Field("srm_config", "Steam ROM Manager settings file", "path",
          "~/.config/steam-rom-manager/userData/userConfigurations.json", "Folders"),
    Field("multi_file_layout", "Multi-file game layout", "choice", "shared", "Folders",
          "Shared suits ES-DE and Steam. ES-DE folders only suit ES-DE.",
          choices=(("shared", "Shared (ES-DE and Steam)"), ("esde", "ES-DE folders"))),
    Field("enable_libretro_thumbnails", "Download libretro thumbnails", "bool", True, "Artwork",
          "Covers, screenshots and title screens. No account needed."),
    Field("enable_steamgriddb", "Download from SteamGridDB", "bool", True, "Artwork",
          "Steam artwork, plus ES-DE marquees and fan art."),
    Field("steamgriddb_api", "SteamGridDB API key", "secret", "", "Artwork",
          "Free from steamgriddb.com, under Preferences > API."),
    Field("enable_screenscraper", "Scrape game data with Skyscraper", "bool", True, "Game data",
          "Runs after organising when Skyscraper is installed."),
    Field("screenscraper_user", "ScreenScraper user name", "text", "", "Game data"),
    Field("screenscraper_password", "ScreenScraper password", "secret", "", "Game data"),
    Field("scraper_region", "Preferred region", "text", "us", "Game data",
          "For box art and data, e.g. us, eu, jp, wor."),
    Field("scraper_language", "Preferred language", "text", "en", "Game data",
          "For descriptions, e.g. en, fr, de."),
    Field("scraper_threads", "Download threads", "int", 4, "Game data",
          "ScreenScraper limits threads by account level.", minimum=1, maximum=32),
    Field("host", "Listen address", "text", "127.0.0.1", "Server",
          "127.0.0.1 for this device only, 0.0.0.0 for your whole network.", restart=True),
    Field("port", "Port", "int", 8181, "Server", minimum=1, maximum=65535, restart=True),
    Field("debug", "Debug mode", "bool", False, "Server",
          "Only for development, and only with a 127.0.0.1 listen address.", restart=True),
)

FIELDS_BY_KEY = {field.key: field for field in FIELDS}
DEFAULTS = {field.key: field.default for field in FIELDS}

# The settings in use, updated in place by load() and save()
current = dict(DEFAULTS)
# Why settings.json couldn't be read, shown on the Settings page
load_error = None


def get(key):
    return current[key]


def path(key):
    """A path setting with ~ expanded, or None when it's blank."""
    value = current[key]
    return Path(value).expanduser() if value else None


def load():
    """Reads settings.json over the defaults. A missing file just means defaults."""
    global load_error

    current.clear()
    current.update(DEFAULTS)
    load_error = None

    try:
        stored = json.loads(SETTINGS_FILE.read_text())
    except FileNotFoundError:
        return current
    except (OSError, ValueError) as e:
        load_error = f"Couldn't read {SETTINGS_FILE.name}, so defaults are in use: {e}"
        return current

    values, errors = _validate(stored if isinstance(stored, dict) else {})
    current.update(values)
    if errors or not isinstance(stored, dict):
        load_error = f"Some settings in {SETTINGS_FILE.name} were invalid and defaults are in use for them."
    return current


def _validate(updates):
    """Returns (values, errors) for the known keys in updates."""
    values = {}
    errors = {}

    for key, value in updates.items():
        field = FIELDS_BY_KEY.get(key)
        if field is None:
            continue

        if field.kind == "bool":
            if isinstance(value, bool):
                values[key] = value
            else:
                errors[key] = "Must be on or off."
        elif field.kind == "int":
            try:
                number = int(value)
            except (TypeError, ValueError):
                errors[key] = "Must be a whole number."
                continue
            if isinstance(value, bool) or not field.minimum <= number <= field.maximum:
                errors[key] = f"Must be between {field.minimum} and {field.maximum}."
            else:
                values[key] = number
        elif not isinstance(value, str):
            errors[key] = "Must be text."
        elif field.kind == "choice" and value not in dict(field.choices):
            errors[key] = "Pick one of the listed options."
        elif field.key == "host" and not value.strip():
            errors[key] = "Can't be blank."
        else:
            values[key] = value.strip()

    return values, errors


def save(updates):
    """
    Validates updates, writes them to settings.json and applies them. A secret
    sent as None is left as it is. Returns {key: message} for invalid
    settings, in which case nothing is saved.
    """
    updates = {
        key: value
        for key, value in updates.items()
        if not (key in FIELDS_BY_KEY and FIELDS_BY_KEY[key].kind == "secret" and value is None)
    }
    values, errors = _validate(updates)

    merged = {**current, **values}
    if merged["debug"] and merged["host"] not in LOOPBACK_HOSTS:
        errors["debug"] = (
            "Debug mode lets anyone who can open the page run code, so it only "
            "works with a 127.0.0.1 listen address."
        )

    if errors:
        return errors

    _write(merged)
    current.update(values)
    return {}


def _write(values):
    # Written to a temporary file first so a failed write never leaves half a file
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=SETTINGS_FILE.parent, prefix=".settings-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as file:
            json.dump(values, file, indent=2)
        os.chmod(temporary, 0o600)
        os.replace(temporary, SETTINGS_FILE)
    except BaseException:
        os.unlink(temporary)
        raise


def public_values():
    """Settings for the page. Secrets are never sent back, only whether they're set."""
    return {
        field.key: bool(current[field.key]) if field.kind == "secret" else current[field.key]
        for field in FIELDS
    }


load()
