Feature: Media naming and Steam ROM Manager

  Scenario: ES-DE keeps the extension of folder games in media names, Steam doesn't
    Given a game folder "psx/Crash Bandicoot (USA).cue" and a game file "snes/Chrono Trigger (USA).sfc"
    Then the ES-DE media name for "psx/Crash Bandicoot (USA).cue" should be "Crash Bandicoot (USA).cue"
    And the ES-DE media name for "snes/Chrono Trigger (USA).sfc" should be "Chrono Trigger (USA)"
    And the Steam image for "psx/Crash Bandicoot (USA).cue" should be named "Crash Bandicoot (USA).png"

  Scenario: Media coverage counts the games that have each image type
    Given the games "snes/Chrono Trigger (USA).sfc, snes/Super Mario World (USA).sfc, gb/Tetris (World).gb"
    And "snes/Chrono Trigger (USA).sfc" has ES-DE "covers, videos" and Steam "tall"
    And "gb/Tetris (World).gb" has ES-DE "covers, manuals"
    When media coverage is measured
    Then coverage should count 3 games with 2 "covers", 1 "videos", 1 "manuals" and 1 "steam_tall"
    And "snes" should have 2 games with 1 "covers"

  Scenario: Steam artwork lives beside ES-DE's media folder unless set
    Given ES-DE's media folder is "media/downloaded_media"
    Then the Steam artwork folder should be "media/steam-artwork"
    When the Steam artwork folder is set to "~/Steam Art"
    Then the Steam artwork folder should be "~/Steam Art" expanded

  Scenario: Steam ROM Manager parsers are pointed at the app's artwork
    Given Steam ROM Manager parsers
      | configTitle                       | romDirectory                    | glob                                         | tall                 |
      | Sony PlayStation - DuckStation    | ${romsdirglobal}/psx            | **/${title}@(.chd\|.m3u)                      |                      |
      | Nintendo SNES - RetroArch Snes9x  | ${romsdirglobal}                | {snes/**/!(homebrew),snes}/${title}@(.sfc)    |                      |
      | Sega Saturn - RetroArch Beetle    | ${romsdirglobal}/saturn         | **/${title}@(.chd)                           | /my art/${title}.png |
      | Emulators - Emulators             | /home/deck/Emulation/tools/launchers | ${title}@(.sh)                          |                      |
    And the Steam artwork folder is "Steam (art)"
    When Steam ROM Manager is set up
    Then "Sony PlayStation - DuckStation" should look for "tall" art in "Steam \(art\)/psx/tall/${fileName}.@(png|jpg)"
    And "Nintendo SNES - RetroArch Snes9x" should look for "icon" art in "Steam \(art\)/snes/icon/${fileName}.@(png|jpg)"
    And "Sega Saturn - RetroArch Beetle" should look for "tall" art in "/my art/${title}.png"
    And "Sega Saturn - RetroArch Beetle" should look for "hero" art in "Steam \(art\)/saturn/hero/${fileName}.@(png|jpg)"
    And "Emulators - Emulators" should have no local art
    And the setup should report updating "Sony PlayStation - DuckStation, Nintendo SNES - RetroArch Snes9x, Sega Saturn - RetroArch Beetle"
    And the original parsers should be backed up

  Scenario: The first backup of Steam ROM Manager's parsers is kept
    Given Steam ROM Manager parsers
      | configTitle                       | romDirectory                    | glob                     | tall |
      | Sony PlayStation - DuckStation    | ${romsdirglobal}/psx            | **/${title}@(.chd)       |      |
    And the Steam artwork folder is "art"
    When Steam ROM Manager is set up
    And Steam ROM Manager is set up
    Then the original parsers should be backed up
    And the second setup should report no changes

  Scenario Outline: Steam ROM Manager setup reports a missing or broken config
    Given Steam ROM Manager's parsers are <state>
    When Steam ROM Manager is set up
    Then the setup should fail

    Examples:
      | state   |
      | missing |
      | broken  |
