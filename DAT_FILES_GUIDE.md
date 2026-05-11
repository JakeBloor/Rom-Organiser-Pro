# ROM Organizer Pro - DAT File Setup Guide

## What are DAT Files?

DAT files are XML databases that contain metadata about ROM files, including:
- Official game titles
- CRC checksums for validation
- Release dates and publisher information
- ROM type classification

These files are essential for ROM organization and validation.

## Quick Start: Download DAT Files

### Method 1: DAT-o-MATIC (Recommended)

1. **Visit DAT-o-MATIC**: https://datomatic.no-intro.org/
2. **Search** for your system (e.g., "Nintendo NES")
3. **Click** the system result
4. **Select** the standard DAT file
5. **Download** the .dat file
6. **Extract** if it's a .zip file
7. **Place** the .dat file in the `dats/` folder
8. **Refresh** the ROM Organizer Pro page

### Method 2: Alternative Sources

If DAT-o-MATIC is unavailable, try these sources:

#### Arcade Systems (MAME/FBNeo)
- **MAME**: http://mamedev.org/ (search for MAME DATs)
- **FBNeo**: https://github.com/finalburnneo/FBNeo/releases

#### CD-Based Systems (PlayStation, Dreamcast, Saturn)
- **Redump Project**: http://redump.org/downloads/
  - PlayStation (PSX)
  - PlayStation 2 (PS2)
  - Dreamcast
  - Sega Saturn
  - Other CD systems

#### Additional Options
- **Libretro Database**: https://github.com/libretro/libretro-database/tree/master/dat
- **No-Intro**: Official database (via DAT-o-MATIC)

## Popular Systems & How to Find Them

### Nintendo Systems
| System | Search Term on DAT-o-MATIC |
|--------|---------------------------|
| NES | "Nintendo - Nintendo Entertainment System" |
| SNES | "Nintendo - Super Nintendo Entertainment System" |
| N64 | "Nintendo - Nintendo 64" |
| GameCube | "Nintendo - Nintendo GameCube" |
| Wii | "Nintendo - Wii" |
| Game Boy | "Nintendo - Game Boy" |
| Game Boy Color | "Nintendo - Game Boy Color" |
| Game Boy Advance | "Nintendo - Game Boy Advance" |
| Nintendo DS | "Nintendo - Nintendo DS" |
| Nintendo 3DS | "Nintendo - Nintendo 3DS" |

### Sony Systems
| System | Search Term on DAT-o-MATIC |
|--------|---------------------------|
| PlayStation (PSX) | "Sony - PlayStation" |
| PlayStation 2 | "Sony - PlayStation 2" |
| PSP | "Sony - PSP" |

### Sega Systems
| System | Search Term on DAT-o-MATIC |
|--------|---------------------------|
| Genesis/Mega Drive | "Sega - Genesis" or "Sega - Mega Drive" |
| Sega Saturn | Use Redump.org |
| Dreamcast | Use Redump.org |
| Master System | "Sega - Master System" |
| Game Gear | "Sega - Game Gear" |

### Arcade
| System | Source |
|--------|--------|
| MAME | http://mamedev.org/ |
| FBNeo | https://github.com/finalburnneo/FBNeo |

## File Structure

After downloading, your DAT files should be organized like this:

```
ROM Organiser/
├── dats/
│   ├── nes.dat
│   ├── snes.dat
│   ├── psx.dat
│   ├── ps2.dat
│   ├── genesis.dat
│   └── ... (other .dat files)
├── app.py
├── config.py
└── ... (other files)
```

## Supported DAT File Formats

ROM Organizer Pro supports:
- ✅ Standard XML DAT files (.dat)
- ✅ Compressed ZIP files (.zip containing .dat)
- ✅ GZIP compressed files (.gz)
- ✅ Plain text DAT files

**Note**: Only place .dat files in the dats/ folder. Remove .zip and .gz files after extracting.

## Troubleshooting

### "No DAT files found"
- Verify DAT files are in the `dats/` folder
- Check that file extension is `.dat` (not `.zip` or `.gz`)
- Ensure you've refreshed the page after placing files

### "Invalid DAT file"
- The file may be corrupted. Try downloading again
- Ensure you didn't accidentally download an HTML file
- Check the file size (DAT files are usually >100KB)

### "System not supported"
- ROM Organizer Pro supports 60+ systems
- If your system isn't recognized, manually select it
- Consider downloading a DAT file for that system

## About ROM Validation

Once DAT files are in place, ROM Organizer Pro can:
- ✅ Validate ROM CRC checksums
- ✅ Identify duplicate ROMs
- ✅ Extract official game titles
- ✅ Classify ROM types correctly
- ✅ Handle multi-disc games

However, validation is optional - ROM Organizer Pro will still organize ROMs without DAT files, just with less metadata.

## Manual DAT File Download Process (Step-by-Step)

### Example: Downloading NES DAT

1. Go to https://datomatic.no-intro.org/
2. Type "Nintendo NES" in search box and press Enter
3. Click on "Nintendo - Nintendo Entertainment System"
4. You'll see a page with system details
5. Look for a download button or checkbox next to "Download"
6. Select the standard DAT file (usually first option)
7. Click "Download" button
8. Save the file to `dats/nes.dat`
9. If saved as `nes.zip`, extract it and move `Nintendo - Nintendo Entertainment System.dat` to `dats/nes.dat`
10. Refresh ROM Organizer Pro

### Example: Downloading PS2 DAT

1. Go to https://datomatic.no-intro.org/
2. Type "PlayStation 2" in search and press Enter
3. Click on "Sony - PlayStation 2"
4. **Note**: PS2 has multiple DAT variants:
   - "PlayStation 2 (v*.xml)" - Main games
   - Choose the latest version
5. Click download
6. Save to `dats/ps2.dat`

## Getting Help

If you encounter issues:
1. Check that DAT files are in the correct `dats/` folder
2. Ensure .dat file extensions are correct
3. Verify you're downloading actual DAT files (not HTML pages)
4. Try downloading from Redump.org or Libretro if DAT-o-MATIC has issues

---

**Last Updated**: May 2026
**ROM Organizer Pro Version**: 1.0+
