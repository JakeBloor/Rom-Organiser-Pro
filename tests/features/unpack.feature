Feature: Unpacking archives, including ones split into parts

  Scenario: An archive split into parts is unpacked as one
    Given an archive of 3 images split into 3 parts
    When the archive is unpacked
    Then 3 images should have been unpacked
    And the unpacked images should match the originals

  Scenario: Only the files asked for are written
    Given an archive holding "Box/Game (USA).png", "Box/readme.txt" and the folder "Box/"
    When the archive is unpacked keeping only images
    Then the unpacked files should be "Box/Game (USA).png"

  Scenario: Entries that would land outside the target folder are skipped
    Given an archive holding "../escape.png", "/absolute.png" and "safe.png"
    When the archive is unpacked
    Then the unpacked files should be "safe.png"
    And nothing should have been written outside the target folder

  Scenario: A damaged archive is reported
    Given a file that isn't an archive
    When unpacking it is tried
    Then unpacking should fail

  Scenario: An archive cut short is reported and leaves no half file behind
    Given an archive of 3 images split into 3 parts
    And the archive's last part is missing
    When unpacking it is tried
    Then unpacking should fail
    And no unpacked file should be left half written

  Scenario: Unpacking without libarchive is reported
    Given libarchive isn't installed
    When unpacking it is tried
    Then unpacking should fail with "libarchive isn't installed"

  Scenario: An archive damaged partway through is reported
    Given an archive whose second entry is damaged
    When unpacking it is tried
    Then unpacking should fail
