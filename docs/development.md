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
  library.py           Lists games the way ES-DE does; finds new games still to organise
  cache.py             Checksums and last outcomes per file, trusted while size and mtime match
  media.py             ES-DE and Steam image paths, and media coverage counts
  artwork.py           libretro and SteamGridDB downloads
  scraper.py           Runs Skyscraper for game data and extra media
  srm.py               Fills in Steam ROM Manager's local image paths
  settings.py          User settings: fields, defaults, checks, settings files
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

1. **The request is checked.** `POST /api/organise` checks the folders, takes the run lock (a second run gets `409`), resets `status` and starts `run_organise` in a thread. Without `input_path`, the ROM folder is organised in place.
2. **New games are found.** In place, `library.pending_games` lists what still needs organising:
   - games in a system folder the cache hasn't recorded as `organised`
   - multi-file games in a system folder that `organizer.stores_multi_file_games_apart` says belong elsewhere
   - everything outside the system folders

   Only those files go to `process_roms`.
3. **Files are organised.** `process_roms` goes through the files. Track files are skipped here because they move with their sheet. For each candidate it:
   1. identifies the file with `_identify`: a full MD5 and SHA-1 for DAT lookups, or just a 3 MB `hashing.fingerprint` for compressed images and files over `dat_check_limit_mb`. The result's `identity` is reused from the `FileCache` while the file is unchanged. Reading reports bytes to the progress bar.
   2. reports it as a duplicate if this run, or the cache's record of games already organised, has the same checksum
   3. looks the checksum up in the DATs
   4. keeps the system folder the file is in when that system accepts its extension, ignoring a DAT match for another system; otherwise uses the DAT match, then `detect_system(..., allow_guess=False)`
   5. places the game with `_place`, which organises a file already in the right place where it is (`[IN PLACE]`), refuses to overwrite, and records each planned destination so two files can't claim the same one
   6. groups discs by title and handles them after the loop

   Files are sorted by `settings.priority_systems()` first. PS3 game folders are placed whole by `_place_ps3_folder`, titled from `archives.ps3_title`. `status["cancel_requested"]` is checked before each file.

   The cache records every file left in place (`unsorted`, `skipped` or `duplicate`) and every game moved (`organised`). Folders a real run emptied are removed, except system folders. The cache is saved when the run ends, even if it failed.
4. **Each game is described.** `process_roms` returns one entry per placed game: `{system, title, names, dat_title, path}`. `path` is the file ES-DE and Steam list, which may be a playlist or a folder treated as a game.
5. **Game data is scraped.** `run_skyscraper` runs per system, priority systems first. Skyscraper gets no input, so it can't block on a prompt. Each line it prints goes to `status["current_detail"]`. A `None` result (disabled, not installed or stopped) skips the remaining systems.
6. **Artwork is downloaded.** `fetch_artwork` runs for `ARTWORK_WORKERS` games at once. Each worker thread reuses one `requests.Session`, with (5, 15) second timeouts.
7. **The report is built.** `build_report` summarises the run. Real runs then rescan the library, and every run checks for new games again.

The page asks for `GET /status` every second, and draws the progress and the report from it.

## Settings

`modules/settings.py` describes every user setting as a `Field`: key, label, kind, default, group, help text, limits, and whether it needs a restart. The Settings page is built from that list, so a new setting only has to be added there.

- **Reading.** Code calls `settings.get("key")`, or `settings.path("key")` for folders (`~` expanded, `None` when blank), at the moment it needs the value. Never import a setting's value at module level, or changes made on the Settings page won't reach that code.
- **Saving.** `settings.save(updates)` checks every value. If any fail, it saves nothing and returns `{key: message}`. Otherwise it writes account details (secrets, and fields marked `local=True`) to the git-ignored `settings.local.json`, and everything else to `settings.json`. Each file is written through a temporary file, so a failed write never leaves half a file.
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

The tests never touch the network, your real folders or your real settings files:

- **HTTP** is replaced with fake responses (`modules.artwork.requests.get`).
- **Folders and Steam ROM Manager settings** live in `tmp_path`.
- **ES-DE's folders** come from patched `esde.rom_root` and `esde.media_root`.
- **Settings:** an autouse fixture in `tests/conftest.py` points `settings.SETTINGS_FILE` and `settings.LOCAL_SETTINGS_FILE` at `tmp_path` and starts each test from the defaults, with an empty file cache in `tmp_path`. It also waits for any organise run a test started to finish. Tests change a setting with `monkeypatch.setitem(settings.current, "key", value)`.

## Adding a system

1. Add the folder name and its extensions to `SYSTEM_ROM_TYPES` in `config.py`.
2. Add extensions used only by this system to `SYSTEM_MAP`. Add shared ones to that extension's list in `AMBIGUOUS_EXTENSIONS`.
3. Add its DAT names to `DAT_SYSTEM_IDS`. Use libretro's exact spelling, since it's also the thumbnail folder name.
4. If its folder name isn't the obvious one, add other names to `FOLDER_HINTS` in `modules/detection.py`.
5. If its EmuDeck Steam ROM Manager parser accepts `.m3u`, add it to `M3U_SYSTEMS`.
6. If Skyscraper calls the platform something else, add it to `SKYSCRAPER_PLATFORMS`.
7. Add a detection scenario to `tests/features/detection.feature`.
