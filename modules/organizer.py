import shutil
from pathlib import Path

from config import EMUDECK_ROOT
from modules.hashing import hash_file
from modules.dat_validation import validate_hashes
from modules.detection import detect_system, clean_name, get_disc_number
from modules.m3u import append_to_m3u
from modules.artwork import fetch_artwork

ARCADE_SYSTEMS = ["fbneo", "arcade"]

def process_roms(input_folder, logger, status):
    processed_systems = set()
    seen_hashes = {}
    total_files = sum(1 for _ in Path(input_folder).rglob("*") if _.is_file())
    processed_count = 0

    for file in Path(input_folder).rglob("*"):
        if not file.is_file():
            continue

        system = detect_system(file)

        if not system:
            continue

        hashes = hash_file(file)

        if hashes["md5"] in seen_hashes:
            logger(f"[DUPLICATE] {file}")
            status["duplicates"] += 1
            continue

        seen_hashes[hashes["md5"]] = file

        verified_name = validate_hashes(hashes)

        if system in ARCADE_SYSTEMS:
            game_name = file.stem
        else:
            game_name = verified_name or clean_name(file.stem)

        system_folder = EMUDECK_ROOT / system
        system_folder.mkdir(parents=True, exist_ok=True)

        game_folder = system_folder / game_name
        game_folder.mkdir(exist_ok=True)

        destination = game_folder / file.name

        shutil.move(str(file), str(destination))

        disc = get_disc_number(file.stem)

        if disc:
            append_to_m3u(game_folder, game_name, destination.name)

        (game_folder / ".hidden").touch(exist_ok=True)

        fetch_artwork(game_name, game_folder, logger)
        status["artwork_downloads"] += 1

        processed_count += 1
        status["roms_processed"] += 1
        status["progress"] = int((processed_count / total_files) * 100) if total_files > 0 else 100

        if verified_name:
            status["dat_matches"] += 1

        processed_systems.add(system)

    return processed_systems