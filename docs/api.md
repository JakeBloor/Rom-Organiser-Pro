# Web API

The page uses a small JSON API, which you can call from scripts as well. The server listens on `127.0.0.1:8181` unless you've changed it (see [Configuration](configuration.md)). There is no authentication, so don't expose the app beyond machines you trust.

## Organise

### `POST /api/organise`

Starts an organise run in the background. By default it organises the new games in the ROM folder, the ones `GET /api/new-roms` lists, and leaves everything already in place alone.

```json
{
  "rom_root": "/home/deck/Emulation/roms",
  "dry_run": true
}
```

| Field | Required | Notes |
|---|---|---|
| `rom_root` | no | Defaults to ES-DE's ROM folder. |
| `input_path` | no | Organise a separate folder of new ROMs into `rom_root` instead. Every ROM in it is moved. |
| `dry_run` | no | Defaults to `true`. Send `false` to move files and download artwork. |
| `force` | no | `true` re-organises every game in the ROM folder, not just new ones. A real run forgets what the cache knew about the folder; a dry run only previews this. |

| Status | Meaning |
|---|---|
| `202` | Started: `{"started": true}`. Follow it with `GET /status`. |
| `400` | The import folder or ROM folder doesn't exist. |
| `409` | A run is already going. |

### `POST /api/stop`

Asks the current run to stop after the file, system or game it's on. Returns `202`, or `409` if no run is going. The run ends with phase `stopped` and a report of what it did.

### `GET /api/new-roms?rom_root=<folder>`

Checks the ROM folder for games that still need organising. `rom_root` defaults to ES-DE's ROM folder. While a run is going, the result of the last check is returned.

```json
{
  "rom_root": "/home/deck/Emulation/roms",
  "new": ["Chrono Trigger (USA).sfc", "New games/Tetris (World).gb"],
  "needs_attention": [{"path": "Mystery Disc.iso", "reason": "unsorted"}],
  "total": 3,
  "all_organised": false,
  "checked": "2026-10-25T14:05:00"
}
```

- `new` lists games the app hasn't organised yet: ones in a system folder it hasn't handled, or that have changed since, plus anything outside the system folders.
- `needs_attention` lists games an earlier run left in place, with the reason: `unsorted`, `skipped` or `duplicate`.
- Paths are relative to the ROM folder.

Returns `404` with an `error` field if the folder doesn't exist.

### `GET /status`

The live state of the current or last run. The page asks for this every second.

| Field | Meaning |
|---|---|
| `running`, `phase` | Whether a run is going, and its phase: `starting`, `finding`, `organising`, `scraping`, `artwork`, `done`, `stopped` or `failed`. |
| `current_detail` | What's happening right now, such as `"checking 1.2 GB of 4.3 GB"` or Skyscraper's latest line. |
| `started_at`, `updated_at` | When the run started, and when progress last moved, in seconds since 1970. |
| `cancel_requested` | `true` once a stop has been asked for. |
| `dry_run` | Whether this is a dry run. |
| `progress`, `files_total`, `files_checked`, `current_file` | Progress within the current phase. |
| `roms_processed`, `dat_matches`, `name_matches`, `duplicates`, `unsorted`, `skipped`, `artwork_downloads` | Counters. `dat_matches` counts checksum matches, `serial_matches` serial matches and `name_matches` name matches. |
| `dat_misses` | Games that matched no DAT entry, by reason: `{reason: count}`. |
| `media_downloads` | Images saved this run, by type, such as `{"covers": 3, "steam_tall": 3}`. |
| `unsorted_files` | Paths of the files left in place, relative to the folder being organised. |
| `report` | The run report once the run finishes, otherwise `null` (see below). |
| `log`, `log_total` | The last 500 log lines, and how many lines there are in total. |

The `report` object:

```json
{
  "dry_run": false,
  "finished": "2026-10-25T14:03:11",
  "outcomes": {"Organised": 8, "Unsorted": 1, "Skipped": 0, "Duplicates": 1},
  "dat_matches": 6,
  "name_matches": 1,
  "dat_misses": {"compressed image, and its name isn't in the DATs": 1},
  "by_system": {"psx": 3, "snes": 2},
  "unsorted_files": ["Mystery Disc.iso"],
  "media": { "total": 8, "by_type": {"covers": 8}, "by_system": {} }
}
```

`media` is `null` for a dry run. See [Media coverage](#media-coverage) for its shape.

## Library

### `POST /api/scan-games`

Scans the ROM folder and counts its games. Nothing is changed.

```json
{ "rom_root": "/home/deck/Emulation/roms", "systems": ["snes", "psx"] }
```

| Field | Required | Notes |
|---|---|---|
| `rom_root` | no | Defaults to ES-DE's ROM folder. `emudeck_path` is accepted as another name for it. |
| `systems` | no | Only scan these systems. Leave it out, or send `null` or `[]`, to scan all of them. |

A successful scan returns:

```json
{
  "success": true,
  "total_games": 412,
  "systems_detected": 2,
  "games_by_system": {"snes": 250, "psx": 162},
  "to_organise": 3,
  "scanned_systems": ["psx", "snes"],
  "media": { "...": "see Media coverage" },
  "timestamp": "2026-10-25T14:05:00"
}
```

`scanned_systems` is `null` when every system was scanned. `to_organise` counts the games waiting in the ROM folder, as `GET /api/new-roms` reports them.

| Status | Meaning |
|---|---|
| `200` | Scanned. |
| `400` | `systems` isn't a list of names. |
| `404` | The ROM folder doesn't exist. |
| `500` | The scan failed. The `error` field says why. |

### `GET /api/systems?rom_root=<folder>`

Lists the system folders in a ROM folder, which the page uses for its system picker. `rom_root` defaults to ES-DE's ROM folder.

```json
{ "systems": ["gb", "psx", "snes"] }
```

Returns `404` with an `error` field if the folder doesn't exist.

### `GET /api/status`

The library stats from the last scan, plus API key status and the DAT files on disk:

- `detection`: `total_games`, `detected_systems`, `games_by_system`, `media`, `last_scan`, `scanned_systems`, `to_organise`, `supported_systems`
- `apis`: `enabled` and `configured` for `steamgriddb` and `screenscraper`
- `dats`: the `.dat` files directly in the `dats/` folder, with their sizes and dates

## Steam ROM Manager

### `POST /api/steam-rom-manager`

Points Steam ROM Manager's parsers at the app's Steam artwork. See [Steam ROM Manager](artwork.md#steam-rom-manager).

Returns `{"updated": ["Sony PlayStation - DuckStation", ...], "backup": "<path>"}`. It returns `404` with an `error` field if SRM's settings file is missing or can't be read.

## Settings

### `GET /api/settings`

```json
{
  "settings": {"port": 8181, "multi_file_layout": "shared", "steamgriddb_api": true, "...": "..."},
  "restart_needed": false,
  "load_error": null
}
```

Secrets (`steamgriddb_api`, `screenscraper_password`) are `true` or `false`, saying whether one is saved; their values are never returned. `restart_needed` is `true` once a server setting differs from the one the app started with. `load_error` explains why `settings.json` couldn't be read, if it couldn't.

### `POST /api/settings`

Saves the settings you send. Leave out any you don't want to change. For a secret, `null` keeps it and `""` deletes it.

```json
{ "steamgriddb_api": "new-key", "scraper_region": "eu", "port": 9000 }
```

| Status | Meaning |
|---|---|
| `200` | Saved. The response has the same shape as `GET /api/settings`, plus `"saved": true`. |
| `400` | `{"errors": {"port": "Must be between 1 and 65535."}}`. Nothing was saved. |
| `500` | A settings file couldn't be written. |

Setting keys: `esde_home`, `default_rom_folder`, `steam_artwork_dir`, `srm_config`, `multi_file_layout` (`shared` or `esde`), `enable_libretro_thumbnails`, `enable_steamgriddb`, `steamgriddb_api`, `enable_screenscraper`, `screenscraper_user`, `screenscraper_password`, `scraper_region`, `scraper_language`, `scraper_threads`, `host`, `port` and `debug`.

## Media coverage

The scan, `/api/status` and the run report describe image coverage like this:

```json
{
  "total": 3,
  "by_type": {"covers": 2, "screenshots": 0, "videos": 1, "steam_tall": 1},
  "by_system": {"snes": {"games": 2, "covers": 1, "videos": 1, "steam_tall": 1}}
}
```

- **ES-DE types** use ES-DE's folder names: `covers`, `screenshots`, `titlescreens`, `marquees`, `fanart`, `backcovers`, `3dboxes`, `physicalmedia`, `miximages`, `videos` and `manuals`.
- **Steam types** are `steam_tall`, `steam_long`, `steam_hero`, `steam_logo` and `steam_icon`.

## Pages

| Path | Shows |
|---|---|
| `/` | The main page. |
| `/settings` | The Settings page. |
| `/logs` | The full log of the app's current session, up to the most recent 5,000 lines. Log files under `logs/` keep everything. |
