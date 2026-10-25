Feature: DAT loading and fetching

  Scenario: clrmamepro DATs with brackets in ROM names load their hashes
    Given a libretro DAT and a No-Intro metadat DAT exist
    When the DAT files are loaded from the DAT directory
    Then the hash lookup should return "Advance Wars (USA)" for the No-Intro SHA1
    And the hash lookup should return "Tetris (World)" for the libretro MD5

  Scenario: Pinned libretro DATs already on disk are not downloaded again
    Given libretro DATs for the pinned commit are on disk
    And downloads are recorded
    When the libretro DATs are fetched
    Then no download should be attempted
    And the libretro fetch should report success

  Scenario: A failed libretro download keeps the existing DATs
    Given libretro DATs from an older commit are on disk
    And downloads fail
    When the libretro DATs are fetched
    Then the libretro fetch should report failure
    And the existing libretro DATs should be kept

  Scenario: A failed libretro download points the user at manual DAT sources
    Given downloads fail
    When the latest DATs are fetched
    Then only the libretro archive should be requested
    And the log should explain where to put manually downloaded DATs

  Scenario: Without libretro DATs, top-level DATs load and libretro's own folders are ignored
    Given an XML DAT "Top.dat" listing "Tetris (World)" with MD5 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    And an XML DAT "dat/Ignored.dat" listing "Ignored Game" with MD5 "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    When the DAT files are loaded from the DAT directory
    Then MD5 "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa" should be "Tetris (World)"
    And MD5 "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb" should not be found

  Scenario: Games without a name and ROMs without hashes are skipped
    Given a clrmamepro DAT "metadat/no-intro/Nintendo - Game Boy.dat" with an unnamed game, a ROM without hashes and "Tetris (World)" with MD5 "cccccccccccccccccccccccccccccccc"
    When the DAT files are loaded from the DAT directory
    Then MD5 "cccccccccccccccccccccccccccccccc" should be "Tetris (World)" for "gb" in "Nintendo - Game Boy"
    And the DAT log should not mention "Skipped"

  Scenario: DATs that list games without checksums still give their names
    Given a clrmamepro DAT "Sega - Saturn.dat" with no hashes
    When the DAT files are loaded from the DAT directory
    Then the DAT log should mention "Loaded 1 game names from Sega - Saturn.dat (no checksums)"
    And the name "NiGHTS" should be found for "saturn"

  Scenario: Empty and unreadable DATs are reported
    Given a clrmamepro DAT "Stub.dat" with no games
    And an unreadable DAT "Broken.dat"
    When the DAT files are loaded from the DAT directory
    Then the DAT log should mention "Skipped unsupported or invalid DAT: Stub.dat"
    And the DAT log should mention "Broken.dat clrmamepro parse failed"

  Scenario: Games are found by name, for one system or when only one system has the name
    Given an XML DAT "metadat/no-intro/Nintendo - Game Boy.dat" listing "Tetris (World)" with MD5 "eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"
    And an XML DAT "metadat/no-intro/Nintendo - Nintendo Entertainment System.dat" listing "Tetris (World)" with MD5 "ffffffffffffffffffffffffffffffff"
    And an XML DAT "metadat/no-intro/Nintendo - Game Boy Advance.dat" listing "Golden_Sun  (USA)" with MD5 "abababababababababababababababab"
    When the DAT files are loaded from the DAT directory
    Then the name "tetris (world)" should be found for "gb"
    And the name "Tetris (World)" should not be found without a system
    And the name "golden sun (usa)" should be found without a system as "Golden_Sun  (USA)"
    And the name "Tetris (World)" should not be found for "snes"

  Scenario: A DAT shipped both inside libretro and in the DAT folder is loaded once
    Given an XML DAT "libretro/metadat/no-intro/Nintendo - Game Boy.dat" listing "Tetris (World)" with MD5 "dddddddddddddddddddddddddddddddd"
    And an XML DAT "metadat/no-intro/Nintendo - Game Boy.dat" listing "Tetris (World)" with MD5 "dddddddddddddddddddddddddddddddd"
    When the DAT files are loaded from the DAT directory
    Then the DAT log should mention "Nintendo - Game Boy.dat" once

  Scenario: DATs for the pinned commit already on disk count as a successful fetch
    Given libretro DATs for the pinned commit are on disk
    And downloads are recorded
    When the latest DATs are fetched
    Then the latest DAT fetch should report success

  Scenario: A libretro download extracts the DAT folders and replaces older DATs
    Given libretro DATs from an older commit are on disk
    And a leftover staging folder from an earlier download
    And the download returns a libretro archive
    When the libretro DATs are fetched
    Then the libretro fetch should report success
    And the libretro folder should hold exactly
      | path                                            |
      | .commit                                         |
      | dat/Nintendo - Game Boy.dat                     |
      | metadat/no-intro/Nintendo - Game Boy Advance.dat |
      | metadat/redump/Sony - PlayStation.dat           |
    And the commit marker should name the pinned commit

  Scenario Outline: A bad libretro download keeps the existing DATs
    Given libretro DATs from an older commit are on disk
    And the download returns <download>
    When the libretro DATs are fetched
    Then the libretro fetch should report failure
    And the existing libretro DATs should be kept
    And no staging folder should be left behind

    Examples:
      | download                       |
      | an HTML page                   |
      | a libretro archive without DATs |
      | a damaged zip                  |

  Scenario: The first libretro download creates the libretro folder
    Given the download returns a libretro archive
    When the libretro DATs are fetched
    Then the libretro fetch should report success
    And the commit marker should name the pinned commit

  Scenario: Names from a DAT for an unknown system aren't used to match games
    Given a clrmamepro DAT "Unknown Maker - Thing.dat" with no hashes
    When the DAT files are loaded from the DAT directory
    Then the name "NiGHTS" should not be found without a system

  Scenario: A plain name stands for the latest release the DAT lists under more tags
    Given an XML DAT "metadat/redump/Sony - PlayStation 2.dat" listing the games "Gran Turismo 4 (USA) (Beta) | Gran Turismo 4 (USA) (v1.01) | Gran Turismo 4 (USA) (v2.00) | Gran Turismo 4 (USA) (Demo) | Gran Turismo 4 - Prologue (Japan)"
    When the DAT files are loaded from the DAT directory
    Then the name "Gran Turismo 4 (USA)" should be found for "ps2" as "Gran Turismo 4 (USA) (v2.00)"
    And the name "Gran Turismo 4 (Japan)" should not be found for "ps2"
    And the name "Gran Turismo 4 (USA)" should be found without a system as "Gran Turismo 4 (USA) (v2.00)"

  Scenario: A plain name with only unreleased versions in the DAT isn't matched
    Given an XML DAT "metadat/redump/Sony - PlayStation 2.dat" listing the games "Lost Game (USA) (Proto) | Lost Game (USA) (Beta 2)"
    When the DAT files are loaded from the DAT directory
    Then the name "Lost Game (USA)" should not be found for "ps2"

  Scenario: FinalBurn Neo's DATs are downloaded into their own folder
    Given FinalBurn Neo's DATs can be downloaded
    When FinalBurn Neo's DATs are fetched
    Then FinalBurn Neo's fetch should report success
    And FinalBurn Neo's DATs should be on disk

  Scenario: FinalBurn Neo's DATs aren't downloaded again
    Given FinalBurn Neo's DATs for the pinned commit are on disk
    And downloads are recorded
    When FinalBurn Neo's DATs are fetched
    Then FinalBurn Neo's fetch should report success
    And no download should be attempted

  Scenario: A failed FinalBurn Neo download is reported
    Given downloads fail
    When FinalBurn Neo's DATs are fetched
    Then FinalBurn Neo's fetch should report failure

  Scenario: Arcade sets are found by zip name, titled by their description
    Given FinalBurn Neo's "Arcade only" DAT lists "sf2" as "Street Fighter II - The World Warrior (World 910522)"
    And FinalBurn Neo's "Neogeo only" DAT lists "mslug" as "Metal Slug - Super Vehicle-001"
    And FinalBurn Neo's "Unknown only" DAT lists "odd" as "Odd Game"
    When the DAT files are loaded from the DAT directory
    Then the name "sf2" should be found for "arcade" as "Street Fighter II - The World Warrior (World 910522)" in "FBNeo - Arcade Games"
    And the name "sf2" should be found for "mame" as "Street Fighter II - The World Warrior (World 910522)" in "FBNeo - Arcade Games"
    And the name "mslug" should be found for "neogeo" as "Metal Slug - Super Vehicle-001" in "FBNeo - Arcade Games"
    And the name "odd" should not be found for "arcade"

  Scenario: DATs you add yourself are loaded, TOSEC and MAME included
    Given an extra DAT "Commodore Amiga - Games - [ADF] (TOSEC-v2024-01-01_CM).dat" whose game "Lemmings (1991)(Psygnosis)" has MD5 "12121212121212121212121212121212"
    And an extra DAT "MAME 0.270.dat" whose machine "pacman" has MD5 "34343434343434343434343434343434"
    And an extra DAT "Nintendo - Game Boy.dat" whose game "Tetris (World)" has MD5 "56565656565656565656565656565656"
    When the DAT files are loaded from the DAT directory
    Then MD5 "12121212121212121212121212121212" should be "Lemmings (1991)(Psygnosis)" for "amiga" with no thumbnail folder
    And MD5 "34343434343434343434343434343434" should be "pacman (Full Title)" for "mame" with no thumbnail folder
    And the name "pacman" should be found for "mame" as "pacman (Full Title)"
    And MD5 "56565656565656565656565656565656" should be "Tetris (World)" for "gb" in "Nintendo - Game Boy"
