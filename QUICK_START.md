# Quick Start: ROM Organizer Pro Enhancements

## What's New

### 1. Complete EmuDeck System Support
- 104 file extensions → 58 gaming systems
- Covers retro, modern, arcade, and computer systems
- Smart detection using folder hints and priority order

### 2. API Status Monitoring
- Real-time display of API configuration status
- Shows which scraper APIs are ready to use
- Lists all downloaded DAT files with sizes & dates

### 3. Enhanced System Detection
Three-tier resolution strategy:
1. **Arcade Keywords** - Detect arcade systems by folder name
2. **Folder Hints** - Use folder names like "ps2", "psx", "saturn"
3. **System Priority** - Smart fallback for ambiguous files

## Get Started

### Start the Application
```bash
cd /Users/jakebloor/PycharmProjects/RomOrganiser
python app.py
```

Then visit: http://localhost:8080

### Status Panel
Located at top of homepage showing:
- **API Connections**: Green (✓ Ready) or Yellow (○ Not Configured)
- **Downloaded DAT Files**: List with sizes and modification dates
- **Last Updated**: Auto-refreshes every 5 seconds

### API Endpoint
```bash
curl http://localhost:8080/api/status | python -m json.tool
```

## How Detection Works

### Example 1: Clear Folder Structure
```
/Emulation/roms/ps2/final_fantasy7.iso
                ↓
         Detects "ps2" in path
                ↓
            ✓ Returns: ps2
```

### Example 2: Ambiguous Extension
```
/Emulation/roms/dreamcast/shenmue.cue
                ↓
    .cue could be: psx, segacd, dreamcast, pcenginecd
                ↓
         Detects "dreamcast" in path
                ↓
         ✓ Returns: dreamcast
```

### Example 3: No Folder Hint
```
/roms/unknown/game.iso
     ↓
.iso could be: ps2, ps3, psx, segacd, dreamcast
     ↓
Use SYSTEM_PRIORITY (ps3 highest)
     ↓
  ✓ Returns: ps3
```

## Configuration

### Adding Folder Hints
Edit `modules/detection.py` - FOLDER_HINTS dictionary:

```python
FOLDER_HINTS = {
    "ps2": ["ps2", "playstation2", "playstation 2"],
    "psx": ["psx", "playstation1", "playstation", "ps1", "ps-1"],
    # Add more like:
    "customsystem": ["hint1", "hint2", "hint3"],
}
```

### Changing System Priority
Edit `config.py` - SYSTEM_PRIORITY array:

```python
SYSTEM_PRIORITY = [
    "switch",      # Modern systems first
    "ps3",
    "xbox360",
    # ... etc
]
```

### Adding New Extensions
Edit `config.py` - SYSTEM_MAP dictionary:

```python
SYSTEM_MAP = {
    ".newext": "newsystem",
    # ... etc
}
```

## Testing

### Run Tests
```bash
python test_enhancements.py
```

Expected output: **16/16 PASSING ✓**

### Test Specific Detection
```python
from modules.detection import detect_system
from pathlib import Path

# Test cases
print(detect_system(Path("/roms/ps2/game.iso")))      # ps2
print(detect_system(Path("/roms/psx/game.cue")))      # psx
print(detect_system(Path("/arcade/mame.chd")))        # fbneo
```

## Supported Systems (58 total)

### Nintendo (13)
NES, FDS, SNES, N64, GB, GBC, GBA, NDS, 3DS, GameCube, Wii, Wii U, Switch

### Sega (7)
Master System, Game Gear, Genesis, 32X, Sega CD, Saturn, Dreamcast

### Sony (5)
PSX, PS2, PS3, PSP, PS Vita

### Atari (8)
2600, 5200, 7800, Lynx, Jaguar, Jaguar CD, Atari 800, Atari ST

### Arcade (2)
FBNeo, MAME

### Computers (16)
C64, Amiga, Vic 20, ZX Spectrum, Amstrad CPC, MSX, X68000, ScummVM, EasyRPG, Lutro, Solarus, OpenBoR, Pico-8, TIC-80, DOS, PC Engine

### Others (7)
NEC, SNK (Neo Geo, NGP, NGPC), Microsoft (Xbox, Xbox 360), Wonderswan (2)

## Folder Structure Best Practices

```
Emulation/roms/
├── nes/
│   └── super_mario.nes
├── snes/
│   └── chrono_trigger.smc
├── ps2/
│   ├── final_fantasy_x.iso
│   └── metal_gear_solid_2.iso
├── psx/
│   ├── final_fantasy_vii.cue
│   └── metal_gear_solid.cue
├── dreamcast/
│   ├── shenmue.gdi
│   └── sonic_adventure.cdi
├── saturn/
│   └── panzer_dragoon.chd
├── gamecube/
│   └── zelda_windwaker.gcm
├── switch/
│   ├── zelda_totk.xci
│   └── mario_kart.nsp
├── arcade/
│   └── fbneo/
│       └── pacman.zip
└── dos/
    └── doom.exe
```

## Troubleshooting

### Wrong System Detected
1. **Check folder name** - Use hints like "ps2", "psx", "saturn"
2. **Add to FOLDER_HINTS** - If custom folder name, add it to dictionary
3. **Check SYSTEM_PRIORITY** - May need reordering

### Status Panel Not Updating
1. **Check browser console** - Press F12, look for errors
2. **Verify endpoint** - Visit http://localhost:8080/api/status
3. **Check DAT directory** - Ensure dats/ folder exists

### DAT Files Not Showing
1. **Run DAT download** - Use "Fetch DATs" button in UI
2. **Check dats/ folder** - Verify files are actually there
3. **Check file permissions** - Ensure app can read dats/ directory

## Performance Tips

- **Large ROM collections** - Use folder hints for faster detection
- **Avoid ambiguous extensions** - Organize by system folder
- **Status auto-refresh** - Default 5 seconds, adjust if too frequent

## Next Steps

1. Organize ROMs into system-specific folders
2. Use folder hints that match FOLDER_HINTS dictionary
3. Run app and verify detection in status panel
4. Configure API keys for scraper services
5. Download DAT files for accurate validation

## Documentation

- **ENHANCEMENTS.md** - Detailed technical documentation
- **IMPLEMENTATION_SUMMARY.md** - Complete feature breakdown
- **test_enhancements.py** - Working code examples

## Support

For issues or questions:
1. Check test results: `python test_enhancements.py`
2. Review FOLDER_HINTS and SYSTEM_PRIORITY settings
3. Verify folder structure matches hints
4. Check API Status endpoint for configuration issues
