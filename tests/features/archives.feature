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

  Scenario: Fingerprints tell files apart without reading them in full
    Given two copies of a 3 MB file and a third that differs only in the middle
    Then the copies should have the same fingerprint
    And the third should have a different fingerprint
    And hashing a ROM without watching progress should still give its MD5

  Scenario Outline: A PS3 game folder's title is read from its PARAM.SFO
    Given a PS3 game folder whose <where> PARAM.SFO is <contents>
    Then its title should be "<title>"

    Examples:
      | where     | contents                         | title         |
      | disc      | titled "Demon's Souls"           | Demon's Souls |
      | installed | titled "Journey"                 | Journey       |
      | disc      | missing                          |               |
      | disc      | not a PARAM.SFO                  |               |
      | disc      | cut short                        |               |
      | disc      | without a title                  |               |
      | disc      | titled ""                        |               |

  Scenario Outline: The SHA-1s in a CHD header are read without reading the rest
    Given a version <version> CHD header recording SHA-1s "<raw>" and "<overall>"
    Then the CHD SHA-1s should be "<found>"

    Examples:
      | version | raw                                      | overall                                  | found                                                                             |
      | 5       | 1111111111111111111111111111111111111111 | 2222222222222222222222222222222222222222 | 1111111111111111111111111111111111111111, 2222222222222222222222222222222222222222 |
      | 4       | 3333333333333333333333333333333333333333 | 4444444444444444444444444444444444444444 | 3333333333333333333333333333333333333333, 4444444444444444444444444444444444444444 |
      | 3       | 5555555555555555555555555555555555555555 | 0000000000000000000000000000000000000000 | 5555555555555555555555555555555555555555                                          |
      | 9       | 1111111111111111111111111111111111111111 | 2222222222222222222222222222222222222222 |                                                                                   |

  Scenario: A file that isn't a CHD has no CHD SHA-1s
    Given a file "fake.chd" that isn't a CHD
    Then the CHD SHA-1s should be ""

  Scenario Outline: A disc's serial is read from just its header
    Given a <kind> disc image "<file>" with serial "<serial>"
    Then its serial should be "<serial>"

    Examples:
      | kind          | file             | serial     |
      | GameCube      | Metroid.iso      | GM8E01     |
      | GameCube      | Metroid.gcm      | GM8E01     |
      | Wii           | Galaxy.rvz       | RMGE01     |
      | Wii           | Galaxy.wia       | RMGE01     |
      | Wii           | Galaxy.wbfs      | RMGE01     |
      | GameCube      | Metroid.ciso     | GM8E01     |
      | PlayStation 2 | FFX.iso          | SLUS20312  |
      | PlayStation   | FF7.bin          | SCUS94163  |
      | PSP           | GTA.iso          | ULUS10041  |
      | PBP           | Crash.pbp        | SCUS94900  |

  Scenario Outline: Images without a readable serial have none
    Given a file "<file>" containing "<contents>"
    Then its serial should be ""

    Examples:
      | file        | contents              |
      | Random.iso  | nothing to see here   |
      | Random.rvz  | RVZ but no disc magic |
      | Random.pbp  | not a PBP             |
      | Random.chd  | MComprHD              |
      | Missing.iso |                       |

  Scenario: A PS3 game folder's serial comes from its PARAM.SFO
    Given a PS3 game folder whose installed PARAM.SFO is titled "Journey"
    Then its PS3 serial should be "NPUA80068"

  Scenario: A PS3 game folder without a PARAM.SFO has no serial
    Given a PS3 game folder whose disc PARAM.SFO is missing
    Then its PS3 serial should be ""

  Scenario: A sheet pointing into a folder that doesn't exist has no tracks
    Given a cue sheet "Game.cue" pointing at "../gone/Game.bin"
    Then the sheet should have no tracks

  Scenario: Rewriting a .gdi moves only the tracks it was told about, quoting names with spaces
    Given a Dreamcast sheet "Shenmue.gdi" with tracks "track01.bin", "track02.raw" and "track03.bin"
    When the sheet's "track01.bin" moves to "../hidden/track01.bin" and "track03.bin" to "../hidden/my track03.bin"
    Then the sheet should read "1 0 4 2352 ../hidden/track01.bin 0 | 2 600 0 2352 track02.raw 0 | 3 45000 4 2352 "../hidden/my track03.bin" 0"
