Feature: Settings saved in settings.json and edited on the Settings page

  Scenario: Defaults are used when there's no settings file
    Then the "port" setting should be 8181
    And the "multi_file_layout" setting should be "shared"
    And the "default_rom_folder" setting should be "~/Emulation/roms" expanded
    And the "steam_artwork_dir" setting should be no folder

  Scenario: Saved settings are written to settings.json and used straight away
    When the settings are saved with
      | key                | value       |
      | port               | 9000        |
      | scraper_region     | eu          |
      | screenscraper_user | player one  |
      | enable_steamgriddb | false       |
    Then the "port" setting should be 9000
    And the "screenscraper_user" setting should be "player one"
    And the "enable_steamgriddb" setting should be off
    And settings.json should be readable only by its owner
    When the settings are loaded again
    Then the "scraper_region" setting should be "eu"

  Scenario Outline: Invalid settings are refused and nothing is saved
    When the settings are saved with
      | key   | value   |
      | <key> | <value> |
    Then saving should fail for "<key>" with "<message>"
    And there should be no settings.json

    Examples:
      | key               | value | message                   |
      | port              | abc   | Must be a whole number    |
      | port              | 70000 | Must be between 1 and 65535 |
      | port              | true  | Must be between 1 and 65535 |
      | debug             | yes   | Must be on or off         |
      | multi_file_layout | flat  | Pick one of the listed    |
      | host              |       | Can't be blank            |
      | scraper_region    | 5     | Must be text              |

  Scenario: Debug mode is refused when the app listens beyond this machine
    When the settings are saved with
      | key   | value   |
      | host  | 0.0.0.0 |
      | debug | true    |
    Then saving should fail for "debug" with "only works with a 127.0.0.1 listen address"

  Scenario: Secrets are kept unless changed, and never shown
    Given the SteamGridDB API key "old-key" is saved
    When the settings are saved with
      | key             | value |
      | steamgriddb_api | none  |
    Then the "steamgriddb_api" setting should be "old-key"
    And the page values should show the "steamgriddb_api" secret as set
    When the settings are saved with
      | key             | value |
      | steamgriddb_api |       |
    Then the "steamgriddb_api" setting should be ""

  Scenario: Unknown settings are ignored
    When the settings are saved with
      | key        | value |
      | not_a_real | x     |
    Then saving should succeed

  Scenario Outline: A broken settings.json falls back to the defaults
    Given settings.json contains '<contents>'
    When the settings are loaded again
    Then the "port" setting should be 8181
    And the settings should report "<problem>"

    Examples:
      | contents          | problem                 |
      | {not json         | Couldn't read           |
      | ["a list"]        | were invalid            |
      | {"port": "lots"}  | were invalid            |

  Scenario: A failed write leaves settings.json as it was
    Given the SteamGridDB API key "old-key" is saved
    And writing settings fails with "disk full"
    When the settings are saved with
      | key             | value   |
      | steamgriddb_api | new-key |
    Then saving should raise "disk full"
    And settings.json should still hold "old-key"
    And no temporary settings files should be left
