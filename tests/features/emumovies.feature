Feature: Videos and manuals from EmuMovies, the first source

  Background:
    Given EmuMovies has the sets
      | folder           | set                                                           | file                                      |
      | Video Snaps (HQ) | Sony Playstation (Video Snaps)(HQ480p)(ReDump)(EM 2.3)        | Final Fantasy VII (USA) (Disc 1).mp4      |
      | Video Snaps (HQ) | Sony Playstation (Video Snaps)(HQ480p)(ReDump)(EM 2.3)        | Spyro the Dragon (Europe).mp4             |
      | Video Snaps (HQ) | Sony Playstation (Video Snaps)(HQ480p)(ReDump)(EM 2.3)        | Spyro the Dragon (USA).mp4                |
      | Video Snaps (HD) | Sony Playstation (Video Snaps)(HD)(ReDump)(EM 1.0)            | Final Fantasy VII (USA) (Disc 1).mp4      |
      | Video Snaps (SQ) | Sony Playstation 2 (Video Snaps)(SQ)(Redump)(EM 1.0)          | Gran Turismo 4 (USA).mp4                  |
      | Video Snaps (HQ) | Sony Playstation 2 (Video Snaps)(HQ)(Redump)(USA)(1.6)        | Gran Turismo 4 (USA).mp4                  |
      | Video Snaps (HQ) | Sega Genesis - USA (Video Snaps)(HQ)(No-Intro)(EM 2.6)        | Sonic the Hedgehog (USA, Europe).mp4      |
      | Video Snaps (HQ) | Nintendo Entertainment System-Hacks (Video Snaps)(HQ)(EM 1.7) | Super Mario Bros. (World).mp4             |
      | Video Snaps (HQ) | Nintendo Entertainment System (Video Snaps)(HQ)(EM 2.5)       | Super Mario Bros. (World).mp4             |
      | Game Manuals     | Sony PlayStation (Game Manuals-Extras)(ReDump)(EM 1.4)        | Final Fantasy VII (USA) (Disc 1).pdf      |
      | Game Manuals     | Sony PlayStation (Game Manuals)(ReDump)(EM 1.4)               | Final Fantasy VII (USA) (Disc 1).pdf      |
      | Game Manuals     | Nintendo Game Boy Color (Manuals)(CBZ)(No-Intro)(EM 2.1)      | Tetris DX (World).cbz                     |

  Scenario: A game's video and manual are downloaded, in the chosen quality, from the main sets
    Given EmuMovies is set up with video quality "HQ"
    When EmuMovies media is fetched for "psx/Final Fantasy VII (USA).m3u" named "Final Fantasy VII (USA) (Disc 1), Final Fantasy VII (USA)"
    Then EmuMovies should have saved "videos, manuals"
    And the ES-DE "videos" file should have come from "Video Snaps (HQ)/Sony Playstation (Video Snaps)(HQ480p)(ReDump)(EM 2.3)"
    And the ES-DE "manuals" file should have come from "Game Manuals/Sony PlayStation (Game Manuals)(ReDump)(EM 1.4)"

  Scenario: HD videos are used when chosen
    Given EmuMovies is set up with video quality "HD"
    When EmuMovies media is fetched for "psx/Final Fantasy VII (USA).m3u" named "Final Fantasy VII (USA) (Disc 1)"
    Then the ES-DE "videos" file should have come from "Video Snaps (HD)"

  Scenario: Without a video in the chosen quality, the next quality is tried
    Given EmuMovies is set up with video quality "HD"
    When EmuMovies media is fetched for "ps2/Gran Turismo 4 (USA).iso" named "Gran Turismo 4 (USA) (v2.00)"
    Then the ES-DE "videos" file should have come from "Video Snaps (HQ)/Sony Playstation 2 (Video Snaps)(HQ)(Redump)(USA)(1.6)/Gran Turismo 4 (USA).mp4"

  Scenario: A set named with a region still counts for its system, and originals come before hacks
    Given EmuMovies is set up with video quality "HQ"
    When EmuMovies media is fetched for "genesis/Sonic.md" named "Sonic the Hedgehog (USA, Europe)"
    Then EmuMovies should have saved "videos"
    When EmuMovies media is fetched for "nes/SMB.nes" named "Super Mario Bros. (World)"
    Then the ES-DE "videos" file should have come from "Video Snaps (HQ)/Nintendo Entertainment System (Video Snaps)(HQ)(EM 2.5)"

  Scenario: Media a game already has, and switched-off kinds, aren't downloaded
    Given EmuMovies is set up with video quality "HQ"
    And manuals from EmuMovies are switched off
    And "psx/Final Fantasy VII (USA).m3u" already has ES-DE "videos"
    When EmuMovies media is fetched for "psx/Final Fantasy VII (USA).m3u" named "Final Fantasy VII (USA) (Disc 1)"
    Then EmuMovies should have saved nothing

  Scenario: Only manuals when videos are switched off
    Given EmuMovies is set up with video quality "HQ"
    And videos from EmuMovies are switched off
    When EmuMovies media is fetched for "psx/Final Fantasy VII (USA).m3u" named "Final Fantasy VII (USA) (Disc 1)"
    Then EmuMovies should have saved "manuals"

  Scenario: Manuals ES-DE can't open aren't downloaded
    Given EmuMovies is set up with video quality "HQ"
    When EmuMovies media is fetched for "gbc/Tetris DX.gbc" named "Tetris DX (World)"
    Then EmuMovies should have saved nothing

  Scenario: Without an exact name the title is matched, preferring the game's region
    Given EmuMovies is set up with video quality "HQ"
    When EmuMovies media is fetched for "psx/Spyro.chd" named "Spyro the Dragon (USA) (Rev 1)"
    Then the ES-DE "videos" file should have come from "Video Snaps (HQ)/Sony Playstation (Video Snaps)(HQ480p)(ReDump)(EM 2.3)/Spyro the Dragon (USA).mp4"

  Scenario Outline: Without the game's region the first title match is used
    Given EmuMovies is set up with video quality "HQ"
    When EmuMovies media is fetched for "psx/Spyro.chd" named "<name>"
    Then the ES-DE "videos" file should have come from "Video Snaps (HQ)/Sony Playstation (Video Snaps)(HQ480p)(ReDump)(EM 2.3)/Spyro the Dragon (Europe).mp4"

    Examples:
      | name                      |
      | Spyro the Dragon          |
      | Spyro the Dragon (Japan)  |

  Scenario Outline: A game or system EmuMovies doesn't have gets nothing
    Given EmuMovies is set up with video quality "HQ"
    When EmuMovies media is fetched for "<path>" named "<name>"
    Then EmuMovies should have saved nothing

    Examples:
      | path           | name                  |
      | psx/Crash.chd  | Crash Bandicoot (USA) |
      | vic20/Gorf.prg | Gorf (USA)            |

  Scenario: Folder listings are cached for a day
    Given EmuMovies is set up with video quality "HQ"
    When EmuMovies media is fetched for "psx/Crash.chd" named "Crash Bandicoot (USA)"
    And EmuMovies is reconnected and media is fetched for "psx/Crash.chd" named "Crash Bandicoot (USA)"
    Then the server should have been asked for each folder once
    When the cached listings are a day old and media is fetched for "psx/Crash.chd" named "Crash Bandicoot (USA)"
    Then the server should have been asked for each folder twice

  Scenario: A failed download is reported and leaves nothing half written
    Given EmuMovies is set up with video quality "HQ"
    And EmuMovies downloads fail with "connection reset"
    When EmuMovies media is fetched for "psx/Final Fantasy VII (USA).m3u" named "Final Fantasy VII (USA) (Disc 1)"
    Then EmuMovies should have saved nothing
    And the EmuMovies log should mention "connection reset"
    And no partly downloaded files should be left

  Scenario: A folder the server won't list counts as empty
    Given EmuMovies is set up with video quality "HQ"
    And the EmuMovies folder "Official/Game Manuals" can't be listed
    And videos from EmuMovies are switched off
    When EmuMovies media is fetched for "psx/Final Fantasy VII (USA).m3u" named "Final Fantasy VII (USA) (Disc 1)"
    Then EmuMovies should have saved nothing

  Scenario: The connection can only list and download, never change the server
    Given EmuMovies is set up with video quality "HQ"
    Then deleting, uploading, renaming and making folders on EmuMovies should be refused
    And a download command other than RETR should be refused
    And nothing on the EmuMovies server should have changed

  Scenario Outline: Connecting to EmuMovies
    Given EmuMovies is <state>
    When EmuMovies is connected to
    Then <outcome>

    Examples:
      | state                                 | outcome                                                              |
      | switched off                          | there should be no EmuMovies connection                              |
      | switched on without a login           | there should be no EmuMovies connection and the log should say "Add your FTP server" |
      | set up and allows encryption          | the EmuMovies connection should be encrypted                         |
      | set up but refuses encryption         | the EmuMovies connection should be plain FTP                         |
      | set up with a wrong password          | there should be no EmuMovies connection and the log should say "Couldn't log in" |

  Scenario: The backup server is used when the main one can't be reached
    Given EmuMovies is set up with a main server that's down and a working backup
    When EmuMovies is connected to
    Then the EmuMovies connection should be to the backup server
    And the EmuMovies log should mention "Couldn't log in to main.example"

  Scenario: Only a backup server set up is enough
    Given EmuMovies is set up with only a backup server
    When EmuMovies is connected to
    Then the EmuMovies connection should be to the backup server

  Scenario: Closing the connection saves the listings even if the server has gone
    Given EmuMovies is set up with video quality "HQ"
    And the EmuMovies server has gone away
    When EmuMovies media is fetched for "psx/Crash.chd" named "Crash Bandicoot (USA)"
    And the EmuMovies connection is closed
    Then the EmuMovies listings should be saved

  Scenario: Closing a connection that never logged in still writes the listing cache
    Given an EmuMovies connection that never logged in
    When the EmuMovies connection is closed
    Then the EmuMovies listing cache should exist

  Scenario: Games of one system share the sets already found on the connection
    Given EmuMovies is set up with video quality "HQ"
    When EmuMovies media is fetched for "psx/Spyro.chd" named "Spyro the Dragon (USA)"
    And EmuMovies media is fetched for "psx/Final Fantasy VII (USA).m3u" named "Final Fantasy VII (USA) (Disc 1)"
    Then the server should have been asked for each folder once
