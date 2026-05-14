# Getting Started - ROM Organizer Pro

## Installation (5 minutes)

### 1. Clone or Navigate to Project
```bash
cd ROM-Organiser
```

### 2. Create Python Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Installs:
- Flask 5.3.3 (Web framework)
- requests 2.32.3 (HTTP library)
- lxml 5.0.0 (XML parsing)
- rapidfuzz 3.8.1 (Fuzzy matching)
- pytest 9.0.3 (Testing)

## Running the Application (1 minute)

### Start the Server
```bash
python app.py
```

Server starts on `http://localhost:8080`

### Access the Web Interface
Open your browser to: **http://localhost:8080**

You should see:
- **ROM Organizer Pro** header
- Status panel with detection statistics
- Form to enter ROM folder paths
- Buttons: "Run Organizer" and "Scan Games"

## Using the Web Interface

### Status Panel (Top Section)
Displays real-time information:

| Section | Shows |
|---------|-------|
| **Games Detected** | Total games, systems found, undetected files |
| **Top Systems** | Top 10 systems with game counts and percentages |
| **API Connections** | Status of enabled scraper APIs |

Auto-refreshes every 5 seconds.

### Game Scanning

1. **Locate Your ROM Path**
   - For EmuDeck: typically `/home/deck/Emulation/roms`
   - Note: The path where your ROMs are organized

2. **Click "Scan Games" Button** 
   - Walks through your ROM directory
   - Detects each ROM's system
   - Counts games per system
   - Displays results in real-time

3. **View Detection Results**
   - See which systems were found
   - Check undetected file count
   - View percentage distribution

### Running the Organizer

1. **Enter ROM Import Folder**
   - Path to your newly downloaded ROMs
   - Example: `/home/deck/Downloads/NewROMs`

2. **Enter EmuDeck ROM Folder** (if different)
   - Where organized ROMs should go
   - Default: `/home/deck/Emulation/roms`

3. **Click "Run Organizer"**
   - Processes ROM files
   - Moves them to system folders
   - Fetches artwork (if APIs configured)
   - Shows progress and results

### Viewing Logs

- Click "📜 Logs" link at bottom
- Shows all application messages
- Helpful for debugging

## Configuration

### Environment Variables (Optional)

For artwork scraping, set API keys:

```bash
# In terminal before running app.py
export STEAMGRIDDB_API_KEY="your_key"
export SCREENSCRAPER_USERNAME="username"
export SCREENSCRAPER_PASSWORD="password"
```

Or add to `.env` file (if supported by your setup).

### System Detection Configuration

Edit `config.py` to customize:

**SYSTEM_MAP** - Maps file extensions to systems
```python
SYSTEM_MAP = {
    ".nes": ["nes"],
    ".snes": ["snes"],
    ".iso": ["ps2", "ps3", "psx", "gc", "wii", "dreamcast", "saturn"],
    # ... more extensions
}
```

**SYSTEM_ROM_TYPES** - Valid extensions per system
```python
SYSTEM_ROM_TYPES = {
    "ps2": [".iso", ".isz", ".cso", ".chd"],
    "psx": [".pbp", ".cue", ".bin", ".ecm", ".img", ".iso"],
    # ... more systems
}
```

**SYSTEM_PRIORITY** - Fallback detection order
```python
SYSTEM_PRIORITY = ["switch", "ps3", "xbox360", "ps2", "psx", ...]
```

## Folder Structure for ROMs

Recommended organization:

```
Emulation/roms/
├── nes/
│   ├── Super Mario Bros.nes
│   └── The Legend of Zelda.nes
├── snes/
│   ├── Final Fantasy 3.snes
│   └── Super Metroid.snes
├── ps2/
│   ├── Final Fantasy 7.iso
│   └── Metal Gear Solid 2.iso
├── psx/
│   ├── Crash Bandicoot.cue
│   └── Spyro.cue
└── ... (other systems)
```

ROM Organizer Pro will:
- Auto-detect system from folder name
- Validate ROM file types
- Handle ambiguous extensions intelligently

## How Detection Works

### 3-Tier Detection Algorithm

**1. Arcade Keywords**
- Looks for "mame" or "fbneo" in filename
- Immediately returns detected arcade system

**2. Folder Hints**
- Checks parent folder names (ps2, psx, genesis, etc.)
- Validates extension is correct for that system
- Returns if match found

**3. System Priority**
- Uses SYSTEM_PRIORITY fallback order
- Picks first system where extension is valid
- Example: `.iso` could be ps2, ps3, or others

### Example Detections

| Path | Detection | Reason |
|------|-----------|--------|
| `/roms/ps2/game.iso` | **ps2** | Folder hint: "ps2" |
| `/roms/psx/game.cue` | **psx** | Folder hint: "psx" |
| `/roms/genesis/game.bin` | **genesis** | Folder hint: "genesis" |
| `/unknown/game.iso` | **ps3** | SYSTEM_PRIORITY (ps3 before ps2) |
| `/roms/mame32.zip` | **mame** | Arcade keyword detected |

## Testing the System

### Run Detection Tests
```bash
# Test ROM detection accuracy
pytest test_enhancements.py -v
```

Expected output:
```
test_system_priority PASSED
test_detection PASSED
test_system_map_coverage PASSED
```

### Manual Testing

```bash
# Test single file detection
python -c "
from modules.detection import detect_system
system = detect_system('/path/to/game.iso')
print(f'Detected: {system}')
"
```

## Troubleshooting

### Application won't start
```bash
# Verify Python 3.12+
python --version

# Verify dependencies installed
pip list | grep Flask

# Try reinstalling
pip install -r requirements.txt --force-reinstall
```

### No games detected
```bash
# 1. Check EmuDeck path exists
ls -la /home/deck/Emulation/roms

# 2. Click "Scan Games" button in UI

# 3. Check logs for errors
# View via web UI at /logs route
```

### System not recognized
1. Check if system is in supported list (60+)
2. Verify ROM file extension is correct
3. Check folder structure matches system name
4. Verify extension is in SYSTEM_ROM_TYPES

### API connection errors
1. Verify internet connection
2. Check API keys are set correctly
3. Review logs for specific error
4. Some APIs may be rate-limited

## Common Tasks

### Add Support for New System

1. **Add to SYSTEM_MAP** (config.py):
```python
SYSTEM_MAP = {
    ...
    ".ext": ["newsystem"],
}
```

2. **Add to SYSTEM_ROM_TYPES** (config.py):
```python
SYSTEM_ROM_TYPES = {
    "newsystem": [".ext"],
}
```

3. **Add folder hints** (modules/detection.py):
```python
FOLDER_HINTS = {
    "newsystem": ["hint1", "hint2"],
}
```

4. **Test detection**:
```bash
pytest test_enhancements.py -v
```

### Enable Debug Logging

In `app.py`, change:
```python
app.run(host="0.0.0.0", port=8080, debug=True)
```

Changes will auto-reload. Check logs at `/logs` route.

### Change Web Server Port

In `app.py`:
```python
app.run(host="0.0.0.0", port=YOUR_PORT, debug=True)
```

Then access at: `http://localhost:YOUR_PORT`

### Backup Your Configuration

```bash
# Backup config
cp config.py config.py.backup

# Backup system mappings
cp modules/detection.py modules/detection.py.backup
```

## Next Steps

1. **Scan Your ROMs**
   - Click "Scan Games" to see what's detected
   - Check detection accuracy

2. **Organize Your Collection**
   - Use "Run Organizer" to move ROMs to system folders
   - Verify files moved correctly

3. **Add More Systems**
   - Edit config.py for additional systems
   - Test with pytest

4. **Configure APIs** (Optional)
   - Set STEAMGRIDDB_API_KEY for artwork
   - Set SCREENSCRAPER credentials
   - ROMs will fetch artwork during organization

## Getting Help

### Check Documentation
- See [README.md](README.md) for full feature list
- See [config.py](config.py) for all configuration options
- See [modules/detection.py](modules/detection.py) for detection logic

### View Logs
- Via web UI: Click "📜 Logs" at bottom
- Browser console: Press F12, check Console tab
- Terminal: Watch app.py output directly

### Common Issues & Solutions
- **No DAT files**: DAT support currently disabled
- **0 games found**: Check ROM path, click "Scan Games"
- **System not recognized**: Verify in config.py SYSTEM_MAP
- **Slow startup**: Initial game scan can take time for large libraries

## Architecture Overview

### Web Server (Flask)
- Runs on localhost:8080
- Routes: /, /api/status, /api/scan-games, /logs
- Serves HTML UI with Bootstrap

### Detection Engine
- 3-tier algorithm for 60+ systems
- ROM type validation prevents false positives
- Real-time game counting

### Database
- In-memory detection stats
- Config-based system mappings
- No external database required

### Testing
- pytest for unit tests
- Detection accuracy tests (16/16 passing)
- Framework: pytest-bdd for BDD tests

---

**Ready to start?** Run `python app.py` and visit http://localhost:8080!
