Feature: ROM organiser

  Scenario: Organiser moves a ROM straight into its system folder
    Given an import folder containing "Chrono Trigger (USA).sfc"
    When the organiser runs
    Then the ROM folder should contain "snes/Chrono Trigger (USA).sfc"
    And the import file should no longer exist

  Scenario: Dry run leaves every file where it is
    Given an import folder containing "Chrono Trigger (USA).sfc"
    When the organiser runs in dry-run mode
    Then the import file should still exist
    And the ROM folder should be empty
    And the log should mention "[DRY RUN]"

  Scenario: Organiser does not overwrite an existing ROM
    Given an import folder containing "Chrono Trigger (USA).sfc"
    And the ROM folder already contains "snes/Chrono Trigger (USA).sfc"
    When the organiser runs
    Then the import file should still exist
    And the existing ROM should be unchanged
    And the log should mention "[SKIP]"

  Scenario: A cue sheet and its tracks are stored outside the system folder behind one playlist
    Given an import folder containing "psx/Crash Bandicoot (USA).cue" for track "Crash Bandicoot (USA).bin"
    When the organiser runs
    Then the ROM folder should contain ".multifile/psx/Crash Bandicoot (USA)/Crash Bandicoot (USA).cue"
    And the ROM folder should contain ".multifile/psx/Crash Bandicoot (USA)/Crash Bandicoot (USA).bin"
    And the playlist "psx/Crash Bandicoot (USA).m3u" should list "../.multifile/psx/Crash Bandicoot (USA)/Crash Bandicoot (USA).cue"
    And the system folder "psx" should only hold "Crash Bandicoot (USA).m3u"

  Scenario: Multi-disc games get one playlist in the system folder
    Given an import folder containing "psx/Final Fantasy VII (USA) (Disc 1).chd"
    And the import folder also contains "psx/Final Fantasy VII (USA) (Disc 2).chd"
    When the organiser runs
    Then the ROM folder should contain ".multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd"
    And the playlist "psx/Final Fantasy VII (USA).m3u" should list "../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd | ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 2).chd"
    And the system folder "psx" should only hold "Final Fantasy VII (USA).m3u"

  Scenario: In the ES-DE layout a cue sheet and its tracks share a folder ES-DE launches as one game
    Given the ES-DE folder layout
    And an import folder containing "psx/Crash Bandicoot (USA).cue" for track "Crash Bandicoot (USA).bin"
    When the organiser runs
    Then the ROM folder should contain "psx/Crash Bandicoot (USA).cue/Crash Bandicoot (USA).cue"
    And the ROM folder should contain "psx/Crash Bandicoot (USA).cue/Crash Bandicoot (USA).bin"

  Scenario: In the ES-DE layout multi-disc games share a folder with their playlist
    Given the ES-DE folder layout
    And an import folder containing "psx/Final Fantasy VII (USA) (Disc 1).chd"
    And the import folder also contains "psx/Final Fantasy VII (USA) (Disc 2).chd"
    When the organiser runs
    Then the ROM folder should contain "psx/Final Fantasy VII (USA).m3u/Final Fantasy VII (USA) (Disc 1).chd"
    And the playlist "psx/Final Fantasy VII (USA).m3u/Final Fantasy VII (USA).m3u" should list "Final Fantasy VII (USA) (Disc 1).chd | Final Fantasy VII (USA) (Disc 2).chd"

  Scenario: Systems whose Steam parser can't launch playlists keep their sheet in the system folder and hide its tracks
    Given an import folder containing "pcenginecd/Ys Book I & II (USA).cue" for track "Ys Book I & II (USA).bin"
    And the import folder also contains "pcenginecd/Dungeon Explorer II (USA) (Disc 1).chd"
    And the import folder also contains "pcenginecd/Dungeon Explorer II (USA) (Disc 2).chd"
    When the organiser runs
    Then the system folder "pcenginecd" should only hold "Dungeon Explorer II (USA) (Disc 1).chd | Dungeon Explorer II (USA) (Disc 2).chd | Ys Book I & II (USA).cue"
    And the ROM folder should contain ".multifile/pcenginecd/Ys Book I & II (USA)/Ys Book I & II (USA).bin"
    And the sheet "pcenginecd/Ys Book I & II (USA).cue" should point at "../.multifile/pcenginecd/Ys Book I & II (USA)/Ys Book I & II (USA).bin"

  Scenario: A disc image that can't be identified is left in place
    Given an import folder containing "Mystery Game.iso"
    When the organiser runs
    Then the import file should still exist
    And the ROM folder should be empty
    And the log should mention "[UNSORTED]"

  Scenario: A zip holding one ROM is sorted by the ROM inside
    Given an import folder containing a zip "Pokemon Emerald.zip" holding "Pokemon Emerald (USA).gba"
    When the organiser runs
    Then the ROM folder should contain "gba/Pokemon Emerald.zip"

  Scenario: A GameCube disc image is identified from its header
    Given an import folder containing a GameCube disc image "Wind Waker.iso"
    When the organiser runs
    Then the ROM folder should contain "gc/Wind Waker.iso"

  Scenario: A PS2 disc image is identified from its header
    Given an import folder containing a PS2 disc image "Gran Turismo 4 (USA).iso"
    When the organiser runs
    Then the ROM folder should contain "ps2/Gran Turismo 4 (USA).iso"

  Scenario: A second copy of the same ROM is reported as a duplicate
    Given an import folder containing "Tetris (World).gb"
    And the import folder also contains "Tetris copy.gb" with the same contents
    When the organiser runs
    Then the ROM folder should contain "gb/Tetris (World).gb"
    And the log should mention "[DUPLICATE]"
    And the status should count 1 duplicates

  Scenario: A DAT match decides the system of a file with a shared extension
    Given an import folder containing "sonic.bin"
    And the DATs list "sonic.bin" as "Sonic the Hedgehog (USA, Europe)" for "genesis" in "Sega - Mega Drive - Genesis"
    When the organiser runs
    Then the ROM folder should contain "genesis/sonic.bin"
    And the status should count 1 dat_matches

  Scenario: An old flat file with the same name blocks a cue folder in the ES-DE layout
    Given the ES-DE folder layout
    And an import folder containing "psx/Crash Bandicoot (USA).cue" for track "Crash Bandicoot (USA).bin"
    And the ROM folder already contains "psx/Crash Bandicoot (USA).cue"
    When the organiser runs
    Then the import file should still exist
    And the log should mention "[SKIP]"

  Scenario: An unrelated playlist with the same name blocks a cue sheet
    Given an import folder containing "psx/Crash Bandicoot (USA).cue" for track "Crash Bandicoot (USA).bin"
    And the ROM folder already contains "psx/Crash Bandicoot (USA).m3u"
    When the organiser runs
    Then the import file should still exist
    And the existing ROM should be unchanged
    And the log should mention "[SKIP]"

  Scenario: A missing disc is added back to an existing multi-disc game
    Given an import folder containing "psx/Final Fantasy VII (USA) (Disc 1).chd"
    And the import folder also contains "psx/Final Fantasy VII (USA) (Disc 2).chd"
    And the ROM folder already contains ".multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd"
    And the ROM folder already contains playlist "psx/Final Fantasy VII (USA).m3u" listing "../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd | ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 2).chd"
    When the organiser runs
    Then the ROM folder should contain ".multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 2).chd"
    And the playlist "psx/Final Fantasy VII (USA).m3u" should list "../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd | ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 2).chd"

  Scenario: A multi-disc game already in the library is left alone
    Given an import folder containing "psx/Final Fantasy VII (USA) (Disc 1).chd"
    And the import folder also contains "psx/Final Fantasy VII (USA) (Disc 2).chd"
    And the ROM folder already contains ".multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd"
    And the ROM folder already contains ".multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 2).chd"
    When the organiser runs
    Then the ROM folder should not contain "psx/Final Fantasy VII (USA).m3u"
    And the status should count 2 skipped

  Scenario: A dry run shows the playlist a multi-disc game would get
    Given an import folder containing "psx/Final Fantasy VII (USA) (Disc 1).chd"
    And the import folder also contains "psx/Final Fantasy VII (USA) (Disc 2).chd"
    When the organiser runs in dry-run mode
    Then the ROM folder should be empty
    And the log should mention "psx/Final Fantasy VII (USA).m3u lists: ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd, ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 2).chd"

  Scenario: A dry run shows the playlist a cue sheet would get
    Given an import folder containing "psx/Crash Bandicoot (USA).cue" for track "Crash Bandicoot (USA).bin"
    When the organiser runs in dry-run mode
    Then the ROM folder should be empty
    And the log should mention "psx/Crash Bandicoot (USA).m3u lists: ../.multifile/psx/Crash Bandicoot (USA)/Crash Bandicoot (USA).cue"

  Scenario: A disc already in a system without playlists is skipped
    Given an import folder containing "pcenginecd/Dungeon Explorer II (USA) (Disc 1).chd"
    And the ROM folder already contains "pcenginecd/Dungeon Explorer II (USA) (Disc 1).chd"
    When the organiser runs
    Then the import file should still exist
    And the status should count 1 skipped

  Scenario: Games dropped into the ROM folder are organised where they are
    Given "Chrono Trigger (USA).sfc" is dropped into the ROM folder
    And "New Stuff/Tetris (World).gb" is dropped into the ROM folder
    And "Keep Me/Golden Sun (USA).gba" is dropped into the ROM folder
    And "Keep Me/notes.txt" is dropped into the ROM folder
    And "psx/More/Final Fantasy VII (USA) (Disc 1).chd" is dropped into the ROM folder
    And "psx/More/Final Fantasy VII (USA) (Disc 2).chd" is dropped into the ROM folder
    And the ROM folder already contains "snes/Super Mario World (USA).sfc"
    When the ROM folder is organised
    Then the ROM folder should contain "snes/Chrono Trigger (USA).sfc"
    And the ROM folder should contain "gb/Tetris (World).gb"
    And the ROM folder should contain "gba/Golden Sun (USA).gba"
    And the ROM folder should contain ".multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 2).chd"
    And the playlist "psx/Final Fantasy VII (USA).m3u" should list "../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd | ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 2).chd"
    And the ROM folder should contain "snes/Super Mario World (USA).sfc"
    And the folder "New Stuff" should be gone
    And the folder "psx/More" should be gone
    And the ROM folder should contain "Keep Me/notes.txt"
    And the cache should say "snes/Chrono Trigger (USA).sfc" was organised

  Scenario: A game dropped in again is recognised as already in the library
    Given "Chrono Trigger (USA).sfc" is dropped into the ROM folder
    And the ROM folder is organised
    And a copy of "snes/Chrono Trigger (USA).sfc" is dropped into the ROM folder as "Chrono Copy.sfc"
    When the ROM folder is organised
    Then the log should mention "already in your library as"
    And the ROM folder should contain "Chrono Copy.sfc"
    And the cache should say "Chrono Copy.sfc" was duplicate

  Scenario: Files left in place aren't hashed again until they change
    Given ROM hashing is counted
    And "Mystery Disc.iso" is dropped into the ROM folder
    And the ROM folder is organised
    When the ROM folder is organised
    Then 1 file should have been hashed
    And the cache should say "Mystery Disc.iso" was unsorted
    When "Mystery Disc.iso" is changed
    And the ROM folder is organised
    Then 2 files should have been hashed

  Scenario: A clash is remembered as skipped
    Given "Chrono Trigger (USA).sfc" is dropped into the ROM folder
    And the ROM folder already contains "snes/Chrono Trigger (USA).sfc"
    When the ROM folder is organised
    Then the cache should say "Chrono Trigger (USA).sfc" was skipped

  Scenario: A dry run in the ROM folder moves nothing and removes no folders
    Given "New Stuff/Tetris (World).gb" is dropped into the ROM folder
    When the ROM folder is organised in dry-run mode
    Then the ROM folder should contain "New Stuff/Tetris (World).gb"
    And the ROM folder should not contain "gb/Tetris (World).gb"

  Scenario: Games for systems that keep discs apart are noted for duplicate checks
    Given "New/pcenginecd/Dungeon Explorer II (USA) (Disc 1).chd" is dropped into the ROM folder
    When the ROM folder is organised
    Then the ROM folder should contain "pcenginecd/Dungeon Explorer II (USA) (Disc 1).chd"
    And the cache should say "pcenginecd/Dungeon Explorer II (USA) (Disc 1).chd" was organised

  Scenario: Switching layout moves organised games again without calling them duplicates
    Given "New/pcenginecd/Dungeon Explorer II (USA) (Disc 1).chd" is dropped into the ROM folder
    And the ROM folder is organised
    And the ES-DE folder layout
    When the ROM folder is organised
    Then the ROM folder should contain "pcenginecd/Dungeon Explorer II (USA).m3u/Dungeon Explorer II (USA) (Disc 1).chd"
    And no duplicates should be reported

  Scenario: A game in the system folder you chose stays there even if a DAT says otherwise
    Given "snes/Chrono Trigger (USA).sfc" is dropped into the ROM folder
    And the DATs list "snes/Chrono Trigger (USA).sfc" in the ROM folder as "Some GBA Game" for "gba" in "Nintendo - Game Boy Advance"
    When the ROM folder is organised
    Then the ROM folder should contain "snes/Chrono Trigger (USA).sfc"
    And the log should mention "[IN PLACE]"
    And the placed game should have no DAT name

  Scenario: A game dropped into a system folder that can't run it is moved to the right one
    Given "snes/Golden Sun (USA).gba" is dropped into the ROM folder
    When the ROM folder is organised
    Then the ROM folder should contain "gba/Golden Sun (USA).gba"

  Scenario: Compressed and very large images are fingerprinted, not read in full
    Given ROM hashing is counted
    And files up to 1 MB are checked against the DATs
    And "psx/Spyro (USA).chd" is dropped into the ROM folder
    And a 2 MB "ps2/Gran Turismo 4 (USA).iso" is dropped into the ROM folder
    And "snes/Chrono Trigger (USA).sfc" is dropped into the ROM folder
    When the ROM folder is organised
    Then 1 file should have been hashed
    And the cache should say "ps2/Gran Turismo 4 (USA).iso" was organised
    And the cache should hold a fingerprint for "psx/Spyro (USA).chd"

  Scenario: A big image dropped in twice is still caught as a duplicate
    Given files up to 1 MB are checked against the DATs
    And a 2 MB "ps2/Gran Turismo 4 (USA).iso" is dropped into the ROM folder
    And the ROM folder is organised
    And a copy of "ps2/Gran Turismo 4 (USA).iso" is dropped into the ROM folder as "ps2/GT4 copy.iso"
    When the ROM folder is organised
    Then the cache should say "ps2/GT4 copy.iso" was duplicate

  Scenario: The priority systems are organised first, in order
    Given "snes/Chrono Trigger (USA).sfc" is dropped into the ROM folder
    And "gc/Metroid Prime (USA).rvz" is dropped into the ROM folder
    And "psx/Spyro (USA).chd" is dropped into the ROM folder
    And "gba/Golden Sun (USA).gba" is dropped into the ROM folder
    When the ROM folder is organised
    Then the games should have been organised in the order "psx, gc, gba, snes"

  Scenario: A file's progress moves while it's read
    Given a 2 MB "ps2/Gran Turismo 4 (USA).iso" is dropped into the ROM folder
    And reading happens in 1 MB chunks
    When the ROM folder is organised
    Then the progress should have shown "checking 1 MB of 2 MB"

  Scenario: A stop request ends the run before the next file
    Given "snes/Chrono Trigger (USA).sfc" is dropped into the ROM folder
    And a stop has been requested
    When the ROM folder is organised
    Then the log should mention "[STOPPED] Stopped before Chrono Trigger (USA).sfc"
    And the cache should know nothing about "snes/Chrono Trigger (USA).sfc"

  Scenario: Progress on a multi-gigabyte file is shown in GB
    Then 1.5 GB of 4.3 GB should read as "1.5 GB of 4.3 GB"

  Scenario: PS3 game folders are organised whole, by their real title, and only once
    Given a PS3 disc folder "ps3/BLUS30443" titled "Demon's Souls" with 500 files is dropped into the ROM folder
    And a PS3 game folder "New/Journey (USA).ps3" is dropped into the ROM folder
    When the ROM folder is organised
    Then the ROM folder should contain "ps3/BLUS30443/PS3_GAME/PARAM.SFO"
    And the ROM folder should contain "ps3/Journey (USA).ps3/PS3_GAME/USRDIR/EBOOT.BIN"
    And the log should mention "[IN PLACE]"
    And the placed games should be titled "Demon's Souls, Journey"
    And nothing should be waiting to be organised

  Scenario: A PS3 game folder whose name is taken is left where it was dropped
    Given a PS3 game folder "New/Journey (USA).ps3" is dropped into the ROM folder
    And a PS3 game folder "ps3/Journey (USA).ps3" is dropped into the ROM folder
    And the ROM folder is organised
    When the ROM folder is organised
    Then the cache should say "New/Journey (USA).ps3" was skipped

  Scenario: A compressed game named like a DAT entry is matched by name
    Given the DATs know "Spyro the Dragon (USA)" for "psx" in "Sony - PlayStation" by name
    And "psx/Spyro the Dragon (USA).chd" is dropped into the ROM folder
    When the ROM folder is organised
    Then the status should count 1 name_matches
    And the placed game should come from the DAT "Sony - PlayStation"

  Scenario: A DVD-based CHD matches the DAT by the checksum in its header
    Given a CHD "ps2/Gran Turismo 4 (USA).chd" whose header records SHA-1 "1111111111111111111111111111111111111111"
    And the DATs list SHA-1 "1111111111111111111111111111111111111111" as "Gran Turismo 4 (USA)" for "ps2" in "Sony - PlayStation 2"
    When the ROM folder is organised
    Then the status should count 1 dat_matches

  Scenario: An SNES dump with a copier header matches its headerless DAT entry
    Given "snes/Chrono Trigger (USA).smc" is dropped into the ROM folder with a 512-byte copier header
    And the DATs list the ROM without its header as "Chrono Trigger (USA)" for "snes" in "Nintendo - Super Nintendo Entertainment System"
    When the ROM folder is organised
    Then the status should count 1 dat_matches

  Scenario: Games that match nothing say why
    Given files up to 1 MB are checked against the DATs
    And "psx/Homebrew Thing.chd" is dropped into the ROM folder
    And a 2 MB "ps2/Unknown Disc.iso" is dropped into the ROM folder
    And "snes/My Hack.sfc" is dropped into the ROM folder
    When the ROM folder is organised
    Then the DAT misses should be
      | reason                                                 | games |
      | compressed image, and its serial and name aren't in the DATs | 1     |
      | too big to check, and its serial and name aren't in the DATs | 1     |
      | not in the DATs: renamed, patched, a hack or homebrew  | 1     |

  Scenario: A game in one of ES-DE's other folder names matches the DAT for that system
    Given "megadrive/Sonic the Hedgehog (USA, Europe).md" is dropped into the ROM folder
    And the DATs list "megadrive/Sonic the Hedgehog (USA, Europe).md" in the ROM folder as "Sonic the Hedgehog (USA, Europe)" for "genesis" in "Sega - Mega Drive - Genesis"
    When the ROM folder is organised
    Then the ROM folder should contain "megadrive/Sonic the Hedgehog (USA, Europe).md"
    And the status should count 1 dat_matches
    And the placed game should come from the DAT "Sega - Mega Drive - Genesis"

  Scenario: A compressed game in an alternative folder is matched by name for the system it stands for
    Given the DATs know "Sonic CD (USA)" for "segacd" in "Sega - Mega-CD - Sega CD" by name
    And "megacd/Sonic CD (USA).chd" is dropped into the ROM folder
    When the ROM folder is organised
    Then the status should count 1 name_matches

  Scenario: A compressed GameCube image is matched by the game ID in its header
    Given the DATs know serial "GM8E01" as "Metroid Prime (USA)" for "gc" in "Nintendo - GameCube"
    And a Wii-style image "gc/Metroid.rvz" with game ID "GM8E01" is dropped into the ROM folder
    When the ROM folder is organised
    Then the status should count 1 serial_matches
    And the placed game should come from the DAT "Nintendo - GameCube"

  Scenario: A GameCube game ID matches a Redump serial by its 4-character code
    Given the DATs know serial "DL-DOL-GM8E-USA" as "Metroid Prime (USA)" for "gc" in "Nintendo - GameCube"
    And a Wii-style image "gc/Metroid.rvz" with game ID "GM8E01" is dropped into the ROM folder
    When the ROM folder is organised
    Then the status should count 1 serial_matches

  Scenario: A serial the DATs don't know falls back to the name
    Given the DATs know "Metroid Prime (USA)" for "gc" in "Nintendo - GameCube" by name
    And a Wii-style image "gc/Metroid Prime (USA).rvz" with game ID "ZZZZ01" is dropped into the ROM folder
    When the ROM folder is organised
    Then the status should count 1 name_matches

  Scenario: A PS3 game folder is matched by the serial in its PARAM.SFO
    Given the DATs know serial "BLUS30443" as "Demon's Souls (USA)" for "ps3" in "Sony - PlayStation 3"
    And a PS3 disc folder "ps3/BLUS30443" with serial "BLUS30443" is dropped into the ROM folder
    When the ROM folder is organised
    Then the status should count 1 serial_matches
    And the placed games should be titled "Demon's Souls"

  Scenario: An arcade zip is matched by its set name and titled from the DAT
    Given the DATs know "sf2" as "Street Fighter II - The World Warrior (World 910522)" for "arcade" in "FBNeo - Arcade Games" by zip name
    And "arcade/sf2.zip" is dropped into the ROM folder
    When the ROM folder is organised
    Then the ROM folder should contain "arcade/sf2.zip"
    And the status should count 1 name_matches
    And the placed games should be titled "Street Fighter II - The World Warrior"

  Scenario: Every game in a messy system folder ends up listed once in ES-DE and Steam
    Given "psx/Crash Bandicoot (USA).cue" in the ROM folder points at "crash bandicoot (usa).bin"
    And "psx/Crash Bandicoot (USA).bin" is dropped into the ROM folder
    And "psx/Spyro (USA).cue" in the ROM folder points at "Spyro (USA).bin"
    And "psx/Spyro (USA).bin" is dropped into the ROM folder
    And "psx/Spyro (USA).m3u" in the ROM folder lists "Spyro (USA).cue"
    And "psx/Final Fantasy VII (USA) (Disc 1).chd" is dropped into the ROM folder
    And "psx/Final Fantasy VII (USA) (Disc 2).chd" is dropped into the ROM folder
    And "psx/Final Fantasy VII (USA).m3u" in the ROM folder lists "Final Fantasy VII (USA) (Disc 1).chd | Final Fantasy VII (USA) (Disc 2).chd"
    And "3do/Gex (USA).cue" in the ROM folder points at "Gex (USA) (Track 1).bin | Gex (USA) (Track 2).bin"
    And "3do/Gex (USA) (Track 1).bin" is dropped into the ROM folder
    And "3do/Gex (USA) (Track 2).bin" is dropped into the ROM folder
    When the ROM folder is organised
    Then the system folder "psx" should only hold "Crash Bandicoot (USA).m3u | Final Fantasy VII (USA).m3u | Spyro (USA).m3u"
    And the system folder "3do" should only hold "Gex (USA).cue"
    And the playlist "psx/Final Fantasy VII (USA).m3u" should list "../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd | ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 2).chd"
    And the playlist "psx/Spyro (USA).m3u" should list "../.multifile/psx/Spyro (USA)/Spyro (USA).cue"
    And the sheet "3do/Gex (USA).cue" should point at "../.multifile/3do/Gex (USA)/Gex (USA) (Track 1).bin | ../.multifile/3do/Gex (USA)/Gex (USA) (Track 2).bin"
    And no duplicates should be reported

  Scenario: A disc added later joins the discs already behind the playlist
    Given "psx/Final Fantasy VII (USA) (Disc 1).chd" is dropped into the ROM folder
    And the ROM folder is organised
    And "psx/Final Fantasy VII (USA) (Disc 2).chd" is dropped into the ROM folder
    When the ROM folder is organised
    Then the playlist "psx/Final Fantasy VII (USA).m3u" should list "../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd | ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 2).chd"

  Scenario: A CD game whose tracks are already hidden is organised where it is
    Given "3do/Gex (USA).cue" in the ROM folder points at "../.multifile/3do/Gex (USA)/Gex (USA).bin"
    And ".multifile/3do/Gex (USA)/Gex (USA).bin" is dropped into the ROM folder
    When the ROM folder is organised
    Then the log should mention "[IN PLACE]"
    And the system folder "3do" should only hold "Gex (USA).cue"

  Scenario: Hiding a CD game's tracks never overwrites a file already there
    Given "3do/Gex (USA).cue" in the ROM folder points at "Gex (USA).bin"
    And "3do/Gex (USA).bin" is dropped into the ROM folder
    And the ROM folder already contains ".multifile/3do/Gex (USA)/Gex (USA).bin"
    When the ROM folder is organised
    Then the log should mention "[SKIP]"
    And the ROM folder should contain "3do/Gex (USA).bin"

  Scenario: A dry run shows how a CD game's tracks would be hidden
    Given "3do/Gex (USA).cue" in the ROM folder points at "Gex (USA).bin"
    And "3do/Gex (USA).bin" is dropped into the ROM folder
    When the ROM folder is organised in dry-run mode
    Then the log should mention "[DRY RUN]"
    And the ROM folder should contain "3do/Gex (USA).bin"

  Scenario: A multi-disc CD game for a system without playlists hides each disc's tracks
    Given "New/pcenginecd/Dungeon Explorer II (USA) (Disc 1).cue" in the ROM folder points at "Dungeon Explorer II (USA) (Disc 1).bin"
    And "New/pcenginecd/Dungeon Explorer II (USA) (Disc 1).bin" is dropped into the ROM folder
    When the ROM folder is organised
    Then the system folder "pcenginecd" should only hold "Dungeon Explorer II (USA) (Disc 1).cue"
    And the ROM folder should contain ".multifile/pcenginecd/Dungeon Explorer II (USA) (Disc 1)/Dungeon Explorer II (USA) (Disc 1).bin"

  Scenario: Dead entries are dropped from the app's playlists, and your own are left alone
    Given ".multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd" is dropped into the ROM folder
    And "psx/Final Fantasy VII (USA).m3u" in the ROM folder lists "Final Fantasy VII (USA) (Disc 1).chd | ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd"
    And "psx/My Mix.m3u" in the ROM folder lists "Missing Game.chd"
    And "psx/All Gone.m3u" in the ROM folder lists "../.multifile/psx/Gone/Gone.chd"
    And "psx/Fine.m3u" in the ROM folder lists "../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd"
    And "psx/Legend of Dragoon (USA).m3u/Legend of Dragoon (USA).m3u" in the ROM folder lists "LoD (Disc 1).chd"
    When the playlists are repaired
    Then 1 playlist should have been repaired
    And the playlist "psx/Final Fantasy VII (USA).m3u" should list "../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd"
    And the playlist "psx/My Mix.m3u" should still read "Missing Game.chd"
    And the playlist "psx/All Gone.m3u" should still read "../.multifile/psx/Gone/Gone.chd"

  Scenario: A dry run only says which playlists it would repair
    Given ".multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd" is dropped into the ROM folder
    And "psx/Final Fantasy VII (USA).m3u" in the ROM folder lists "Final Fantasy VII (USA) (Disc 1).chd | ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd"
    When the playlists are repaired in dry-run mode
    Then the log should mention "would drop 1 entries"
    And the playlist "psx/Final Fantasy VII (USA).m3u" should still read "Final Fantasy VII (USA) (Disc 1).chd | ../.multifile/psx/Final Fantasy VII (USA)/Final Fantasy VII (USA) (Disc 1).chd"
