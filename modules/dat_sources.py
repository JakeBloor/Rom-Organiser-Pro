"""
Alternative DAT file sources with direct download links
"""

# Alternative DAT sources with simpler download mechanisms
DAT_SOURCES = {
    # FBNeo (Arcade) - GitHub releases
    "fbneo": {
        "url": "https://api.github.com/repos/finalburnneo/FBNeo/releases/latest",
        "description": "FBNeo - Arcade and console emulator",
        "type": "github_release"
    },
    
    # MAME - Direct archive download
    "mame": {
        "url": "http://mamedev.org/",
        "description": "MAME - Arcade and console emulator",
        "type": "manual"
    },
    
    # Libretro DAT files
    "libretro": {
        "url": "https://github.com/libretro/libretro-database/tree/master/dat",
        "description": "Libretro database - Multiple systems",
        "type": "github_repo"
    },
    
    # Redump (CD-based systems) - Direct download
    "redump": {
        "url": "http://redump.org/downloads/",
        "description": "Redump - PlayStation, Dreamcast, Saturn, etc.",
        "type": "manual"
    },
    
    # No-Intro (DAT-o-MATIC)
    "datomatic": {
        "url": "https://datomatic.no-intro.org/",
        "description": "DAT-o-MATIC - No-Intro database",
        "type": "datomatic"
    }
}

def get_alternate_sources():
    """Get list of alternative DAT download sources"""
    return DAT_SOURCES

def get_download_instructions():
    """Get user-friendly download instructions for popular systems"""
    return """
Popular Systems Download Guide:

**Nintendo Systems:**
- NES: Search for "Nintendo - NES" on DAT-o-MATIC
- SNES: Search for "Nintendo - SNES" on DAT-o-MATIC
- N64: Search for "Nintendo - N64" on DAT-o-MATIC
- GameCube: Search for "Nintendo - GameCube" on DAT-o-MATIC
- Wii: Search for "Nintendo - Wii" on DAT-o-MATIC

**PlayStation Systems:**
- PS1: Search for "Sony - PlayStation" on DAT-o-MATIC
- PS2: Search for "Sony - PlayStation 2" on DAT-o-MATIC (PSX ISO/CSO/BIN)
- PSP: Search for "Sony - PSP" on DAT-o-MATIC

**Sega Systems:**
- Genesis: Search for "Sega - Genesis" on DAT-o-MATIC
- Saturn: Visit Redump.org for Saturn CD images
- Dreamcast: Visit Redump.org for Dreamcast CD images

**Arcade & Other:**
- MAME: Download from mamedev.org
- FBNeo: Visit FBNeo GitHub releases
- Other systems: Check Libretro database on GitHub
"""
