import requests
from pathlib import Path

from config import (
    STEAMGRIDDB_API,
    ENABLE_STEAMGRIDDB
)

def fetch_artwork(game_name, folder, logger, status=None):
    if not ENABLE_STEAMGRIDDB:
        return

    if not STEAMGRIDDB_API:
        logger("[ARTWORK] Missing SteamGridDB API key")
        return

    cover = folder / "cover.png"

    if cover.exists():
        return

    try:
        headers = {
            "Authorization": f"Bearer {STEAMGRIDDB_API}"
        }

        search = requests.get(
            f"https://www.steamgriddb.com/api/v2/search/autocomplete/{game_name}",
            headers=headers
        ).json()

        if not search.get("data"):
            logger(f"[ARTWORK] No results for {game_name}")
            return

        game_id = search["data"][0]["id"]

        grids = requests.get(
            f"https://www.steamgriddb.com/api/v2/grids/game/{game_id}",
            headers=headers
        ).json().get("data", [])

        if not grids:
            logger(f"[ARTWORK] No grids found for {game_name}")
            return

        img_url = grids[0]["url"]

        img = requests.get(img_url).content

        with open(cover, "wb") as f:
            f.write(img)

        if status:
            status["artwork_downloads"] += 1

        logger(f"[ARTWORK] Downloaded for {game_name}")

    except Exception as e:
        logger(f"[ARTWORK ERROR] {e}")