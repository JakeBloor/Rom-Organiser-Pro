Feature: Organising from the web page

  Scenario: A dry run started from the page reports progress and moves nothing
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    When a dry run is started through the API
    And the run finishes
    Then the status should show 1 game organised in a dry run
    And the status log should mention "[DRY RUN]"
    And the imported ROM should still be in the import folder

  Scenario: A run with a missing import folder is rejected
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    When a run is started for a missing import folder
    Then the API should reject it with "Import folder not found"

  Scenario: A real run moves files, scrapes each system, downloads covers and refreshes the library
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    And scraping and cover downloads are stubbed
    When a real run is started through the API
    And the run finishes
    Then the status should show the run finished with 1 cover downloaded
    And "snes" should have been scraped
    And the ROM folder should now hold "snes/Chrono Trigger (USA).sfc"
    And the library should count 1 game for "snes"

  Scenario: Scraping stops after the first system when Skyscraper can't run
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    And the import folder also has "Tetris (World).gb"
    And scraping can't run and cover downloads are stubbed
    When a real run is started through the API
    And the run finishes
    Then only "gb" should have been scraped

  Scenario: A real run that places nothing skips scraping and covers
    Given an import folder with "Mystery Disc.iso" and an empty ROM folder
    And scraping and cover downloads are stubbed
    When a real run is started through the API
    And the run finishes
    Then nothing should have been scraped
    And the status log should mention "[UNSORTED]"

  Scenario: An error during a run is reported and a new run can start
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    And organising fails with "disk full"
    When a dry run is started through the API
    And the run finishes
    Then the status phase should be "failed"
    And the status log should mention "Organise failed: disk full"
    And another run can be started

  Scenario: A run with a missing ROM folder is rejected
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    When a run is started for a missing ROM folder
    Then the API should reject it with "ROM folder not found"

  Scenario: A second run can't start while one is in progress
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    And an organise run is already in progress
    When a dry run is requested through the API
    Then the API should refuse it as already running

  Scenario: The status API reports the library, API keys and DAT files
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    And the DAT folder holds "Nintendo - Game Boy.dat"
    When the ROM folder is scanned through the API
    And the status API is requested
    Then the status API should list "Nintendo - Game Boy.dat" and the API connections

  Scenario: The status API reports errors instead of crashing
    Given the DAT folder can't be read
    When the status API is requested
    Then the status API should fail with "permission denied"

  Scenario: Scanning reports the games found in the ROM folder
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    When the ROM folder is scanned through the API
    Then the scan should find 2 games across 2 systems

  Scenario: Scanning without a folder uses the ES-DE ROM folder
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    And ES-DE's ROM folder is that folder
    When the default ROM folder is scanned through the API
    Then the scan should find 2 games across 2 systems

  Scenario: Scanning can be limited to chosen systems
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    When the ROM folder's "snes" games are scanned through the API
    And the status API is requested
    Then the scan should find 1 games across 1 systems
    And the scan and status API should say only "snes" was scanned

  Scenario: Scanning everything again clears the chosen systems
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    When the ROM folder's "snes" games are scanned through the API
    And the ROM folder is scanned through the API
    Then the scan should find 2 games across 2 systems
    And the scan should say all systems were scanned

  Scenario: A malformed list of systems to scan is refused
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    When the ROM folder is scanned through the API with systems "snes"
    Then the scan should fail with status 400 and "systems must be a list"

  Scenario: The page can list the system folders to choose from
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    When the ROM folder's systems are listed through the API
    Then the API should list the systems "gb, snes"

  Scenario: Listing systems uses the ES-DE ROM folder by default
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    And ES-DE's ROM folder is that folder
    When the default ROM folder's systems are listed through the API
    Then the API should list the systems "gb, snes"

  Scenario: Listing the systems of a missing folder is reported
    When a missing ROM folder's systems are listed through the API
    Then listing the systems should fail with "ROM folder not found"

  Scenario: Scanning a missing folder is reported
    When a missing ROM folder is scanned through the API
    Then the scan should fail with status 404 and "ROM folder not found"

  Scenario: Scanning errors are reported
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    And scanning fails with "disk unplugged"
    When the ROM folder is scanned through the API
    Then the scan should fail with status 500 and "disk unplugged"

  Scenario: Startup counts the games in the ES-DE ROM folder
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    And ES-DE's ROM folder is that folder
    And DAT fetch and load functions are stubbed
    When the app starts up
    Then the startup log should mention "Found 2 games across 2 systems"

  Scenario: Startup reports DAT and scan failures without crashing
    Given DAT loading fails with "bad DAT"
    And scanning fails with "disk unplugged"
    And ES-DE's ROM folder exists
    When the app starts up
    Then the startup log should mention "DAT initialization failed: bad DAT"
    And the startup log should mention "Game scan on startup failed: disk unplugged"

  Scenario: The status API copes with no DAT folder yet
    Given there is no DAT folder yet
    When the status API is requested
    Then the status API should list no DAT files

  Scenario: Games whose cover isn't downloaded aren't counted as covers
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    And scraping is stubbed and no covers are downloaded
    When a real run is started through the API
    And the run finishes
    Then the status should show the run finished with 0 covers downloaded

  Scenario: A dry run's report shows outcomes, systems and unsorted files but no images
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    And the import folder also has "Mystery Disc.iso"
    When a dry run is started through the API
    And the run finishes
    Then the run report should count 1 organised and 1 unsorted
    And the run report should show 1 game for "snes"
    And the run report should list "Mystery Disc.iso" as unsorted
    And the run report should have no media coverage

  Scenario: A real run's report shows which images the organised games have
    Given an import folder with "Chrono Trigger (USA).sfc" and an empty ROM folder
    And scraping and cover downloads are stubbed
    And ES-DE keeps its media in a temporary folder
    When a real run is started through the API
    And the run finishes
    Then the run report should cover 1 game
    And the status should count 1 "covers" and 1 "steam_tall" download

  Scenario: Scanning reports which images the library's games have
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    And ES-DE keeps its media in a temporary folder
    When the ROM folder is scanned through the API
    Then the scan should report media coverage for 2 games

  Scenario: Steam ROM Manager can be pointed at the app's artwork from the page
    Given Steam ROM Manager has a DuckStation parser
    When Steam ROM Manager is set up through the API
    Then the API should report 1 Steam ROM Manager parser updated

  Scenario: Setting up Steam ROM Manager without it installed is reported
    Given Steam ROM Manager isn't installed
    When Steam ROM Manager is set up through the API
    Then the Steam ROM Manager setup should fail with status 404

  Scenario: The Settings page shows each setting without revealing secrets
    Given the SteamGridDB API key "secret-key" is saved
    When the Settings page is opened
    Then the page should show "SteamGridDB API key" and "Applies after restart"
    And the page should not contain "secret-key"
    And the settings API should show "steamgriddb_api" as set without its value

  Scenario: Settings saved through the API are used straight away
    When the settings are saved through the API with "steamgriddb_api" set to "new-key"
    And the status API is requested
    Then the settings API should report the save
    And the status API should show SteamGridDB as configured

  Scenario: Changing a server setting asks for a restart
    When the settings are saved through the API with "port" set to "9123"
    Then the settings API should say a restart is needed

  Scenario Outline: Bad settings are refused through the API
    When the settings are saved through the API with <body>
    Then the settings API should refuse it with status <code> and "<message>"

    Examples:
      | body                         | code | message                  |
      | "port" set to "abc"          | 400  | Must be a whole number   |
      | a body that isn't an object  | 400  | JSON object              |
      | a disk that's full           | 500  | Couldn't save settings   |

  Scenario: A broken settings file is reported when the app starts
    Given settings.json can't be read
    And DAT fetch and load functions are stubbed
    When the app starts up
    Then the startup log should mention "defaults are in use"

  Scenario: The page sees games dropped into the ROM folder, and which ones need you
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "New/Tetris (World).gb"
    And "Mystery Disc.iso" was left in the ROM folder by an earlier run
    When the ROM folder is checked for new games through the API
    Then the check should find new "New/Tetris (World).gb, snes/Chrono Trigger (USA).sfc" and "Mystery Disc.iso" needing attention as "unsorted"

  Scenario: The new games check uses the ES-DE ROM folder by default
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    And ES-DE's ROM folder is that folder
    When the default ROM folder is checked for new games through the API
    Then the check should find 2 new games

  Scenario: Checking a missing ROM folder for new games is reported
    When a missing ROM folder is checked for new games through the API
    Then the check should fail with "ROM folder not found"

  Scenario: While a run is going the last check is reported
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "New/Tetris (World).gb"
    And an organise run is going
    When the ROM folder is checked for new games through the API
    Then the check should say everything is organised

  Scenario: Without an import folder the games dropped into the ROM folder and its system folders are organised
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "New/Tetris (World).gb"
    And scraping and cover downloads are stubbed
    When the ROM folder is organised through the API
    And the run finishes
    And the ROM folder is checked for new games through the API
    Then the ROM folder should now hold "gb/Tetris (World).gb"
    And the ROM folder should now hold "snes/Chrono Trigger (USA).sfc"
    And the status log should mention "new games in"
    And the status log should mention "[IN PLACE]"
    And the check should say everything is organised

  Scenario: A cache that can't be saved is reported, not fatal
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "New/Tetris (World).gb"
    And saving the file cache fails with "read-only"
    When the ROM folder is organised in a dry run through the API
    And the run finishes
    Then the status log should mention "Couldn't save the file cache: read-only"

  Scenario: Startup says when new games are waiting
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "New/Tetris (World).gb"
    And ES-DE's ROM folder is that folder
    And DAT fetch and load functions are stubbed
    When the app starts up
    Then the startup log should mention "2 new games in the ROM folder need organising"

  Scenario: Startup says nothing about new games when none are waiting
    Given ES-DE's ROM folder exists
    And DAT fetch and load functions are stubbed
    When the app starts up
    Then the startup log should not mention "need organising"

  Scenario: A run stopped while organising skips scraping and artwork
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    And scraping and cover downloads are stubbed
    And a stop is requested once organising finishes
    When the ROM folder is organised through the API
    And the run finishes
    Then the status phase should be "stopped"
    And nothing should have been scraped
    And the status log should mention "Stopped: games not reached yet are still listed as new"

  Scenario: A run stopped during artwork downloads stops starting new ones
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    And the ROM folder also holds "gba/Golden Sun (USA).gba"
    And scraping is stubbed and a stop is requested during the first artwork download
    When the ROM folder is organised through the API
    And the run finishes
    Then the status phase should be "stopped"
    And artwork should have been fetched for at most 1 game after the stop

  Scenario: The priority systems are scraped first
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "psx/Spyro (USA).chd"
    And scraping and cover downloads are stubbed
    When the ROM folder is organised through the API
    And the run finishes
    Then the systems should have been scraped in the order "psx, snes"
    And the status should have shown Skyscraper's output

  Scenario: Stopping needs a run to stop
    When a stop is requested through the API
    Then the stop should be refused because nothing is running

  Scenario: Stopping a run asks it to stop
    Given an organise run is going
    When a stop is requested through the API
    Then the run should be asked to stop

  Scenario: Re-organising everything works through games already organised
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    And scraping and cover downloads are stubbed
    And the ROM folder has been organised through the API
    When everything in the ROM folder is re-organised through the API
    And the run finishes
    Then the status should show 2 games organised
    And the status log should mention "Re-organise everything: forgot what was known about 2 files"

  Scenario: Previewing a re-organise keeps what's been organised
    Given a ROM folder holding "snes/Chrono Trigger (USA).sfc" and "gb/Tetris (World).gb"
    And scraping and cover downloads are stubbed
    And the ROM folder has been organised through the API
    When everything in the ROM folder is re-organised in a dry run through the API
    And the run finishes
    And the ROM folder is checked for new games through the API
    Then the status should show 2 games organised
    And the status log should mention "Re-organise everything (preview)"
    And the check should say everything is organised
