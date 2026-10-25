import os
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from flask import Flask, render_template, request, jsonify
from pathlib import Path
from datetime import datetime

from modules import esde, settings
from modules.artwork import fetch_artwork
from modules.cache import LEFT_IN_PLACE, FileCache
from modules.library import list_library, pending_games, system_folders
from modules.media import media_coverage, steam_artwork_root
from modules.srm import configure_srm
from modules.organizer import process_roms, repair_playlists, sort_by_priority
from modules.scraper import run_skyscraper
from modules.logging_utils import AppLogger
from modules.dat_validation import fetch_latest_dats, load_dat_files
from config import DAT_DIR, SYSTEM_MAP

app = Flask(__name__)

app_logger = AppLogger()

# Log lines sent to the page with each status poll
LOG_TAIL = 500

STATUS_COUNTERS = (
    "roms_processed",
    "duplicates",
    "dat_matches",
    "serial_matches",
    "name_matches",
    "artwork_downloads",
    "unsorted",
    "skipped",
)

# Live state of the current (or last) organise run, polled by the page
status = {
    "running": False,
    "phase": "idle",
    "dry_run": True,
    "progress": 0,
    "files_total": 0,
    "files_checked": 0,
    "current_file": "",
    # What's happening to the current file or system, e.g. "checking 1.2 of 4.3 GB"
    "current_detail": "",
    # Seconds since the epoch: when the run started, and when progress last moved
    "started_at": None,
    "updated_at": None,
    # Set by POST /api/stop; the run stops at the next file, system or game
    "cancel_requested": False,
    **{counter: 0 for counter in STATUS_COUNTERS},
    # Images saved this run, per media type ("covers", "steam_tall", ...)
    "media_downloads": {},
    "unsorted_files": [],
    # Games that matched no DAT entry, by why: {reason: count}
    "dat_misses": {},
    # Summary shown on the page once a run finishes
    "report": None,
}

# Only one organise run at a time
organise_lock = threading.Lock()

# Games given artwork at once; each makes a few small requests
ARTWORK_WORKERS = 4

# Checksums and last outcomes of files in the ROM folder, shared by every run
file_cache = FileCache()

# Detection statistics tracking
detection_stats = {
    "total_games": 0,
    "games_by_system": {},
    "last_scan": None,
    "supported_systems": len(SYSTEM_MAP),
    "media": None,
    # Systems the last scan was limited to; None means all of them
    "scanned_systems": None,
}


# Files in the ROM folder that still need organising, from the last check
new_roms = {"rom_root": None, "new": [], "needs_attention": [], "checked": None}


def check_new_roms(rom_root):
    """
    Finds the games dropped into the ROM folder that still need organising.
    Ones a run already tried and left in place (unsorted, skipped or a
    duplicate) are listed apart, with why, until they change.
    """
    rom_root = Path(rom_root)
    waiting = []
    attention = []

    for path in pending_games(rom_root, file_cache):
        name = path.relative_to(rom_root).as_posix()
        entry = file_cache.get(path)
        if entry and entry.get("outcome") in LEFT_IN_PLACE:
            attention.append({"path": name, "reason": entry["outcome"]})
        else:
            waiting.append(name)

    new_roms.update(
        rom_root=str(rom_root),
        new=waiting,
        needs_attention=attention,
        checked=datetime.now().isoformat(),
    )
    return new_roms


def new_roms_summary():
    return {
        **new_roms,
        "total": len(new_roms["new"]) + len(new_roms["needs_attention"]),
        "all_organised": not new_roms["new"] and not new_roms["needs_attention"],
    }


def update_detection_stats(rom_root, systems=None):
    games = list_library(rom_root, systems)
    detection_stats["games_by_system"] = dict(
        Counter(system for system, _ in games).most_common()
    )
    detection_stats["total_games"] = len(games)
    detection_stats["media"] = media_coverage(games, esde.media_root(), steam_artwork_root())
    detection_stats["scanned_systems"] = sorted(systems) if systems else None
    detection_stats["last_scan"] = datetime.now().isoformat()
    check_new_roms(rom_root)


def build_report(placed, dry_run):
    """Summary of a finished organise run for the page's report charts."""
    return {
        "dry_run": dry_run,
        "finished": datetime.now().isoformat(),
        "outcomes": {
            "Organised": status["roms_processed"],
            "Unsorted": status["unsorted"],
            "Skipped": status["skipped"],
            "Duplicates": status["duplicates"],
        },
        "dat_matches": status["dat_matches"],
        "serial_matches": status["serial_matches"],
        "name_matches": status["name_matches"],
        # Why the rest matched nothing: {reason: games}
        "dat_misses": dict(status["dat_misses"]),
        "by_system": dict(Counter(game["system"] for game in placed).most_common()),
        "unsorted_files": list(status["unsorted_files"]),
        "media": None
        if dry_run
        else media_coverage(
            [(game["system"], game["path"]) for game in placed],
            esde.media_root(),
            steam_artwork_root(),
        ),
    }


@app.route("/api/status")
def api_status():
    """Return comprehensive status of API connections, DAT files, and detection stats"""
    try:
        # Library stats, API connections and DAT files on disk
        api_status_data = {
            "timestamp": datetime.now().isoformat(),
            "detection": {
                "total_games": detection_stats["total_games"],
                "supported_systems": detection_stats["supported_systems"],
                "detected_systems": len(detection_stats["games_by_system"]),
                "games_by_system": detection_stats["games_by_system"],
                "media": detection_stats["media"],
                "last_scan": detection_stats["last_scan"],
                "scanned_systems": detection_stats["scanned_systems"],
                "to_organise": new_roms_summary()["total"],
            },
            "apis": {
                "steamgriddb": {
                    "enabled": settings.get("enable_steamgriddb"),
                    "configured": bool(settings.get("steamgriddb_api")),
                },
                "screenscraper": {
                    "enabled": settings.get("enable_screenscraper"),
                    "configured": bool(
                        settings.get("screenscraper_user")
                        and settings.get("screenscraper_password")
                    ),
                },
            },
            "dats": {"directory": str(DAT_DIR), "total_files": 0, "files": []},
        }

        # Scan DAT directory for downloaded files
        if DAT_DIR.exists():
            dat_files = list(DAT_DIR.glob("*.dat"))
            api_status_data["dats"]["total_files"] = len(dat_files)

            for dat_file in sorted(dat_files):
                file_stat = dat_file.stat()
                api_status_data["dats"]["files"].append(
                    {
                        "name": dat_file.name,
                        "size_kb": round(file_stat.st_size / 1024, 2),
                        "modified": datetime.fromtimestamp(
                            file_stat.st_mtime
                        ).isoformat(),
                    }
                )

        return jsonify(api_status_data)

    except Exception as e:
        app_logger.error(f"Status API error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/status")
def get_status():
    messages = app_logger.get_messages()
    return jsonify({**status, "log": messages[-LOG_TAIL:], "log_total": len(messages)})


@app.route("/api/scan-games", methods=["POST"])
def scan_games():
    """Scan the ROM library and count games by system"""
    try:
        body = request.get_json(silent=True) or {}
        requested = body.get("rom_root") or body.get("emudeck_path")
        scan_root = Path(requested) if requested else esde.rom_root()
        systems = body.get("systems") or None

        if systems is not None and (
            not isinstance(systems, list) or not all(isinstance(s, str) for s in systems)
        ):
            return (
                jsonify({"success": False, "error": "systems must be a list of system names"}),
                400,
            )

        if not scan_root.is_dir():
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"ROM folder not found: {scan_root}",
                        "stats": detection_stats,
                    }
                ),
                404,
            )

        update_detection_stats(scan_root, systems)

        return jsonify(
            {
                "success": True,
                "scanned_systems": detection_stats["scanned_systems"],
                "total_games": detection_stats["total_games"],
                "to_organise": new_roms_summary()["total"],
                "systems_detected": len(detection_stats["games_by_system"]),
                "games_by_system": detection_stats["games_by_system"],
                "media": detection_stats["media"],
                "timestamp": detection_stats["last_scan"],
            }
        )

    except Exception as e:
        app_logger.error(f"Game scan error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/systems")
def list_systems():
    """The system folders in a ROM folder, for choosing which ones to scan"""
    requested = request.args.get("rom_root")
    rom_root = Path(requested) if requested else esde.rom_root()

    if not rom_root.is_dir():
        return jsonify({"systems": [], "error": f"ROM folder not found: {rom_root}"}), 404

    return jsonify({"systems": system_folders(rom_root)})


@app.route("/api/new-roms")
def api_new_roms():
    """Check the ROM folder for games dropped in that still need organising"""
    requested = request.args.get("rom_root")
    rom_root = Path(requested) if requested else esde.rom_root()

    if not rom_root.is_dir():
        return jsonify({"error": f"ROM folder not found: {rom_root}"}), 404

    # A run moves files while it goes; report what was found before it started
    if not status["running"]:
        check_new_roms(rom_root)
    return jsonify(new_roms_summary())


def _progress(**fields):
    status.update(fields, updated_at=time.time())


def _stopping():
    return status["cancel_requested"]


def _scrape(systems, rom_root):
    for index, system in enumerate(systems):
        if _stopping():
            return
        _progress(progress=int(index * 100 / len(systems)), current_file=system, current_detail="")
        result = run_skyscraper(
            system,
            app_logger.log,
            rom_root,
            on_output=lambda line: _progress(current_detail=line[:120]),
            should_stop=_stopping,
        )
        if result is None:
            return


def _download_artwork(games):
    """Downloads artwork for several games at once, counting what each saved."""
    media_root = esde.media_root()
    steam_root = steam_artwork_root()

    with ThreadPoolExecutor(max_workers=ARTWORK_WORKERS) as pool:
        futures = {
            pool.submit(fetch_artwork, game, media_root, steam_root, app_logger.log): game
            for game in games
        }
        for done, future in enumerate(as_completed(futures), start=1):
            saved = future.result()
            if saved:
                status["artwork_downloads"] += 1
            for media_type in saved:
                downloads = status["media_downloads"]
                downloads[media_type] = downloads.get(media_type, 0) + 1
            _progress(
                progress=int(done * 100 / len(games)),
                current_file=Path(futures[future]["path"]).name,
                current_detail=f"{done} of {len(games)} games",
            )
            if _stopping():
                pool.shutdown(cancel_futures=True)
                break


def run_organise(input_path, rom_root, dry_run, force=False):
    """
    Organise, then scrape game data and download covers. Runs in a worker
    thread. With force, the cache is ignored and every game in the ROM folder
    is organised again: a real run forgets what it knew, a dry run only
    previews that.
    """
    try:
        _progress(phase="finding", current_detail="looking for new games")
        cache = file_cache
        # Organising the ROM folder itself only touches what still needs it
        files = None
        if Path(input_path).resolve() == Path(rom_root).resolve():
            if force and dry_run:
                cache = None
                app_logger.info("Re-organise everything (preview): every game is checked again")
            elif force:
                forgotten = file_cache.forget_under(rom_root)
                app_logger.info(f"Re-organise everything: forgot what was known about {forgotten} files")
            files = [
                file
                for game, tracks in pending_games(rom_root, cache).items()
                for file in [game, *tracks]
            ]
        _progress(phase="organising", current_detail="")
        if files is not None:
            repair_playlists(rom_root, app_logger.log, dry_run)
        placed = process_roms(
            input_path,
            app_logger.log,
            status,
            dry_run=dry_run,
            rom_root=rom_root,
            files=files,
            cache=cache,
        )

        if dry_run:
            app_logger.info("Dry run: no files were moved, nothing was scraped")
        elif placed:
            # The priority systems get their game data and artwork first
            order = sort_by_priority({game["system"] for game in placed})
            placed.sort(key=lambda game: order.index(game["system"]))

            _progress(phase="scraping", progress=0)
            _scrape(order, rom_root)

            if not _stopping():
                _progress(phase="artwork", progress=0, current_file="", current_detail="")
                _download_artwork(placed)

            update_detection_stats(rom_root)

        check_new_roms(rom_root)
        status["report"] = build_report(placed, dry_run)
        if _stopping():
            _progress(phase="stopped")
            app_logger.warning("Stopped: games not reached yet are still listed as new")
            return
        _progress(phase="done", progress=100)
        app_logger.success(
            f"COMPLETE: {status['roms_processed']} games "
            f"{'would be ' if dry_run else ''}organised, "
            f"{status['unsorted']} unsorted, {status['skipped']} skipped, "
            f"{status['duplicates']} duplicates"
        )

    except Exception as e:
        status["phase"] = "failed"
        app_logger.error(f"Organise failed: {e}")

    finally:
        try:
            file_cache.save()
        except OSError as e:
            app_logger.warning(f"Couldn't save the file cache: {e}")
        status["running"] = False
        status["current_file"] = ""
        status["current_detail"] = ""
        organise_lock.release()


@app.route("/api/organise", methods=["POST"])
def start_organise():
    body = request.get_json(silent=True) or {}
    rom_root = str(body.get("rom_root", "")).strip() or str(esde.rom_root())
    # Without an import folder, new games dropped into the ROM folder are organised
    input_path = str(body.get("input_path", "")).strip() or rom_root
    dry_run = bool(body.get("dry_run", True))
    # Forget what's been organised and work through the whole ROM folder again
    force = bool(body.get("force", False))

    if not Path(rom_root).is_dir():
        return jsonify({"error": f"ROM folder not found: {rom_root}"}), 400

    if not Path(input_path).is_dir():
        return jsonify({"error": f"Import folder not found: {input_path}"}), 400

    if not organise_lock.acquire(blocking=False):
        return jsonify({"error": "An organise run is already in progress"}), 409

    app_logger.clear()
    status.update(
        running=True,
        phase="starting",
        dry_run=dry_run,
        progress=0,
        files_total=0,
        files_checked=0,
        current_file="",
        current_detail="",
        started_at=time.time(),
        updated_at=time.time(),
        cancel_requested=False,
        media_downloads={},
        unsorted_files=[],
        dat_misses={},
        report=None,
        **{counter: 0 for counter in STATUS_COUNTERS},
    )
    action = "Dry run" if dry_run else "Organising"
    if Path(input_path).resolve() == Path(rom_root).resolve():
        app_logger.info(f"{action}: new games in {rom_root}")
    else:
        app_logger.info(f"{action}: {input_path} -> {rom_root}")

    threading.Thread(
        target=run_organise, args=(input_path, rom_root, dry_run, force), daemon=True
    ).start()

    return jsonify({"started": True}), 202


@app.route("/api/stop", methods=["POST"])
def stop_organise():
    """Ask the current run to stop at the next file, system or game"""
    if not status["running"]:
        return jsonify({"error": "No organise run is going"}), 409

    status["cancel_requested"] = True
    app_logger.warning("Stopping after the current step...")
    return jsonify({"stopping": True}), 202


@app.route("/api/steam-rom-manager", methods=["POST"])
def setup_steam_rom_manager():
    """Point Steam ROM Manager's parsers at the app's Steam artwork."""
    result = configure_srm(steam_artwork_root(), app_logger.log)
    return jsonify(result), 404 if "error" in result else 200


@app.route("/")
def index():
    return render_template(
        "index.html",
        rom_root=esde.rom_root(),
        status=status,
    )


# Server settings only change when the app restarts
SERVER_SETTINGS_AT_START = {
    field.key: settings.get(field.key) for field in settings.FIELDS if field.restart
}


def settings_response():
    return {
        "settings": settings.public_values(),
        "restart_needed": any(
            settings.get(key) != value for key, value in SERVER_SETTINGS_AT_START.items()
        ),
        "load_error": settings.load_error,
    }


@app.route("/settings")
def settings_page():
    groups = {}
    for field in settings.FIELDS:
        groups.setdefault(field.group, []).append(field)
    return render_template("settings.html", groups=groups, **settings_response())


@app.route("/api/settings", methods=["GET", "POST"])
def api_settings():
    """Read the settings, or save changes to them"""
    if request.method == "GET":
        return jsonify(settings_response())

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return jsonify({"errors": {"": "Send the settings as a JSON object."}}), 400

    try:
        errors = settings.save(body)
    except OSError as e:
        app_logger.error(f"Couldn't save settings: {e}")
        return jsonify({"errors": {"": f"Couldn't save settings: {e}"}}), 500

    if errors:
        return jsonify({"errors": errors}), 400

    app_logger.info("Settings saved")
    return jsonify({"saved": True, **settings_response()})


@app.route("/logs")
def view_logs():
    return render_template("logs.html", log="\n".join(app_logger.get_messages()))


def initialize_dat_files():
    if settings.load_error:
        app_logger.warning(settings.load_error)

    # Attempt to fetch DATs from libretro first, fall back to local DATs
    try:
        app_logger.info("Initializing DAT files: fetching latest DATs if available...")
        fetch_latest_dats(app_logger.log)
        load_dat_files(app_logger.log)
        app_logger.success("DAT initialization complete (libretro/local fallback)")
    except Exception as e:
        app_logger.error(f"DAT initialization failed: {e}")

    # Scan for games on startup (now with DATs loaded if available)
    try:
        app_logger.info("Scanning for games...")
        rom_root = esde.rom_root()
        if rom_root.is_dir():
            update_detection_stats(rom_root)
            app_logger.success(
                f"Found {detection_stats['total_games']} games across {len(detection_stats['games_by_system'])} systems"
            )
            waiting = new_roms_summary()["total"]
            if waiting:
                app_logger.info(f"{waiting} new games in the ROM folder need organising")
        else:
            app_logger.warning(
                f"ROM folder not found: {rom_root}; skipping startup scan"
            )
    except Exception as e:
        app_logger.error(f"Game scan on startup failed: {e}")


if __name__ == "__main__":
    # The debug reloader runs this module twice: once in a watcher process and
    # again in the child that serves requests. Only the child needs the DATs.
    debug = settings.get("debug")
    if not debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        initialize_dat_files()
    app.run(host=settings.get("host"), port=settings.get("port"), debug=debug)
