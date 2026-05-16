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
