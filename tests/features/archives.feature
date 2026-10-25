Feature: Looking inside ROM files

  Scenario Outline: Disc images are identified from their headers
    Given a disc image with a <header> header
    When the disc image is sniffed
    Then the sniffed system should be "<system>"

    Examples:
      | header                | system    |
      | GameCube              | gc        |
      | Wii                   | wii       |
      | Saturn                | saturn    |
      | Sega CD               | segacd    |
      | Dreamcast             | dreamcast |
      | Genesis               | genesis   |
      | PSP                   | psp       |
      | PS1                   | psx       |
      | PS2                   | ps2       |
      | raw PS1               | psx       |
      | PlayStation, no boot  | none      |
      | unknown               | none      |

  Scenario: A missing disc image can't be sniffed
    When a missing disc image is sniffed
    Then the sniffed system should be "none"

  Scenario: A zip with several ROMs has no single ROM
    Given a zip holding "Game (Disc 1).sfc" and "Game (Disc 2).sfc"
    Then the zip should have no single ROM

  Scenario: A zip with one ROM and a readme names the ROM
    Given a zip holding "Super Mario World (USA).sfc" and "readme.txt"
    Then the zip's single ROM should be "Super Mario World (USA).sfc"

  Scenario: A damaged zip has no single ROM
    Given a damaged zip
    Then the zip should have no single ROM

  Scenario: A cue sheet lists only the tracks that exist, once each
    Given a cue sheet pointing at "Game (Track 1).bin", "Game (Track 2).bin" and "Game (Track 1).bin" where track 2 is missing
    Then the sheet's tracks should be "Game (Track 1).bin"

  Scenario: A gdi sheet lists its quoted and unquoted tracks
    Given a gdi sheet pointing at "track01.bin" and "track 02.raw"
    Then the sheet's tracks should be "track01.bin, track 02.raw"

  Scenario: A missing sheet has no tracks
    Then a missing sheet should have no tracks
