# ROM Organizer Pro — PyCharm Project

## Project Overview

A full Steam Deck / EmuDeck ROM management application with:

* **60+ Game Systems** - NES, SNES, PlayStation, Genesis, and more
* **Smart ROM Detection** - 3-tier detection with ROM type validation
* **EmuDeck Integration** - Automatic folder organization
* **DAT Validation** - Optional CRC validation and ROM metadata
* **Status Monitoring** - Real-time detection statistics
* **Web UI** - Bootstrap-based Flask interface on localhost:8080

Designed for:

* SteamOS / Steam Deck
* EmuDeck
* EmulationStation-DE
* RetroArch
* FinalBurn Neo
* Any emulation setup

---

## Quick Start

### 1. Installation
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Run Application
```bash
python app.py
# Visit http://localhost:8080
```

### 3. Download DAT Files (Optional)
- Visit https://datomatic.no-intro.org/
- Search for your systems (NES, SNES, PlayStation, etc.)
- Download .dat files and place in `dats/` folder
- See `DAT_FILES_GUIDE.md` for detailed instructions

### 4. Scan Games
- Enter your EmuDeck ROM path in the web UI
- Click "Scan Games" to detect systems
- View detection statistics in real-time

---

## Features

### System Detection
- **Automatic Detection**: Identifies 60+ gaming systems
- **3-Tier Algorithm**: 
  1. Arcade keyword matching
  2. Folder name heuristics
  3. System priority fallback
- **ROM Type Validation**: Confirms file extensions match system

### Game Detection & Status
- **Real-time Statistics**: Total games, systems, undetected count
- **Per-System Counts**: Top 10 systems with percentages
- **Last Scan Time**: Track when detection was last run

### DAT File Support
- **Optional Validation**: CRC checking and metadata extraction
- **Multiple Sources**: DAT-o-MATIC, Redump, FBNeo GitHub
- **Automatic Loading**: Place .dat files in `dats/` folder
- **Supported Formats**: XML, ZIP, GZIP compressed files

### Web Interface
- **Status Panel** with detection metrics
- **Game Scanner** with progress tracking
- **Log Viewer** for debugging
- **Responsive Design** - works on mobile

---

# Project Structure

```text
ROM Organizer Pro/
├── app.py                    # Flask application & routes
├── config.py                 # System mapping & configuration
├── requirements.txt          # Python dependencies
├── README.md                 # This file
├── DAT_FILES_GUIDE.md        # DAT file setup instructions
│
├── dats/                     # Download DAT files here
│   ├── nes.dat
│   ├── snes.dat
│   ├── psx.dat
│   └── ...
│
├── static/
│   ├── css/
│   │   └── custom.css        # Custom styling
│   └── img/
│
├── templates/
│   └── index.html            # Web UI template
│
├── modules/
│   ├── __init__.py
│   ├── artwork.py            # Artwork fetching
│   ├── dat_fetcher.py        # DAT file downloader
│   ├── dat_validation.py     # DAT validation & loading
│   ├── dat_sources.py        # Alternative DAT sources
│   ├── detection.py           # System detection (60+ systems)
│   ├── detection_tests.py     # Detection test suite
│   ├── m3u.py                # Multi-disc M3U generation
│   ├── scraper.py            # Game metadata scraping
│   ├── organizer.py          # ROM file organization
│   ├── hashing.py            # CRC/hash calculation
│   ├── logging_utils.py       # Logging utilities
│   └── __init__.py
│
├── logs/
├── cache/
└── media/

```

---

## Supported Systems (60+)

### Nintendo
NES, SNES, N64, GameCube, Wii, WiiU, Switch, Game Boy, GBC, GBA, NDS, 3DS

### Sony
PlayStation, PlayStation 2, PSP, PS Vita

### Sega
Genesis, Mega Drive, Game Gear, Master System, Dreamcast, Saturn

### Atari
2600, 5200, 7800, Lynx, Jaguar

### Other
FBNeo, MAME, Commodore 64, Amiga, Neo Geo, Arcade systems, and more

See `config.py` for complete system mapping.

---

## DAT Files Setup

DAT files are optional but enable:
- ✅ ROM validation via CRC checksums
- ✅ Accurate game titles and metadata
- ✅ Duplicate detection
- ✅ ROM type classification

### Download DAT Files

1. **Visit DAT-o-MATIC**: https://datomatic.no-intro.org/
2. **Search** for your system (e.g., "Nintendo NES")
3. **Download** the .dat file
4. **Place** in the `dats/` folder
5. **Refresh** the web UI

**See `DAT_FILES_GUIDE.md` for detailed instructions with examples for each system.**

### Alternative DAT Sources
- **Redump**: http://redump.org/downloads/ (PS1, PS2, Dreamcast, Saturn)
- **MAME**: http://mamedev.org/ (Arcade)
- **FBNeo**: https://github.com/finalburnneo/FBNeo (Arcade)
- **Libretro**: https://github.com/libretro/libretro-database (Multiple systems)

---

## API Configuration

The following optional API keys can be set as environment variables for scraping:

```bash
export STEAMGRIDDB_API_KEY="your_key_here"
export SCREENSCRAPER_USERNAME="username"
export SCREENSCRAPER_PASSWORD="password"
export TWITCH_IGDB_CLIENT_ID="your_client_id"
export RETROACHIEVEMENTS_API_KEY="your_key"
export LAUNCHBOX_API_KEY="your_key"
export GIANTBOMB_API_KEY="your_key"
export RAWG_API_KEY="your_key"
```

---

## Running the Application

### Development Mode
```bash
python app.py
# Runs on http://localhost:8080
# Auto-reloads on code changes (if debug=True in app.py)
```

### Production Mode
```bash
export FLASK_ENV=production
python app.py
```

---

## Web Interface Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET/POST | Main interface with form |
| `/api/status` | GET | System status JSON |
| `/api/scan-games` | POST | Scan ROMs and detect systems |
| `/api/dat-sources` | GET | Available DAT sources |
| `/status` | GET | Processing progress |
| `/logs` | GET | View application logs |

---

## Python Environment

**Required Python**: 3.12+

**Dependencies**:
```
Flask==5.3.3
requests==2.32.3
lxml==5.0.0
rapidfuzz==3.8.1
pytest==9.0.3
pytest-bdd==8.1.0
types-requests
```

---

## Testing

Run automated tests:
```bash
pytest modules/detection_tests.py -v
```

Test coverage includes:
- ✅ System detection accuracy
- ✅ ROM type validation
- ✅ Ambiguous extension handling
- ✅ DAT file validation

---

## Troubleshooting

### "No DAT files found"
- Ensure DAT files are in the `dats/` folder
- Verify file extensions are `.dat` (not `.zip`)
- Refresh the web page

### Game detection shows 0 games
- Check that EmuDeck path is correct
- Ensure ROMs are in proper folder structure
- Click "Scan Games" button to trigger detection

### System not recognized
- Check system is in the supported list
- Try adding folder hints in `config.py`
- Add ROM type to `SYSTEM_ROM_TYPES` in `config.py`

### Connection errors
- Verify API keys are set correctly (if using scraping)
- Check internet connection
- Review logs at `/logs` route

---

## Contributing

To add support for new systems:

1. **Add to `SYSTEM_MAP`** in `config.py` with file extensions
2. **Add to `SYSTEM_ROM_TYPES`** with valid extensions
3. **Add test cases** to `modules/detection_tests.py`
4. **Run tests** to verify: `pytest modules/detection_tests.py -v`

Example:
```python
# In config.py
SYSTEM_MAP = {
    ...
    ".rom": ["system_name"],
    ".bin": ["system_name", "other_system"],
}

SYSTEM_ROM_TYPES = {
    "system_name": [".rom", ".bin"],
    ...
}
```

---

## License

This project is designed for personal use with legally obtained ROM files.

---

## Changelog

### Version 1.0
- Initial release
- 60+ game system support
- Smart ROM detection with 3-tier algorithm
- Status panel with real-time detection stats
- DAT file support (optional)
- Web UI with game scanner
- 16/16 detection tests passing

---

# Requirements

```txt
flask
requests
lxml
rapidfuzz
```

---

# PyCharm Setup

## Create Virtual Environment

Inside PyCharm:

```text
Settings → Python Interpreter → Add Interpreter → Virtualenv
````

---

# Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Run Configuration

Main file:

```text
app.py
```

Parameters:

```text
(none)
```

---

# Launch

Run:

```bash
python app.py
```

Open:

```text
http://localhost:5000
```

---

# Steam Deck Notes

Install:

```bash
sudo pacman -S skyscraper
```

Configure ScreenScraper:

```bash
Skyscraper --config set screenscraper_user=YOUR_USER
Skyscraper --config set screenscraper_password=YOUR_PASS
```

---

# Recommended DAT Files

These are the best DAT sources for use with ROM Organizer Pro:

- No-Intro DATs for cartridge systems
- Redump DATs for disc-based systems
- FBNeo DATs for arcade collections
- MAME DATs for BIOS and arcade validation

## Recommended DAT sources

### No-Intro DATs (cartridge systems)

Best for: NES, SNES, N64, GBA, DS, 3DS, Genesis

Official: https://datomatic.no-intro.org

Use for:

- Clean retail dumps
- Naming standardization
- Hash verification

### Redump DATs (disc systems)

Best for: PS1, PS2, Saturn, Dreamcast, GameCube, Wii, Sega CD

Official: https://redump.org

Use for:

- CHD validation
- BIN/CUE validation
- ISO verification

### FBNeo DAT

Best for FinalBurn Neo arcade ROMs

Official GitHub: https://github.com/finalburnneo/FBNeo

Direct DAT location: https://github.com/finalburnneo/FBNeo/tree/master/Extras/dats

Important:

- Match DAT version to emulator version
- Arcade ROM sets are version-sensitive

### MAME DATs

Best for MAME, arcade validation, and BIOS verification

Official: https://www.mame.net/download

Or generate directly:

```bash
mame -listxml > mame.xml
```

### RetroArch DAT collection

Useful mega-pack: https://github.com/libretro/libretro-dats

Contains:

- Playlist DATs
- No-Intro mappings
- Arcade mappings

Very useful for ES-DE scraping and RetroArch playlists.

## DAT setup

```text
dats/
├── no-intro/
├── redump/
├── fbneo/
├── mame/
└── retroarch/
```

## Recommended usage by system

| System | DAT Source |
|---|---|
| NES | No-Intro |
| SNES | No-Intro |
| N64 | No-Intro |
| GBA | No-Intro |
| DS | No-Intro |
| 3DS | No-Intro |
| PS1 | Redump |
| PS2 | Redump |
| Dreamcast | Redump |
| Saturn | Redump |
| GameCube | Redump |
| Wii | Redump |
| Arcade | FBNeo / MAME |

## Important

Arcade DATs are version-sensitive. Always update DATs together with emulator updates and keep FBNeo/MAME versions aligned.

## Best practice

Use:

- No-Intro for cartridge systems
- Redump for discs
- FBNeo for arcade
- MAME for BIOS validation

This gives:

- better scraper matching
- accurate naming
- clean EmulationStation libraries
- fewer duplicates

## Future upgrade

Add a DAT auto-downloader so the app can fetch latest DATs automatically, cache versions, update on startup, and detect emulator versions. This would make the app behave more like RomVault, ClrMamePro, or LaunchBox importer, but Steam Deck-native.

---

# Detailed README.md

```markdown
 # 🎮 ROM Organizer Pro

ROM Organizer Pro is an advanced ROM management and scraping suite designed specifically for:

- Steam Deck
- SteamOS
- EmuDeck
- EmulationStation-DE (ES-DE)
- RetroArch
- FinalBurn Neo (FBNeo)
- Arcade ROM collections

The project provides a unified workflow for organizing, validating, scraping, and preparing ROM collections for both Steam Game Mode and EmulationStation.

---

# 🚀 Core Features

## 📁 Intelligent ROM Organization

Automatically:

- Detects game systems
- Organizes ROMs into EmuDeck folder structures
- Creates game folders
- Preserves compatible ROM naming
- Detects duplicates
- Supports existing EmuDeck libraries

Supported systems include:

- NES
- SNES
- Nintendo 64
- Game Boy / GBA
- Nintendo DS / 3DS
- GameCube
- Wii
- Wii U
- Switch
- PS1
- PS2
- PSP
- Sega Genesis
- Dreamcast
- Saturn
- FBNeo
- Arcade
- Xbox
- Xbox 360

---

# 💿 Multi-Disc Support

Automatically detects:

- Disc 1
- Disc 2
- CD1
- CD2
- Disk A/B naming

Then:

- Creates `.m3u` playlists
- Hides raw disc files from ES-DE
- Ensures proper multi-disc launching

Compatible with:

- DuckStation
- PCSX2
- RetroArch cores
- Beetle PSX
- Flycast

---

# 🔍 DAT Validation

Supports:

- No-Intro DATs
- Redump DATs
- FBNeo DATs
- MAME DATs

Validation methods:

- MD5
- SHA1
- CRC

Benefits:

- Accurate game naming
- Better scraper matches
- Duplicate detection
- ROM integrity verification

---

# 🕹️ Arcade & FBNeo Support

Special handling for arcade ROMs:

- ZIP files are preserved
- Internal ROM structure untouched
- FBNeo-compatible organization
- MAME-safe processing

Important:

Arcade ROM ZIP filenames are NOT renamed.

Changing arcade ZIP names can break:

- FinalBurn Neo
- MAME
- RetroArch arcade cores

---

# 🌐 Web Interface

Built using:

- Flask
- Bootstrap 5

Features:

- Dark mode UI
- Real-time progress bars
- Live logs
- Statistics dashboard
- Steam Deck friendly layout

Progress metrics include:

- ROMs processed
- DAT matches
- Duplicate detection
- Artwork downloads
- Scraping progress

---

# 🎮 EmulationStation Integration

Automatically integrates with:

EmulationStation Desktop Edition (ES-DE)

Features:

- gamelist.xml generatio
```
