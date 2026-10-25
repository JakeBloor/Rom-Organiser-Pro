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

  Scenario: Systems whose Steam parser can't launch playlists keep their files in the system folder
    Given an import folder containing "pcenginecd/Ys Book I & II (USA).cue" for track "Ys Book I & II (USA).bin"
    And the import folder also contains "pcenginecd/Dungeon Explorer II (USA) (Disc 1).chd"
    And the import folder also contains "pcenginecd/Dungeon Explorer II (USA) (Disc 2).chd"
    When the organiser runs
    Then the system folder "pcenginecd" should only hold "Dungeon Explorer II (USA) (Disc 1).chd | Dungeon Explorer II (USA) (Disc 2).chd | Ys Book I & II (USA).bin | Ys Book I & II (USA).cue"

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

  Scenario: An existing playlist with the same name blocks a cue sheet
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
