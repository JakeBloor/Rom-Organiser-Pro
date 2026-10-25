Feature: Remembering what's known about files in the ROM folder

  Scenario: An entry is trusted only while its file is unchanged
    Given a cached file "Game.sfc" with checksum "abc"
    Then the cache should know "Game.sfc" has checksum "abc"
    When "Game.sfc" is rewritten
    Then the cache should know nothing about "Game.sfc"

  Scenario: A missing file has no entry
    Then the cache should know nothing about "Nowhere.sfc"

  Scenario: Entries follow files the app moves and survive a restart
    Given a cached file "Game.sfc" with checksum "abc"
    When "Game.sfc" is moved to "snes/Game.sfc"
    And the cache is saved and loaded again
    Then the cache should know "snes/Game.sfc" has checksum "abc"

  Scenario: Saving drops entries for files that have gone
    Given a cached file "Game.sfc" with checksum "abc"
    And a cached file "Gone.sfc" with checksum "def"
    When "Gone.sfc" is deleted
    And the cache is saved and loaded again
    Then the cache should hold only "Game.sfc"

  Scenario: Only games still where the app put them count as the library
    Given a cached file "snes/Game.sfc" with checksum "abc" that was organised
    And a cached file "snes/Moved.sfc" with checksum "def" that was organised
    And a cached file "Unsorted.iso" with checksum "123"
    When "snes/Moved.sfc" is deleted
    Then the library checksums should be "abc"

  Scenario Outline: A broken or outdated cache starts empty
    Given the cache file contains '<contents>'
    When the cache is loaded
    Then the cache should be empty

    Examples:
      | contents                         |
      | {not json                        |
      | []                               |
      | {"version": 0, "files": {}}      |
      | {"version": 1, "files": []}      |

  Scenario: A failed save leaves no temporary file behind
    Given a cached file "Game.sfc" with checksum "abc"
    And writing the cache fails with "disk full"
    When the cache is saved
    Then saving the cache should raise "disk full"
    And no temporary cache files should be left

  Scenario: Moving a file the cache doesn't know about changes nothing
    Given a cached file "Game.sfc" with checksum "abc"
    When an unknown file is moved
    Then the cache should hold only "Game.sfc"

  Scenario: Forgetting a folder forgets only what's inside it
    Given a cached file "snes/Game.sfc" with checksum "abc"
    And a cached file "snes-old/Other.sfc" with checksum "def"
    When everything under "snes" is forgotten
    Then 1 entry should have been forgotten
    And the cache should hold only "snes-old/Other.sfc"
