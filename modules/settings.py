"""
User settings, edited on the Settings page and kept in two files in the app
folder:

- settings.json, tracked in git: everything except account details
- settings.local.json, ignored by git: API keys, passwords and user names

Modules read settings when they need them (settings.get(...)), so changes
apply straight away; server settings apply on the next start.
"""

import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = APP_DIR / "settings.json"
LOCAL_SETTINGS_FILE = APP_DIR / "settings.local.json"

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
    # Account details kept out of git in settings.local.json; secrets always are
    local: bool = False


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
    Field("screenscraper_user", "ScreenScraper user name", "text", "", "Game data", local=True),
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
LOCAL_KEYS = {field.key for field in FIELDS if field.local or field.kind == "secret"}

# The settings in use, updated in place by load() and save()
current = dict(DEFAULTS)
# Why a settings file couldn't be read, shown on the Settings page
load_error = None


def get(key):
    return current[key]


def path(key):
    """A path setting with ~ expanded, or None when it's blank."""
    value = current[key]
    return Path(value).expanduser() if value else None


def _read(settings_file):
    """Returns (values, problem) from one settings file. A missing file has no values."""
    try:
        stored = json.loads(settings_file.read_text())
    except FileNotFoundError:
        return {}, None
    except (OSError, ValueError) as e:
        return {}, f"Couldn't read {settings_file.name}, so defaults are in use for it: {e}"

    values, errors = _validate(stored if isinstance(stored, dict) else {})
    if errors or not isinstance(stored, dict):
        return values, f"Some settings in {settings_file.name} were invalid and defaults are in use for them."
    return values, None


def load():
    """Reads settings.json, then settings.local.json, over the defaults."""
    global load_error

    current.clear()
    current.update(DEFAULTS)
    problems = []

    for settings_file in (SETTINGS_FILE, LOCAL_SETTINGS_FILE):
        values, problem = _read(settings_file)
        current.update(values)
        if problem:
            problems.append(problem)

    load_error = " ".join(problems) or None
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
    Validates updates, saves them and applies them: account details to
    settings.local.json, everything else to settings.json. A secret sent as
    None is left as it is. Returns {key: message} for invalid settings, in
    which case nothing is saved.
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

    # Account details first, so a failed write can't leave them only in memory
    _write(LOCAL_SETTINGS_FILE, {key: merged[key] for key in sorted(LOCAL_KEYS)}, 0o600)
    _write(SETTINGS_FILE, {key: value for key, value in merged.items() if key not in LOCAL_KEYS}, 0o644)
    current.update(values)
    return {}


def _write(settings_file, values, mode):
    # Written to a temporary file first so a failed write never leaves half a file
    settings_file.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(dir=settings_file.parent, prefix=".settings-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as file:
            json.dump(values, file, indent=2)
            file.write("\n")
        os.chmod(temporary, mode)
        os.replace(temporary, settings_file)
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
