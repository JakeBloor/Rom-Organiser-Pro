from flask import Flask, render_template, request, jsonify

from modules.organizer import process_roms
from modules.scraper import run_skyscraper
from modules.dat_validation import load_dat_files, fetch_latest_dats
from modules.logging_utils import AppLogger  # Add this import

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


@app.route("/status")
def get_status():
    return jsonify(status)


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
    )


@app.route("/fetch-dats", methods=["POST"])
def fetch_dats():
    """Fetch latest DAT files"""
    try:
        systems = request.json.get("systems")  # Optional: specific systems
        results = fetch_latest_dats(app_logger.log, systems)

        # Reload DAT database
        load_dat_files(app_logger.log)

        return jsonify(
            {
                "success": True,
                "message": "DATs updated successfully",
                "results": results,
            }
        )
    except Exception as e:
        app_logger.error(f"Failed to fetch DATs: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/logs")
def view_logs():
    return render_template("logs.html", log="\n".join(app_logger.get_messages()))


def initialize_dat_files():
    try:
        app_logger.info("Checking for latest DAT files...")
        fetch_latest_dats(app_logger.log)
    except Exception as e:
        app_logger.error(f"DAT auto-download failed: {e}")

    load_dat_files(app_logger.log)


if __name__ == "__main__":
    initialize_dat_files()
    app.run(host="0.0.0.0", port=8080, debug=True)
