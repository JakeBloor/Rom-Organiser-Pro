import re
import threading
from pathlib import Path
from urllib.parse import quote

import requests

from config import DAT_SYSTEM_IDS, canonical_system
from modules import settings
from modules.detection import clean_name
from modules.media import (
    STEAM_IMAGE_TYPES,
    esde_media_path,
    has_esde_media,
    has_steam_artwork,
    steam_artwork_path,
)

API_BASE = "https://www.steamgriddb.com/api/v2"
LIBRETRO_BASE = "https://thumbnails.libretro.com"

# ES-DE media folder -> libretro thumbnail folder
LIBRETRO_TYPES = {
    "covers": "Named_Boxarts",
    "screenshots": "Named_Snaps",
    "titlescreens": "Named_Titles",
}
# libretro replaces these characters in game names with "_"
LIBRETRO_UNSAFE = re.compile(r"[&*/:`<>?\\|]")
# A system's libretro folder when the game didn't match a DAT: the first DAT
# name mapped to it, e.g. "nds" -> "Nintendo - Nintendo DS"
LIBRETRO_SYSTEM_NAMES = {
    system: name for name, system in reversed(list(DAT_SYSTEM_IDS.items()))
}

# Steam ROM Manager image kind -> SteamGridDB endpoint and filters
STEAMGRIDDB_QUERIES = {
    "tall": ("grids", {"dimensions": "600x900", "mimes": "image/png,image/jpeg"}),
    "long": ("grids", {"dimensions": "920x430,460x215", "mimes": "image/png,image/jpeg"}),
    "hero": ("heroes", {"mimes": "image/png,image/jpeg"}),
    "logo": ("logos", {"mimes": "image/png"}),
    "icon": ("icons", {"mimes": "image/png"}),
}
# ES-DE media also filled from SteamGridDB when libretro has nothing
STEAMGRIDDB_FOR_ESDE = {"covers": "tall", "marquees": "logo", "fanart": "hero"}


# (connect, read) seconds: a slow server shouldn't hold a run up for long
TIMEOUT = (5, 15)
# Artwork is downloaded for several games at once, each worker with its own
# connection pool (requests sessions aren't safe to share between threads)
_local = threading.local()


def _get(url, **kwargs):
    session = getattr(_local, "session", None)
    if session is None:
        session = _local.session = requests.Session()
    return session.get(url, timeout=TIMEOUT, **kwargs)


def _suffix(url):
    return ".jpg" if Path(url.split("?")[0]).suffix.lower() in (".jpg", ".jpeg") else ".png"


def _save(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)


def _fetch_libretro(game, media_root, logger):
    folder = game.get("dat_title") or LIBRETRO_SYSTEM_NAMES.get(canonical_system(game["system"]))
    if not folder:
        return []

    saved = []

    for media_type, thumbnail_kind in LIBRETRO_TYPES.items():
        if has_esde_media(media_root, game["system"], game["path"], media_type):
            continue

        for name in game["names"]:
            url = (
                f"{LIBRETRO_BASE}/{quote(folder)}/{thumbnail_kind}/"
                f"{quote(LIBRETRO_UNSAFE.sub('_', name))}.png"
            )
            try:
                response = _get(url)
            except requests.RequestException as e:
                logger(f"[ARTWORK ERROR] libretro thumbnails: {e}", "WARNING")
                return saved

            if response.status_code == 200:
                _save(
                    esde_media_path(media_root, game["system"], game["path"], media_type, ".png"),
                    response.content,
                )
                saved.append(media_type)
                break

    if saved:
        logger(f"[ARTWORK] libretro {', '.join(saved)} for {game['names'][0]}")
    return saved


def _fetch_steamgriddb(game, media_root, steam_root, logger):
    system, game_path = game["system"], game["path"]

    steam_wanted = [
        kind for kind in STEAM_IMAGE_TYPES
        if not has_steam_artwork(steam_root, system, game_path, kind)
    ]
    esde_wanted = {
        media_type: kind for media_type, kind in STEAMGRIDDB_FOR_ESDE.items()
        if not has_esde_media(media_root, system, game_path, media_type)
    }
    kinds = [k for k in STEAM_IMAGE_TYPES if k in steam_wanted or k in esde_wanted.values()]
    if not kinds:
        return []

    api_key = settings.get("steamgriddb_api")
    if not api_key:
        logger("[ARTWORK] Missing SteamGridDB API key")
        return []

    search_name = clean_name(game["title"])
    headers = {"Authorization": f"Bearer {api_key}"}
    saved = []

    try:
        search = _get(
            f"{API_BASE}/search/autocomplete/{quote(search_name, safe='')}",
            headers=headers,
        )
        search.raise_for_status()
        results = search.json().get("data") or []

        if not results:
            logger(f"[ARTWORK] No results for {search_name}")
            return []

        game_id = results[0]["id"]

        for kind in kinds:
            endpoint, params = STEAMGRIDDB_QUERIES[kind]
            listing = _get(
                f"{API_BASE}/{endpoint}/game/{game_id}",
                headers=headers,
                params={**params, "types": "static"},
            )
            listing.raise_for_status()
            images = listing.json().get("data") or []

            if not images:
                continue

            img_url = images[0]["url"]
            img = _get(img_url)
            img.raise_for_status()
            suffix = _suffix(img_url)

            if kind in steam_wanted:
                _save(steam_artwork_path(steam_root, system, game_path, kind, suffix), img.content)
                saved.append(f"steam_{kind}")

            for media_type, source_kind in esde_wanted.items():
                if source_kind == kind:
                    _save(esde_media_path(media_root, system, game_path, media_type, suffix), img.content)
                    saved.append(media_type)

    except (requests.RequestException, ValueError, KeyError) as e:
        logger(f"[ARTWORK ERROR] {search_name}: {e}", "WARNING")
        return saved

    if saved:
        logger(f"[ARTWORK] SteamGridDB {', '.join(saved)} for {search_name}")
    else:
        logger(f"[ARTWORK] No SteamGridDB images found for {search_name}")
    return saved


def fetch_artwork(game, media_root, steam_root, logger):
    """
    Download any missing images for a placed game (see process_roms): ES-DE
    covers, screenshots and title screens from libretro's thumbnails, which
    match DAT names exactly, then SteamGridDB for anything still missing plus
    ES-DE marquees and fan art and the five Steam ROM Manager image kinds.
    Existing images are never replaced. Returns the media types saved.
    """
    saved = []

    if settings.get("enable_libretro_thumbnails"):
        saved += _fetch_libretro(game, media_root, logger)

    if settings.get("enable_steamgriddb"):
        saved += _fetch_steamgriddb(game, media_root, steam_root, logger)

    return saved
