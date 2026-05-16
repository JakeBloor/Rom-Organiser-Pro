from flask import Flask, render_template, request, jsonify
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from modules.organizer import process_roms
from modules.scraper import run_skyscraper
from modules.logging_utils import AppLogger
from modules.detection import detect_system
from modules.dat_validation import fetch_latest_dats, load_dat_files
from config import (
    DAT_DIR,
    EMUDECK_ROOT,
    SYSTEM_MAP,
    ENABLE_STEAMGRIDDB,
    STEAMGRIDDB_API,
    ENABLE_SCREENSCRAPER,
    SCREENSCRAPER_USER,
    SCREENSCRAPER_PASSWORD,
)

app = Flask(__name__)

# Replace log_output list and logger function with:
app_logger = AppLogger()

status = {
    "progress": 0,
    "roms_processed": 0,
    "duplicates": 0,
    "dat_matches": 0,
    "artwork_downloads": 0,
}

# Detection statistics tracking
detection_stats = {
    "total_games": 0,
    "games_by_system": {},
    "last_scan": None,
    "supported_systems": len(SYSTEM_MAP),
    "undetected_files": [],
}


@app.route("/api/status")
def api_status():
    """Return comprehensive status of API connections, DAT files, and detection stats"""
    try:
        # Get environment-based API configuration
        api_status_data = {
            "timestamp": datetime.now().isoformat(),
            "detection": {
                "total_games": detection_stats["total_games"],
                "supported_systems": detection_stats["supported_systems"],
                "detected_systems": len(detection_stats["games_by_system"]),
                "games_by_system": detection_stats["games_by_system"],
                "last_scan": detection_stats["last_scan"],
                "undetected_count": len(detection_stats["undetected_files"]),
            },
            "apis": {
                "steamgriddb": {
                    "enabled": bool(ENABLE_STEAMGRIDDB),
                    "configured": bool(STEAMGRIDDB_API),
                },
                "screenscraper": {
                    "enabled": bool(ENABLE_SCREENSCRAPER),
                    "configured": bool(SCREENSCRAPER_USER and SCREENSCRAPER_PASSWORD),
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
    return jsonify(status)


@app.route("/api/scan-games", methods=["POST"])
def scan_games():
    """Scan EmuDeck ROM directory and detect all games by system"""
    try:
        detection_stats["games_by_system"] = defaultdict(int)
        detection_stats["undetected_files"] = []

        body = request.get_json(silent=True) or {}
        scan_root = (
            Path(body.get("emudeck_path", ""))
            if body.get("emudeck_path")
            else EMUDECK_ROOT
        )

        if not scan_root.exists():
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f"EmuDeck directory not found: {scan_root}",
                        "stats": detection_stats,
                    }
                ),
                404,
            )

        # Scan all ROM files
        game_count = 0
        undetected_count = 0

        for rom_file in scan_root.rglob("*"):
            if rom_file.is_file():
                # Detect system for this ROM
                system = detect_system(str(rom_file))

                if system:
                    if system not in detection_stats["games_by_system"]:
                        detection_stats["games_by_system"][system] = 0
                    detection_stats["games_by_system"][system] += 1
                    game_count += 1
                else:
                    detection_stats["undetected_files"].append(rom_file.name)
                    undetected_count += 1

        # Sort by count descending
        detection_stats["games_by_system"] = dict(
            sorted(
                detection_stats["games_by_system"].items(),
                key=lambda x: x[1],
                reverse=True,
            )
        )

        detection_stats["total_games"] = game_count
        detection_stats["last_scan"] = datetime.now().isoformat()

        return jsonify(
            {
                "success": True,
                "total_games": game_count,
                "undetected": undetected_count,
                "systems_detected": len(detection_stats["games_by_system"]),
                "games_by_system": dict(detection_stats["games_by_system"]),
                "timestamp": detection_stats["last_scan"],
            }
        )

    except Exception as e:
        app_logger.error(f"Game scan error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        app_logger.clear()  # Changed from log_output = []

        status["progress"] = 0
        status["roms_processed"] = 0
        status["duplicates"] = 0
        status["dat_matches"] = 0
        status["artwork_downloads"] = 0

        input_path = request.form["input_path"]

        systems = process_roms(
            input_path, app_logger.log, status  # Changed from logger
        )

        for system in systems:
            run_skyscraper(system, app_logger.log)  # Changed from logger

        status["progress"] = 100

        app_logger.success("COMPLETE")  # Changed from logger()

    return render_template(
        "index.html",
        log="\n".join(app_logger.get_messages()),  # Changed from log_output
        progress=status["progress"],
        roms_processed=status["roms_processed"],
        duplicates=status["duplicates"],
        dat_matches=status["dat_matches"],
        artwork_downloads=status["artwork_downloads"],
        detection_stats=detection_stats,
    )


@app.route("/logs")
def view_logs():
    return render_template("logs.html", log="\n".join(app_logger.get_messages()))


def initialize_dat_files():
    # Attempt to fetch DATs from libretro first, fall back to local DATs
    try:
        app_logger.info("Initializing DAT files: fetching latest DATs if available...")
        results = fetch_latest_dats(app_logger.log)
        # If fetch_latest_dats loaded DATs it will have called load_dat_files; ensure local load as well
        load_dat_files(app_logger.log)
        app_logger.success("DAT initialization complete (libretro/local fallback)")
    except Exception as e:
        app_logger.error(f"DAT initialization failed: {e}")

    # Scan for games on startup (now with DATs loaded if available)
    try:
        app_logger.info("Scanning for games...")
        if EMUDECK_ROOT.exists():
            for rom_file in EMUDECK_ROOT.rglob("*"):
                if rom_file.is_file():
                    system = detect_system(str(rom_file))
                    if system:
                        detection_stats["games_by_system"].setdefault(system, 0)
                        detection_stats["games_by_system"][system] += 1
                    else:
                        detection_stats["undetected_files"].append(rom_file.name)

            detection_stats["total_games"] = sum(
                detection_stats["games_by_system"].values()
            )
            detection_stats["last_scan"] = datetime.now().isoformat()

            # Sort by count
            detection_stats["games_by_system"] = dict(
                sorted(
                    detection_stats["games_by_system"].items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            )

            app_logger.success(
                f"Found {detection_stats['total_games']} games across {len(detection_stats['games_by_system'])} systems"
            )
    except Exception as e:
        app_logger.error(f"Game scan on startup failed: {e}")


if __name__ == "__main__":
    initialize_dat_files()
    app.run(host="0.0.0.0", port=8181, debug=True)
