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

  Scenario: DATs without any hashes, and unreadable DATs, are reported
    Given a clrmamepro DAT "Sega - Saturn.dat" with no hashes
    And an unreadable DAT "Broken.dat"
    When the DAT files are loaded from the DAT directory
    Then the DAT log should mention "Skipped unsupported or invalid DAT: Sega - Saturn.dat"
    And the DAT log should mention "Broken.dat clrmamepro parse failed"

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
