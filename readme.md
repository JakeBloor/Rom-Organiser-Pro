# ROM Organizer Pro — PyCharm Project

## Project Overview

A full Steam Deck / EmuDeck ROM management application with:

* EmuDeck integration
* EmulationStation-DE compatibility
* DAT validation
* FBNeo / arcade support
* Multi-disc M3U support
* SteamGridDB artwork
* Skyscraper scraping automation
* Bootstrap web UI
* Flask backend

Designed for:

* SteamOS
* Steam Deck
* EmuDeck
* ES-DE
* RetroArch
* FinalBurn Neo

---

# Project Structure

```text
rom-organizer-pro/
├── app.py
├── requirements.txt
├── README.md
├── config.py
├── dats/
│   ├── FBNeo.dat
│   ├── MAME.dat
│   ├── No-Intro.dat
│   └── Redump.dat
├── static/
│   ├── css/
│   │   └── custom.css
│   └── img/
├── templates/
│   └── index.html
├── modules/
│   ├── __init__.py
│   ├── artwork.py
│   ├── dat_validation.py
│   ├── detection.py
│   ├── m3u.py
│   ├── scraper.py
│   ├── organizer.py
│   ├── hashing.py
├── logs/
├── cache/
└── media/
```

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
