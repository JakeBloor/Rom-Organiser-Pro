Feature: ES-DE folders and app logging

  Scenario: ES-DE settings decide where ROMs and media live
    Given ES-DE settings with ROMDirectory "~/sdcard/Emulation/roms" and MediaDirectory "/media/esde"
    Then the ROM folder should be "~/sdcard/Emulation/roms" expanded
    And the media folder should be "/media/esde"
    And the gamelists folder should be inside the ES-DE folder

  Scenario: Defaults are used when ES-DE has no settings
    Given ES-DE has no settings file
    Then the ROM folder should be the EmuDeck default
    And the media folder should be inside the ES-DE folder

  Scenario: Blank ES-DE settings fall back to the defaults
    Given ES-DE settings with blank ROM and media folders
    Then the ROM folder should be the EmuDeck default
    And the media folder should be inside the ES-DE folder

  Scenario Outline: Log messages are kept with an icon for their level
    Given an app logger
    When "<message>" is logged at <level> level
    Then the logger should hold "<icon> <message>"

    Examples:
      | level   | icon | message     |
      | INFO    | ℹ️    | Scanning    |
      | WARNING | ⚠️    | Low space   |
      | ERROR   | ❌    | Failed      |
      | DEBUG   | 🐛    | Details     |
      | SUCCESS | ✅    | Done        |
      | OTHER   | 📝    | Unspecified |

  Scenario: Only the most recent log messages are kept in memory
    Given an app logger that keeps 3 messages
    When 5 messages are logged
    Then the logger should hold messages 3 to 5
    And clearing the logger should empty it
