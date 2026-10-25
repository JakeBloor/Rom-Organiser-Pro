Feature: Game data and artwork

  Scenario: Missing Skyscraper is reported instead of crashing
    Given Skyscraper is not installed
    When game data is scraped for "snes"
    Then scraping should report it can't run
    And the scraping log should mention "Skyscraper isn't installed"

  Scenario: Skyscraper gathers from ScreenScraper and writes ES-DE game data
    Given ScreenScraper credentials "player1" and "secret"
    And ES-DE lives in a temporary folder
    When the Skyscraper commands are built for "genesis"
    Then the gather command should scrape platform "megadrive" with credentials "player1:secret"
    And the generate command should write the ES-DE gamelist and media for "genesis"

  Scenario: Scraping is skipped when ScreenScraper is disabled
    Given ScreenScraper is disabled
    When game data is scraped for "snes"
    Then scraping should report it can't run
    And the scraping log should mention "[SCRAPER] Disabled"

  Scenario: Without credentials Skyscraper scrapes anonymously
    Given no ScreenScraper credentials
    When the Skyscraper commands are built for "snes"
    Then the gather command should not pass credentials

  Scenario: Skyscraper gathers then generates, and reports success
    Given Skyscraper is installed and exits with 0
    When game data is scraped for "snes"
    Then scraping should report success
    And Skyscraper should have run the gather then the generate command
    And the scraping log should mention "snes game data and media written for ES-DE"

  Scenario Outline: A failing Skyscraper run stops and reports why
    Given Skyscraper is installed and exits with 1 printing "<output>"
    When game data is scraped for "snes"
    Then scraping should report failure
    And Skyscraper should have run only the gather command
    And the scraping log should mention "<message>"

    Examples:
      | output                                 | message                                                       |
      | Starting\nScreenScraper login failed   | snes: Skyscraper exited with 1: ScreenScraper login failed    |
      |                                        | snes: Skyscraper exited with 1                                |

  Scenario: Skyscraper's output is shown as it runs, and it never waits for input
    Given Skyscraper is installed and prints "Pass 1 | #1/3 Chrono Trigger |  | #2/3 Tetris"
    When game data is scraped for "snes" while watching its output
    Then the output seen should be "Pass 1 | #1/3 Chrono Trigger | #2/3 Tetris | Pass 1 | #1/3 Chrono Trigger | #2/3 Tetris"
    And Skyscraper should get no input
    And scraping should report success

  Scenario: A stopped scrape ends Skyscraper and skips the remaining systems
    Given Skyscraper is installed and prints "Pass 1 | #1/3 Chrono Trigger | #2/3 Tetris"
    When game data is scraped for "snes" and stopped after "#1/3 Chrono Trigger"
    Then Skyscraper should have been stopped
    And scraping should report it can't run
    And the scraping log should mention "Scraping snes was stopped"
