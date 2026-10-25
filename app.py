import os
import threading
from collections import Counter

from flask import Flask, render_template, request, jsonify
from pathlib import Path
from datetime import datetime

from modules import esde, settings
from modules.artwork import fetch_artwork
from modules.library import list_library, system_folders
from modules.media import media_coverage, steam_artwork_root
from modules.srm import configure_srm
from modules.organizer import process_roms
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
    **{counter: 0 for counter in STATUS_COUNTERS},
    # Images saved this run, per media type ("covers", "steam_tall", ...)
    "media_downloads": {},
    "unsorted_files": [],
    # Summary shown on the page once a run finishes
    "report": None,
}

# Only one organise run at a time
organise_lock = threading.Lock()

# Detection statistics tracking
detection_stats = {
    "total_games": 0,
    "games_by_system": {},
    "last_scan": None,
    "supported_systems": len(SYSTEM_MAP),
    "undetected_files": [],
    "media": None,
    # Systems the last scan was limited to; None means all of them
    "scanned_systems": None,
}


def update_detection_stats(rom_root, systems=None):
    games, undetected = list_library(rom_root, systems)
    detection_stats["games_by_system"] = dict(
        Counter(system for system, _ in games).most_common()
    )
    detection_stats["undetected_files"] = undetected
    detection_stats["total_games"] = len(games)
    detection_stats["media"] = media_coverage(games, esde.media_root(), steam_artwork_root())
    detection_stats["scanned_systems"] = sorted(systems) if systems else None
    detection_stats["last_scan"] = datetime.now().isoformat()


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
                "undetected_count": len(detection_stats["undetected_files"]),
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
                "undetected": len(detection_stats["undetected_files"]),
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


def run_organise(input_path, rom_root, dry_run):
    """Organise, then scrape game data and download covers. Runs in a worker thread."""
    try:
        status["phase"] = "organising"
        placed = process_roms(
            input_path, app_logger.log, status, dry_run=dry_run, rom_root=rom_root
        )

        if dry_run:
            app_logger.info("Dry run: no files were moved, nothing was scraped")
        elif placed:
            systems = sorted({game["system"] for game in placed})

            status["phase"] = "scraping"
            for index, system in enumerate(systems):
                status["progress"] = int(index * 100 / len(systems))
                status["current_file"] = system
                if run_skyscraper(system, app_logger.log, rom_root) is None:
                    break

            status["phase"] = "artwork"
            media_root = esde.media_root()
            steam_root = steam_artwork_root()
            for index, game in enumerate(placed):
                status["progress"] = int(index * 100 / len(placed))
                status["current_file"] = Path(game["path"]).name
                saved = fetch_artwork(game, media_root, steam_root, app_logger.log)
                if saved:
                    status["artwork_downloads"] += 1
                for media_type in saved:
                    downloads = status["media_downloads"]
                    downloads[media_type] = downloads.get(media_type, 0) + 1

            update_detection_stats(rom_root)

        status["report"] = build_report(placed, dry_run)
        status["phase"] = "done"
        status["progress"] = 100
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
        status["running"] = False
        status["current_file"] = ""
        organise_lock.release()


@app.route("/api/organise", methods=["POST"])
def start_organise():
    body = request.get_json(silent=True) or {}
    input_path = str(body.get("input_path", "")).strip()
    rom_root = str(body.get("rom_root", "")).strip() or str(esde.rom_root())
    dry_run = bool(body.get("dry_run", True))

    # An empty path would resolve to the app's own folder
    if not input_path or not Path(input_path).is_dir():
        return jsonify({"error": f"Import folder not found: {input_path or '(empty)'}"}), 400

    if not Path(rom_root).is_dir():
        return jsonify({"error": f"ROM folder not found: {rom_root}"}), 400

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
        media_downloads={},
        unsorted_files=[],
        report=None,
        **{counter: 0 for counter in STATUS_COUNTERS},
    )
    app_logger.info(
        f"{'Dry run' if dry_run else 'Organising'}: {input_path} -> {rom_root}"
    )

    threading.Thread(
        target=run_organise, args=(input_path, rom_root, dry_run), daemon=True
    ).start()

    return jsonify({"started": True}), 202


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
