Feature: ROM System Detection

  Scenario: Clear extensions are detected correctly
    Given a ROM with path "/roms/nes/super_mario.nes"
    When the system detection runs
    Then the detected system should be "nes"

  Scenario: SNES ROM with clear extension detected
    Given a ROM with path "/roms/snes/chrono.smc"
    When the system detection runs
    Then the detected system should be "snes"

  Scenario: GBA ROM with clear extension detected
    Given a ROM with path "/roms/gba/fire_emblem.gba"
    When the system detection runs
    Then the detected system should be "gba"

  Scenario: PS2 ROM with folder hint and ambiguous extension
    Given a ROM with path "/roms/ps2/final_fantasy_vii.iso"
    When the system detection runs
    Then the detected system should be "ps2"

  Scenario: PSX ROM with folder hint and ambiguous extension
    Given a ROM with path "/roms/psx/final_fantasy_vii.iso"
    When the system detection runs
    Then the detected system should be "psx"

  Scenario: PS3 ROM with folder hint and ambiguous extension
    Given a ROM with path "/roms/ps3/final_fantasy_xv.iso"
    When the system detection runs
    Then the detected system should be "ps3"

  Scenario: Sega CD ROM with folder hint and ISO extension
    Given a ROM with path "/roms/segacd/sonic_cd.iso"
    When the system detection runs
    Then the detected system should be "segacd"

  Scenario: Saturn ROM with folder hint and CHD extension
    Given a ROM with path "/roms/saturn/sonic_adventure.chd"
    When the system detection runs
    Then the detected system should be "saturn"

  Scenario: GameCube ROM with folder hint and CHD extension
    Given a ROM with path "/roms/gamecube/zelda_windwaker.chd"
    When the system detection runs
    Then the detected system should be "gc"

  Scenario: Arcade ROM with folder hint and CHD extension
    Given a ROM with path "/roms/arcade/caveman_ninja.chd"
    When the system detection runs
    Then the detected system should be "fbneo"

  Scenario: PSX ROM with folder hint and CUE extension
    Given a ROM with path "/roms/psx/metal_gear_solid.cue"
    When the system detection runs
    Then the detected system should be "psx"

  Scenario: Dreamcast ROM with folder hint and CUE extension
    Given a ROM with path "/roms/dreamcast/shenmue.cue"
    When the system detection runs
    Then the detected system should be "dreamcast"

  Scenario: Switch ROM with XCI extension
    Given a ROM with path "/roms/switch/zelda_totk.xci"
    When the system detection runs
    Then the detected system should be "switch"

  Scenario: Switch ROM with NSP extension
    Given a ROM with path "/roms/switch/mario_kart.nsp"
    When the system detection runs
    Then the detected system should be "switch"

  Scenario: PS4 ROM with folder hint and ambiguous ISO extension
    Given a ROM with path "/roms/ps4/horizon_zero_dawn.iso"
    When the system detection runs
    Then the detected system should be "ps4"

  Scenario: PS5 ROM with folder hint and ambiguous ISO extension
    Given a ROM with path "/roms/ps5/demon_souls.iso"
    When the system detection runs
    Then the detected system should be "ps5"

  Scenario: PS4 ROM with folder hint and ambiguous PKG extension
    Given a ROM with path "/roms/ps4/ratchet_and_clank.pkg"
    When the system detection runs
    Then the detected system should be "ps4"

  Scenario: PS5 ROM with folder hint and ambiguous PKG extension
    Given a ROM with path "/roms/ps5/returnal.pkg"
    When the system detection runs
    Then the detected system should be "ps5"

  Scenario: FBNeo arcade ROM in arcade folder
    Given a ROM with path "/arcade/fbneo/pacman.zip"
    When the system detection runs
    Then the detected system should be "fbneo"

  Scenario: MAME ROM with arcade folder hint uses priority
    Given a ROM with path "/arcade/mame/mortal_kombat.7z"
    When the system detection runs
    Then the detected system should be "mame"

  Scenario: System priority configuration is complete
    When checking system priority configuration
    Then system priority should not be empty
    And all systems in priority should be strings

  Scenario: System map has complete extension coverage
    When checking system map coverage
    Then system map should contain extensions
    And all systems should be mapped to valid systems
    And system map should have at least 100 extensions

  Scenario: SNES archive in snes folder is not detected as NES
    Given a ROM with path "/roms/snes/zelda.zip"
    When the system detection runs
    Then the detected system should be "snes"

  Scenario: GBA archive in gba folder is not detected as Game Boy
    Given a ROM with path "/roms/gba/pokemon_emerald.zip"
    When the system detection runs
    Then the detected system should be "gba"

  Scenario: Arcade in a file name does not make it an arcade ROM
    Given a ROM with path "/roms/n64/arcade_racer.z64"
    When the system detection runs
    Then the detected system should be "n64"

  Scenario: Folder names with spaces match folder hints
    Given a ROM with path "/roms/PlayStation 2/gran_turismo_4.iso"
    When the system detection runs
    Then the detected system should be "ps2"

  Scenario Outline: Files that aren't ROMs for any system are not detected
    Given a ROM with path "<path>"
    When the system detection runs
    Then no system should be detected

    Examples:
      | path                    |
      | /roms/snes/README       |
      | /roms/snes/notes.xyz    |
      | /roms/mame/readme.txt   |

  Scenario Outline: Ambiguous files outside system folders are guessed only when allowed
    Given a ROM with path "<path>"
    When the system detection runs
    Then the detected system should be "<guess>"
    When the system detection runs without guessing
    Then no system should be detected

    Examples:
      | path                    | guess      |
      | /downloads/game.iso     | ps5        |
      | /downloads/disk.dsk     | amstradcpc |

  Scenario Outline: Zips whose contents don't decide a system are not sorted
    Given a zip on disk holding <contents>
    When the system detection runs without guessing
    Then no system should be detected

    Examples:
      | contents                         |
      | "Game (Disc 1).sfc" and "Game (Disc 2).sfc" |
      | "Game.iso"                       |
      | "Game.xyz"                       |
