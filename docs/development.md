# Development

## Project layout

```
app.py                 Flask app: routes, the organise worker thread, status and reports
config.py              Fixed tables: systems, extensions, DAT names, layout rules
modules/
  organizer.py         Identifies and moves ROMs; builds the shared and ES-DE layouts
  detection.py         Works out a file's system (extension, folder names, contents)
  archives.py          Zip contents, cue/gdi track lists, disc header checks
  hashing.py           MD5/SHA-1, using the ROM inside a single-file zip
  dat_fetcher.py       Downloads the pinned libretro database
  dat_validation.py    Loads DAT files and looks up checksums
  library.py           Lists and counts the games in a ROM folder the way ES-DE does
  media.py             ES-DE and Steam image paths, and media coverage counts
  artwork.py           libretro and SteamGridDB downloads
  scraper.py           Runs Skyscraper for game data and extra media
  srm.py               Fills in Steam ROM Manager's local image paths
  settings.py          User settings: fields, defaults, checks, settings.json
  esde.py              Reads ROM and media folders from ES-DE's settings
  m3u.py               Writes playlist entries
  logging_utils.py     Log kept in memory for the page, and in files under logs/
templates/             index.html (main page), settings.html, logs.html
static/css/custom.css  Theme colours and chart styles
tests/
  features/            Gherkin feature files, one per area
  steps/               Step code for each feature
  test_app_steps.py    Steps for app.feature
```

## How a run works

1. **The request is checked.** `POST /api/organise` checks both folders, takes the run lock (a second run gets `409`), resets `status` and starts `run_organise` in a thread.
2. **Files are organised.** `process_roms` walks the import folder. Track files are skipped here because they move with their sheet. For each candidate it:
   1. hashes the file
   2. looks the checksum up in the DATs
   3. otherwise calls `detect_system(..., allow_guess=False)`
   4. places the game with `_place`, which refuses to overwrite and records each planned destination so two files can't claim the same one
   5. groups discs by title and handles them after the loop
3. **Each game is described.** `process_roms` returns one entry per placed game: `{system, title, names, dat_title, path}`. `path` is the file ES-DE and Steam list, which may be a playlist or a folder treated as a game.
4. **Game data is scraped.** `run_skyscraper` runs per system. A `None` result (disabled or not installed) skips the remaining systems.
5. **Artwork is downloaded.** `fetch_artwork` runs per game and returns the media types it saved.
6. **The report is built.** `build_report` summarises the run. Real runs then rescan the library.

The page asks for `GET /status` every second, and draws the progress and the report from it.

## Settings

`modules/settings.py` describes every user setting as a `Field`: key, label, kind, default, group, help text, limits, and whether it needs a restart. The Settings page is built from that list, so a new setting only has to be added there.

- **Reading.** Code calls `settings.get("key")`, or `settings.path("key")` for folders (`~` expanded, `None` when blank), at the moment it needs the value. Never import a setting's value at module level, or changes made on the Settings page won't reach that code.
- **Saving.** `settings.save(updates)` checks every value. If any fail, it saves nothing and returns `{key: message}`. Otherwise it writes `settings.json` through a temporary file, so a failed write never leaves half a file.
- **Secrets.** A secret sent as `null` keeps the saved value. `settings.public_values()` replaces secrets with `true` or `false` before anything goes to the page.

## Running the tests

```bash
source .venv/bin/activate
pytest                                  # all tests
pytest --cov                            # with coverage; fails below 100%
pytest tests/steps/library_steps.py     # one area
```

The tests use [pytest-bdd](https://pytest-bdd.readthedocs.io). Each area has a feature file in `tests/features/` and a step file in `tests/steps/`, linked with `scenarios("../features/<name>.feature")`. `pytest.ini` collects both `test_*.py` and `*_steps.py`.

Coverage is configured in `.coveragerc`: branch coverage over `app`, `config` and `modules`, with `fail_under = 100`. Only the `if __name__ == "__main__":` block is excluded.

The tests never touch the network, your real folders or your real `settings.json`:

- **HTTP** is replaced with fake responses (`modules.artwork.requests.get`).
- **Folders and Steam ROM Manager settings** live in `tmp_path`.
- **ES-DE's folders** come from patched `esde.rom_root` and `esde.media_root`.
- **Settings:** an autouse fixture in `tests/conftest.py` points `settings.SETTINGS_FILE` at `tmp_path` and starts each test from the defaults. Tests change a setting with `monkeypatch.setitem(settings.current, "key", value)`.

## Adding a system

1. Add the folder name and its extensions to `SYSTEM_ROM_TYPES` in `config.py`.
2. Add extensions used only by this system to `SYSTEM_MAP`. Add shared ones to that extension's list in `AMBIGUOUS_EXTENSIONS`.
3. Add its DAT names to `DAT_SYSTEM_IDS`. Use libretro's exact spelling, since it's also the thumbnail folder name.
4. If its folder name isn't the obvious one, add other names to `FOLDER_HINTS` in `modules/detection.py`.
5. If its EmuDeck Steam ROM Manager parser accepts `.m3u`, add it to `M3U_SYSTEMS`.
6. If Skyscraper calls the platform something else, add it to `SKYSCRAPER_PLATFORMS`.
7. Add a detection scenario to `tests/features/detection.feature`.
